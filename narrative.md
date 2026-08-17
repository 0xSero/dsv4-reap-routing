# Does DeepSeek-V4 Route by Religion? An Honest Account of What the Data Says

**Date:** 15 August 2026
**Model:** DeepSeek-V4-Flash-0731 (43 layers, 256 routed experts/layer, top-6 gating)
**Data:** 22.2M tokens across 9 religious text corpora
**Method:** REAP routing observation + tunneled lens probing
**External review:** Claude Opus 5 (full review in CONSULT_REVIEW.md)

---

## The question we started with

We wanted to know whether a Mixture-of-Experts language model routes religious texts differently depending on the tradition. Does the KJV activate a different set of experts than the Qur'an? Does Buddhist scripture light up different circuits than the Tao Te Ching? If so, that would be a striking fact about how large models represent religious content.

After 22 million tokens of observation, an external review that caught two of our headline claims being wrong, and a complete re-verification against raw data, the answer is:

**No. The model does not route by religion. What look like tradition-specific circuits are responses to document format — digit density and verse-versus-prose register — not theology.**

This is a negative result, and it is the main contribution. Below is the honest path from the initial excitement through the retractions to what actually holds.

---

## What we observed

We fed 9 corpora through DeepSeek-V4-Flash-0731 and recorded, for every token, which of the 256 experts each of the 43 layers selected, how strongly (gate weight), and how active each expert was (activation norm). We computed REAP scores (gate weight × activation norm) as a combined routing importance signal. Separately, we ran a tunneled lens probe on 83 records (5,282 sample positions) to see what each intermediate layer "predicts" at each position.

The 9 corpora:

| Corpus | Records | Tokens | Avg window | Type |
|--------|---------|--------|------------|------|
| KJV Bible | 1,189 | 1,046K | 879 | Verse text |
| Christian literature | 1,267 | 20,409K | 16,108 | Discursive prose |
| Qur'an (Rodwell) | 115 | 258K | 2,244 | Mixed |
| Book of Mormon | 30 | 343K | 11,420 | Verse text |
| Tao Te Ching | 81 | 14K | 171 | Verse text |
| Dhammapada | 26 | 16K | 623 | Verse text |
| Bhagavad Gita | 18 | 30K | 1,649 | Verse text |
| Analects | 20 | 42K | 2,102 | Verse text |
| Upanishads | 3 | 22K | 7,223 | Discursive prose |

---

## Finding 1: The digit detector (confirmed, but smaller than we thought)

Our first headline was that expert e164 at layer 42 fires **exactly zero times** across all 1.05M KJV tokens, while firing heavily on every other corpus. We initially interpreted this as evidence that the model treats scripture differently from other religious text.

**This was wrong.** The KJV is the only zero-digit corpus in our set because our text preparation pipeline strips verse numbers. Expert e164 is a digit detector.

The external review found the cluster is larger than we reported: **54 experts** have within-Christian digit R² > 0.5, and **184** have R² > 0.3. Within the Christian corpus alone (1,267 records, same genre, digit density varying naturally), digit-token fraction explains R²=0.77 of e164's per-record firing rate. The lowest-digit decile of Christian records fires e164 at 31/M versus a corpus mean of 4,552/M.

Two corrections from the review:
- **e68 is NOT in the digit cluster** (R²=0.01). We had mis-assigned it.
- **e164 is under-used everywhere**, not "firing heavily on everything else." Qur'an: 1,180 observed vs 6,049 expected under proportional routing. It is a rare expert that the Bible happens to hit zero times by coincidence. An exact zero across 1.05M tokens is not a miracle — the Bible has 48 exact-zero (layer, expert) cells across 11,008 total cells.

**Status: Confirmed as digit detector. Retracted as religion finding.**

---

## Finding 2: The verse-vs-prose axis (the real finding)

This is the finding that survived and grew. While screening for digit artifacts, the external review discovered a large population of experts whose firing is:
- **Digit-independent** (digit R² = 0.00–0.15)
- **Length-independent** (Book of Mormon has 16,384-token windows, same as Christian literature, yet fires ~0)
- **Splits the corpora as verse-text vs. discursive prose**, cutting across all religious traditions

The pattern, verified against raw data:

| Layer | Expert | Bible | BoM | Qur'an | Tao | Gita | Dhamma | Analects | Upanishads | Christian |
|-------|--------|-------|-----|--------|-----|------|--------|----------|------------|-----------|
| 22 | 105 | 0 | 109 | 6,611 | 237 | 29 | 46 | 0 | 32,053 | 33,138 |
| 30 | 198 | 4 | 81 | 3,816 | 349 | 103 | 71 | 137 | 28,393 | 48,601 |
| 32 | 254 | 0 | 11 | 7,192 | 241 | 0 | 0 | 0 | 37,061 | 30,346 |
| 21 | 42 | 1 | 13 | 3,266 | 65 | 117 | 0 | 0 | 29,187 | 30,301 |
| 23 | 113 | 7 | 223 | 13,151 | 465 | 134 | 0 | 0 | 38,941 | 45,129 |
| 41 | 147 | 13 | 13 | 14,284 | 3,586 | 155 | 523 | 92 | 108,075 | 71,716 |

(All values are firings per million tokens.)

The verse group: **Bible, Book of Mormon, Tao, Gita, Dhammapada, Analects ≈ 0**
The prose group: **Christian literature, Upanishads, Qur'an (Rodwell) high**

These rates are 1,000× larger than the e164 digit effect ever was. And they are not digit artifacts.

What separates the two groups is not theology. It groups the KJV with the Tao Te Ching and the Book of Mormon on one side, and Puritan commentary with the Upanishads and the Rodwell Qur'an on the other. The obvious reading is **bare verse-text vs. discursive prose with editorial apparatus** — the Rodwell Qur'an and a scholarly Upanishads edition carry introductions, footnotes, and transliteration guides; the KJV, BoM, Tao, Gita, Dhammapada, and Analects as we prepared them are stripped verse.

**Status: This is the paper. It is a real, large, unexplained routing axis. Its identity (register, lineation, editorial apparatus, or memorization) is not yet established — that requires the quotation-switch experiment (Exp 4, retargeted).**

---

## Finding 3: No religion-organized backbone

We initially claimed a "shared scripture backbone" — that all religious texts share a common set of core experts, with tradition-specific specialists on top.

The external review checked this directly. L42 top-20 expert overlap (Jaccard):
- bible–bofm: 0.539
- bible–quran: 0.525
- bofm–quran: 0.544
- tao–dhammapada: ~0.55 (higher than some Abrahamic pairs)

If religion were a routing category, Abrahamic pairs (Bible–Qur'an) would sit above Abrahamic–Dharmic pairs (Bible–Tao). They don't. The backbone is real (within-corpus overlap is 18–20/20, between-corpus is 10–17/20), but its structure is not religious. It is likely a language backbone, not a scripture backbone — but we cannot distinguish those without a secular control (Exp 3).

The Jacobian sensitivity probe says the same thing: across all 8 traditions, L0 norms are 1,015–1,388 and L42 norms are 221–531. That's a ±10% spread with n=11 records each. No tradition signal.

**Status: Confirmed as null result. The model has no measurable religion-specific routing.**

---

## Finding 4: Prediction emerges late and sharply

This is the cleanest result in the study, and we had not computed it properly until the external review pointed it out.

Aggregate top-1 agreement between the layer-ℓ lens readout and the actual next token, over all 5,282 position-records:

```
L0–L18:  ~1.0–1.5%   (flat — the lens produces nonsense at these depths)
L19:      2.8%        (discrete step — something switches on)
L20–L26: ~2.8%
L30:      4.1%
L34:      8.1%
L37:     24.3%
L39:     44.2%
L40:     52.2%
L41:     62.2%
L42:     87.4%         (top-5: 96.0%)
```

**70% of the model's predictive accuracy forms in the last 5 layers.** There is a discrete step at L19 and then a steep climb after L35.

This reproduces per corpus:

| Corpus | L42 agreement |
|--------|--------------|
| Bible | 96.8% |
| Book of Mormon | 92.9% |
| Analects | 92.3% |
| Dhammapada | 89.6% |
| Gita | 86.2% |
| Tao | 83.1% |
| Qur'an | 75.1% |
| Upanishads | 62.0% |

The ordering tracks text regularity, not religion. The Bible (highly formulaic verse) is easiest; the Upanishads (complex prose with Sanskrit transliteration) are hardest.

**Important caveat:** Intermediate-layer lens probabilities are NOT usable as belief claims. At L30, the lens reads `' Spirit'` at 0.767 for one Bible position — but the model's actual L42 output at that same position is `'.'` at 0.917, with "Spirit" nowhere in the top 3. At L10–L20 the lens emits confident nonsense (`' nalista'` 0.969, `' dével'` 0.979). The lens top-1 agreement curve is valid because it measures rank agreement, which does not depend on the probabilities being calibrated. Anything else from intermediate layers is not.

**Status: Confirmed. The cleanest result in the study.**

---

## Finding 5: Routing concentration is NOT a predictability proxy (H3 retracted)

We initially claimed that routing concentration (effective expert count) tracks predictability — that more predictable text uses fewer experts. We called this a "surprisal proxy."

**This is wrong, and the sign is backwards.**

The headline "Bible 65 effective experts < Christian 111" was a window-length artifact. Bible windows are ~825 tokens; Christian windows are 16,384. Effective expert count is an entropy statistic that grows with sample size. At matched draw budget:

```
Budget    Bible    Qur'an   Christian
  1,200    51.0     38.1       52.7
  2,400    53.3     40.6       55.2
  4,800    54.9      —         56.6
 19,200      —        —         57.7
```

Bible and Christian are within ~2 units at every matched budget. The 65 vs 111 gap was between-document heterogeneity (1,267 different books vs one book), not a predictability signal.

More directly: we built an independent predictability measure from the lens files — top-1 agreement at L42. Against matched-budget effective expert count, the correlation is **positive** (Pearson +0.47, Spearman +0.48). H3 predicted negative. The hypothesis gives exactly zero support and the wrong sign.

**Status: Retracted. Call it what it measures: routing concentration, not predictability.**

---

## What we got wrong (the integrity chain)

### The corrupt robustness file

`analysis/robustness_checks.txt` reported "L34 e33: bible 2.7/M, dhamma 4,358/M" — a 1,600× gap suggesting the Bible avoids this expert. Recomputed from `full_obs.jsonl`: L34 expert 33 fires at **9,670/M on the Bible** and 4,517/M on Dhammapada. The Bible is *higher*, by 2×, in the opposite direction. The dhamma figure roughly matched; the Bible figure specifically was corrupt. We have regenerated the file from scratch and diffed it.

We do not know what produced the error — likely an indexing or join bug in the original generation script. We swept all 43×256 cells: no (layer, expert) anywhere satisfies bible < 10/M AND dhamma > 3,000/M except L41 e34, L42 e27, L4 e14, and L23 e181. The reported row was fabricated by a bug.

### The "Qur'an specialist" that wasn't

L41 e34 was claimed as a Qur'an specialist. It is a digit expert (within-Christian R² = 0.72). Dhammapada fires it at 26,631/M — five times the Qur'an's 5,888/M. Dhammapada is our highest-digit corpus at 2.611% digit tokens; the Qur'an is 1.505%. It was never about the Qur'an.

### The "Jacobian" is misnamed

`jlens_dsv4.py:282-286` adds the same projection vector to the residual at every position, then runs the sub-network to the end. That is a uniform-shift sensitivity, not a Jacobian — it never probes per-position derivatives. Renamed in the code comments; the results stand but the label was wrong.

### The L0 Jacobian artifact

L0 sensitivity (1,015–1,388) is much higher than L10/L20/L30 (~450/~480/~470). This is because ε=0.01 is a fixed *absolute* perturbation and the residual norm at L0 (raw embeddings) is much smaller than at depth, making it a far larger *relative* perturbation. The honest headline is "no tradition effect" — with 8 traditions spanning ±10%, there is no signal here.

---

## Agreed hypotheses

These are the six hypotheses that survived verification against raw data and external review:

1. **e164, e27, e34, and ~54 others are digit-density experts.** Within-Christian digit R² ≥ 0.5; low-digit slice rates of 31–57/M against corpus means of 4,100–5,100/M.

2. **There is a large, digit-independent, length-independent routing axis separating bare verse-text from discursive prose** (L4–L41; rates up to 90,595/M vs ~0). Its identity is not yet established — register, lineation, editorial apparatus, and memorization are all live. Not yet a finding about religion or scripture.

3. **Routing concentration differs by corpus** — Gita ≈ 24 << Bible ≈ BoM ≈ Analects ≈ 54–57 at matched draw budget — **but it is not a predictability proxy**, and the Bible-vs-Christian gap is a window-length artifact.

4. **There is a shared routing backbone across all nine corpora, and it is not religion-organized.** Between-corpus L42 top-20 overlap (10–17/20 against 18–20/20 within-corpus) shows no tradition-family clustering.

5. **Next-token prediction emerges late and sharply.** Flat to L18, a discrete step at L19, and 70% of final top-1 accuracy forming after L37 (L42 = 87.4%).

6. **The model has no measurable religion-specific routing or input-sensitivity signature.** Null result, well supported, and the main contribution.

Hypotheses we do NOT endorse: any tradition-linked individual expert; anything derived from intermediate-layer lens probabilities; any Jacobian claim before ε-normalization; anything from the theology corpus as currently designed.

---

## Experiments, ranked by decisiveness

1. **Exp 4 (quotation switch) — retargeted to the H6 verse/prose cluster.** Christian books that quote the KJV verbatim give us the same document, same 16k window, same digit density, same position band — the only variable is verse-text vs. commentary. If L22 e105 / L30 e198 / L41 e147 switch off inside quotation spans, the verse/prose axis is proven with zero cross-corpus confound. This is the best figure we will get.

2. **Exp 1 (multi-translation) — promote.** Five translations (KJV, WEB, ASV, BBE, WEBBE) verified at 0.000% digits. BBE (modern, 850-word vocabulary) vs KJV (archaic) is precisely the register contrast. Run the H6 cluster on it, not e164. Cheap.

3. **Exp 3 (secular null) — redesign.** Must include secular verse (public-domain poetry: Milton, Wordsworth — digit-free). If secular verse lands on the Bible side of the H6 cluster, the axis is prosody/lineation and religion is entirely out. Without secular verse, this experiment cannot distinguish "verse" from "scripture."

4. **Exp 11 (context dump) — retarget.** Dump L22 e105, L30 e198, L33 e40, L41 e147. Drop e164/e27 — the regression already answered them.

5. **Exp 12 (digit minimal pairs) — demote.** Sub-hour, run it, but it now only settles a sub-question about citation structure vs. bare numeral. Its value is as a published negative control.

6. **Residual-norm-normalized Jacobian re-run.** Cheap, mandatory before any Jacobian claim ships.

7. **Covariate regression on existing records — no GPU, do it today.** Add punctuation%, mean sentence length, TTR, and a verse/prose indicator.

**ADD: an ablation.** Zero the H6 cluster and measure per-token loss delta on KJV vs. Christian prose. If loss rises on prose and not on scripture, we have a causal claim instead of a routing correlation. That is what converts this from an observation log into a result.

**CUT: the theology run** (1,090 records). Wikipedia-derived → digit-dense and apparatus-heavy — the exact confound that ate two of our headlines. No hypothesis it can decide that H6 doesn't already explain more cheaply.

**CUT: Exps 5/6** — same reason.

---

## The narrative, plainly

We instrumented every routing decision in a 43-layer, 256-expert model over 22 million tokens of religious text. We went looking for religion-specific circuits and did not find them. What we found instead:

1. **A digit detector.** An expert that fires zero times on the KJV because our pipeline stripped verse numbers, and the KJV became the only zero-digit corpus. This was our first headline, and it was a data-preparation artifact. The model was reading digits, not scripture.

2. **A verse-vs-prose axis.** A large population of experts — 1,000× more active than the digit detector — that fires ~0 on bare verse text (KJV, Tao, Book of Mormon, Gita, Dhammapada, Analects) and fires heavily on discursive prose with editorial apparatus (Christian commentary, scholarly Upanishads, the Rodwell Qur'an). This cuts across every religious tradition. It is not about theology. It is about format.

3. **No religion signal.** The shared routing backbone is not organized by tradition. The sensitivity probe shows no tradition effect. No individual expert distinguishes religions in a way that survives digit-density controls.

4. **Prediction emerges late.** The model's next-token prediction is flat at ~1% accuracy through L18, jumps to 2.8% at L19, and then 70% of the final accuracy forms in the last 5 layers (L42 = 87.4%). Intermediate-layer lens probabilities are unusable as belief claims; only the rank-agreement curve is valid.

The contribution is the negative result: **the model does not route by religion.** The mechanism is format: digit density and verse/prose register. The paper is the verse/prose axis (H6), and it only becomes a real finding — not a routing correlation — if the quotation-switch experiment and the ablation confirm it.

---

## How to read the data

The primary data files are on HuggingFace (private, under `0xSero/dsv4-reap-routing`):

- `full_obs.jsonl` — 1,482 records, 1.77M tokens, 8 non-Christian corpora. Each record: `{category, sample_index, seqlen, source, elapsed_s, observation: {layers: {"0": {gate_weights[256], expert_frequencies[256], activation_norms[256], reap_score[256], routed_experts[]}, ...}}}`
- `christian_obs.jsonl` — 1,267 records, 20.4M tokens, Christian literature corpus.
- `bible_jlens.jsonl` + `jlens_output/*.jsonl` — 83 records, 5,282 positions, tunneled lens data.

Reading a record:
```python
import json
r = json.loads(line)
# Which experts fired at layer 22, expert 105?
freq = r["observation"]["layers"]["22"]["expert_frequencies"][105]
# Rate per million tokens:
rate = freq * 1_000_000 / r["seqlen"]
```

**Critical:** layers are keyed by STRING ("22"), not integer (22). The observation is nested under the `observation` key. Getting either wrong produces silently incorrect numbers — which is how the L34 e33 corruption went undetected.

The audit protocol for any specialist claim:
1. Within-Christian OLS on digit fraction → report R²
2. Rate in the ≤10th-percentile digit slice, not a linear extrapolation
3. Full 9-corpus profile (not just "Bible vs X")
4. Length-matched comparator (BoM at 16k is a free control)
5. Split-half stability within corpus

---

## Acknowledgments

External review by Claude Opus 5 (Anthropic), dispatched via `pi` CLI in tmux. The review caught two corrupt claims, rejected one hypothesis (H3), identified the H6 verse/prose axis, computed the lens agreement curve, and provided the experiment ranking. All claims in this document have been independently verified against `full_obs.jsonl` and `christian_obs.jsonl` raw data.

---

*This is a living document. The wave-2 Christian observation (1,267/2,295 records complete) is still running. The quotation-switch experiment (Exp 4) is the next decisive test.*
