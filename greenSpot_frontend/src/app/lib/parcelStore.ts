// GreenSpot — parcel data store backed by the backend API.
// A tiny external store so any component can subscribe to the fetched parcel
// list and re-render when it loads, without prop-drilling through App.

import { useSyncExternalStore } from "react";
import { getParcels as apiGetParcels, getParcel as apiGetParcel } from "./api";
import { apiParcelToUi } from "./parcelAdapter";
import { _setParcelLookup } from "../data/greenspot";
import type { Parcel } from "../data/greenspot";
import type { ParcelStats } from "./types";

_setParcelLookup(findParcel);

let parcels: Parcel[] = [];
/** 검색으로 목록이 교체돼도 북마크/비교용으로 유지하는 단건 캐시 */
const parcelCache = new Map<string, Parcel>();
let stats: ParcelStats | null = null;
let loading = false;
let error: string | null = null;
let listeners = new Set<() => void>();
let inflight: Promise<void> | null = null;
const hydrateInflight = new Map<string, Promise<Parcel | undefined>>();

function emit() {
  listeners.forEach((l) => l());
}

function recomputeStats(list: Parcel[]): ParcelStats {
  return {
    total: list.length,
    avgTreeScore: list.length
      ? Math.round(list.reduce((a, p) => a + p.scores.sumokScore, 0) / list.length)
      : 0,
    avgGardenScore: list.length
      ? Math.round(list.reduce((a, p) => a + p.scores.gardenScore, 0) / list.length)
      : 0,
    avgSolarScore: list.length
      ? Math.round(list.reduce((a, p) => a + p.scores.solarScore, 0) / list.length)
      : 0,
    topTreeCount: list.filter((p) => p.scores.topRecommendation === "SUMOK").length,
    topGardenCount: list.filter((p) => p.scores.topRecommendation === "GARDEN").length,
    topSolarCount: list.filter((p) => p.scores.topRecommendation === "SOLAR").length,
    totalAreaSqm: Math.round(list.reduce((a, p) => a + (p.areaSqm || 0), 0)),
  };
}

function remember(list: Parcel[]) {
  for (const p of list) parcelCache.set(p.id, p);
}

export function getLoadingSnapshot(): boolean {
  return loading;
}

export function getErrorSnapshot(): string | null {
  return error;
}

export function useParcelsLoading(): boolean {
  return useSyncExternalStore(subscribe, getLoadingSnapshot, () => false);
}

export function useParcelsError(): string | null {
  return useSyncExternalStore(subscribe, getErrorSnapshot, () => null);
}

export function getParcelsSnapshot(): Parcel[] {
  return parcels;
}

export function getStatsSnapshot(): ParcelStats | null {
  return stats;
}

export function useParcelStats(): ParcelStats | null {
  return useSyncExternalStore(subscribe, getStatsSnapshot, () => null);
}

export function subscribe(cb: () => void): () => void {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
}

export function findParcel(id: string | null | undefined): Parcel | undefined {
  if (!id) return undefined;
  return parcels.find((p) => p.id === id) ?? parcelCache.get(id);
}

/** 단건 병합 (목록 앞에 두고 캐시 유지) */
export function upsertParcel(p: Parcel, opts?: { selectToFront?: boolean }): void {
  parcelCache.set(p.id, p);
  const idx = parcels.findIndex((x) => x.id === p.id);
  if (idx >= 0) {
    const next = [...parcels];
    next[idx] = p;
    parcels = next;
  } else if (opts?.selectToFront !== false) {
    parcels = [p, ...parcels];
  } else {
    parcels = [...parcels, p];
  }
  stats = recomputeStats(parcels);
  emit();
}

/** 목록에 없으면 API로 hydrate. 성공 시 캐시·목록 반영 */
export async function ensureParcel(id: string): Promise<Parcel | undefined> {
  const hit = findParcel(id);
  if (hit) return hit;
  const existing = hydrateInflight.get(id);
  if (existing) return existing;

  const job = (async () => {
    try {
      const detail = await apiGetParcel(id);
      const raw = {
        ...(detail.parcel as Record<string, unknown>),
        scores: detail.scores ?? (detail.parcel as { scores?: unknown })?.scores,
      };
      const ui = apiParcelToUi(raw as Parameters<typeof apiParcelToUi>[0]);
      upsertParcel(ui);
      return ui;
    } catch {
      return undefined;
    } finally {
      hydrateInflight.delete(id);
    }
  })();
  hydrateInflight.set(id, job);
  return job;
}

/** AI/VWorld 실시간 검색 결과를 목록에 반영 (이전 캐시는 유지) */
export function setLiveParcels(apiRows: Array<Record<string, unknown>>): void {
  parcels = apiRows.map((p) => apiParcelToUi(p as Parameters<typeof apiParcelToUi>[0]));
  remember(parcels);
  stats = recomputeStats(parcels);
  error = null;
  loading = false;
  emit();
}

export async function searchLiveParcels(district: string, parcelType?: string): Promise<Parcel[]> {
  loading = true;
  error = null;
  emit();
  try {
    const data = await apiGetParcels({ district, type: parcelType, live: true });
    setLiveParcels(data.parcels ?? []);
  } catch (e) {
    error = e instanceof Error ? e.message : "실시간 조회에 실패했습니다.";
    emit();
  }
  return parcels;
}

export async function loadParcels(force = false): Promise<Parcel[]> {
  // 실시간 모드: DB 일괄 로드 대신 빈 상태 유지 (검색으로 채움)
  if (!force) return parcels;
  if (inflight && !force) return inflight.then(() => parcels);
  inflight = (async () => {
    loading = true;
    error = null;
    emit();
    try {
      const data = await apiGetParcels({ live: false });
      parcels = (data.parcels ?? []).map(apiParcelToUi);
      remember(parcels);
      stats = data.stats ?? recomputeStats(parcels);
    } catch (e) {
      parcels = [];
      stats = null;
      error = e instanceof Error ? e.message : "부지 데이터를 불러오지 못했습니다.";
    } finally {
      loading = false;
      inflight = null;
      emit();
    }
  })();
  return inflight.then(() => parcels);
}

export function useParcels(): Parcel[] {
  return useSyncExternalStore(subscribe, getParcelsSnapshot, getParcelsSnapshot);
}