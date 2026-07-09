import { useEffect, useMemo, useState } from "react";
import { Crown, Star, Plus, Check, MapPin, GitCompareArrows, Loader2 } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Button } from "../ui/button";
import {
  DISTRICTS,
  PARCEL_TYPES,
  PARCEL_TYPE_LABEL,
  topScore,
  type Parcel,
} from "../../data/greenspot";
import { useParcels, useParcelsLoading, useParcelsError, searchLiveParcels } from "../../lib/parcelStore";
import { USE_META, ScoreBar, mono } from "../../lib/greenspot-ui";

function ParcelCard({
  parcel,
  rank,
  selected,
  bookmarked,
  inCompare,
  onSelect,
  onToggleBookmark,
  onToggleCompare,
}: {
  parcel: Parcel;
  rank: number;
  selected: boolean;
  bookmarked: boolean;
  inCompare: boolean;
  onSelect: () => void;
  onToggleBookmark: () => void;
  onToggleCompare: () => void;
}) {
  const rec = parcel.scores.topRecommendation;
  const m = USE_META[rec === "TREE" ? "SUMOK" : rec] ?? USE_META.SUMOK;
  const top = topScore(parcel);
  return (
    <div
      onClick={onSelect}
      className={`group relative cursor-pointer rounded-md border bg-card p-3 transition-all ${
        selected ? "border-primary ring-1 ring-primary/40" : "border-border hover:border-primary/40"
      }`}
    >
      {selected && <span className="absolute inset-y-2 left-0 w-0.5 rounded-full bg-primary" />}
      <div className="flex items-start gap-2.5">
        <div className="flex w-6 shrink-0 flex-col items-center pt-0.5">
          {rank === 1 ? (
            <Crown className="size-4 text-solar" />
          ) : (
            <span className={mono("text-xs text-muted-foreground")}>{rank}</span>
          )}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h4 className="truncate text-[13px] text-foreground">{parcel.name}</h4>
            <span className={`inline-flex shrink-0 items-center gap-1 rounded px-1.5 py-0.5 text-[10px] ${m.bg} ${m.text}`}>
              <m.Icon className="size-3" strokeWidth={2.4} /> {m.label}
            </span>
          </div>
          <div className="mt-0.5 flex items-center gap-1 text-[11px] text-muted-foreground">
            <MapPin className="size-3" /> {parcel.district} {parcel.neighborhood}
            <span className="opacity-50">·</span> {parcel.areaSqm.toLocaleString()}㎡
            <span className="opacity-50">·</span> {PARCEL_TYPE_LABEL[parcel.parcelType]}
          </div>

          <div className="mt-2 space-y-1">
            <ScoreBar use="SUMOK" value={parcel.scores.sumokScore} />
            <ScoreBar use="GARDEN" value={parcel.scores.gardenScore} />
            <ScoreBar use="SOLAR" value={parcel.scores.solarScore} />
          </div>
        </div>

        <div className="flex shrink-0 flex-col items-end gap-1.5">
          <div className="text-right">
            <div className={mono("text-[18px] font-semibold leading-none")} style={{ color: m.hex }}>
              {top}
            </div>
            <div className="text-[10px] text-muted-foreground">±{parcel.scores.uncertainty}</div>
          </div>
          <div className="flex gap-1">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleBookmark();
              }}
              className={`flex size-6 items-center justify-center rounded transition-colors hover:bg-accent ${
                bookmarked ? "text-solar" : "text-muted-foreground"
              }`}
              aria-label="북마크"
            >
              <Star className="size-3.5" fill={bookmarked ? "currentColor" : "none"} />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleCompare();
              }}
              className={`flex size-6 items-center justify-center rounded transition-colors hover:bg-accent ${
                inCompare ? "bg-primary text-primary-foreground hover:bg-primary/90" : "text-muted-foreground"
              }`}
              aria-label="비교"
            >
              {inCompare ? <Check className="size-3.5" /> : <Plus className="size-3.5" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function ParcelList({
  selectedId,
  onSelect,
  isBookmarked,
  onToggleBookmark,
  compareIds,
  onToggleCompare,
  onOpenCompare,
  onFilteredChange,
}: {
  selectedId: string | null;
  onSelect: (id: string) => void;
  isBookmarked: (id: string) => boolean;
  onToggleBookmark: (p: Parcel) => void;
  compareIds: string[];
  onToggleCompare: (id: string) => void;
  onOpenCompare: () => void;
  onFilteredChange?: (items: Parcel[]) => void;
}) {
  const parcels = useParcels();
  const loading = useParcelsLoading();
  const error = useParcelsError();
  const [district, setDistrict] = useState("ALL");
  const [type, setType] = useState("ALL");

  // 시드 서울 구 + 현재 라이브 결과에 있는 지역 (해운대/성남 등)
  const districtOptions = useMemo(() => {
    const fromLive = parcels.map((p) => p.district).filter(Boolean);
    return Array.from(new Set([...DISTRICTS, ...fromLive]));
  }, [parcels]);

  const filtered = useMemo(() => {
    return parcels.filter((p) => (district === "ALL" || p.district === district) && (type === "ALL" || p.parcelType === type)).sort(
      (a, b) => topScore(b) - topScore(a),
    );
  }, [parcels, district, type]);

  useEffect(() => {
    onFilteredChange?.(filtered);
  }, [filtered, onFilteredChange]);

  useEffect(() => {
    if (district === "ALL") return;
    searchLiveParcels(district, type === "ALL" ? undefined : type);
  }, [district, type]);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-border px-3 py-2.5">
        <Select value={district} onValueChange={setDistrict}>
          <SelectTrigger className="h-8 flex-1 bg-input-background text-xs">
            <SelectValue placeholder="지역" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">전체 지역</SelectItem>
            {districtOptions.map((d) => (
              <SelectItem key={d} value={d}>
                {d}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={type} onValueChange={setType}>
          <SelectTrigger className="h-8 flex-1 bg-input-background text-xs">
            <SelectValue placeholder="부지유형" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">전체 유형</SelectItem>
            {PARCEL_TYPES.map((t) => (
              <SelectItem key={t} value={t}>
                {PARCEL_TYPE_LABEL[t]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center justify-between px-3 py-2 text-[11px] text-muted-foreground">
        <span>
          <span className={mono("text-foreground")}>{filtered.length}</span>개 부지 · 점수순
        </span>
        {compareIds.length > 0 && (
          <Button size="sm" variant="secondary" className="h-7 gap-1 px-2 text-xs" onClick={onOpenCompare}>
            <GitCompareArrows className="size-3.5" /> 비교 ({compareIds.length})
          </Button>
        )}
      </div>

      <div className="flex-1 space-y-2 overflow-y-auto px-3 pb-4">
        {loading && (
          <div className="flex items-center justify-center gap-2 py-10 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" /> 불러오는 중…
          </div>
        )}
        {!loading && filtered.map((p, i) => (
          <ParcelCard
            key={p.id}
            parcel={p}
            rank={i + 1}
            selected={selectedId === p.id}
            bookmarked={isBookmarked(p.id)}
            inCompare={compareIds.includes(p.id)}
            onSelect={() => onSelect(p.id)}
            onToggleBookmark={() => onToggleBookmark(p)}
            onToggleCompare={() => onToggleCompare(p.id)}
          />
        ))}
        {error && !loading && (
          <div className="py-10 text-center text-sm text-destructive">{error}</div>
        )}
        {!error && !loading && filtered.length === 0 && (
          <div className="px-4 py-10 text-center text-sm text-muted-foreground">
            AI 검색창에 지역을 입력하세요.
            <br />
            <span className="text-[12px]">예: 용산구, 해운대구, 성남시, 제주시</span>
          </div>
        )}
      </div>
    </div>
  );
}
