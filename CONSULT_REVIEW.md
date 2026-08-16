# Review request — DeepSeek-V4-Flash-0731 REAP routing interpretability study

You are asked to act as an external reviewer. Read ALL of the material below,
sanity-check the methodology and claims, and give: (1) your assessment of what
we actually found, (2) flaws/confounds we haven't killed, (3) the single most
valuable next experiment, (4) anything genuinely novel here worth publishing.

## What we did

Read-only observation of MoE expert routing in DeepSeek-V4-Flash-0731
(43 layers, 256 routed experts/layer, top-6, TP2 across two DGX Spark GB10
nodes). For each text sample (16,384-token windows) we record per layer:
gate_weights[256], activation_norms[256], reap_score[256] (= gate × act-norm),
routed_experts[], expert_frequencies[256]. Fail-closed: Σfreq == seqlen×6
asserted per layer per record; per-sample fsync; no weight edits.

Corpora: KJV Bible, Qur'an (Rodwell), Tao Te Ching, Bhagavad Gita, Dhammapada,
Book of Mormon, Analects, Upanishads (1,482 records); Christian literature
(1,267 records / 20.4M tokens from 3,562 Gutenberg books); wave-2 (2,295 more
books) running; theology corpus (~113M tokens: Jesus, Lucifer, Judaism,
Moloch, Saturn) scraped and queued.

## Files to read (all local, relative to this directory)

- wiki.html (site copy) or https://0xsero.github.io/dsv4-reap-routing/ — the full writeup. READ THIS FIRST.
- EXPERIMENTS.md — 10 prioritized experiments, 1 done
- analysis_all/exp8_sorted_freq_results.txt — permutation-confound check result
- analysis_all/*.csv, analysis_all/*.json — rankings, Jaccard matrix, aggregates
- code/observe_religious.py — the harness
- code/analyze_experts.py — the analysis
- code/run_jlens.py, code/jlens_dsv4.py — logit-lens/Jacobian probes

## Headline claims to sanity-check

1. L42 expert e164 fires exactly 0 times in 1,045,776 Bible tokens (expected
   ~24,510 under proportional routing) but ~4,572/M tokens on Qur'an,
   ~4,570/M on Christian doctrine, 157.6/M on Book of Mormon. Claimed: a
   "not-memorized-scripture" expert (memorization gradient, not topic).
2. Layer sandwich: Bible↔Christian-literature Jaccard on per-layer top-20
   expert sets: J≤0.03 at L0–2 (surface form), 0.54–0.74 at L3–6/19
   (semantics), 0.11–0.14 at L39–42 (voice/register).
3. Effective-expert count at L40 tracks predictability: Gita 26 < Qur'an 43
   < Bible 65 < Christian doctrine 111.
4. Logit lens: Genesis 1:2 decodes "Spirit" at 76.7% confidence by layer 30
   (via hc_head → RMSNorm → lm_head readout). Caveat acknowledged: untuned lens.
5. Permutation confound ruled out (exp8): 15/20 top L42 experts share IDs
   across Bible↔Qur'an↔Christian campaigns, so expert-ID mapping is consistent;
   e164 exact-zero is real, not a TP-shard bookkeeping bug.
6. Bible↔BoM highest pairwise Jaccard (0.53); bible↔christian lowest (0.33).

## Known caveats we already track

Position/length confound (Bible chapters ~880 tokens vs 16k windows) untested
until Exp 9; entropy-explanation for e164 untested (Exp 7); no secular null
(Exp 3); REAP is correlational (no ablations); Jacobians are 16-direction
finite differences; Qur'an/Gita are translation-English.

Be skeptical and specific. Cite which file/number you are checking.
