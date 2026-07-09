from __future__ import annotations

from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.models.models import Scenario
from app.services.parcel_service import get_parcel_by_id
from app.services.live_search_service import live_get_parcel
import secrets
import time


# Static coefficients
TREE_CO2_KG_PER_YEAR = 79.4
TREE_PM25_KG_PER_YEAR = 0.158
TREE_TEMP_REDUCTION_C = 0.079
TREE_RAINWATER_LITERS = 1100
TREE_COST_PER_TREE_WON = 200000
TREE_MAINTENANCE_PER_TREE_WON = 15000

GARDEN_YIELD_KG_PER_SQM = 3.5
GARDEN_CO2_KG_PER_SQM = 0.5
GARDEN_COST_PER_SQM_WON = 15000
GARDEN_MAINTENANCE_PER_SQM_WON = 3000

SOLAR_KWH_PER_SQM_PER_YEAR = 140
SOLAR_CO2_KG_PER_KWH = 0.416
SOLAR_COST_PER_SQM_WON = 500000
SOLAR_PAYBACK_YEARS = 24

# 프론트 ScoreUse → 시나리오 타입
_SCENARIO_ALIASES = {
    "SUMOK": "PLANT_TREES",
    "TREE": "PLANT_TREES",
    "PLANT_TREES": "PLANT_TREES",
    "GARDEN": "CREATE_GARDEN",
    "CREATE_GARDEN": "CREATE_GARDEN",
    "SOLAR": "INSTALL_SOLAR",
    "INSTALL_SOLAR": "INSTALL_SOLAR",
    "COMPARE_ALL": "COMPARE_ALL",
}


class _LiveParcelArea:
    def __init__(self, parcel_id: str, area_sqm: float, name: str = ""):
        self.id = parcel_id
        self.name = name
        self.area_sqm = area_sqm
        self.is_live = True


def normalize_scenario_type(scenario_type: str) -> str:
    key = (scenario_type or "").strip().upper()
    return _SCENARIO_ALIASES.get(key, key)


async def _resolve_parcel_for_sim(
    db: AsyncSession,
    parcel_id: str,
    *,
    area_sqm_hint: Optional[float] = None,
    name_hint: Optional[str] = None,
):
    parcel = await get_parcel_by_id(db, parcel_id)
    if parcel:
        # ORM 객체에 is_live 없음
        return parcel

    try:
        live = await live_get_parcel(parcel_id)
    except Exception:  # noqa: BLE001
        live = None

    if live and live.get("parcel"):
        p = live["parcel"]
        return _LiveParcelArea(
            parcel_id,
            float(p.get("areaSqm") or area_sqm_hint or 0),
            p.get("name") or name_hint or "",
        )

    # 프론트에서 이미 로드한 면적을 힌트로 넘긴 경우 (VWorld 재조회 실패 대비)
    if area_sqm_hint is not None and float(area_sqm_hint) > 0:
        return _LiveParcelArea(
            parcel_id,
            float(area_sqm_hint),
            name_hint or "",
        )
    return None


def _is_live_parcel(parcel: Any) -> bool:
    return isinstance(parcel, _LiveParcelArea) or getattr(parcel, "is_live", False)


async def simulate_scenario(
    db: AsyncSession,
    parcel_id: str,
    scenario_type: str,
    quantity: int,
    *,
    area_sqm_hint: Optional[float] = None,
    name_hint: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    t0 = time.perf_counter()
    scenario_type = normalize_scenario_type(scenario_type)
    parcel = await _resolve_parcel_for_sim(
        db, parcel_id, area_sqm_hint=area_sqm_hint, name_hint=name_hint
    )
    if not parcel:
        return None

    effects: Dict[str, Any] = {}

    if scenario_type == "PLANT_TREES":
        co2 = round(quantity * TREE_CO2_KG_PER_YEAR)
        pm25 = round(quantity * TREE_PM25_KG_PER_YEAR, 3)
        temp = round(quantity * TREE_TEMP_REDUCTION_C, 1)
        rain = quantity * TREE_RAINWATER_LITERS
        cost = quantity * TREE_COST_PER_TREE_WON
        maintenance = quantity * TREE_MAINTENANCE_PER_TREE_WON
        cost_per_carbon = round(cost / co2) if co2 > 0 else 0

        effects = {
            "carbonKgPerYear": co2,
            "pm25ReductionKgPerYear": pm25,
            "temperatureReductionC": temp,
            "rainwaterLitersPerYear": rain,
            "costEstimateWon": cost,
            "annualMaintenanceWon": maintenance,
            "costPerCarbonKgWon": cost_per_carbon,
            "paybackYears": None,
            "summary": f"은행나무 성목 {quantity}그루 식재 시 연간 CO2 {co2}kg 흡수, 미세먼지 {pm25}kg 감소, 온도 {temp}℃ 낮춤",
        }

    elif scenario_type == "CREATE_GARDEN":
        area_used = min(quantity * 1.5, parcel.area_sqm)
        co2 = round(area_used * GARDEN_CO2_KG_PER_SQM)
        yield_kg = round(area_used * GARDEN_YIELD_KG_PER_SQM)
        cost = round(area_used * GARDEN_COST_PER_SQM_WON)
        maintenance = round(area_used * GARDEN_MAINTENANCE_PER_SQM_WON)

        effects = {
            "areaUsedSqm": round(area_used, 1),
            "yieldKgPerYear": yield_kg,
            "carbonKgPerYear": co2,
            "costEstimateWon": cost,
            "annualMaintenanceWon": maintenance,
            "costPerCarbonKgWon": round(cost / co2) if co2 > 0 else 0,
            "summary": f"{round(area_used)}㎡ 텃밭 조성 시 연간 수확량 {yield_kg}kg, CO2 {co2}kg 흡수",
        }

    elif scenario_type == "INSTALL_SOLAR":
        area_used = min(quantity * 2, parcel.area_sqm * 0.7)
        kwh = round(area_used * SOLAR_KWH_PER_SQM_PER_YEAR)
        co2 = round(kwh * SOLAR_CO2_KG_PER_KWH)
        cost = round(area_used * SOLAR_COST_PER_SQM_WON)
        payback = SOLAR_PAYBACK_YEARS

        effects = {
            "areaUsedSqm": round(area_used, 1),
            "energyKwhPerYear": kwh,
            "energyMonthly": [round(kwh / 12) for _ in range(12)],
            "carbonKgPerYear": co2,
            "costEstimateWon": cost,
            "paybackYears": payback,
            "costPerCarbonKgWon": round(cost / co2) if co2 > 0 else 0,
            "summary": f"{round(area_used)}㎡ 태양광 패널 설치 시 연간 {kwh}kWh 발전, CO2 {co2}kg 감소, 투자회수 {payback}년",
        }
    else:
        return None

    # DB 부지만 시나리오 저장 (라이브 VW- 필지는 FK 없음)
    if not _is_live_parcel(parcel):
        try:
            scenario = Scenario(
                id=_generate_id(),
                parcel_id=parcel_id,
                scenario_type=scenario_type,
                quantity=quantity,
                effects=effects,
            )
            db.add(scenario)
            await db.commit()
        except IntegrityError:
            await db.rollback()

    return {
        "parcelId": parcel_id,
        "parcelName": parcel.name or "",
        "parcelArea": float(parcel.area_sqm or 0),
        "scenarios": {
            scenario_type: {
                "label": f"{scenario_type} {quantity}개",
                "effects": effects,
            }
        },
        "elapsed_ms": int((time.perf_counter() - t0) * 1000),
    }


def _generate_id() -> str:
    return secrets.token_hex(8)


async def simulate_compare_all(
    db: AsyncSession,
    parcel_id: str,
    *,
    area_sqm_hint: Optional[float] = None,
    name_hint: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    t0 = time.perf_counter()
    parcel = await _resolve_parcel_for_sim(
        db, parcel_id, area_sqm_hint=area_sqm_hint, name_hint=name_hint
    )
    if not parcel:
        return None

    scenarios: Dict[str, Any] = {}
    area = float(parcel.area_sqm or 0)

    tree_qty = min(28, max(1, int(area / 20)))
    tree_result = await simulate_scenario(
        db, parcel_id, "PLANT_TREES", tree_qty,
        area_sqm_hint=area, name_hint=parcel.name,
    )
    if tree_result:
        scenarios["PLANT_TREES"] = {
            "label": f"나무 {tree_qty}그루",
            "effects": tree_result["scenarios"]["PLANT_TREES"]["effects"],
        }

    garden_qty = min(50, max(1, int(area / 10)))
    garden_result = await simulate_scenario(
        db, parcel_id, "CREATE_GARDEN", garden_qty,
        area_sqm_hint=area, name_hint=parcel.name,
    )
    if garden_result:
        scenarios["CREATE_GARDEN"] = {
            "label": f"텃밭 {garden_qty}구획",
            "effects": garden_result["scenarios"]["CREATE_GARDEN"]["effects"],
        }

    solar_qty = min(100, max(1, int(area / 3)))
    solar_result = await simulate_scenario(
        db, parcel_id, "INSTALL_SOLAR", solar_qty,
        area_sqm_hint=area, name_hint=parcel.name,
    )
    if solar_result:
        scenarios["INSTALL_SOLAR"] = {
            "label": f"태양광 {solar_qty}패널",
            "effects": solar_result["scenarios"]["INSTALL_SOLAR"]["effects"],
        }

    return {
        "parcelId": parcel_id,
        "parcelName": parcel.name or "",
        "parcelArea": area,
        "scenarios": scenarios,
        "elapsed_ms": int((time.perf_counter() - t0) * 1000),
    }
