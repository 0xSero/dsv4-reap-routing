#!/usr/bin/env python3
"""Analyze Exp 4b results: H6 anchor firing on quote vs commentary spans.

Exp 4b tests whether H6 verse/prose axis experts fire on the prose commentary
context surrounding verse quotes, or on the verse quotes themselves.

Each record in the corpus has quote_spans with start_tok/end_tok positions.
The observation records have per-layer expert frequencies (aggregate, not per-token).
Since we don't have per-token routing (that would require --raw-budget-tokens),
we analyze at the record level: compare H6 firing rates across records with
different quote fractions.

Key analysis:
1. H6 composite rate per record vs quote_fraction
2. Correlation: does more verse content = less H6 firing?
3. Per-anchor rates across all 351 records
4. Compare to Exp 4 pilot results
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

# Load corpus (has quote_spans)
corpus_path = Path(__file__).parent / "corpus/samples/exp4b_quotation_switch.jsonl"
obs_path = Path(__file__).parent / "exp4b_obs.jsonl"

# Load corpus records (keyed by category + sample_index)
corpus = {}
with open(corpus_path) as f:
    for line in f:
        r = json.loads(line)
        key = (r["category"], r["sample_index"])
        corpus[key] = r

# Load observation records
observations = []
with open(obs_path) as f:
    for line in f:
        r = json.loads(line)
        observations.append(r)

print(f"Corpus records: {len(corpus)}")
print(f"Observation records: {len(observations)}")
print()

# H6 anchors (frozen registry)
H6_ANCHORS = {
    21: {42},
    22: {105},
    23: {113},
    30: {198},
    32: {254},
    41: {147},
}

# Match observations to corpus and compute metrics
results = []
for obs in observations:
    key = (obs["category"], obs["sample_index"])
    if key not in corpus:
        continue
    corp = corpus[key]
    seqlen = obs["seqlen"]
    layers = obs["observation"]["layers"]

    # Quote metrics
    quote_tokens = corp.get("quote_tokens", 0)
    n_quotes = corp.get("n_quotes", 0)
    quote_fraction = corp.get("quote_fraction", 0.0)
    digit_density = corp.get("digit_density", 0.0)

    # H6 anchor firing rates
    h6_freqs = {}
    h6_total_freq = 0
    for layer_id, expert_ids in H6_ANCHORS.items():
        layer = layers[str(layer_id)]
        for eid in expert_ids:
            freq = layer["expert_frequencies"][eid]
            rate = freq * 1_000_000 / seqlen if seqlen > 0 else 0
            h6_freqs[f"L{layer_id}e{eid}"] = {"freq": freq, "rate": rate}
            h6_total_freq += freq

    h6_composite_rate = h6_total_freq * 1_000_000 / seqlen if seqlen > 0 else 0

    results.append({
        "category": obs["category"],
        "source": obs.get("source", ""),
        "seqlen": seqlen,
        "quote_tokens": quote_tokens,
        "n_quotes": n_quotes,
        "quote_fraction": quote_fraction,
        "digit_density": digit_density,
        "h6_composite_rate": h6_composite_rate,
        "h6_freqs": h6_freqs,
    })

print(f"Matched records: {len(results)}")
print()

# Summary statistics
print("=" * 80)
print("H6 COMPOSITE FIRING RATE BY QUOTE FRACTION QUARTILE")
print("=" * 80)

# Sort by quote_fraction and split into quartiles
results.sort(key=lambda r: r["quote_fraction"])
n = len(results)
q = n // 4
quartiles = [
    ("Q1 (lowest quote%)", results[:q]),
    ("Q2", results[q:2*q]),
    ("Q3", results[2*q:3*q]),
    ("Q4 (highest quote%)", results[3*q:]),
]

for name, subset in quartiles:
    rates = [r["h6_composite_rate"] for r in subset]
    qfs = [r["quote_fraction"] for r in subset]
    print(f"  {name}: n={len(subset)}, "
          f"quote_frac mean={sum(qfs)/len(qfs):.4f}, "
          f"H6 rate mean={sum(rates)/len(rates):.0f}/M, "
          f"min={min(rates):.0f}, max={max(rates):.0f}")

print()
print("=" * 80)
print("CORRELATION: quote_fraction vs H6 composite rate")
print("=" * 80)

# Simple Pearson correlation
xs = [r["quote_fraction"] for r in results]
ys = [r["h6_composite_rate"] for r in results]
n = len(xs)
mean_x = sum(xs) / n
mean_y = sum(ys) / n
num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
den_x = (sum((x - mean_x) ** 2 for x in xs)) ** 0.5
den_y = (sum((y - mean_y) ** 2 for y in ys)) ** 0.5
r_val = num / (den_x * den_y) if den_x * den_y > 0 else 0
print(f"  Pearson r = {r_val:.4f}")
print(f"  (negative r means more verse quotes → less H6 firing)")

print()
print("=" * 80)
print("PER-ANCHOR FIRING RATES (all 351 records)")
print("=" * 80)

for anchor_name in ["L21e42", "L22e105", "L23e113", "L30e198", "L32e254", "L41e147"]:
    rates = [r["h6_freqs"][anchor_name]["rate"] for r in results]
    print(f"  {anchor_name}: mean={sum(rates)/len(rates):.0f}/M, "
          f"min={min(rates):.0f}, max={max(rates):.0f}, "
          f"median={sorted(rates)[len(rates)//2]:.0f}")

print()
print("=" * 80)
print("TOP 10 RECORDS BY H6 COMPOSITE RATE (most 'prose-like')")
print("=" * 80)
results_by_rate = sorted(results, key=lambda r: r["h6_composite_rate"], reverse=True)
for r in results_by_rate[:10]:
    print(f"  {r['source']:20s} H6={r['h6_composite_rate']:>8.0f}/M  "
          f"qf={r['quote_fraction']:.4f}  qtok={r['quote_tokens']:>5d}  "
          f"seqlen={r['seqlen']}")

print()
print("=" * 80)
print("BOTTOM 10 RECORDS BY H6 COMPOSITE RATE (least 'prose-like')")
print("=" * 80)
for r in results_by_rate[-10:]:
    print(f"  {r['source']:20s} H6={r['h6_composite_rate']:>8.0f}/M  "
          f"qf={r['quote_fraction']:.4f}  qtok={r['quote_tokens']:>5d}  "
          f"seqlen={r['seqlen']}")

print()
print("=" * 80)
print("COMPARISON TO EXP 4 PILOT")
print("=" * 80)
print("  Exp 4 pilot: H6 on commentary context = 44,822/M")
print("  Exp 4 pilot: H6 on verse content = 4.1/M")
print("  Exp 4 pilot: ratio = 10,911x")
print(f"  Exp 4b mean H6 composite: {sum(r['h6_composite_rate'] for r in results)/len(results):.0f}/M")
print(f"  Exp 4b max H6 composite: {max(r['h6_composite_rate'] for r in results):.0f}/M")
print(f"  Exp 4b min H6 composite: {min(r['h6_composite_rate'] for r in results):.0f}/M")
