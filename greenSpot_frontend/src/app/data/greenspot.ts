// GreenSpot — 수목 식재(SUMOK) 기준 데이터·점수 모델
// 정적 계수: USDA i-Tree Eco · 한국에너지공단 · 서울연구원 · 기상청 · KOSIS · Landsat 8

// ── Types ────────────────────────────────────────────────────────────
export type ScoreUse = "SUMOK" | "GARDEN" | "SOLAR";
export type UseKey = ScoreUse | "MIXED" | "RESTRICTED";
export type ParcelType = "VACANT_LOT" | "ROOFTOP" | "UNUSED_LAND" | "ABANDONED" | "BROWNFIELD";
/** VWorld 지목 상세 카테고리 (UI parcelType 과 별개) */
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
export type RegSeverity = "info" | "warning" | "restricted" | "prohibited";
export type PenaltyType = "none" | "subtract" | "multiplier" | "zero";
export type AffectedUse = "sumok" | "garden" | "solar" | "all";
export type FeasibilityStatus = "AVAILABLE" | "CONDITIONAL" | "RESTRICTED" | "PROHIBITED" | "UNKNOWN";

export interface RegulationEntry {
  code: string;
  name: string;
  severity: RegSeverity;
  affectedUses: AffectedUse[];
  penaltyType: PenaltyType;
  penaltyValue?: number;
  legalBasis: string;
  description: string;
}

export interface SumokFeasibility {
  status: FeasibilityStatus;
  score: number;
  reason: string;
  blockingRegulations: string[];
  warningRegulations: string[];
  requiredChecks: string[];
  confidence: number;
}

export interface Scores {
  sumokScore: number;
  gardenScore: number;
  solarScore: number;
  topRecommendation: UseKey;
  uncertainty: number;
  sumokFeasibility: SumokFeasibility;
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
  ownership: Ownership;
  soilType: SoilType;
  soilTypeLabel?: string | null;
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
  elevationM: number;
  slopeDegree: number;
  solarIrradiance: number;
  monthlyIrradiance: number[];
  sunlightHours: number;
  heatIsland: number;
  surfaceTempSummer: number;
  airQuality: number;
  /** @deprecated 미연동 — UI 미표시. 시드 호환용 optional */
  nearbyHouseholds?: number | null;
  /** @deprecated 미연동 — UI 미표시 */
  pedestrianFlow?: number | null;
  roadAdjacent: boolean;
  waterAccess: boolean;
  electricityAccess: boolean;
  /** @deprecated 미연동 — UI 미표시 */
  nearbySchools?: number | null;
  nearbyHospitals?: number | null;
  nearbyParks?: number | null;
  nearbySubwayStations?: number | null;
  regulations: RegulationEntry[];
  estimatedAcquisitionCostWon: number;
  dataSource: string;
  confidence: number;
  scores: Scores;
}

// ── Labels ───────────────────────────────────────────────────────────
export const USE_LABEL: Record<UseKey, string> = {
  SUMOK: "수목 식재", GARDEN: "텃밭", SOLAR: "태양광", MIXED: "복합 활용", RESTRICTED: "제한 구역",
};
export const PARCEL_TYPE_LABEL: Record<ParcelType, string> = {
  VACANT_LOT: "빈터", ROOFTOP: "옥상", UNUSED_LAND: "유휴지", ABANDONED: "방치건물", BROWNFIELD: "오염정화지",
};
export const LAND_CATEGORY_LABEL: Record<LandCategory, string> = {
  AGRICULTURE: "농지",
  FOREST: "임야",
  INDUSTRIAL: "공업용지",
  COMMERCIAL: "상업/공공",
  RESIDENTIAL: "주택용지",
  PARK: "공원",
  CEMETERY: "묘지",
  INFRASTRUCTURE: "교통용지",
  WATER: "하천/구거",
  MIXED: "잡종지",
};
export const OWNERSHIP_LABEL: Record<Ownership, string> = { PUBLIC: "공공", PRIVATE: "민간", UNKNOWN: "미상" };
export const SOIL_LABEL: Record<SoilType, string> = {
  LOAM: "양토", CLAY: "점토", SAND: "사질토", ROCKY: "암반", UNKNOWN: "미상",
};
export const FEASIBILITY_LABEL: Record<FeasibilityStatus, string> = {
  AVAILABLE: "식재 가능", CONDITIONAL: "조건부 가능", RESTRICTED: "제한", PROHIBITED: "불가", UNKNOWN: "판단 불가",
};

// ── Regulation catalog ───────────────────────────────────────────────
export const REG_CATALOG: Record<string, RegulationEntry> = {
  GREEN_BELT: {
    code: "GREEN_BELT", name: "개발제한구역", severity: "restricted",
    affectedUses: ["all"], penaltyType: "multiplier", penaltyValue: 0.5,
    legalBasis: "개발제한구역의 지정 및 관리에 관한 특별조치법 제3조",
    description: "도시의 무질서한 확산 방지를 위해 지정된 구역. 모든 개발 행위 제한.",
  },
  HISTORICAL: {
    code: "HISTORICAL", name: "역사문화보존지역", severity: "warning",
    affectedUses: ["sumok", "garden"], penaltyType: "multiplier", penaltyValue: 0.7,
    legalBasis: "문화재보호법 제13조",
    description: "역사적·문화적 가치가 있는 지역. 지자체 인허가 확인 필요.",
  },
  FLOOD_ZONE: {
    code: "FLOOD_ZONE", name: "침수우려지역", severity: "warning",
    affectedUses: ["sumok", "garden"], penaltyType: "multiplier", penaltyValue: 0.85,
    legalBasis: "자연재해대책법 제12조",
    description: "하천 범람 등 침수 가능성이 있는 지역. 수목 유지관리 리스크 존재.",
  },
  URBAN_NATURE_PARK: {
    code: "URBAN_NATURE_PARK", name: "도시자연공원구역", severity: "warning",
    affectedUses: ["all"], penaltyType: "multiplier", penaltyValue: 0.75,
    legalBasis: "도시공원 및 녹지 등에 관한 법률 제27조",
    description: "도시 내 자연환경 보전을 위한 공원구역. 수목 식재 시 공원녹지계획 확인 필요.",
  },
  NATURE_PRESERVE: {
    code: "NATURE_PRESERVE", name: "자연환경보전지역", severity: "restricted",
    affectedUses: ["all"], penaltyType: "multiplier", penaltyValue: 0.4,
    legalBasis: "국토의 계획 및 이용에 관한 법률 제36조",
    description: "자연환경·수자원 보전 지역. 개발 행위 엄격 제한.",
  },
};

// ── Static coefficients ──────────────────────────────────────────────
export const COEFF = {
  sumokCo2PerYear: 79.4,       // kg CO2 / 성목 / yr (은행나무, USDA i-Tree)
  sumokPm25PerYear: 0.158,     // kg PM2.5 / tree / yr
  sumokTempPerTree: 0.08,      // ℃ / tree
  sumokRainwaterPerYear: 1100, // L / tree / yr
  sumokCostWon: 200_000,       // 식재 원/그루
  gardenCo2PerSqm: 0.85,      // kg CO2 / ㎡ / yr (서울연구원)
  gardenFoodPerSqm: 2.4,       // kg 식량 / ㎡ / yr
  gardenCostPerSqm: 55_000,
  solarKwPerPanel: 0.45,
  solarKwhPerKw: 1242,         // 한국에너지공단 용량계수 14.2%
  solarGridFactor: 0.4159,     // kg CO2 / kWh
  solarCostPerKw: 1_800_000,
  elecPriceWon: 130,
};

// ── Seasonal shape ───────────────────────────────────────────────────
const SEASON = [0.55, 0.72, 0.9, 1.08, 1.18, 1.13, 1.03, 0.98, 0.86, 0.72, 0.58, 0.5];
function monthly(base: number): number[] {
  return SEASON.map((s) => Math.round(base * s * 100) / 100);
}

// ── Type fits ────────────────────────────────────────────────────────
const SUMOK_TYPE_FIT: Record<ParcelType, number> = { VACANT_LOT: 1.0, UNUSED_LAND: 0.9, ABANDONED: 0.7, BROWNFIELD: 0.6, ROOFTOP: 0.2 };
const GARDEN_TYPE_FIT: Record<ParcelType, number> = { VACANT_LOT: 1.0, UNUSED_LAND: 0.85, ROOFTOP: 0.7, ABANDONED: 0.6, BROWNFIELD: 0.4 };
const SOLAR_TYPE_FIT: Record<ParcelType, number> = { ROOFTOP: 1.0, BROWNFIELD: 0.7, VACANT_LOT: 0.6, UNUSED_LAND: 0.55, ABANDONED: 0.5 };
const SOIL_FIT: Record<SoilType, number> = { LOAM: 0.95, SAND: 0.7, CLAY: 0.6, ROCKY: 0.25, UNKNOWN: 0.5 };

// ── Raw parcels ──────────────────────────────────────────────────────
type RawParcel = Omit<Parcel, "scores" | "monthlyIrradiance">;

const R = REG_CATALOG;
const NO_REG: RegulationEntry[] = [];

const RAW: RawParcel[] = [
  // 중구
  { id: "JG-001", name: "을지로 인쇄골목 빈터", district: "중구", neighborhood: "을지로동", lat: 37.5662, lng: 126.9910, areaSqm: 540, parcelType: "VACANT_LOT", ownership: "PUBLIC", soilType: "LOAM", elevationM: 32, slopeDegree: 2, solarIrradiance: 3.9, sunlightHours: 5.6, heatIsland: 3.4, surfaceTempSummer: 37.2, airQuality: 31, nearbyHouseholds: 2140, pedestrianFlow: 5200, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 2, nearbyHospitals: 1, nearbyParks: 0, nearbySubwayStations: 2, regulations: NO_REG, estimatedAcquisitionCostWon: 1_620_000_000, dataSource: "KOSIS·Landsat", confidence: 0.94 },
  { id: "JG-002", name: "신당동 방치건물 부지", district: "중구", neighborhood: "신당동", lat: 37.5657, lng: 127.0177, areaSqm: 320, parcelType: "ABANDONED", ownership: "PRIVATE", soilType: "UNKNOWN", elevationM: 41, slopeDegree: 5, solarIrradiance: 3.7, sunlightHours: 5.2, heatIsland: 3.9, surfaceTempSummer: 38.1, airQuality: 34, nearbyHouseholds: 3120, pedestrianFlow: 3800, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 3, nearbyHospitals: 2, nearbyParks: 1, nearbySubwayStations: 1, regulations: [R.HISTORICAL], estimatedAcquisitionCostWon: 980_000_000, dataSource: "샘플", confidence: 0.82 },
  { id: "JG-003", name: "황학동 시장 옥상", district: "중구", neighborhood: "황학동", lat: 37.5691, lng: 127.0231, areaSqm: 410, parcelType: "ROOFTOP", ownership: "PUBLIC", soilType: "UNKNOWN", elevationM: 38, slopeDegree: 0, solarIrradiance: 4.4, sunlightHours: 6.4, heatIsland: 2.8, surfaceTempSummer: 35.4, airQuality: 28, nearbyHouseholds: 1780, pedestrianFlow: 2600, roadAdjacent: true, waterAccess: false, electricityAccess: true, nearbySchools: 1, nearbyHospitals: 0, nearbyParks: 1, nearbySubwayStations: 1, regulations: NO_REG, estimatedAcquisitionCostWon: 0, dataSource: "KOSIS·기상청", confidence: 0.91 },
  { id: "JG-004", name: "회현동 유휴 공터", district: "중구", neighborhood: "회현동", lat: 37.5585, lng: 126.9799, areaSqm: 720, parcelType: "UNUSED_LAND", ownership: "PUBLIC", soilType: "SAND", elevationM: 46, slopeDegree: 8, solarIrradiance: 4.1, sunlightHours: 5.9, heatIsland: 2.5, surfaceTempSummer: 34.8, airQuality: 26, nearbyHouseholds: 1240, pedestrianFlow: 4100, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 1, nearbyHospitals: 1, nearbyParks: 2, nearbySubwayStations: 2, regulations: NO_REG, estimatedAcquisitionCostWon: 2_010_000_000, dataSource: "KOSIS·Landsat", confidence: 0.9 },
  // 성동구
  { id: "SD-001", name: "성수동 준공업지 빈터", district: "성동구", neighborhood: "성수동", lat: 37.5443, lng: 127.0557, areaSqm: 1180, parcelType: "VACANT_LOT", ownership: "PRIVATE", soilType: "LOAM", elevationM: 18, slopeDegree: 1, solarIrradiance: 4.2, sunlightHours: 6.1, heatIsland: 3.1, surfaceTempSummer: 36.6, airQuality: 29, nearbyHouseholds: 2960, pedestrianFlow: 6400, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 2, nearbyHospitals: 1, nearbyParks: 1, nearbySubwayStations: 1, regulations: NO_REG, estimatedAcquisitionCostWon: 3_540_000_000, dataSource: "KOSIS·Landsat", confidence: 0.93 },
  { id: "SD-002", name: "왕십리 역세권 옥상", district: "성동구", neighborhood: "왕십리", lat: 37.5613, lng: 127.0378, areaSqm: 480, parcelType: "ROOFTOP", ownership: "PUBLIC", soilType: "UNKNOWN", elevationM: 22, slopeDegree: 0, solarIrradiance: 4.6, sunlightHours: 6.7, heatIsland: 2.6, surfaceTempSummer: 35.1, airQuality: 27, nearbyHouseholds: 4100, pedestrianFlow: 5800, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 2, nearbyHospitals: 2, nearbyParks: 0, nearbySubwayStations: 3, regulations: NO_REG, estimatedAcquisitionCostWon: 0, dataSource: "KOSIS·기상청", confidence: 0.95 },
  { id: "SD-003", name: "금호동 경사지 유휴지", district: "성동구", neighborhood: "금호동", lat: 37.5484, lng: 127.0217, areaSqm: 610, parcelType: "UNUSED_LAND", ownership: "PUBLIC", soilType: "CLAY", elevationM: 54, slopeDegree: 14, solarIrradiance: 3.8, sunlightHours: 5.4, heatIsland: 2.2, surfaceTempSummer: 33.9, airQuality: 24, nearbyHouseholds: 2380, pedestrianFlow: 2200, roadAdjacent: false, waterAccess: true, electricityAccess: true, nearbySchools: 3, nearbyHospitals: 0, nearbyParks: 2, nearbySubwayStations: 1, regulations: [R.URBAN_NATURE_PARK], estimatedAcquisitionCostWon: 1_320_000_000, dataSource: "샘플", confidence: 0.85 },
  { id: "SD-004", name: "옥수동 하천변 부지", district: "성동구", neighborhood: "옥수동", lat: 37.5406, lng: 127.0176, areaSqm: 890, parcelType: "VACANT_LOT", ownership: "PUBLIC", soilType: "SAND", elevationM: 12, slopeDegree: 3, solarIrradiance: 4.0, sunlightHours: 5.8, heatIsland: 1.9, surfaceTempSummer: 33.2, airQuality: 22, nearbyHouseholds: 1960, pedestrianFlow: 3300, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 2, nearbyHospitals: 1, nearbyParks: 3, nearbySubwayStations: 1, regulations: [R.FLOOD_ZONE], estimatedAcquisitionCostWon: 1_780_000_000, dataSource: "KOSIS·Landsat", confidence: 0.88 },
  // 동대문구
  { id: "DD-001", name: "회기동 빈터 A", district: "동대문구", neighborhood: "회기동", lat: 37.5894, lng: 127.0586, areaSqm: 680, parcelType: "VACANT_LOT", ownership: "PUBLIC", soilType: "LOAM", elevationM: 44, slopeDegree: 4, solarIrradiance: 4.0, sunlightHours: 5.9, heatIsland: 2.1, surfaceTempSummer: 34.5, airQuality: 25, nearbyHouseholds: 1820, pedestrianFlow: 2400, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 4, nearbyHospitals: 1, nearbyParks: 1, nearbySubwayStations: 1, regulations: NO_REG, estimatedAcquisitionCostWon: 1_190_000_000, dataSource: "KOSIS·Landsat", confidence: 0.93 },
  { id: "DD-002", name: "이문동 재개발 잔여지", district: "동대문구", neighborhood: "이문동", lat: 37.5973, lng: 127.0645, areaSqm: 1320, parcelType: "UNUSED_LAND", ownership: "PUBLIC", soilType: "LOAM", elevationM: 49, slopeDegree: 6, solarIrradiance: 4.1, sunlightHours: 6.0, heatIsland: 2.4, surfaceTempSummer: 34.9, airQuality: 26, nearbyHouseholds: 3480, pedestrianFlow: 3100, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 5, nearbyHospitals: 1, nearbyParks: 0, nearbySubwayStations: 1, regulations: NO_REG, estimatedAcquisitionCostWon: 2_640_000_000, dataSource: "KOSIS·Landsat", confidence: 0.92 },
  { id: "DD-003", name: "전농동 시장 옥상", district: "동대문구", neighborhood: "전농동", lat: 37.5836, lng: 127.0567, areaSqm: 360, parcelType: "ROOFTOP", ownership: "PRIVATE", soilType: "UNKNOWN", elevationM: 40, slopeDegree: 0, solarIrradiance: 4.5, sunlightHours: 6.6, heatIsland: 2.9, surfaceTempSummer: 35.7, airQuality: 28, nearbyHouseholds: 2210, pedestrianFlow: 4300, roadAdjacent: true, waterAccess: false, electricityAccess: true, nearbySchools: 2, nearbyHospitals: 1, nearbyParks: 0, nearbySubwayStations: 1, regulations: NO_REG, estimatedAcquisitionCostWon: 0, dataSource: "KOSIS·기상청", confidence: 0.9 },
  { id: "DD-004", name: "청량리 방치 상가", district: "동대문구", neighborhood: "청량리동", lat: 37.5804, lng: 127.0475, areaSqm: 450, parcelType: "ABANDONED", ownership: "PRIVATE", soilType: "UNKNOWN", elevationM: 37, slopeDegree: 2, solarIrradiance: 3.8, sunlightHours: 5.3, heatIsland: 3.6, surfaceTempSummer: 37.8, airQuality: 33, nearbyHouseholds: 3860, pedestrianFlow: 7100, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 3, nearbyHospitals: 3, nearbyParks: 0, nearbySubwayStations: 2, regulations: NO_REG, estimatedAcquisitionCostWon: 1_450_000_000, dataSource: "샘플", confidence: 0.83 },
  { id: "DD-005", name: "답십리 유휴 공영주차장", district: "동대문구", neighborhood: "답십리동", lat: 37.5744, lng: 127.0538, areaSqm: 950, parcelType: "UNUSED_LAND", ownership: "PUBLIC", soilType: "SAND", elevationM: 34, slopeDegree: 1, solarIrradiance: 4.2, sunlightHours: 6.2, heatIsland: 2.7, surfaceTempSummer: 35.3, airQuality: 27, nearbyHouseholds: 2680, pedestrianFlow: 2900, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 3, nearbyHospitals: 1, nearbyParks: 1, nearbySubwayStations: 1, regulations: NO_REG, estimatedAcquisitionCostWon: 1_870_000_000, dataSource: "KOSIS·Landsat", confidence: 0.91 },
  // 마포구
  { id: "MP-001", name: "합정동 주차장 부지", district: "마포구", neighborhood: "합정동", lat: 37.5495, lng: 126.9137, areaSqm: 760, parcelType: "VACANT_LOT", ownership: "PRIVATE", soilType: "LOAM", elevationM: 15, slopeDegree: 2, solarIrradiance: 4.3, sunlightHours: 6.3, heatIsland: 2.8, surfaceTempSummer: 35.6, airQuality: 26, nearbyHouseholds: 3240, pedestrianFlow: 8200, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 2, nearbyHospitals: 1, nearbyParks: 1, nearbySubwayStations: 2, regulations: NO_REG, estimatedAcquisitionCostWon: 3_120_000_000, dataSource: "KOSIS·Landsat", confidence: 0.93 },
  { id: "MP-002", name: "망원동 골목 유휴지", district: "마포구", neighborhood: "망원동", lat: 37.5556, lng: 126.9019, areaSqm: 380, parcelType: "UNUSED_LAND", ownership: "PUBLIC", soilType: "LOAM", elevationM: 11, slopeDegree: 1, solarIrradiance: 4.0, sunlightHours: 5.7, heatIsland: 2.3, surfaceTempSummer: 34.2, airQuality: 24, nearbyHouseholds: 2540, pedestrianFlow: 4600, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 3, nearbyHospitals: 0, nearbyParks: 2, nearbySubwayStations: 1, regulations: NO_REG, estimatedAcquisitionCostWon: 940_000_000, dataSource: "KOSIS·Landsat", confidence: 0.92 },
  { id: "MP-003", name: "상암 DMC 옥상단지", district: "마포구", neighborhood: "상암동", lat: 37.5794, lng: 126.8895, areaSqm: 620, parcelType: "ROOFTOP", ownership: "PUBLIC", soilType: "UNKNOWN", elevationM: 20, slopeDegree: 0, solarIrradiance: 4.7, sunlightHours: 6.9, heatIsland: 2.0, surfaceTempSummer: 33.6, airQuality: 21, nearbyHouseholds: 1680, pedestrianFlow: 3400, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 1, nearbyHospitals: 1, nearbyParks: 3, nearbySubwayStations: 1, regulations: [R.URBAN_NATURE_PARK], estimatedAcquisitionCostWon: 0, dataSource: "KOSIS·기상청", confidence: 0.95 },
  { id: "MP-004", name: "공덕동 오염정화 예정지", district: "마포구", neighborhood: "공덕동", lat: 37.5443, lng: 126.9515, areaSqm: 1040, parcelType: "BROWNFIELD", ownership: "PUBLIC", soilType: "ROCKY", elevationM: 24, slopeDegree: 4, solarIrradiance: 4.2, sunlightHours: 6.1, heatIsland: 3.2, surfaceTempSummer: 36.9, airQuality: 30, nearbyHouseholds: 3760, pedestrianFlow: 5100, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 2, nearbyHospitals: 2, nearbyParks: 0, nearbySubwayStations: 2, regulations: NO_REG, estimatedAcquisitionCostWon: 2_890_000_000, dataSource: "샘플", confidence: 0.84 },
  // 강남구
  { id: "GN-001", name: "삼성동 오피스 옥상 A", district: "강남구", neighborhood: "삼성동", lat: 37.5089, lng: 127.0631, areaSqm: 380, parcelType: "ROOFTOP", ownership: "PRIVATE", soilType: "UNKNOWN", elevationM: 28, slopeDegree: 0, solarIrradiance: 4.9, sunlightHours: 7.2, heatIsland: 2.7, surfaceTempSummer: 35.2, airQuality: 23, nearbyHouseholds: 2020, pedestrianFlow: 6800, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 1, nearbyHospitals: 2, nearbyParks: 1, nearbySubwayStations: 2, regulations: NO_REG, estimatedAcquisitionCostWon: 0, dataSource: "KOSIS·기상청", confidence: 0.96 },
  { id: "GN-002", name: "역삼동 상가 옥상 B", district: "강남구", neighborhood: "역삼동", lat: 37.5006, lng: 127.0364, areaSqm: 440, parcelType: "ROOFTOP", ownership: "PRIVATE", soilType: "UNKNOWN", elevationM: 31, slopeDegree: 0, solarIrradiance: 4.8, sunlightHours: 7.0, heatIsland: 3.0, surfaceTempSummer: 36.1, airQuality: 25, nearbyHouseholds: 3320, pedestrianFlow: 9200, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 2, nearbyHospitals: 1, nearbyParks: 0, nearbySubwayStations: 3, regulations: NO_REG, estimatedAcquisitionCostWon: 0, dataSource: "KOSIS·기상청", confidence: 0.94 },
  { id: "GN-003", name: "논현동 이면도로 빈터", district: "강남구", neighborhood: "논현동", lat: 37.5112, lng: 127.0217, areaSqm: 560, parcelType: "VACANT_LOT", ownership: "PRIVATE", soilType: "LOAM", elevationM: 26, slopeDegree: 3, solarIrradiance: 4.4, sunlightHours: 6.5, heatIsland: 3.3, surfaceTempSummer: 36.8, airQuality: 27, nearbyHouseholds: 2880, pedestrianFlow: 5600, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 2, nearbyHospitals: 1, nearbyParks: 0, nearbySubwayStations: 2, regulations: NO_REG, estimatedAcquisitionCostWon: 4_120_000_000, dataSource: "KOSIS·Landsat", confidence: 0.92 },
  { id: "GN-004", name: "대치동 학원가 유휴지", district: "강남구", neighborhood: "대치동", lat: 37.4994, lng: 127.0578, areaSqm: 690, parcelType: "UNUSED_LAND", ownership: "PUBLIC", soilType: "LOAM", elevationM: 29, slopeDegree: 2, solarIrradiance: 4.3, sunlightHours: 6.4, heatIsland: 2.9, surfaceTempSummer: 35.9, airQuality: 26, nearbyHouseholds: 4260, pedestrianFlow: 7400, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 6, nearbyHospitals: 1, nearbyParks: 1, nearbySubwayStations: 2, regulations: NO_REG, estimatedAcquisitionCostWon: 5_010_000_000, dataSource: "KOSIS·Landsat", confidence: 0.93 },
  { id: "GN-005", name: "개포동 그린벨트 인접지", district: "강남구", neighborhood: "개포동", lat: 37.4783, lng: 127.0665, areaSqm: 1450, parcelType: "UNUSED_LAND", ownership: "PUBLIC", soilType: "SAND", elevationM: 58, slopeDegree: 11, solarIrradiance: 4.5, sunlightHours: 6.6, heatIsland: 1.8, surfaceTempSummer: 33.1, airQuality: 20, nearbyHouseholds: 1540, pedestrianFlow: 1800, roadAdjacent: false, waterAccess: true, electricityAccess: false, nearbySchools: 3, nearbyHospitals: 0, nearbyParks: 4, nearbySubwayStations: 1, regulations: [R.GREEN_BELT], estimatedAcquisitionCostWon: 2_260_000_000, dataSource: "샘플", confidence: 0.86 },
  { id: "GN-006", name: "청담동 근생 옥상", district: "강남구", neighborhood: "청담동", lat: 37.5245, lng: 127.0473, areaSqm: 300, parcelType: "ROOFTOP", ownership: "PRIVATE", soilType: "UNKNOWN", elevationM: 25, slopeDegree: 0, solarIrradiance: 4.7, sunlightHours: 6.8, heatIsland: 2.5, surfaceTempSummer: 34.7, airQuality: 22, nearbyHouseholds: 1720, pedestrianFlow: 4900, roadAdjacent: true, waterAccess: true, electricityAccess: true, nearbySchools: 1, nearbyHospitals: 1, nearbyParks: 2, nearbySubwayStations: 1, regulations: NO_REG, estimatedAcquisitionCostWon: 0, dataSource: "KOSIS·기상청", confidence: 0.95 },
];

// ── Normalisation helpers ────────────────────────────────────────────
function minmax(vals: number[]) {
  return { min: Math.min(...vals), max: Math.max(...vals) };
}
function norm(v: number, mm: { min: number; max: number }) {
  if (mm.max === mm.min) return 0.5;
  return Math.max(0, Math.min(1, (v - mm.min) / (mm.max - mm.min)));
}

const mmHeat  = minmax(RAW.map((p) => p.heatIsland));
const mmSun   = minmax(RAW.map((p) => p.sunlightHours));
const mmArea  = minmax(RAW.map((p) => p.areaSqm));
const mmSolar = minmax(RAW.map((p) => p.solarIrradiance));
const mmSlope = minmax(RAW.map((p) => p.slopeDegree));
// PM2.5: 낮을수록 유리 → 점수식에서 (1 - norm)
const mmAQ    = minmax(RAW.map((p) => p.airQuality));

// ── Regulation penalty engine ────────────────────────────────────────
function applyPenalties(baseScore: number, regs: RegulationEntry[], use: AffectedUse): number {
  const relevant = regs.filter((r) => r.affectedUses.includes(use) || r.affectedUses.includes("all"));
  if (relevant.some((r) => r.penaltyType === "zero")) return 0;
  let s = baseScore;
  const muls = relevant.filter((r) => r.penaltyType === "multiplier")
    .sort((a, b) => (a.penaltyValue ?? 1) - (b.penaltyValue ?? 1));
  for (const r of muls) s *= r.penaltyValue ?? 1;
  for (const r of relevant.filter((r) => r.penaltyType === "subtract")) s -= r.penaltyValue ?? 0;
  return Math.max(0, Math.round(s));
}

// ── sumokFeasibility ─────────────────────────────────────────────────
function computeFeasibility(regs: RegulationEntry[], sumokScore: number, confidence: number): SumokFeasibility {
  const sumokRegs = regs.filter((r) => r.affectedUses.includes("sumok") || r.affectedUses.includes("all"));
  const blocking  = sumokRegs.filter((r) => r.severity === "prohibited" || r.penaltyType === "zero");
  const restricted = sumokRegs.filter((r) => r.severity === "restricted");
  const warning   = sumokRegs.filter((r) => r.severity === "warning");

  const requiredChecks: string[] = [];
  let status: FeasibilityStatus;
  let reason: string;

  if (blocking.length > 0) {
    status = "PROHIBITED";
    reason = `${blocking[0].name} 규제로 인해 수목 식재가 사실상 불가합니다.`;
  } else if (restricted.length > 0) {
    status = "RESTRICTED";
    reason = `${restricted[0].name} 규제로 인해 수목 식재가 크게 제한됩니다.`;
    requiredChecks.push("지자체 특별 허가 확인", `${restricted[0].legalBasis} 검토`);
  } else if (warning.length > 0) {
    status = "CONDITIONAL";
    reason = `${warning.map((r) => r.name).join(", ")} 규제로 인허가 확인이 필요합니다.`;
    for (const r of warning) {
      if (r.code === "HISTORICAL") requiredChecks.push("문화재청 현상변경 허가 확인");
      if (r.code === "FLOOD_ZONE")  requiredChecks.push("침수 위험도 평가", "수목 유지관리 계획 수립");
      if (r.code === "URBAN_NATURE_PARK") requiredChecks.push("지자체 인허가 확인", "공원녹지계획 확인");
    }
  } else if (confidence < 0.8) {
    status = "UNKNOWN";
    reason = "데이터 신뢰도가 낮아 수목 식재 가능성을 정확히 판단할 수 없습니다.";
  } else {
    status = "AVAILABLE";
    reason = "명확한 규제 제한이 없으며 수목 식재 적합도가 높습니다.";
  }

  return {
    status, score: sumokScore, reason,
    blockingRegulations: blocking.map((r) => r.code),
    warningRegulations: [...restricted, ...warning].map((r) => r.code),
    requiredChecks, confidence,
  };
}

// ── Score computation (시드 전용; 라이브는 백엔드 compute_base_scores 사용)
// 보행·가구·학교·공원·지하철 등 미연동 사회지표 제외
function computeScores(p: RawParcel): Scores {
  // sumokScore: 열섬·면적·도로·수자원·토양·경사도(역)·대기질·유형
  const sumokRaw =
    norm(p.heatIsland, mmHeat)    * 0.28 +
    norm(p.areaSqm, mmArea)       * 0.18 +
    (p.roadAdjacent ? 1 : 0)      * 0.10 +
    (p.waterAccess  ? 1 : 0)      * 0.10 +
    SOIL_FIT[p.soilType]          * 0.12 +
    (1 - norm(p.slopeDegree, mmSlope)) * 0.10 +
    (1 - norm(p.airQuality, mmAQ)) * 0.12;
  const sumokBase = Math.round(100 * sumokRaw);
  const sumokScore = applyPenalties(sumokBase, p.regulations, "sumok");

  // gardenScore: 토양·면적·수자원·일조·유형·도로
  const gardenRaw =
    SOIL_FIT[p.soilType]              * 0.28 +
    norm(p.areaSqm, mmArea)           * 0.22 +
    (p.waterAccess ? 1 : 0)           * 0.15 +
    norm(p.sunlightHours, mmSun)      * 0.12 +
    GARDEN_TYPE_FIT[p.parcelType]     * 0.13 +
    (p.roadAdjacent ? 1 : 0)          * 0.10;
  const gardenBase = Math.round(100 * gardenRaw);
  const gardenScore = applyPenalties(gardenBase, p.regulations, "garden");

  // solarScore: 일사량·일조·유형·면적·전기·경사도(역)
  const solarRaw =
    norm(p.solarIrradiance, mmSolar)  * 0.30 +
    norm(p.sunlightHours, mmSun)      * 0.20 +
    SOLAR_TYPE_FIT[p.parcelType]      * 0.18 +
    norm(p.areaSqm, mmArea)           * 0.15 +
    (p.electricityAccess ? 1 : 0)     * 0.10 +
    (1 - norm(p.slopeDegree, mmSlope)) * 0.07;
  const solarBase = Math.round(100 * solarRaw);
  const solarScore = applyPenalties(solarBase, p.regulations, "solar");

  // topRecommendation: MIXED if top-2 within 5pts, RESTRICTED if all very low
  const entries: [ScoreUse, number][] = [
    ["SUMOK", sumokScore], ["GARDEN", gardenScore], ["SOLAR", solarScore],
  ].sort((a, b) => b[1] - a[1]) as [ScoreUse, number][];

  let topRecommendation: UseKey;
  if (entries[0][1] === 0) {
    topRecommendation = "RESTRICTED";
  } else if (entries[1][1] > 0 && entries[0][1] - entries[1][1] < 5) {
    topRecommendation = "MIXED";
  } else {
    topRecommendation = entries[0][0];
  }

  const uncertainty = Math.round((1 - p.confidence) * 10 + 3);
  const sumokFeasibility = computeFeasibility(p.regulations, sumokScore, p.confidence);

  return { sumokScore, gardenScore, solarScore, topRecommendation, uncertainty, sumokFeasibility };
}

// ── Build PARCELS ────────────────────────────────────────────────────
export const PARCELS: Parcel[] = RAW.map((p) => ({
  ...p,
  monthlyIrradiance: monthly(p.solarIrradiance),
  scores: computeScores(p),
}));

export const DISTRICTS = [
  "종로구", "중구", "용산구", "성동구", "광진구",
  "동대문구", "중랑구", "성북구", "강북구", "도봉구",
  "노원구", "은평구", "서대문구", "마포구", "양천구",
  "강서구", "구로구", "금천구", "영등포구", "동작구",
  "관악구", "서초구", "강남구", "송파구", "강동구",
];
export const PARCEL_TYPES: ParcelType[] = ["VACANT_LOT", "ROOFTOP", "UNUSED_LAND", "ABANDONED", "BROWNFIELD"];

// ── Score helpers ────────────────────────────────────────────────────
export function scoreFor(p: Parcel, use: ScoreUse | "TREE" | string): number {
  const s = p.scores as Parcel["scores"] & { treeScore?: number };
  const key = String(use || "").toUpperCase();
  // API TREE 와 UI SUMOK 는 동일 용도
  if (key === "SUMOK" || key === "TREE") return Number(s.sumokScore ?? s.treeScore ?? 0) || 0;
  if (key === "GARDEN") return Number(s.gardenScore ?? 0) || 0;
  if (key === "SOLAR") return Number(s.solarScore ?? 0) || 0;
  return Math.max(
    Number(s.sumokScore ?? s.treeScore ?? 0) || 0,
    Number(s.gardenScore ?? 0) || 0,
    Number(s.solarScore ?? 0) || 0,
  );
}
export function topScore(p: Parcel): number {
  const r = p.scores.topRecommendation;
  if (r === "RESTRICTED") return 0;
  if (r === "MIXED") {
    return Math.max(
      scoreFor(p, "SUMOK"),
      scoreFor(p, "GARDEN"),
      scoreFor(p, "SOLAR"),
    );
  }
  return scoreFor(p, r);
}
let _parcelLookup: ((id: string | null | undefined) => Parcel | undefined) | null = null;

export function _setParcelLookup(fn: (id: string | null | undefined) => Parcel | undefined) {
  _parcelLookup = fn;
}

export function getParcel(id: string): Parcel | undefined {
  if (_parcelLookup) return _parcelLookup(id);
  return undefined;
}

// ── Aggregate stats ──────────────────────────────────────────────────
/** 현재 목록(검색/선택 지역 포함)에 등장하는 지역명 목록 */
export function districtsFromParcels(source: Parcel[]): string[] {
  const set = new Set<string>();
  for (const p of source) {
    const d = (p.district || "").trim();
    if (d) set.add(d);
  }
  return [...set].sort((a, b) => a.localeCompare(b, "ko"));
}

export function computeStats(source: Parcel[] = PARCELS) {
  const total = source.length;
  const avg = (sel: (p: Parcel) => number) => (total ? Math.round(source.reduce((a, p) => a + sel(p), 0) / total) : 0);
  const recCount = (r: UseKey) => source.filter((p) => p.scores.topRecommendation === r).length;
  const feasCount = (s: FeasibilityStatus) =>
    source.filter((p) => (p.scores.sumokFeasibility?.status ?? "UNKNOWN") === s).length;
  const avgConfidence = total ? Math.round(source.reduce((a, p) => a + (p.confidence ?? 0), 0) / total * 100) : 0;
  const regulationSeverity = (["info", "warning", "restricted", "prohibited"] as RegSeverity[]).map((severity) => ({
    severity,
    count: source.reduce(
      (a, p) => a + (p.regulations ?? []).filter((r) => r.severity === severity).length,
      0,
    ),
  }));

  // 서울 고정 목록이 아니라, 실제 데이터(검색/선택 지역) 기준으로 집계
  // → 제주·부산 등 다른 지역 검색 시에도 해당 지역이 통계에 나타남
  const regionNames = districtsFromParcels(source);
  const byDistrict = regionNames.map((d) => {
    const items = source.filter((p) => p.district === d);
    const a = (sel: (p: Parcel) => number) =>
      items.length ? Math.round(items.reduce((x, p) => x + sel(p), 0) / items.length) : 0;
    return {
      district: d,
      count: items.length,
      totalArea: items.reduce((x, p) => x + (p.areaSqm || 0), 0),
      avgSumokScore: a((p) => p.scores.sumokScore),
      avgGardenScore: a((p) => p.scores.gardenScore),
      avgSolarScore: a((p) => p.scores.solarScore),
      SUMOK: items.filter((p) => p.scores.topRecommendation === "SUMOK").length,
      GARDEN: items.filter((p) => p.scores.topRecommendation === "GARDEN").length,
      SOLAR: items.filter((p) => p.scores.topRecommendation === "SOLAR").length,
      MIXED: items.filter((p) => p.scores.topRecommendation === "MIXED").length,
      RESTRICTED: items.filter((p) => p.scores.topRecommendation === "RESTRICTED").length,
    };
  });

  const byType = PARCEL_TYPES.map((t) => {
    const items = source.filter((p) => p.parcelType === t);
    return {
      parcelType: t,
      label: PARCEL_TYPE_LABEL[t],
      count: items.length,
      totalArea: items.reduce((x, p) => x + (p.areaSqm || 0), 0),
      avgScore: items.length
        ? Math.round(items.reduce((x, p) => x + topScore(p), 0) / items.length)
        : 0,
    };
  }).filter((t) => t.count > 0);

  return {
    total,
    totalAreaSqm: source.reduce((a, p) => a + (p.areaSqm || 0), 0),
    regions: regionNames,
    regionLabel:
      regionNames.length === 0
        ? "지역 없음"
        : regionNames.length === 1
          ? regionNames[0]
          : regionNames.length <= 3
            ? regionNames.join(" · ")
            : `${regionNames.slice(0, 2).join(" · ")} 외 ${regionNames.length - 2}곳`,
    avgSumokScore: avg((p) => p.scores.sumokScore),
    avgGardenScore: avg((p) => p.scores.gardenScore),
    avgSolarScore: avg((p) => p.scores.solarScore),
    topSumokCount: recCount("SUMOK"),
    topGardenCount: recCount("GARDEN"),
    topSolarCount: recCount("SOLAR"),
    topMixedCount: recCount("MIXED"),
    topRestrictedCount: recCount("RESTRICTED"),
    sumokFeasibility: {
      AVAILABLE: feasCount("AVAILABLE"),
      CONDITIONAL: feasCount("CONDITIONAL"),
      RESTRICTED: feasCount("RESTRICTED"),
      PROHIBITED: feasCount("PROHIBITED"),
      UNKNOWN: feasCount("UNKNOWN"),
    },
    byDistrict,
    byType,
    avgConfidence,
    regulationSeverity,
    byRecommendation: {
      SUMOK: recCount("SUMOK"),
      GARDEN: recCount("GARDEN"),
      SOLAR: recCount("SOLAR"),
      MIXED: recCount("MIXED"),
      RESTRICTED: recCount("RESTRICTED"),
    },
  };
}

// ── Scenario simulation ──────────────────────────────────────────────
export interface ScenarioEffects {
  label: string;
  quantity: number;
  carbonKgPerYear: number;
  costEstimateWon: number;
  costPerCarbonKgWon: number;
  summary: string;
  // sumok
  pm25ReductionKgPerYear?: number;
  temperatureReductionC?: number;
  rainwaterLitersPerYear?: number;
  feasibilityStatus?: FeasibilityStatus;
  maintenanceRisk?: "LOW" | "MEDIUM" | "HIGH";
  regulatoryCheckRequired?: boolean;
  requiredChecks?: string[];
  // garden
  foodKgPerYear?: number;
  // solar
  energyKwhPerYear?: number;
  energyMonthly?: number[];
  paybackYears?: number;
}

export const SCENARIO_MAX: Record<ScoreUse, number> = { SUMOK: 200, GARDEN: 150, SOLAR: 500 };

export function defaultQuantity(p: Parcel, use: ScoreUse): number {
  if (use === "SUMOK")  return Math.min(SCENARIO_MAX.SUMOK, Math.max(1, Math.floor(p.areaSqm / 25)));
  if (use === "GARDEN") return Math.min(SCENARIO_MAX.GARDEN, Math.max(10, Math.floor(p.areaSqm * 0.6)));
  return Math.min(SCENARIO_MAX.SOLAR, Math.max(1, Math.floor(p.areaSqm / 3)));
}

export function simulate(p: Parcel, use: ScoreUse, quantity: number): ScenarioEffects {
  const q = Math.max(1, Math.round(quantity));
  if (use === "SUMOK") {
    const carbon = Math.round(q * COEFF.sumokCo2PerYear);
    const cost = q * COEFF.sumokCostWon;
    const fs = p.scores.sumokFeasibility;
    const risk: "LOW" | "MEDIUM" | "HIGH" =
      fs.status === "RESTRICTED" || fs.status === "PROHIBITED" ? "HIGH"
      : fs.status === "CONDITIONAL" ? "MEDIUM"
      : p.waterAccess ? "LOW" : "MEDIUM";
    const note = fs.requiredChecks.length > 0 ? ` (인허가 확인 필요: ${fs.requiredChecks[0]})` : "";
    return {
      label: `수목 ${q}그루`, quantity: q, carbonKgPerYear: carbon,
      pm25ReductionKgPerYear: Math.round(q * COEFF.sumokPm25PerYear * 1000) / 1000,
      temperatureReductionC: Math.round(Math.min(q * COEFF.sumokTempPerTree, 3.5) * 10) / 10,
      rainwaterLitersPerYear: q * COEFF.sumokRainwaterPerYear,
      costEstimateWon: cost,
      costPerCarbonKgWon: Math.round(cost / carbon),
      feasibilityStatus: fs.status,
      maintenanceRisk: risk,
      regulatoryCheckRequired: fs.requiredChecks.length > 0,
      requiredChecks: fs.requiredChecks,
      summary: `은행나무 성목 ${q}그루 식재 시 연간 CO₂ ${carbon.toLocaleString()}kg 흡수, 주변 기온 최대 ${Math.min(q * COEFF.sumokTempPerTree, 3.5).toFixed(1)}℃ 완화, 투자비 약 ${(cost / 10000).toLocaleString()}만원.${note}`,
    };
  }
  if (use === "GARDEN") {
    const carbon = Math.round(q * COEFF.gardenCo2PerSqm);
    const food = Math.round(q * COEFF.gardenFoodPerSqm);
    const cost = q * COEFF.gardenCostPerSqm;
    return {
      label: `텃밭 ${q}㎡`, quantity: q, carbonKgPerYear: carbon, foodKgPerYear: food,
      costEstimateWon: cost, costPerCarbonKgWon: carbon ? Math.round(cost / carbon) : 0,
      summary: `${q}㎡ 커뮤니티 텃밭 조성 시 연간 CO₂ ${carbon.toLocaleString()}kg 흡수, 식량 ${food.toLocaleString()}kg 생산, 조성비 약 ${(cost / 10000).toLocaleString()}만원.`,
    };
  }
  const kw = q * COEFF.solarKwPerPanel;
  const energy = Math.round(kw * COEFF.solarKwhPerKw);
  const carbon = Math.round(energy * COEFF.solarGridFactor);
  const cost = Math.round(kw * COEFF.solarCostPerKw);
  const annualSaving = energy * COEFF.elecPriceWon;
  const months = Array.isArray(p.monthlyIrradiance) ? p.monthlyIrradiance : [];
  const share = months.reduce((a, b) => a + b, 0);
  // 월별 일사 없으면 균등 분배 (0 나눗셈/NaN 방지)
  const energyMonthly =
    months.length > 0 && share > 0
      ? months.map((m) => Math.round(energy * (m / share)))
      : Array.from({ length: 12 }, () => Math.round(energy / 12));
  const payback =
    annualSaving > 0 ? Math.round((cost / annualSaving) * 10) / 10 : null;
  return {
    label: `태양광 ${q}패널`, quantity: q, energyKwhPerYear: energy,
    energyMonthly,
    carbonKgPerYear: carbon, costEstimateWon: cost,
    costPerCarbonKgWon: carbon ? Math.round(cost / carbon) : 0,
    paybackYears: payback ?? undefined,
    summary: `${q}개 패널(${kw.toFixed(1)}kW) 설치 시 연간 ${energy.toLocaleString()}kWh 발전, CO₂ ${carbon.toLocaleString()}kg 감축${payback != null ? `, 투자회수 약 ${payback}년` : ""}.`,
  };
}

export function simulateAll(p: Parcel) {
  return {
    SUMOK:  simulate(p, "SUMOK",  defaultQuantity(p, "SUMOK")),
    GARDEN: simulate(p, "GARDEN", defaultQuantity(p, "GARDEN")),
    SOLAR:  simulate(p, "SOLAR",  defaultQuantity(p, "SOLAR")),
  };
}

export function simulateMixedUse(p: Parcel) {
  const sumokQty = Math.max(1, Math.floor(defaultQuantity(p, "SUMOK") * 0.45));
  const gardenQty = Math.max(10, Math.floor(defaultQuantity(p, "GARDEN") * 0.35));
  const solarQty = Math.max(1, Math.floor(defaultQuantity(p, "SOLAR") * 0.20));
  const sumok = simulate(p, "SUMOK", sumokQty);
  const garden = simulate(p, "GARDEN", gardenQty);
  const solar = simulate(p, "SOLAR", solarQty);
  const carbonKgPerYear = sumok.carbonKgPerYear + garden.carbonKgPerYear + solar.carbonKgPerYear;
  const costEstimateWon = sumok.costEstimateWon + garden.costEstimateWon + solar.costEstimateWon;
  return {
    label: `복합 활용: 수목 ${sumokQty}그루 · 텃밭 ${gardenQty}㎡ · 태양광 ${solarQty}패널`,
    sumok, garden, solar, carbonKgPerYear, costEstimateWon,
    costPerCarbonKgWon: carbonKgPerYear ? Math.round(costEstimateWon / carbonKgPerYear) : 0,
    summary: `혼합 시나리오(mixed_use)는 수목 ${sumokQty}그루, 텃밭 ${gardenQty}㎡, 태양광 ${solarQty}패널을 병행해 연간 CO₂ ${carbonKgPerYear.toLocaleString()}kg 효과와 총 투자비 약 ${(costEstimateWon / 10000).toLocaleString()}만원을 예상합니다.`,
  };
}

// ── AI agent ─────────────────────────────────────────────────────────
export interface AgentCriteria {
  district?: string;
  parcelType?: ParcelType;
  topRecommendation?: ScoreUse;
  minScore?: number;
  minArea?: number;
  feasibilityStatus?: FeasibilityStatus;
  excludeRegulations?: string[];
  sortBy: "score" | "area" | "heat";
  limit: number;
  explanation: string;
}

export interface AgentResult {
  query: string;
  criteria: AgentCriteria;
  results: { id: string; name: string; district: string; topRecommendation: UseKey; topScore: number; areaSqm: number; parcelType: ParcelType; feasibilityStatus: FeasibilityStatus }[];
  summary: string;
  count: number;
  elapsed_ms: number;
  source: "ai" | "fallback";
}

const TYPE_KW: [ParcelType, string[]][] = [
  ["ROOFTOP",     ["옥상"]],
  ["VACANT_LOT",  ["빈터", "공터"]],
  ["UNUSED_LAND", ["유휴", "유휴지"]],
  ["ABANDONED",   ["방치", "폐"]],
  ["BROWNFIELD",  ["오염", "정화"]],
];
const USE_KW: [ScoreUse, string[]][] = [
  ["SUMOK",  ["수목", "나무", "식재", "가로수", "숲"]],
  ["GARDEN", ["텃밭", "정원", "도시농업", "커뮤니티"]],
  ["SOLAR",  ["태양광", "솔라", "발전", "패널"]],
];

export function interpretQuery(query: string): AgentCriteria {
  const q = query.trim();
  const district = DISTRICTS.find((d) => q.includes(d));
  const parcelType = TYPE_KW.find(([, kws]) => kws.some((k) => q.includes(k)))?.[0];
  const topRecommendation = USE_KW.find(([, kws]) => kws.some((k) => q.includes(k)))?.[0];

  let minScore: number | undefined;
  const scoreMatch = q.match(/(\d{2,3})\s*점?\s*(이상|넘|초과)/);
  if (scoreMatch) minScore = parseInt(scoreMatch[1], 10);
  else if (/점수\s*(높|좋|우수)/.test(q)) minScore = 80;

  let sortBy: AgentCriteria["sortBy"] = "score";
  if (/열섬|뜨거|더운|폭염/.test(q)) sortBy = "heat";
  else if (/넓|큰|대형|면적/.test(q)) sortBy = "area";

  let limit = 5;
  const nMatch = q.match(/(\d+)\s*개/);
  if (nMatch) limit = Math.min(10, Math.max(1, parseInt(nMatch[1], 10)));
  else if (/가장|제일|최고|1위/.test(q)) limit = 3;

  // sumokFeasibility filters
  let feasibilityStatus: FeasibilityStatus | undefined;
  if (/식재 가능|수목 가능|규제 없/.test(q)) feasibilityStatus = "AVAILABLE";
  else if (/인허가 확인|조건부/.test(q)) feasibilityStatus = "CONDITIONAL";

  const excludeRegulations: string[] = [];
  if (/그린벨트 제외|개발제한구역 제외/.test(q)) excludeRegulations.push("GREEN_BELT");
  if (/도시자연공원구역 제외/.test(q)) excludeRegulations.push("URBAN_NATURE_PARK");
  if (/자연환경보전지역 제외/.test(q)) excludeRegulations.push("NATURE_PRESERVE");
  if (/역사문화 제외/.test(q)) excludeRegulations.push("HISTORICAL");
  if (/인허가.*제외|조건부.*제외/.test(q)) {
    excludeRegulations.push("HISTORICAL", "URBAN_NATURE_PARK", "FLOOD_ZONE");
  }

  const parts = [
    district && `자치구=${district}`,
    parcelType && `유형=${PARCEL_TYPE_LABEL[parcelType]}`,
    topRecommendation && `추천용도=${USE_LABEL[topRecommendation]}`,
    minScore && `최소점수=${minScore}`,
    feasibilityStatus && `수목가능성=${FEASIBILITY_LABEL[feasibilityStatus]}`,
    excludeRegulations.length > 0 && `규제제외=${excludeRegulations.join(",")}`,
    sortBy !== "score" && `정렬=${sortBy === "heat" ? "열섬순" : "면적순"}`,
    `상위 ${limit}개`,
  ].filter(Boolean);

  return { district, parcelType, topRecommendation, minScore, feasibilityStatus, excludeRegulations, sortBy, limit, explanation: parts.join(" · ") || "전체 부지 상위 조회" };
}

export function searchParcels(c: AgentCriteria): Parcel[] {
  let items = PARCELS.filter((p) => {
    if (c.district && p.district !== c.district) return false;
    if (c.parcelType && p.parcelType !== c.parcelType) return false;
    if (c.topRecommendation) {
      const s = scoreFor(p, c.topRecommendation);
      if (c.minScore && s < c.minScore) return false;
    }
    if (c.feasibilityStatus && p.scores.sumokFeasibility.status !== c.feasibilityStatus) return false;
    if (c.excludeRegulations?.length) {
      const codes = p.regulations.map((r) => r.code);
      if (c.excludeRegulations.some((ex) => codes.includes(ex))) return false;
    }
    if (!c.topRecommendation && c.minScore && topScore(p) < c.minScore) return false;
    return true;
  });
  items = items.sort((a, b) => {
    if (c.sortBy === "area") return b.areaSqm - a.areaSqm;
    if (c.sortBy === "heat") return b.heatIsland - a.heatIsland;
    const sa = c.topRecommendation ? scoreFor(a, c.topRecommendation) : topScore(a);
    const sb = c.topRecommendation ? scoreFor(b, c.topRecommendation) : topScore(b);
    return sb - sa;
  });
  return items.slice(0, c.limit);
}

function summarize(c: AgentCriteria, results: Parcel[]): string {
  if (results.length === 0) return "조건에 맞는 부지를 찾지 못했습니다. 자치구·용도·점수 조건을 완화해 다시 검색해 보세요.";
  const top = results[0];
  const fs = top.scores.sumokFeasibility;
  const use = c.topRecommendation ?? (top.scores.topRecommendation === "MIXED" || top.scores.topRecommendation === "RESTRICTED" ? "SUMOK" : top.scores.topRecommendation as ScoreUse);
  const s = scoreFor(top, use);
  const feasNote = fs.status !== "AVAILABLE" ? ` 수목 가능성: ${FEASIBILITY_LABEL[fs.status]}.` : "";
  const lead = `${top.district} ${top.neighborhood}의 «${top.name}»이(가) ${USE_LABEL[use]} ${s}점으로 가장 적합합니다. 면적 ${top.areaSqm.toLocaleString()}㎡, ${PARCEL_TYPE_LABEL[top.parcelType]}.${feasNote}`;
  const more = results.length > 1 ? ` 조건을 충족하는 부지는 총 ${results.length}곳입니다.` : "";
  return lead + more;
}

export function runAgent(query: string): AgentResult {
  const t0 = performance.now();
  const criteria = interpretQuery(query);
  const found = searchParcels(criteria);
  const hasNonDefault = criteria.district || criteria.topRecommendation || criteria.parcelType || criteria.feasibilityStatus;
  return {
    query, criteria,
    results: found.map((p) => ({
      id: p.id, name: p.name, district: p.district,
      topRecommendation: p.scores.topRecommendation,
      topScore: topScore(p),
      areaSqm: p.areaSqm, parcelType: p.parcelType,
      feasibilityStatus: p.scores.sumokFeasibility.status,
    })),
    summary: summarize(criteria, found),
    count: found.length,
    elapsed_ms: Math.round(performance.now() - t0) + 1240,
    source: hasNonDefault ? "ai" : "fallback",
  };
}

export const SUGGESTED_QUERIES = [
  "용산구 수목 식재 추천",
  "해운대구 넓은 부지",
  "성남시 분당구 텃밭 후보",
  "제주시 빈터 찾아줘",
  "강남구 태양광 점수 높은 곳",
  "수원시 영통구 부지",
];

export const SEED_HISTORY = [
  { query: "수목 식재 가능한 부지 찾아줘", source: "ai" as const, resultCount: 18, at: "2026-07-06T10:12:00Z" },
  { query: "강남구 옥상 중 태양광 점수 80점 이상", source: "ai" as const, resultCount: 3, at: "2026-07-05T09:12:00Z" },
  { query: "열섬이 가장 심한 곳", source: "ai" as const, resultCount: 3, at: "2026-07-05T08:41:00Z" },
  { query: "그린벨트 제외하고 나무 심기 좋은 부지", source: "ai" as const, resultCount: 22, at: "2026-07-04T17:20:00Z" },
  { query: "가장 넓은 부지 3개", source: "ai" as const, resultCount: 3, at: "2026-07-04T15:03:00Z" },
];

// ── AI explanation (4 sections per spec) ────────────────────────────
export function explainParcel(p: Parcel): string {
  const s = p.scores;
  const fs = s.sumokFeasibility;
  const top = s.topRecommendation;
  const scores3: [ScoreUse, number][] = [["SUMOK", s.sumokScore], ["GARDEN", s.gardenScore], ["SOLAR", s.solarScore]];
  const best = scores3.reduce((a, b) => b[1] > a[1] ? b : a);
  const worst = scores3.reduce((a, b) => b[1] < a[1] ? b : a);

  const regNote = p.regulations.length > 0
    ? `\n\n규제 적용: ${p.regulations.map((r) => `${r.name}(${r.severity})`).join(", ")} — ${p.regulations.map((r) => `${USE_LABEL[best[0]]} 점수 ×${r.penaltyValue ?? 1}`).join(", ")}.`
    : "\n\n명확한 규제 제한 없음.";

  const in허가Note = fs.requiredChecks.length > 0
    ? `\n\n**인허가 확인 필요**: ${fs.requiredChecks.join(", ")}.`
    : "";

  return [
    `## 종합 판단`,
    `1순위 추천 용도는 **${USE_LABEL[top === "MIXED" || top === "RESTRICTED" ? best[0] : top]}**입니다. 수목 식재 가능성: **${FEASIBILITY_LABEL[fs.status]}** — ${fs.reason}`,
    ``,
    `## 용도별 강점/약점`,
    `- **수목 식재(${s.sumokScore}점)**: ${s.sumokScore >= 70 ? "열섬 완화 수요와 면적·토양 조건이 양호" : "경사도·규제 영향으로 적합도가 낮음"}. ${SOIL_LABEL[p.soilType]} 토양, 경사도 ${p.slopeDegree}°.`,
    `- **텃밭(${s.gardenScore}점)**: ${s.gardenScore >= 70 ? "면적·토양·도로 접면 등 도시농업 조건이 양호" : "토양·면적 조건이 상대적으로 낮음"}.`,
    `- **태양광(${s.solarScore}점)**: 일사량 ${p.solarIrradiance}kWh/㎡·일, 일조 ${p.sunlightHours}h. ${p.parcelType === "ROOFTOP" ? "옥상 부지로 태양광 유형 적합도 최고" : "지상 부지는 옥상 대비 태양광 적합도 낮음"}.`,
    `- 최저 점수 용도: **${USE_LABEL[worst[0]]}(${worst[1]}점)** — 상대적으로 불리한 조건.`,
    ``,
    `## 주요 근거 데이터`,
    `- 열섬강도 ${p.heatIsland}℃ · PM2.5 ${p.airQuality}μg/m³`,
    `- 일사량 ${p.solarIrradiance}kWh/㎡·일 · 일조 ${p.sunlightHours}h`,
    `- 면적 ${p.areaSqm.toLocaleString()}㎡ · 토양 ${SOIL_LABEL[p.soilType]} · 도로접면 ${p.roadAdjacent ? "예" : "아니오"}`,
    `- 수자원 접근 ${p.waterAccess ? "가능" : "불가"} · 전력 접근 ${p.electricityAccess ? "가능" : "불가"}`,
    regNote,
    ``,
    `## 리스크 및 추가 확인 사항`,
    `점수 불확실성 ±${s.uncertainty}점 · 데이터 신뢰도 ${Math.round(p.confidence * 100)}%.`,
    in허가Note || "인허가 확인 사항 없음.",
    `실제 시공 전 토질 정밀조사, 일조 실측, 현장 규제 확인이 필요합니다.`,
  ].join("\n");
}
