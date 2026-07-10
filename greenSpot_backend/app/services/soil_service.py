"""농촌진흥청 흙토람 토양도 기반 토양특성 상세 정보 V3 클라이언트.

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

import logging
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

SOURCE_LABEL = "흙토람 (농진청)"
SOURCE_UNCONFIGURED = "흙토람 (농진청, 미연동)"


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
_SURTTURE_LABEL: Dict[str, str] = {
    "01": "사토",
    "02": "양질사토",
    "03": "사양토",
    "04": "양토",
    "05": "미사질양토",
    "06": "식양토",
    "07": "식토",
    "08": "미사질식양토",
    "09": "미사질식토",
    "10": "사질식양토",
}

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

# 배수등급 (Soildra_Cd) — 관례 코드
_DRAINAGE_LABEL: Dict[str, str] = {
    "01": "매우불량",
    "02": "불량",
    "03": "약간불량",
    "04": "양호",
    "05": "약간양호",
    "06": "매우양호",
}

# 유효토심 (Vldsoildep_Cd)
_DEPTH_LABEL: Dict[str, str] = {
    "01": "매우얕음",
    "02": "얕음",
    "03": "보통",
    "04": "깊음",
    "05": "매우깊음",
}

# 표토 자갈함량 (Sur_Ston_Cd)
_STON_LABEL: Dict[str, str] = {
    "01": "없음",
    "02": "약간있음",
    "03": "보통",
    "04": "많음",
    "05": "매우많음",
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


def _pad_code(raw: Any) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    if value.isdigit():
        return value.zfill(2)
    return value


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


def _item_has_soil_payload(item: Dict[str, Any]) -> bool:
    """빈 코드만 있는 도시 필지 응답을 걸러낸다."""
    for key in (
        "Surtture_Cd",
        "surtture_Cd",
        "SURTTURE_CD",
        "Soildra_Cd",
        "Vldsoildep_Cd",
        "Soil_Type_Cd",
        "soilTexture",
        "토성",
    ):
        if str(item.get(key) or "").strip():
            return True
    # 코드 필드 중 하나라도 비어 있지 않으면 유효
    for k, v in item.items():
        if k in ("PNU_Cd", "PNU_CD", "pnu"):
            continue
        if str(v or "").strip():
            return True
    return False


def _build_soil_detail(item: Dict[str, Any], soil_type: str) -> Dict[str, Any]:
    surtture = _pad_code(
        item.get("Surtture_Cd")
        or item.get("surtture_Cd")
        or item.get("SURTTURE_CD")
        or item.get("Surtture_cd")
    )
    drainage = _pad_code(item.get("Soildra_Cd") or item.get("soildra_Cd"))
    depth = _pad_code(item.get("Vldsoildep_Cd") or item.get("vldsoildep_Cd"))
    ston = _pad_code(item.get("Sur_Ston_Cd") or item.get("sur_Ston_Cd"))
    soil_type_cd = _pad_code(item.get("Soil_Type_Cd") or item.get("soil_Type_Cd"))

    surtture_name = _SURTTURE_LABEL.get(surtture, "")
    if not surtture_name and soil_type != "UNKNOWN":
        surtture_name = {
            "LOAM": "양토",
            "SAND": "사질토",
            "CLAY": "점토",
            "ROCKY": "암반/자갈",
        }.get(soil_type, "")

    return {
        "surttureCd": surtture or None,
        "surttureName": surtture_name or None,
        "drainageCd": drainage or None,
        "drainageName": _DRAINAGE_LABEL.get(drainage) if drainage else None,
        "validDepthCd": depth or None,
        "validDepthName": _DEPTH_LABEL.get(depth) if depth else None,
        "surfaceStoneCd": ston or None,
        "surfaceStoneName": _STON_LABEL.get(ston) if ston else None,
        "soilTypeCd": soil_type_cd or None,
        "soilTypeLabel": surtture_name or None,
        "pnu": str(item.get("PNU_Cd") or item.get("PNU_CD") or item.get("pnu") or "") or None,
    }


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

    def _empty_result(self, pnu: str, *, error: Optional[str] = None) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "pnu": pnu,
            "soilType": "UNKNOWN",
            "soilTypeLabel": None,
            "dataAvailable": False,
            "source": SOURCE_LABEL,
            "soilDetail": None,
        }
        if error:
            out["error"] = error
        return out

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
                "soilTypeLabel": "양토",
                "dataAvailable": True,
                "source": "흙토람 (농진청)",
                "soilDetail": {...},
            }
        """
        self._check_key()
        pnu = str(pnu or "").strip()
        if not pnu or len(pnu) < 10:
            return self._empty_result(pnu, error="invalid_pnu")

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
        except Exception as exc:
            logger.warning("soil API request failed pnu=%s: %s", pnu, exc)
            return self._empty_result(pnu, error="request_failed")

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
                    logger.info("soil API non-ok result_code=%s pnu=%s", result_code, pnu)
                    return self._empty_result(pnu, error=f"result_code:{result_code}")
                items = _xml_items_to_dicts(root)
        except Exception as exc:
            logger.warning("soil API parse failed pnu=%s: %s", pnu, exc)
            return self._empty_result(pnu, error="parse_failed")

        if not items:
            return self._empty_result(pnu, error="no_items")

        # 유효 토양 코드가 있는 첫 item 사용 (빈 코드 행 스킵)
        item: Optional[Dict[str, Any]] = None
        for candidate in items:
            if _item_has_soil_payload(candidate):
                item = candidate
                break
        if item is None:
            return self._empty_result(pnu, error="empty_soil_codes")

        soil_type = self._extract_soil_type(item)
        detail = _build_soil_detail(item, soil_type)
        available = soil_type != "UNKNOWN"
        return {
            "pnu": pnu,
            "soilType": soil_type,
            "soilTypeLabel": detail.get("soilTypeLabel") or detail.get("surttureName"),
            "dataAvailable": available,
            "source": SOURCE_LABEL,
            "soilDetail": detail,
            "raw": item,
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
                "soilTypeLabel": None,
                "dataAvailable": False,
                "source": SOURCE_UNCONFIGURED,
                "soilDetail": None,
            }
        result = await self.get_soil_by_pnu(pnu)
        if not result["dataAvailable"]:
            result["soilType"] = fallback
        return result


def client() -> SoilClient:
    return SoilClient()
