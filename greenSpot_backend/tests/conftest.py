"""공유 pytest fixtures — 전체 기능 테스트용."""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.database import Base, get_db
from main import app


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """기본 TestClient (기존 파일과 호환). startup init_db 비활성."""
    with patch("main.init_db"):
        with TestClient(app) as c:
            yield c


@pytest.fixture
def db_client() -> Generator[TestClient, None, None]:
    """인메모리 SQLite + get_db 오버라이드. 인증/북마크/실DB 기능용."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _prepare() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_prepare())

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with patch("main.init_db"):
            with TestClient(app) as c:
                yield c
    finally:
        app.dependency_overrides.pop(get_db, None)
        asyncio.run(engine.dispose())


def live_parcel_dict(
    parcel_id: str = "VW-1154510100100010000",
    *,
    district: str = "금천구",
    tree: float = 70,
    garden: float = 65,
    solar: float = 80,
    top: str = "SOLAR",
) -> dict:
    return {
        "id": parcel_id,
        "name": f"{district} 테스트 부지",
        "district": district,
        "neighborhood": "가산동",
        "lat": 37.48,
        "lng": 126.89,
        "areaSqm": 1200.0,
        "parcelType": "UNUSED_LAND",
        "ownership": "PUBLIC",
        "soilType": "LOAM",
        "solarIrradiance": 4.2,
        "sunlightHours": 6.0,
        "heatIsland": 2.1,
        "surfaceTempSummer": 34.0,
        "airQuality": 22,
        "nearbyHouseholds": None,
        "pedestrianFlow": None,
        "roadAdjacent": True,
        "waterAccess": False,
        "electricityAccess": True,
        "nearbySchools": None,
        "nearbyHospitals": None,
        "nearbyParks": None,
        "nearbySubwayStations": None,
        "regulatoryRestriction": "",
        "regulations": [],
        "sumokFeasibility": {
            "status": "AVAILABLE",
            "score": tree,
            "reason": "ok",
            "blockingRegulations": [],
            "warningRegulations": [],
            "requiredChecks": [],
            "confidence": 0.9,
        },
        "confidence": 0.9,
        "dataSource": "VWorld Live",
        "dataProvenance": {
            "soilType": {"actual": True},
            "monthlyIrradiance": {"actual": False},
        },
        "scores": {
            "treeScore": tree,
            "gardenScore": garden,
            "solarScore": solar,
            "topRecommendation": top,
            "uncertainty": 5,
            "treeBreakdown": ["면적"],
            "gardenBreakdown": ["토양"],
            "solarBreakdown": ["일사"],
        },
    }
