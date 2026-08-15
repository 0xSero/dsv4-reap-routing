#!/usr/bin/env python3
"""analyze_experts.py — Phase 3: 'experts that light up' analysis.

Reads the observe_religious.py output JSONL (per-sample REAP observation with
per-layer gate_weights / activation_norms / reap_score / expert_frequencies)
and produces:

  * outputs/expert_rankings.csv         — per (text) top experts (several metrics)
  * outputs/expert_rankings_per_book.csv— per (text, book/chapter) top experts
  * outputs/expert_frequency.csv        — long-format per text/layer/expert frequency
  * outputs/text_expert_profiles.parquet— aggregate per text per expert
  * outputs/cross_text_jaccard.csv      — Jaccard overlap matrix (text x text)
  * outputs/per_layer_topk.csv          — per layer top experts (shared vs specialist)
  * outputs/expert_summary.json         — machine-readable summary

Metric definitions (paper REAP saliency per expert j):
  reap_score_j   = (1/|X_j|) sum g_j * ||f_j||_2   (g_j = normalized top-k weight,
                   divide applied weight by route_scale for paper g_j)
  also aggregate activation_norms and gate_affinity.

Usage:
  python3 analyze_experts.py --obs <obs.jsonl> --out outputs
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


LAYERS = 43
EXPERTS = 256
TOP_K = 6


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--obs", required=True, type=Path, help="observe_religious output JSONL")
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--topk-metrics", type=int, default=30, help="experts shown per rank table")
    return p.parse_args()


def load_obs(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


TEXTS = ["bible", "quran", "tao", "gita", "dhamma", "bofm", "analects", "upanishads"]

_BIBLE_BOOKS = frozenset([
    "genesis", "exodus", "leviticus", "numbers", "deuteronomy",
    "joshua", "judges", "ruth", "samuel", "kings", "chronicles",
    "ezra", "nehemiah", "esther", "job", "psalms", "proverbs",
    "ecclesiastes", "song", "isaiah", "jeremiah", "lamentations",
    "ezekiel", "daniel", "hosea", "joel", "amos", "obadiah",
    "jonah", "micah", "nahum", "habakkuk", "zephaniah", "haggai",
    "zechariah", "malachi", "matthew", "mark", "luke", "john",
    "acts", "romans", "corinthians", "galatians", "ephesians",
    "philippians", "colossians", "thessalonians", "timothy", "titus",
    "philemon", "hebrews", "james", "peter", "jude", "revelation",
])
_BOFM_BOOKS = frozenset([
    "1_nephi", "2_nephi", "3_nephi", "4_nephi", "alma", "enos",
    "ether", "helaman", "jacob", "jarom", "mormon", "moroni",
    "mosiah", "omni", "words_of_mormon",
])
_UPANISHADS = frozenset(["isa", "katha", "kena"])


def text_of(category: str) -> str:
    """Map a category string to one of the 8 religious texts."""
    c = category.lower()
    parts = c.split("_")
    # Bible: first part is a book name, OR "N_bookname" pattern (1_chronicles, 2_kings, etc.)
    # Check if any part matches a known Bible book name
    for part in parts:
        if part in _BIBLE_BOOKS:
            return "bible"
    if c.startswith("sura_"):
        return "quran"
    if c.startswith("tao_"):
        return "tao"
    if c.startswith("gita_"):
        return "gita"
    if c in _UPANISHADS:
        return "upanishads"
    if c in _BOFM_BOOKS:
        return "bofm"
    if c.startswith("book_"):
        return "analects"
    if c.startswith("ch_") and "the_" in c:
        return "dhamma"
    # Fallbacks
    if c.startswith("ch_"):
        return "dhamma"  # bare ch_NN (shouldn't happen with prefixed merge)
    return c.split("_")[0]


def main() -> None:
    args = parse_args()
    rows = load_obs(args.obs)
    if not rows:
        raise SystemExit("no observation rows")
    args.out.mkdir(parents=True, exist_ok=True)

    # ---- aggregate per (text, expert) and (text, book, expert) ----
    aggr_text: dict[str, dict] = {}          # text -> per-expert sums
    aggr_book: dict[str, dict] = {}          # (text,book) -> per-expert sums
    per_layer: dict[tuple[str, int], dict] = {}  # (text, layer) -> per-expert sums
    for r in rows:
        cat = r["category"]
        text = text_of(cat)
        layers = r["observation"]["layers"]
        seqlen = r["seqlen"]
        for lname, ldata in layers.items():
            layer = int(lname)
            fre = np.array(ldata["expert_frequencies"], dtype=np.int64)
            reap = np.array(ldata["reap_score"], dtype=np.float64)
            act = np.array(ldata["activation_norms"], dtype=np.float64)
            gate = np.array(ldata["gate_weights"], dtype=np.float64)
            ok = fre > 0
            if not ok.any():
                continue
            # reap already = (sum g*||f||)/count ; weight by frequency for totals
            aggr_text.setdefault(text, {"freq": np.zeros(EXPERTS),
                                        "reap": np.zeros(EXPERTS),
                                        "act": np.zeros(EXPERTS),
                                        "gate": np.zeros(EXPERTS),
                                        "n": 0})
            a = aggr_text[text]
            a["freq"] += fre
            a["reap"] += reap * fre
            a["act"] += act * fre
            a["gate"] += gate
            a["n"] += int(seqlen)
            book = cat
            aggr_book.setdefault((text, book), {"freq": np.zeros(EXPERTS),
                                                "reap": np.zeros(EXPERTS),
                                                "act": np.zeros(EXPERTS),
                                                "gate": np.zeros(EXPERTS),
                                                "n": 0})
            b = aggr_book[(text, book)]
            b["freq"] += fre
            b["reap"] += reap * fre
            b["act"] += act * fre
            b["gate"] += gate
            b["n"] += int(seqlen)
            per_layer.setdefault((text, layer), {"freq": np.zeros(EXPERTS),
                                                 "reap": np.zeros(EXPERTS),
                                                 "act": np.zeros(EXPERTS)})
            pl = per_layer[(text, layer)]
            pl["freq"] += fre
            pl["reap"] += reap * fre
            pl["act"] += act * fre

    def top_by(a: dict, metric: str, n: int) -> list[tuple[int, float]]:
        denom = a["freq"].copy()
        denom[denom <= 0] = 1
        vals = a[metric] / denom if metric in ("reap", "act") else a[metric]
        idx = np.argsort(-vals)
        out = []
        for i in idx:
            if metric in ("reap", "act") and a["freq"][i] <= 0:
                continue
            out.append((int(i), float(vals[i])))
            if len(out) >= n:
                break
        return out

    # ---- text-level rankings ----
    rank_rows = []
    freq_rows = []
    for text, a in aggr_text.items():
        denom = a["freq"].copy(); denom[denom <= 0] = 1
        for metric, label in (("reap", "reap"), ("act", "actnorm"), ("gate", "gate")):
            for e, v in top_by(a, metric, args.topk_metrics):
                rank_rows.append({"text": text, "metric": label, "expert_id": e,
                                  "value": v, "freq": float(a["freq"][e])})
        for e in range(EXPERTS):
            if a["freq"][e] > 0:
                freq_rows.append({"text": text, "expert_id": e, "count": float(a["freq"][e]),
                                  "norm_frac": float(a["freq"][e] / a["freq"].sum())})
    pd.DataFrame(rank_rows).to_csv(args.out / "expert_rankings.csv", index=False)
    pd.DataFrame(freq_rows).to_csv(args.out / "expert_frequency.csv", index=False)

    # ---- per-book rankings ----
    book_rows = []
    for (text, book), a in sorted(aggr_book.items()):
        for metric, label in (("reap", "reap"), ("act", "actnorm"), ("gate", "gate")):
            for e, v in top_by(a, metric, args.topk_metrics):
                book_rows.append({"text": text, "category": book, "metric": label,
                                  "expert_id": e, "value": v, "freq": float(a["freq"][e])})
    pd.DataFrame(book_rows).to_csv(args.out / "expert_rankings_per_book.csv", index=False)

    # ---- text-level profiles (parquet) ----
    prof_rows = []
    for text, a in aggr_text.items():
        denom = a["freq"].copy(); denom[denom <= 0] = 1
        for e in range(EXPERTS):
            prof_rows.append({"text": text, "expert_id": e,
                              "count": float(a["freq"][e]),
                              "norm_frac": float(a["freq"][e] / a["freq"].sum()),
                              "mean_reap": float(a["reap"][e] / denom[e]),
                              "mean_actnorm": float(a["act"][e] / denom[e]),
                              "mean_gate": float(a["gate"][e] / a["n"])})
    pd.DataFrame(prof_rows).to_parquet(args.out / "text_expert_profiles.parquet", index=False)

    # ---- per-layer top-k ----
    layer_rows = []
    for (text, layer), pl in sorted(per_layer.items()):
        denom = pl["freq"].copy(); denom[denom <= 0] = 1
        tops = top_by(pl, "reap", 10)
        top_ids = [str(e) for e, _ in tops]
        layer_rows.append({"text": text, "layer": layer, "top10_reap": ";".join(top_ids),
                           "n_routed": int(pl["freq"][pl["freq"] > 0].sum())})
    pd.DataFrame(layer_rows).to_csv(args.out / "per_layer_topk.csv", index=False)

    # ---- cross-text Jaccard (top experts by reap share) ----
    texts = sorted(aggr_text)
    def top_set(text: str, k: int = 20) -> set[int]:
        a = aggr_text[text]
        return {e for e, _ in top_by(a, "reap", k)}
    sets = {t: top_set(t, 20) for t in texts}
    jac_rows = []
    for t1 in texts:
        for t2 in texts:
            inter = len(sets[t1] & sets[t2])
            union = len(sets[t1] | sets[t2]) or 1
            jac_rows.append({"text_a": t1, "text_b": t2, "intersection": inter,
                             "union": union, "jaccard": inter / union,
                             "size_a": len(sets[t1]), "size_b": len(sets[t2])})
    pd.DataFrame(jac_rows).to_csv(args.out / "cross_text_jaccard.csv", index=False)

    summary = {
        "n_samples": len(rows),
        "n_texts": len(texts),
        "texts": texts,
        "layers": LAYERS,
        "experts": EXPERTS,
        "topk": TOP_K,
        "files": [
            "expert_rankings.csv", "expert_rankings_per_book.csv",
            "expert_frequency.csv", "text_expert_profiles.parquet",
            "per_layer_topk.csv", "cross_text_jaccard.csv",
        ],
    }
    (args.out / "expert_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print("wrote", len(rank_rows), "rank rows,", len(book_rows), "book rows")


if __name__ == "__main__":
    main()
