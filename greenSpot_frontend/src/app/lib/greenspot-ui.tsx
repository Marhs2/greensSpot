import { Sprout, Leaf, Sun, Layers, ShieldAlert } from "lucide-react";
import type { UseKey, ScoreUse } from "../data/greenspot";
import { USE_LABEL } from "../data/greenspot";

export const USE_META: Record<UseKey, { label: string; text: string; bg: string; hex: string; Icon: typeof Sprout }> = {
  SUMOK:      { label: USE_LABEL.SUMOK,      text: "text-tree",        bg: "bg-tree-soft",        hex: "var(--tree)",             Icon: Sprout },
  GARDEN:     { label: USE_LABEL.GARDEN,     text: "text-garden",      bg: "bg-garden-soft",      hex: "var(--garden)",           Icon: Leaf },
  SOLAR:      { label: USE_LABEL.SOLAR,      text: "text-solar",       bg: "bg-solar-soft",       hex: "var(--solar)",            Icon: Sun },
  MIXED:      { label: USE_LABEL.MIXED,      text: "text-foreground",  bg: "bg-muted",            hex: "var(--muted-foreground)", Icon: Layers },
  RESTRICTED: { label: USE_LABEL.RESTRICTED, text: "text-destructive", bg: "bg-destructive/10",   hex: "var(--destructive)",      Icon: ShieldAlert },
};

export function mono(cls = "") {
  return `font-mono tabular-nums ${cls}`;
}

export function ScoreBar({ use, value, showLabel = true }: { use: ScoreUse; value: number; showLabel?: boolean }) {
  const m = USE_META[use];
  return (
    <div className="flex items-center gap-2">
      {showLabel && (
        <span className={`flex w-9 shrink-0 items-center gap-1 text-xs ${m.text}`}>
          <m.Icon className="size-3" strokeWidth={2.4} />
        </span>
      )}
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full transition-[width] duration-500"
          style={{ width: `${value}%`, backgroundColor: m.hex }}
        />
      </div>
      <span className={`w-7 shrink-0 text-right ${mono("text-xs")} text-muted-foreground`}>{value}</span>
    </div>
  );
}

// Per-user bookmark type (used across BookmarkSheet / App)
export interface Bookmark {
  id: string;
  parcelId: string;
  parcelName: string;
  district: string;
  topRecommendation: UseKey;
  topScore: number;
  bookmarkedAt: string;
}
