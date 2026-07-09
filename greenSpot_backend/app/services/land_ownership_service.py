"""토지소유정보 API 클라이언트.

지원:
1) VWorld NED `getPossessionAttr` (권장)
   - URL 예: https://api.vworld.kr/ned/data/getPossessionAttr
   - 파라미터: key, domain, pnu, format=json
   - 응답: possessions.field[] 의 posesnSeCodeNm / posesnSeCode

2) 공공데이터포털 일반 속성조회
   - serviceKey + pnu
   - 응답: response.body.items

API 미연동/실패 시 ownership=UNKNOWN, dataAvailable=False.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from app.core.config import settings


class LandOwnershipNotConfigured(Exception):
    pass


# VWorld / 공공데이터 응답에서 사용할 소유구분 필드
_OWNER_CODE_FIELDS = (
    "posesnSeCode",
    "ownerSe",
    "ownerCode",
    "ownerSeCode",
    "possOwnerGbn",
    "ownerGbn",
)
_OWNER_NAME_FIELDS = (
    "posesnSeCodeNm",
    "ownerNm",
    "ownerName",
    "possOwnerNm",
    "owner",
)


def _normalize_owner(raw: Any) -> str:
    """소유구분 코드/명칭 → GreenSpot ownership (PUBLIC/PRIVATE/UNKNOWN)."""
    if raw is None:
        return "UNKNOWN"
    value = str(raw).strip()
    if not value or value in ("-", "null", "NULL"):
        return "UNKNOWN"

    upper = value.upper()
    # 공공/국유/공유(지자체)
    public_tokens = (
        "국유", "국유지", "공유", "공유지", "지자체", "공공", "국가", "시유", "도유",
        "군유", "구유", "PUBLIC", "GOVERNMENT", "중앙부처",
    )
    for token in public_tokens:
        if token.upper() in upper or token in value:
            return "PUBLIC"

    # 민간/개인/법인
    private_tokens = (
        "개인", "사유", "사유지", "법인", "PRIVATE", "CORPORATE", "민간",
    )
    for token in private_tokens:
        if token.upper() in upper or token in value:
            return "PRIVATE"

    # VWorld posesnSeCode: 01 개인, 02 국유지, 03 공유지 등 (문서에 따라 상이)
    if value in ("01", "1"):
        return "PRIVATE"
    if value in ("02", "2", "03", "3", "04", "4"):
        return "PUBLIC"

    return "UNKNOWN"


def _extract_items(data: Any) -> List[Dict[str, Any]]:
    """VWorld / data.go.kr 응답에서 field/items 목록을 추출한다."""
    if not isinstance(data, dict):
        return []

    # VWorld getPossessionAttr: { "possessions": { "field": [...] } }
    for wrapper_key in ("possessions", "possession", "landOwnerships", "landOwnership"):
        wrapped = data.get(wrapper_key)
        if isinstance(wrapped, dict):
            field = wrapped.get("field") or wrapped.get("items") or wrapped.get("item") or wrapped.get("list")
            if isinstance(field, dict):
                return [field]
            if isinstance(field, list):
                return [x for x in field if isinstance(x, dict)]
        if isinstance(wrapped, list):
            return [x for x in wrapped if isinstance(x, dict)]

    # 공공데이터포털: { "response": { "body": { "items": ... } } }
    response = data.get("response") or {}
    body = response.get("body") if isinstance(response, dict) else {}
    items = None
    if isinstance(body, dict):
        items = body.get("items") or body.get("item")
    if items is None:
        items = data.get("items") or data.get("item") or data.get("list") or data.get("field")
    if isinstance(items, dict):
        # body.items.item 형태
        nested = items.get("item") or items.get("field")
        if nested is not None:
            items = nested
        else:
            return [items]
    if isinstance(items, list):
        return [x for x in items if isinstance(x, dict)]
    return []


class LandOwnershipClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = (api_key or settings.land_ownership_api_key or "").strip()
        self.base_url = (base_url or settings.land_ownership_base_url or "").strip()

    def _check_key(self):
        if not self.api_key:
            raise LandOwnershipNotConfigured("LAND_OWNERSHIP_API_KEY가 설정되지 않았습니다.")
        if not self.base_url:
            raise LandOwnershipNotConfigured("LAND_OWNERSHIP_BASE_URL이 설정되지 않았습니다.")

    def _is_vworld(self) -> bool:
        host = (urlparse(self.base_url).hostname or "").lower()
        path = (urlparse(self.base_url).path or "").lower()
        return "vworld" in host or "possession" in path or "getpossession" in path

    def _extract_owner(self, item: Dict[str, Any]) -> str:
        for field in _OWNER_CODE_FIELDS:
            if field in item and item[field] not in (None, ""):
                ownership = _normalize_owner(item[field])
                if ownership != "UNKNOWN":
                    return ownership
        for field in _OWNER_NAME_FIELDS:
            if field in item and item[field] not in (None, ""):
                ownership = _normalize_owner(item[field])
                if ownership != "UNKNOWN":
                    return ownership
        return "UNKNOWN"

    def _resolve_url(self) -> str:
        url = self.base_url.rstrip("/")
        if self._is_vworld():
            # 이미 getPossessionAttr 등 전체 path면 그대로
            if "getpossession" in url.lower() or "possession" in url.lower():
                return url
            return f"{url}/ned/data/getPossessionAttr"

        # 공공데이터포털: 마지막 세그먼트에 ownership/possession 없으면 기본 path
        last_seg = url.split("/")[-1].lower()
        if "ownership" in last_seg or "possession" in last_seg or "owner" in last_seg:
            return url
        return f"{url}/1613000/OwnerInfoService/getLandOwnerInfo"

    async def get_ownership_by_pnu(
        self,
        pnu: str,
        *,
        num_of_rows: int = 100,
        page_no: int = 1,
    ) -> Dict[str, Any]:
        """PNU 기반 토지소유정보를 조회한다."""
        self._check_key()
        url = self._resolve_url()

        if self._is_vworld():
            params: Dict[str, Any] = {
                "key": self.api_key,
                "domain": settings.vworld_domain or "localhost",
                "pnu": pnu,
                "format": "json",
                "numOfRows": num_of_rows,
                "pageNo": page_no,
            }
            source = "VWorld 토지소유정보"
        else:
            params = {
                "serviceKey": self.api_key,
                "returnType": "json",
                "numOfRows": num_of_rows,
                "pageNo": page_no,
                "pnu": pnu,
            }
            source = "국토교통부 토지소유정보"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            return {
                "pnu": pnu,
                "ownership": "UNKNOWN",
                "dataAvailable": False,
                "source": source,
            }

        items = _extract_items(data)
        if not items:
            return {
                "pnu": pnu,
                "ownership": "UNKNOWN",
                "dataAvailable": False,
                "source": source,
            }

        ownership = self._extract_owner(items[0])
        return {
            "pnu": pnu,
            "ownership": ownership,
            "dataAvailable": ownership != "UNKNOWN",
            "source": source,
            "raw": items[0],
        }

    async def get_ownership(
        self,
        pnu: str,
        fallback: str = "UNKNOWN",
    ) -> Dict[str, Any]:
        """소유정보 실제값 조회. 실패/미연동 시 fallback 값을 사용한다."""
        if not self.api_key or not self.base_url:
            return {
                "pnu": pnu,
                "ownership": fallback,
                "dataAvailable": False,
                "source": "국토교통부 토지소유정보 (미연동)",
            }
        result = await self.get_ownership_by_pnu(pnu)
        if not result["dataAvailable"]:
            result["ownership"] = fallback
        return result


def client() -> LandOwnershipClient:
    return LandOwnershipClient()
