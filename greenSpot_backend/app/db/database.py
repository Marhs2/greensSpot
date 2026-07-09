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