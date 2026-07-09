"""
VWorld WFS 기반 규제 데이터 클라이언트 (GreenSpot 수목 식재 기준).

명세서 F-03 / docs/기능명세서.MD 의 VWorld WFS 레이어를 기반으로,
부지 좌표(lat/lng) 주변의 공간 규제 레이어를 조회하고
수목 식재(sumok) / 도시농업(garden) / 태양광(solar) 관점의
penalty 모델로 정규화한다.

참고 문서: https://www.vworld.kr/dev/v4dv_wmsguide2_s001.do
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
import httpx
from app.core.config import settings


# ---------------------------------------------------------------------------
# VWorld WFS 레이어 카탈로그 (명세서 F-03 주요 VWorld WFS 레이어)
# ---------------------------------------------------------------------------
# code            : 내부 규제 코드 (ParcelRegulation.regulationType)
# typename        : VWorld WFS typename
# name            : 한글 명칭
# severity         : info / warning / restricted / prohibited
# affectedUses     : ["sumok"] / ["garden"] / ["solar"] / ["all"]
# penaltyType      : none / subtract / multiplier / zero
# penaltyValue     : subtract=차감점, multiplier=배율
# legalBasis       : 관련 법령/근거
VWORLD_LAYERS: Dict[str, Dict[str, Any]] = {
    "lt_c_ud801": {
        "code": "GREEN_BELT",
        "name": "개발제한구역",
        "severity": "prohibited",
        "affectedUses": ["all"],
        "penaltyType": "zero",
        "penaltyValue": 0.0,
        "legalBasis": "개발제한구역의 지정 및 관리에 관한 특별조치법",
        "description": "그린벨트(개발제한구역)로 건축/개발 행위가 강하게 제한된다.",
    },
    "lt_c_uq162": {
        "code": "URBAN_NATURE_PARK",
        "name": "도시자연공원구역",
        "severity": "restricted",
        "affectedUses": ["sumok", "garden", "solar"],
        "penaltyType": "multiplier",
        "penaltyValue": 0.5,
        "legalBasis": "도시공원 및 녹지 등에 관한 법률",
        "description": "도시자연공원구역으로 지정되어 인허가 확인이 필요하며 식재/개발이 제한될 수 있다.",
    },
    "lt_c_uq114": {
        "code": "NATURAL_CONSERVATION",
        "name": "자연환경보전지역",
        "severity": "prohibited",
        "affectedUses": ["all"],
        "penaltyType": "zero",
        "penaltyValue": 0.0,
        "legalBasis": "자연환경보전법",
        "description": "자연환경보전지역으로 생태적 보전 가치가 높아 사실상 개발이 불가하다.",
    },
    "lt_c_uq111": {
        "code": "URBAN_ZONE",
        "name": "도시지역",
        "severity": "info",
        "affectedUses": ["sumok", "garden", "solar"],
        "penaltyType": "none",
        "penaltyValue": 0.0,
        "legalBasis": "국토의 계획 및 이용에 관한 법률",
        "description": "도시지역 용도지역. 기본 용도지역 판단용이며 직접 제한은 아니다.",
    },
    "lt_c_uq113": {
        "code": "AGRICULTURE_FORESTRY_ZONE",
        "name": "농림지역",
        "severity": "warning",
        "affectedUses": ["sumok", "garden"],
        "penaltyType": "none",
        "penaltyValue": 0.0,
        "legalBasis": "국토의 계획 및 이용에 관한 법률",
        "description": "농림지역으로 수목 식재/텃밭은 가능하나 성토·건축 등에 주의가 필요하다.",
    },
    "lt_c_uq126": {
        "code": "PROTECTION_DISTRICT",
        "name": "보호지구",
        "severity": "restricted",
        "affectedUses": ["all"],
        "penaltyType": "zero",
        "penaltyValue": 0.0,
        "legalBasis": "국토의 계획 및 이용에 관한 법률",
        "description": "보호지구(군사·문화재 등)로 용도에 따라 사실상 불가할 수 있다.",
    },
}


VWORLD_WFS_URL = "https://api.vworld.kr/req/wfs"
VWORLD_POSSESSION_WMS_URL = "https://api.vworld.kr/ned/wms/getPossessionWMS"
VWORLD_LAND_CHARACTERISTICS_URL = "https://api.vworld.kr/ned/data/getLandCharacteristics"


class VWorldNotConfigured(Exception):
    pass


class VWorldBBoxError(Exception):
    """bbox 문자열 파싱 또는 유효성 검증 오류."""
    pass


class VWorldClient:
    """VWorld WFS 1.1.0 클라이언트."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or settings.vworld_api_key or "").strip()

    def _check_key(self):
        if not self.api_key:
            raise VWorldNotConfigured(
                "VWORLD_API_KEY가 설정되지 않았습니다. .env에 키를 입력하세요."
            )

    async def _get_feature(
        self,
        typename: str,
        lat: float,
        lng: float,
        radius_deg: float = 0.0008,
        *,
        http: Optional[httpx.AsyncClient] = None,
    ) -> List[Dict[str, Any]]:
        """점(point) 주변 bbox로 WFS GetFeature를 호출하고 feature 목록을 반환한다."""
        self._check_key()
        # WFS 1.1.0 / EPSG:4326 은 axis order = (lat, lon)
        half = radius_deg
        bbox = f"{lat - half},{lng - half},{lat + half},{lng + half}"
        params = {
            "key": self.api_key,
            "domain": settings.vworld_domain,
            "service": "WFS",
            "version": "1.1.0",
            "request": "GetFeature",
            "typename": typename,
            "output": "application/json",
            "srsname": "EPSG:4326",
            "bbox": bbox,
            "maxFeatures": 20,
        }

        async def _do(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
            resp = await client.get(VWORLD_WFS_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            features = data.get("features") or []
            if not features and isinstance(data.get("response"), dict):
                features = []
            return features

        if http is not None:
            return await _do(http)
        async with httpx.AsyncClient(timeout=10.0) as client:
            return await _do(client)

    async def get_possession_wms(
        self,
        pnu: str,
        bbox: Union[str, Tuple[float, float, float, float]],
        width: int = 915,
        height: int = 700,
    ) -> bytes:
        """토지소유정보 WMS 이미지(PNG)를 조회한다.

        bbox는 EPSG:4326 기준 `ymin,xmin,ymax,xmax` 형식 문자열 또는
        4개 float 튜플로 전달할 수 있다.
        """
        self._check_key()
        bbox_str = self._normalize_bbox(bbox)
        params = {
            "key": self.api_key,
            "domain": settings.vworld_domain,
            "layer": "dt_d160",
            "format": "image/png",
            "bbox": bbox_str,
            "width": width,
            "height": height,
            "pnu": pnu,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(VWORLD_POSSESSION_WMS_URL, params=params)
                resp.raise_for_status()
                data = resp.content
                if data and not data.startswith(b"<") and len(data) > 0:
                    return data
                raise httpx.HTTPError("Invalid WMS image response")
        except Exception:
            return b""

    @staticmethod
    def _normalize_bbox(
        bbox: Union[str, Tuple[float, float, float, float]],
    ) -> str:
        if isinstance(bbox, str):
            parts = [p.strip() for p in bbox.split(",")]
            if len(parts) != 4:
                raise VWorldBBoxError("bbox는 'ymin,xmin,ymax,xmax' 4개 값이 필요합니다.")
            try:
                values = [float(p) for p in parts]
            except ValueError as exc:
                raise VWorldBBoxError("bbox 값은 숫자여야 합니다.") from exc
        else:
            values = list(bbox)
            if len(values) != 4:
                raise VWorldBBoxError("bbox는 4개의 float 값이 필요합니다.")

        ymin, xmin, ymax, xmax = values
        if not (-180 <= xmin <= 180 and -180 <= xmax <= 180):
            raise VWorldBBoxError("경도는 -180~180 범위여야 합니다.")
        if not (-90 <= ymin <= 90 and -90 <= ymax <= 90):
            raise VWorldBBoxError("위도는 -90~90 범위여야 합니다.")
        if ymin >= ymax or xmin >= xmax:
            raise VWorldBBoxError("bbox의 최소값은 최대값보다 작아야 합니다.")
        return f"{ymin},{xmin},{ymax},{xmax}"

    async def get_land_characteristics(
        self,
        pnu: str,
        stdr_year: Optional[str] = None,
    ) -> Dict[str, Any]:
        """토지특성정보(JSON)를 조회한다.

        stdr_year가 None이면 현재 연도를 사용한다.
        """
        self._check_key()
        year = stdr_year or str(datetime.utcnow().year)
        params = {
            "key": self.api_key,
            "domain": settings.vworld_domain,
            "pnu": pnu,
            "stdrYear": year,
            "format": "json",
            "numOfRows": 100,
            "pageNo": 1,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(VWORLD_LAND_CHARACTERISTICS_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError:
            return {
                "pnu": pnu,
                "items": [],
                "count": 0,
                "source": "vworld",
                "dataAvailable": False,
                "year": year,
            }

        items: List[Dict[str, Any]] = []
        if isinstance(data, dict):
            # VWorld 실제 키는 landCharacteristicss (s 중복) + field[]
            raw = (
                data.get("landCharacteristicss")
                or data.get("landCharacteristics")
                or data.get("result")
                or data
            )
            if isinstance(raw, dict):
                field = (
                    raw.get("field")
                    or raw.get("items")
                    or raw.get("item")
                    or raw.get("list")
                    or []
                )
                items = field
            elif isinstance(raw, list):
                items = raw
        if isinstance(items, dict):
            nested = items.get("item") or items.get("field")
            items = nested if nested is not None else [items]

        if not isinstance(items, list):
            items = []
        items = [x for x in items if isinstance(x, dict)]

        # 현재 연도 데이터 없으면 최근 연도로 재시도
        if not items and stdr_year is None:
            for fallback_year in (str(int(year) - 1), str(int(year) - 2)):
                retry = await self.get_land_characteristics(pnu, stdr_year=fallback_year)
                if retry.get("dataAvailable") and retry.get("items"):
                    return retry

        return {
            "pnu": pnu,
            "items": items,
            "count": len(items),
            "source": "vworld",
            "dataAvailable": len(items) > 0,
            "year": year,
        }

    async def get_regulations_at_point(
        self, lat: float, lng: float, radius_deg: float = 0.0008,
        typenames: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """좌표 주변의 규제 레이어를 조회해 ParcelRegulation 형태로 정규화한다.

        레이어별 WFS 호출을 병렬로 수행한다.
        """
        import asyncio

        typenames = typenames or list(VWORLD_LAYERS.keys())
        regulations: List[Dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=10.0) as http:
            async def _one(typename: str) -> List[Dict[str, Any]]:
                cfg = VWORLD_LAYERS.get(typename)
                if cfg is None:
                    return []
                try:
                    features = await self._get_feature(
                        typename, lat, lng, radius_deg, http=http
                    )
                except httpx.HTTPError:
                    return []
                out: List[Dict[str, Any]] = []
                for feat in features:
                    props = feat.get("properties") or {}
                    name = (
                        props.get("full_nm")
                        or props.get("emd_kor_nm")
                        or props.get("frt_cs")
                        or props.get("name")
                        or cfg["name"]
                    )
                    out.append({
                        "regulationType": cfg["code"],
                        "regulationName": name,
                        "severity": cfg["severity"],
                        "affectedUses": cfg["affectedUses"],
                        "penaltyType": cfg["penaltyType"],
                        "penaltyValue": cfg["penaltyValue"],
                        "legalBasis": cfg["legalBasis"],
                        "description": cfg["description"],
                        "source": "VWorld",
                        "sourceLayer": cfg["name"],
                        "typename": typename,
                        "rawData": props,
                    })
                return out

            batches = await asyncio.gather(
                *[_one(t) for t in typenames],
                return_exceptions=True,
            )

        for batch in batches:
            if isinstance(batch, list):
                regulations.extend(batch)
        return regulations


# ---------------------------------------------------------------------------
# 점수 / sumokFeasibility 계산 (명세서 F-03)
# ---------------------------------------------------------------------------
def _apply_penalty(score: float, penalty_type: str, penalty_value: float) -> float:
    if penalty_type == "zero":
        return 0.0
    if penalty_type == "subtract":
        return max(0.0, score - (penalty_value or 0.0))
    if penalty_type == "multiplier":
        return max(0.0, score * (penalty_value if penalty_value is not None else 1.0))
    return score


def apply_regulation_penalties(
    base_scores: Dict[str, float],
    regulations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """규제 penalty를 점수에 적용하고 최종 점수/스냅샷을 반환한다.

    affectedUses 에 "all" 이 있으면 sumok/garden/solar 전 용도에 적용한다.
    """
    use_map = {
        "sumok": "sumokScore",
        "garden": "gardenScore",
        "solar": "solarScore",
        "tree": "sumokScore",  # API TREE 별칭
        "TREE": "sumokScore",
        "SUMOK": "sumokScore",
        "GARDEN": "gardenScore",
        "SOLAR": "solarScore",
    }
    all_uses = ("sumok", "garden", "solar")
    applied: Dict[str, Any] = {
        "sumokScore": float(base_scores.get("sumokScore", 0.0)),
        "gardenScore": float(base_scores.get("gardenScore", 0.0)),
        "solarScore": float(base_scores.get("solarScore", 0.0)),
    }
    penalties: List[Dict[str, Any]] = []

    for reg in regulations:
        affects = reg.get("affectedUses") or []
        ptype = reg.get("penaltyType", "none")
        pvalue = reg.get("penaltyValue") or 0.0
        if ptype == "none":
            continue
        # "all" → 전 용도 확장 (그린벨트 등 zero 페널티가 무시되던 버그 수정)
        expanded: list[str] = []
        for use in affects:
            key = str(use).strip()
            if key.lower() == "all":
                expanded.extend(all_uses)
            else:
                expanded.append(key)
        seen_fields: set[str] = set()
        for use in expanded:
            field = use_map.get(use) or use_map.get(str(use).lower())
            if not field or field in seen_fields:
                continue
            seen_fields.add(field)
            before = applied[field]
            after = _apply_penalty(before, ptype, pvalue)
            if before != after:
                applied[field] = after
                penalties.append({
                    "regulationType": reg.get("regulationType") or reg.get("code"),
                    "use": field.replace("Score", "").lower(),
                    "penaltyType": ptype,
                    "penaltyValue": pvalue,
                    "before": round(before, 2),
                    "after": round(after, 2),
                })

    applied["penalties"] = penalties
    applied["regulationsSnapshot"] = regulations
    return applied


def compute_sumok_feasibility(
    sumok_score: float,
    regulations: List[Dict[str, Any]],
    confidence: float = 0.9,
) -> Dict[str, Any]:
    """sumokScore 와 규제 정보로 sumokFeasibility 객체를 생성한다."""
    blocking: List[str] = []
    warnings: List[str] = []
    required_checks: List[str] = []
    info_notes: List[str] = []

    for reg in regulations:
        affects_sumok = ("sumok" in (reg.get("affectedUses") or [])) or (
            "all" in (reg.get("affectedUses") or [])
        )
        if not affects_sumok:
            continue
        sev = reg.get("severity")
        code = reg.get("regulationType") or reg.get("code") or ""
        name = reg.get("regulationName") or reg.get("name") or code
        ptype = reg.get("penaltyType")
        if sev in ("prohibited", "restricted") and ptype == "zero":
            blocking.append(code)
        elif sev == "restricted":
            blocking.append(code)
        elif sev == "warning":
            warnings.append(code)
            required_checks.append(f"{name} 관련 용도/행위 제한 확인")
        elif sev == "info" and code and code != "URBAN_ZONE":
            info_notes.append(str(name))

    if blocking:
        status = "PROHIBITED" if any(
            reg.get("severity") == "prohibited"
            for reg in regulations
            if ("sumok" in (reg.get("affectedUses") or []) or "all" in (reg.get("affectedUses") or []))
            and reg.get("penaltyType") == "zero"
        ) else "RESTRICTED"
        reason = "강한 제한 규제가 있어 수목 식재가 사실상 불가하거나 0점 처리됩니다."
        for code in blocking:
            required_checks.append(f"{code} 관련 지자체 인허가 확인")
    elif warnings:
        status = "CONDITIONAL"
        # 자연녹지 등 용도지역 warning 을 문구에 명시
        names = []
        for reg in regulations:
            if reg.get("severity") == "warning":
                names.append(reg.get("regulationName") or reg.get("name") or reg.get("regulationType"))
        zone_txt = ", ".join(str(n) for n in names if n)
        if zone_txt:
            reason = f"{zone_txt} 등으로 수목 식재는 가능하나 행위 제한·인허가 확인이 필요합니다."
        else:
            reason = "수목 식재 가능성은 있으나 인허가/현장 확인이 필요합니다."
    elif sumok_score >= 60:
        status = "AVAILABLE"
        if info_notes:
            reason = (
                f"금지 규제는 없으나 용도지역({', '.join(info_notes[:3])}) 등 "
                "기본 제약을 확인하세요. 적합도는 양호합니다."
            )
            for note in info_notes[:3]:
                required_checks.append(f"{note} 행위 제한 여부 확인")
        else:
            reason = "명확한 제한이 없고 수목 식재 적합도가 높습니다."
    else:
        status = "UNKNOWN"
        reason = "데이터 부족 또는 적합도가 낮아 판단이 불확실합니다."

    return {
        "status": status,
        "score": round(float(sumok_score), 2),
        "reason": reason,
        "blockingRegulations": blocking,
        "warningRegulations": warnings,
        "requiredChecks": required_checks,
        "confidence": round(float(confidence), 2),
    }


def client() -> VWorldClient:
    return VWorldClient()
