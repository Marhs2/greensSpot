"""농촌진흥청 토양도 기반 토양특성 상세 정보 V3 클라이언트.

엔드포인트 예시:
  GET https://apis.data.go.kr/1390802/SoilEnviron/SoilCharac/V3/getSoilCharacter
    ?serviceKey=...&PNU_CD={19자리PNU}

응답: XML
  <response><body><items><item>
    <Surtture_Cd>04</Surtture_Cd>  <!-- 표토토성코드 -->
    ...
  </item></items></body></response>

.env:
  SOIL_API_KEY=...
  SOIL_BASE_URL=https://apis.data.go.kr/1390802/SoilEnviron/SoilCharac/V3
  (또는 .../getSoilCharacter 까지 포함 가능)
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

import httpx

from app.core.config import settings


class SoilNotConfigured(Exception):
    pass


def _normalize_service_key(raw: str) -> str:
    """공공데이터포털 인코딩 키(%2F 등)가 들어오면 디코딩해 이중 인코딩을 막는다."""
    key = (raw or "").strip()
    if not key:
        return ""
    if "%" in key:
        key = unquote(key)
    return key


# 표토토성코드(Surtture_Cd) — 세부정밀토양도 속성 관례
# 01 사토, 02 양질사토, 03 사양토, 04 양토, 05 미사질양토,
# 06 식양토, 07 식토, 08 미사질식양토, 09 미사질식토, 10 사질식양토
_SURTTURE_TO_SOIL: Dict[str, str] = {
    "01": "SAND",
    "1": "SAND",
    "02": "SAND",
    "2": "SAND",
    "03": "SAND",  # 사양토 → 사질 계열
    "3": "SAND",
    "04": "LOAM",
    "4": "LOAM",
    "05": "LOAM",  # 미사질양토
    "5": "LOAM",
    "06": "CLAY",  # 식양토
    "6": "CLAY",
    "07": "CLAY",
    "7": "CLAY",
    "08": "CLAY",
    "8": "CLAY",
    "09": "CLAY",
    "9": "CLAY",
    "10": "SAND",
}

# 텍스트/기타 필드 정규화용 패턴
_SOIL_CODE_FIELDS = (
    "Surtture_Cd",
    "surtture_cd",
    "SURTTURE_CD",
    "soilCode",
    "soilSymbol",
    "soilFeatureCode",
    "scllorCd",
    "scllorNm",
    "surftSldcCd",
    "sldcCd",
)
_SOIL_NAME_FIELDS = (
    "soilName",
    "soilFeature",
    "scllor",
    "soilTexture",
    "토성",
    "surftSldcNm",
    "sldcNm",
)


def _normalize_soil_type(raw: Any) -> str:
    if raw is None:
        return "UNKNOWN"
    value = str(raw).strip()
    if not value or value.upper() in ("-", "", "NULL"):
        return "UNKNOWN"

    # 숫자/코드 우선 (Surtture_Cd)
    code = value.zfill(2) if value.isdigit() else value
    if code in _SURTTURE_TO_SOIL:
        return _SURTTURE_TO_SOIL[code]
    if value in _SURTTURE_TO_SOIL:
        return _SURTTURE_TO_SOIL[value]

    upper = value.upper()
    sandy = ("모래", "SAND", "사질", "SANDY", "사토", "사양토", "LOAMY SAND", "SANDY LOAM")
    loam = ("양토", "LOAM", "SILT LOAM", "SILT", "SLT", "양질", "미사질양토")
    clay = ("점토", "CLAY", "식점토", "식토", "식양토", "CLAY LOAM", "SILTY CLAY", "점질")
    rocky = ("암반", "ROCK", "ROCKY", "자갈", "GRAVEL", "GRAVELLY", "SHALLOW")

    for pattern in sandy:
        if pattern.upper() in upper or pattern in value:
            return "SAND"
    for pattern in loam:
        if pattern.upper() in upper or pattern in value:
            return "LOAM"
    for pattern in clay:
        if pattern.upper() in upper or pattern in value:
            return "CLAY"
    for pattern in rocky:
        if pattern.upper() in upper or pattern in value:
            return "ROCKY"
    return "UNKNOWN"


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _xml_items_to_dicts(root: ET.Element) -> List[Dict[str, Any]]:
    """XML 응답에서 item 목록을 dict 리스트로 변환."""
    items: List[Dict[str, Any]] = []
    for el in root.iter():
        if _local(el.tag).lower() != "item":
            continue
        row: Dict[str, Any] = {}
        for child in list(el):
            row[_local(child.tag)] = (child.text or "").strip()
        if row:
            items.append(row)
    return items


def _extract_items(data: Any) -> List[Dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    response = data.get("response") or data
    if not isinstance(response, dict):
        return []
    body = response.get("body") or {}
    if not isinstance(body, dict):
        return []
    items = body.get("items") or body.get("item")
    if items is None:
        items = data.get("items") or data.get("item") or data.get("list")
    if isinstance(items, dict):
        nested = items.get("item") or items.get("field")
        if nested is not None:
            items = nested
        else:
            return [items]
    if isinstance(items, list):
        return [x for x in items if isinstance(x, dict)]
    return []


class SoilClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = _normalize_service_key(api_key or settings.soil_api_key or "")
        self.base_url = (base_url or settings.soil_base_url or "").strip()

    def _check_key(self):
        if not self.api_key:
            raise SoilNotConfigured("SOIL_API_KEY가 설정되지 않았습니다.")
        if not self.base_url:
            raise SoilNotConfigured("SOIL_BASE_URL이 설정되지 않았습니다.")

    def _resolve_url(self) -> str:
        """BASE_URL 이 서비스 root 이든 getSoilCharacter 전체 path 이든 정규화."""
        url = (self.base_url or "").rstrip("/")
        lower = url.lower()
        if lower.endswith("getsoilcharacter"):
            return url
        if "soilcharac" in lower or "soilenviron" in lower:
            return f"{url}/getSoilCharacter"
        if url:
            return f"{url}/1390802/SoilEnviron/SoilCharac/V3/getSoilCharacter"
        return "https://apis.data.go.kr/1390802/SoilEnviron/SoilCharac/V3/getSoilCharacter"

    def _extract_soil_type(self, item: Dict[str, Any]) -> str:
        # 표토토성코드 최우선
        for field in ("Surtture_Cd", "surtture_Cd", "SURTTURE_CD", "Surtture_cd"):
            if field in item and item[field] not in (None, ""):
                mapped = _normalize_soil_type(item[field])
                if mapped != "UNKNOWN":
                    return mapped
        for field in _SOIL_CODE_FIELDS:
            if field in item and item[field] not in (None, ""):
                mapped = _normalize_soil_type(item[field])
                if mapped != "UNKNOWN":
                    return mapped
        for field in _SOIL_NAME_FIELDS:
            if field in item and item[field] not in (None, ""):
                mapped = _normalize_soil_type(item[field])
                if mapped != "UNKNOWN":
                    return mapped
        # 자갈/석력 많으면 ROCKY 힌트 (Sur_Ston_Cd 높을 때)
        ston = str(item.get("Sur_Ston_Cd") or item.get("sur_Ston_Cd") or "").strip()
        if ston in ("04", "05", "4", "5"):
            return "ROCKY"
        return "UNKNOWN"

    async def get_soil_by_pnu(
        self,
        pnu: str,
        *,
        num_of_rows: int = 100,
        page_no: int = 1,
    ) -> Dict[str, Any]:
        """PNU 기반 토양 타입을 조회한다.

        반환 형식:
            {
                "pnu": "1117010300101680003",
                "soilType": "LOAM",
                "dataAvailable": True,
                "source": "농촌진흥청 토양정보",
            }
        """
        self._check_key()
        url = self._resolve_url()
        # 공식 예시: serviceKey + PNU_CD
        params: Dict[str, Any] = {
            "serviceKey": self.api_key,
            "PNU_CD": pnu,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                text = resp.text.strip()
                ct = (resp.headers.get("content-type") or "").lower()
        except Exception:
            return {
                "pnu": pnu,
                "soilType": "UNKNOWN",
                "dataAvailable": False,
                "source": "농촌진흥청 토양정보",
            }

        items: List[Dict[str, Any]] = []
        try:
            if "json" in ct or text.startswith(("{", "[")):
                data = resp.json()
                items = _extract_items(data)
            else:
                # XML (기본 응답)
                root = ET.fromstring(text)
                # 결과코드 확인
                result_code = None
                for el in root.iter():
                    if _local(el.tag) in ("Result_Code", "resultCode", "result_code"):
                        result_code = (el.text or "").strip()
                        break
                if result_code and result_code not in ("200", "00", "0", "NORMAL_SERVICE"):
                    return {
                        "pnu": pnu,
                        "soilType": "UNKNOWN",
                        "dataAvailable": False,
                        "source": "농촌진흥청 토양정보",
                    }
                items = _xml_items_to_dicts(root)
        except Exception:
            return {
                "pnu": pnu,
                "soilType": "UNKNOWN",
                "dataAvailable": False,
                "source": "농촌진흥청 토양정보",
            }

        if not items:
            return {
                "pnu": pnu,
                "soilType": "UNKNOWN",
                "dataAvailable": False,
                "source": "농촌진흥청 토양정보",
            }

        soil_type = self._extract_soil_type(items[0])
        return {
            "pnu": pnu,
            "soilType": soil_type,
            "dataAvailable": soil_type != "UNKNOWN",
            "source": "농촌진흥청 토양정보",
            "raw": items[0],
        }

    async def get_soil_type(
        self,
        pnu: str,
        fallback: str = "UNKNOWN",
    ) -> Dict[str, Any]:
        """토양 타입 실제값 조회. 실패/미연동 시 fallback 값을 사용한다."""
        if not self.api_key or not self.base_url:
            return {
                "pnu": pnu,
                "soilType": fallback,
                "dataAvailable": False,
                "source": "농촌진흥청 토양정보 (미연동)",
            }
        result = await self.get_soil_by_pnu(pnu)
        if not result["dataAvailable"]:
            result["soilType"] = fallback
        return result


def client() -> SoilClient:
    return SoilClient()
