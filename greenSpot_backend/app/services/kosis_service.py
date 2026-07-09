"""
KOSIS Open API 클라이언트 (국가통계포털, kosis.kr).

부지별 인구·가구 통계를 KOSIS Open API에서 조회하여
명세서 F-25 (KOSIS 인구·가구 통계 연동) 응답을 생성한다.

기본 통계:
- DT_1B04005N : 주민등록인구(행정구역별) → itmId="T1" 총인구
- DT_1B41     : 인구총조사 가구         → itmId="T1" 총가구

참고:
- https://kosis.kr/openapi/openApiIntro.do
- https://kosis.kr/openapi/Param/statisticsParameterData.do
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings


# ---------------------------------------------------------------------------
# 서울 5개 자치구 → KOSIS objL1 (시군구 5자리 코드)
# ---------------------------------------------------------------------------
# KOSIS 주민등록인구/인구총조사 통계의 objL1 은 시군구 코드(5자리) 이다.
# 출처: 행정표준코드(시군구) — 통계청 KOSIS 행정구역 코드 체계.
DISTRICT_TO_OBJ_L1: Dict[str, str] = {
    "종로구": "11110",
    "중구": "11140",
    "용산구": "11170",
    "성동구": "11200",
    "광진구": "11215",
    "동대문구": "11230",
    "중랑구": "11260",
    "성북구": "11290",
    "강북구": "11305",
    "도봉구": "11320",
    "노원구": "11350",
    "은평구": "11380",
    "서대문구": "11410",
    "마포구": "11440",
    "양천구": "11470",
    "강서구": "11500",
    "구로구": "11530",
    "금천구": "11545",
    "영등포구": "11560",
    "동작구": "11590",
    "관악구": "11620",
    "서초구": "11650",
    "강남구": "11680",
    "송파구": "11710",
    "강동구": "11740",
}


class KosisNotConfigured(Exception):
    """KOSIS API 키가 설정되지 않았을 때 발생하는 예외."""


class KosisClient:
    """KOSIS Open API 비동기 클라이언트."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        org_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = (settings.kosis_api_key if api_key is None else api_key).strip()
        self.org_id = (org_id or settings.kosis_org_id or "").strip()
        self.base_url = (base_url or settings.kosis_base_url or "").strip()

    # ------------------------------------------------------------------ helpers
    def _check_key(self):
        if not self.api_key:
            raise KosisNotConfigured(
                "KOSIS_API_KEY가 설정되지 않았습니다. .env에 KOSIS_API_KEY를 입력하세요."
            )

    @staticmethod
    def _district_to_obj_l1(district: str) -> str:
        """서울 자치구 → KOSIS objL1 (시군구 5자리) 코드를 반환한다."""
        if district not in DISTRICT_TO_OBJ_L1:
            raise ValueError(
                f"KOSIS 매핑되지 않은 자치구입니다: {district!r} "
                f"(지원: {sorted(DISTRICT_TO_OBJ_L1.keys())})"
            )
        return DISTRICT_TO_OBJ_L1[district]

    # ------------------------------------------------------------------ API
    async def get_statistics(
        self,
        tbl_id: str,
        itm_id: str,
        obj_l1: str,
        start_prd: str,
        end_prd: str,
        prd_se: str = "Y",
    ) -> List[Dict[str, Any]]:
        """KOSIS statisticsParameterData.do 를 호출해 원본 row 리스트를 반환한다."""
        self._check_key()
        params = {
            "method": "getList",
            "apiKey": self.api_key,
            "itmId": itm_id,
            "objL1": obj_l1,
            "objL2": "",
            "objL3": "",
            "objL4": "",
            "objL5": "",
            "format": "json",
            "jsonVD": "Y",
            "prdSe": prd_se,
            "startPrdDe": start_prd,
            "endPrdDe": end_prd,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(self.base_url, params=params)
            resp.raise_for_status()
            data = resp.json()

        # KOSIS 응답은 호출 옵션에 따라 다양한 키(list/rows/data 등)로 row 가 반환된다.
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("list", "rows", "data", "result"):
                rows = data.get(key)
                if isinstance(rows, list):
                    return rows
            # errCd != 0 인 경우 빈 응답으로 취급
            err_cd = str(data.get("errCd", "")).strip()
            if err_cd and err_cd != "0":
                return []
        return []

    # ------------------------------------------------------------------ high-level
    async def get_population(
        self, district: str, year: Optional[int] = None
    ) -> Dict[str, Any]:
        """자치구 + 연도 → {source, district, year, population, dataAvailable}."""
        try:
            obj_l1 = self._district_to_obj_l1(district)
        except ValueError:
            return self._fallback_population(district, year)

        yr = year if year is not None else datetime.now(timezone.utc).year - 1
        try:
            rows = await self.get_statistics(
                tbl_id=settings.kosis_pop_tbl_id,
                itm_id="T1",  # 총인구
                obj_l1=obj_l1,
                start_prd=str(yr),
                end_prd=str(yr),
            )
        except (httpx.HTTPError, KeyError, ValueError):
            return self._fallback_population(district, yr)

        if not rows:
            return self._fallback_population(district, yr)

        population = self._extract_numeric(rows)
        if population is None:
            return self._fallback_population(district, yr)

        return {
            "source": "kosis",
            "district": district,
            "year": yr,
            "population": population,
            "dataAvailable": True,
        }

    async def get_household(
        self, district: str, year: Optional[int] = None
    ) -> Dict[str, Any]:
        """자치구 + 연도 → {source, district, year, households, dataAvailable}.

        year 미지정 시 작년→재작년 순으로 조회해 최신 가용 연도를 쓴다.
        """
        try:
            obj_l1 = self._district_to_obj_l1(district)
        except ValueError:
            return self._fallback_household(district, year)

        if year is not None:
            years = [year]
        else:
            base = datetime.now(timezone.utc).year - 1
            years = [base, base - 1, base - 2]

        last_yr = years[-1]
        for yr in years:
            last_yr = yr
            try:
                rows = await self.get_statistics(
                    tbl_id=settings.kosis_hh_tbl_id,
                    itm_id="T1",  # 총가구
                    obj_l1=obj_l1,
                    start_prd=str(yr),
                    end_prd=str(yr),
                )
            except (httpx.HTTPError, KeyError, ValueError):
                continue

            if not rows:
                continue

            households = self._extract_numeric(rows)
            if households is None:
                continue

            return {
                "source": "kosis",
                "district": district,
                "year": yr,
                "households": households,
                "dataAvailable": True,
            }

        return self._fallback_household(district, last_yr)

    # ------------------------------------------------------------------ internals
    @staticmethod
    def _extract_numeric(rows: List[Dict[str, Any]]) -> Optional[int]:
        """row 리스트에서 숫자 값을 추출한다 (KOSIS 응답 키 변동 대응)."""
        # 숫자 값이 들어있는 흔한 키 우선순위
        candidate_keys = ("DT", "C1", "C2", "C3", "VALUE", "value", "data", "DATA")
        for row in rows:
            if not isinstance(row, dict):
                continue
            for key in candidate_keys:
                if key not in row:
                    continue
                raw = row[key]
                if raw is None or raw == "":
                    continue
                try:
                    # 천단위 콤마/문자열 정수 모두 허용
                    if isinstance(raw, str):
                        cleaned = raw.replace(",", "").strip()
                        if not cleaned:
                            continue
                        return int(float(cleaned))
                    if isinstance(raw, (int, float)):
                        return int(raw)
                except (ValueError, TypeError):
                    continue
        return None

    @staticmethod
    def _fallback_population(district: str, year: Optional[int]) -> Dict[str, Any]:
        return {
            "source": "kosis",
            "district": district,
            "year": year,
            "population": None,
            "dataAvailable": False,
        }

    @staticmethod
    def _fallback_household(district: str, year: Optional[int]) -> Dict[str, Any]:
        return {
            "source": "kosis",
            "district": district,
            "year": year,
            "households": None,
            "dataAvailable": False,
        }


def client() -> KosisClient:
    """기본 settings 로 KosisClient 인스턴스를 생성하는 팩토리."""
    return KosisClient()
