// GreenSpot — backend API client.
// Base URL is configurable via VITE_API_BASE. In development it defaults to the
// same origin so the Vite dev server can proxy "/api" to the FastAPI backend.
// Reference: backend/docs/api.md

import type {
  AgentResult,
  AuthUser,
  CompareResponse,
  ExplainResponse,
  Parcel,
  ParcelsResponse,
  ParcelDetailResponse,
  ScenarioResponse,
  ScenarioType,
  ShareResponse,
  StatsResponse,
  UserBookmark,
  UseKey,
} from "./types";

const API_BASE: string = ((import.meta.env.VITE_API_BASE as string | undefined) ?? "").replace(/\/+$/, "");

function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

// ── Token storage ───────────────────────────────────────────────────────
const ACCESS_KEY = "gs.access_token";
const REFRESH_KEY = "gs.refresh_token";
const SESSION_KEY = "gs.session";
const NAMES_KEY = "gs.names";

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}
function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}
export function setTokens(access?: string | null, refresh?: string | null): void {
  if (access) localStorage.setItem(ACCESS_KEY, access);
  else localStorage.removeItem(ACCESS_KEY);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  else localStorage.removeItem(REFRESH_KEY);
}
export function clearTokens(): void {
  setTokens(null, null);
}

function loadNames(): Record<string, string> {
  try {
    return JSON.parse(localStorage.getItem(NAMES_KEY) ?? "{}");
  } catch {
    return {};
  }
}
function saveName(email: string, name: string): void {
  const names = loadNames();
  names[email.toLowerCase()] = name;
  localStorage.setItem(NAMES_KEY, JSON.stringify(names));
}

export function loadSession(): AuthUser | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}
export function saveSession(user: AuthUser): void {
  localStorage.setItem(SESSION_KEY, JSON.stringify(user));
}
export function clearSession(): void {
  localStorage.removeItem(SESSION_KEY);
}

// ── Errors ──────────────────────────────────────────────────────────────
export class ApiError extends Error {
  status: number;
  detail?: string;
  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

// ── Low-level fetch ─────────────────────────────────────────────────────
let refreshing: Promise<boolean> | null = null;

async function apiFetch<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const url = apiUrl(path);
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401 && retry) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      return apiFetch<T>(path, options, false);
    }
    clearTokens();
    throw new ApiError(401, "인증이 만료되었습니다. 다시 로그인해 주세요.");
  }

  if (!res.ok) {
    let message = `요청 실패 (${res.status})`;
    let detail: string | undefined;
    try {
      const body = await res.json();
      const rawDetail = body?.detail ?? body?.error ?? body?.message;
      if (typeof rawDetail === "string") {
        detail = rawDetail;
        message = rawDetail;
      } else if (Array.isArray(rawDetail)) {
        // FastAPI validation errors
        detail = rawDetail
          .map((e: { msg?: string; loc?: unknown[] }) => e?.msg ?? JSON.stringify(e))
          .join("; ");
        message = detail || message;
      } else if (rawDetail != null) {
        detail = JSON.stringify(rawDetail);
        message = detail;
      }
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, message, detail);
  }

  if (res.status === 204) return undefined as T;
  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) return (await res.json()) as T;
  return (await res.text()) as unknown as T;
}

async function tryRefresh(): Promise<boolean> {
  if (refreshing) return refreshing;
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;
  refreshing = (async () => {
    try {
      const res = await fetch(apiUrl("/api/auth/refresh"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) return false;
      const data = (await res.json()) as { access_token: string; refresh_token: string };
      setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    } finally {
      refreshing = null;
    }
  })();
  return refreshing;
}

// ── Parcels ─────────────────────────────────────────────────────────────
export async function getParcels(params?: {
  district?: string;
  type?: string;
  live?: boolean;
  limit?: number;
}): Promise<ParcelsResponse> {
  const qs = new URLSearchParams();
  if (params?.district) qs.set("district", params.district);
  if (params?.type) qs.set("type", params.type);
  if (params?.live === false) qs.set("live", "false");
  else qs.set("live", "true");
  if (params?.limit) qs.set("limit", String(params.limit));
  const q = qs.toString();
  return apiFetch<ParcelsResponse>(`/api/gs/parcels${q ? `?${q}` : ""}`);
}

export async function getParcel(id: string): Promise<ParcelDetailResponse> {
  return apiFetch<ParcelDetailResponse>(`/api/gs/parcels/${encodeURIComponent(id)}`);
}

// ── Agent search ────────────────────────────────────────────────────────
const USE_LABEL_LOCAL: Record<UseKey, string> = {
  TREE: "수목 식재",
  GARDEN: "텃밭",
  SOLAR: "태양광",
};
const PARCEL_TYPE_LABEL_LOCAL: Record<string, string> = {
  VACANT_LOT: "빈터",
  ROOFTOP: "옥상",
  UNUSED_LAND: "유휴지",
  ABANDONED: "방치건물",
  BROWNFIELD: "오염정화지",
};

function topScoreFromScores(
  s: { topRecommendation?: UseKey; treeScore?: number; gardenScore?: number; solarScore?: number },
  preferred?: string | null,
): number {
  const use = (preferred || s.topRecommendation || "TREE").toString().toUpperCase();
  if (use === "TREE" || use === "SUMOK") return Number(s.treeScore) || 0;
  if (use === "GARDEN") return Number(s.gardenScore) || 0;
  if (use === "SOLAR") return Number(s.solarScore) || 0;
  return Math.max(Number(s.treeScore) || 0, Number(s.gardenScore) || 0, Number(s.solarScore) || 0);
}

function criteriaExplanation(c: Record<string, unknown>): string {
  const parts: string[] = [];
  if (c.district) parts.push(`자치구=${c.district}`);
  if (c.parcelType) parts.push(`유형=${PARCEL_TYPE_LABEL_LOCAL[c.parcelType as string] ?? c.parcelType}`);
  if (c.topRecommendation) parts.push(`추천용도=${USE_LABEL_LOCAL[c.topRecommendation as UseKey] ?? c.topRecommendation}`);
  if (c.minScore) parts.push(`최소점수=${c.minScore}`);
  if (c.sortBy && c.sortBy !== "score") parts.push(`정렬=${c.sortBy === "heat" ? "열섬순" : "면적순"}`);
  if (c.limit) parts.push(`상위 ${c.limit}개`);
  return parts.join(" · ") || "전체 부지 상위 조회";
}

export async function agentSearch(query: string): Promise<AgentResult> {
  const data = await apiFetch<{
    query: string;
    criteria: Record<string, unknown>;
    results: Array<Record<string, any>>;
    summary: string;
    count: number;
    elapsed_ms: number;
    source: "ai" | "fallback";
  }>(`/api/gs/agent`, {
    method: "POST",
    body: JSON.stringify({ query }),
  });

  // 소프트 정렬 시 표시 점수는 선호 용도(수목/텃밭/태양광) 기준
  const preferred = (data.criteria?.topRecommendation as string | undefined) ?? null;

  const results = data.results.map((r): AgentResult["results"][number] => {
    const scores = r.scores ?? {};
    const top: UseKey = scores.topRecommendation ?? "TREE";
    return {
      id: r.id,
      name: r.name,
      district: r.district,
      neighborhood: r.neighborhood,
      areaSqm: r.areaSqm ?? 0,
      parcelType: r.parcelType,
      topRecommendation: top,
      topScore: topScoreFromScores(scores, preferred),
      scores,
    };
  });

  return {
    query: data.query,
    criteria: { ...(data.criteria as any), explanation: criteriaExplanation(data.criteria) },
    results,
    parcels: data.results,
    summary: data.summary,
    count: data.count,
    elapsed_ms: data.elapsed_ms,
    source: data.source,
  };
}

export async function explainParcel(id: string): Promise<ExplainResponse> {
  return apiFetch<ExplainResponse>(`/api/gs/parcels/${encodeURIComponent(id)}/explain`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function simulate(
  id: string,
  scenarioType: ScenarioType,
  quantity: number,
  opts?: { areaSqm?: number; parcelName?: string },
): Promise<ScenarioResponse> {
  return apiFetch<ScenarioResponse>(`/api/gs/parcels/${encodeURIComponent(id)}/simulate`, {
    method: "POST",
    body: JSON.stringify({
      scenario_type: scenarioType,
      quantity,
      // 라이브 VW- 필지: DB에 없어도 시뮬레이션 가능하도록 힌트 전달
      area_sqm: opts?.areaSqm,
      parcel_name: opts?.parcelName,
    }),
  });
}

export async function compare(ids: string[]): Promise<CompareResponse> {
  return apiFetch<CompareResponse>(`/api/gs/compare`, {
    method: "POST",
    body: JSON.stringify({ ids }),
  });
}

export async function getStats(): Promise<StatsResponse> {
  return apiFetch<StatsResponse>(`/api/gs/stats`);
}

// ── Report / export ─────────────────────────────────────────────────────
export async function exportReport(parcelId: string, format: "markdown" | "json"): Promise<Blob> {
  const res = await fetch(apiUrl("/api/gs/report"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(getAccessToken() ? { Authorization: `Bearer ${getAccessToken()}` } : {}),
    },
    body: JSON.stringify({ parcelId, format }),
  });
  if (!res.ok) throw new ApiError(res.status, "리포트 생성에 실패했습니다.");
  return res.blob();
}

export async function exportCsv(): Promise<Blob> {
  const res = await fetch(apiUrl("/api/gs/export"), {
    headers: getAccessToken() ? { Authorization: `Bearer ${getAccessToken()}` } : {},
  });
  if (!res.ok) throw new ApiError(res.status, "CSV 내보내기에 실패했습니다.");
  return res.blob();
}

// ── Auth ────────────────────────────────────────────────────────────────
export interface AuthResult {
  user: AuthUser;
}

export async function signup(name: string, email: string, password: string): Promise<AuthUser> {
  const res = await fetch(apiUrl("/api/auth/signup"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    if (res.status === 409) throw new ApiError(409, "이미 사용 중인 이메일입니다.");
    if (res.status === 400) throw new ApiError(400, "입력값을 확인해 주세요.");
    throw new ApiError(res.status, "회원가입에 실패했습니다.");
  }
  saveName(email, name);
  return login(email, password);
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const res = await fetch(apiUrl("/api/auth/login"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    throw new ApiError(res.status, "이메일 또는 비밀번호가 올바르지 않습니다.");
  }
  const data = (await res.json()) as {
    access_token: string;
    refresh_token: string;
    user?: { id: string; email: string; created_at: string };
  };
  setTokens(data.access_token, data.refresh_token);

  const names = loadNames();
  const displayName = names[email.toLowerCase()] ?? email.split("@")[0];
  const user: AuthUser = {
    id: data.user?.id ?? email,
    email: data.user?.email ?? email,
    name: displayName,
    role: "user",
    createdAt: data.user?.created_at ?? new Date().toISOString(),
  };
  saveSession(user);
  return user;
}

export async function logout(): Promise<void> {
  const refreshToken = getRefreshToken();
  if (refreshToken) {
    try {
      await fetch(apiUrl("/api/auth/logout"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch {
      /* ignore */
    }
  }
  clearTokens();
  clearSession();
}

/** 세션 복원 — GET /users/me 제거 후 로컬 세션 + access token 존재로 판단 */
export async function getMe(): Promise<AuthUser | null> {
  const token = getAccessToken();
  if (!token) return null;
  return loadSession();
}

// ── Bookmarks ───────────────────────────────────────────────────────────
export async function getBookmarks(): Promise<UserBookmark[]> {
  const data = await apiFetch<{ bookmarks: UserBookmark[] }>(`/api/bookmarks`);
  return data.bookmarks.map((b) => ({ ...b, id: b.id ?? b.parcelId }));
}

export async function addBookmark(
  parcelId: string,
  meta?: {
    parcelName?: string;
    district?: string;
    topRecommendation?: string;
    topScore?: number;
  },
): Promise<void> {
  await apiFetch<{ ok: boolean }>(`/api/bookmarks`, {
    method: "POST",
    body: JSON.stringify({
      parcelId,
      parcelName: meta?.parcelName,
      district: meta?.district,
      topRecommendation: meta?.topRecommendation,
      topScore: meta?.topScore,
    }),
  });
}

export async function removeBookmark(parcelId: string): Promise<void> {
  await apiFetch<{ ok: boolean }>(`/api/bookmarks?parcelId=${encodeURIComponent(parcelId)}`, {
    method: "DELETE",
  });
}

export async function createShare(parcelId: string): Promise<ShareResponse> {
  return apiFetch<ShareResponse>(`/api/share`, {
    method: "POST",
    body: JSON.stringify({ parcelId }),
  });
}

// ── Health ──────────────────────────────────────────────────────────────
export async function getHealth(): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(`/api/gs/health`);
}
