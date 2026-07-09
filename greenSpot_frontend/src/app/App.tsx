import { useEffect, useState, useCallback } from "react";
import { MapPin } from "lucide-react";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";
import { Header } from "./components/greenspot/Header";
import { StatsBar } from "./components/greenspot/StatsBar";
import { AgentPanel } from "./components/greenspot/AgentPanel";
import { ParcelList } from "./components/greenspot/ParcelList";
import { DetailPanel } from "./components/greenspot/DetailPanel";
import { CompareDialog } from "./components/greenspot/CompareDialog";
import { BookmarkSheet } from "./components/greenspot/BookmarkSheet";
import { StatsView, type HistoryEntry } from "./components/greenspot/StatsView";
import { LoginPage, RegisterPage } from "./components/greenspot/AuthPages";
import {
  getMe,
  logout as apiLogout,
  getBookmarks,
  addBookmark,
  removeBookmark,
  loadSession,
  saveSession,
  getHistory,
  updatePreferences,
} from "./lib/api";
import { setLiveParcels, useParcels, useParcelsLoading, ensureParcel, findParcel } from "./lib/parcelStore";
import { getParcel, topScore, type Parcel } from "./data/greenspot";
import type { AgentResult, AuthUser, UserBookmark } from "./lib/types";

type View = "dashboard" | "stats" | "login" | "register";

function enrichBookmarks(raw: UserBookmark[]): UserBookmark[] {
  return raw.map((b) => {
    const p = getParcel(b.parcelId);
    if (!p) return b;
    const top = p.scores.topRecommendation;
    const topRec = top === "SUMOK" ? "TREE" : top === "GARDEN" ? "GARDEN" : "SOLAR";
    return {
      ...b,
      parcelName: p.name,
      district: p.district,
      topRecommendation: topRec as UserBookmark["topRecommendation"],
      topScore: topScore(p),
    };
  });
}

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [dark, setDark] = useState(() => {
    try {
      return localStorage.getItem("gs.theme") === "dark";
    } catch {
      return false;
    }
  });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [compareOpen, setCompareOpen] = useState(false);
  const [bookmarksOpen, setBookmarksOpen] = useState(false);
  const [exportItems, setExportItems] = useState<Parcel[]>([]);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  const parcels = useParcels();
  const parcelsLoading = useParcelsLoading();

  const [user, setUser] = useState<AuthUser | null>(null);
  const [userBookmarks, setUserBookmarks] = useState<UserBookmark[]>([]);

  useEffect(() => {
    if (parcels.length === 0) return;
    setExportItems(parcels);

    if (!selectedId) {
      const best = [...parcels].sort((a, b) => topScore(b) - topScore(a))[0];
      if (best) setSelectedId(best.id);
    }
  }, [parcels]);

  // 딥링크 · 북마크 · 비교용: 목록에 없어도 API hydrate
  useEffect(() => {
    const param = new URLSearchParams(location.search).get("parcel");
    if (param && !selectedId) {
      setSelectedId(param);
    }
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    if (findParcel(selectedId) || getParcel(selectedId)) return;
    let cancelled = false;
    (async () => {
      const p = await ensureParcel(selectedId);
      if (!cancelled && !p) {
        toast.error("부지를 불러오지 못했습니다", { description: selectedId });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  useEffect(() => {
    (async () => {
      const cached = loadSession();
      const me = await getMe();
      if (me) {
        setUser(me);
        saveSession(me);
        try {
          const bookmarks = await getBookmarks();
          setUserBookmarks(enrichBookmarks(bookmarks));
        } catch {
          setUserBookmarks([]);
        }
      } else if (cached) {
        setUser(null);
      }
    })();
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const data = await getHistory(30);
        setHistory(
          data.history.map((h) => ({
            query: h.query,
            source: h.source,
            resultCount: h.resultCount,
            at: h.createdAt,
          })),
        );
      } catch {
        setHistory([]);
      }
    })();
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    const url = new URL(location.href);
    url.searchParams.set("parcel", selectedId);
    window.history.replaceState({}, "", url.toString());
  }, [selectedId]);

  // 초기 테마 클래스 적용
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  function toggleDark() {
    setDark((d) => {
      const next = !d;
      document.documentElement.classList.toggle("dark", next);
      try {
        localStorage.setItem("gs.theme", next ? "dark" : "light");
      } catch {
        /* ignore */
      }
      // F-15: 회원은 서버 환경설정에도 저장
      if (user) {
        void updatePreferences(next ? "dark" : "light").catch(() => {
          /* 로컬 저장은 이미 반영 */
        });
      }
      return next;
    });
  }

  function select(id: string) {
    setSelectedId(id);
    setView("dashboard");
    setBookmarksOpen(false);
    setCompareOpen(false);
    // 목록 밖(북마크 VW-*) 이면 백그라운드 hydrate
    if (!findParcel(id) && !getParcel(id)) {
      void ensureParcel(id);
    }
  }

  function toggleCompare(id: string) {
    setCompareIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length >= 3 ? prev : [...prev, id],
    );
  }

  const toggleBookmark = useCallback(
    async (p: Parcel) => {
      if (!user) {
        toast("로그인이 필요합니다", {
          description: "북마크는 로그인한 사용자만 이용할 수 있습니다.",
          action: { label: "로그인", onClick: () => setView("login") },
        });
        return;
      }
      const exists = userBookmarks.some((b) => b.parcelId === p.id);
      try {
        if (exists) {
          await removeBookmark(p.id);
          setUserBookmarks((prev) => prev.filter((b) => b.parcelId !== p.id));
        } else {
          const top = p.scores.topRecommendation;
          const topRec = top === "SUMOK" ? "TREE" : top === "GARDEN" ? "GARDEN" : "SOLAR";
          const score = topScore(p);
          // 라이브 VW- 필지는 DB에 없으므로 메타를 함께 전송
          await addBookmark(p.id, {
            parcelName: p.name,
            district: p.district,
            topRecommendation: topRec,
            topScore: score,
          });
          const next: UserBookmark = {
            parcelId: p.id,
            parcelName: p.name,
            district: p.district,
            topRecommendation: topRec as UserBookmark["topRecommendation"],
            topScore: score,
            createdAt: new Date().toISOString(),
          };
          setUserBookmarks((prev) => [next, ...prev]);
        }
      } catch {
        toast.error("북마크 처리에 실패했습니다.");
      }
    },
    [user, userBookmarks],
  );

  async function clearBookmarks() {
    if (!user) return;
    try {
      await Promise.all(userBookmarks.map((b) => removeBookmark(b.parcelId)));
      setUserBookmarks([]);
    } catch {
      toast.error("북마크 삭제에 실패했습니다.");
    }
  }

  async function removeBookmarkItem(parcelId: string) {
    if (!user) return;
    try {
      await removeBookmark(parcelId);
      setUserBookmarks((prev) => prev.filter((b) => b.parcelId !== parcelId));
    } catch {
      toast.error("북마크 삭제에 실패했습니다.");
    }
  }

  function isBookmarked(id: string) {
    return userBookmarks.some((b) => b.parcelId === id);
  }

  async function onAuthSuccess(u: AuthUser) {
    setUser(u);
    saveSession(u);
    try {
      const bookmarks = await getBookmarks();
      setUserBookmarks(enrichBookmarks(bookmarks));
    } catch {
      setUserBookmarks([]);
    }
    toast.success(`안녕하세요, ${u.name}님!`, { description: "북마크가 서버에 저장됩니다." });
    setView("dashboard");
  }

  async function logout() {
    await apiLogout();
    setUser(null);
    setUserBookmarks([]);
    toast("로그아웃되었습니다");
  }

  function onQueryLogged(r: AgentResult) {
    if (r.parcels?.length) {
      setLiveParcels(r.parcels);
      const first = r.parcels[0] as { id?: string };
      if (first?.id) setSelectedId(first.id);
    }
    setHistory((prev) => [
      { query: r.query, source: r.source, resultCount: r.count, at: new Date().toISOString() },
      ...prev,
    ].slice(0, 30));
  }

  const selected = selectedId ? (findParcel(selectedId) ?? getParcel(selectedId)) : undefined;

  if (view === "login") {
    return (
      <>
        <LoginPage
          onSuccess={onAuthSuccess}
          onGoRegister={() => setView("register")}
          onGuest={() => setView("dashboard")}
        />
        <Toaster position="bottom-right" />
      </>
    );
  }
  if (view === "register") {
    return (
      <>
        <RegisterPage
          onSuccess={onAuthSuccess}
          onGoLogin={() => setView("login")}
          onGuest={() => setView("dashboard")}
        />
        <Toaster position="bottom-right" />
      </>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-background text-foreground">
      <Header
        view={view}
        onView={setView}
        dark={dark}
        onToggleDark={toggleDark}
        bookmarkCount={userBookmarks.length}
        onOpenBookmarks={() => setBookmarksOpen(true)}
        user={user}
        onLogout={logout}
        exportItems={exportItems}
      />

      <main className="min-h-0 flex-1 overflow-y-auto">
        {view === "stats" ? (
          <StatsView history={history} />
        ) : (
          <div className="mx-auto max-w-[1600px] space-y-4 px-4 py-4 sm:px-6">
            <StatsBar />
            <AgentPanel onSelectParcel={select} onQueryLogged={onQueryLogged} />

            <div className="grid gap-4 lg:grid-cols-[minmax(340px,420px)_1fr]">
              <div className="flex h-[560px] min-h-[480px] flex-col overflow-hidden rounded-lg border border-border bg-card lg:h-[calc(100vh-268px)]">
                <div className="border-b border-border px-4 py-3">
                  <h2 className="text-[15px]">부지 목록</h2>
                </div>
                <ParcelList
                  selectedId={selectedId}
                  onSelect={setSelectedId}
                  isBookmarked={isBookmarked}
                  onToggleBookmark={toggleBookmark}
                  compareIds={compareIds}
                  onToggleCompare={toggleCompare}
                  onOpenCompare={() => setCompareOpen(true)}
                  onFilteredChange={setExportItems}
                />
              </div>

              <div className="min-h-[480px] overflow-hidden rounded-lg border border-border bg-card lg:h-[calc(100vh-268px)]">
                {parcelsLoading ? (
                  <div className="flex h-full flex-col items-center justify-center gap-2 text-muted-foreground">
                    <p className="text-sm">부지 데이터를 불러오는 중…</p>
                  </div>
                ) : selected ? (
                  <DetailPanel
                    parcel={selected}
                    bookmarked={isBookmarked(selected.id)}
                    onToggleBookmark={() => toggleBookmark(selected)}
                  />
                ) : (
                  <div className="flex h-full flex-col items-center justify-center gap-2 text-muted-foreground">
                    <MapPin className="size-8 opacity-30" />
                    <p className="text-sm">부지를 선택하세요</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      <CompareDialog
        ids={compareIds}
        open={compareOpen}
        onOpenChange={setCompareOpen}
        onRemove={(id) => toggleCompare(id)}
        onSelect={select}
      />
      <BookmarkSheet
        open={bookmarksOpen}
        onOpenChange={setBookmarksOpen}
        bookmarks={userBookmarks}
        onSelect={select}
        onClear={clearBookmarks}
        onRemove={removeBookmarkItem}
        user={user}
        onGoLogin={() => { setBookmarksOpen(false); setView("login"); }}
      />
      <Toaster position="bottom-right" />
    </div>
  );
}