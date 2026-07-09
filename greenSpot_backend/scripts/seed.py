# -*- coding: utf-8 -*-
import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import delete

from app.db.database import init_db, async_session_maker
from app.models.models import Parcel, ParcelScore
from app.services.auth_service import generate_id


DATA_PATH = Path(__file__).parent / "seed_data.json"


async def seed(from_vworld: bool = False):
    if not from_vworld:
        gen_script = Path(__file__).parent / "generate_full_seoul_seed.py"
        if gen_script.exists():
            import subprocess
            subprocess.run([sys.executable, str(gen_script)], check=True)

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"seed_data.json not found. Run: cd greenSpot_frontend && npx tsx scripts/export-seed.mts"
        )

    with open(DATA_PATH, encoding="utf-8") as f:
        rows = json.load(f)

    await init_db()
    async with async_session_maker() as session:
        await session.execute(delete(ParcelScore))
        await session.execute(delete(Parcel))

        batch = 0
        for row in rows:
            scores = row.pop("scores")
            parcel = Parcel(
                id=row["id"],
                name=row["name"],
                district=row["district"],
                neighborhood=row["neighborhood"],
                lat=row["lat"],
                lng=row["lng"],
                area_sqm=row["area_sqm"],
                parcel_type=row["parcel_type"],
                ownership=row["ownership"],
                soil_type=row["soil_type"],
                solar_irradiance=row["solar_irradiance"],
                monthly_irradiance=row["monthly_irradiance"],
                sunlight_hours=row["sunlight_hours"],
                heat_island=row["heat_island"],
                surface_temp_summer=row["surface_temp_summer"],
                air_quality=row["air_quality"],
                nearby_households=row["nearby_households"],
                pedestrian_flow=row["pedestrian_flow"],
                road_adjacent=row["road_adjacent"],
                water_access=row["water_access"],
                electricity_access=row["electricity_access"],
                nearby_schools=row["nearby_schools"],
                nearby_hospitals=row["nearby_hospitals"],
                nearby_parks=row["nearby_parks"],
                nearby_subway_stations=row["nearby_subway_stations"],
                regulatory_restriction=row["regulatory_restriction"],
                regulations=row.get("regulations") or [],
                sumok_feasibility=row.get("sumok_feasibility"),
                confidence=row["confidence"],
            )
            session.add(parcel)

            session.add(
                ParcelScore(
                    id=generate_id(),
                    parcel_id=row["id"],
                    tree_score=scores["tree_score"],
                    garden_score=scores["garden_score"],
                    solar_score=scores["solar_score"],
                    top_recommendation=scores["top_recommendation"],
                    uncertainty=scores["uncertainty"],
                    score_breakdown=json.dumps({}, ensure_ascii=False),
                )
            )
            batch += 1
            if batch % 100 == 0:
                await session.commit()

        await session.commit()
        print(f"Seeded {len(rows)} parcels and {len(rows)} scores")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GreenSpot DB seed")
    parser.add_argument(
        "--from-vworld",
        action="store_true",
        help="VWorld 수집 seed_data.json 사용 (합성 데이터 보강 생략)",
    )
    args = parser.parse_args()
    asyncio.run(seed(from_vworld=args.from_vworld))