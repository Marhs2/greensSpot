from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.parcel_service import get_parcel_detail_resolved
from app.services.simulation_service import simulate_compare_all
from datetime import datetime


def _fmt_money(v: Any) -> str:
    try:
        n = int(float(v))
        return f"₩{n:,}"
    except (TypeError, ValueError):
        return "—"


def _fmt_num(v: Any, digits: int = 0) -> str:
    try:
        n = float(v)
        if digits:
            return f"{n:.{digits}f}"
        return f"{int(round(n)):,}"
    except (TypeError, ValueError):
        return "—"


def _scenario_block(title: str, effects: Optional[Dict[str, Any]]) -> str:
    if not effects:
        return f"### {title}\n- 시뮬레이션 데이터 없음\n"
    lines = [f"### {title}"]
    if effects.get("label"):
        lines.append(f"- 규모: {effects.get('label')}")
    if effects.get("summary"):
        lines.append(f"- 요약: {effects.get('summary')}")
    if effects.get("carbonKgPerYear") is not None:
        lines.append(f"- 연간 CO₂: {_fmt_num(effects.get('carbonKgPerYear'))} kg")
    if effects.get("pm25ReductionKgPerYear") is not None:
        lines.append(f"- 연간 PM2.5 저감: {_fmt_num(effects.get('pm25ReductionKgPerYear'), 3)} kg")
    if effects.get("temperatureReductionC") is not None:
        lines.append(f"- 기온 완화: {_fmt_num(effects.get('temperatureReductionC'), 2)} ℃")
    if effects.get("yieldKgPerYear") is not None or effects.get("foodKgPerYear") is not None:
        y = effects.get("yieldKgPerYear") or effects.get("foodKgPerYear")
        lines.append(f"- 연간 수확: {_fmt_num(y)} kg")
    if effects.get("energyKwhPerYear") is not None:
        lines.append(f"- 연간 발전: {_fmt_num(effects.get('energyKwhPerYear'))} kWh")
    if effects.get("costEstimateWon") is not None:
        lines.append(f"- 투자비: {_fmt_money(effects.get('costEstimateWon'))}")
    if effects.get("annualMaintenanceWon") is not None:
        lines.append(f"- 연간 유지비: {_fmt_money(effects.get('annualMaintenanceWon'))}")
    if effects.get("costPerCarbonKgWon") is not None:
        lines.append(f"- 효율성: {_fmt_money(effects.get('costPerCarbonKgWon'))}/kg CO₂")
    if effects.get("paybackYears") is not None:
        lines.append(f"- 회수기간: {_fmt_num(effects.get('paybackYears'))}년")
    return "\n".join(lines) + "\n"


async def generate_report(db: AsyncSession, parcel_id: str, format: str = "markdown") -> Optional[str]:
    detail = await get_parcel_detail_resolved(db, parcel_id)
    if not detail:
        return None

    parcel = detail["parcel"]
    scores = detail["scores"]
    area = float(parcel.get("areaSqm") or 0)
    name = str(parcel.get("name") or parcel_id)

    scenarios: Dict[str, Any] = {}
    try:
        sim = await simulate_compare_all(
            db,
            parcel_id,
            area_sqm_hint=area if area > 0 else None,
            name_hint=name,
        )
        scenarios = (sim or {}).get("scenarios") or {}
    except Exception:  # noqa: BLE001
        # 테스트 mock DB / 시뮬 실패 시에도 점수·환경 리포트는 생성
        scenarios = {}

    if format == "markdown":
        conf = parcel.get("confidence")
        try:
            conf_pct = f"{float(conf) * 100:.0f}%"
        except (TypeError, ValueError):
            conf_pct = "—"

        report = f"""# GreenSpot 분석 리포트

## 부지 정보
- 부지명: {parcel.get('name')}
- 위치: {parcel.get('district')} {parcel.get('neighborhood')}
- 좌표: {parcel.get('lat')}, {parcel.get('lng')}
- 면적: {parcel.get('areaSqm')}㎡
- 유형: {parcel.get('parcelType')}
- 소유권: {parcel.get('ownership')}
- 토양: {parcel.get('soilType')}
- 규제: {parcel.get('regulatoryRestriction')}

## 환경 데이터
- 일사량: {parcel.get('solarIrradiance')} kWh/㎡/일
- 일조시간: {parcel.get('sunlightHours')} 시간
- 열섬강도: {parcel.get('heatIsland')}℃
- 여름 지표면온도: {parcel.get('surfaceTempSummer')}℃
- PM2.5: {parcel.get('airQuality')} μg/m³
- 도로 접면: {'예' if parcel.get('roadAdjacent') else '아니오'}
- 수자원 접근: {'가능' if parcel.get('waterAccess') else '불가/추정'}
- 전력 접근: {'가능' if parcel.get('electricityAccess') else '불가/추정'}

## 점수 분석 (불확실성 ±{scores.get('uncertainty', 0)}점, 신뢰도 {conf_pct})
| 용도 | 점수 |
| --- | --- |
| 수목 식재 | {scores.get('treeScore', 0)} |
| 텃밭 | {scores.get('gardenScore', 0)} |
| 태양광 | {scores.get('solarScore', 0)} |
| 1순위 | {scores.get('topRecommendation', '—')} |

## 시나리오 시뮬레이션
{_scenario_block('수목 식재', (scenarios.get('PLANT_TREES') or {}).get('effects'))}
{_scenario_block('텃밭', (scenarios.get('CREATE_GARDEN') or {}).get('effects'))}
{_scenario_block('태양광', (scenarios.get('INSTALL_SOLAR') or {}).get('effects'))}
---
생성일시: {datetime.utcnow().isoformat()}
"""
        return report

    elif format == "json":
        import json
        return json.dumps({
            "parcel": parcel,
            "scores": scores,
            "scenarios": scenarios,
            "generatedAt": datetime.utcnow().isoformat(),
        }, ensure_ascii=False, indent=2)

    return None
