from pydantic_settings import BaseSettings
from pydantic import ConfigDict, model_validator
from typing import List, Any
import json
import logging
import secrets as secrets_mod

_log = logging.getLogger(__name__)

_DEFAULT_SECRET = "your-super-secret-key-change-in-production"


class Settings(BaseSettings):
    app_name: str = "GreenSpot API"
    app_version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"

    database_url: str = "sqlite+aiosqlite:///./greenspot.db"

    secret_key: str = _DEFAULT_SECRET
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # 공유 링크 공개 베이스 URL (예: https://app.example.com). 비면 request origin 사용.
    public_base_url: str = ""

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ai_model: str = "gpt-4o-mini"

    # Groq (Qwen 등) LLM
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.6-27b"

    vworld_api_key: str = ""
    vworld_domain: str = "localhost"

    # Visual Crossing Weather API (https://www.visualcrossing.com/weather-api)
    visual_crossing_api_key: str = ""
    visual_crossing_base_url: str = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"

    # KOSIS Open API (국가통계포털) — 주민등록인구/인구총조사 가구
    # 키 발급: https://kosis.kr/openapi/openApiIntro.do
    kosis_api_key: str = ""
    kosis_org_id: str = "101"  # 통계청
    kosis_pop_tbl_id: str = "DT_1B04005N"  # 주민등록인구(행정구역별)
    kosis_hh_tbl_id: str = "DT_1B41"      # 인구총조사 가구
    kosis_base_url: str = "https://kosis.kr/openapi/Param/statisticsParameterData.do"

    # KMA(기상청 ASOS) — 향후 legacy 호환을 위한 자리표시자
    # /api/v1/gs/parcels/{id}/enrich 는 Visual Crossing 으로 대체되었으며,
    # 본 키는 health-check 응답 호환을 위해서만 유지한다.
    kma_api_key: str = ""

    # 국토교통부 토지소유정보 API (공공데이터포털)
    # 키 발급: [REDACTED-URL]
    land_ownership_api_key: str = ""
    land_ownership_base_url: str = "[REDACTED-URL]"

    # 한국환경공단 AirKorea 대기오염정보 API
    # 키 발급: [REDACTED-URL]
    airkorea_api_key: str = ""
    airkorea_base_url: str = "[REDACTED-URL]"

    # 농촌진흥청 토양정보 API (흙토람 / 공공데이터포털)
    # 키 발급: [REDACTED-URL]
    soil_api_key: str = ""
    soil_base_url: str = "[REDACTED-URL]"

    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = ConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @model_validator(mode="after")
    def _guard_secret_key(self) -> "Settings":
        env = (self.environment or "development").lower()
        weak = not self.secret_key or self.secret_key == _DEFAULT_SECRET
        if weak and env in ("production", "prod", "staging"):
            raise ValueError(
                "SECRET_KEY 가 기본값이거나 비어 있습니다. "
                "운영/스테이징 환경에서는 강력한 SECRET_KEY 를 .env 에 설정하세요."
            )
        if weak:
            # 개발: 프로세스별 임시 키 (재시작 시 기존 토큰 무효화)
            object.__setattr__(self, "secret_key", secrets_mod.token_urlsafe(32))
            _log.warning(
                "SECRET_KEY 미설정 — 개발용 임시 키를 사용합니다. "
                "재시작 시 로그인 토큰이 무효화됩니다."
            )
        return self


settings = Settings()