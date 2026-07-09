import { useState, useRef, useEffect } from "react";
import { Leaf, Moon, Sun, Download, Star, BarChart3, LayoutDashboard, LogIn, UserPlus, LogOut, ChevronDown, ShieldCheck } from "lucide-react";
import { Button } from "../ui/button";
import { type Parcel } from "../../data/greenspot";
import { exportCsv as apiExportCsv } from "../../lib/api";
import type { AuthUser } from "../../lib/types";

type View = "dashboard" | "stats" | "login" | "register";

function downloadClientCsv(items: Parcel[]) {
  const esc = (v: unknown) => {
    const s = v == null ? "" : String(v);
    if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
    return s;
  };
  const headers = [
    "ID", "부지명", "자치구", "행정동", "면적(㎡)", "유형", "소유권", "토양",
    "일사량", "일조", "열섬", "PM2.5", "도로접면", "수자원", "전력",
    "수목점수", "텃밭점수", "태양광점수", "1순위", "불확실성",
  ];
  const rows = items.map((p) => [
    p.id, p.name, p.district, p.neighborhood, p.areaSqm, p.parcelType, p.ownership, p.soilType,
    p.solarIrradiance, p.sunlightHours, p.heatIsland, p.airQuality,
    p.roadAdjacent ? "Y" : "N", p.waterAccess ? "Y" : "N", p.electricityAccess ? "Y" : "N",
    p.scores.sumokScore, p.scores.gardenScore, p.scores.solarScore,
    p.scores.topRecommendation, p.scores.uncertainty,
  ]);
  const csv = "\uFEFF" + [headers, ...rows].map((r) => r.map(esc).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `greenspot-parcels-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

async function downloadCsv(exportItems: Parcel[]) {
  // 화면에 보이는 라이브/필터 목록이 있으면 그걸 내보냄 (DB 시드 전체와 혼동 방지)
  if (exportItems.length > 0) {
    downloadClientCsv(exportItems);
    return;
  }
  const blob = await apiExportCsv();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `greenspot-parcels-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

function UserDropdown({ user, onLogout }: { user: AuthUser; onLogout: () => void }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handle(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, []);

  const initials = user.name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-md border border-border bg-card px-2.5 py-1.5 text-[13px] text-foreground transition-colors hover:bg-accent"
      >
        <span className="flex size-6 items-center justify-center rounded-full bg-primary text-[10px] font-semibold text-primary-foreground">
          {initials}
        </span>
        <span className="hidden max-w-[96px] truncate sm:inline">{user.name}</span>
        <ChevronDown className="size-3.5 text-muted-foreground" />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1.5 w-56 overflow-hidden rounded-lg border border-border bg-popover shadow-md">
          <div className="border-b border-border px-4 py-3">
            <div className="truncate text-[13px] font-medium text-foreground">{user.name}</div>
            <div className="truncate text-[11px] text-muted-foreground">{user.email}</div>
            <div className="mt-1 flex items-center gap-1 text-[10px] text-muted-foreground">
              <ShieldCheck className="size-3" />
              회원 · 북마크 DB 저장 활성
            </div>
          </div>
          <button
            onClick={() => { setOpen(false); onLogout(); }}
            className="flex w-full items-center gap-2 px-4 py-2.5 text-[13px] text-destructive hover:bg-destructive/10"
          >
            <LogOut className="size-4" /> 로그아웃
          </button>
        </div>
      )}
    </div>
  );
}

export function Header({
  view,
  onView,
  dark,
  onToggleDark,
  bookmarkCount,
  onOpenBookmarks,
  user,
  onLogout,
  exportItems = [],
}: {
  view: View;
  onView: (v: View) => void;
  dark: boolean;
  onToggleDark: () => void;
  bookmarkCount: number;
  onOpenBookmarks: () => void;
  user: AuthUser | null;
  onLogout: () => void;
  exportItems?: Parcel[];
}) {
  return (
    <header className="sticky top-0 z-30 border-b border-border bg-card/85 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-[1600px] items-center gap-3 px-4 sm:px-6">
        <button onClick={() => onView("dashboard")} className="flex items-center gap-2.5 outline-none">
          <span className="flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Leaf className="size-4.5" strokeWidth={2.5} />
          </span>
          <span className="flex items-baseline gap-1.5">
            <span className="font-display text-[17px] font-bold tracking-tight text-foreground">GreenSpot</span>
          </span>
        </button>

        <span className="ml-1 hidden text-xs text-muted-foreground md:inline">서울 도시 녹지 인프라 의사결정 대시보드</span>

        <div className="ml-auto flex items-center gap-1">
          <Button
            variant={view === "dashboard" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => onView("dashboard")}
            className="hidden sm:inline-flex"
          >
            <LayoutDashboard className="size-4" /> 대시보드
          </Button>
          <Button
            variant={view === "stats" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => onView("stats")}
          >
            <BarChart3 className="size-4" /> 통계
          </Button>
          <Button variant="ghost" size="sm" onClick={() => downloadCsv(exportItems)} className="hidden sm:inline-flex">
            <Download className="size-4" /> CSV{exportItems.length > 0 ? `(${exportItems.length})` : ""}
          </Button>
          <Button variant="ghost" size="sm" onClick={onOpenBookmarks} className="relative">
            <Star className="size-4" /> 북마크
            {bookmarkCount > 0 && (
              <span className="absolute -right-1 -top-1 flex size-4.5 min-w-4.5 items-center justify-center rounded-full bg-destructive px-1 font-mono text-[10px] font-semibold leading-none text-destructive-foreground">
                {bookmarkCount}
              </span>
            )}
          </Button>
          <Button variant="ghost" size="icon" onClick={onToggleDark} aria-label="테마 전환">
            {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </Button>

          <div className="ml-1 h-5 w-px bg-border" />

          {user ? (
            <UserDropdown user={user} onLogout={onLogout} />
          ) : (
            <div className="flex items-center gap-1">
              <Button variant="ghost" size="sm" onClick={() => onView("login")}>
                <LogIn className="size-4" /> 로그인
              </Button>
              <Button size="sm" onClick={() => onView("register")}>
                <UserPlus className="size-4" /> <span className="hidden sm:inline">회원가입</span>
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
