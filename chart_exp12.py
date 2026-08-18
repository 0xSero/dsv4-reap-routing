#!/usr/bin/env python3
"""Generate charts for Exp 12 digit minimal-pair test."""
import json
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

H6_ANCHORS = {21: 42, 22: 105, 23: 113, 30: 198, 32: 254, 41: 147}
DIGIT_EXPERTS = {42: [164]}

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

def main():
    obs_path = sys.argv[1] if len(sys.argv) > 1 else "exp12_obs.jsonl"
    corpus_path = sys.argv[2] if len(sys.argv) > 2 else "corpus/samples/exp12_digit_minimal_pairs.jsonl"
    out_dir = sys.argv[3] if len(sys.argv) > 3 else "/tmp/dsv4-reap-site/img"

    records = load_records(obs_path)
    corpus = load_corpus(corpus_path)

    for r in records:
        key = (r['category'], r['sample_index'])
        if key in corpus:
            c = corpus[key]
            r['condition'] = c['condition']
            r['pair_id'] = c['pair_id']
            r['digit_density'] = c['digit_density']

    # === Chart 1: H6 and e164 by condition (grouped bar) ===
    fig, ax = plt.subplots(figsize=(8, 5))

    h6_by_cond = defaultdict(lambda: [0, 0])
    e164_by_cond = defaultdict(lambda: [0, 0])
    for r in records:
        if 'condition' not in r:
            continue
        h6_fires = count_fires(r, H6_ANCHORS)
        h6_by_cond[r['condition']][0] += h6_fires
        h6_by_cond[r['condition']][1] += r['seqlen']
        e164_fires = count_fires(r, DIGIT_EXPERTS)
        e164_by_cond[r['condition']][0] += e164_fires
        e164_by_cond[r['condition']][1] += r['seqlen']

    conds = ['with_digits', 'digit_stripped']
    h6_rates = [h6_by_cond[c][0] / h6_by_cond[c][1] * 1e6 if h6_by_cond[c][1] > 0 else 0 for c in conds]
    e164_rates = [e164_by_cond[c][0] / e164_by_cond[c][1] * 1e6 if e164_by_cond[c][1] > 0 else 0 for c in conds]

    x = np.arange(len(conds))
    width = 0.35
    ax.bar(x - width/2, h6_rates, width, label='H6 (verse/prose axis)', color='#4a7ba6', edgecolor='black', linewidth=0.5)
    ax.bar(x + width/2, e164_rates, width, label='e164 (digit expert)', color='#d4915b', edgecolor='black', linewidth=0.5)

    ax.set_ylabel('Firing rate (per M tokens)')
    ax.set_title('Exp 12: H6 vs e164 by digit condition')
    ax.set_xticks(x)
    ax.set_xticklabels(conds)
    ax.legend()
    ax.set_yscale('symlog', linthresh=1)
    ax.set_ylim(bottom=0)
    ax.grid(axis='y', alpha=0.3)

    for i, (h, e) in enumerate(zip(h6_rates, e164_rates)):
        ax.text(i - width/2, max(h, 0.5), f'{h:.1f}', ha='center', va='bottom', fontsize=9)
        ax.text(i + width/2, max(e, 0.5), f'{e:.1f}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(f'{out_dir}/chart_exp12_h6_vs_e164.png', dpi=150)
    print(f"Saved chart_exp12_h6_vs_e164.png")
    plt.close()

    # === Chart 2: H6 by category × condition ===
    fig, ax = plt.subplots(figsize=(10, 6))

    cats = sorted(set(r['category'] for r in records if 'condition' in r))
    h6_cat_cond = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for r in records:
        if 'condition' not in r:
            continue
        fires = count_fires(r, H6_ANCHORS)
        h6_cat_cond[r['category']][r['condition']][0] += fires
        h6_cat_cond[r['category']][r['condition']][1] += r['seqlen']

    x = np.arange(len(cats))
    width = 0.35
    wd_rates = [h6_cat_cond[c]['with_digits'][0] / h6_cat_cond[c]['with_digits'][1] * 1e6
                if h6_cat_cond[c]['with_digits'][1] > 0 else 0 for c in cats]
    ds_rates = [h6_cat_cond[c]['digit_stripped'][0] / h6_cat_cond[c]['digit_stripped'][1] * 1e6
                if h6_cat_cond[c]['digit_stripped'][1] > 0 else 0 for c in cats]

    ax.bar(x - width/2, wd_rates, width, label='with_digits', color='#4a7ba6', edgecolor='black', linewidth=0.5)
    ax.bar(x + width/2, ds_rates, width, label='digit_stripped', color='#7fa8c8', edgecolor='black', linewidth=0.5)

    ax.set_ylabel('H6 firing rate (per M tokens)')
    ax.set_title('Exp 12: H6 by category × digit condition')
    ax.set_xticks(x)
    ax.set_xticklabels([c.replace('_', '\n') for c in cats], fontsize=9)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{out_dir}/chart_exp12_by_category.png', dpi=150)
    print(f"Saved chart_exp12_by_category.png")
    plt.close()

    # === Chart 3: e164 by category × condition (positive control) ===
    fig, ax = plt.subplots(figsize=(10, 6))

    e164_cat_cond = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for r in records:
        if 'condition' not in r:
            continue
        fires = count_fires(r, DIGIT_EXPERTS)
        e164_cat_cond[r['category']][r['condition']][0] += fires
        e164_cat_cond[r['category']][r['condition']][1] += r['seqlen']

    wd_rates = [e164_cat_cond[c]['with_digits'][0] / e164_cat_cond[c]['with_digits'][1] * 1e6
                if e164_cat_cond[c]['with_digits'][1] > 0 else 0 for c in cats]
    ds_rates = [e164_cat_cond[c]['digit_stripped'][0] / e164_cat_cond[c]['digit_stripped'][1] * 1e6
                if e164_cat_cond[c]['digit_stripped'][1] > 0 else 0 for c in cats]

    ax.bar(x - width/2, wd_rates, width, label='with_digits', color='#d4915b', edgecolor='black', linewidth=0.5)
    ax.bar(x + width/2, ds_rates, width, label='digit_stripped', color='#e6c89f', edgecolor='black', linewidth=0.5)

    ax.set_ylabel('e164 firing rate (per M tokens)')
    ax.set_title('Exp 12: e164 (digit expert) by category × digit condition — positive control')
    ax.set_xticks(x)
    ax.set_xticklabels([c.replace('_', '\n') for c in cats], fontsize=9)
    ax.legend()
    ax.set_yscale('symlog', linthresh=1)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{out_dir}/chart_exp12_e164_by_category.png', dpi=150)
    print(f"Saved chart_exp12_e164_by_category.png")
    plt.close()

if __name__ == "__main__":
    main()
