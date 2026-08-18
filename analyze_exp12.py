#!/usr/bin/env python3
"""Analyze Exp 12: Digit minimal-pair test.

Compares H6 firing on with_digits vs digit_stripped versions of the same text.
If H6 is digit-independent, H6 rates should be similar across both conditions.
If digit experts exist, they should fire much more on with_digits.

Also checks known digit-associated experts (e.g. e164 at L42) to confirm
they DO respond to digit density — the positive control.
"""
import json
import sys
from collections import defaultdict

# H6 anchors
H6_ANCHORS = {21: 42, 22: 105, 23: 113, 30: 198, 32: 254, 41: 147}

# Known digit-associated expert from prior analysis
# e164 at L42 was the original "scripture detector" that was actually a digit detector
DIGIT_EXPERTS = {42: [164]}  # L42 e164 — the original digit detector

def load_records(path):
    records = []
    with open(path) as f:
        for line in f:
            records.append(json.loads(line))
    return records

def load_corpus(path):
    corpus = {}
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            corpus[(r['category'], r['sample_index'])] = r
    return corpus

def count_fires(record, anchors):
    """Count total fires for specified anchor experts across all layers.
    anchors: dict of {layer_int: expert_idx} or {layer_int: [expert_idx, ...]}"""
    fires = 0
    for lid, layer in record['observation']['layers'].items():
        lid_int = int(lid)
        if lid_int in anchors:
            eidxs = anchors[lid_int]
            if isinstance(eidxs, int):
                eidxs = [eidxs]
            for eidx in eidxs:
                fires += layer['expert_frequencies'][eidx]
    return fires

def check_invariants(records):
    violations = 0
    for r in records:
        for lid, layer in r['observation']['layers'].items():
            freq_sum = sum(layer['expert_frequencies'])
            expected = r['seqlen'] * 6
            if freq_sum != expected:
                violations += 1
                if violations <= 5:
                    print(f"  VIOLATION: {r['category']}:{r['sample_index']} L{lid} sum={freq_sum} expected={expected}")
    return violations

def main():
    obs_path = sys.argv[1] if len(sys.argv) > 1 else "exp12_obs.jsonl"
    corpus_path = sys.argv[2] if len(sys.argv) > 2 else "corpus/samples/exp12_digit_minimal_pairs.jsonl"

    print(f"Loading observations from {obs_path}...")
    records = load_records(obs_path)
    print(f"  {len(records)} records")

    print(f"Loading corpus from {corpus_path}...")
    corpus = load_corpus(corpus_path)
    print(f"  {len(corpus)} corpus entries")

    # Check invariants
    print("\n=== Invariant check ===")
    violations = check_invariants(records)
    print(f"  Violations: {violations}")

    # Merge corpus metadata into records
    for r in records:
        key = (r['category'], r['sample_index'])
        if key in corpus:
            c = corpus[key]
            r['condition'] = c['condition']
            r['pair_id'] = c['pair_id']
            r['digit_density'] = c['digit_density']
        else:
            print(f"  WARNING: no corpus match for {key}")

    # === H6 analysis ===
    print("\n=== H6 firing by condition ===")
    h6_by_cond = defaultdict(lambda: [0, 0])  # [fires, tokens]
    for r in records:
        if 'condition' not in r:
            continue
        fires = count_fires(r, H6_ANCHORS)
        h6_by_cond[r['condition']][0] += fires
        h6_by_cond[r['condition']][1] += r['seqlen']

    for cond in sorted(h6_by_cond):
        f, t = h6_by_cond[cond]
        rate = f / t * 1e6 if t > 0 else 0
        print(f"  {cond}: {f} fires / {t} tokens = {rate:.1f}/M")

    # === H6 by condition × category ===
    print("\n=== H6 by condition × category ===")
    h6_by_cat_cond = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for r in records:
        if 'condition' not in r:
            continue
        fires = count_fires(r, H6_ANCHORS)
        h6_by_cat_cond[r['category']][r['condition']][0] += fires
        h6_by_cat_cond[r['category']][r['condition']][1] += r['seqlen']

    print(f"  {'Category':<25} {'with_digits (M)':>18} {'stripped (M)':>15} {'ratio':>8}")
    for cat in sorted(h6_by_cat_cond):
        wd = h6_by_cat_cond[cat]['with_digits']
        ds = h6_by_cat_cond[cat]['digit_stripped']
        wd_rate = wd[0] / wd[1] * 1e6 if wd[1] > 0 else 0
        ds_rate = ds[0] / ds[1] * 1e6 if ds[1] > 0 else 0
        ratio = wd_rate / ds_rate if ds_rate > 0 else float('inf') if wd_rate > 0 else 1.0
        print(f"  {cat:<25} {wd_rate:>18.1f} {ds_rate:>15.1f} {ratio:>8.2f}x")

    # === Per-pair comparison ===
    print("\n=== Per-pair H6 comparison ===")
    pair_data = defaultdict(dict)
    for r in records:
        if 'condition' not in r or 'pair_id' not in r:
            continue
        fires = count_fires(r, H6_ANCHORS)
        pair_data[r['pair_id']][r['condition']] = (fires, r['seqlen'])

    higher_with_digits = 0
    higher_stripped = 0
    equal = 0
    for pid in sorted(pair_data):
        wd = pair_data[pid].get('with_digits', (0, 0))
        ds = pair_data[pid].get('digit_stripped', (0, 0))
        if wd[0] > ds[0]:
            higher_with_digits += 1
        elif ds[0] > wd[0]:
            higher_stripped += 1
        else:
            equal += 1
    print(f"  with_digits > stripped: {higher_with_digits}")
    print(f"  stripped > with_digits: {higher_stripped}")
    print(f"  equal (both zero or same): {equal}")

    # === Digit expert (e164 at L42) analysis — positive control ===
    print("\n=== e164 (L42) digit expert — positive control ===")
    e164_by_cond = defaultdict(lambda: [0, 0])
    for r in records:
        if 'condition' not in r:
            continue
        fires = count_fires(r, DIGIT_EXPERTS)
        e164_by_cond[r['condition']][0] += fires
        e164_by_cond[r['condition']][1] += r['seqlen']

    for cond in sorted(e164_by_cond):
        f, t = e164_by_cond[cond]
        rate = f / t * 1e6 if t > 0 else 0
        print(f"  {cond}: {f} fires / {t} tokens = {rate:.1f}/M")

    # === Digit expert by category × condition ===
    print("\n=== e164 by condition × category ===")
    e164_by_cat_cond = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for r in records:
        if 'condition' not in r:
            continue
        fires = count_fires(r, DIGIT_EXPERTS)
        e164_by_cat_cond[r['category']][r['condition']][0] += fires
        e164_by_cat_cond[r['category']][r['condition']][1] += r['seqlen']

    print(f"  {'Category':<25} {'with_digits (M)':>18} {'stripped (M)':>15} {'ratio':>8}")
    for cat in sorted(e164_by_cat_cond):
        wd = e164_by_cat_cond[cat]['with_digits']
        ds = e164_by_cat_cond[cat]['digit_stripped']
        wd_rate = wd[0] / wd[1] * 1e6 if wd[1] > 0 else 0
        ds_rate = ds[0] / ds[1] * 1e6 if ds[1] > 0 else 0
        ratio = wd_rate / ds_rate if ds_rate > 0 else float('inf') if wd_rate > 0 else 1.0
        print(f"  {cat:<25} {wd_rate:>18.1f} {ds_rate:>15.1f} {ratio:>8.2f}x")

    # === Digit density correlation ===
    print("\n=== Digit density vs H6 correlation ===")
    densities = []
    h6_rates = []
    for r in records:
        if 'digit_density' not in r:
            continue
        fires = count_fires(r, H6_ANCHORS)
        rate = fires / r['seqlen'] * 1e6 if r['seqlen'] > 0 else 0
        densities.append(r['digit_density'])
        h6_rates.append(rate)
    if len(densities) > 2:
        import statistics
        n = len(densities)
        mean_x = sum(densities) / n
        mean_y = sum(h6_rates) / n
        cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(densities, h6_rates)) / n
        std_x = (sum((x - mean_x) ** 2 for x in densities) / n) ** 0.5
        std_y = (sum((y - mean_y) ** 2 for y in h6_rates) / n) ** 0.5
        r_corr = cov / (std_x * std_y) if std_x > 0 and std_y > 0 else 0
        print(f"  Pearson r = {r_corr:.4f}")
        print(f"  n = {n}")

    # === Summary ===
    print("\n=== SUMMARY ===")
    wd = h6_by_cond.get('with_digits', [0, 0])
    ds = h6_by_cond.get('digit_stripped', [0, 0])
    wd_rate = wd[0] / wd[1] * 1e6 if wd[1] > 0 else 0
    ds_rate = ds[0] / ds[1] * 1e6 if ds[1] > 0 else 0
    print(f"H6 with_digits:    {wd_rate:.1f}/M")
    print(f"H6 digit_stripped: {ds_rate:.1f}/M")
    if ds_rate > 0 and wd_rate > 0:
        print(f"H6 ratio: {wd_rate/ds_rate:.2f}x")
    elif wd_rate == 0 and ds_rate == 0:
        print("H6 ratio: both zero (H6 does not fire on digits OR their absence)")
    else:
        print(f"H6 ratio: {'inf' if wd_rate > 0 else 0}")

    e164_wd = e164_by_cond.get('with_digits', [0, 0])
    e164_ds = e164_by_cond.get('digit_stripped', [0, 0])
    e164_wd_rate = e164_wd[0] / e164_wd[1] * 1e6 if e164_wd[1] > 0 else 0
    e164_ds_rate = e164_ds[0] / e164_ds[1] * 1e6 if e164_ds[1] > 0 else 0
    print(f"e164 with_digits:    {e164_wd_rate:.1f}/M")
    print(f"e164 digit_stripped: {e164_ds_rate:.1f}/M")
    if e164_ds_rate > 0:
        print(f"e164 ratio: {e164_wd_rate/e164_ds_rate:.1f}x (should be large if digit detector)")

if __name__ == "__main__":
    main()
