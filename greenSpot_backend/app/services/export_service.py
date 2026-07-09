import csv
import io
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.parcel_service import get_all_parcels


async def export_csv(db: AsyncSession) -> str:
    parcels, _ = await get_all_parcels(db)

    output = io.StringIO()
    writer = csv.writer(output)

    # BOM for Excel compatibility
    output.write("\ufeff")

    # Header
    writer.writerow([
        "ID", "부지명", "자치구", "행정동", "위도", "경도",
        "면적(㎡)", "부지유형", "소유권", "토양",
        "일사량(kWh/㎡/일)", "일조시간", "열섬강도(℃)", "여름지표면온도(℃)", "PM2.5(μg/m³)",
        "도로접면", "수자원접근", "전력접근",
        "수목점수", "텃밭점수", "태양광점수", "1순위추천", "불확실성(±)"
    ])

    # Rows
    for p in parcels:
        scores = p.get("scores", {})
        writer.writerow([
            p.get("id", ""),
            p.get("name", ""),
            p.get("district", ""),
            p.get("neighborhood", ""),
            p.get("lat", ""),
            p.get("lng", ""),
            p.get("areaSqm", ""),
            p.get("parcelType", ""),
            p.get("ownership", ""),
            p.get("soilType", ""),
            p.get("solarIrradiance", ""),
            p.get("sunlightHours", ""),
            p.get("heatIsland", ""),
            p.get("surfaceTempSummer", ""),
            p.get("airQuality", ""),
            "Y" if p.get("roadAdjacent") else "N",
            "Y" if p.get("waterAccess") else "N",
            "Y" if p.get("electricityAccess") else "N",
            scores.get("treeScore", ""),
            scores.get("gardenScore", ""),
            scores.get("solarScore", ""),
            scores.get("topRecommendation", ""),
            scores.get("uncertainty", ""),
        ])

    return output.getvalue()