// GreenSpot — shared types aligned to the backend API response shapes.
// Reference: backend/docs/api.md, app/schemas/schemas.py, app/services/parcel_service.py

export type ParcelType = "VACANT_LOT" | "ROOFTOP" | "UNUSED_LAND" | "ABANDONED" | "BROWNFIELD";
export type LandCategory =
  | "AGRICULTURE"
  | "FOREST"
  | "INDUSTRIAL"
  | "COMMERCIAL"
  | "RESIDENTIAL"
  | "PARK"
  | "CEMETERY"
  | "INFRASTRUCTURE"
  | "WATER"
  | "MIXED";
export type Ownership = "PUBLIC" | "PRIVATE" | "UNKNOWN";
export type SoilType = "LOAM" | "CLAY" | "SAND" | "ROCKY" | "UNKNOWN";
export type Regulation = "NONE" | "GREEN_BELT" | "HISTORICAL" | "FLOOD_ZONE";
export type UseKey = "TREE" | "GARDEN" | "SOLAR";

export interface Scores {
  treeScore: number;
  gardenScore: number;
  solarScore: number;
  topRecommendation: UseKey;
  uncertainty: number;
  confidence?: number;
  treeBreakdown?: string[];
  gardenBreakdown?: string[];
  solarBreakdown?: string[];
}

export interface Parcel {
  id: string;
  name: string;
  district: string;
  neighborhood: string;
  lat: number;
  lng: number;
  areaSqm: number;
  parcelType: ParcelType;
  landCategory?: LandCategory | string | null;
  ownership: Ownership;
  soilType: SoilType;
  /** 흙토람 표토토성 한글명 (실조회 시) */
  soilTypeLabel?: string | null;
  /** 흙토람 상세 특성 */
  soilDetail?: {
    surttureCd?: string | null;
    surttureName?: string | null;
    drainageName?: string | null;
    validDepthName?: string | null;
    surfaceStoneName?: string | null;
    soilTypeLabel?: string | null;
    pnu?: string | null;
  } | null;
  pnu?: string | null;
  dataProvenance?: Record<string, { source?: string; dataType?: string; actual?: boolean }>;
  solarIrradiance: number; // kWh/㎡/day
  monthlyIrradiance: number[]; // 12
  sunlightHours: number;
  heatIsland: number; // ℃ above baseline
  surfaceTempSummer: number;
  airQuality: number; // PM2.5 μg/m³
  nearbyHouseholds?: number | null;
  pedestrianFlow?: number | null;
  roadAdjacent: boolean;
  waterAccess: boolean;
  electricityAccess: boolean;
  nearbySchools?: number | null;
  nearbyHospitals?: number | null;
  nearbyParks?: number | null;
  nearbySubwayStations?: number | null;
  regulatoryRestriction: Regulation;
  regulations?: Array<Record<string, unknown>>;
  sumokFeasibility?: Record<string, unknown> | null;
  confidence: number;
  scores?: Scores;
  // Fields the UI historically displayed; not returned by the API, kept optional.
  elevationM?: number;
  slopeDegree?: number;
  estimatedAcquisitionCostWon?: number;
  dataSource?: string;
}

export interface ParcelStats {
  total: number;
  avgTreeScore: number;
  avgGardenScore: number;
  avgSolarScore: number;
  topTreeCount: number;
  topGardenCount: number;
  topSolarCount: number;
  totalAreaSqm: number;
}

export interface ParcelsResponse {
  parcels: Parcel[];
  stats: ParcelStats;
  source: string;
  vworldEnabled: boolean;
}

export interface ParcelDetailResponse {
  parcel: Parcel;
  scores: Scores;
  source: string;
}

// Agent search
export interface AgentCriteria {
  district?: string;
  parcelType?: ParcelType;
  topRecommendation?: UseKey;
  minScore?: number;
  minArea?: number;
  maxArea?: number;
  sortBy: "score" | "area" | "heat";
  limit: number;
  explanation?: string;
}

export interface AgentResultItem {
  id: string;
  name: string;
  district: string;
  neighborhood: string;
  areaSqm: number;
  parcelType: ParcelType;
  topRecommendation: UseKey;
  topScore: number;
  scores?: Scores;
}

export interface AgentResult {
  query: string;
  criteria: AgentCriteria;
  results: AgentResultItem[];
  /** VWorld 실시간 API 원본 부지 (목록/상세 연동용) */
  parcels?: Array<Record<string, unknown>>;
  summary: string;
  count: number;
  elapsed_ms: number;
  source: "ai" | "fallback";
}

// Explain
export interface ExplainResponse {
  parcelId: string;
  explanation: string;
  facts: Record<string, unknown>;
  promptVersion: string;
  uncertainty: number;
}

// Simulation
export interface ScenarioEffects {
  label: string;
  quantity: number;
  carbonKgPerYear: number;
  costEstimateWon: number;
  costPerCarbonKgWon: number;
  summary: string;
  pm25ReductionKgPerYear?: number;
  temperatureReductionC?: number;
  rainwaterLitersPerYear?: number;
  foodKgPerYear?: number;
  areaUsedSqm?: number;
  yieldKgPerYear?: number;
  energyKwhPerYear?: number;
  energyMonthly?: number[];
  paybackYears?: number;
  annualMaintenanceWon?: number;
}

export type ScenarioType = "PLANT_TREES" | "CREATE_GARDEN" | "INSTALL_SOLAR" | "COMPARE_ALL";

export interface ScenarioResponse {
  parcelId: string;
  parcelName: string;
  parcelArea: number;
  scenarios: Record<string, { label: string; effects: ScenarioEffects }>;
  elapsed_ms: number;
}

// Compare
export interface CompareResponse {
  comparison: Array<{
    id: string;
    name: string;
    district: string;
    areaSqm: number;
    scores: { tree: number; garden: number; solar: number; top: UseKey };
    effects: Record<string, unknown>;
  }>;
  ranking: Record<string, string[]>;
}

// Stats / trending / history
export interface DistrictStat {
  district: string;
  count: number;
  totalArea: number;
  avgTreeScore: number;
  avgGardenScore: number;
  avgSolarScore: number;
  TREE: number;
  GARDEN: number;
  SOLAR: number;
}

export interface TypeStat {
  parcelType: ParcelType;
  label: string;
  count: number;
  totalArea: number;
  avgScore: number;
}

export interface StatsResponse {
  totalParcels: number;
  byDistrict: DistrictStat[];
  byType: TypeStat[];
  byRecommendation: Record<UseKey, number>;
  generatedAt: string;
}

export interface TrendingResponse {
  totalQueries: number;
  topKeywords: Array<{ keyword: string; count: number }>;
  topDistricts: Array<{ district: string; count: number }>;
  recentQueries: string[];
  generatedAt: string;
}

export interface HistoryEntryDto {
  id: string;
  query: string;
  criteria: AgentCriteria | Record<string, unknown>;
  resultCount: number;
  summary: string;
  source: "ai" | "fallback";
  createdAt: string;
}

export interface HistoryResponse {
  history: HistoryEntryDto[];
  total: number;
}

// Auth
export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: "user";
  createdAt: string;
}

export interface UserBookmark {
  id?: string;
  parcelId: string;
  parcelName: string;
  district: string;
  topRecommendation: UseKey;
  topScore: number;
  createdAt: string;
}

export interface ShareResponse {
  shareId: string;
  url: string;
}
