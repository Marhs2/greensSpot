import { useEffect, useState } from "react";
import { X, Trophy, Crown, ShieldAlert, CheckCircle2, AlertTriangle, Loader2 } from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "../ui/dialog";
import { getParcel, type ScoreUse, scoreFor, topScore, PARCEL_TYPE_LABEL, USE_LABEL, FEASIBILITY_LABEL, type Parcel } from "../../data/greenspot";
import { compare as apiCompare } from "../../lib/api";
import { ensureParcel, findParcel } from "../../lib/parcelStore";
import { USE_META, mono } from "../../lib/greenspot-ui";

function toUiUse(rec: string) {
  if (rec === "TREE") return "SUMOK";
  return rec;
}

export function CompareDialog({ ids, open, onOpenChange, onRemove, onSelect }: {
  ids: string[]; open: boolean; onOpenChange: (o: boolean) => void;
  onRemove: (id: string) => void; onSelect: (id: string) => void;
}) {
  const [parcels, setParcels] = useState<Parcel[]>([]);
  const [loading, setLoading] = useState(false);
  const [carbonById, setCarbonById] = useState<Record<string, number>>({});

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    (async () => {
      const loaded: Parcel[] = [];
      for (const id of ids) {
        const p = findParcel(id) ?? getParcel(id) ?? (await ensureParcel(id));
        if (p) loaded.push(p);
      }
      if (!cancelled) setParcels(loaded);
    })();
    return () => {
      cancelled = true;
    };
  }, [open, ids.join("|")]);

  useEffect(() => {
    if (!open || ids.length < 2) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const data = await apiCompare(ids);
        if (cancelled) return;
        const map: Record<string, number> = {};
        for (const item of data.comparison ?? []) {
          const effects = (item.effects ?? {}) as Record<string, Record<string, number> | undefined>;
          const vals = Object.values(effects).map((e) => Number(e?.carbonKgPerYear ?? 0) || 0);
          map[item.id] = vals.length ? Math.max(...vals) : 0;
        }
        // API 에 없는 항목은 클라이언트 부지 점수 기반으로 0 유지
        setCarbonById(map);
      } catch {
        // 라이브 필지 비교 API 실패 시에도 UI 점수 비교는 유지
        if (!cancelled) setCarbonById({});
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [open, ids.join(",")]);

  const metrics: { key: string; label: string; value: (i: number) => number; fmt: (n: number) => string; higherBetter?: boolean }[] = [
    { key: "sumok", label: "수목 식재 점수", value: (i) => scoreFor(parcels[i], "SUMOK"), fmt: (n) => `${n}`, higherBetter: true },
    { key: "garden", label: "텃밭 점수", value: (i) => scoreFor(parcels[i], "GARDEN"), fmt: (n) => `${n}`, higherBetter: true },
    { key: "solar", label: "태양광 점수", value: (i) => scoreFor(parcels[i], "SOLAR"), fmt: (n) => `${n}`, higherBetter: true },
    { key: "carbon", label: "탄소 효율 (CO₂)", value: (i) => carbonById[parcels[i].id] ?? 0, fmt: (n) => `${n.toLocaleString()}kg`, higherBetter: true },
  ];

  const feasibilityRows = parcels.map((p) => p.scores.sumokFeasibility);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Trophy className="size-4.5 text-solar" /> 부지 비교 · {parcels.length}곳
            {loading && <Loader2 className="size-4 animate-spin text-muted-foreground" />}
          </DialogTitle>
          <DialogDescription className="sr-only">선택한 부지들의 점수와 수목 식재 가능성을 나란히 비교합니다.</DialogDescription>
        </DialogHeader>

        <div className="overflow-x-auto">
          <div className="grid gap-2 min-w-[520px]" style={{ gridTemplateColumns: `140px repeat(${parcels.length}, 1fr)` }}>
            <div />
            {parcels.map((p) => {
              const top = toUiUse(p.scores.topRecommendation === "SUMOK" ? "SUMOK" : p.scores.topRecommendation);
              const m = USE_META[top as keyof typeof USE_META] ?? USE_META.SUMOK;
              return (
                <div key={p.id} className="relative rounded-md border border-border bg-muted/30 p-2.5">
                  <button onClick={() => onRemove(p.id)} className="absolute right-1 top-1 flex size-5 items-center justify-center rounded text-muted-foreground hover:bg-accent">
                    <X className="size-3.5" />
                  </button>
                  <button onClick={() => onSelect(p.id)} className="block text-left">
                    <div className="truncate pr-4 text-[13px] font-medium text-foreground">{p.name}</div>
                    <div className="text-[11px] text-muted-foreground">{p.district} · {PARCEL_TYPE_LABEL[p.parcelType]}</div>
                    <div className="mt-1 flex items-center gap-1.5">
                      <span className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] ${m.bg} ${m.text}`}>
                        <m.Icon className="size-3" /> {m.label}
                      </span>
                      <span className={mono("text-[13px] font-semibold")} style={{ color: m.hex }}>{topScore(p)}</span>
                    </div>
                  </button>
                </div>
              );
            })}

            {metrics.map((metric) => {
              const vals = parcels.map((_, i) => metric.value(i));
              const best = metric.higherBetter !== false ? Math.max(...vals) : Math.min(...vals);
              return (
                <RowFragment key={metric.key} label={metric.label}>
                  {parcels.map((p, i) => {
                    const isBest = vals[i] === best && parcels.length > 1;
                    return (
                      <div key={p.id} className={`flex items-center gap-1.5 rounded-md border px-2.5 py-2 text-[13px] ${isBest ? "border-primary/50 bg-primary/5" : "border-border"}`}>
                        {isBest && <Crown className="size-3.5 text-solar" />}
                        <span className={mono("font-medium text-foreground")}>{metric.fmt(vals[i])}</span>
                      </div>
                    );
                  })}
                </RowFragment>
              );
            })}

            <RowFragment label="수목 식재 가능성">
              {feasibilityRows.map((fs, i) => {
                const Icon = fs.status === "AVAILABLE" ? CheckCircle2 : fs.status === "CONDITIONAL" ? AlertTriangle : ShieldAlert;
                return (
                  <div key={parcels[i].id} className="flex items-center gap-1.5 rounded-md border border-border px-2.5 py-2 text-[12px]">
                    <Icon className="size-3.5 shrink-0" />
                    <span>{FEASIBILITY_LABEL[fs.status]}</span>
                  </div>
                );
              })}
            </RowFragment>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function RowFragment({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <>
      <div className="flex items-center text-[12px] text-muted-foreground">{label}</div>
      {children}
    </>
  );
}

import React from "react";