from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.models import Parcel, ParcelScore, AgentQuery
from datetime import datetime


async def get_stats(db: AsyncSession) -> Dict[str, Any]:
    total_result = await db.execute(select(func.count(Parcel.id)))
    total = total_result.scalar()

    district_result = await db.execute(
        select(
            Parcel.district,
            func.count(Parcel.id).label("count"),
            func.sum(Parcel.area_sqm).label("totalArea"),
            func.avg(ParcelScore.tree_score).label("avgTreeScore"),
            func.avg(ParcelScore.garden_score).label("avgGardenScore"),
            func.avg(ParcelScore.solar_score).label("avgSolarScore"),
        )
        .outerjoin(ParcelScore)
        .group_by(Parcel.district)
    )
    by_district = []
    for row in district_result.all():
        rec_result = await db.execute(
            select(ParcelScore.top_recommendation, func.count(ParcelScore.id))
            .join(Parcel, Parcel.id == ParcelScore.parcel_id)
            .where(Parcel.district == row.district)
            .group_by(ParcelScore.top_recommendation)
        )
        top_recs = {r[0]: r[1] for r in rec_result.all()}
        by_district.append({
            "district": row.district,
            "count": row.count,
            "totalArea": row.totalArea or 0,
            "avgTreeScore": round(row.avgTreeScore or 0),
            "avgGardenScore": round(row.avgGardenScore or 0),
            "avgSolarScore": round(row.avgSolarScore or 0),
            "topRecs": {
                "TREE": top_recs.get("TREE", 0),
                "GARDEN": top_recs.get("GARDEN", 0),
                "SOLAR": top_recs.get("SOLAR", 0),
            },
        })

    type_result = await db.execute(
        select(
            Parcel.parcel_type,
            func.count(Parcel.id).label("count"),
            func.sum(Parcel.area_sqm).label("totalArea"),
            func.avg(ParcelScore.tree_score + ParcelScore.garden_score + ParcelScore.solar_score).label("avgScore"),
        )
        .outerjoin(ParcelScore)
        .group_by(Parcel.parcel_type)
    )
    by_type = []
    for row in type_result.all():
        by_type.append({
            "parcelType": row.parcel_type,
            "count": row.count,
            "totalArea": row.totalArea or 0,
            "avgScore": round(row.avgScore / 3) if row.avgScore else 0,
        })

    rec_result = await db.execute(
        select(ParcelScore.top_recommendation, func.count(ParcelScore.id)).group_by(
            ParcelScore.top_recommendation
        )
    )
    by_recommendation = {"TREE": 0, "GARDEN": 0, "SOLAR": 0}
    for rec, count in rec_result.all():
        if rec in by_recommendation:
            by_recommendation[rec] = count

    return {
        "totalParcels": total,
        "byDistrict": by_district,
        "byType": by_type,
        "byRecommendation": by_recommendation,
        "generatedAt": datetime.utcnow(),
    }


from app.constants.seoul import SEOUL_DISTRICTS as DISTRICTS
KEYWORDS = [
    *DISTRICTS,
    "수목", "식재", "나무", "텃밭", "태양광", "솔라", "옥상", "빈터", "유휴", "열섬", "넓은", "그린벨트", "규제",
]


async def get_trending(db: AsyncSession) -> Dict[str, Any]:
    total_result = await db.execute(select(func.count(AgentQuery.id)))
    total = total_result.scalar()

    result = await db.execute(
        select(AgentQuery.query).order_by(AgentQuery.created_at.desc()).limit(50)
    )
    queries = [row[0] for row in result.all()]

    keyword_counts: Dict[str, int] = {}
    district_counts: Dict[str, int] = {}
    for q in queries:
        for kw in KEYWORDS:
            if kw in q:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
        for d in DISTRICTS:
            if d in q:
                district_counts[d] = district_counts.get(d, 0) + 1

    top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    top_districts = sorted(district_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "totalQueries": total,
        "topKeywords": [{"keyword": k, "count": c} for k, c in top_keywords],
        "topDistricts": [{"district": d, "count": c} for d, c in top_districts],
        "recentQueries": queries[:5],
        "generatedAt": datetime.utcnow(),
    }


async def get_history(db: AsyncSession, limit: int = 20) -> Dict[str, Any]:
    result = await db.execute(
        select(AgentQuery).order_by(AgentQuery.created_at.desc()).limit(limit)
    )
    queries = result.scalars().all()

    history = []
    for q in queries:
        history.append({
            "id": q.id,
            "query": q.query,
            "criteria": q.criteria,
            "resultCount": q.result_count,
            "summary": q.summary,
            "source": q.source,
            "createdAt": q.created_at,
        })

    return {
        "history": history,
        "total": len(history),
    }