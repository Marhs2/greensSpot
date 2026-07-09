# -*- coding: utf-8 -*-
"""
기존 seed_data.json(5개 자치구)에 서울 25개 자치구 부지를 보강한다.
각 미등록 자치구에 2개 부지를 추가해 '용산구' 등 전 구역 검색이 가능하게 한다.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

DATA_PATH = Path(__file__).parent / "seed_data.json"

# 서울 25개 자치구 (대략 중심 좌표)
SEOUL_DISTRICTS: dict[str, tuple[float, float]] = {
    "종로구": (37.5735, 126.9790),
    "중구": (37.5640, 126.9970),
    "용산구": (37.5320, 126.9900),
    "성동구": (37.5500, 127.0400),
    "광진구": (37.5385, 127.0820),
    "동대문구": (37.5740, 127.0400),
    "중랑구": (37.6060, 127.0930),
    "성북구": (37.5890, 127.0190),
    "강북구": (37.6390, 127.0260),
    "도봉구": (37.6680, 127.0470),
    "노원구": (37.6540, 127.0610),
    "은평구": (37.6020, 126.9290),
    "서대문구": (37.5790, 126.9370),
    "마포구": (37.5660, 126.9020),
    "양천구": (37.5170, 126.8660),
    "강서구": (37.5500, 126.8500),
    "구로구": (37.4950, 126.8870),
    "금천구": (37.4560, 126.8950),
    "영등포구": (37.5260, 126.8960),
    "동작구": (37.5120, 126.9400),
    "관악구": (37.4780, 126.9520),
    "서초구": (37.4830, 127.0320),
    "강남구": (37.5170, 127.0470),
    "송파구": (37.5140, 127.1060),
    "강동구": (37.5300, 127.1240),
}

DISTRICT_PREFIX = {
    "종로구": "JR", "중구": "JG", "용산구": "YS", "성동구": "SD", "광진구": "GJ",
    "동대문구": "DD", "중랑구": "JL", "성북구": "SB", "강북구": "GB", "도봉구": "DB",
    "노원구": "NW", "은평구": "EP", "서대문구": "SM", "마포구": "MP", "양천구": "YC",
    "강서구": "GS", "구로구": "GR", "금천구": "GC", "영등포구": "YD", "동작구": "DJ",
    "관악구": "GA", "서초구": "SC", "강남구": "GN", "송파구": "SP", "강동구": "GD",
}

NEIGHBORHOODS: dict[str, list[str]] = {
    "용산구": ["이태원동", "한남동", "서빙고동", "청파동"],
    "종로구": ["종로1가", "혜화동", "삼청동", "이화동"],
    "광진구": ["자양동", "구의동", "화양동", "군자동"],
    "중랑구": ["면목동", "상봉동", "망우동", "중화동"],
    "성북구": ["성북동", "길음동", "정릉동", "돈암동"],
    "강북구": ["수유동", "미아동", "번동", "우이동"],
    "도봉구": ["쌍문동", "방학동", "창동", "도봉동"],
    "노원구": ["상계동", "중계동", "하계동", "공릉동"],
    "은평구": ["불광동", "응암동", "갈현동", "녹번동"],
    "서대문구": ["연희동", "홍제동", "남가좌동", "북아현동"],
    "양천구": ["목동", "신정동", "신월동", "목1동"],
    "강서구": ["화곡동", "등촌동", "가양동", "방화동"],
    "구로구": ["구로동", "신도림동", "개봉동", "고척동"],
    "금천구": ["가산동", "독산동", "시흥동", "독산1동"],
    "영등포구": ["여의도동", "당산동", "대림동", "신길동"],
    "동작구": ["노량진동", "사당동", "상도동", "흑석동"],
    "관악구": ["신림동", "봉천동", "남현동", "서원동"],
    "서초구": ["반포동", "서초동", "방배동", "잠원동"],
    "송파구": ["잠실동", "문정동", "가락동", "방이동"],
    "강동구": ["천호동", "길동", "둔촌동", "암사동"],
}

PARCEL_TYPES = [
    ("VACANT_LOT", "빈터", "LOAM", "PUBLIC"),
    ("ROOFTOP", "옥상", "UNKNOWN", "PRIVATE"),
    ("UNUSED_LAND", "유휴지", "SAND", "PUBLIC"),
    ("ROOFTOP", "옥상", "UNKNOWN", "PUBLIC"),
]

SEASON = [0.55, 0.72, 0.9, 1.08, 1.18, 1.13, 1.03, 0.98, 0.86, 0.72, 0.58, 0.5]


def monthly(base: float) -> list[float]:
    return [round(base * s, 2) for s in SEASON]


def simple_scores(area: float, ptype: str, solar: float, heat: float, ped: int) -> dict:
    tree = min(95, int(40 + heat * 8 + ped / 200 + area / 50))
    garden = min(95, int(35 + area / 40 + ped / 300))
    solar_s = min(95, int(30 + solar * 12 + (25 if ptype == "ROOFTOP" else 0)))
    if ptype == "ROOFTOP":
        solar_s += 15
    scores = {"TREE": tree, "GARDEN": garden, "SOLAR": solar_s}
    top = max(scores, key=scores.get)
    return {
        "tree_score": scores["TREE"],
        "garden_score": scores["GARDEN"],
        "solar_score": scores["SOLAR"],
        "top_recommendation": top,
        "uncertainty": 5,
    }


def make_parcel(
    district: str,
    idx: int,
    ptype: str,
    label: str,
    soil: str,
    ownership: str,
    lat: float,
    lng: float,
) -> dict:
    prefix = DISTRICT_PREFIX[district]
    nb = (NEIGHBORHOODS.get(district) or [f"{district[:-1]}동"])[idx % 4]
    pid = f"{prefix}-{idx:03d}"
    area = 280 + (idx * 137) % 900
    solar = round(3.6 + (idx % 5) * 0.2, 1)
    heat = round(1.8 + (idx % 6) * 0.3, 1)
    ped = 1800 + idx * 420
    scores = simple_scores(area, ptype, solar, heat, ped)
    top = scores["top_recommendation"]
    feas_score = scores["tree_score"]
    return {
        "id": pid,
        "name": f"{nb} {label}",
        "district": district,
        "neighborhood": nb,
        "lat": round(lat, 4),
        "lng": round(lng, 4),
        "area_sqm": area,
        "parcel_type": ptype,
        "ownership": ownership,
        "soil_type": soil,
        "solar_irradiance": solar,
        "monthly_irradiance": monthly(solar),
        "sunlight_hours": round(5.0 + solar * 0.35, 1),
        "heat_island": heat,
        "surface_temp_summer": round(33.0 + heat * 1.2, 1),
        "air_quality": 22 + (idx % 8),
        "nearby_households": 1200 + idx * 310,
        "pedestrian_flow": ped,
        "road_adjacent": True,
        "water_access": ptype != "ROOFTOP",
        "electricity_access": True,
        "nearby_schools": 1 + idx % 4,
        "nearby_hospitals": idx % 3,
        "nearby_parks": idx % 3,
        "nearby_subway_stations": 1 + idx % 3,
        "regulatory_restriction": "NONE",
        "regulations": [],
        "sumok_feasibility": {
            "status": "AVAILABLE",
            "score": feas_score,
            "reason": "명확한 규제 제한이 없으며 수목 식재 적합도가 높습니다.",
            "blockingRegulations": [],
            "warningRegulations": [],
            "requiredChecks": [],
            "confidence": 0.88,
        },
        "confidence": 0.88,
        "scores": scores,
    }


def main():
    existing: list[dict] = []
    if DATA_PATH.exists():
        with open(DATA_PATH, encoding="utf-8") as f:
            existing = json.load(f)

    covered = {p["district"] for p in existing}
    generated: list[dict] = []

    for district, (clat, clng) in SEOUL_DISTRICTS.items():
        if district in covered:
            continue
        for i, (ptype, label, soil, own) in enumerate(PARCEL_TYPES[:2], start=1):
            jitter_lat = clat + math.sin(i) * 0.008
            jitter_lng = clng + math.cos(i) * 0.010
            generated.append(make_parcel(district, i, ptype, label, soil, own, jitter_lat, jitter_lng))

    merged = existing + generated
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"기존 {len(existing)}건 + 신규 {len(generated)}건 = 총 {len(merged)}건")
    print(f"자치구 커버: {len({p['district'] for p in merged})}/25")


if __name__ == "__main__":
    main()