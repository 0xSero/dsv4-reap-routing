# External review: DeepSeek-V4-Flash-0731 REAP routing interpretability study

I read the local write-ups (`wiki_research_report.html`, `EXPERIMENTS.md`,
`analysis_all/exp8_sorted_freq_results.txt`, `analysis/*.csv`, the aggregate JSONs
`core_agg.json` / `christian_agg.json`, and the code in `observe_religious.py`,
`analyze_experts.py`, `run_jlens.py`, `jlens_dsv4.py`), then re-derived the key
numbers myself. Below is what I think the data actually shows, where the write-up
oversteps or contradicts the artifacts, and what would change my mind.

---

## 1. What I think you actually found

### 1.1 The e164 exact-zero is real and is the strongest result

The headline observation survives the checks you did:

- `exp8_sorted_freq_results.txt` reports L42 expert 164 fires **0 times in
  1,189 KJV Bible chapters / 1,045,776 tokens**, vs. 1,180 times in the Qur'an
  (258 k tokens) and 93,265 times in Christian literature (20.4 M tokens).
- Re-derived from `core_agg.json` / `christian_agg.json`:
  - Bible: 0.0 / M tokens
  - Qur'an: 4,571 / M tokens
  - Gita: 1,549 / M tokens
  - Book of Mormon: 158 / M tokens
  - Christian literature: ~4,565 / M tokens
- The permutation control in `exp8_sorted_freq_results.txt` is the right idea:
  15 of the top-20 L42 experts by frequency are shared between Bible and Qur'an,
  and the multiset of sorted frequencies differs in shape enough (rank 152 vs 255
  for e164) that a simple shard-index permutation cannot explain the zero.
- The observation harness is fail-closed: it asserts `Σfreq == seqlen × top_k`
  per layer per record, fsyncs each row, and reports zero violations
  (`observe_religious.py` lines 100–120; `generate_report.py` verification).

So **there is a real, sharp routing feature at L42 that is active for Qur'anic
English, post-biblical Christian doctrine, and the Bhagavad Gita, and almost
completely inactive for verbatim KJV scripture and the Book of Mormon.**

### 1.2 The interpretation is weaker than the write-up claims

The write-up calls this a “not-memorized-scripture” / KJV-register expert. That
is a plausible *post-hoc* story, but the current evidence only supports the
descriptive claim: **e164 separates KJV-scripture-like text from the other
English religious corpora you observed.** It could be:

1. KJV 1611 register / memorization (the preferred story),
2. a modern-English / doctrinal-prose detector,
3. an entropy / predictability expert,
4. a length / position confound (the KJV samples are ~880-token chapters, the
   Christian samples are 16 k windows),
5. a translation-English detector (Qur'an and Gita are translations; KJV is not).

Your `EXPERIMENTS.md` lists all of these as open questions (Exp 1, 3, 7, 9), so
you already know the register label is not yet locked in.

### 1.3 The Jaccard / “layer sandwich” story is inconsistent across files

The write-up gives a neat layer-wise picture for Bible ↔ Christian literature:
low overlap at L0–2 and L39–42, high at L3–6/19. I cannot reproduce that exact
pattern from the committed artifacts:

- `analysis/cross_text_jaccard.csv` (produced by `analyze_experts.py`) is an
  **overall** top-20 REAP matrix for the 8 core texts and gives Bible–BoM =
  0.212, not 0.53, and Bible–Christian is not in that file at all.
- `analysis/robustness_checks.txt` lines 8–10 says the 0.53-class numbers are
  from **per-layer top-5 profiles** (Bible–BoM 0.539, Bible–Qur'an 0.525,
  BoM–Qur'an 0.544), not top-20.
- I re-derived per-layer top-20 REAP Jaccard from `core_agg.json` +
  `christian_agg.json` for Bible ↔ Christian and got mean ≈ 0.11, with L0–2 ≈
  0.03, L3–6 ≈ 0.03, and L39–42 ≈ 0.14–0.21. The mid-layer “semantic backbone”
  overlap of 0.54–0.74 does **not** fall out of this metric.
- Using per-layer top-20 **frequency** Jaccard gives the opposite early-layer
  pattern (L0–2 ≈ 0.6–0.9), so the “surface form” interpretation would flip.

**Conclusion:** the layer-sandwich numbers are metric-dependent and the write-up
appears to mix a top-5 per-layer profile (the 0.53 matrix) with a top-20 REAP
claim (the sandwich). The qualitative idea that Christian doctrine diverges from
KJV scripture is directionally supported (Christian literature is the most
distant from the KJV in the committed top-20 REAP matrix), but the precise
layer-by-layer story needs to be recomputed with one metric and documented.

### 1.4 Effective-expert count claim is reproducible

From `core_agg.json` / `christian_agg.json` at L40, using the exponential-Shannon
entropy effective-count on the expert-frequency distribution:

- Gita: 26
- Qur'an: 43
- Bible: 65
- Christian literature: 111

These match the headline ordering and are a nice, independent signature that
doctrinal prose recruits a broader late-layer palette.

### 1.5 The Genesis 1:2 logit-lens claim is overstated

The write-up says:

> “Logit-lens decoding of Genesis 1 surfaces ‘Spirit’ at 76.7% confidence at
> layer 30 — the KJV rendering of Genesis 1:2.”

I checked `jlens_output/bible_jlens.jsonl` (sample `genesis_c001`). The token
that the write-up calls “position 3” is actually **position 30**, and the input
token at position 30 is `' deep'`, not `' Spirit'`:

```
position 30 token: ' deep'
layer 30 top token: ' Spirit' 0.7668
final layer top token at position 30: '.' 0.9166
```

The actual `' Spirit'` token is at position 34. The intermediate layer 30 is
“predicting” a token that appears four positions later in the same verse, while
the final layer correctly predicts the immediate next token `'.'`. This is
exactly the kind of noisy, untuned-lens behavior the authors acknowledge in the
caveats, and it should not be described as the model “knowing Genesis 1:2.”
Cherry-picking position 30 because it happens to decode to a later token is not
a valid logit-lens finding.

### 1.6 Bounded Jacobian is reported accurately

The bounded-Jacobian norms in the write-up (L0 ≈ 1268, L10 ≈ 371, L20 ≈ 363,
L30 ≈ 378, L42 ≈ 320) match `jlens_output/bible_jlens.jsonl` within rounding.
The interpretation that layer 0 has the largest leverage is therefore supported
by the bounded finite-difference probe, with the caveat that it uses only 16
random projection directions and does not give a full Jacobian.

---

## 2. Flaws and confounds not yet killed

### 2.1 Position / length confound (your Exp 9)

This is the biggest immediate threat to the e164 story. KJV chapters average
~880 tokens and never reach the later positions of a 16 k window. If e164 is a
position-dependent or length-dependent expert, the Bible’s exact-zero could be
an artifact of the windowing strategy, not of register. This is listed as a
high-priority, cheap experiment in `EXPERIMENTS.md`; it should be run before any
publication.

### 2.2 Translation-English vs. register (your Exp 1)

The Qur'an and Gita are English translations; the KJV and BoM are not. e164 may
be a “translationese” detector rather than a “not-memorized-scripture” detector.
Your Exp 1 (Genesis 1 in six translations, same content) is the cleanest way to
separate these.

### 2.3 No secular null (your Exp 3)

You compare religious corpora against each other, but not against non-religious
English. If Wikipedia, arXiv, and news also activate e164 at ~4,500/M tokens,
the finding becomes “non-KJV English,” not “non-KJV scripture.” Exp 3 is
essential before interpreting any Jaccard overlap as religious.

### 2.4 Entropy / predictability alternative (your Exp 7)

The effective-expert count ordering tracks predictability, which raises the
possibility that e164 is an entropy/routine expert rather than a register
expert. A regression of e164 firing on per-token loss/entropy and position
would kill or confirm this.

### 2.5 REAP is correlational

The write-up’s causal language (“the router learned,” “the model treats
Christianity as two regimes”) is not justified by read-only REAP statistics.
Your limitation section acknowledges this; I would make it more prominent in the
abstract and discussion.

### 2.6 Logit-lens cherry-pick

As shown in §1.5, the Genesis lens example is mislabeled and appears to be a
cherry-picked position. I would remove it from the headline findings until a
systematic, position-matched logit-lens analysis is done.

### 2.7 Numerical reproducibility of the Jaccard / layer sandwich

The Jaccard matrix in the write-up cannot be reproduced from
`analysis/cross_text_jaccard.csv` or from the committed aggregation scripts. The
matrix values appear to come from per-layer top-5 profiles
(`robustness_checks.txt`), while the figure caption says “top-20 REAP experts.”
This is a serious paper-level inconsistency and must be resolved before
submission.

### 2.8 Small-sample traditions

Gita (n = 18, 30 k tokens) and Upanishads (n = 3, 22 k tokens) are too small for
strong claims. The write-up is appropriately cautious about Upanishads but still
uses the Gita e164 number in the main specialist table.

### 2.9 Code-level caveat: patched kernels

`observe_religious.py` replaces the tilelang `sparse_attn` kernel and
`fast_hadamard_transform` with pure-PyTorch equivalents. The authors claim
numerical equivalence, but any difference here would affect routing. This is
reasonable for an observation study but should be noted in the methods.

---

## 3. The single most valuable next experiment

**Run Experiment 1 (Genesis 1 multi-translation register test) *and* Experiment
9 (re-window the Bible into 16 k blocks) in parallel.**

If forced to pick one: **Experiment 1 is the highest-value scientific test**
because it directly distinguishes the register/memorization hypothesis from
the content hypothesis while holding text constant. If e164 fires on NIV/
Message but stays silent on KJV, the “not-memorized-scripture” label is
strongly supported. If it fires on none, the label is wrong.

However, **Experiment 9 is a mandatory prerequisite**: if e164 turns out to be
a position/length artifact, Experiment 1 would be uninterpretable. It is also
cheaper (1–2 GPU hours). My recommended order is:

1. **Exp 9** (position/length confound) — run first; if e164 stays zero in 16 k
   Bible windows, the core result hardens.
2. **Exp 1** (Genesis multi-translation) — the interpretive killer experiment.
3. **Exp 3** (secular null) — needed before any claim about religion vs. general
   English.

If you only have one GPU block, do **Exp 9 first**, because it guards every
other claim.

---

## 4. Is anything here genuinely novel / publishable?

**Yes, but only the e164 observation, and only if the controls hold.**

Finding a single expert in a 256-expert, 43-layer MoE that is *exactly* silent
on ~1 M tokens of one register and highly active on doctrinal prose and
translations is a striking, auditable phenomenon. It is also easy to verify
independently because expert routing is discrete and countable. If Experiment 1
shows the effect is driven by register/memorization and Experiment 9 rules out
position, this would be a credible, novel observation for an interpretability
workshop or a short conference paper.

The broader framing—religious-text routing, a scriptural “backbone,” doctrinal
overlay experts, layer-wise division of labor—is currently too correlational
and too entangled with translation/length confounds to be publishable as a
strong claim. The Genesis logit-lens result should be removed from any
publication draft.

**Verdict:** the study has one genuinely novel *observation* (e164) and a clear
experimental path to turn it into a *claim*. Do not publish the current draft as
a paper; publish it only after Exp 1, Exp 3, and Exp 9, and after reconciling
the Jaccard metrics in the write-up with the committed artifacts.

---

## 5. Concrete fixes before the next review

- Recompute the Jaccard matrix and layer-sandwich numbers with a single,
  documented metric (e.g., per-layer top-20 by corpus-specific mean REAP), and
  make the write-up match `cross_text_jaccard.csv` / `robustness_checks.txt`.
- Remove or heavily qualify the Genesis 1:2 logit-lens claim; show the actual
  position-30 result if you keep it.
- Add the secular null (Exp 3) to the main methods, not just the future-work
  list.
- Run Exp 9 and Exp 1 and report the results before making any causal/register
  claims.
- Release the bootstrap script or notebook used for §5.4; the matched-n
  resampling procedure is described but not present in the committed code I
  read.
