import json
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.parcel_service import get_parcel_detail_resolved
from app.services.llm_service import chat, LLMNotConfigured

_SCORE_LABELS = {
    "treeScore": "수목 식재",
    "sumokScore": "수목 식재",
    "gardenScore": "텃밭",
    "solarScore": "태양광",
}

_REC_LABELS = {
    "TREE": "수목 식재",
    "SUMOK": "수목 식재",
    "GARDEN": "텃밭",
    "SOLAR": "태양광",
}

_PARCEL_TYPE_LABELS = {
    "VACANT_LOT": "빈터",
    "ROOFTOP": "옥상",
    "UNUSED_LAND": "유휴지",
    "ABANDONED": "방치건물",
    "BROWNFIELD": "오염정화지",
}

_OWNERSHIP_LABELS = {
    "PUBLIC": "공공",
    "PRIVATE": "민간",
    "UNKNOWN": "미상",
}


def _score_label(key: str) -> str:
    return _SCORE_LABELS.get(key, key)


def _fallback_explanation(parcel: Dict[str, Any], scores: Dict[str, Any]) -> str:
    score_items = sorted(
        [(k, float(v or 0)) for k, v in scores.items() if str(k).endswith("Score")],
        key=lambda x: x[1],
        reverse=True,
    )
    second = _score_label(score_items[1][0]) if len(score_items) > 1 else "없음"
    third = _score_label(score_items[2][0]) if len(score_items) > 2 else "없음"
    top_key = score_items[0][0] if score_items else ""
    top_score = score_items[0][1] if score_items else 0
    top_rec = scores.get("topRecommendation") or "NONE"
    top_label = _REC_LABELS.get(str(top_rec).upper(), str(top_rec))
    if top_rec in (None, "NONE", "") and top_key:
        top_label = _score_label(top_key)

    parcel_type = parcel.get("parcelType") or ""
    parcel_type_label = _PARCEL_TYPE_LABELS.get(str(parcel_type), str(parcel_type) or "—")
    ownership = parcel.get("ownership") or ""
    ownership_label = _OWNERSHIP_LABELS.get(str(ownership), str(ownership) or "—")

    reg = parcel.get("regulatoryRestriction") or ""
    # 코드성 값이면 완화 표기 (UI 규명 목록은 상세 탭 참고)
    if isinstance(reg, str) and reg.startswith("ZONING"):
        reg_display = f"용도지역 코드({reg})"
    else:
        reg_display = reg or "없음"

    conf = parcel.get("confidence")
    try:
        conf_pct = float(conf or 0) * 100
    except (TypeError, ValueError):
        conf_pct = 0.0

    return f"""## 📍 부지 요약
- 부지명: {parcel.get('name')}
- 위치: {parcel.get('district')} {parcel.get('neighborhood')}
- 면적: {parcel.get('areaSqm')}㎡
- 유형: {parcel_type_label}
- 소유권: {ownership_label}
- 규제: {reg_display}

## 🎯 추천 결과 및 이유
1순위: {top_label} (점수: {top_score:.0f})
- 불확실성: ±{scores.get('uncertainty', 0)}점

## 💡 대안 용도 검토
- 2순위: {second}
- 3순위: {third}

## ⚠️ 한계 및 보완점
- 신뢰도: {conf_pct:.0f}%
- 데이터 출처: VWorld(지적·규제), AirKorea(대기), Visual Crossing(일사·기온), KOSIS(인구·가구), GreenSpot 점수 알고리즘
"""


async def explain_parcel(db: AsyncSession, parcel_id: str) -> Optional[Dict[str, Any]]:
    detail = await get_parcel_detail_resolved(db, parcel_id)
    if not detail:
        return None

    parcel = detail["parcel"]
    scores = detail["scores"]

    facts = {
        "parcelName": parcel.get("name"),
        "district": parcel.get("district"),
        "neighborhood": parcel.get("neighborhood"),
        "areaSqm": parcel.get("areaSqm"),
        "parcelType": parcel.get("parcelType"),
        "ownership": parcel.get("ownership"),
        "soilType": parcel.get("soilType"),
        "regulatoryRestriction": parcel.get("regulatoryRestriction"),
        "solarIrradiance": parcel.get("solarIrradiance"),
        "sunlightHours": parcel.get("sunlightHours"),
        "heatIsland": parcel.get("heatIsland"),
        "airQuality": parcel.get("airQuality"),
        "roadAdjacent": parcel.get("roadAdjacent"),
        "waterAccess": parcel.get("waterAccess"),
        "electricityAccess": parcel.get("electricityAccess"),
        "scores": scores,
    }

    explanation = _fallback_explanation(parcel, scores)
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 GreenSpot 부지 분석 AI입니다. facts 객체의 수치만 사용해 "
                    "한국어 마크다운 4개 섹션(📍 부지 요약, 🎯 추천 결과 및 이유, "
                    "💡 대안 용도 검토, ⚠️ 한계 및 보완점)으로 설명하세요. "
                    "용도 이름은 수목 식재/텃밭/태양광으로 쓰고 treeScore 등 필드명을 그대로 쓰지 마세요. "
                    "유형·소유권 코드는 가능한 한 한국어로 풀어 쓰세요. "
                    "facts 외의 수치를 만들지 말고, 출처는 VWorld/AirKorea/Visual Crossing/"
                    "KOSIS/GreenSpot 알고리즘을 명시하세요. 기상청·Landsat을 실제 연동 출처처럼 "
                    "단정하지 마세요. 정치적 단어(불평등/격차/소외/차별)를 사용하지 마세요."
                ),
            },
            {
                "role": "user",
                "content": f"다음 facts로 부지 분석 리포트를 작성하세요:\n{json.dumps(facts, ensure_ascii=False, default=str)}",
            },
        ]
        explanation = await chat(messages)
    except (LLMNotConfigured, Exception):
        explanation = _fallback_explanation(parcel, scores)

    return {
        "parcelId": parcel_id,
        "explanation": explanation,
        "facts": facts,
        "promptVersion": "v3-greenspot3",
        "uncertainty": scores.get("uncertainty", 0),
    }
