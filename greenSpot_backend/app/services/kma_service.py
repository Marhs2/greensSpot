"""KMA(기상청 ASOS) 서비스 스텁.

레거시 호환용: /api/v1/gs/parcels/{id}/enrich 는 Visual Crossing 으로 대체되었으며,
본 모듈은 import 오류를 방지하기 위한 최소 스텁이다.
"""
from typing import Any, Dict


class KmaNotConfigured(Exception):
    pass


class KmaClient:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or ""

    async def get_climate_for_district(self, district: str) -> Dict[str, Any]:
        raise KmaNotConfigured("KMA_API_KEY가 설정되지 않았습니다.")


def client() -> KmaClient:
    return KmaClient()
