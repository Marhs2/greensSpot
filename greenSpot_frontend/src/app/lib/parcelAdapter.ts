// Maps backend API parcel shapes to the UI model used by greenspot components.
// Backend uses TREE / treeScore; the UI uses SUMOK / sumokScore.

import {
  REG_CATALOG,
  type Parcel as UiParcel,
  type RegulationEntry,
  type Scores as UiScores,
  type UseKey,
} from "../data/greenspot";
import type { Parcel as ApiParcel, Scores as ApiScores, UseKey as ApiUseKey } from "./types";

function mapTopRecommendation(rec: ApiUseKey | string): UseKey {
  if (rec === "TREE") return "SUMOK";
  return rec as UseKey;
}

function mapRegulations(code?: string): RegulationEntry[] {
  if (!code || code === "NONE") return [];
  return REG_CATALOG[code] ? [REG_CATALOG[code]] : [];
}

function defaultFeasibility(tree: number, confidence: number): UiScores["sumokFeasibility"] {
  return {
    status: "AVAILABLE",
    score: tree,
    reason: "백엔드 점수 데이터 기준",
    blockingRegulations: [],
    warningRegulations: [],
    requiredChecks: [],
    confidence,
  };
}

function mapScores(
  scores?: ApiScores,
  confidence = 0.9,
  sumokFeasibility?: Record<string, unknown> | null,
): UiScores {
  const tree = scores?.treeScore ?? 0;
  const garden = scores?.gardenScore ?? 0;
  const solar = scores?.solarScore ?? 0;
  const top = mapTopRecommendation(scores?.topRecommendation ?? "SUMOK");
  const uncertainty = scores?.uncertainty ?? 5;

  const raw = sumokFeasibility as Partial<UiScores["sumokFeasibility"]> | undefined | null;
  const fs: UiScores["sumokFeasibility"] = raw?.status
    ? {
        status: raw.status,
        score: Number(raw.score ?? tree) || tree,
        reason: String(raw.reason ?? ""),
        blockingRegulations: Array.isArray(raw.blockingRegulations) ? raw.blockingRegulations : [],
        warningRegulations: Array.isArray(raw.warningRegulations) ? raw.warningRegulations : [],
        requiredChecks: Array.isArray(raw.requiredChecks) ? raw.requiredChecks : [],
        confidence: Number(raw.confidence ?? confidence) || confidence,
      }
    : defaultFeasibility(tree, confidence);

  return {
    sumokScore: tree,
    gardenScore: garden,
    solarScore: solar,
    topRecommendation: top,
    uncertainty,
    sumokFeasibility: fs,
  };
}

function mapApiRegulations(
  restriction: string,
  regs?: Array<Record<string, unknown>>,
): RegulationEntry[] {
  if (regs?.length) {
    return regs.map((r) => ({
      code: String(r.code ?? ""),
      name: String(r.name ?? ""),
      severity: r.severity as RegulationEntry["severity"],
      affectedUses: (r.affectedUses ?? r.affected_uses ?? ["all"]) as RegulationEntry["affectedUses"],
      penaltyType: (r.penaltyType ?? r.penalty_type ?? "none") as RegulationEntry["penaltyType"],
      penaltyValue: r.penaltyValue as number | undefined,
      legalBasis: String(r.legalBasis ?? r.legal_basis ?? ""),
      description: String(r.description ?? ""),
    }));
  }
  return mapRegulations(restriction);
}

export function apiParcelToUi(p: ApiParcel & {
  regulations?: Array<Record<string, unknown>>;
  sumokFeasibility?: Record<string, unknown> | null;
}): UiParcel {
  const restriction =
    typeof p.regulatoryRestriction === "string"
      ? p.regulatoryRestriction
      : "NONE";

  return {
    id: p.id,
    name: p.name,
    district: p.district,
    neighborhood: p.neighborhood,
    lat: p.lat,
    lng: p.lng,
    areaSqm: p.areaSqm,
    parcelType: p.parcelType,
    ownership: p.ownership,
    soilType: p.soilType,
    soilTypeLabel: p.soilTypeLabel ?? null,
    soilDetail: p.soilDetail ?? null,
    pnu: p.pnu ?? null,
    dataProvenance: p.dataProvenance,
    elevationM: p.elevationM ?? 0,
    slopeDegree: p.slopeDegree ?? 0,
    solarIrradiance: p.solarIrradiance,
    monthlyIrradiance: p.monthlyIrradiance ?? [],
    sunlightHours: p.sunlightHours,
    heatIsland: p.heatIsland,
    surfaceTempSummer: p.surfaceTempSummer,
    airQuality: p.airQuality,
    // 사회·접근성 지표(보행/학교/지하철 등)는 미연동 — 매핑만 유지, UI 미사용
    nearbyHouseholds: p.nearbyHouseholds ?? null,
    pedestrianFlow: p.pedestrianFlow ?? null,
    roadAdjacent: Boolean(p.roadAdjacent),
    waterAccess: Boolean(p.waterAccess),
    electricityAccess: Boolean(p.electricityAccess),
    nearbySchools: p.nearbySchools ?? null,
    nearbyHospitals: p.nearbyHospitals ?? null,
    nearbyParks: p.nearbyParks ?? null,
    nearbySubwayStations: p.nearbySubwayStations ?? null,
    regulations: mapApiRegulations(restriction, p.regulations),
    estimatedAcquisitionCostWon: p.estimatedAcquisitionCostWon ?? 0,
    dataSource: p.dataSource ?? "GreenSpot DB",
    confidence: p.confidence,
    scores: mapScores(p.scores, p.confidence, p.sumokFeasibility),
  };
}