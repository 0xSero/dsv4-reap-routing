# External review — DeepSeek-V4-Flash-0731 REAP routing interpretability study

Reviewer: Claude Opus 5. Date: 2026-08-16.

**Scope of what I did.** I did not take any reported number on faith. I re-parsed
`full_obs.jsonl` (586 MB, 1,482 records) and `christian_obs.jsonl` (566 MB, 1,267
records) from scratch, re-derived the corpus groupings from the `category` field,
recomputed the L42 expert-frequency tables, the per-layer Jaccard curves, the
effective-expert counts, and then ran three controls the study has not run. I also
read `observe_religious.py`, `exp8_sorted_freq.py`, `prepare_corpus.py`,
`jlens_dsv4.py`, `analysis/robustness_checks.txt`, `jac_matrix.json`, and
`EXPERIMENTS.md`, and I decoded corpus samples back to text with the tokenizer in
`tokenizer/`.

**Bottom line.** The engineering is sound and the numbers are real — every headline
figure reproduced exactly from the raw JSONL. The *interpretation* of the flagship
finding is wrong. e164 is not a "not-memorized-scripture" expert. It is a
numeral/citation-apparatus expert, and the KJV corpus has exactly zero digit
characters in it by construction of your own `prepare_corpus.py`. I show this below
with a within-corpus, length-controlled test. Separately, the "layer sandwich"
(claim 2) is an artifact of measuring `reap_score` instead of routing frequency, and
it inverts when you measure actual routing. Claim 3 is a pooling artifact. Claim 6 is
factually wrong against your own `jac_matrix.json`.

---

## 0. What reproduced cleanly (credit where due)

I rebuilt the L42 table independently. Against your claim 1 and
`analysis_all/exp8_sorted_freq_results.txt`:

| corpus | n | tokens | median len | e164 @ L42 | rate /M | expected (proportional) |
|---|---|---|---|---|---|---|
| christian | 1267 | 20,409,440 | 16,384 | 93,265 | **4569.7** | 478,346 |
| bible | 1189 | 1,045,776 | 825 | **0** | **0.0** | 24,510 |
| bofm | 15 | 342,614 | 12,018 | 54 | **157.6** | 8,030 |
| quran | 114 | 258,122 | 1,241 | 1,180 | **4571.5** | 6,050 |
| gita | 18 | 29,690 | 1,476 | 46 | 1549.3 | 696 |
| dhamma | 26 | 16,203 | 566 | 35 | 2160.1 | 380 |
| analects | 20 | 42,041 | 2,108 | 1 | 23.8 | 985 |
| tao | 81 | 13,852 | 162 | 1 | 72.2 | 325 |
| upanishads | 3 | 21,669 | 4,995 | 0 | 0.0 | 508 |

4569.7, 4571.5, 157.6, and the hard zero over 1,045,776 tokens all match your
reported values to the digit. The harness's data path is trustworthy: I found zero
duplicate `(category, sample_index)` keys across either file, and `freq_sum ==
seqlen × 6` held on every record I touched. The measurement layer is not the problem.

I also killed one thing you list as an open caveat, in your favour — see §2.1.

---

## 1. The flagship finding is a digit detector

### 1.1 The confound you did not list

Decode a Bible sample and a Qur'an sample and look at them side by side.

`corpus/samples/bible.jsonl`, `genesis_c001` begins:

> `'In the beginning God created the heaven and the earth.\nAnd the earth was without form, and void;...'`

Clean prose. No numerals at all. This is by design — `prepare_corpus.py:219-227`
splits KJV chapters on the inline `N:M ` verse markers and keeps only
`full[m.end():end]`, i.e. it **strips every verse number out of the text**. The KJV
corpus is 0.000% digits.

`corpus/samples/quran.jsonl`, `sura_096` begins:

> `'RECITE3 thou, in the name of thy Lord who created;-\n...Nay, verily,4 Man is insolent,...A servant5 of God when he prayeth?\nWhat thinkest thou?6 ...Then let him summon his associates;7\n...and draw nigh to God.8\n_______________________\n1 The word Sura occurs nine times in the Koran, viz. Sur. ix. 65, 87, 125, 128; xx'`

That is Rodwell's **scholarly apparatus**: superscript footnote markers fused into
words (`RECITE3`, `verily,4`, `servant5`, `associates;7`, `God.8`), a horizontal
rule, and then a footnote block full of digits and citation strings. The Gutenberg
Christian literature corpus is likewise full of footnotes, page references, chapter
numbers, and inline scripture citations.

So the Bible↔Qur'an and Bible↔Christian contrasts are not "memorized vs not
memorized." They are "digit-free vs digit-bearing."

### 1.2 The test

I joined every observation record back to its source text via
`(category, sample_index)`, computed digit-character density per sample, and binned
e164's L42 firing rate by that density. Pooled across all corpora (samples ≥300
tokens):

| decile | digit % range | n | e164 /M |
|---|---|---|---|
| 1 | 0.000–0.000 | 253 | **0.0** |
| 2 | 0.000–0.000 | 254 | **0.0** |
| 3 | 0.000–0.000 | 254 | **0.0** |
| 4 | 0.000–0.000 | 254 | **0.0** |
| 5 | 0.000–0.013 | 254 | 44.7 |
| 6 | 0.013–0.095 | 253 | 502.0 |
| 7 | 0.095–0.215 | 254 | 1829.2 |
| 8 | 0.216–0.413 | 254 | 3682.5 |
| 9 | 0.413–0.807 | 254 | 7013.5 |
| 10 | 0.807–6.087 | 254 | **13829.1** |

Perfectly monotone across ten deciles, spanning zero to 13,829/M.

The obvious objection is that digit density is confounded with corpus and with
length. So I repeated it **inside the Christian corpus alone**, where every sample is
a 16,384-token Gutenberg window — length, genre, provenance, and windowing all held
fixed:

| decile | digit % range | n | e164 /M |
|---|---|---|---|
| 1 | 0.000–0.012 | 121 | **42.9** |
| 2 | 0.012–0.045 | 122 | 220.3 |
| 3 | 0.045–0.095 | 122 | 768.4 |
| 4 | 0.095–0.151 | 121 | 1447.2 |
| 5 | 0.151–0.219 | 122 | 2225.6 |
| 6 | 0.220–0.310 | 122 | 3320.9 |
| 7 | 0.310–0.462 | 121 | 4606.7 |
| 8 | 0.464–0.702 | 122 | 6961.0 |
| 9 | 0.703–1.079 | 122 | 9952.2 |
| 10 | 1.084–6.087 | 122 | **16448.2** |

Still perfectly monotone. A 383× range in firing rate, generated entirely *within*
the corpus you used as the high-e164 pole, with zero contribution from theology,
memorization, or register.

### 1.3 The strict control

Christian samples containing **exactly zero digit characters**: n=38,
613,506 tokens, **3** e164 firings → **4.9 /M**.

Against 4569.7 /M for the Christian corpus as a whole. Removing digits removes
~99.9% of the effect.

Now the decisive comparison. At the zero-digit Christian rate of 4.9/M, the KJV's
1,045,776 tokens would be expected to produce **≈5 firings**. You observed 0. With
only 3 events in the control the rate is very noisy (Poisson 95% CI on 3 events is
roughly 1–15/M), so the expectation is somewhere between ~1 and ~15 firings and
observing 0 is unremarkable.

Compare that to the number in your writeup: expected 4,779 at the full Christian rate,
observed 0. That gap — the thing that makes the finding look astronomical — is
**entirely** the digit confound. Once you condition on digits there is no anomaly
left to explain.

Every secondary number falls into line under this reading:

- Book of Mormon: Gutenberg, clean prose, 0.000% median digits → 157.6/M. You read
  this as a "memorization gradient" (partially memorized, so partially suppressed).
  It is simply another digit-free corpus.
- Upanishads: 0.000% digits → 0.0/M.
- Tao: numbers stripped by `prepare_corpus.py:329` → 72.2/M.
- Dhammapada: 1.97% median digits → 2160/M.
- Analects at 0.317% digits → 23.8/M is the one point off the curve; n=20 and short
  samples, worth a look but not load-bearing.

The memorization ordering you report (KJV ≫ BoM ≫ Qur'an-in-English) happens to
correlate with the digit ordering, because the most-memorized texts are the ones you
had the cleanest public-domain plaintext for and stripped the verse numbers from.
That is a corpus-construction artifact, not a property of the model.

### 1.4 e164 is also not a singleton

Your writeup presents e164 as *the* expert. I ranked all 256 L42 experts by
log(bible rate / christian rate):

| rank | expert | bible freq | bible /M | christian /M | expected in bible |
|---|---|---|---|---|---|
| 1 | **e164** | 0 | 0.0 | 4569.7 | 4,779 |
| 2 | **e27** | 0 | 0.0 | 4174.0 | 4,365 |
| 3 | e171 | 0 | 0.0 | 597.6 | 625 |
| 4 | e4 | 0 | 0.0 | 259.0 | 271 |
| 5 | **e68** | 1 | 1.0 | 19124.5 | **20,000** |
| 6 | e93 | 272 | 260.1 | 53586.4 | 56,039 |
| 7 | e173 | 22 | 21.0 | 3375.1 | 3,530 |
| 8 | e56 | 284 | 271.6 | 40573.0 | 42,430 |

e27 is e164's near-twin (zero in the Bible, 4174/M in Christian) and goes unmentioned.
e68 is *more* extreme in absolute terms — 20,000 firings expected, 1 observed — and
also goes unmentioned. **29 experts** have expected count >1,000 in the Bible and
observe less than 10% of it.

So the honest statement is: L42 contains a *cluster* of experts, at least five of
them, that are near-completely off on digit-free archaic English. Picking the single
most extreme one out of 256 and naming it is a selection effect; the cluster is the
finding. This matters for publication, because a reviewer will ask what the null
distribution over 256 experts looks like, and right now the writeup does not report
it.

---

## 2. Other claims

### 2.1 Claim 1's length/position confound is already dead — better news than you think

You have this queued as Exp 9 (`EXPERIMENTS.md`, priority HIGH). You can close it.
Binning by sample length:

- **Bible**, all length bins from [0,600) through [1500,3000): 1,045,776 tokens,
  **e164 = 0 in every bin**. Zero of 1,189 samples fire.
- **Qur'an**, [600,1000): 4201/M. [1000,1500): 4525/M. [1500,3000): 4080/M. Flat.

Restricting both to the overlapping window [600, 1500) tokens: Bible n=743,
714,242 tokens, **0** firings; Qur'an n=32, 31,484 tokens, **138** firings
(4383/M). The Bible has 23× more tokens in the matched band and still exactly zero.
The rate is flat in length across two decades. Length and absolute position do not
explain the contrast, and Exp 9 as specified would tell you nothing you don't
already have. (This does not rescue the finding — §1 still applies — but the
confound you were worried about is genuinely not the problem.)

**However**, there is a length effect you missed, in the opposite direction, inside
BoM:

| BoM length bin | n | tokens | e164 | /M |
|---|---|---|---|---|
| [1500,3000) | 2 | 4,695 | 42 | **8945.7** |
| [3000,9000) | 5 | 27,582 | 4 | 145.0 |
| [9000,17000) | 20 | 306,490 | 8 | **26.1** |

A 340× swing within a single corpus. Your headline BoM figure of 157.6/M is a
weighted average over that. Small n, and it is probably the short BoM books (Enos,
Jarom, Omni, Words of Mormon) differing from the long ones rather than length per se
— but as reported, the BoM number is not a stable quantity and should not be used as
the middle rung of a "memorization gradient."

### 2.2 Claim 2 (layer sandwich) — reproducible only on `reap_score`, and it inverts on routing

This one needs the most attention because the sandwich is the interpretive spine of
the writeup.

Computing per-layer top-20 Jaccard from **`expert_frequencies`** — i.e. from which
experts the model actually routes tokens to — Bible vs Christian:

| L | J(bible,christian) |
|---|---|
| 0 | **0.905** |
| 1 | 0.600 |
| 2 | 0.739 |
| 3 | 0.538 |
| 5–41 | 0.05 – 0.43 (low, flat, noisy) |
| 42 | **0.600** |

That is the *opposite* of your claim of J≤0.03 at L0–2. On the routing channel the
early layers are the most corpus-invariant part of the whole stack, and L42 is also
high. There is no surface-form/semantics/register sandwich; there is a shared
backbone at the two ends and divergence in the middle.

Computing the same thing on **`reap_score`** reproduces your numbers:

| L | J on reap_score | your claim |
|---|---|---|
| 0 | 0.026 | ≤0.03 ✓ |
| 1 | 0.026 | ≤0.03 ✓ |
| 2 | 0.000 | ≤0.03 ✓ |
| 3 | 0.600 | 0.54–0.74 ✓ |
| 4 | 0.481 | ✓ |
| 6 | 0.481 | ✓ |
| 19 | 0.481 | ✓ |
| 39 | 0.143 | 0.11–0.14 ✓ |
| 41 | 0.212 | ~ |
| 42 | 0.143 | 0.11–0.14 ✓ |

So the sandwich is a statement about `reap_score`, not about routing. And
`reap_score` cannot support it, because of how it is defined in
`observe_religious.py:96-100`:

```python
reap = torch.where(frequencies > 0, reap_sum / frequencies.clamp_min(1), 0)
```

It is a **per-firing mean**. An expert hit once with a large activation norm
outranks an expert hit 400,000 times. Taking the top-20 by that quantity selects
for rare experts, not important ones. Concretely, for one 16,384-token Christian
record (98,304 routing slots at L42), the top-20 experts by `reap_score` have
frequencies:

`[25, 232, 398, 1105, 392, 33, 173, 1635, 613, 1282, 29, 2195, 888, 274, 31, 3187, 1835, 405, 98, 1907]`

Five of the top twenty fired fewer than 35 times out of 98,304 slots. Overlap with
the top-20 by frequency is 6/20 at L42 and 7/20 at L2. The J=0.000 at L2 is not two
corpora using disjoint machinery; it is two independent draws from the noise floor of
a mean-over-tiny-denominators statistic.

Fix: either weight by frequency (use `reap_sum` directly, or `reap_score × frequency`,
which is what REAP saliency actually means as a pruning criterion), or apply a
minimum-firing threshold before ranking. Then recompute the sandwich. I expect it to
change substantially. As it stands, both the "L0–2 surface form" and the "L39–42
voice/register" bands are unsupported, and the routing data says the opposite about
L0–2.

### 2.3 Claim 3 (effective-expert count) — pooling artifact

Your figures (Gita 26 < Qur'an 43 < Bible 65 < Christian 111) reproduce exactly, but
only when entropy is computed on the **corpus-pooled** L40 histogram. Computed
per-sample and then averaged:

| corpus | pooled exp(H) | per-sample mean | median sample length |
|---|---|---|---|
| gita | 26.3 | 24.3 | 1,432 |
| dhamma | 40.6 | 36.5 | 564 |
| tao | 49.1 | 37.4 | 162 |
| upanishads | 39.7 | 38.7 | 4,995 |
| quran | 43.2 | 39.5 | 1,241 |
| bible | 64.8 | 54.1 | 825 |
| bofm | 60.3 | 56.3 | 15,977 |
| analects | 62.5 | 58.1 | 2,102 |
| christian | **111.1** | **70.1** | 16,384 |

Christian collapses from 111 to 70. Pooling conflates within-sample expert diversity
with between-sample heterogeneity, and the Christian corpus is 1,267 windows drawn
from 3,562 different books — it is heterogeneous by construction. The "111" measures
how varied your book selection was, not how unpredictable the text is.

Two further problems. (a) Plug-in entropy is negatively biased at small n, and your
sample lengths differ by 100× (162 to 16,384 tokens), so the estimator itself is
ordering the corpora. (b) On the per-sample numbers, Analects (58.1) outranks Bible
(54.1) and BoM (56.3) ≈ Bible — the "predictability" ordering does not survive.

What *does* survive: Gita (24.3) < Qur'an (39.5) < Bible (54.1) holds despite the
Bible having the *shortest* samples of the three, which is the direction the length
bias works against. That sub-claim is real. The Christian rung is not. Drop the
pooled numbers or replace them with a length-matched, bias-corrected estimator
(Chao-Shen or Miller-Madow).

### 2.4 Claim 5 (permutation ruled out) — right conclusion, wrong argument, moved goalpost

The conclusion is correct: e164's zero is not a TP-shard bookkeeping bug. But
`exp8_sorted_freq.py` checks a channel that was never at risk, and misses the one
that was.

From `observe_religious.py:283` and the comment at :299-302, `frequencies` is
`torch.bincount(indices.flatten())` where `indices` comes from the **replicated**
gate over all 256 experts, and is explicitly *not* all-reduced. A per-shard
permutation is structurally incapable of touching `expert_frequencies`. So Exp 8's
premise ("if shapes match → permutation bug, investigate TP-2 shard mapping") was
never applicable to the frequency channel.

The channels that *are* built from the sharded loop over
`range(self.experts_start_idx, self.experts_end_idx)` and then all-reduced are
`reap_sum` and `activation_sum` — i.e. `reap_score` and `activation_norms`. A
mis-mapped `experts_start_idx` would corrupt exactly those, silently, while leaving
frequencies pristine. That is the check you needed and did not run. It matters
because §2.2 shows your headline layer-sandwich figure is computed on `reap_score`.

Separately: `EXPERIMENTS.md` Exp 8 pre-registers "If shapes match → permutation bug."
You got r=0.9902, which is a match, and the verdict block in
`analysis_all/exp8_sorted_freq_results.txt` then overrides the rule post hoc
("r=0.99 on sorted shapes reflects the universal heavy-tail routing profile, not a
bug"). That override is substantively correct — sorted heavy-tail histograms
correlate at ~0.99 between any two corpora, so the rule was badly specified — but
rewriting a pre-registered decision rule after seeing the result is exactly what a
reviewer will flag. Say plainly that the rule was wrong, rather than reporting it as
a passed check.

### 2.5 Claim 6 — wrong against your own file

You claim "bible↔christian lowest (0.33)." From `jac_matrix.json`:
`"bible|christian": 0.326`, but `"tao|christian": 0.3`. Tao↔Christian is the lowest
pairwise value in the matrix. Bible↔BoM = 0.527 as the highest is correct.

Also worth noting from that same file: `upanishads|christian` = 0.477 is the *second
highest* Christian pairing, above `bofm|christian` = 0.436 and far above
`bible|christian` = 0.326. If these Jaccards tracked doctrinal or traditional
affinity at all, that ordering would be inexplicable. It is consistent with
`robustness_checks.txt`'s own conclusion that the core overlap is tradition-agnostic
— which is a fine finding, but it argues against reading any of the pairwise numbers
as semantic.

### 2.6 Claim 4 (logit lens) — thin, and the framing overstates it

`bible_jlens.jsonl` contains **3 records**. The entire claim rests on one token
position in one sample.

Beyond the untuned-lens caveat you already acknowledge, two structural issues.
`jlens_dsv4.py:110` reduces every layer's hidden state using
`model.layers[0].hc_head` — layer 0's hyper-connection reduction — and then applies
the final `RMSNorm` and `lm_head`. Reading a mid-stack 4-way hyper-connection state
through layer 0's reduction and the *final* norm is a readout path the model never
uses at layer 30. Confidence numbers from it are not calibrated in any sense, and
"76.7%" reads as far more precise than the method can support.

More basically: Genesis 1:2 is among the most-quoted sentences in English. A model
predicting " Spirit" after "And the" in that context by layer 30 is a memorization
result, and an unsurprising one. It is not evidence about where semantic content
becomes linearly decodable, because there is no contrast condition — no unmemorized
control sentence with matched syntax, no comparison to the same clause in a
paraphrase. Either add that contrast or demote this to an illustrative figure.

---

## 3. Two harness issues to check before anything else

**3.1 `gate_weights` may not be the routing score.** `observe_religious.py:262`:

```python
gate_affinity = logits.softmax(dim=-1).mean(dim=0)
```

This is computed as softmax *unconditionally*, immediately before the code branches
on `gate.score_func` for softmax / sigmoid / softplus. I confirmed against the data
that the recorded vector sums to 1.000000 at L0, L20, L42, so it is indeed a softmax
mean. If `config.json` has `score_func: "sigmoid"` — the DeepSeek-V3 default, and the
`gate.bias` handling on the next lines is V3's aux-loss-free load-balancing bias,
which strongly suggests V3 lineage — then `gate_weights[256]` is **not** the quantity
the router used, and any analysis reading that field is reading a different function
of the same logits. Frequencies and `reap_score` are unaffected (they use
`normalized_weights`, which is correct). One-line check against your `config.json`.

**3.2 The bigger one: group-limited routing may be missing.** `observe_religious.py:277`:

```python
indices = selection_scores.topk(gate.topk, dim=-1)[1]
```

DeepSeek-V3's `Gate.forward` does **not** do a plain top-k. It reshapes scores into
`n_groups`, takes the top-`topk_groups` groups by their top-2 sum, masks the rest to
`-inf`, and only then takes the final top-k. Your `observed_moe_forward` is a
from-scratch reimplementation that replaces `MoE.forward` wholesale
(`DSV4.MoE.forward = observed_moe_forward`), and I see no group masking in it.

If `source-inference/model.py` retains V3's group-limited routing, then this harness
is routing to a *different expert set than the model actually uses*, and — because
`y` is computed from those same indices — every downstream layer is running on
off-distribution activations. That would not be a caveat; it would invalidate the
entire dataset. I could not check this because `source-inference/model.py` lives on
the remote node and is not in this directory.

**Diff `observed_moe_forward` against the real `Gate.forward` and `MoE.forward`, line
by line, before publishing anything.** If `n_groups`/`topk_groups` are present in
`config.json`, stop and re-run. This is a ten-minute check that gates everything
else, and I would not sign off on any result until it is done.

(Two smaller notes. `append_fsynced` at line ~490 is called by **both** ranks, not
guarded by `rank == 0` — only the logging is. If both ranks ever share a filesystem
path you would get interleaved duplicate records. I found no duplicate keys in
either file, so this did not bite, but it is a live hazard for the queued runs. And
`sparse_attn_pytorch` is a hand-written replacement for the tilelang kernel with no
numerical equivalence test recorded anywhere I could find; a `max|Δ|` check against
the kernel on one sample, on a machine where the kernel runs, would be worth having
in the appendix.)

---

## 4. Non-obvious corpus check that came back clean

I checked whether the Christian literature corpus leaks scripture into the comparison
arm — since sample `chr_000017` is literally the Book of Mormon, I expected worse.
Verbatim probes across all 1,267 Christian samples:

- "In the beginning God created the heaven and the earth" → 3/1267
- "For God so loved the world, that he gave his only begotten Son" → 0/1267
- "The LORD is my shepherd; I shall not want" → 0/1267
- "I, Nephi, having been born of goodly parents" → 1/1267
- Samples with heavy KJV register (>2 "unto" per 1k tokens) → 16/1267

Leakage is negligible. The Christian arm is a genuinely independent corpus. Worth
stating explicitly in the writeup — it is a real check and it passed.

---

## 5. The single most valuable next experiment

Not any of the ten in `EXPERIMENTS.md` as written. **Exp 2 (the e164 context dump),
re-scoped as a digit-controlled ablation, and run first.**

Concretely:

1. **Look at the feature.** Dump the top-500 e164 firing contexts with ±20 tokens and
   decode them. You have never looked at this feature directly, which is how a
   corpus artifact survived this long. My prediction: the firing tokens are numerals,
   footnote markers, verse references, page numbers, and roman numerals. This is
   cheap — the routing indices are already in your JSONL for aggregate counts; you
   need one re-run with per-token capture (`--raw-budget-tokens` already exists in
   the harness).

2. **Run the minimal-pair test.** Take one Bible chapter. Produce three versions:
   (a) as-is, digit-free; (b) with verse numbers reinserted in `N:M` form — *the text
   `prepare_corpus.py` threw away*; (c) with arbitrary non-verse numerals inserted at
   matched positions and matched density. Same content, same length, same register,
   same memorization status. If e164 fires on (b) and (c) but not (a), it is a numeral
   feature and the memorization story is finished. If it fires on (b) but not (c),
   it is a *citation/reference-structure* feature — which would actually be
   interesting and publishable. If it fires on none, I am wrong and you have
   something.

   This is a handful of short samples. It is a sub-hour run and it is strictly more
   decisive than Exp 1 (Genesis multi-translation), because the multi-translation
   design varies register *and* digits *and* memorization together and cannot separate
   them.

3. Only if (2) survives, proceed to Exp 1 with digit density explicitly matched
   across all six translations.

I would deprioritize Exp 9 (answered, §2.1), Exp 8 (checked the wrong channel,
§2.4), and Exps 5/6 (Jesus vs Lucifer, Moloch/Saturn) entirely for now. Those are
Wikipedia-derived corpora, which are extremely digit-dense — infoboxes, dates,
citation markers, reference numbers — and given §1 they will light up e164 and every
expert correlated with it, producing findings that look theological and are
orthographic. Running them before the digit question is settled will generate
confident conclusions that are wrong. Exp 3 (secular null) becomes much more valuable
if you *stratify it by digit density* rather than by topic.

The right general fix: add digit density, punctuation density, mean sentence length,
and type-token ratio as covariates to every corpus comparison, and report expert
contrasts as partial effects after controlling for them. Every current claim is an
unadjusted marginal.

---

## 6. What is genuinely novel and publishable

Strip out the theology and there is real work here.

**Strongest: the harness and the dataset.** A read-only, fail-closed
(`freq_sum == seqlen × topk` asserted per layer per record), fsynced, resumable
observation rig for full per-layer × per-expert routing on a 43-layer / 256-expert
MoE, running TP2 on consumer-class GB10 hardware with pure-PyTorch replacements for
both the tilelang sparse-attention kernel and the Hadamard transform — that is a
genuine engineering contribution, and the OOM-avoidance work in `load_incremental`
(incremental safetensors load with batched `POSIX_FADV_DONTNEED` page-cache eviction)
solves a problem people actually hit. Nobody has published a routing dataset at this
granularity for a model this size on this hardware class. Release the harness and the
aggregate tables. That alone is worth a writeup.

**Second, and this is the real scientific finding you have in hand:** a small set of
L42 experts (e164, e27, e68, e171, e4, and ~29 more at weaker suppression) are
near-perfectly gated by an orthographic surface property, at the *last* layer of the
network. That is the interesting part, and it is more interesting than what you
claimed. The prior expectation from the interpretability literature is that surface
features are handled early and late layers work in an abstract, task-oriented space.
You have a clean counterexample: a top-layer expert whose firing is predicted by
digit density across four orders of magnitude, monotonically, within a
length-controlled corpus. Frame it as "MoE routers maintain surface-form-conditioned
specialists at the final layer" and it stands on its own, with a clean null (256
experts, ranked) and a clean control (within-corpus digit deciles). Both of which
I have handed you above.

**Third, worth a paragraph:** the tradition-agnostic backbone in
`robustness_checks.txt` — bible↔bofm 0.539 ≈ bofm↔quran 0.544 ≈ bible↔quran 0.525 —
combined with `upanishads|christian` (0.477) > `bofm|christian` (0.436) >
`bible|christian` (0.326). A negative result, honestly reported: routing overlap
between religious corpora carries no information about doctrinal or traditional
relatedness. That is worth saying out loud, and it is the kind of null that saves
other people time.

**What is not publishable as it stands:** the "not-memorized-scripture expert" (§1),
the layer sandwich (§2.2), the effective-expert predictability ordering (§2.3), and
the logit-lens confidence figure (§2.6).

---

## 7. Summary scorecard

| # | Claim | Verdict |
|---|---|---|
| 1 | e164 = "not-memorized-scripture" expert | **Numbers reproduce exactly; interpretation refuted.** Digit-density confound explains ~99.9% of it. Zero-digit Christian control: 4.9/M vs corpus 4569.7/M. Also not a singleton — e27 is a twin, e68 is more extreme. |
| 2 | Layer sandwich (L0–2 / L3–6,19 / L39–42) | **Artifact of the `reap_score` channel.** Inverts on `expert_frequencies` (L0=0.905, L42=0.600). `reap_score` top-20 is dominated by experts firing <35 times in 98,304 slots. |
| 3 | Effective-expert count tracks predictability | **Pooling artifact.** Christian 111 → 70 per-sample; ordering breaks (Analects > Bible). Gita < Qur'an < Bible sub-claim survives. |
| 4 | Logit lens "Spirit" 76.7% @ L30 | **Too thin.** n=3 records, one token, uncalibrated readout path, no contrast condition. |
| 5 | Permutation confound ruled out | **Right answer, wrong argument.** Frequencies were never at risk by construction. `reap_score`/`activation_norms` *are* at risk and were not checked. Pre-registered decision rule was overridden post hoc. |
| 6 | Bible↔BoM highest, bible↔christian lowest | **Half wrong.** BoM highest ✓ (0.527). Lowest is tao↔christian (0.300), not bible↔christian (0.326). |
| — | Position/length confound (your Exp 9) | **Already dead, in your favour.** Length-matched [600,1500): Bible 714,242 tok → 0; Qur'an 31,484 tok → 4383/M. But BoM has an unreported 340× internal length swing. |
| — | Corpus leakage | **Clean.** 3/1267 Christian samples contain Gen 1:1; the rest of the probes are 0. |
| — | Harness correctness | **Unverified and gating.** Group-limited routing may be missing from the reimplemented gate (§3.2). Check before publishing anything. |

The measurement infrastructure is good and the data is real — I reproduced your
headline numbers to the digit from raw JSONL, which is more than most studies at this
stage would survive. The problem is that every comparison is an unadjusted marginal
across corpora that differ in more ways than the one you are attributing the
difference to. Fix the corpus controls, verify the gate against the real model, and
the surface-form-specialist-at-the-final-layer result is a genuinely good paper.
