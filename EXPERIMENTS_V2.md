# Redesigned Experiment Plan (V2)
## Correctness-First, Post-Claude-Opus-5-Review

**Date:** 15 August 2026
**Status:** Wave-2 Christian observation COMPLETE (3,562 records, 55.9M tokens). Sparks free.
**Prior work:** 22.2M tokens observed across 9 corpora. Claude Opus 5 review found 2 corrupt claims, rejected H3, identified H6 verse-vs-prose axis. All verified against raw data.

---

## What we're keeping (salvaged from V1)

1. **REAP observation harness** — read-only, fail-closed, verified line-for-line against model.py. Works.
2. **Core 8-corpus observation** (full_obs.jsonl, 1,482 records, 1.77M tokens) — clean data, correctly recorded.
3. **Christian observation** (christian_all_obs.jsonl, 3,562 records, 55.9M tokens) — wave-1 + wave-2 merged, zero invariant violations.
4. **J-lens data** (83 records, 5,282 positions) — top-1 agreement curve verified, the cleanest result.
5. **Digit expert characterization** (H1) — 54 experts with R² > 0.5, settled.
6. **H6 verse-vs-prose axis** — verified, rates up to 90,595/M vs ~0, digit-independent, length-independent.
7. **Lens agreement curve** — L19 step, L42 = 87.4%, per-corpus breakdown.
8. **No-religion-routing null** (H5) — well supported, main contribution.

## What we're cutting

- **Theology observation** (1,090 records) — Wikipedia-derived, digit-dense, apparatus-heavy. The exact confound that ate two headlines. No hypothesis it can decide.
- **Exps 5/6** (Jesus vs Lucifer, Moloch vs Saturn) — same confound.
- **H3** (routing concentration = predictability proxy) — retracted, sign is backwards.
- **Any intermediate-layer lens probability claims** — uncalibrated, unusable.
- **Any Jacobian claim before ε-normalization** — misnamed probe, L0 artifact.

---

## Redesigned experiments (ranked by decisiveness per GPU-hour)

### Exp 4: Quotation Switch (THE decisive experiment) — READY TO DEPLOY

**Hypothesis:** The H6 verse-vs-prose routing axis is caused by verse-text vs discursive prose, not by corpus, tradition, digit density, or window length.

**Design:** 30 samples from Christian books that quote the KJV verbatim. Each 16k-token window contains BOTH quoted scripture (verse-text) AND surrounding commentary (discursive prose). Same document, same window, same digit density, same position band. The ONLY variable is verse-text vs commentary.

**Corpus:** `corpus/samples/exp4_quotation_switch.jsonl` — 30 samples, 465K tokens, each with annotated quote spans (token positions where KJV verses appear).

**Prediction:** If L22 e105, L30 e198, L41 e147, and the rest of the H6 cluster switch OFF inside quotation spans and ON in commentary spans — within the same document — H6 is proven with zero cross-corpus confound. This is the best figure we will get.

**Anti-predition:** If H6 experts fire uniformly within each document regardless of quote/commentary boundaries, the axis is NOT verse-vs-prose but something else about the corpora (vocabulary, topic, era).

**GPU time:** ~2 hours (30 samples × ~4 min each).

**Analysis:** For each sample, compute H6 expert firing rate in quote-token ranges vs non-quote-token ranges. This requires `--raw-budget-tokens` mode (per-token routing capture), since existing records only store aggregate frequencies.

### Exp 1: Multi-Translation Register Test — READY TO DEPLOY

**Hypothesis:** The H6 axis responds to register (archaic vs modern English), not content.

**Design:** Genesis 1-3 in 5 public-domain translations: KJV (1611, archaic), ASV (1901), WEB, WEBBE (British), BBE (850-word Basic English). All verse numbers stripped, all verified 0.0000% digits. Content held constant; only register varies.

**Corpus:** `corpus/samples/exp1_translations.jsonl` — 5 samples, 52K tokens.

**Prediction:** If BBE (modern, simple vocabulary) fires the H6 cluster more than KJV (archaic), the axis is register-driven. If all 5 fire ~0, the axis is not register but format (verse structure itself).

**GPU time:** Sub-hour.

### Exp 12: Digit Minimal-Pairs — READY TO DEPLOY (negative control)

**Hypothesis:** e164 is a bare-numeral detector, not a citation-structure detector.

**Design:** 12 KJV chapters × 3 versions: (a) as-is (digit-free), (b) verse numbers restored ("1:1 In the beginning...", 2.234% digits), (c) arbitrary numerals at random word boundaries (2.825% digits).

**Corpus:** `corpus/samples/exp12_minimal_pairs.jsonl` — 111 samples.

**Prediction:** If (b) ≈ (c) >> (a): bare-numeral detector. If (b) >> (c): citation-structure detector. Published as negative control — the digit question is already settled, but this confirms the mechanism.

**GPU time:** Sub-hour.

### Exp 11: Context Dump (retargeted) — READY TO DEPLOY

**Hypothesis:** What tokens actually trigger the H6 cluster experts?

**Design:** Re-run observation with `--raw-budget-tokens` on a small subset (10-20 samples). Extract top-500 firing contexts with ±20-token windows for L22 e105, L30 e198, L41 e147.

**Prediction:** Contexts in prose sections will be discursive markers (transition words, conjunctions, editorial language). Contexts in verse sections (if any) will show what the experts are NOT firing on.

**GPU time:** ~1 hour.

### Exp 3: Secular Null (redesigned) — NEEDS CORPUS BUILD

**Hypothesis:** The H6 axis is prosody/lineation, not scripture-specific.

**Design:** Stratify by digit density AND verse/prose format. Include:
- Secular verse: public-domain poetry (Milton, Wordsworth, Whitman) — digit-free, lineated
- Secular prose: public-domain essays/philosophy (Hume, Russell) — digit-free, discursive
- Matched-digit-density prose from Wikipedia

**Prediction:** If Milton and Wordsworth land on the Bible side of the H6 cluster, the axis is prosody/lineation and religion is entirely out. This is the experiment that converts "verse-vs-prose" into "lineated-vs-unlineated" or rules it out.

**GPU time:** ~4-6 hours after corpus is built.

### Exp 13 (NEW): Expert Ablation — NEEDS SCOPE DECISION

**Hypothesis:** Zeroing the H6 cluster experts causes per-token loss to rise on prose but not on verse.

**Design:** Force the H6 experts to zero (override routing) on a small set of matched samples. Measure ΔNLL on KJV vs Christian prose.

**Note:** This requires modifying the forward pass (not read-only). Needs explicit re-scoping. If approved, this is the experiment that converts the routing correlation into a causal claim.

**GPU time:** ~2 hours.

### Exp 14 (NEW): Covariate Regression — NO GPU, DO TODAY

**Hypothesis:** After controlling for format features, no tradition effect remains.

**Design:** On existing records, regress H6 expert firing rates on: digit%, punctuation%, mean sentence length, type-token ratio, verse/prose indicator, and tradition dummy variables. If tradition coefficients are zero after controlling for format, religion is fully explained away.

**GPU time:** None — pure statistics on existing data.

---

## Deployment order

1. **Exp 4** (quotation switch) — 30 samples, ~2h, THE decisive test
2. **Exp 1** (multi-translation) — 5 samples, sub-hour, register test
3. **Exp 12** (digit minimal-pairs) — 111 samples, sub-hour, negative control
4. **Exp 11** (context dump) — 20 samples, ~1h, retargeted to H6
5. **Exp 14** (covariate regression) — no GPU, run while others deploy
6. **Exp 3** (secular null) — build corpus first, then ~4-6h
7. **Exp 13** (ablation) — pending scope decision

All three of Exp 4, 1, and 12 can run sequentially on the same spark deployment (total ~4h GPU time).

---

## Visualization plan

All visualizations published to the wiki with raw-data provenance:

1. **H6 heatmap** — 13 H6 expert cells × 9 corpora, log-scale firing rates ✓ DONE
2. **H6 boxplot** — verse vs prose distributions per expert ✓ DONE
3. **Lens agreement curve** — overall + per-corpus L42 comparison ✓ DONE
4. **Expert utilization** — L42 distribution histograms for all 9 corpora ✓ DONE
5. **Effective expert count** (matched budget) — length-controlled bar chart ✓ DONE
6. **Quotation-switch result** (pending Exp 4) — within-document firing rate: quote spans vs commentary spans
7. **Covariate regression** (pending Exp 14) — coefficient plot showing format vs tradition effect sizes
8. **Ablation ΔNLL** (pending Exp 13) — loss delta per token when H6 cluster is zeroed
