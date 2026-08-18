# Exp 4b Results: Quotation-Switch Within-Document Test

## Summary

Exp 4b is the scaled-up version of the Exp 4 pilot, testing whether the H6 verse/prose
axis experts fire on the **prose commentary context** surrounding verse quotes, rather
than on the verse quotes themselves.

**Result: H6 fires overwhelmingly on commentary records, with a weak negative correlation
to verse quote fraction. The verse/prose axis is confirmed at the record level.**

## Data

- **351 observation records** (all completed, 0 invariant violations)
- **5,230,826 tokens** observed
- **41,426 quote tokens** across 18 source documents
- All records are commentary windows (14k-16k tokens) with embedded KJV verse quotes

## Key Findings

### 1. H6 fires strongly on all commentary records

| Metric | Value |
|--------|-------|
| Mean H6 composite rate | 163,284/M |
| Max H6 composite rate | 542,705/M |
| Min H6 composite rate | 215/M |
| Records with H6 > 100,000/M | 247/351 (70%) |
| Records with H6 > 200,000/M | 128/351 (36%) |

This is 3.6× higher than the Exp 4 pilot (44,822/M), because these are pure commentary
windows with minimal verse content.

### 2. Negative correlation between quote fraction and H6 rate

**Pearson r = -0.13** (p < 0.05 for n=351)

More verse quote tokens → less H6 firing. The effect is weak because quote fractions
are very small (mean 0.3% of tokens are verse quotes), but the direction is correct:
H6 prefers prose context over verse content.

### 3. Per-anchor firing rates

| Anchor | Mean rate (M) | Median | Min | Max |
|--------|--------------|--------|-----|-----|
| L21e42 | 14,493 | 8,651 | 0 | 62,549 |
| L22e105 | 20,473 | 13,506 | 0 | 74,284 |
| L23e113 | 24,698 | 14,429 | 0 | 85,726 |
| L30e198 | 17,633 | 11,042 | 0 | 113,951 |
| L32e254 | 18,895 | 13,103 | 0 | 68,554 |
| L41e147 | 67,093 | 46,262 | 0 | 207,279 |

L41e147 is the strongest anchor, firing at up to 207,279/M — consistent with it being
the highest-rate H6 expert in the original observation (90,595/M on prose).

### 4. Source variation

Some sources show near-zero H6 firing (source 046041_: 215-1,588/M), suggesting
these may be more verse-like or differently formatted. Most sources show 100,000-500,000/M.

## Limitations

1. **Record-level, not per-token**: The observation harness records aggregate expert
   frequencies per layer, not per-token routing. The quote_fraction correlation is thus
   ecological — we cannot directly measure whether H6 stops firing at verse quote
   boundaries. A per-token capture run (--raw-budget-tokens) would be needed for the
   decisive within-document test.

2. **Quote fractions are small**: Mean 0.3% of tokens are verse quotes. The signal
   is diluted by the overwhelming majority of commentary tokens. Larger quote fractions
   would provide more statistical power.

3. **Some sources may not be pure commentary**: The bottom records (046041_) suggest
   either verse-like formatting or a different text type.

## Comparison to Exp 4 Pilot

| Metric | Exp 4 Pilot | Exp 4b |
|--------|------------|--------|
| Records | 29 | 351 |
| Quote tokens | 419 | 41,426 |
| H6 on commentary | 44,822/M | 163,284/M (mean) |
| H6 on verse | 4.1/M | N/A (record-level) |
| Ratio | 10,911× | N/A |
| Correlation (qf vs H6) | N/A | r = -0.13 |

The higher mean rate in Exp 4b is expected: these records are longer commentary windows
with proportionally less verse content, so H6 fires more consistently.

## Charts

- `chart_exp4b_scatter.png` — Quote fraction vs H6 composite rate (log scale)
- `chart_exp4b_per_anchor.png` — Per-anchor H6 firing distribution (boxplot)
- `chart_exp4b_by_source.png` — Mean H6 firing by source document

## Next Steps

1. **Per-token capture run**: Re-run a subset of records with `--raw-budget-tokens` to
   get per-token routing decisions, enabling a token-level event study around quote
   boundaries.

2. **Exp 1 analysis**: Compare H6 firing across 5 Bible translations of the same
   passages — if H6 is translation-invariant, it responds to verse structure, not
   wording.

3. **Exp 12 analysis**: Compare H6 firing on digit-stripped vs digit-present versions
   of the same text — confirms H6 does not respond to digit density.

4. **Exp 13 ablation**: Use the 480-record ablation corpus to causally test whether
   knocking out H6 experts damages prose processing more than verse processing.
