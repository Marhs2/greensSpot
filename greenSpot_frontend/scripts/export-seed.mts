import { writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { PARCELS } from "../src/app/data/greenspot.ts";

const __dirname = dirname(fileURLToPath(import.meta.url));
const outPath = resolve(__dirname, "../../greenSpot_backend/scripts/seed_data.json");

function mapTopRec(rec: string): string {
  if (rec === "SUMOK") return "TREE";
  if (rec === "MIXED" || rec === "RESTRICTED") return "GARDEN";
  return rec;
}

const out = PARCELS.map((p) => ({
  id: p.id,
  name: p.name,
  district: p.district,
  neighborhood: p.neighborhood,
  lat: p.lat,
  lng: p.lng,
  area_sqm: p.areaSqm,
  parcel_type: p.parcelType,
  ownership: p.ownership,
  soil_type: p.soilType,
  solar_irradiance: p.solarIrradiance,
  monthly_irradiance: p.monthlyIrradiance,
  sunlight_hours: p.sunlightHours,
  heat_island: p.heatIsland,
  surface_temp_summer: p.surfaceTempSummer,
  air_quality: p.airQuality,
  nearby_households: p.nearbyHouseholds,
  pedestrian_flow: p.pedestrianFlow,
  road_adjacent: p.roadAdjacent,
  water_access: p.waterAccess,
  electricity_access: p.electricityAccess,
  nearby_schools: p.nearbySchools,
  nearby_hospitals: p.nearbyHospitals,
  nearby_parks: p.nearbyParks,
  nearby_subway_stations: p.nearbySubwayStations,
  regulatory_restriction: p.regulations.length ? p.regulations[0].code : "NONE",
  regulations: p.regulations.map((r) => ({
    code: r.code,
    name: r.name,
    severity: r.severity,
    affectedUses: r.affectedUses,
    penaltyType: r.penaltyType,
    penaltyValue: r.penaltyValue,
    legalBasis: r.legalBasis,
    description: r.description,
  })),
  sumok_feasibility: p.scores.sumokFeasibility,
  confidence: p.confidence,
  scores: {
    tree_score: p.scores.sumokScore,
    garden_score: p.scores.gardenScore,
    solar_score: p.scores.solarScore,
    top_recommendation: mapTopRec(p.scores.topRecommendation),
    uncertainty: p.scores.uncertainty,
  },
}));

writeFileSync(outPath, JSON.stringify(out, null, 2), "utf-8");
console.log(`Exported ${out.length} parcels → ${outPath}`);