from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


# ========== Auth Schemas ==========

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    # F-20 제거 후 로그인 응답에 사용자 정보 포함 (별도 GET /users/me 없음)
    user: Optional[UserResponse] = None


# ========== Parcel Schemas ==========

class ParcelBase(BaseModel):
    id: str
    name: str
    district: str
    neighborhood: str
    lat: float
    lng: float
    areaSqm: float = Field(alias="area_sqm")
    parcelType: str = Field(alias="parcel_type")
    ownership: str
    soilType: str = Field(alias="soil_type")
    solarIrradiance: float = Field(alias="solar_irradiance")
    monthlyIrradiance: Optional[List[float]] = Field(None, alias="monthly_irradiance")
    sunlightHours: float = Field(alias="sunlight_hours")
    heatIsland: float = Field(alias="heat_island")
    surfaceTempSummer: float = Field(alias="surface_temp_summer")
    airQuality: float = Field(alias="air_quality")
    nearbyHouseholds: int = Field(alias="nearby_households")
    pedestrianFlow: int = Field(alias="pedestrian_flow")
    roadAdjacent: bool = Field(alias="road_adjacent")
    waterAccess: bool = Field(alias="water_access")
    electricityAccess: bool = Field(alias="electricity_access")
    nearbySchools: int = Field(alias="nearby_schools")
    nearbyHospitals: int = Field(alias="nearby_hospitals")
    nearbyParks: int = Field(alias="nearby_parks")
    nearbySubwayStations: int = Field(alias="nearby_subway_stations")
    regulatoryRestriction: str = Field(alias="regulatory_restriction")
    confidence: float
    dataProvenance: Optional[Dict[str, Any]] = Field(None, alias="data_provenance")


class ParcelResponse(ParcelBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ParcelListResponse(BaseModel):
    parcels: List[Dict[str, Any]]
    stats: Dict[str, Any]
    source: str
    vworldEnabled: bool = False


class ParcelDetailResponse(BaseModel):
    parcel: Dict[str, Any]
    scores: Dict[str, Any]
    source: str


# ========== Score Schemas ==========

class ScoreResponse(BaseModel):
    treeScore: float = Field(alias="tree_score")
    gardenScore: float = Field(alias="garden_score")
    solarScore: float = Field(alias="solar_score")
    topRecommendation: str = Field(alias="top_recommendation")
    uncertainty: float
    treeBreakdown: List[str] = Field(alias="tree_breakdown", default=[])
    gardenBreakdown: List[str] = Field(alias="garden_breakdown", default=[])
    solarBreakdown: List[str] = Field(alias="solar_breakdown", default=[])


# ========== Agent Schemas ==========

class AgentSearchRequest(BaseModel):
    query: str = Field(min_length=2)


class AgentSearchResponse(BaseModel):
    query: str
    criteria: Dict[str, Any]
    results: List[Dict[str, Any]]
    summary: str
    count: int
    elapsed_ms: int
    source: str


# ========== Explain Schemas ==========

class ExplainResponse(BaseModel):
    parcelId: str
    explanation: str
    facts: Dict[str, Any]
    promptVersion: str
    uncertainty: float


# ========== Simulation Schemas ==========

class SimulateRequest(BaseModel):
    scenarioType: str = Field(alias="scenario_type")
    quantity: int = Field(default=10, ge=1)
    # 라이브(VWorld) 필지: 상세 화면이 이미 아는 면적/이름 (재조회 실패 시 폴백)
    areaSqm: Optional[float] = Field(default=None, alias="area_sqm", ge=0)
    parcelName: Optional[str] = Field(default=None, alias="parcel_name")

    model_config = ConfigDict(populate_by_name=True)


class SimulateEffects(BaseModel):
    model_config = ConfigDict(extra="allow")

    pass


class ScenarioResponse(BaseModel):
    parcelId: str
    parcelName: str
    parcelArea: float
    scenarios: Dict[str, Any]
    elapsed_ms: int


# ========== Compare Schemas ==========

class CompareRequest(BaseModel):
    ids: List[str] = Field(min_length=2, max_length=3)


class CompareResponse(BaseModel):
    comparison: List[Dict[str, Any]]
    ranking: Dict[str, List[str]]


# ========== Report Schemas ==========

class ReportRequest(BaseModel):
    parcelId: str
    format: str = Field(pattern="^(markdown|json)$")


# ========== Export Schemas ==========

class StatsResponse(BaseModel):
    totalParcels: int
    byDistrict: List[Dict[str, Any]]
    byType: List[Dict[str, Any]]
    byRecommendation: Dict[str, int]
    generatedAt: datetime


# ========== Bookmark Schemas ==========

class BookmarkResponse(BaseModel):
    bookmarks: List[Dict[str, Any]]


class BookmarkCreateRequest(BaseModel):
    parcelId: str
    # 라이브 VW- 필지용 스냅샷 (DB에 없어도 북마크 가능)
    parcelName: Optional[str] = None
    district: Optional[str] = None
    topRecommendation: Optional[str] = None
    topScore: Optional[float] = None


class BookmarkCreateResponse(BaseModel):
    ok: bool


class BookmarkDeleteResponse(BaseModel):
    ok: bool


# ========== Share Schemas ==========

class ShareCreateRequest(BaseModel):
    parcelId: str


class ShareCreateResponse(BaseModel):
    shareId: str
    url: str


# ========== Health Schemas ==========

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str
    stats: Dict[str, Any]
    environment: Dict[str, Any]
    elapsed_ms: int


class HealthErrorResponse(BaseModel):
    status: str
    database: str
    error: str


# ========== VWorld Schemas ==========

class VWorldPossessionResponse(BaseModel):
    pnu: str
    contentType: str = "image/png"
    dataAvailable: bool


class VWorldLandCharacteristicsResponse(BaseModel):
    pnu: str
    items: List[Dict[str, Any]]
    count: int
    source: str = "vworld"
    dataAvailable: bool
    year: str


class VisualCrossingClimateResponse(BaseModel):
    source: str = "visualcrossing"
    district: Optional[str]
    location: str
    start: str
    end: str
    solarIrradiance: float
    sunlightHours: float
    avgTemperature: float
    dataAvailable: bool


class VisualCrossingHeatResponse(BaseModel):
    source: str = "visualcrossing"
    district: Optional[str]
    location: str
    period: Dict[str, str]
    heatIsland: Optional[float]
    surfaceTempSummer: Optional[float]
    avgTemperature: Optional[float]
    maxTemperature: Optional[float]
    dataAvailable: bool


class VisualCrossingTimelineResponse(BaseModel):
    source: str = "visualcrossing"
    location: str
    start: str
    end: str
    days: List[Dict[str, Any]]
    count: int
    dataAvailable: bool
