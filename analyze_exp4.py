#!/usr/bin/env python3
"""
Exp 4 Pilot Analysis: Window-level H6 firing in quotation-switch windows.

Compares H6 expert firing rates in:
  - Exp 4 windows (Christian commentary + embedded KJV verse quotes)
  - Pure Bible verse windows (core 8-tradition data)
  - Pure Christian commentary windows (christian_all_obs.jsonl)

The within-window quote-span vs commentary-span comparison requires per-token
routing capture (--raw-budget-tokens > 0), which was not enabled in this run.
This is the window-level pilot — Exp 4b will do the per-token analysis.
"""
import json
import numpy as np
from collections import defaultdict
from pathlib import Path

# ── H6 anchor experts (frozen registry) ──
H6_ANCHORS = {
    "H6-A1": (21, 42),
    "H6-A2": (22, 105),
    "H6-A3": (23, 113),
    "H6-A4": (30, 198),
    "H6-A5": (32, 254),
    "H6-A6": (41, 147),
}

# All 13+ H6 cluster cells (from robustness checks)
H6_FULL_CLUSTER = [
    (4, 89), (7, 204), (12, 71), (18, 190),
    (21, 42), (22, 105), (23, 113),
    (30, 198), (32, 254),
    (37, 91), (39, 173), (40, 56), (41, 147),
]

BASE = Path("/Users/sero/research/deepseek-v4-flash-0731")

def load_records(path):
    """Load observation records from JSONL."""
    records = []
    with open(path) as f:
        for line in f:
            records.append(json.loads(line))
    return records

def get_freq(record, layer, expert):
    """Get expert frequency for a specific layer/expert from a record."""
    layers = record["observation"]["layers"]
    key = str(layer)
    if key not in layers:
        return 0
    return layers[key]["expert_frequencies"][expert]

def get_rate_per_million(record, layer, expert):
    """Get expert firing rate per million tokens."""
    freq = get_freq(record, layer, expert)
    seqlen = record["seqlen"]
    if seqlen == 0:
        return 0
    return freq / seqlen * 1_000_000

def compute_h6_composite(record, anchors=H6_ANCHORS):
    """Compute the mean H6 anchor firing rate (per million tokens)."""
    rates = []
    for name, (layer, expert) in anchors.items():
        rates.append(get_rate_per_million(record, layer, expert))
    return np.mean(rates), rates

def analyze_corpus(records, label):
    """Analyze H6 firing across a set of records."""
    composites = []
    anchor_rates = defaultdict(list)
    for rec in records:
        comp, rates = compute_h6_composite(rec)
        composites.append(comp)
        for i, (name, _) in enumerate(H6_ANCHORS.items()):
            anchor_rates[name].append(rates[i])

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  n={len(records)}, tokens={sum(r['seqlen'] for r in records):,}")
    print(f"{'='*60}")
    print(f"  H6 composite: mean={np.mean(composites):,.1f}/M  "
          f"median={np.median(composites):,.1f}/M  "
          f"std={np.std(composites):,.1f}/M")
    print(f"  Per-anchor rates (mean /M):")
    for name, (layer, expert) in H6_ANCHORS.items():
        r = anchor_rates[name]
        print(f"    {name} (L{layer}e{expert}): {np.mean(r):,.1f}/M  "
              f"[{np.min(r):,.1f} - {np.max(r):,.1f}]")
    return composites, anchor_rates

def main():
    # ── Load data ──
    print("Loading data...")
    exp4_recs = load_records(BASE / "exp4_obs.jsonl")
    print(f"  Exp 4: {len(exp4_recs)} records")

    # Bible (KJV) from core data — filter by source field
    core_recs = load_records(BASE / "full_obs.jsonl")
    bible_recs = [r for r in core_recs if r.get("source") == "bible"]
    print(f"  Bible (KJV): {len(bible_recs)} records")

    # Christian commentary
    christian_recs = load_records(BASE / "christian_all_obs.jsonl")
    print(f"  Christian commentary: {len(christian_recs)} records")

    # Verse traditions: bible, bofm, tao, gita, dhamma, analects
    verse_sources = {"bible", "bofm", "tao", "gita", "dhamma", "analects"}
    verse_recs = [r for r in core_recs if r.get("source") in verse_sources]
    print(f"  All verse (6 traditions): {len(verse_recs)} records")

    # Prose traditions: upanishads, quran
    prose_sources = {"upanishads", "quran"}
    prose_recs = [r for r in core_recs if r.get("source") in prose_sources]
    print(f"  Core prose (Upanishads+Qur'an): {len(prose_recs)} records")

    # ── Analyze each group ──
    exp4_comp, exp4_anchors = analyze_corpus(exp4_recs, "Exp 4: Commentary + Embedded KJV Quotes")
    bible_comp, bible_anchors = analyze_corpus(bible_recs, "Bible (KJV) — Pure Verse")
    christian_comp, christian_anchors = analyze_corpus(christian_recs, "Christian Commentary — Pure Prose")
    verse_comp, verse_anchors = analyze_corpus(verse_recs, "All Verse Traditions")
    prose_comp, prose_anchors = analyze_corpus(prose_recs, "Core Prose (Upanishads + Qur'an)")

    # ── Key comparison: Exp 4 vs Bible vs Christian commentary ──
    print(f"\n{'='*60}")
    print("  KEY COMPARISON: H6 Composite Rates")
    print(f"{'='*60}")
    print(f"  Pure Bible verse:      {np.mean(bible_comp):>12,.1f}/M")
    print(f"  Exp 4 (comm + quotes):  {np.mean(exp4_comp):>12,.1f}/M")
    print(f"  Christian commentary:   {np.mean(christian_comp):>12,.1f}/M")
    print(f"  All verse:              {np.mean(verse_comp):>12,.1f}/M")
    print(f"  Core prose:             {np.mean(prose_comp):>12,.1f}/M")

    # Ratios
    print(f"\n  Ratios:")
    if np.mean(bible_comp) > 0:
        print(f"    Exp4 / Bible:         {np.mean(exp4_comp)/max(np.mean(bible_comp),0.001):>12,.1f}x")
    if np.mean(christian_comp) > 0:
        print(f"    Exp4 / Christian comm: {np.mean(exp4_comp)/max(np.mean(christian_comp),0.001):>12,.1f}x")
    if np.mean(bible_comp) > 0 and np.mean(christian_comp) > 0:
        print(f"    Christian/Bible:       {np.mean(christian_comp)/max(np.mean(bible_comp),0.001):>12,.1f}x")

    # ── Per-anchor comparison table ──
    print(f"\n{'='*60}")
    print("  PER-ANCHOR: Exp4 vs Bible vs Commentary")
    print(f"{'='*60}")
    print(f"  {'Anchor':<12} {'Bible':>10} {'Exp4':>10} {'Christian':>10} {'Exp4/Bible':>10} {'Exp4/Chr':>10}")
    for name, (layer, expert) in H6_ANCHORS.items():
        b = np.mean(bible_anchors[name])
        e = np.mean(exp4_anchors[name])
        c = np.mean(christian_anchors[name])
        r_b = e / max(b, 0.001)
        r_c = e / max(c, 0.001)
        print(f"  {name} (L{layer}e{expert})  {b:>10,.1f} {e:>10,.1f} {c:>10,.1f} {r_b:>10.1f}x {r_c:>10.1f}x")

    # ── Full H6 cluster analysis ──
    print(f"\n{'='*60}")
    print("  FULL H6 CLUSTER (13 cells)")
    print(f"{'='*60}")
    for label, recs in [("Bible", bible_recs), ("Exp4", exp4_recs), ("Christian", christian_recs)]:
        rates_all = []
        for rec in recs:
            rates = []
            for layer, expert in H6_FULL_CLUSTER:
                rates.append(get_rate_per_million(rec, layer, expert))
            rates_all.append(np.mean(rates))
        print(f"  {label:>12}: mean={np.mean(rates_all):>10,.1f}/M  "
              f"median={np.median(rates_all):>10,.1f}/M")

    # ── Per-record Exp 4 breakdown ──
    print(f"\n{'='*60}")
    print("  PER-RECORD Exp 4 H6 Composite")
    print(f"{'='*60}")
    # Load the corpus to get quote span info
    corpus_path = BASE / "corpus/samples/exp4_quotation_switch.jsonl"
    corpus_meta = {}
    if corpus_path.exists():
        with open(corpus_path) as f:
            for line in f:
                s = json.loads(line)
                idx = s["sample_index"]
                qt = sum(span["end_tok"] - span["start_tok"] for span in s.get("quote_spans", []))
                corpus_meta[idx] = {
                    "quote_tokens": qt,
                    "total_tokens": s["seqlen"],
                    "quote_fraction": qt / s["seqlen"] if s["seqlen"] > 0 else 0,
                    "n_quotes": len(s.get("quote_spans", [])),
                    "digit_density": s.get("digit_density", 0),
                }

    print(f"  {'idx':>3} {'seqlen':>6} {'quotes':>6} {'qtok':>5} {'qfrac':>6} {'digits':>6} {'H6/M':>10}")
    for rec in sorted(exp4_recs, key=lambda r: r["sample_index"]):
        idx = rec["sample_index"]
        comp, _ = compute_h6_composite(rec)
        meta = corpus_meta.get(idx, {})
        print(f"  {idx:>3} {rec['seqlen']:>6} {meta.get('n_quotes',0):>6} "
              f"{meta.get('quote_tokens',0):>5} {meta.get('quote_fraction',0):>6.4f} "
              f"{meta.get('digit_density',0):>6.4f} {comp:>10,.1f}")

    # ── Correlation: quote fraction vs H6 composite ──
    if corpus_meta:
        qfracs = []
        h6vals = []
        for rec in exp4_recs:
            idx = rec["sample_index"]
            if idx in corpus_meta:
                qfracs.append(corpus_meta[idx]["quote_fraction"])
                comp, _ = compute_h6_composite(rec)
                h6vals.append(comp)
        if len(qfracs) > 2:
            r = np.corrcoef(qfracs, h6vals)[0, 1]
            print(f"\n  Correlation(quote_fraction, H6_composite): r={r:.3f}")
            print(f"  (Negative r = more quotes → less H6 firing = verse suppresses H6)")

    # ── Save summary ──
    summary = {
        "exp4_n": len(exp4_recs),
        "exp4_tokens": sum(r["seqlen"] for r in exp4_recs),
        "exp4_h6_composite_mean": float(np.mean(exp4_comp)),
        "exp4_h6_composite_median": float(np.median(exp4_comp)),
        "bible_h6_composite_mean": float(np.mean(bible_comp)),
        "christian_h6_composite_mean": float(np.mean(christian_comp)),
        "verse_h6_composite_mean": float(np.mean(verse_comp)),
        "prose_h6_composite_mean": float(np.mean(prose_comp)),
        "exp4_to_bible_ratio": float(np.mean(exp4_comp) / max(np.mean(bible_comp), 0.001)),
        "exp4_to_christian_ratio": float(np.mean(exp4_comp) / max(np.mean(christian_comp), 0.001)),
        "note": "Window-level pilot. Per-token quote vs commentary comparison requires Exp 4b with --raw-budget-tokens > 0.",
    }
    with open(BASE / "analysis/exp4_pilot_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Summary saved to analysis/exp4_pilot_summary.json")

if __name__ == "__main__":
    main()
