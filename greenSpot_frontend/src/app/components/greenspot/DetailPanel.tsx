import { Component, useEffect, useMemo, useState, type ErrorInfo, type ReactNode } from "react";
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell,
} from "recharts";
import {
  Share2, FileDown, Star, Sparkles, Loader2, Ruler, Landmark, Layers, Droplets,
  Zap, Sun as SunIcon, Thermometer, Wind, Info, ShieldAlert, CheckCircle2, AlertTriangle, Ban,
} from "lucide-react";
import { Button } from "../ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../ui/tabs";
import { Slider } from "../ui/slider";
import { toast } from "sonner";
import {
  type Parcel, type ScoreUse, type FeasibilityStatus,
  scoreFor, PARCEL_TYPE_LABEL, OWNERSHIP_LABEL, SOIL_LABEL, USE_LABEL,
  FEASIBILITY_LABEL, defaultQuantity, SCENARIO_MAX, type ScenarioEffects,
} from "../../data/greenspot";
import { explainParcel as apiExplain, simulate as apiSimulate, exportReport, createShare, ApiError } from "../../lib/api";
import type { ScenarioType } from "../../lib/types";
import { USE_META, ScoreBar, mono } from "../../lib/greenspot-ui";

const USE_TO_SCENARIO: Record<ScoreUse, ScenarioType> = {
  SUMOK: "PLANT_TREES",
  GARDEN: "CREATE_GARDEN",
  SOLAR: "INSTALL_SOLAR",
};

function numOr(v: unknown, fallback = 0): number {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

function fmtNum(v: unknown, digits?: number): string {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  if (digits !== undefined) return n.toFixed(digits);
  return n.toLocaleString();
}

function mapApiEffects(effects: Record<string, unknown> | null | undefined, quantity: number): ScenarioEffects {
  const e = effects ?? {};
  // 백엔드 CREATE_GARDEN 은 yieldKgPerYear / yieldKg 등 여러 키 가능 → UI foodKgPerYear 로 통일
  const foodRaw =
    e.foodKgPerYear ??
    e.yieldKgPerYear ??
    e.yield_kg_per_year ??
    e.yieldKg ??
    e.food_kg_per_year;
  return {
    label: String(e.label ?? ""),
    quantity: numOr(quantity, 1),
    carbonKgPerYear: numOr(e.carbonKgPerYear),
    costEstimateWon: numOr(e.costEstimateWon),
    costPerCarbonKgWon: numOr(e.costPerCarbonKgWon),
    summary: String(e.summary ?? ""),
    // optional 지표도 숫자 기본값 0 — toLocaleString 크래시 방지
    pm25ReductionKgPerYear: numOr(e.pm25ReductionKgPerYear),
    temperatureReductionC: numOr(e.temperatureReductionC),
    rainwaterLitersPerYear: numOr(e.rainwaterLitersPerYear),
    foodKgPerYear: numOr(foodRaw),
    energyKwhPerYear: numOr(e.energyKwhPerYear),
    energyMonthly: Array.isArray(e.energyMonthly)
      ? (e.energyMonthly as unknown[]).map((x) => numOr(x))
      : undefined,
    paybackYears: e.paybackYears == null ? undefined : numOr(e.paybackYears),
    maintenanceRisk: (e.maintenanceRisk as ScenarioEffects["maintenanceRisk"]) ?? undefined,
  };
}

const MONTHS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"];

const FEASIBILITY_ICON: Record<FeasibilityStatus, typeof CheckCircle2> = {
  AVAILABLE: CheckCircle2, CONDITIONAL: AlertTriangle,
  RESTRICTED: ShieldAlert, PROHIBITED: Ban, UNKNOWN: Info,
};
const FEASIBILITY_COLOR: Record<FeasibilityStatus, string> = {
  AVAILABLE: "text-tree", CONDITIONAL: "text-garden",
  RESTRICTED: "text-solar", PROHIBITED: "text-destructive", UNKNOWN: "text-muted-foreground",
};

function Stat({ icon: Icon, label, value, unit }: { icon: typeof Ruler; label: string; value: string | number; unit?: string }) {
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2.5">
      <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
        <Icon className="size-3.5" /> {label}
      </div>
      <div className="mt-1 flex items-baseline gap-1">
        <span className={mono("text-[15px] font-semibold text-foreground")}>{value}</span>
        {unit && <span className="text-[11px] text-muted-foreground">{unit}</span>}
      </div>
    </div>
  );
}

function SectionTitle({ icon: Icon, children }: { icon: typeof Ruler; children: React.ReactNode }) {
  return (
    <h4 className="mb-2 flex items-center gap-1.5 text-[12px] uppercase tracking-wide text-muted-foreground">
      <Icon className="size-3.5" /> {children}
    </h4>
  );
}

// ── Tab: Overview ────────────────────────────────────────────────────
function OverviewTab({ p }: { p: Parcel }) {
  const fs = p.scores.sumokFeasibility;
  const FsIcon = FEASIBILITY_ICON[fs.status];
  const fsColor = FEASIBILITY_COLOR[fs.status];

  return (
    <div className="space-y-5">
      {/* sumokFeasibility card */}
      <div className={`rounded-md border p-3.5 ${fs.status === "AVAILABLE" ? "border-tree/40 bg-tree-soft/50" : fs.status === "PROHIBITED" ? "border-destructive/30 bg-destructive/5" : "border-border bg-muted/30"}`}>
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <FsIcon className={`size-5 ${fsColor}`} />
            <div>
              <div className="text-[11px] uppercase tracking-wide text-muted-foreground">수목 식재 가능성</div>
              <div className={`text-[14px] font-semibold ${fsColor}`}>{FEASIBILITY_LABEL[fs.status]}</div>
            </div>
          </div>
          <span className={mono("text-[13px] text-muted-foreground")}>신뢰도 {Math.round(fs.confidence * 100)}%</span>
        </div>
        <p className="mt-2 text-[12px] text-muted-foreground">{fs.reason}</p>
        {(fs.requiredChecks?.length ?? 0) > 0 && (
          <ul className="mt-2 space-y-0.5">
            {fs.requiredChecks!.map((c) => (
              <li key={c} className="flex items-center gap-1.5 text-[11px] text-garden">
                <AlertTriangle className="size-3" /> {c}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Regulations */}
      {p.regulations.length > 0 && (
        <div>
          <SectionTitle icon={ShieldAlert}>적용 규제</SectionTitle>
          <div className="space-y-1.5">
            {p.regulations.map((r, index) => (
              <div key={`${r.code}-${index}`} className="rounded-md border border-border bg-card px-3 py-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-[13px] font-medium text-foreground">{r.name}</span>
                  <span className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                    r.severity === "prohibited" ? "bg-destructive/10 text-destructive"
                    : r.severity === "restricted" ? "bg-solar-soft text-solar"
                    : "bg-garden-soft text-garden"
                  }`}>
                    {r.severity}
                  </span>
                </div>
                <p className="mt-0.5 text-[11px] text-muted-foreground">{r.description}</p>
                <p className="mt-0.5 text-[10px] text-muted-foreground opacity-70">{r.legalBasis}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <SectionTitle icon={Layers}>물리 · 환경 지표</SectionTitle>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          <Stat icon={Ruler} label="면적" value={Number(p.areaSqm || 0).toLocaleString()} unit="㎡" />
          <Stat icon={SunIcon} label="일사량" value={p.solarIrradiance ?? "—"} unit="kWh/㎡·일" />
          <Stat icon={SunIcon} label="일조시간" value={p.sunlightHours ?? "—"} unit="h" />
          <Stat
            icon={Thermometer}
            label="열섬강도"
            value={
              p.heatIsland == null
                ? "—"
                : p.heatIsland === 0
                  ? "0"
                  : p.heatIsland > 0
                    ? `+${p.heatIsland}`
                    : String(p.heatIsland)
            }
            unit="℃"
          />
          <Stat icon={Thermometer} label="여름 지표온도" value={p.surfaceTempSummer ?? "—"} unit="℃" />
          <Stat icon={Wind} label="PM2.5" value={p.airQuality ?? "—"} unit="μg/m³" />
        </div>
      </div>

      <div>
        <SectionTitle icon={Landmark}>부지 속성</SectionTitle>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          <Stat icon={Layers} label="유형" value={PARCEL_TYPE_LABEL[p.parcelType] ?? p.parcelType} />
          <Stat icon={Landmark} label="소유권" value={OWNERSHIP_LABEL[p.ownership] ?? p.ownership} />
          <Stat
            icon={Layers}
            label="토양"
            value={
              p.soilTypeLabel
              || p.soilDetail?.surttureName
              || SOIL_LABEL[p.soilType]
              || p.soilType
            }
          />
          <Stat icon={Droplets} label="수자원 접근" value={p.waterAccess ? "가능" : "불가/추정"} />
          <Stat icon={Zap} label="전력 접근" value={p.electricityAccess ? "가능" : "불가/추정"} />
          <Stat icon={Ruler} label="경사도" value={p.slopeDegree != null && p.slopeDegree > 0 ? p.slopeDegree : "—"} unit="°" />
        </div>
        {(() => {
          const soilProv = p.dataProvenance?.soilType;
          const actual = soilProv?.actual === true;
          const detail = p.soilDetail;
          return (
            <div className="mt-2 rounded-md border border-border bg-card px-3 py-2.5 text-[11px]">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-muted-foreground">토양 유형</span>
                <span className="font-medium text-foreground">
                  {p.soilTypeLabel || detail?.surttureName || SOIL_LABEL[p.soilType] || p.soilType}
                </span>
                <span
                  className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                    actual ? "bg-tree-soft text-tree" : "bg-muted text-muted-foreground"
                  }`}
                >
                  {actual ? "ACTUAL" : "ESTIMATED"}
                </span>
              </div>
              <div className="mt-1 text-muted-foreground">
                {soilProv?.source || "흙토람 (농진청)"}
                {soilProv?.dataType ? ` · ${soilProv.dataType}` : actual ? " · PNU 표토토성" : " · 미조회/미제공"}
                {p.pnu ? ` · PNU ${p.pnu}` : ""}
              </div>
              {detail && (detail.drainageName || detail.validDepthName || detail.surfaceStoneName) && (
                <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 text-muted-foreground">
                  {detail.drainageName && <span>배수 {detail.drainageName}</span>}
                  {detail.validDepthName && <span>유효토심 {detail.validDepthName}</span>}
                  {detail.surfaceStoneName && <span>자갈 {detail.surfaceStoneName}</span>}
                </div>
              )}
            </div>
          );
        })()}
      </div>

      <div className="flex items-start gap-2 rounded-md border border-border bg-muted/40 px-3 py-2.5 text-[11px] text-muted-foreground">
        <Info className="mt-0.5 size-3.5 shrink-0" />
        <span>데이터 출처: {p.dataSource} · 신뢰도 <span className={mono("text-foreground")}>{Math.round(p.confidence * 100)}%</span></span>
      </div>
    </div>
  );
}

// ── Tab: Scores ──────────────────────────────────────────────────────
function ScoresTab({ p }: { p: Parcel }) {
  const s = p.scores;
  const rawTop = String(s.topRecommendation || "").toUpperCase();
  const top: ScoreUse =
    rawTop === "MIXED" || rawTop === "RESTRICTED"
      ? (["SUMOK", "GARDEN", "SOLAR"] as ScoreUse[]).reduce(
          (best, u) => (scoreFor(p, u) > scoreFor(p, best) ? u : best),
          "SUMOK" as ScoreUse,
        )
      : rawTop === "TREE" || rawTop === "SUMOK"
        ? "SUMOK"
        : rawTop === "GARDEN"
          ? "GARDEN"
          : rawTop === "SOLAR"
            ? "SOLAR"
            : "SUMOK";
  const m = USE_META[top] ?? USE_META.SUMOK;
  const topS = scoreFor(p, top);

  // 실제 연동·물리 지표만 레이더에 사용 (보행·학교·지하철 등 미연동 축 제외)
  const soilScore = ({ LOAM: 95, SAND: 70, CLAY: 60, ROCKY: 25, UNKNOWN: 50 } as Record<string, number>)[p.soilType] ?? 50;
  const air = Number(p.airQuality);
  // PM2.5 낮을수록 좋음 → 점수 반전 (15 이하 100, 50 이상 0)
  const airScore = Number.isFinite(air)
    ? Math.round(Math.max(0, Math.min(100, (50 - air) / 35 * 100)))
    : 50;
  const infraScore = Math.min(
    100,
    (p.roadAdjacent ? 40 : 0) + (p.waterAccess ? 30 : 0) + (p.electricityAccess ? 30 : 0),
  );
  const radarData = [
    { axis: "열섬완화", v: Math.round(norm01(Number(p.heatIsland) || 0, 0.5, 4.5) * 100) },
    { axis: "일사/일조", v: Math.round(norm01(Number(p.sunlightHours) || 0, 4, 8) * 100) },
    { axis: "면적", v: Math.round(norm01(Number(p.areaSqm) || 0, 300, 8000) * 100) },
    { axis: "토양", v: soilScore },
    { axis: "대기질", v: airScore },
    { axis: "기반시설", v: infraScore },
  ];

  return (
    <div className="space-y-4">
      <div className="rounded-lg border p-4" style={{ borderColor: m.hex, backgroundColor: `${m.hex}0f` }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="flex size-8 items-center justify-center rounded-md" style={{ backgroundColor: m.hex, color: "#fff" }}>
              <m.Icon className="size-4.5" strokeWidth={2.4} />
            </span>
            <div>
              <div className="text-[11px] uppercase tracking-wide text-muted-foreground">
                {rawTop === "MIXED" ? "복합 활용 추천" : rawTop === "RESTRICTED" ? "제한 구역" : "1순위 추천"}
              </div>
              <div className="text-[15px] font-medium" style={{ color: m.hex }}>{USE_LABEL[top]}</div>
            </div>
          </div>
          <div className="text-right">
            <span className={mono("text-[30px] font-bold leading-none")} style={{ color: m.hex }}>{topS}</span>
            <div className="text-[11px] text-muted-foreground">±{s.uncertainty}점 · 신뢰도 {Math.round(p.confidence * 100)}%</div>
          </div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-md border border-border p-3">
          <SectionTitle icon={Layers}>기여 요인 프로파일</SectionTitle>
          <ResponsiveContainer width="100%" height={220}>
            <RadarChart data={radarData} outerRadius="72%">
              <PolarGrid stroke="var(--border)" />
              <PolarAngleAxis dataKey="axis" tick={{ fontSize: 10, fill: "var(--muted-foreground)" }} />
              <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
              <Radar dataKey="v" stroke={m.hex} fill={m.hex} fillOpacity={0.28} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-md border border-border p-3">
          <SectionTitle icon={Layers}>3중 용도 점수</SectionTitle>
          <div className="space-y-3 pt-1">
            {(["SUMOK", "GARDEN", "SOLAR"] as ScoreUse[]).map((u) => {
              const um = USE_META[u];
              const sc = scoreFor(p, u);
              return (
                <div key={u}>
                  <div className="mb-1 flex items-center justify-between text-[12px]">
                    <span className={`flex items-center gap-1.5 ${um.text}`}>
                      <um.Icon className="size-3.5" strokeWidth={2.4} /> {USE_LABEL[u]}
                    </span>
                    <span className={mono("font-semibold")} style={{ color: um.hex }}>
                      {sc} <span className="text-muted-foreground">±{s.uncertainty}</span>
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-muted">
                    <div className="h-full rounded-full" style={{ width: `${sc}%`, backgroundColor: um.hex }} />
                  </div>
                </div>
              );
            })}
          </div>
          <p className="mt-3 border-t border-border pt-2.5 text-[11px] leading-relaxed text-muted-foreground">
            {p.regulations.length > 0
              ? `규제 패널티 적용됨: ${p.regulations.map((r) => r.name).join(", ")}.`
              : "명확한 규제 제한 없음. 점수는 환경·물리 조건만 반영."}
          </p>
        </div>
      </div>
    </div>
  );
}

function norm01(v: number, min: number, max: number) {
  return Math.max(0, Math.min(1, (v - min) / (max - min)));
}

// ── Tab: AI explanation ──────────────────────────────────────────────
function renderMarkdown(md: string) {
  return md.split("\n").map((line, i) => {
    if (line.startsWith("## ")) {
      return <h4 key={i} className="mt-4 mb-1.5 text-[13px] font-semibold text-foreground first:mt-0">{line.slice(3)}</h4>;
    }
    if (line.startsWith("- ")) {
      const parts = line.slice(2).split(/(\*\*[^*]+\*\*)/g);
      return (
        <p key={i} className="ml-2 text-[12px] leading-relaxed text-muted-foreground">
          · {parts.map((seg, j) => seg.startsWith("**") ? <strong key={j} className="font-semibold text-foreground">{seg.slice(2, -2)}</strong> : seg)}
        </p>
      );
    }
    if (line.trim() === "") return <div key={i} className="h-1" />;
    const parts = line.split(/(\*\*[^*]+\*\*)/g);
    return (
      <p key={i} className="text-[13px] leading-relaxed text-muted-foreground">
        {parts.map((seg, j) => seg.startsWith("**") ? <strong key={j} className="font-semibold text-foreground">{seg.slice(2, -2)}</strong> : seg)}
      </p>
    );
  });
}

function AiTab({ p }: { p: Parcel }) {
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState<string | null>(null);

  async function generate() {
    setLoading(true);
    setText(null);
    try {
      const data = await apiExplain(p.id);
      setText(data.explanation);
    } catch (err) {
      setText(err instanceof ApiError ? err.message : "AI 설명 생성에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-start gap-2 rounded-md border border-dashed border-border bg-muted/30 px-3 py-2 text-[11px] text-muted-foreground">
        <Sparkles className="mt-0.5 size-3.5 shrink-0 text-primary" />
        AI는 검증된 facts 수치와 규제 데이터만 인용합니다. 4섹션(📍 부지 요약 / 🎯 추천 결과 / 💡 대안 용도 / ⚠️ 한계) 구조.
      </div>
      {!text && !loading && (
        <Button onClick={generate} className="w-full">
          <Sparkles className="size-4" /> AI 점수 설명 생성
        </Button>
      )}
      {loading && (
        <div className="flex items-center justify-center gap-2 rounded-md border border-dashed border-border py-8 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" /> AI가 근거를 정리하는 중…
        </div>
      )}
      {text && (
        <div className="rounded-md border border-border bg-card p-4">
          {renderMarkdown(text)}
          <Button variant="ghost" size="sm" onClick={generate} className="mt-3">
            <Sparkles className="size-3.5" /> 다시 생성
          </Button>
        </div>
      )}
    </div>
  );
}

// ── Tab: Simulation ──────────────────────────────────────────────────
class SimulationErrorBoundary extends Component<
  { children: ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.warn("[SimulationTab]", error, info.componentStack);
  }
  render() {
    if (this.state.error) {
      return (
        <div className="space-y-3 py-10 text-center text-sm text-muted-foreground">
          <p>시뮬레이션 화면을 표시하는 중 오류가 났습니다.</p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => this.setState({ error: null })}
          >
            다시 시도
          </Button>
        </div>
      );
    }
    return this.props.children;
  }
}

function SimulationTab({ p }: { p: Parcel }) {
  const pickDefaultUse = (parcel: Parcel): ScoreUse =>
    (["SUMOK", "GARDEN", "SOLAR"] as ScoreUse[]).reduce(
      (best, u) => (scoreFor(parcel, u) > scoreFor(parcel, best) ? u : best),
      "SUMOK" as ScoreUse,
    );
  const [use, setUse] = useState<ScoreUse>(() => pickDefaultUse(p));
  const [qty, setQty] = useState(() => defaultQuantity(p, pickDefaultUse(p)));
  const [eff, setEff] = useState<ScenarioEffects | null>(null);
  const [all, setAll] = useState<Record<ScoreUse, ScenarioEffects> | null>(null);
  const [simLoading, setSimLoading] = useState(false);
  const m = USE_META[use];

  // 필지 변경 시 용도·수량 초기화
  useEffect(() => {
    const next = pickDefaultUse(p);
    setUse(next);
    setQty(defaultQuantity(p, next));
    setEff(null);
    setAll(null);
  }, [p.id]);

  // 비교 차트용 COMPARE_ALL — 필지당 1회
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const simOpts = { areaSqm: p.areaSqm, parcelName: p.name };
        const compareAll = await apiSimulate(
          p.id,
          "COMPARE_ALL",
          defaultQuantity(p, pickDefaultUse(p)),
          simOpts,
        );
        if (cancelled || !compareAll?.scenarios) return;
        const scenarios = compareAll.scenarios;
        setAll({
          SUMOK: mapApiEffects(scenarios.PLANT_TREES?.effects ?? {}, defaultQuantity(p, "SUMOK")),
          GARDEN: mapApiEffects(scenarios.CREATE_GARDEN?.effects ?? {}, defaultQuantity(p, "GARDEN")),
          SOLAR: mapApiEffects(scenarios.INSTALL_SOLAR?.effects ?? {}, defaultQuantity(p, "SOLAR")),
        });
      } catch {
        if (!cancelled) setAll(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [p.id]);

  // 현재 용도·수량 시나리오 — 용도/수량 변경 시에만
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setSimLoading(true);
      try {
        const simOpts = { areaSqm: p.areaSqm, parcelName: p.name };
        const single = await apiSimulate(p.id, USE_TO_SCENARIO[use], qty, simOpts);
        if (cancelled) return;
        if (!single) throw new Error("simulate failed");
        const key = USE_TO_SCENARIO[use];
        const effects = single.scenarios?.[key]?.effects ?? single.effects ?? {};
        setEff(mapApiEffects(effects as Record<string, unknown>, qty));
      } catch {
        if (!cancelled) setEff(null);
      } finally {
        if (!cancelled) setSimLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [p.id, use, qty]);

  const unit = use === "SUMOK" ? "그루" : use === "GARDEN" ? "㎡" : "패널";

  const compareData = all
    ? (["SUMOK", "GARDEN", "SOLAR"] as ScoreUse[]).map((u) => ({
        use: USE_LABEL[u],
        carbon: numOr(all[u]?.carbonKgPerYear),
        fill: USE_META[u].hex,
      }))
    : [];

  if (simLoading && !eff) {
    return (
      <div className="flex items-center justify-center gap-2 py-16 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" /> 시뮬레이션 데이터를 불러오는 중…
      </div>
    );
  }

  if (!eff) {
    return (
      <div className="py-16 text-center text-sm text-muted-foreground">
        시뮬레이션 데이터를 불러오지 못했습니다.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-1.5">
        {(["SUMOK", "GARDEN", "SOLAR"] as ScoreUse[]).map((u) => {
          const um = USE_META[u]; const active = use === u;
          return (
            <button key={u} onClick={() => { setUse(u); setQty(defaultQuantity(p, u)); }}
              className={`flex flex-1 items-center justify-center gap-1.5 rounded-md border px-2 py-2 text-[12px] transition-colors ${active ? "text-white" : "border-border text-muted-foreground hover:bg-accent"}`}
              style={active ? { backgroundColor: um.hex, borderColor: um.hex } : undefined}>
              <um.Icon className="size-3.5" strokeWidth={2.4} /> {USE_LABEL[u]}
            </button>
          );
        })}
      </div>

      {/* sumokFeasibility warning in simulation */}
      {use === "SUMOK" && p.scores?.sumokFeasibility && p.scores.sumokFeasibility.status !== "AVAILABLE" && (
        <div className={`flex items-start gap-2 rounded-md border px-3 py-2.5 text-[12px] ${p.scores.sumokFeasibility.status === "PROHIBITED" ? "border-destructive/30 bg-destructive/5 text-destructive" : "border-garden/30 bg-garden-soft text-garden"}`}>
          <AlertTriangle className="mt-0.5 size-3.5 shrink-0" />
          <div>
            <span className="font-medium">{FEASIBILITY_LABEL[p.scores.sumokFeasibility.status] ?? p.scores.sumokFeasibility.status}</span>
            {(p.scores.sumokFeasibility.requiredChecks?.length ?? 0) > 0 && (
              <span className="ml-1 text-[11px] opacity-80">— {p.scores.sumokFeasibility.requiredChecks!.join(", ")}</span>
            )}
          </div>
        </div>
      )}

      <div className="rounded-md border border-border p-3">
        <div className="mb-2 flex items-center justify-between text-[12px]">
          <span className="text-muted-foreground">설치 수량</span>
          <span className={mono("font-semibold text-foreground")}>{fmtNum(qty)} {unit}</span>
        </div>
        <Slider value={[qty]} min={1} max={SCENARIO_MAX[use]} step={1} onValueChange={(v) => setQty(v[0])} />
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        <MetricCard label="연간 CO₂ 흡수/감축" value={fmtNum(eff?.carbonKgPerYear)} unit="kg" hex={m?.hex} />
        {use === "SUMOK" && <>
          <MetricCard label="PM2.5 저감" value={fmtNum(eff?.pm25ReductionKgPerYear, 2)} unit="kg/년" />
          <MetricCard label="기온 완화" value={fmtNum(eff?.temperatureReductionC, 1)} unit="℃" />
          <MetricCard label="우수 저류" value={fmtNum(eff?.rainwaterLitersPerYear)} unit="L/년" />
          {eff?.maintenanceRisk && (
            <MetricCard
              label="유지관리 리스크"
              value={eff.maintenanceRisk === "LOW" ? "낮음" : eff.maintenanceRisk === "MEDIUM" ? "보통" : "높음"}
              unit=""
            />
          )}
        </>}
        {use === "GARDEN" && (
          <MetricCard
            label="식량 생산"
            value={fmtNum(eff?.foodKgPerYear ?? (eff as { yieldKgPerYear?: number } | null)?.yieldKgPerYear)}
            unit="kg/년"
          />
        )}
        {use === "SOLAR" && <>
          <MetricCard label="연간 발전량" value={fmtNum(eff?.energyKwhPerYear)} unit="kWh" />
          <MetricCard label="투자 회수" value={fmtNum(eff?.paybackYears, 1)} unit="년" />
        </>}
        <MetricCard label="투자비" value={fmtNum(numOr(eff?.costEstimateWon) / 10000)} unit="만원" />
        <MetricCard label="CO₂ 1kg당 비용" value={fmtNum(eff?.costPerCarbonKgWon)} unit="원" />
      </div>

      <p className="rounded-md border border-border bg-muted/40 px-3 py-2.5 text-[12px] leading-relaxed text-foreground">{eff.summary}</p>

      {use === "SOLAR" && eff.energyMonthly && (
        <div className="rounded-md border border-border p-3">
          <SectionTitle icon={SunIcon}>월별 예상 발전량 (kWh)</SectionTitle>
          <ResponsiveContainer width="100%" height={170}>
            <BarChart data={eff.energyMonthly.map((v, i) => ({ m: MONTHS[i], v }))} margin={{ top: 4, right: 4, left: -18, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="m" tick={{ fontSize: 10, fill: "var(--muted-foreground)" }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 10, fill: "var(--muted-foreground)" }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "var(--muted)" }} />
              <Bar dataKey="v" fill="var(--solar)" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="rounded-md border border-border p-3">
        <SectionTitle icon={Layers}>용도별 연간 CO₂ 비교 (kg)</SectionTitle>
        <ResponsiveContainer width="100%" height={150}>
          <BarChart data={compareData} margin={{ top: 4, right: 4, left: -18, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="use" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} tickLine={false} axisLine={false} />
            <YAxis tick={{ fontSize: 10, fill: "var(--muted-foreground)" }} tickLine={false} axisLine={false} />
            <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "var(--muted)" }} />
            <Bar dataKey="carbon" radius={[2, 2, 0, 0]}>
              {compareData.map((d, i) => <Cell key={i} fill={d.fill} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

const tooltipStyle = { backgroundColor: "var(--popover)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 12, color: "var(--popover-foreground)" };

function MetricCard({ label, value, unit, hex }: { label: string; value: string; unit: string; hex?: string }) {
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2.5">
      <div className="text-[11px] text-muted-foreground">{label}</div>
      <div className="mt-1 flex items-baseline gap-1">
        <span className={mono("text-[15px] font-semibold")} style={{ color: hex ?? "var(--foreground)" }}>{value}</span>
        <span className="text-[11px] text-muted-foreground">{unit}</span>
      </div>
    </div>
  );
}

// ── Report export ────────────────────────────────────────────────────
function download(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a"); a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

async function downloadReport(parcelId: string, format: "markdown" | "json") {
  const blob = await exportReport(parcelId, format);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `greenspot-${parcelId}.${format === "markdown" ? "md" : "json"}`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Main panel ───────────────────────────────────────────────────────
export function DetailPanel({ parcel, bookmarked, onToggleBookmark }: { parcel: Parcel; bookmarked: boolean; onToggleBookmark: () => void }) {
  const rec = parcel.scores.topRecommendation === "TREE" ? "SUMOK" : parcel.scores.topRecommendation;
  const m = USE_META[rec] ?? USE_META.SUMOK;

  async function share() {
    // F-14: POST /api/share 로 shareId 발급 후 딥링크 복사 (실패 시 로컬 ?parcel= 폴백)
    let url = `${location.origin}/?parcel=${encodeURIComponent(parcel.id)}`;
    try {
      const res = await createShare(parcel.id);
      if (res?.url) {
        url = res.url.startsWith("http")
          ? res.url
          : `${location.origin}${res.url.startsWith("/") ? "" : "/"}${res.url}`;
      } else if (res?.shareId) {
        url = `${location.origin}/?parcel=${encodeURIComponent(parcel.id)}&share=${res.shareId}`;
      }
    } catch {
      /* 로컬 딥링크 폴백 */
    }
    try {
      await navigator.clipboard?.writeText(url);
      toast.success("공유 링크가 복사되었습니다", { description: url });
    } catch {
      toast.error("복사에 실패했습니다", { description: url });
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] ${m.bg} ${m.text}`}>
                <m.Icon className="size-3" strokeWidth={2.4} /> {USE_LABEL[rec] ?? rec}
              </span>
              <span className={mono("text-[11px] text-muted-foreground")}>{parcel.id}</span>
              {parcel.scores.sumokFeasibility?.status && parcel.scores.sumokFeasibility.status !== "AVAILABLE" && (
                <span className={`inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] ${FEASIBILITY_COLOR[parcel.scores.sumokFeasibility.status] ?? ""} bg-muted`}>
                  {(() => {
                    const Ic = FEASIBILITY_ICON[parcel.scores.sumokFeasibility.status] ?? Info;
                    return <Ic className="size-3" />;
                  })()}
                  {FEASIBILITY_LABEL[parcel.scores.sumokFeasibility.status] ?? parcel.scores.sumokFeasibility.status}
                </span>
              )}
            </div>
            <h2 className="mt-1 truncate text-[18px]">{parcel.name}</h2>
            <p className="text-[12px] text-muted-foreground">{parcel.district} {parcel.neighborhood}</p>
          </div>
          <div className="flex shrink-0 gap-1">
            <Button variant="outline" size="sm" onClick={onToggleBookmark} className={bookmarked ? "text-solar" : ""}>
              <Star className="size-4" fill={bookmarked ? "currentColor" : "none"} />
            </Button>
            <Button variant="outline" size="sm" onClick={share}>
              <Share2 className="size-4" /> <span className="hidden lg:inline">공유</span>
            </Button>
            <Button variant="outline" size="sm" onClick={() => downloadReport(parcel.id, "markdown")}>
              <FileDown className="size-4" /> MD
            </Button>
            <Button variant="outline" size="sm" onClick={() => downloadReport(parcel.id, "json")}>
              <FileDown className="size-4" /> JSON
            </Button>
          </div>
        </div>
      </div>

      <Tabs defaultValue="overview" className="flex min-h-0 flex-1 flex-col">
        <TabsList className="mx-4 mt-3 grid w-auto grid-cols-4">
          <TabsTrigger value="overview">개요</TabsTrigger>
          <TabsTrigger value="scores">점수</TabsTrigger>
          <TabsTrigger value="ai">AI 분석</TabsTrigger>
          <TabsTrigger value="sim">시뮬레이션</TabsTrigger>
        </TabsList>
        <div className="min-h-0 flex-1 overflow-y-auto p-4">
          <TabsContent value="overview" className="mt-0"><OverviewTab p={parcel} /></TabsContent>
          <TabsContent value="scores"   className="mt-0"><ScoresTab p={parcel} /></TabsContent>
          <TabsContent value="ai"       className="mt-0"><AiTab p={parcel} /></TabsContent>
          <TabsContent value="sim" className="mt-0">
            <SimulationErrorBoundary>
              <SimulationTab p={parcel} />
            </SimulationErrorBoundary>
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}

// need React for createElement
import React from "react";
