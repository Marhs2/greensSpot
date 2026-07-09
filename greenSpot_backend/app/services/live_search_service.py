"""
VWorld 실시간 부지 검색 — DB 저장 없이 검색 시 API 호출로 전국 조회.

연속지적도(LP_PA_CBND_BUBUN) + 규제 WFS를 조합해 결과를 반환한다.
최근 조회 결과는 메모리 캐시에만 보관(상세/북마크 조회용).
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.services.vworld_discovery_service import (
    VWorldDataClient,
    VWorldDiscoveryError,
    build_parcel_from_feature,
    geometry_area_sqm,
)

# parcel_id -> {parcel, scores, cached_at}
_LIVE_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_MAX = 800

SIGG_DATA = "LT_C_ADSIGG_INFO"
EMD_DATA = "LT_C_ADEMD_INFO"


def _cache_put(parcel_api: Dict[str, Any], scores: Dict[str, Any]) -> None:
    pid = parcel_api["id"]
    _LIVE_CACHE[pid] = {
        "parcel": parcel_api,
        "scores": scores,
        "cached_at": time.time(),
    }
    if len(_LIVE_CACHE) > _CACHE_MAX:
        oldest = sorted(_LIVE_CACHE.items(), key=lambda x: x[1]["cached_at"])[:100]
        for k, _ in oldest:
            _LIVE_CACHE.pop(k, None)


def _parse_pnu_from_id(parcel_id: str) -> Optional[str]:
    if parcel_id.startswith("VW-"):
        return parcel_id[3:]
    if len(parcel_id) == 19 and parcel_id.isdigit():
        return parcel_id
    return None


def extract_region_name(query: str) -> Optional[str]:
    """전국 시·군·구 이름 추출 (예: 용산구, 해운대구, 성남시, 제주시)."""
    q = query.strip()
    for pat in (
        r"([가-힣]{2,8}시\s+[가-힣]{2,6}(?:구|군))",
        r"([가-힣]{2,8}(?:특별시|광역시|특별자치시|특별자치도|도)\s*[가-힣]{2,6}(?:구|군))",
        r"([가-힣]{2,6}(?:구|군))",
        r"([가-힣]{2,8}시)",
    ):
        m = re.search(pat, q)
        if m:
            name = m.group(1)
            # Province-level prefix only (e.g. "경기도 성남시 분당구" -> "성남시 분당구").
            # Keep city/do suffixes such as "특별시" so "서울특별시 강남구" remains intact.
            name = re.sub(r"^\S+(?:특별자치도|도)\s+", "", name).strip()
            return name
    return None


def extract_neighborhood(query: str) -> Optional[str]:
    m = re.search(r"([가-힣]{1,6}(?:동|읍|면|리|가))", query)
    return m.group(1) if m else None


async def _data_get(client: VWorldDataClient, http, params: Dict[str, Any]) -> Dict[str, Any]:
    from app.services.vworld_discovery_service import VWORLD_DATA_URL
    import httpx

    base = {
        "service": "data",
        "version": "2.0",
        "request": "GetFeature",
        "key": client.api_key,
        "domain": client.domain,
        "format": "json",
    }
    base.update(params)
    last_err: Optional[Exception] = None
    # VWorld 일시 502/503 대비 재시도 (키/URL 은 로그·메시지에 남기지 않음)
    for attempt in range(3):
        try:
            resp = await http.get(VWORLD_DATA_URL, params=base)
            if resp.status_code in (502, 503, 504) and attempt < 2:
                logger.warning("VWorld HTTP %s (attempt %s), retrying", resp.status_code, attempt + 1)
                await asyncio.sleep(0.4 * (attempt + 1))
                continue
            resp.raise_for_status()
            body = resp.json().get("response") or {}
            if body.get("status") == "ERROR":
                err = body.get("error") or {}
                text = err.get("text") or "VWorld API error"
                code = err.get("code") or ""
                raise VWorldDiscoveryError(f"{text}" + (f" ({code})" if code else ""))
            return body
        except VWorldDiscoveryError:
            raise
        except (httpx.HTTPError, httpx.InvalidURL, ValueError) as e:
            last_err = e
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status in (502, 503, 504) and attempt < 2:
                logger.warning("VWorld request error HTTP %s (attempt %s), retrying", status, attempt + 1)
                await asyncio.sleep(0.4 * (attempt + 1))
                continue
            logger.warning("VWorld data request failed: %s", type(e).__name__)
            raise VWorldDiscoveryError(
                f"VWorld API 연결 실패 (HTTP {status or 'network'}). "
                "VWORLD_API_KEY / VWORLD_DOMAIN 과 VWorld 서비스 상태를 확인하세요."
            ) from e
    raise VWorldDiscoveryError(f"VWorld API 연결 실패: {type(last_err).__name__ if last_err else 'unknown'}")


def _bbox_from_geometry(geometry: Optional[Dict[str, Any]]) -> Optional[Tuple[float, float, float, float]]:
    if not geometry:
        return None
    coords = geometry.get("coordinates")
    if not coords:
        return None
    points: List[List[float]] = []
    gtype = geometry.get("type")
    if gtype == "Polygon":
        points = coords[0]
    elif gtype == "MultiPolygon":
        for poly in coords:
            if poly:
                points.extend(poly[0])
    if not points:
        return None
    lngs = [p[0] for p in points]
    lats = [p[1] for p in points]
    return min(lngs), min(lats), max(lngs), max(lats)


async def resolve_region(region_name: str) -> Optional[Dict[str, Any]]:
    """시·군·구 명칭 → VWorld 행정구역 + bbox."""
    import httpx

    client = VWorldDataClient()
    client._check_key()
    keyword = region_name
    norm_keyword = keyword.replace(" ", "")
    try:
        async with httpx.AsyncClient(timeout=20.0) as http:
            for attr in (
                f"sig_kor_nm:like:{keyword}",
                f"full_nm:like:{keyword}",
            ):
                response = await _data_get(client, http, {
                    "data": SIGG_DATA,
                    "size": 10,
                    "page": 1,
                    "attrFilter": attr,
                    "geometry": "true",
                    "attribute": "true",
                    "crs": "EPSG:4326",
                })
                if response.get("status") != "OK":
                    continue
                feats = response.get("result", {}).get("featureCollection", {}).get("features", [])
                for feat in feats:
                    props = feat.get("properties") or {}
                    kor = props.get("sig_kor_nm") or ""
                    full = props.get("full_nm") or ""
                    norm_kor = kor.replace(" ", "")
                    norm_full = full.replace(" ", "")
                    if norm_keyword not in norm_kor and norm_keyword not in norm_full and keyword not in kor:
                        continue
                    bbox = _bbox_from_geometry(feat.get("geometry"))
                    if not bbox:
                        continue
                    return {
                        "name": kor or region_name,
                        "full_name": full,
                        "sig_cd": str(props.get("sig_cd", "")),
                        "bbox": bbox,
                    }
    except VWorldDiscoveryError:
        raise
    except Exception as e:
        logger.warning("resolve_region failed for %r: %s", region_name, e)
        raise VWorldDiscoveryError(f"행정구역 조회 실패: {e}") from e
    return None


async def _emd_codes_in_bbox(
    client: VWorldDataClient,
    http,
    bbox: Tuple[float, float, float, float],
    sig_cd: str,
    neighborhood: Optional[str] = None,
) -> List[str]:
    min_lng, min_lat, max_lng, max_lat = bbox
    geom = f"BOX({min_lng},{min_lat},{max_lng},{max_lat})"
    codes: List[str] = []
    page = 1
    while page <= 5:
        response = await _data_get(client, http, {
            "data": EMD_DATA,
            "size": 100,
            "page": page,
            "geomFilter": geom,
            "geometry": "false",
            "attribute": "true",
        })
        if response.get("status") != "OK":
            break
        feats = response.get("result", {}).get("featureCollection", {}).get("features", [])
        for feat in feats:
            props = feat.get("properties") or {}
            emd_cd = str(props.get("emd_cd", ""))
            emd_nm = str(props.get("emd_kor_nm") or props.get("full_nm") or "")
            if sig_cd and emd_cd and not emd_cd.startswith(sig_cd[:5]):
                continue
            if neighborhood and neighborhood not in emd_nm:
                continue
            if emd_cd:
                codes.append(emd_cd)
        total = int(response.get("record", {}).get("total", 0))
        if page * 100 >= total:
            break
        page += 1
    return sorted(set(codes))


def _internal_to_api(row: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    scores_raw = row.get("scores") or {}
    parcel = {
        "id": row["id"],
        "name": row["name"],
        "district": row["district"],
        "neighborhood": row["neighborhood"],
        "lat": row["lat"],
        "lng": row["lng"],
        "areaSqm": row["area_sqm"],
        "parcelType": row["parcel_type"],
        "landCategory": row.get("land_category"),
        "ownership": row["ownership"],
        "soilType": row["soil_type"],
        "solarIrradiance": row["solar_irradiance"],
        "monthlyIrradiance": row.get("monthly_irradiance"),
        "sunlightHours": row["sunlight_hours"],
        "heatIsland": row["heat_island"],
        "surfaceTempSummer": row["surface_temp_summer"],
        "airQuality": row.get("air_quality"),
        # 미연동 지표는 null (가짜 0 위장 금지)
        "nearbyHouseholds": row.get("nearby_households"),
        "pedestrianFlow": row.get("pedestrian_flow"),
        "roadAdjacent": row.get("road_adjacent", False),
        "waterAccess": row.get("water_access", False),
        "electricityAccess": row.get("electricity_access", False),
        "nearbySchools": row.get("nearby_schools"),
        "nearbyHospitals": row.get("nearby_hospitals"),
        "nearbyParks": row.get("nearby_parks"),
        "nearbySubwayStations": row.get("nearby_subway_stations"),
        "regulatoryRestriction": row.get("regulatory_restriction", ""),
        "regulations": row.get("regulations") or [],
        "sumokFeasibility": row.get("sumok_feasibility"),
        "confidence": row["confidence"],
        "dataSource": "VWorld Live",
        "dataProvenance": row.get("data_provenance"),
        "pnu": row.get("pnu"),
    }
    scores = {
        "treeScore": scores_raw.get("tree_score", 0),
        "gardenScore": scores_raw.get("garden_score", 0),
        "solarScore": scores_raw.get("solar_score", 0),
        "topRecommendation": scores_raw.get("top_recommendation", "TREE"),
        "uncertainty": scores_raw.get("uncertainty", 6),
        "treeBreakdown": list(scores_raw.get("tree_breakdown") or []),
        "gardenBreakdown": list(scores_raw.get("garden_breakdown") or []),
        "solarBreakdown": list(scores_raw.get("solar_breakdown") or []),
    }
    parcel["scores"] = scores
    return parcel, scores


def _score_for_use(parcel: Dict[str, Any], use: Optional[str] = None) -> float:
    """용도 키워드가 있으면 해당 점수, 없으면 topRecommendation 점수."""
    s = parcel.get("scores") or {}
    rec = (use or s.get("topRecommendation") or "TREE").upper()
    if rec in ("TREE", "SUMOK"):
        return float(s.get("treeScore") or 0)
    if rec == "GARDEN":
        return float(s.get("gardenScore") or 0)
    if rec == "SOLAR":
        return float(s.get("solarScore") or 0)
    return max(
        float(s.get("treeScore") or 0),
        float(s.get("gardenScore") or 0),
        float(s.get("solarScore") or 0),
    )


def _top_score(parcel: Dict[str, Any]) -> float:
    return _score_for_use(parcel, None)


async def live_search(criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    실시간 VWorld 검색. criteria: district, neighborhood, parcelType, topRecommendation,
    minScore, limit, minArea, maxArea
    """
    if not settings.vworld_api_key:
        raise VWorldDiscoveryError("VWORLD_API_KEY가 설정되지 않았습니다.")

    region_name = criteria.get("district") or criteria.get("region")
    if not region_name:
        return {
            "results": [],
            "meta": {"source": "vworld_live", "error": "region_required"},
            "message": "지역을 입력해 주세요. 예: 용산구, 해운대구, 성남시, 제주시",
        }

    try:
        region = await resolve_region(region_name)
    except VWorldDiscoveryError as e:
        return {
            "results": [],
            "meta": {"source": "vworld_live", "region": region_name, "error": "upstream"},
            "message": f"VWorld 실시간 검색에 실패했습니다. ({e})",
        }
    if not region:
        return {
            "results": [],
            "meta": {"source": "vworld_live", "region": region_name},
            "message": f"'{region_name}' 행정구역을 VWorld에서 찾지 못했습니다.",
        }

    min_area = float(criteria.get("minArea") or 350)
    max_area = float(criteria.get("maxArea") or 15_000)
    limit = min(int(criteria.get("limit") or 10), 20)
    neighborhood = criteria.get("neighborhood")

    import httpx

    client = VWorldDataClient()
    data_client = VWorldDataClient()
    candidates: List[Dict[str, Any]] = []
    seen_pnu: set[str] = set()

    try:
        async with httpx.AsyncClient(timeout=25.0) as http:
            emd_codes = await _emd_codes_in_bbox(
                client, http, region["bbox"], region["sig_cd"], neighborhood
            )
            if not emd_codes:
                return {
                    "results": [],
                    "meta": {"source": "vworld_live", "region": region["name"]},
                    "message": f"{region['name']}에서 읍면동 데이터를 찾지 못했습니다.",
                }

            # 실시간 응답: 읍면동 샘플 수 제한 (속도 우선)
            max_emd = 12 if neighborhood else 8
            step = max(1, len(emd_codes) // max_emd)
            sampled = emd_codes[::step][:max_emd]

            # 1) 후보 필지 수집 (enrich 없이 빠름)
            feature_picks: List[Dict[str, Any]] = []
            for emd_cd in sampled:
                feats, _ = await data_client.fetch_cadastral_by_emd(emd_cd, page=1, size=40)
                picks: List[Dict[str, Any]] = []
                for feat in feats:
                    props = feat.get("properties") or {}
                    pnu = str(props.get("pnu") or "")
                    if not pnu or pnu in seen_pnu:
                        continue
                    area = geometry_area_sqm(feat.get("geometry"))
                    if area < min_area or area > max_area:
                        continue
                    picks.append({**feat, "_area": area})
                if not picks:
                    continue
                picks.sort(key=lambda f: f["_area"], reverse=True)
                top = picks[0]
                pnu = str((top.get("properties") or {}).get("pnu") or "")
                if pnu and pnu not in seen_pnu:
                    seen_pnu.add(pnu)
                    feature_picks.append(top)
                if len(feature_picks) >= limit * 2:
                    break

            # 2) 상세 enrich 병렬 (동시 4개)
            sem = asyncio.Semaphore(4)

            async def _enrich(feat: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                async with sem:
                    try:
                        return await build_parcel_from_feature(feat, enrich_regulations=True)
                    except Exception:
                        return None

            if feature_picks:
                rows = await asyncio.gather(*[_enrich(f) for f in feature_picks])
                for row in rows:
                    if row and row.get("pnu"):
                        candidates.append(row)
    except VWorldDiscoveryError as e:
        return {
            "results": [],
            "meta": {"source": "vworld_live", "region": region.get("name", region_name), "error": "upstream"},
            "message": f"VWorld 실시간 검색에 실패했습니다. ({e})",
        }
    except Exception as e:
        logger.warning("live_search failed for %r: %s", region_name, e)
        return {
            "results": [],
            "meta": {"source": "vworld_live", "region": region.get("name", region_name), "error": "upstream"},
            "message": f"VWorld 실시간 검색에 실패했습니다. 잠시 후 다시 시도해 주세요.",
        }

    preferred = criteria.get("topRecommendation")  # TREE/GARDEN/SOLAR — 정렬 우선, 기본은 하드 필터 아님
    strict_top = bool(criteria.get("strictTopRecommendation"))
    min_score = criteria.get("minScore")

    api_results: List[Dict[str, Any]] = []
    for row in candidates:
        parcel, scores = _internal_to_api(row)
        if criteria.get("parcelType") and parcel["parcelType"] != criteria["parcelType"]:
            continue
        # 예: "금천구 수목" → topRecommendation=TREE 이지만 1위가 SOLAR 인 부지도
        # 수목 점수가 높으면 보여야 함. 하드 필터는 strictTopRecommendation 일 때만.
        if preferred and strict_top:
            if scores.get("topRecommendation") != preferred:
                continue
        if min_score is not None:
            if _score_for_use(parcel, preferred) < float(min_score):
                continue
        _cache_put(parcel, scores)
        api_results.append(parcel)

    # 선호 용도 점수로 정렬 (수목 검색이면 treeScore 내림차순)
    api_results.sort(
        key=lambda p: _score_for_use(p, preferred),
        reverse=True,
    )
    api_results = api_results[:limit]

    msg = None
    if not api_results and candidates:
        msg = (
            f"{region['name']}에서 후보 {len(candidates)}건을 찾았으나 "
            f"필터 조건(유형/최소점수)에 맞는 결과가 없습니다."
        )
    elif not api_results:
        msg = f"{region['name']}에서 조건에 맞는 부지를 찾지 못했습니다. 면적·지역 조건을 넓혀 보세요."

    return {
        "results": api_results,
        "meta": {
            "source": "vworld_live",
            "region": region["name"],
            "full_name": region.get("full_name"),
            "sig_cd": region.get("sig_cd"),
            "sampled_emd": len(sampled),
            "candidates": len(candidates),
            "preferredUse": preferred,
            "strictTopRecommendation": strict_top,
        },
        "message": msg,
    }


async def live_get_parcel(parcel_id: str) -> Optional[Dict[str, Any]]:
    """캐시 또는 PNU 단건 조회."""
    cached = _LIVE_CACHE.get(parcel_id)
    if cached:
        return {"parcel": cached["parcel"], "scores": cached["scores"], "source": "vworld_live_cache"}

    pnu = _parse_pnu_from_id(parcel_id)
    if not pnu:
        return None

    import httpx

    client = VWorldDataClient()
    client._check_key()
    params = {
        "data": "LP_PA_CBND_BUBUN",
        "size": 1,
        "page": 1,
        "attrFilter": f"pnu:=:{pnu}",
        "geometry": "true",
        "attribute": "true",
        "crs": "EPSG:4326",
    }
    response: Dict[str, Any] = {}
    last_error: Optional[Exception] = None

    async with httpx.AsyncClient(timeout=30.0) as http:
        for attempt in range(3):
            try:
                response = await _data_get(client, http, params)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning(
                    "VWorld _data_get failed for parcel_id=%s pnu=%s attempt=%d: %s",
                    parcel_id,
                    pnu,
                    attempt + 1,
                    exc,
                )
                if attempt < 2:
                    await asyncio.sleep(0.5)
                continue

            if response.get("status") == "OK":
                feats = response.get("result", {}).get("featureCollection", {}).get("features", [])
                if feats:
                    break
                last_error = None
            if attempt < 2:
                await asyncio.sleep(0.5)
        else:
            logger.info(
                "VWorld returned non-OK or empty features after retries for parcel_id=%s pnu=%s (status=%s error=%s)",
                parcel_id,
                pnu,
                response.get("status"),
                last_error,
            )
            return None

        row = await build_parcel_from_feature(feats[0], enrich_regulations=True)
        if not row:
            return None
        parcel, scores = _internal_to_api(row)
        _cache_put(parcel, scores)
        return {"parcel": parcel, "scores": scores, "source": "vworld_live"}


def live_stats_from_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not results:
        return {
            "total": 0,
            "avgTreeScore": 0,
            "avgGardenScore": 0,
            "avgSolarScore": 0,
            "topTreeCount": 0,
            "topGardenCount": 0,
            "topSolarCount": 0,
            "totalAreaSqm": 0,
        }
    n = len(results)
    trees = [r.get("scores", {}).get("treeScore", 0) for r in results]
    gardens = [r.get("scores", {}).get("gardenScore", 0) for r in results]
    solars = [r.get("scores", {}).get("solarScore", 0) for r in results]
    recs = [r.get("scores", {}).get("topRecommendation") for r in results]
    return {
        "total": n,
        "avgTreeScore": round(sum(trees) / n),
        "avgGardenScore": round(sum(gardens) / n),
        "avgSolarScore": round(sum(solars) / n),
        "topTreeCount": recs.count("TREE"),
        "topGardenCount": recs.count("GARDEN"),
        "topSolarCount": recs.count("SOLAR"),
        "totalAreaSqm": round(sum(r.get("areaSqm", 0) for r in results)),
    }