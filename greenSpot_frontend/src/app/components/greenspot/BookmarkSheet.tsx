import { Star, Trash2, ArrowRight, LogIn } from "lucide-react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "../ui/sheet";
import { Button } from "../ui/button";
import { USE_META, mono } from "../../lib/greenspot-ui";
import type { AuthUser, UserBookmark } from "../../lib/types";
import { FEASIBILITY_LABEL, type FeasibilityStatus } from "../../data/greenspot";

export function BookmarkSheet({
  open,
  onOpenChange,
  bookmarks,
  onSelect,
  onClear,
  onRemove,
  user,
  onGoLogin,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  bookmarks: UserBookmark[];
  onSelect: (id: string) => void;
  onClear: () => void;
  onRemove: (parcelId: string) => void;
  user: AuthUser | null;
  onGoLogin: () => void;
}) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full gap-0 sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Star className="size-4.5 text-solar" fill="currentColor" /> 북마크한 부지
            {user && (
              <span className={mono("ml-1 rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground")}>
                {bookmarks.length}
              </span>
            )}
          </SheetTitle>
          <SheetDescription className="sr-only">
            북마크한 부지 목록입니다.
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 space-y-2 overflow-y-auto px-4 pb-4">
          {/* Not logged in state */}
          {!user && (
            <div className="flex flex-col items-center gap-4 rounded-lg border border-dashed border-border bg-muted/30 py-12 text-center">
              <Star className="size-8 opacity-25" />
              <div>
                <p className="text-[13px] font-medium text-foreground">로그인이 필요합니다</p>
                <p className="mt-1 text-[12px] text-muted-foreground">
                  로그인하면 북마크가 서버 DB에 영구 저장됩니다.
                </p>
              </div>
              <Button onClick={() => { onOpenChange(false); onGoLogin(); }}>
                <LogIn className="size-4" /> 로그인하기
              </Button>
            </div>
          )}

          {/* Logged in, no bookmarks */}
          {user && bookmarks.length === 0 && (
            <div className="flex flex-col items-center gap-2 py-16 text-center text-sm text-muted-foreground">
              <Star className="size-8 opacity-30" />
              저장된 부지가 없습니다.
              <span className="text-xs">부지 카드의 ☆ 버튼으로 추가하세요.</span>
            </div>
          )}

          {/* Bookmark list */}
          {user && bookmarks.map((b) => {
            const raw = (b.topRecommendation || "NONE").toString().toUpperCase();
            const useKey =
              raw === "TREE" || raw === "SUMOK" ? "SUMOK"
              : raw === "GARDEN" ? "GARDEN"
              : raw === "SOLAR" ? "SOLAR"
              : "MIXED";
            const m = USE_META[useKey] ?? USE_META.MIXED;
            return (
              <div
                key={b.id ?? b.parcelId}
                className="group flex items-center gap-3 rounded-md border border-border bg-card p-3 transition-colors hover:border-primary/40"
              >
                <button onClick={() => onSelect(b.parcelId)} className="flex min-w-0 flex-1 items-center gap-3 text-left">
                  <span className={`flex size-8 shrink-0 items-center justify-center rounded-md ${m.bg} ${m.text}`}>
                    <m.Icon className="size-4" strokeWidth={2.4} />
                  </span>
                  <div className="min-w-0">
                    <div className="truncate text-[13px] font-medium text-foreground">{b.parcelName}</div>
                    <div className="text-[11px] text-muted-foreground">
                      {b.district} · {m.label} <span className={mono("font-semibold")} style={{ color: m.hex }}>{b.topScore}</span>
                      {typeof b.sumokScore === "number" && <span> · SUMOK <span className={mono("text-tree")}>{b.sumokScore}</span></span>}
                    </div>
                    {b.feasibilityStatus && (
                      <div className="mt-0.5 text-[10px] text-muted-foreground">가능성: {FEASIBILITY_LABEL[b.feasibilityStatus as FeasibilityStatus] ?? b.feasibilityStatus}</div>
                    )}
                  </div>
                  <ArrowRight className="ml-auto size-3.5 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                </button>
                <button
                  onClick={() => onRemove(b.parcelId)}
                  className="flex size-6 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                >
                  <Trash2 className="size-3.5" />
                </button>
              </div>
            );
          })}
        </div>

        {user && bookmarks.length > 0 && (
          <div className="border-t border-border p-4">
            <Button variant="outline" className="w-full text-destructive" onClick={onClear}>
              <Trash2 className="size-4" /> 전체 삭제
            </Button>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
