# -*- coding: utf-8 -*-
"""
VWorld 연속지적도(LP_PA_CBND_BUBUN)로 서울 전역 GreenSpot 후보 부지를 수집한다.

사용법:
  cd greenSpot_backend
  python -m scripts.fetch_vworld_seoul_parcels
  python -m scripts.fetch_vworld_seoul_parcels --min-area 400 --per-emd 3
  python -m scripts.seed --from-vworld
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.vworld_discovery_service import discover_seoul_parcels

DATA_PATH = Path(__file__).parent / "seed_data.json"
META_PATH = Path(__file__).parent / "seed_meta.json"


def _progress(done: int, total: int, count: int):
    if done % 20 == 0 or done == total:
        print(f"  읍면동 {done}/{total} 처리 · 누적 부지 {count}건", flush=True)


def _strip_internal(row: dict) -> dict:
    return {k: v for k, v in row.items() if k not in ("pnu", "vworld_addr", "data_source")}


async def main(args: argparse.Namespace) -> int:
    print("VWorld 연속지적도 수집 시작…")
    print(f"  min_area={args.min_area}㎡ · per_emd={args.per_emd} · regulations={not args.no_regs}")

    rows = await discover_seoul_parcels(
        min_area_sqm=args.min_area,
        max_area_sqm=args.max_area,
        per_emd=args.per_emd,
        max_pages_per_emd=args.max_pages,
        enrich_regulations=not args.no_regs,
        regulation_concurrency=args.reg_concurrency,
        progress_cb=_progress,
    )

    if not rows:
        print("수집된 부지가 없습니다. VWORLD_API_KEY와 domain 설정을 확인하세요.")
        return 1

    export_rows = [_strip_internal(r) for r in rows]
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(export_rows, f, ensure_ascii=False, indent=2)

    by_district = Counter(r["district"] for r in export_rows)
    meta = {
        "source": "VWorld/LP_PA_CBND_BUBUN",
        "total": len(export_rows),
        "districts": len(by_district),
        "per_district": dict(sorted(by_district.items())),
        "min_area_sqm": args.min_area,
        "per_emd": args.per_emd,
    }
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n완료: {len(export_rows)}건 · {len(by_district)}/25 자치구")
    print(f"저장: {DATA_PATH}")
    for d, c in sorted(by_district.items()):
        print(f"  {d}: {c}건")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VWorld 서울 연속지적도 부지 수집")
    parser.add_argument("--min-area", type=float, default=350, help="최소 면적(㎡)")
    parser.add_argument("--max-area", type=float, default=15000, help="최대 면적(㎡)")
    parser.add_argument("--per-emd", type=int, default=2, help="읍면동당 최대 부지 수")
    parser.add_argument("--max-pages", type=int, default=2, help="읍면동당 조회 페이지 수")
    parser.add_argument("--no-regs", action="store_true", help="규제 조회 생략(빠른 수집)")
    parser.add_argument("--reg-concurrency", type=int, default=4, help="규제 조회 동시성")
    raise SystemExit(asyncio.run(main(parser.parse_args())))