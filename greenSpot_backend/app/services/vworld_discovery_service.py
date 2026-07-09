"""
VWorld 2D Data API — 서울 연속지적도(LP_PA_CBND_BUBUN) 기반 부지 발굴.

연속지적도에서 필지를 수집하고, 기존 vworld_service 규제 레이어로
수목 식재 가능성·점수를 산출한다.
"""
from __future__ import annotations

import asyncio
import math
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.config import settings
from app.services.airkorea_service import client as airkorea_client
from app.services.land_ownership_service import client as land_ownership_client
from app.services.soil_service import client as soil_client
from app.services.vworld_service import (
    VWORLD_LAYERS,
    apply_regulation_penalties,
    client as vworld_client,
    compute_sumok_feasibility,
)

VWORLD_DATA_URL = "https://api.vworld.kr/req/data"
CADASTral_DATA = "LP_PA_CBND_BUBUN"
EMD_DATA = "LT_C_ADEMD_INFO"

SEOUL_BBOX = (126.75, 37.42, 127.25, 37.72)  # min_lng, min_lat, max_lng, max_lat
SEASON = [0.55, 0.72, 0.9, 1.08, 1.18, 1.13, 1.03, 0.98, 0.86, 0.72, 0.58, 0.5]

DISTRICT_PREFIX = {
    "종로구": "JR", "중구": "JG", "용산구": "YS", "성동구": "SD", "광진구": "GJ",
    "동대문구": "DD", "중랑구": "JL", "성북구": "SB", "강북구": "GB", "도봉구": "DB",
    "노원구": "NW", "은평구": "EP", "서대문구": "SM", "마포구": "MP", "양천구": "YC",
    "강서구": "GS", "구로구": "GR", "금천구": "GC", "영등포구": "YD", "동작구": "DJ",
    "관악구": "GA", "서초구": "SC", "강남구": "GN", "송파구": "SP", "강동구": "GD",
}


class VWorldDiscoveryError(Exception):
    pass


def _monthly(base: float) -> List[float]:
    return [round(base * s, 2) for s in SEASON]


def _ring_area_sqm(ring: List[List[float]]) -> float:
    if len(ring) < 3:
        return 0.0
    lat0 = sum(p[1] for p in ring) / len(ring)
    m_per_deg_lat = 111_320.0
    m_per_deg_lng = 111_320.0 * math.cos(math.radians(lat0))
    pts = [(p[0] * m_per_deg_lng, p[1] * m_per_deg_lat) for p in ring]
    area = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def geometry_area_sqm(geometry: Optional[Dict[str, Any]]) -> float:
    if not geometry:
        return 0.0
    gtype = geometry.get("type")
    coords = geometry.get("coordinates") or []
    total = 0.0
    if gtype == "Polygon":
        if coords:
            total += _ring_area_sqm(coords[0])
    elif gtype == "MultiPolygon":
        for poly in coords:
            if poly:
                total += _ring_area_sqm(poly[0])
    return round(total, 1)


def geometry_centroid(geometry: Optional[Dict[str, Any]]) -> Tuple[float, float]:
    if not geometry:
        return 0.0, 0.0
    gtype = geometry.get("type")
    coords = geometry.get("coordinates") or []
    ring: List[List[float]] = []
    if gtype == "Polygon" and coords:
        ring = coords[0]
    elif gtype == "MultiPolygon" and coords and coords[0]:
        ring = coords[0][0]
    if not ring:
        return 0.0, 0.0
    lng = sum(p[0] for p in ring) / len(ring)
    lat = sum(p[1] for p in ring) / len(ring)
    return round(lat, 6), round(lng, 6)


def parse_address(addr: str) -> Tuple[str, str, str]:
    """'서울특별시 용산구 이태원동 347-2' → district, neighborhood, jibun."""
    text = (addr or "").strip()
    parts = text.split()
    district = parts[1] if len(parts) >= 2 else "서울"
    neighborhood = parts[2] if len(parts) >= 3 else district
    jibun = parts[3] if len(parts) >= 4 else ""
    if not neighborhood.endswith("동") and not neighborhood.endswith("가"):
        neighborhood = f"{neighborhood}동"
    return district, neighborhood, jibun


def classify_parcel_type(area_sqm: float, jibun: str) -> str:
    if area_sqm >= 1200:
        return "UNUSED_LAND"
    if area_sqm >= 600:
        return "VACANT_LOT"
    if "대" in jibun:
        return "VACANT_LOT"
    return "VACANT_LOT"


# 지목명 → 상세 카테고리 (landCategory)
LAND_CATEGORY_DETAIL: Dict[str, str] = {
    "대": "AGRICULTURE",
    "전": "AGRICULTURE",
    "과수원": "AGRICULTURE",
    "목장용지": "AGRICULTURE",
    "임야": "FOREST",
    "공장용지": "INDUSTRIAL",
    "학교용지": "COMMERCIAL",
    "관공서용지": "COMMERCIAL",
    "상업용지": "COMMERCIAL",
    "업무용지": "COMMERCIAL",
    "주택용지": "RESIDENTIAL",
    "아파트용지": "RESIDENTIAL",
    "공원": "PARK",
    "유원지": "PARK",
    "운동장": "PARK",
    "묘지": "CEMETERY",
    "도로": "INFRASTRUCTURE",
    "철도용지": "INFRASTRUCTURE",
    "제방": "INFRASTRUCTURE",
    "하천": "WATER",
    "구거": "WATER",
    "잡종지": "MIXED",
}

# 상세 카테고리/지목 → UI 호환 parcelType
# (프론트: VACANT_LOT | ROOFTOP | UNUSED_LAND | ABANDONED | BROWNFIELD)
LAND_CATEGORY_TO_UI_TYPE: Dict[str, str] = {
    "AGRICULTURE": "VACANT_LOT",
    "FOREST": "UNUSED_LAND",
    "INDUSTRIAL": "BROWNFIELD",
    "COMMERCIAL": "ABANDONED",
    "RESIDENTIAL": "VACANT_LOT",
    "PARK": "UNUSED_LAND",
    "CEMETERY": "UNUSED_LAND",
    "INFRASTRUCTURE": "UNUSED_LAND",
    "WATER": "UNUSED_LAND",
    "MIXED": "UNUSED_LAND",
}

# 하위 호환: 기존 이름 유지
LAND_CATEGORY_TO_PARCEL_TYPE = LAND_CATEGORY_DETAIL

UI_PARCEL_TYPES = frozenset({"VACANT_LOT", "ROOFTOP", "UNUSED_LAND", "ABANDONED", "BROWNFIELD"})


def _extract_lndcgr(items: List[Dict[str, Any]]) -> Optional[str]:
    if not items or not isinstance(items[0], dict):
        return None
    lndcgr = items[0].get("lndcgrCodeNm") or items[0].get("lndcgrCode") or ""
    lndcgr = str(lndcgr).strip()
    return lndcgr or None


def classify_land_category_from_characteristics(items: List[Dict[str, Any]]) -> Optional[str]:
    """지목 → 상세 landCategory (MIXED/FOREST 등)."""
    lndcgr = _extract_lndcgr(items)
    if not lndcgr:
        return None
    return LAND_CATEGORY_DETAIL.get(lndcgr)


def classify_parcel_type_from_land_characteristics(items: List[Dict[str, Any]]) -> Optional[str]:
    """지목 → UI 호환 parcelType (UNUSED_LAND 등).

    상세 지목은 landCategory 로 별도 제공. 하위 호환을 위해 함수명 유지.
    """
    detail = classify_land_category_from_characteristics(items)
    if not detail:
        return None
    return LAND_CATEGORY_TO_UI_TYPE.get(detail, "UNUSED_LAND")


def normalize_soil_type_for_api(soil_type: str) -> str:
    """백엔드 내부 SANDY 등을 프론트 SoilType(SAND)으로 정규화."""
    mapping = {
        "SANDY": "SAND",
        "SAND": "SAND",
        "LOAM": "LOAM",
        "CLAY": "CLAY",
        "ROCKY": "ROCKY",
        "UNKNOWN": "UNKNOWN",
    }
    return mapping.get((soil_type or "UNKNOWN").upper(), "UNKNOWN")


def settings_source(name: str, key: Optional[str]) -> str:
    """Return source label; append (미연동) when the API key is missing."""
    return name if key else f"{name} (미연동)"


def _is_visualcrossing_configured() -> bool:
    """Visual Crossing API 가 사용 가능한지 확인한다."""
    return bool(
        settings.visual_crossing_api_key
        and settings.visual_crossing_base_url
    )


def _vc_label(actual: bool, configured: bool) -> str:
    if actual:
        return "Visual Crossing"
    if configured:
        return "Visual Crossing (미조회/실패)"
    return "Visual Crossing (미연동)"


def build_data_provenance(
    data_source: str,
    *,
    regulations: Optional[List[Dict[str, Any]]] = None,
    parcel_type_actual: bool = False,
    ownership_actual: bool = False,
    soil_type_actual: bool = False,
    air_quality_actual: bool = False,
    solar_actual: bool = False,
    sunlight_actual: bool = False,
    heat_actual: bool = False,
    surface_temp_actual: bool = False,
    area_actual: bool = False,
    road_adjacent_actual: bool = False,
    households_actual: bool = False,
    water_access_actual: bool = False,
    electricity_access_actual: bool = False,
    monthly_irradiance_mode: str = "seasonal_model",
) -> Dict[str, Any]:
    """Build the dataProvenance map for a parcel response.

    actual 플래그는 **해당 필드에 실제 외부 데이터가 반영됐을 때만** True.
    API 키만 있고 조회에 실패하면 False + (미조회/실패) 라벨.
    """
    kma_configured = bool(settings.kma_api_key)
    vc_configured = _is_visualcrossing_configured()
    is_vworld = "VWorld" in (data_source or "")

    return {
        "boundary": {"source": "VWorld", "dataType": "지적도(연속지적도)", "actual": is_vworld},
        "location": {"source": "VWorld", "dataType": "좌표(EPSG:4326)", "actual": is_vworld},
        "areaSqm": {
            "source": "VWorld 토지특성(대장면적)" if area_actual else "VWorld 도형 면적",
            "dataType": "lndpclAr" if area_actual else "geometry 산출",
            "actual": is_vworld,
        },
        "regulations": {
            "source": "VWorld WFS+토지특성",
            "dataType": "규제/용도지역 레이어",
            "actual": is_vworld and bool(regulations),
        },
        "parcelType": {
            "source": "VWorld 토지특성정보" if parcel_type_actual else "GreenSpot",
            "dataType": "지목→UI유형" if parcel_type_actual else "면적 기반 분류",
            "actual": parcel_type_actual,
        },
        "ownership": {
            "source": "VWorld/국토부 토지소유정보" if ownership_actual else "GreenSpot",
            "dataType": "소유구분(실제)" if ownership_actual else "추정",
            "actual": ownership_actual,
        },
        "soilType": {
            "source": "농촌진흥청 토양정보" if soil_type_actual else "GreenSpot",
            "dataType": "토성(실제)" if soil_type_actual else "추정",
            "actual": soil_type_actual,
        },
        "solarIrradiance": {
            "source": _vc_label(solar_actual, vc_configured),
            "dataType": "일사량(kWh/㎡/day)" if solar_actual else "자치구 hash 추정",
            "actual": solar_actual,
        },
        "sunlightHours": {
            "source": _vc_label(sunlight_actual, vc_configured),
            "dataType": "일조시간" if sunlight_actual else "일사량 기반 추정",
            "actual": sunlight_actual,
        },
        "monthlyIrradiance": {
            "source": "GreenSpot",
            "dataType": "연간일사×계절계수 (월별 실측 아님)",
            "actual": False,
        },
        "heatIsland": {
            "source": _vc_label(heat_actual, vc_configured),
            "dataType": "기온 기반 추정" if heat_actual else "위도 기반 추정",
            "actual": heat_actual,
        },
        "surfaceTempSummer": {
            "source": _vc_label(surface_temp_actual, vc_configured),
            "dataType": "기온+오프셋 추정" if surface_temp_actual else "위도 기반 추정",
            "actual": surface_temp_actual,
        },
        "airQuality": {
            "source": "AirKorea" if air_quality_actual else "GreenSpot",
            "dataType": "PM2.5(실제)" if air_quality_actual else "추정",
            "actual": air_quality_actual,
        },
        "roadAdjacent": {
            "source": "VWorld 토지특성(접면도로)" if road_adjacent_actual else "GreenSpot",
            "dataType": "roadSideCode" if road_adjacent_actual else "추정",
            "actual": road_adjacent_actual,
        },
        "waterAccess": {
            "source": "GreenSpot",
            "dataType": "도로인접 기반 추정" if not water_access_actual else "실측",
            "actual": water_access_actual,
        },
        "electricityAccess": {
            "source": "GreenSpot",
            "dataType": "도시지역 기본 가정",
            "actual": electricity_access_actual,
        },
        "nearbyHouseholds": {
            "source": "KOSIS" if households_actual else "GreenSpot",
            "dataType": "자치구 총가구" if households_actual else "미제공",
            "actual": households_actual,
        },
        "scores": {
            "source": "GreenSpot",
            "dataType": "알고리즘(입력 일부 추정 가능)",
            "actual": True,
        },
        "sumokFeasibility": {"source": "GreenSpot", "dataType": "규제 기반 수목 식재 가능성", "actual": True},
        # legacy health-check 호환
        "kmaApiKeyConfigured": kma_configured,
        "visualCrossingConfigured": vc_configured,
    }


def regulations_for_seed(regs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for reg in regs:
        code = reg.get("regulationType") or reg.get("code")
        out.append({
            "code": code,
            "name": reg.get("regulationName") or reg.get("name") or code,
            "severity": reg.get("severity", "info"),
            "affectedUses": reg.get("affectedUses", ["sumok"]),
            "penaltyType": reg.get("penaltyType", "none"),
            "penaltyValue": reg.get("penaltyValue"),
            "legalBasis": reg.get("legalBasis", ""),
            "description": reg.get("description", ""),
        })
    return out


def _zoning_severity(name: str) -> str:
    """용도지역명 → severity. 자연녹지 등은 warning."""
    n = name or ""
    if any(k in n for k in ("자연녹지", "보전녹지", "생산녹지", "개발제한", "녹지지역")):
        return "warning"
    if any(k in n for k in ("전용주거", "일반주거", "준주거", "상업", "공업", "관리지역")):
        return "info"
    return "info"


def zoning_regulations_from_land_chars(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """토지특성의 용도지역(prposArea*)을 규제 항목으로 변환."""
    if not items or not isinstance(items[0], dict):
        return []
    item = items[0]
    regs: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for name_key, code_key in (
        ("prposArea1Nm", "prposArea1"),
        ("prposArea2Nm", "prposArea2"),
    ):
        name = str(item.get(name_key) or "").strip()
        code_raw = str(item.get(code_key) or "").strip()
        if not name:
            continue
        code = f"ZONING_{code_raw}" if code_raw else f"ZONING_{name}"
        if code in seen:
            continue
        seen.add(code)
        sev = _zoning_severity(name)
        regs.append({
            "regulationType": code,
            "regulationName": name,
            "severity": sev,
            "affectedUses": ["sumok", "garden", "solar"],
            "penaltyType": "none",
            "penaltyValue": 0.0,
            "legalBasis": "국토의 계획 및 이용에 관한 법률",
            "description": f"토지특성 용도지역: {name}"
            + (" — 행위 제한·인허가 확인 권장" if sev == "warning" else ""),
        })
    return regs


def primary_regulation_code(regs: List[Dict[str, Any]]) -> str:
    if not regs:
        return "NONE"
    order = {"prohibited": 0, "restricted": 1, "warning": 2, "info": 3}

    def _rank(r: Dict[str, Any]) -> Tuple[int, int]:
        sev = order.get(r.get("severity", "info"), 9)
        code = str(r.get("regulationType") or r.get("code") or "")
        # 동일 severity 면 URBAN_ZONE 보다 구체 용도지역 우선
        specificity = 1 if code == "URBAN_ZONE" else 0
        return (sev, specificity)

    regs_sorted = sorted(regs, key=_rank)
    return regs_sorted[0].get("regulationType") or regs_sorted[0].get("code") or "NONE"


def base_environment(district: str, area_sqm: float, lat: float) -> Dict[str, Any]:
    """부지의 기본 환경값(추정). VC/AirKorea 등으로 이후 덮어쓴다.

    사회·접근성(학교/병원 등)은 가짜 hash 값을 넣지 않는다.
    """
    solar = round(3.6 + (abs(hash(district)) % 7) * 0.1, 1)
    heat = round(2.0 + (1.0 - (lat - 37.42) / 0.3) * 1.5, 1)
    heat = max(1.5, min(4.5, heat))
    return {
        "solar_irradiance": solar,
        "monthly_irradiance": _monthly(solar),
        "sunlight_hours": round(5.0 + solar * 0.35, 1),
        "heat_island": heat,
        "surface_temp_summer": round(33.0 + heat * 1.4, 1),
        "air_quality": 20 + (abs(hash(district)) % 15),
        # 접근성: 미연동 시 null (0 위장 금지)
        "nearby_households": None,
        "pedestrian_flow": None,
        "nearby_schools": None,
        "nearby_hospitals": None,
        "nearby_parks": None,
        "nearby_subway_stations": None,
        # 인프라: 보수적 기본값 (토지특성으로 보정)
        "road_adjacent": False,
        "water_access": False,
        "electricity_access": True,  # 서울 시가지 기본 가정
    }


# VC 429 시 일정 시간 스킵 (초)
_VC_COOLDOWN_UNTIL: float = 0.0
_VC_COOLDOWN_SEC = 1800.0  # 30분


async def enrich_environment_with_visualcrossing(
    env: Dict[str, Any],
    district: str,
    *,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
) -> Dict[str, bool]:
    """VC로 일사/일조/열섬 보강.

    - 일사+기온을 **한 번의 climate 호출**로 처리 (쿼터·지연 절감)
    - district 단위 TTL 캐시
    - 429 시 쿨다운
    """
    import time

    from app.services.ttl_cache import cache_get, cache_set
    from app.services.visual_crossing_service import (
        URBAN_SURFACE_OFFSET_C,
        HEAT_ISLAND_BASELINE_C,
        VisualCrossingRateLimited,
        client as vc_client,
    )

    flags = {
        "solar_actual": False,
        "sunlight_actual": False,
        "heat_actual": False,
        "surface_temp_actual": False,
    }
    global _VC_COOLDOWN_UNTIL
    if not _is_visualcrossing_configured():
        return flags
    if time.monotonic() < _VC_COOLDOWN_UNTIL:
        return flags

    # district 캐시 (좌표보다 재사용성 높음)
    cache_key = f"vc:climate:{district}"
    climate = cache_get(cache_key)
    if climate is None:
        try:
            # 자치구명 location 사용 (동일 구 재조회 캐시 효율)
            climate = await vc_client().get_climate_for_district(district)
            cache_set(cache_key, climate, ttl_sec=3600.0)
        except VisualCrossingRateLimited:
            _VC_COOLDOWN_UNTIL = time.monotonic() + _VC_COOLDOWN_SEC
            return flags
        except Exception:
            return flags

    if not isinstance(climate, dict) or not climate.get("dataAvailable"):
        return flags

    solar = climate.get("solarIrradiance")
    if solar is not None and float(solar) > 0:
        env["solar_irradiance"] = round(float(solar), 2)
        env["monthly_irradiance"] = _monthly(float(solar))
        flags["solar_actual"] = True

    sun_h = climate.get("sunlightHours")
    if sun_h is not None and float(sun_h) > 0:
        env["sunlight_hours"] = round(float(sun_h), 2)
        flags["sunlight_actual"] = True
    elif flags["solar_actual"]:
        env["sunlight_hours"] = round(5.0 + float(env["solar_irradiance"]) * 0.35, 2)
        flags["sunlight_actual"] = False

    # 최근 기온으로 열섬/지표면 온도 파생 (별도 summer timeline 호출 생략)
    avg_temp = climate.get("avgTemperature")
    if avg_temp is not None:
        try:
            t = float(avg_temp)
            env["heat_island"] = round(max(0.0, t - HEAT_ISLAND_BASELINE_C), 2)
            env["surface_temp_summer"] = round(t + URBAN_SURFACE_OFFSET_C, 2)
            flags["heat_actual"] = True
            flags["surface_temp_actual"] = True
        except (TypeError, ValueError):
            pass

    return flags


def _area_score_component(area_sqm: float, cap: float = 22.0) -> float:
    """면적 기여 — log 스케일로 천장 방지 (1만㎡≈20, 5만㎡≈cap)."""
    return min(cap, max(0.0, math.log10(max(area_sqm, 50.0)) * 8.0))


def compute_base_scores(
    area_sqm: float,
    parcel_type: str,
    env: Dict[str, Any],
    *,
    actual_flags: Optional[Dict[str, bool]] = None,
) -> Dict[str, Any]:
    """면적 상한 폭주/ped 의존을 제거한 점수 산출."""
    solar = float(env.get("solar_irradiance") or 0)
    heat = float(env.get("heat_island") or 0)
    soil = str(env.get("_soil_type_for_score") or env.get("soil_type") or "UNKNOWN").upper()
    road = bool(env.get("road_adjacent"))
    air = env.get("air_quality")
    try:
        air_f = float(air) if air is not None else 25.0
    except (TypeError, ValueError):
        air_f = 25.0

    area_c = _area_score_component(area_sqm)
    soil_tree_bonus = 6 if soil in ("LOAM", "SAND", "SANDY") else (0 if soil == "UNKNOWN" else 2)
    soil_garden_bonus = 10 if soil == "LOAM" else (4 if soil in ("SAND", "SANDY", "CLAY") else 0)
    air_bonus = 4 if air_f <= 15 else (2 if air_f <= 35 else 0)
    road_bonus = 4 if road else 0
    rooftop_solar = 16 if parcel_type == "ROOFTOP" else 0
    type_tree = {"VACANT_LOT": 6, "UNUSED_LAND": 8, "BROWNFIELD": 2, "ABANDONED": 1, "ROOFTOP": -8}.get(parcel_type, 3)
    type_garden = {"VACANT_LOT": 8, "UNUSED_LAND": 6, "ROOFTOP": 4, "BROWNFIELD": 0, "ABANDONED": 2}.get(parcel_type, 3)

    tree = int(round(38 + heat * 4.5 + area_c * 0.9 + soil_tree_bonus + air_bonus + type_tree))
    garden = int(round(34 + area_c * 1.0 + soil_garden_bonus + road_bonus + type_garden + air_bonus * 0.5))
    solar_s = int(round(30 + solar * 10.5 + rooftop_solar + road_bonus + min(8.0, area_c * 0.25)))

    tree = max(18, min(92, tree))
    garden = max(18, min(92, garden))
    solar_s = max(18, min(92, solar_s))

    flags = actual_flags or {}
    known = sum(1 for k in (
        "parcel_type_actual", "ownership_actual", "soil_actual", "air_actual",
        "solar_actual", "heat_actual",
    ) if flags.get(k))
    uncertainty = int(max(3, round(11 - known * 1.2)))

    tree_bd = [
        f"열섬 {heat:.1f}℃ 기여",
        f"면적 log기여 {area_c:.1f}",
        f"토양 {soil} 가산 {soil_tree_bonus}",
        f"유형 {parcel_type} 가산 {type_tree}",
    ]
    garden_bd = [
        f"면적 log기여 {area_c:.1f}",
        f"토양 {soil} 가산 {soil_garden_bonus}",
        f"도로인접 {'Y' if road else 'N'}",
        f"유형 {parcel_type}",
    ]
    solar_bd = [
        f"일사량 {solar:.2f} kWh/㎡/day",
        f"옥상 가산 {rooftop_solar}",
        f"도로인접 {'Y' if road else 'N'}",
    ]

    scores = {"TREE": tree, "GARDEN": garden, "SOLAR": solar_s}
    top = max(scores, key=scores.get)
    return {
        "tree_score": tree,
        "garden_score": garden,
        "solar_score": solar_s,
        "top_recommendation": top,
        "uncertainty": uncertainty,
        "tree_breakdown": tree_bd,
        "garden_breakdown": garden_bd,
        "solar_breakdown": solar_bd,
    }


def finalize_scores(
    base_scores: Dict[str, Any],
    regulations: List[Dict[str, Any]],
    confidence: float = 0.86,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    applied = apply_regulation_penalties(
        {
            "sumokScore": float(base_scores["tree_score"]),
            "gardenScore": float(base_scores["garden_score"]),
            "solarScore": float(base_scores["solar_score"]),
        },
        regulations,
    )
    feasibility = compute_sumok_feasibility(applied["sumokScore"], regulations, confidence)
    scores = {
        "tree_score": int(round(applied["sumokScore"])),
        "garden_score": int(round(applied["gardenScore"])),
        "solar_score": int(round(applied["solarScore"])),
        "top_recommendation": base_scores["top_recommendation"],
        "uncertainty": base_scores["uncertainty"],
        "tree_breakdown": list(base_scores.get("tree_breakdown") or []),
        "garden_breakdown": list(base_scores.get("garden_breakdown") or []),
        "solar_breakdown": list(base_scores.get("solar_breakdown") or []),
    }
    # 규제 패널티가 있으면 breakdown 에 표시
    if scores["tree_score"] != base_scores["tree_score"]:
        scores["tree_breakdown"].append(
            f"규제 반영 {base_scores['tree_score']}→{scores['tree_score']}"
        )
    rec_values = {
        "TREE": scores["tree_score"],
        "GARDEN": scores["garden_score"],
        "SOLAR": scores["solar_score"],
    }
    if feasibility["status"] == "PROHIBITED":
        scores["top_recommendation"] = "GARDEN" if scores["garden_score"] >= scores["solar_score"] else "SOLAR"
    else:
        scores["top_recommendation"] = max(rec_values, key=rec_values.get)
    return scores, feasibility


def _confidence_from_flags(flags: Dict[str, bool]) -> float:
    keys = (
        "parcel_type_actual", "ownership_actual", "soil_actual", "air_actual",
        "solar_actual", "heat_actual", "area_actual",
    )
    n = sum(1 for k in keys if flags.get(k))
    return round(min(0.97, 0.58 + n * 0.055), 2)


def _infra_from_land_chars(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """접면도로 등으로 road_adjacent 보정."""
    out = {"road_adjacent": False, "road_adjacent_actual": False}
    if not items or not isinstance(items[0], dict):
        return out
    item = items[0]
    road_nm = str(item.get("roadSideCodeNm") or "").strip()
    road_cd = str(item.get("roadSideCode") or "").strip()
    if road_nm and road_nm not in ("지정되지않음", "해당없음", "-"):
        out["road_adjacent"] = True
        out["road_adjacent_actual"] = True
    elif road_cd and road_cd not in ("00", "0", ""):
        out["road_adjacent"] = True
        out["road_adjacent_actual"] = True
    return out


def _cadastral_area_sqm(items: List[Dict[str, Any]]) -> Optional[float]:
    if not items or not isinstance(items[0], dict):
        return None
    raw = items[0].get("lndpclAr")
    if raw in (None, ""):
        return None
    try:
        val = float(str(raw).replace(",", ""))
        return round(val, 1) if val > 0 else None
    except (TypeError, ValueError):
        return None


class VWorldDataClient:
    def __init__(self, api_key: Optional[str] = None, domain: Optional[str] = None):
        self.api_key = (api_key or settings.vworld_api_key or "").strip()
        self.domain = (domain or settings.vworld_domain or "localhost").strip()

    def _check_key(self):
        if not self.api_key:
            raise VWorldDiscoveryError("VWORLD_API_KEY가 설정되지 않았습니다.")

    async def _get(
        self,
        client: httpx.AsyncClient,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._check_key()
        base = {
            "service": "data",
            "version": "2.0",
            "request": "GetFeature",
            "key": self.api_key,
            "domain": self.domain,
            "format": "json",
        }
        base.update(params)
        last_exc: Optional[Exception] = None
        for attempt in range(3):
            try:
                resp = await client.get(VWORLD_DATA_URL, params=base)
                if resp.status_code in (502, 503, 504) and attempt < 2:
                    await asyncio.sleep(0.4 * (attempt + 1))
                    continue
                resp.raise_for_status()
                payload = resp.json()
                response = payload.get("response") or {}
                status = response.get("status")
                if status == "ERROR":
                    err = response.get("error") or {}
                    raise VWorldDiscoveryError(err.get("text") or "VWorld API error")
                return response
            except VWorldDiscoveryError:
                raise
            except httpx.HTTPError as e:
                last_exc = e
                code = getattr(getattr(e, "response", None), "status_code", None)
                if code in (502, 503, 504) and attempt < 2:
                    await asyncio.sleep(0.4 * (attempt + 1))
                    continue
                raise VWorldDiscoveryError(
                    f"VWorld API 연결 실패 (HTTP {code or 'network'}). "
                    "VWORLD_API_KEY / VWORLD_DOMAIN 을 확인하세요."
                ) from e
        raise VWorldDiscoveryError(
            f"VWorld API 연결 실패: {type(last_exc).__name__ if last_exc else 'unknown'}"
        )

    async def fetch_seoul_emd_codes(self) -> List[str]:
        min_lng, min_lat, max_lng, max_lat = SEOUL_BBOX
        geom = f"BOX({min_lng},{min_lat},{max_lng},{max_lat})"
        codes: List[str] = []
        page = 1
        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                response = await self._get(client, {
                    "data": EMD_DATA,
                    "size": 100,
                    "page": page,
                    "geomFilter": geom,
                    "geometry": "false",
                    "attribute": "true",
                    "crs": "EPSG:4326",
                })
                if response.get("status") != "OK":
                    break
                feats = (
                    response.get("result", {})
                    .get("featureCollection", {})
                    .get("features", [])
                )
                for feat in feats:
                    emd_cd = str((feat.get("properties") or {}).get("emd_cd", ""))
                    if emd_cd.startswith("11") and len(emd_cd) >= 8:
                        codes.append(emd_cd)
                total = int((response.get("record") or {}).get("total", 0))
                if page * 100 >= total:
                    break
                page += 1
        return sorted(set(codes))

    async def fetch_cadastral_by_emd(
        self,
        emd_cd: str,
        *,
        page: int = 1,
        size: int = 100,
    ) -> Tuple[List[Dict[str, Any]], int]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await self._get(client, {
                "data": CADASTral_DATA,
                "size": size,
                "page": page,
                "attrFilter": f"emdCd:=:{emd_cd}",
                "geometry": "true",
                "attribute": "true",
                "crs": "EPSG:4326",
            })
        if response.get("status") != "OK":
            return [], 0
        feats = (
            response.get("result", {})
            .get("featureCollection", {})
            .get("features", [])
        )
        total = int((response.get("record") or {}).get("total", 0))
        return feats, total


async def _cached_call(
    cache_key: str,
    ttl: float,
    coro_factory,
    *,
    cache_if=None,
):
    """TTL 캐시 조회 후 없으면 코루틴 실행.

    cache_if: 캐시 저장 여부 판별 callable(value)->bool. None 이면 항상 저장.
    """
    from app.services.ttl_cache import cache_get, cache_set

    hit = cache_get(cache_key)
    if hit is not None:
        return hit
    value = await coro_factory()
    if cache_if is None or cache_if(value):
        cache_set(cache_key, value, ttl_sec=ttl)
    return value


async def build_parcel_from_feature(
    feature: Dict[str, Any],
    *,
    enrich_regulations: bool = True,
) -> Optional[Dict[str, Any]]:
    props = feature.get("properties") or {}
    geometry = feature.get("geometry")
    pnu = str(props.get("pnu") or "").strip()
    if not pnu:
        return None

    geom_area = geometry_area_sqm(geometry)
    if geom_area < 200:
        return None

    lat, lng = geometry_centroid(geometry)
    if lat == 0.0 and lng == 0.0:
        return None

    addr = props.get("addr") or ""
    district, neighborhood, jibun = parse_address(addr)
    if not (district.endswith("구") or district.endswith("시")):
        return None

    # ---- 독립 외부 API 병렬 조회 ----
    async def _land():
        return await _cached_call(
            f"vworld:land:{pnu}",
            1800.0,
            lambda: vworld_client().get_land_characteristics(pnu),
            cache_if=lambda v: isinstance(v, dict) and bool(v.get("dataAvailable") or v.get("items")),
        )

    async def _owner():
        return await _cached_call(
            f"own:{pnu}",
            1800.0,
            lambda: land_ownership_client().get_ownership(pnu, fallback="UNKNOWN"),
            cache_if=lambda v: isinstance(v, dict) and bool(v.get("dataAvailable")),
        )

    async def _soil():
        return await _cached_call(
            f"soil:{pnu}",
            1800.0,
            lambda: soil_client().get_soil_type(pnu, fallback="UNKNOWN"),
            cache_if=lambda v: isinstance(v, dict) and bool(v.get("dataAvailable")),
        )

    async def _air():
        return await _cached_call(
            f"air:{district}",
            600.0,
            lambda: airkorea_client().get_air_quality(district, fallback=None),
            cache_if=lambda v: isinstance(v, dict) and bool(v.get("dataAvailable")),
        )

    async def _regs():
        if not enrich_regulations:
            return []
        return await _cached_call(
            f"regs:{round(lat, 4)}:{round(lng, 4)}",
            900.0,
            lambda: vworld_client().get_regulations_at_point(lat, lng),
            cache_if=lambda v: isinstance(v, list) and len(v) > 0,
        )

    async def _hh():
        try:
            from app.services.kosis_service import DISTRICT_TO_OBJ_L1, client as kosis_client

            if district not in DISTRICT_TO_OBJ_L1 or not settings.kosis_api_key:
                return None
            return await _cached_call(
                f"kosis:hh:{district}",
                86400.0,
                lambda: kosis_client().get_household(district),
                cache_if=lambda v: isinstance(v, dict) and bool(v.get("dataAvailable")),
            )
        except Exception:
            return None

    land_r, owner_r, soil_r, air_r, regs_r, hh_r = await asyncio.gather(
        _land(),
        _owner(),
        _soil(),
        _air(),
        _regs(),
        _hh(),
        return_exceptions=True,
    )

    # 토지특성
    parcel_type_actual = False
    land_category: Optional[str] = None
    land_items: List[Dict[str, Any]] = []
    area_sqm = geom_area
    area_actual = False
    if not isinstance(land_r, Exception) and isinstance(land_r, dict):
        land_items = list(land_r.get("items") or [])
        land_category = classify_land_category_from_characteristics(land_items)
        ui_type = classify_parcel_type_from_land_characteristics(land_items)
        if ui_type:
            parcel_type = ui_type
            parcel_type_actual = True
        else:
            parcel_type = classify_parcel_type(area_sqm, jibun)
        cad_area = _cadastral_area_sqm(land_items)
        if cad_area is not None:
            area_sqm = cad_area
            area_actual = True
    else:
        parcel_type = classify_parcel_type(area_sqm, jibun)

    # 소유
    ownership = "UNKNOWN"
    ownership_actual = False
    if not isinstance(owner_r, Exception) and isinstance(owner_r, dict):
        if owner_r.get("dataAvailable") and owner_r.get("ownership"):
            ownership = owner_r["ownership"]
            ownership_actual = True

    # 토양
    soil_type = "UNKNOWN"
    soil_type_actual = False
    if not isinstance(soil_r, Exception) and isinstance(soil_r, dict):
        if soil_r.get("dataAvailable") and soil_r.get("soilType"):
            soil_type = normalize_soil_type_for_api(str(soil_r["soilType"]))
            soil_type_actual = True

    env = base_environment(district, area_sqm, lat)
    env["_soil_type_for_score"] = soil_type

    infra = _infra_from_land_chars(land_items)
    env["road_adjacent"] = bool(infra.get("road_adjacent"))
    road_adjacent_actual = bool(infra.get("road_adjacent_actual"))
    env["electricity_access"] = True  # 도시 기본 가정 (actual=false)
    env["water_access"] = bool(env["road_adjacent"])  # 추정 (actual=false)

    # AirKorea
    air_quality_actual = False
    if not isinstance(air_r, Exception) and isinstance(air_r, dict):
        if air_r.get("dataAvailable") and air_r.get("pm25") is not None:
            env["air_quality"] = air_r["pm25"]
            air_quality_actual = True

    # KOSIS
    households_actual = False
    if not isinstance(hh_r, Exception) and isinstance(hh_r, dict):
        if hh_r.get("dataAvailable") and hh_r.get("households") is not None:
            env["nearby_households"] = int(hh_r["households"])
            households_actual = True

    # VC (캐시·쿨다운 포함, 내부 1회 호출)
    vc_flags = await enrich_environment_with_visualcrossing(env, district, lat=lat, lng=lng)

    actual_flags = {
        "parcel_type_actual": parcel_type_actual,
        "ownership_actual": ownership_actual,
        "soil_actual": soil_type_actual,
        "air_actual": air_quality_actual,
        "solar_actual": vc_flags.get("solar_actual", False),
        "heat_actual": vc_flags.get("heat_actual", False),
        "area_actual": area_actual,
    }
    base_scores = compute_base_scores(
        area_sqm, parcel_type, env, actual_flags=actual_flags
    )

    regulations: List[Dict[str, Any]] = []
    if not isinstance(regs_r, Exception) and isinstance(regs_r, list):
        regulations = list(regs_r)
    regulations = regulations + zoning_regulations_from_land_chars(land_items)

    confidence = _confidence_from_flags(actual_flags)
    scores, feasibility = finalize_scores(base_scores, regulations, confidence=confidence)
    reg_seed = regulations_for_seed(regulations)
    seen_reg_codes: set[str] = set()
    deduped_reg_seed: List[Dict[str, Any]] = []
    for reg in reg_seed:
        code = reg.get("code")
        if code in seen_reg_codes:
            continue
        seen_reg_codes.add(code)
        deduped_reg_seed.append(reg)
    reg_seed = deduped_reg_seed
    parcel_id = f"VW-{pnu}"

    label = jibun or props.get("jibun") or "필지"
    name = f"{neighborhood} {label} 부지".replace("  ", " ")

    env.pop("_soil_type_for_score", None)

    return {
        "id": parcel_id,
        "name": name,
        "district": district,
        "neighborhood": neighborhood,
        "lat": lat,
        "lng": lng,
        "area_sqm": area_sqm,
        "parcel_type": parcel_type,
        "land_category": land_category,
        "ownership": ownership,
        "soil_type": soil_type,
        **env,
        "regulatory_restriction": primary_regulation_code(reg_seed),
        "regulations": reg_seed,
        "sumok_feasibility": feasibility,
        "confidence": confidence,
        "scores": scores,
        "pnu": pnu,
        "vworld_addr": addr,
        "data_source": "VWorld/LP_PA_CBND_BUBUN",
        "data_provenance": build_data_provenance(
            "VWorld/LP_PA_CBND_BUBUN",
            regulations=reg_seed,
            parcel_type_actual=parcel_type_actual,
            ownership_actual=ownership_actual,
            soil_type_actual=soil_type_actual,
            air_quality_actual=air_quality_actual,
            solar_actual=vc_flags.get("solar_actual", False),
            sunlight_actual=vc_flags.get("sunlight_actual", False),
            heat_actual=vc_flags.get("heat_actual", False),
            surface_temp_actual=vc_flags.get("surface_temp_actual", False),
            area_actual=area_actual,
            road_adjacent_actual=road_adjacent_actual,
            households_actual=households_actual,
            water_access_actual=False,
            electricity_access_actual=False,
        ),
    }


async def discover_seoul_parcels(
    *,
    min_area_sqm: float = 300,
    max_area_sqm: float = 15_000,
    per_emd: int = 2,
    max_pages_per_emd: int = 2,
    page_size: int = 100,
    enrich_regulations: bool = True,
    regulation_concurrency: int = 4,
    progress_cb=None,
) -> List[Dict[str, Any]]:
    """
    서울 읍면동 단위로 연속지적도를 조회해 GreenSpot 후보 부지를 수집한다.
    """
    data_client = VWorldDataClient()
    emd_codes = await data_client.fetch_seoul_emd_codes()
    candidates: List[Dict[str, Any]] = []
    seen_pnu: set[str] = set()
    sem = asyncio.Semaphore(regulation_concurrency)

    async def enrich_one(feat: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        async with sem:
            row = await build_parcel_from_feature(feat, enrich_regulations=enrich_regulations)
            return row

    for idx, emd_cd in enumerate(emd_codes):
        emd_picks: List[Dict[str, Any]] = []
        for page in range(1, max_pages_per_emd + 1):
            feats, total = await data_client.fetch_cadastral_by_emd(
                emd_cd, page=page, size=page_size
            )
            if not feats:
                break
            for feat in feats:
                props = feat.get("properties") or {}
                pnu = str(props.get("pnu") or "")
                if not pnu or pnu in seen_pnu:
                    continue
                area = geometry_area_sqm(feat.get("geometry"))
                if area < min_area_sqm or area > max_area_sqm:
                    continue
                emd_picks.append({**feat, "_area": area})
            if page * page_size >= total:
                break
            await asyncio.sleep(0.05)

        emd_picks.sort(key=lambda f: f.get("_area", 0), reverse=True)
        selected = emd_picks[:per_emd]
        if selected:
            tasks = [enrich_one(f) for f in selected]
            rows = await asyncio.gather(*tasks)
            for row in rows:
                if row and row.get("pnu") not in seen_pnu:
                    seen_pnu.add(row["pnu"])
                    candidates.append(row)

        if progress_cb:
            progress_cb(idx + 1, len(emd_codes), len(candidates))
        await asyncio.sleep(0.08)

    candidates.sort(key=lambda p: (p["district"], -p["area_sqm"]))
    return candidates