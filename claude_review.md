I read the data rather than the writeup. Several of your surviving claims do not survive, one of your retracted intuitions is partly right for a different reason, and there is a bookkeeping error in `analysis/robustness_checks.txt`. Everything below is computed from `full_obs.jsonl`, `christian_obs.jsonl`, `core_agg.json`, `corpus/samples/*.jsonl` and `jlens_output/*.jsonl`.

---

## Q1. Does anything still support a religion-specific claim?

**No. Not one thing.** Strictly: zero of your surviving observations distinguish religion from text format.

I checked the strongest candidate — the "shared scriptural backbone." Split-half within-corpus overlap on L42 top-20 is 18–20/20 (the ceiling). Between-corpus it runs 10–17/20, and it **does not organize by tradition**: Bible~Qur'an is 14/20, but Tao~Dhammapada is 17/20 and Qur'an~Tao is 16/20. Bible~Christian-literature (15) equals Bible~Book-of-Mormon (15) equals BoM~Dhammapada (15). If religion were a routing category, Abrahamic pairs would sit above Abrahamic–Dharmic pairs. They don't. The backbone is real; its structure is not religious.

The Jacobians say the same thing louder: across all 8 traditions, L0 norms are 1015–1388 and L42 norms are 221–531. That's a ±10% spread with n=11 records each. There is no tradition signal in that probe at all.

## Q2. Hypotheses

**H1 — endorse, and extend further than you have.** e164 is a digit expert; within the Christian corpus alone (1,267 records, same genre, digit density varying), digit-token fraction explains R²=0.77 of e164's per-record rate, and the lowest-digit decile of Christian records (n=101, mean digit fraction 0.00009) fires it at **31/M** versus a corpus mean of 4,552/M. Settled. Two corrections:

- The cluster is bigger than 29. **54 experts** have within-Christian digit R² > 0.5; **184** have R² > 0.3.
- **e68 is not in it** (R²=0.01). You've mis-assigned it. Don't dump it with e164/e27 in Exp 11.

**H2 — endorse, and it's stronger than you think.** See Q1 and the finding in Q3.

**H3 — reject; the sign is backwards, and the headline ordering is an artifact.** Two problems.

First, window length. Your Bible windows are ~825 tokens; Christian windows are 16,384. Effective-expert-count is an entropy statistic and grows with sample size. Rarefying every record to a common draw budget at L40:

```
budget    bible    quran   christian
  1200     51.0     38.1        52.7
  2400     53.3     40.6        55.2
  4800     54.9      -          56.6
 19200      -        -          57.7
```

Bible and Christian literature are within ~2 units at every matched budget. Your reported 65 vs 111 is between-document heterogeneity (1,267 different books vs one book), and your per-sample 54 vs 70 is the length artifact. **"Bible 65 < Christian 111" carries no information about predictability.** The low end survives cleanly: at matched budget, Gita 23.8 < Dhamma 36.3 ≈ Tao 37.4 < Qur'an 38.9 << Bible 53.8 ≈ BoM 54.8 ≈ Analects 56.8. (Small-N estimator bias is only ~2–3% even at 5,280 draws, so that part is fine.)

Second, and worse: I built an *independent* predictability measure from your own lens files — top-1 agreement between the layer-42 lens readout and the actual next token, aggregated over all 80 records × 65 positions. Against matched-budget effK, the correlation is **positive**: Pearson +0.47, Spearman +0.48 (+0.59 / +0.54 dropping the n=3 Upanishads). H3 predicts negative. n=8, so this isn't significant either way — but it gives H3 exactly zero support and the wrong sign. Drop the surprisal framing. Call it what it measures: routing concentration.

**H4 — restate.** "Tradition-agnostic backbone" is right but under-claimed and mis-framed: it's a *language* backbone, not a scripture backbone, and you can't say which without Exp 3. Also, "specialists are thin and late-layer" is false — see below, the biggest specialist effects I found are at L4, L18–L24, L29–L33.

**H5 — endorse as the null you should be trying to reject, and it currently stands.**

**Add H6, which is where your actual finding is.** There exists a large set of experts whose firing is digit-independent, length-independent, and splits the corpora as **{Bible, Book of Mormon, Tao, Gita, Dhammapada, Analects} ≈ 0** versus **{Christian prose, Upanishads, Qur'an} high**. Rates per million, low-digit Christian slice vs everything:

```
  L    e  chr_lowd   bible   bofm  quran    tao   gita dhamma analects upanishads
 22  105     31084       0    109   6611    237     29     46        0      32053
 30  198     90595       4     81   3816    349    103     71      137      28393
 32  254     19935       0     11   7192    241      0      0        0      37061
 21   42     32524       1     13   3266     65    117      0        0      29187
 39  108     14922       0     11   2112    152     43      0        0      29258
 20  163     13790       0     22   6436     96     57     70        0      32492
 23  113     50964       7    223  13151    465    134      0        0      38941
 41  147     26090      13     13  14284      -      -      -        -     108075
```

These are 1,000× larger than e164 ever was, and they are not digit artifacts (digit R² 0.00–0.15). Critically, **Book of Mormon windows are 16,384 tokens — the same as Christian literature — and BoM is ~0.** Length is dead as an explanation. Your e164 story died of digits; this one doesn't.

What separates the two groups is not theology (it splits Christian scripture from Christian commentary, and groups the Upanishads with Puritan divines). The obvious reading is **bare verse-text vs. discursive prose with editorial apparatus** — the Rodwell Qur'an and a scholarly Upanishads edition carry introductions, footnotes and transliteration; the KJV, BoM, Tao, Gita, Dhammapada and Analects as you prepared them are stripped verse. That's H2 again, one level up from digits. But it is a real, large, unexplained routing axis, and it is the paper.

## Q3. The correct narrative

Three findings and a methodological one, in this order:

> We instrumented MoE routing over 22M tokens of religious text and found that **the model does not route by religion**. What look like tradition-specific circuits are, on inspection, responses to document *format*. We demonstrate this twice at increasing depth. First, an expert that fires exactly zero times across 1.05M KJV tokens turns out to be one of 54 digit-density experts — the KJV happened to be the only zero-digit corpus in the set (our pipeline strips verse numbers). Second, and not reducible to digits, we find a large expert population (L4–L41) that separates bare verse-text from discursive prose, cutting *across* traditions: it groups the KJV with the Tao Te Ching and the Book of Mormon on one side, and Puritan commentary with the Upanishads and the Rodwell Qur'an on the other. Third, routing concentration (effective expert count) differs by corpus but does not track predictability — measured independently by lens next-token agreement, the correlation is if anything positive. Methodologically: at 43×256 routing cells, exact-zero counts and extreme cross-corpus ratios are cheap and almost always confound artifacts; we report the two we published and retracted, and give a digit-regression protocol for screening the rest.

That is a better paper than the one you set out to write, and it is honest. The negative result about religion is the contribution; the format axis is the mechanism. "We found a digit detector and a predictability proxy" is *not* the whole story — but only because of H6, and only if you kill the register confound.

## Q4. Experiments, ranked by decisiveness per GPU-hour

1. **Exp 4 (within-document quotation switch) — retargeted to the H6 cluster, not e164.** Promote to #1. Christian books quoting the KJV verbatim give you same document, same 16k window, same digit density, same position band; the only variable is verse-text vs. commentary. If L22 e105 / L30 e198 / L33 e40 / L41 e147 switch off inside quotation spans, H6 is proven with no cross-corpus confound at all. This is the best figure you will get.
2. **Exp 1 (multi-translation) — promote.** You verified all five translations at 0.000% digits, so it's now a clean register test with content held constant. Run the H6 cluster on it, not e164. BBE (modern, 850-word vocabulary) vs KJV is precisely the register contrast. Cheap.
3. **Exp 3 (secular null) — keep at high, but change the design.** Stratify by digit density *and* by verse/prose format, and **include secular verse** (public-domain poetry, digit-free). If Milton and Wordsworth land on the Bible side of the H6 cluster, the axis is prosody/lineation and religion is entirely out. Without secular verse this experiment cannot distinguish "verse" from "scripture."
4. **Exp 11 (context dump) — keep, retarget.** Dump L22 e105, L30 e198, L33 e40, L41 e147 and e68. Drop e164/e27 — the regression already answered them, and you'd burn the run confirming what you know.
5. **Exp 12 (digit minimal pairs) — keep, demote to #5.** Sub-hour, so run it, but it now only settles a sub-question (citation structure vs. bare numeral) about a confound you've already characterized. Its real value is as a published negative control.
6. **Residual-norm-normalized Jacobian re-run.** Cheap, and mandatory before any Jacobian claim ships (see Q6).
7. **Covariate regression on existing records — no GPU, do it today.** I've effectively started it; finish it with punctuation%, mean sentence length, TTR, and a verse/prose indicator.

**ADD: an ablation.** Everything you have is correlational. Zero the H6 cluster and measure per-token loss delta on KJV vs. Christian prose. If loss rises on prose and not on scripture, you have a causal claim instead of a routing correlation. That is what converts this from an observation log into a result.

**CUT: the theology run** (Jesus/Lucifer/Moloch/Saturn, 1,090 records). It's Wikipedia-derived and therefore digit-dense and apparatus-heavy — the exact confound that just ate two of your headlines — and topic is confounded with article length, genre and editor conventions. There is no hypothesis it can decide that H6 doesn't already explain more cheaply. Defer it indefinitely.

**CUT: Exps 5/6** for the same reason, as you've already flagged.

## Q5. The e34/e33 audit

**L41 e34 is dead. It is a digit expert.** Within-Christian digit R² = 0.72; linear extrapolation to zero digits gives −125/M; the empirical low-digit Christian decile fires it at **57/M** against a 5,114/M corpus mean. And the corpus profile refutes "Qur'an specialist" on its face: Dhammapada fires it at **25,983/M**, five times the Qur'an's 5,377/M. Dhammapada is your highest-digit corpus at 2.611% digit tokens; the Qur'an is 1.505%. It was never about the Qur'an. Retract it.

**L34 e33 is worse than dead — the number is wrong.** `robustness_checks.txt` reports "bible 2.7/M, dhamma 4358/M, ~1600×." Recomputed from `full_obs.jsonl`, L34 expert 33 is **bible 9,323/M, dhamma 4,505/M** — the Bible is *higher*, by 2×, in the opposite direction. The dhamma figure matches (4,505 vs 4,358, plausible rounding/weighting), so the Bible figure specifically is corrupt. I swept all 43×256 cells: **no (layer, expert) anywhere in the model** satisfies bible < 10/M and dhamma > 3,000/M except L41 e34, L42 e27, L4 e14 and L23 e181. Whatever produced that row has an indexing or join bug. Find it before you trust anything else that table produced.

**The audit protocol going forward**, for any specialist claim: (a) within-Christian OLS on digit fraction, report R²; (b) rate in the ≤10th-percentile digit slice, not a linear extrapolation; (c) the full 9-corpus profile, because "Bible vs X" hides that the effect is really "Dhammapada vs everything"; (d) a length-matched comparator — BoM at 16k is your free control; (e) split-half stability within corpus.

And retire the framing "e164 fires heavily on everything else." From `exp8_sorted_freq_results.txt`: Qur'an 1,180 observed vs 6,049 expected under proportional routing; Christian 93,265 vs 478,346 expected. e164 is **under**-used everywhere. It's a rare expert that the Bible happens to hit zero times. Relatedly, the Bible has **48 exact-zero (layer, expert) cells** across 11,008, four of them at L42 (experts 4, 27, 164, 171). An exact zero is not the miracle the writeup implies.

## Q6. The lens

**Don't de-emphasize it — you're sitting on the cleanest result in the study and you haven't computed it.** Aggregate top-1 agreement between the layer-ℓ readout and the actual next token, over all 5,090 position-records:

```
L0–L18: ~1.0–1.5%   (flat)
L19:     2.8%       (discrete step)
L20–L26: ~2.8%
L30:     4.1%
L34:     8.0%
L37:    24.1%
L39:    43.8%
L40:    51.7%
L41:    61.7%
L42:    87.1%   (top-5: 96.0%)
```

That is a real prediction-emergence-by-depth curve with a discrete jump at L19 and 70% of the accuracy forming in the last five layers, and it's uncalibrated-lens-proof because top-1 rank agreement doesn't depend on the probabilities being meaningful. It reproduces per corpus (L42: Bible 96.7%, BoM 92.9%, Analects 92.3%, Dhamma 89.6%, Gita 86.2%, Tao 83.1%, Qur'an 75.1%, Upanishads 62.0%) and gives you the independent predictability axis that H3 needs.

It also lets me refute the Genesis claim harder than "cherry-picked." At `bible_jlens.jsonl` record 0, position 30, the L30 lens does read `' Spirit'` at 0.7668 — but at that same position the model's **actual layer-42 output is `'.'` at 0.9166**, with `Spirit` nowhere in the top 3. The lens didn't surface an early belief; it surfaced a token the model does not predict there. At L30 the lens agrees with the real next token 4.1% of the time, and at L10–L20 it emits confident nonsense (`' nalista'` 0.969, `' dével'` 0.979, `' TaxonID'`). Intermediate readouts on this model are unusable as probability claims. Rank-agreement curves: yes. Anything else: no.

## Q7. Integrity chain

Things I would not trust as written:

- **`analysis/robustness_checks.txt`.** One of its six rows is provably wrong (Q5). Regenerate the whole file from `full_obs.jsonl` and diff.
- **The word "Jacobian."** `jlens_dsv4.py:282-286` adds *the same* projection vector to the residual at *every* position, then runs the sub-network to the end. That's a uniform-shift sensitivity, not a Jacobian — it never probes per-position derivatives. Rename it.
- **The L0 Jacobian result.** L0 is 1015–1388 while L10/L20/L30 are ~450/~480/~470 — a step, then flat. Flatness across L10–L30 argues against "more layers = more accumulation," but the likely explanation is that ε=0.01 is a fixed *absolute* perturbation and the residual norm at layer 0 (raw embeddings) is much smaller than at depth, so it's a far larger *relative* perturbation. Record per-layer residual norms and renormalize before claiming anything. Also: with 8 traditions spanning ±10%, the honest headline is "no tradition effect."
- **Σfreq == tokens×6.** This is a good check and I believe it, but be clear about what it proves: bookkeeping consistency, not that logical expert index *i* is the checkpoint's expert *i* under TP2. Exp 8's cross-corpus ID stability shows the mapping is *stable*, which is what your relative claims need — but a fixed permutation applied identically in every run would be invisible to it. Say in the paper that expert IDs are stable labels, not verified checkpoint indices.
- **Upanishads, n=3.** It carries weight in the H6 table above, which is exactly why it needs to be either expanded or dropped, not footnoted.
- **Sample-geometry mismatch.** 1,189 × 825-token Bible windows vs 1,267 × 16,384-token Christian windows already destroyed the effK claim. Every per-sample statistic in the writeup needs a matched-budget or matched-length version before it ships.

---

## AGREED HYPOTHESES

Ones I'd sign:

1. **e164, e27, e34 and ~54 others are digit-density experts.** Within-Christian digit R² ≥ 0.5; low-digit slice rates of 31–57/M against corpus means of 4,100–5,100/M.
2. **There is a large, digit-independent, length-independent routing axis separating bare verse-text from discursive prose** (L4–L41; up to 90,595/M vs ~0). Its identity is not yet established — register, lineation, editorial apparatus and memorization are all still live. Not yet a finding about religion or about scripture.
3. **Routing concentration differs by corpus** — Gita ≈ 24 << Bible ≈ BoM ≈ Analects ≈ 54–57 at matched draw budget — **but it is not a predictability proxy**, and the Bible-vs-Christian-literature gap is a window-length artifact.
4. **There is a shared routing backbone across all nine corpora, and it is not religion-organized**: between-corpus L42 top-20 overlap (10–17/20 against an 18–20/20 within-corpus ceiling) shows no tradition-family clustering.
5. **Next-token prediction emerges late and sharply**: flat to L18, a discrete step at L19, and 70% of final top-1 accuracy forming after L37 (L42 = 87.1%).
6. **The model has no measurable religion-specific routing or input-sensitivity signature.** Null result, well supported, and the main contribution.

Ones I would not sign: any tradition-linked individual expert; anything derived from intermediate-layer lens probabilities; any Jacobian claim before ε-normalization; anything from the theology corpus as currently designed.
