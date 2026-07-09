from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await migrate_db()
    await ensure_seed_if_empty()


async def ensure_seed_if_empty() -> None:
    """배포 환경(DB 비어 있음)에서 seed_data.json 자동 적재. VWorld 불가 시 폴백용."""
    import json
    import logging
    from pathlib import Path
    from sqlalchemy import func, select

    log = logging.getLogger("greenspot.seed")
    try:
        from app.models.models import Parcel, ParcelScore
        from app.services.auth_service import generate_id
    except Exception:
        return

    async with async_session_maker() as session:
        count = await session.scalar(select(func.count()).select_from(Parcel))
        if count and count > 0:
            return

    seed_path = Path(__file__).resolve().parents[2] / "scripts" / "seed_data.json"
    if not seed_path.is_file():
        log.warning("parcels empty and no seed_data.json at %s", seed_path)
        return

    try:
        with open(seed_path, encoding="utf-8") as f:
            rows = json.load(f)
        if not isinstance(rows, list) or not rows:
            log.warning("seed_data.json is empty")
            return

        log.info("Empty parcels table — loading %s rows from seed", len(rows))
        async with async_session_maker() as session:
            batch = 0
            for row in rows:
                scores = dict(row.get("scores") or {})
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
                        tree_score=scores.get("tree_score", 0),
                        garden_score=scores.get("garden_score", 0),
                        solar_score=scores.get("solar_score", 0),
                        top_recommendation=scores.get("top_recommendation", "TREE"),
                        uncertainty=scores.get("uncertainty", 0),
                        score_breakdown=json.dumps({}, ensure_ascii=False),
                    )
                )
                batch += 1
                if batch % 100 == 0:
                    await session.commit()
            await session.commit()
        log.info("Seed load finished (%s parcels)", len(rows))
    except Exception:
        log.exception("Auto-seed failed")


# SQLite는 ALTER TABLE ADD COLUMN 제약으로 인해 기존 테이블에 새 컬럼을
# 자동으로 추가하지 못한다. 누락된 컬럼을 안전하게 보완한다.
_MISSING_COLUMNS = {
    "parcels": [
        ("regulations", "TEXT"),
        ("regulations_updated_at", "DATETIME"),
        ("sumok_feasibility", "TEXT"),
        ("sumok_feasibility_updated_at", "DATETIME"),
    ],
    "parcel_scores": [
        ("sumok_score", "FLOAT"),
        ("sumok_feasibility_snapshot", "TEXT"),
        ("regulations_snapshot", "TEXT"),
        ("algorithm_version", "VARCHAR(50)"),
        ("is_latest", "BOOLEAN"),
    ],
}


async def migrate_db():
    from sqlalchemy import text

    async with engine.begin() as conn:
        for table, columns in _MISSING_COLUMNS.items():
            existing = await conn.run_sync(
                lambda sync_conn, t=table: [
                    row[1] for row in sync_conn.execute(
                        text(f"PRAGMA table_info({t})")
                    ).fetchall()
                ]
            )
            for col_name, col_type in columns:
                if col_name not in existing:
                    await conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                    )