import { useState } from "react";
import { Sparkles, Send, Loader2, ArrowRight, ShieldCheck, Crown } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { SUGGESTED_QUERIES, FEASIBILITY_LABEL, type UseKey } from "../../data/greenspot";
import { agentSearch, ApiError } from "../../lib/api";
import type { AgentResult } from "../../lib/types";
import { USE_META, mono } from "../../lib/greenspot-ui";

function toUiUseKey(rec: string): UseKey {
  if (rec === "TREE") return "SUMOK";
  return rec as UseKey;
}

export function AgentPanel({
  onSelectParcel,
  onQueryLogged,
}: {
  onSelectParcel: (id: string) => void;
  onQueryLogged: (r: AgentResult) => void;
}) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AgentResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(q: string) {
    const text = q.trim();
    if (!text || loading) return;
    setQuery(text);
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const res = await agentSearch(text);
      setResult(res);
      onQueryLogged(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "검색에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="overflow-hidden rounded-lg border border-border bg-card">
      <div className="flex items-center gap-2 border-b border-border bg-gradient-to-r from-accent/60 to-transparent px-4 py-3">
        <span className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <Sparkles className="size-4" strokeWidth={2.4} />
        </span>
        <h2 className="text-[15px]">AI 부지 검색 에이전트</h2>
        <span className="rounded bg-primary/10 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-primary">BETA</span>
        <span className="ml-auto hidden items-center gap-1 text-[11px] text-muted-foreground sm:flex">
          <ShieldCheck className="size-3.5" /> 3단계 할루시네이션 방어
        </span>
      </div>

      <div className="p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit(query);
          }}
          className="flex gap-2"
        >
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="예) 해운대구, 용산구, 성남시 — VWorld 실시간 검색"
            className="h-10 bg-input-background"
          />
          <Button type="submit" disabled={loading || !query.trim()} className="h-10 px-4">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            <span className="hidden sm:inline">검색</span>
          </Button>
        </form>

        <div className="mt-3 flex flex-wrap gap-1.5">
          {SUGGESTED_QUERIES.map((s) => (
            <button
              key={s}
              onClick={() => submit(s)}
              disabled={loading}
              className="rounded-full border border-border bg-muted/60 px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:bg-accent hover:text-accent-foreground disabled:opacity-50"
            >
              {s}
            </button>
          ))}
        </div>

        {loading && (
          <div className="mt-4 flex items-center gap-2 rounded-md border border-dashed border-border px-4 py-3 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            <span>VWorld에서 실시간으로 부지를 조회하는 중…</span>
          </div>
        )}

        {error && !loading && (
          <p className="mt-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-[12px] text-destructive">
            {error}
          </p>
        )}

        {result && !loading && (
          <div className="mt-4 space-y-3">
            <div className="rounded-md border border-border bg-muted/40 p-3.5">
              <div className="mb-2 flex items-center gap-2">
                <span
                  className={`rounded px-1.5 py-0.5 font-mono text-[10px] font-semibold ${
                    result.source === "ai" ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                  }`}
                >
                  {result.source === "ai" ? "AI" : "FALLBACK"}
                </span>
                <span className="text-[11px] text-muted-foreground">
                  결과 {result.count}건 · <span className={mono()}>{result.elapsed_ms}ms</span>
                </span>
              </div>
              <p className="text-[13px] leading-relaxed text-foreground">{result.summary}</p>
              <div className="mt-2.5 border-t border-border pt-2 text-[11px] text-muted-foreground">
                <span className="text-foreground/70">검색 조건</span> · {result.criteria.explanation}
              </div>
              {result.criteria?.topRecommendation && (
                <p className="mt-1.5 text-[11px] leading-snug text-muted-foreground">
                  목록은 검색 용도 점수로 정렬됩니다. 카드 배지의 「1순위 추천」은 부지 종합 1위 용도라 검색 용도와 다를 수 있습니다.
                </p>
              )}
            </div>

            {result.results.length > 0 && (
              <div className="grid gap-1.5">
                {result.results.map((r, i) => {
                  const pref = (result.criteria?.topRecommendation as string | undefined) || null;
                  // 선호 용도로 정렬했을 때 배지/점수도 그 용도 기준
                  const displayUse = toUiUseKey(pref || r.topRecommendation);
                  const m = USE_META[displayUse] ?? USE_META.SUMOK;
                  return (
                    <button
                      key={r.id}
                      onClick={() => onSelectParcel(r.id)}
                      className="group flex items-center gap-3 rounded-md border border-border bg-card px-3 py-2 text-left transition-colors hover:border-primary/40 hover:bg-accent/40"
                    >
                      <span className={mono("w-5 text-center text-xs text-muted-foreground")}>
                        {i === 0 ? <Crown className="size-4 text-solar" /> : i + 1}
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="truncate text-[13px] font-medium text-foreground">{r.name}</span>
                          <span className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] ${m.bg} ${m.text}`}>
                            <m.Icon className="size-3" /> {m.label}{pref ? " 점수" : ""}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                          {r.district} · {Number(r.areaSqm || 0).toLocaleString()}㎡
                          {r.feasibilityStatus && r.feasibilityStatus !== "AVAILABLE" && (
                            <span className={`rounded px-1 py-0.5 text-[10px] ${r.feasibilityStatus === "CONDITIONAL" ? "bg-garden-soft text-garden" : "bg-destructive/10 text-destructive"}`}>
                              {FEASIBILITY_LABEL[r.feasibilityStatus]}
                            </span>
                          )}
                        </div>
                      </div>
                      <span className={mono("text-[15px] font-semibold")} style={{ color: m.hex }}>
                        {r.topScore}
                      </span>
                      <ArrowRight className="size-3.5 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
