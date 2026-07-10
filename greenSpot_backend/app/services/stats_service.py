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
