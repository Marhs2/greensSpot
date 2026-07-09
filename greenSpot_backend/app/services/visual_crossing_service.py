"""
Visual Crossing Weather API 클라이언트.

부지의 환경 데이터(일사량, 일조시간, 기온 등)를 Visual Crossing Timeline API에서
보강한다. district 기반으로 location 을 매핑하고, 최근 30일(또는 지정 기간)의
일별 solarenergy(MJ/m²) 를 kWh/㎡/day 로 변환해 반환한다.

참고: https://www.visualcrossing.com/resources/documentation/weather-api/timeline-api/
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings


# 서울 주요 자치구 + 거점 도시 → Visual Crossing location query
# (Visual Crossing free tier 는 일반적으로 "City,Country" 형태)
DISTRICT_TO_LOCATION: Dict[str, str] = {
    # 서울 자치구 (명세서 5구 + 주요 자치구)
    "종로구": "Seoul,South Korea",
    "중구": "Seoul,South Korea",
    "용산구": "Seoul,South Korea",
    "성동구": "Seoul,South Korea",
    "광진구": "Seoul,South Korea",
    "동대문구": "Seoul,South Korea",
    "중랑구": "Seoul,South Korea",
    "성북구": "Seoul,South Korea",
    "강북구": "Seoul,South Korea",
    "도봉구": "Seoul,South Korea",
    "노원구": "Seoul,South Korea",
    "은평구": "Seoul,South Korea",
    "서대문구": "Seoul,South Korea",
    "마포구": "Seoul,South Korea",
    "양천구": "Seoul,South Korea",
    "강서구": "Seoul,South Korea",
    "구로구": "Seoul,South Korea",
    "금천구": "Seoul,South Korea",
    "영등포구": "Seoul,South Korea",
    "동작구": "Seoul,South Korea",
    "관악구": "Seoul,South Korea",
    "서초구": "Seoul,South Korea",
    "강남구": "Seoul,South Korea",
    "송파구": "Seoul,South Korea",
    "강동구": "Seoul,South Korea",
    # 경기도 / 광역시 주요 거점
    "성남시": "Seongnam,South Korea",
    "수원시": "Suwon,South Korea",
    "용인시": "Yongin,South Korea",
    "고양시": "Goyang,South Korea",
    "제주시": "Jeju,South Korea",
    "부산광역시": "Busan,South Korea",
    "인천광역시": "Incheon,South Korea",
    "대구광역시": "Daegu,South Korea",
    "대전광역시": "Daejeon,South Korea",
    "광주광역시": "Gwangju,South Korea",
}
DEFAULT_LOCATION = "Seoul,South Korea"

# 에너지 단위 변환: 1 MJ/m² = 0.2777778 kWh/m²
MJ_TO_KWH = 0.2777778

# 열섬 추정 상수 — Visual Crossing 평균 기온 → urban heat / heat-island
URBAN_SURFACE_OFFSET_C = 5.0   # 평균 기온 + 도시 열섬 오프셋 = 지표면 온도
HEAT_ISLAND_BASELINE_C = 25.0  # 이 기준보다 높으면 열섬 강도로 간주


class VisualCrossingNotConfigured(Exception):
    pass


class VisualCrossingRateLimited(Exception):
    """일일 쿼터/비용 초과 (HTTP 429)."""
    pass


class VisualCrossingClient:
    """Visual Crossing Timeline API 클라이언트."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = (api_key if api_key is not None else settings.visual_crossing_api_key or "").strip()
        self.base_url = (base_url if base_url is not None else settings.visual_crossing_base_url or "").rstrip("/")

    # ------------------------------------------------------------------ helpers
    def _check_key(self):
        if not self.api_key:
            raise VisualCrossingNotConfigured(
                "VISUAL_CROSSING_API_KEY가 설정되지 않았습니다. .env에 입력하세요."
            )
        if not self.base_url:
            raise VisualCrossingNotConfigured(
                "VISUAL_CROSSING_BASE_URL이 설정되지 않았습니다."
            )

    @staticmethod
    def _default_period() -> tuple[str, str]:
        end = datetime.utcnow().date()
        start = end - timedelta(days=30)
        return str(start), str(end)

    @staticmethod
    def _location_for_district(district: Optional[str]) -> str:
        if not district:
            return DEFAULT_LOCATION
        return DISTRICT_TO_LOCATION.get(district.strip(), DEFAULT_LOCATION)

    @staticmethod
    def _summer_period(reference: Optional[date] = None) -> tuple[str, str]:
        """기본 여름 기간. reference 가 6~8월이면 해당 연도, 아니면 전년도."""
        ref = reference or date.today()
        if 6 <= ref.month <= 8:
            year = ref.year
        else:
            year = ref.year - 1
        return f"{year}-06-01", f"{year}-08-31"

    # ------------------------------------------------------------------ API
    async def get_timeline(
        self,
        location: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Visual Crossing Timeline API 에서 일별(day) 데이터를 조회한다."""
        self._check_key()

        start = start or self._default_period()[0]
        end = end or self._default_period()[1]

        # Visual Crossing Timeline API 는 날짜 범위를 경로에 포함한다.
        # /timeline/{location}/{start}/{end}?key=...&unitGroup=...
        url = f"{self.base_url}/{location}/{start}/{end}"
        params: Dict[str, Any] = {
            "key": self.api_key,
            "unitGroup": "metric",
            "include": "days",
            "contentType": "json",
        }

        async with httpx.AsyncClient(timeout=20.0) as http:
            resp = await http.get(url, params=params)
            if resp.status_code == 429:
                raise VisualCrossingRateLimited(resp.text[:200] or "VC rate limited")
            # 일부 플랜은 본문에 Maximum daily cost 메시지를 남긴다
            text_head = (resp.text or "")[:120].lower()
            if "maximum daily" in text_head or "rate limit" in text_head:
                raise VisualCrossingRateLimited(resp.text[:200])
            resp.raise_for_status()
            data = resp.json()

        days = data.get("days") or []
        return days

    # ------------------------------------------------------------------ climate
    async def get_climate_for_district(
        self,
        district: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        *,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """district 를 기준으로 기후 데이터를 요약 반환한다.

        `location` 이 직접 주어지면 district 매핑을 건너뛰고 그 값을 그대로 사용한다
        (예: ``"37.5145,127.0533"`` 같은 lat,lng 형식).

        반환:
            {
                source: "visualcrossing",
                district,
                location,
                start,
                end,
                solarIrradiance: kWh/㎡/day,
                sunlightHours: hr,
                avgTemperature: °C,
                dataAvailable: bool,
            }
        """
        resolved_location = location or self._location_for_district(district)
        start = start or self._default_period()[0]
        end = end or self._default_period()[1]

        result: Dict[str, Any] = {
            "source": "visualcrossing",
            "district": district,
            "location": resolved_location,
            "start": start,
            "end": end,
            "solarIrradiance": 0.0,
            "sunlightHours": 0.0,
            "avgTemperature": 0.0,
            "dataAvailable": False,
        }

        try:
            days = await self.get_timeline(resolved_location, start=start, end=end)
        except Exception:
            return result

        if not days:
            return result

        solarenergy: List[float] = []
        hours: List[float] = []
        temps: List[float] = []
        for day in days:
            if day.get("solarenergy") not in (None, ""):
                try:
                    solarenergy.append(float(day["solarenergy"]))
                except (TypeError, ValueError):
                    pass
            sunshine = day.get("sunshine")
            if sunshine not in (None, ""):
                try:
                    hours.append(float(sunshine))
                except (TypeError, ValueError):
                    pass
            temp = day.get("temp")
            if temp not in (None, ""):
                try:
                    temps.append(float(temp))
                except (TypeError, ValueError):
                    pass

        if solarenergy:
            # solarenergy 는 MJ/m²/day 단위. kWh/㎡/day 로 변환.
            result["solarIrradiance"] = round(
                (sum(solarenergy) / len(solarenergy)) * MJ_TO_KWH, 3
            )
        if hours:
            result["sunlightHours"] = round(sum(hours) / len(hours), 2)
        if temps:
            result["avgTemperature"] = round(sum(temps) / len(temps), 2)

        result["dataAvailable"] = bool(solarenergy)
        return result

    # ------------------------------------------------------------------ heat
    async def get_heat_estimates(
        self,
        district: Optional[str] = None,
        days: int = 30,
        *,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """district 의 여름 기간 평균 기온으로 열섬/지표면 온도 추정.

        `location` 이 직접 주어지면 district 매핑을 건너뛰고 그 값을 그대로 사용한다
        (예: ``"37.5145,127.0533"`` 같은 lat,lng 형식).

        - `surfaceTempSummer` = 여름 평균 기온 + URBAN_SURFACE_OFFSET_C
        - `heatIsland` = max(0, 여름 평균 기온 - HEAT_ISLAND_BASELINE_C)
        - 미연동/오류 시 모든 추정값 None + `dataAvailable: false`.

        반환:
            {
                source: "visualcrossing",
                district,
                location,
                period: {start, end},
                heatIsland: float | None,
                surfaceTempSummer: float | None,
                avgTemperature: float | None,
                maxTemperature: float | None,
                dataAvailable: bool,
            }
        """
        resolved_location = location or self._location_for_district(district)
        start, end = self._summer_period()

        result: Dict[str, Any] = {
            "source": "visualcrossing",
            "district": district,
            "location": resolved_location,
            "period": {"start": start, "end": end},
            "heatIsland": None,
            "surfaceTempSummer": None,
            "avgTemperature": None,
            "maxTemperature": None,
            "dataAvailable": False,
        }

        try:
            timeline_days = await self.get_timeline(resolved_location, start=start, end=end)
        except VisualCrossingNotConfigured:
            raise
        except Exception:
            return result

        if not timeline_days:
            return result

        temps: List[float] = []
        for day in timeline_days:
            temp = day.get("temp")
            if temp in (None, ""):
                continue
            try:
                temps.append(float(temp))
            except (TypeError, ValueError):
                continue

        if not temps:
            return result

        avg_temp = sum(temps) / len(temps)
        max_temp = max(temps)
        surface_temp = avg_temp + URBAN_SURFACE_OFFSET_C
        heat_island = max(0.0, avg_temp - HEAT_ISLAND_BASELINE_C)

        result["avgTemperature"] = round(avg_temp, 2)
        result["maxTemperature"] = round(max_temp, 2)
        result["surfaceTempSummer"] = round(surface_temp, 2)
        result["heatIsland"] = round(heat_island, 2)
        result["dataAvailable"] = True
        return result


def client() -> VisualCrossingClient:
    return VisualCrossingClient()
