"""AirKorea (한국환경공단) 대기오염정보 API 클라이언트.

제공 기능:
- 시도별 실시간 측정정보를 조회해 구/군 단위 PM2.5 값 추출
- API 미연동/실패 시 fallback 값 반환
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import unquote

import httpx

from app.core.config import settings


class AirKoreaNotConfigured(Exception):
    pass


def _normalize_service_key(raw: str) -> str:
    """공공데이터포털 인코딩 키(%2F 등)가 들어오면 디코딩해 이중 인코딩을 막는다."""
    key = (raw or "").strip()
    if not key:
        return ""
    # 이미 URL-encoded 형태면 한 번 디코딩 (httpx가 다시 인코딩)
    if "%" in key:
        key = unquote(key)
    return key


# 서울 특별시 구명 → AirKorea 측정소명에서 사용되는 짧은 이름 매핑
# 예: "용산구" → "용산", "강남구" → "강남"
def _district_short_name(district: str) -> str:
    district = district.strip()
    if district.endswith("구") or district.endswith("시") or district.endswith("군"):
        district = district[:-1]
    return district


# 서울 구명 → 시도명(서울)
def _district_to_sido(district: str) -> str:
    return "서울"


class AirKoreaClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = _normalize_service_key(api_key or settings.airkorea_api_key or "")
        self.base_url = (base_url or settings.airkorea_base_url or "").strip()

    def _check_key(self):
        if not self.api_key:
            raise AirKoreaNotConfigured("AIRKOREA_API_KEY가 설정되지 않았습니다.")
        if not self.base_url:
            raise AirKoreaNotConfigured("AIRKOREA_BASE_URL이 설정되지 않았습니다.")

    def _build_url(self, path: str) -> str:
        base = self.base_url.rstrip("/")
        return f"{base}{path}"

    def _parse_pm25(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(str(value).strip())
        except (ValueError, TypeError):
            return None

    async def get_pm25_by_district(
        self,
        district: str,
        *,
        num_of_rows: int = 1000,
        page_no: int = 1,
    ) -> Dict[str, Any]:
        """서울 등 특정 시도의 실시간 측정정보에서 구 단위 PM2.5를 추출한다.

        반환 형식:
            {
                "district": "용산구",
                "sido": "서울",
                "pm25": 27.0,
                "station": "용산",
                "dataAvailable": True,
                "source": "AirKorea",
            }
        """
        self._check_key()
        sido = _district_to_sido(district)
        short = _district_short_name(district)

        params: Dict[str, Any] = {
            "serviceKey": self.api_key,
            "returnType": "json",
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "sidoName": sido,
            "ver": "1.2",
        }

        # BASE_URL 이 서비스 root 또는 전체 endpoint 모두 허용
        base = (self.base_url or "").rstrip("/")
        if base.endswith("getCtprvnRltmMesureDnsty"):
            url = base
        elif "ArpltnInforInqireSvc" in base:
            url = f"{base}/getCtprvnRltmMesureDnsty"
        else:
            url = self._build_url("/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            return {
                "district": district,
                "sido": sido,
                "pm25": None,
                "station": None,
                "dataAvailable": False,
                "source": "AirKorea",
            }

        items: List[Dict[str, Any]] = []
        if isinstance(data, dict):
            response = data.get("response") or {}
            body = response.get("body") or {}
            raw_items = body.get("items") or []
            if isinstance(raw_items, list):
                items = raw_items
            elif isinstance(raw_items, dict):
                items = [raw_items]

        # 구 이름이 포함된 측정소 중 PM2.5 값이 있는 첫 항목 선택
        for item in items:
            station = str(item.get("stationName") or "").strip()
            pm25 = self._parse_pm25(item.get("pm25Value"))
            if pm25 is not None and short and short in station:
                return {
                    "district": district,
                    "sido": sido,
                    "pm25": round(pm25, 1),
                    "station": station,
                    "dataAvailable": True,
                    "source": "AirKorea",
                }

        # 구 일치 항목이 없으면 전체 평균 중 유효한 첫 값 사용
        for item in items:
            pm25 = self._parse_pm25(item.get("pm25Value"))
            if pm25 is not None:
                return {
                    "district": district,
                    "sido": sido,
                    "pm25": round(pm25, 1),
                    "station": str(item.get("stationName") or "").strip(),
                    "dataAvailable": True,
                    "source": "AirKorea",
                }

        return {
            "district": district,
            "sido": sido,
            "pm25": None,
            "station": None,
            "dataAvailable": False,
            "source": "AirKorea",
        }

    async def get_air_quality(
        self,
        district: str,
        fallback: Optional[float] = None,
    ) -> Dict[str, Any]:
        """PM2.5 실제값 조회. 실패/미연동 시 fallback 값을 사용한다."""
        if not self.api_key:
            return {
                "district": district,
                "pm25": fallback,
                "station": None,
                "dataAvailable": False,
                "source": "AirKorea (미연동)",
            }
        result = await self.get_pm25_by_district(district)
        if not result["dataAvailable"] and fallback is not None:
            result["pm25"] = fallback
        return result


def client() -> AirKoreaClient:
    return AirKoreaClient()
