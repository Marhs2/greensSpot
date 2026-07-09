import { LandPlot, Ruler, Sprout, Leaf, Sun, Gauge } from "lucide-react";
import { computeStats } from "../../data/greenspot";
import { useParcels } from "../../lib/parcelStore";
import { mono } from "../../lib/greenspot-ui";

function Tile({ icon: Icon, label, value, unit, accent }: { icon: typeof LandPlot; label: string; value: string | number; unit?: string; accent?: string }) {
  return (
    <div className="flex items-center gap-3 rounded-md border border-border bg-card px-3.5 py-3">
      <span className="flex size-9 shrink-0 items-center justify-center rounded-md" style={{ backgroundColor: accent ? `${accent}1f` : "var(--muted)", color: accent ?? "var(--muted-foreground)" }}>
        <Icon className="size-4.5" strokeWidth={2.2} />
      </span>
      <div className="min-w-0">
        <div className="truncate text-[11px] uppercase tracking-wide text-muted-foreground">{label}</div>
        <div className="flex items-baseline gap-1">
          <span className={mono("text-[19px] font-semibold text-foreground")}>{value}</span>
          {unit && <span className="text-[11px] text-muted-foreground">{unit}</span>}
        </div>
      </div>
    </div>
  );
}

export function StatsBar() {
  const parcels = useParcels();
  const stats = computeStats(parcels);

  return (
    <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-6">
      <Tile icon={LandPlot} label="분석 부지" value={stats.total} unit="곳" accent="var(--primary)" />
      <Tile icon={Ruler} label="총 면적" value={stats.totalAreaSqm.toLocaleString()} unit="㎡" />
      <Tile icon={Sprout} label="수목 식재 1위" value={stats.topSumokCount} unit="곳" accent="var(--tree)" />
      <Tile icon={Leaf} label="텃밭 1위" value={stats.topGardenCount} unit="곳" accent="var(--garden)" />
      <Tile icon={Sun} label="태양광 1위" value={stats.topSolarCount} unit="곳" accent="var(--solar)" />
      <Tile icon={Gauge} label="수목 식재 가능" value={stats.sumokFeasibility.AVAILABLE} unit="곳" accent="var(--tree)" />
    </div>
  );
}