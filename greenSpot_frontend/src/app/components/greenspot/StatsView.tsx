import { useMemo, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  PieChart, Pie, Cell, LineChart, Line,
} from "recharts";
import { Sprout, Leaf, Sun, LandPlot, TrendingUp, History, Search, ShieldAlert } from "lucide-react";
import {
  computeStats,
  districtsFromParcels,
  USE_LABEL,
  FEASIBILITY_LABEL,
  type UseKey,
  type FeasibilityStatus,
} from "../../data/greenspot";
import { useParcels } from "../../lib/parcelStore";
import { USE_META, mono } from "../../lib/greenspot-ui";
const EMPTY_REG_SEVERITY = (["info", "warning", "restricted", "prohibited"] as const).map((severity) => ({ severity, count: 0 }));

const tooltipStyle = {
  backgroundColor: "var(--popover)", border: "1px solid var(--border)",
  borderRadius: 6, fontSize: 12, color: "var(--popover-foreground)",
};

export interface HistoryEntry { query: string; source: "ai" | "fallback"; resultCount: number; at: string }

function Panel({ title, icon: Icon, children, className = "" }: { title: string; icon: typeof LandPlot; children: React.ReactNode; className?: string }) {
  return (
    <section className={`rounded-lg border border-border bg-card p-4 ${className}`}>
      <h3 className="mb-3 flex items-center gap-1.5 text-[13px] text-foreground">
        <Icon className="size-4 text-muted-foreground" /> {title}
      </h3>
      {children}
    </section>
  );
}

function SummaryCard({ icon: Icon, label, value, hex }: { icon: typeof LandPlot; label: string; value: number; hex?: string }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-3.5">
      <span className="flex size-10 items-center justify-center rounded-md" style={{ backgroundColor: hex ? `${hex}1f` : "var(--muted)", color: hex ?? "var(--muted-foreground)" }}>
        <Icon className="size-5" strokeWidth={2.2} />
      </span>
      <div>
        <div className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</div>
        <div className={mono("text-[22px] font-semibold text-foreground")}>{value}</div>
      </div>
    </div>
  );
}

const PERIODS = { "7d": 7, "30d": 30, "all": 9999 } as const;

/** 용도·유형 키워드 (지역명은 현재 선택 데이터에서 동적 추가) */
const TOPIC_KEYWORDS = [
  "수목", "식재", "나무", "텃밭", "태양광", "솔라", "옥상", "빈터", "유휴", "열섬", "넓은", "그린벨트", "규제",
];

const FEASIBILITY_COLORS: Record<FeasibilityStatus, string> = {
  AVAILABLE: "var(--tree)", CONDITIONAL: "var(--garden)",
  RESTRICTED: "var(--solar)", PROHIBITED: "var(--destructive)", UNKNOWN: "var(--muted-foreground)",
};

export function StatsView({ history }: { history: HistoryEntry[] }) {
  const parcels = useParcels();
  const stats = useMemo(() => computeStats(parcels), [parcels]);
  const selectedRegions = useMemo(() => districtsFromParcels(parcels), [parcels]);
  const [period, setPeriod] = useState<keyof typeof PERIODS>("30d");

  // 검색 기록: 현재 목록 지역과 관련된 쿼리만 (선택한 지역 기준)
  const periodHistory = useMemo(() => {
    const cutoff = Date.now() - PERIODS[period] * 86400000;
    return history.filter((h) => {
      if (period !== "all" && new Date(h.at).getTime() < cutoff) return false;
      if (selectedRegions.length === 0) return true;
      return selectedRegions.some((d) => h.query.includes(d));
    });
  }, [history, period, selectedRegions]);

  const byDistrict = stats.byDistrict ?? [];
  const byType = stats.byType ?? [];
  const byRecommendation = stats.byRecommendation ?? { SUMOK: 0, GARDEN: 0, SOLAR: 0, MIXED: 0, RESTRICTED: 0 };
  const regulationSeverity = stats.regulationSeverity ?? EMPTY_REG_SEVERITY;

  const districtData = byDistrict.map((d) => ({
    name: d.district, 수목: d.avgSumokScore, 텃밭: d.avgGardenScore, 태양광: d.avgSolarScore,
  }));

  // 1순위 추천 분포 = 현재 선택된(검색된) 부지 기준만
  const pieData = (["SUMOK", "GARDEN", "SOLAR", "MIXED"] as UseKey[])
    .map((u) => ({ name: USE_LABEL[u], value: byRecommendation[u as keyof typeof byRecommendation] ?? 0, hex: USE_META[u].hex }))
    .filter((d) => d.value > 0);

  const typeData = byType.map((t) => ({ name: t.label, count: t.count, area: t.totalArea }));

  const feasData: { name: string; value: number; hex: string }[] = (
    ["AVAILABLE", "CONDITIONAL", "RESTRICTED", "PROHIBITED", "UNKNOWN"] as FeasibilityStatus[]
  ).map((s) => ({
    name: FEASIBILITY_LABEL[s],
    value: stats.sumokFeasibility[s],
    hex: FEASIBILITY_COLORS[s],
  })).filter((d) => d.value > 0);

  // 인기 키워드: 선택 지역명 + 주제 키워드만 (서울 전체 고정 목록 X)
  const trending = useMemo(() => {
    const keywords = [...selectedRegions, ...TOPIC_KEYWORDS];
    const counts: Record<string, number> = {};
    periodHistory.forEach((h) =>
      keywords.forEach((k) => {
        if (h.query.includes(k)) counts[k] = (counts[k] ?? 0) + 1;
      }),
    );
    const arr = Object.entries(counts)
      .map(([keyword, count]) => ({ keyword, count }))
      .sort((a, b) => b.count - a.count);
    const max = arr[0]?.count ?? 1;
    return { arr: arr.slice(0, 8), max };
  }, [periodHistory, selectedRegions]);

  const subtitle =
    parcels.length === 0
      ? "검색으로 지역을 선택하면 해당 지역 통계가 표시됩니다."
      : `${stats.regionLabel} · ${stats.total}개 부지 · 수목 식재(SUMOK) 기준`;

  return (
    <div className="mx-auto max-w-[1600px] space-y-4 px-4 py-5 sm:px-6">
      <div>
        <h1 className="text-[22px]">통계 분석 대시보드</h1>
        <p className="text-[13px] text-muted-foreground">{subtitle}</p>
        {selectedRegions.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {selectedRegions.map((d) => (
              <span
                key={d}
                className="rounded-full border border-primary/30 bg-primary/10 px-2.5 py-0.5 text-[11px] font-medium text-primary"
              >
                {d}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <SummaryCard icon={LandPlot} label="총 분석 부지" value={stats.total} hex="var(--primary)" />
        <SummaryCard icon={Sprout} label="수목 식재 가능" value={stats.sumokFeasibility.AVAILABLE} hex="var(--tree)" />
        <SummaryCard icon={ShieldAlert} label="조건부·제한" value={stats.sumokFeasibility.CONDITIONAL + stats.sumokFeasibility.RESTRICTED} hex="var(--garden)" />
        <SummaryCard icon={Sun} label="태양광 1순위" value={stats.topSolarCount} hex="var(--solar)" />
        <SummaryCard icon={ShieldAlert} label="평균 신뢰도 %" value={stats.avgConfidence ?? 0} hex="var(--primary)" />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="지역별 평균 점수" icon={LandPlot} className="lg:col-span-2">
          {districtData.length === 0 ? (
            <p className="py-16 text-center text-[12px] text-muted-foreground">표시할 지역 데이터가 없습니다. 검색으로 지역을 선택하세요.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={districtData} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "var(--muted-foreground)" }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "var(--muted)" }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar key="bar-sumok"  dataKey="수목"   fill="var(--tree)"   radius={[2, 2, 0, 0]} />
                <Bar key="bar-garden" dataKey="텃밭"   fill="var(--garden)" radius={[2, 2, 0, 0]} />
                <Bar key="bar-solar"  dataKey="태양광" fill="var(--solar)"  radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Panel>

        <Panel title="1순위 추천 분포 (선택 지역)" icon={TrendingUp}>
          {pieData.length === 0 ? (
            <p className="py-16 text-center text-[12px] text-muted-foreground">선택 지역 부지 기준 추천이 없습니다.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={54} outerRadius={92} paddingAngle={3} strokeWidth={0}>
                  {pieData.map((d, i) => <Cell key={`pie-cell-${d.name}-${i}`} fill={d.hex} />)}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* sumokFeasibility distribution */}
        <Panel title="수목 식재 가능성 분포" icon={Sprout}>
          <div className="space-y-2.5 pt-1">
            {feasData.map((d) => (
              <div key={d.name}>
                <div className="mb-0.5 flex items-center justify-between text-[12px]">
                  <span className="text-foreground">{d.name}</span>
                  <span className={mono("font-semibold text-foreground")}>{d.value}<span className="ml-1 font-normal text-muted-foreground">곳</span></span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <div className="h-full rounded-full transition-[width] duration-500" style={{ width: `${(d.value / stats.total) * 100}%`, backgroundColor: d.hex }} />
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="부지 유형별 분포" icon={LandPlot}>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={typeData} layout="vertical" margin={{ top: 4, right: 12, left: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 10, fill: "var(--muted-foreground)" }} tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="name" width={64} tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "var(--muted)" }} />
              <Bar dataKey="count" name="부지 수" fill="var(--primary)" radius={[0, 2, 2, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="규제 심각도별 건수" icon={ShieldAlert}>
          <ResponsiveContainer width="100%" height={190}>
            <BarChart data={regulationSeverity.map((r) => ({ name: r.severity, count: r.count }))} margin={{ top: 4, right: 12, left: -18, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 10, fill: "var(--muted-foreground)" }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "var(--muted)" }} />
              <Bar dataKey="count" name="규제 수" fill="var(--solar)" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="검색량 추세" icon={TrendingUp}>
          <ResponsiveContainer width="100%" height={190}>
            <LineChart data={periodHistory.slice().reverse().map((h, i) => ({ idx: i + 1, count: h.resultCount }))} margin={{ top: 4, right: 12, left: -18, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="idx" tick={{ fontSize: 10, fill: "var(--muted-foreground)" }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 10, fill: "var(--muted-foreground)" }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={tooltipStyle} />
              <Line type="monotone" dataKey="count" stroke="var(--primary)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="인기 검색 키워드" icon={Search}>
          <div className="mb-3 flex gap-1">
            {([["7d", "7일"], ["30d", "30일"], ["all", "전체"]] as const).map(([k, label]) => (
              <button key={k} onClick={() => setPeriod(k)} className={`rounded border px-2 py-1 text-[11px] ${period === k ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground"}`}>{label}</button>
            ))}
          </div>
          <div className="space-y-2.5">
            {trending.arr.map((t) => (
              <div key={t.keyword}>
                <div className="mb-0.5 flex items-center justify-between text-[12px]">
                  <span className="text-foreground">{t.keyword}</span>
                  <span className={mono("text-muted-foreground")}>{t.count}</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                  <div className="h-full rounded-full bg-primary" style={{ width: `${(t.count / trending.max) * 100}%` }} />
                </div>
              </div>
            ))}
            {trending.arr.length === 0 && <p className="text-[12px] text-muted-foreground">검색 기록이 없습니다.</p>}
          </div>
        </Panel>

        <Panel title="최근 검색 기록" icon={History} className="lg:col-span-2">
          <div className="max-h-[220px] space-y-1.5 overflow-y-auto">
            {periodHistory.map((h, i) => (
              <div key={i} className="rounded-md border border-border px-2.5 py-2">
                <div className="flex items-center gap-1.5">
                  <span className={`rounded px-1 py-0.5 font-mono text-[9px] font-semibold ${h.source === "ai" ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"}`}>
                    {h.source.toUpperCase()}
                  </span>
                  <span className="truncate text-[12px] text-foreground">{h.query}</span>
                </div>
                <div className={mono("mt-0.5 text-[10px] text-muted-foreground")}>
                  결과 {h.resultCount}건 · {new Date(h.at).toLocaleString("ko-KR", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <Panel title="지역별 상세 (선택 지역)" icon={LandPlot}>
        <div className="overflow-x-auto">
          {byDistrict.length === 0 ? (
            <p className="py-8 text-center text-[12px] text-muted-foreground">선택 지역 데이터가 없습니다.</p>
          ) : (
            <table className="w-full text-[12px]">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="py-2 pr-4 font-medium">지역</th>
                  <th className="py-2 pr-4 text-right font-medium">부지</th>
                  <th className="py-2 pr-4 text-right font-medium">총 면적</th>
                  <th className="py-2 pr-4 text-right font-medium text-tree">수목 평균</th>
                  <th className="py-2 pr-4 text-right font-medium text-garden">텃밭 평균</th>
                  <th className="py-2 pr-4 text-right font-medium text-solar">태양광 평균</th>
                  <th className="py-2 pr-4 text-right font-medium">수목1위</th>
                  <th className="py-2 pr-4 text-right font-medium">텃밭1위</th>
                  <th className="py-2 text-right font-medium">태양광1위</th>
                </tr>
              </thead>
              <tbody className={mono("")}>
                {byDistrict.map((d) => (
                  <tr key={d.district} className="border-b border-border/60 last:border-0">
                    <td className="py-2 pr-4 font-sans text-foreground">{d.district}</td>
                    <td className="py-2 pr-4 text-right">{d.count}</td>
                    <td className="py-2 pr-4 text-right">{Number(d.totalArea || 0).toLocaleString()}</td>
                    <td className="py-2 pr-4 text-right text-tree">{d.avgSumokScore}</td>
                    <td className="py-2 pr-4 text-right text-garden">{d.avgGardenScore}</td>
                    <td className="py-2 pr-4 text-right text-solar">{d.avgSolarScore}</td>
                    <td className="py-2 pr-4 text-right">{d.SUMOK}</td>
                    <td className="py-2 pr-4 text-right">{d.GARDEN}</td>
                    <td className="py-2 text-right">{d.SOLAR}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Panel>
    </div>
  );
}
