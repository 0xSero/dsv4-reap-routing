# EXPERIMENTS — DeepSeek-V4-Flash-0731 Interpretability

## Running experiments

These experiments are designed to run autonomously when GPU nodes are free,
prioritized by expected scientific value. Each experiment reuses the existing
observation harness (`observe_religious.py`) or J-lens harness (`run_jlens.py`).

---

## Experiment 1: Genesis 1 Multi-Translation Register Test
**Priority: CRITICAL — the killer experiment**

Run the same content (Genesis 1) in multiple English translations that vary
in register but hold meaning constant. If e164 fires on modern translations but
NOT the KJV, we have a within-content proof that the feature is register/
memorization, not theology.

### Translations
- KJV (1611) — archaic, memorized verbatim in pretraining
- Douay-Rheims (1609) — archaic Catholic, slightly different wording
- Young's Literal Translation (1862) — literal, formal
- ESV (2001) — modern formal equivalence
- NIV (2011) — modern dynamic equivalence
- The Message (2002) — contemporary paraphrase

### Method
1. Prepare Genesis 1 (all 31 verses) in each translation as separate samples
2. Run full observation harness on each (they're short — single sample each)
3. Compare e164 and e34 activation frequencies across translations
4. Compare full routing profiles (per-layer top-20 Jaccard) across translations

### Expected outcome
If e164 fires on NIV/Message but not KJV → register/memorization confirmed.
If e164 fires on none → it's not register, it's something else about KJV text identity.
If e164 fires on all → it's content-driven, not register-driven.

---

## Experiment 2: e164 Firing Context Dump
**Priority: HIGH — settles half the debate**

Dump the 500 highest-gate contexts where e164 fires, with ±20 tokens of
surrounding text. We have never looked at the feature directly.

### Method
1. Modify observe_religious.py to capture, for layer 42 expert 164, the top-500
   gate-weight activations across all corpora, storing ±20 token context for each
2. Decode the context tokens back to text using the tokenizer
3. Manually inspect: what do the firing contexts have in common?

### Expected outcome
If firing contexts are all archaic-religious-English-not-KJV → register hypothesis confirmed.
If firing contexts share some other feature (entropy, position, topic) → alternative explanation.

---

## Experiment 3: Secular Null Baseline
**Priority: HIGH — makes all Jaccard numbers interpretable**

Run observation on non-religious English text (Wikipedia, arXiv abstracts, news)
to establish what the "backbone" expert overlap looks like for non-religious corpora.

### Method
1. Scrape ~5000 Wikipedia articles on secular topics (science, history, technology)
2. Scrape ~2000 arXiv abstracts (CS, physics, math)
3. Prepare as corpus/samples/secular_sel.jsonl
4. Run full observation harness
5. Compute L42 top-40 overlap: Wikipedia↔arXiv, Wikipedia↔Bible, arXiv↔Quran
6. If overlap is also ~19, the "scriptural backbone" is just the English backbone

### Expected outcome
If secular↔secular overlap ≈ 19 (same as religious↔religious) → backbone is
language-general, not religion-specific. Every Jaccard number needs reinterpreting.
If secular↔religious overlap << 19 → there IS a religion-specific backbone.

---

## Experiment 4: Within-Document KJV Quotation Switch
**Priority: MEDIUM — the best figure in the paper if it works**

Devotional books quote the KJV verbatim constantly. Find those quotation spans
and check whether e164 switches off mid-paragraph when the quotation starts
and back on when the author resumes.

### Method
1. From Christian literature corpus, find books with extensive KJV quotations
   (e.g., commentaries, sermons)
2. For each 16k sample, identify KJV quotation spans (regex match on verse
   citations or text matching known KJV passages)
3. Run observation with per-token routing capture
4. Plot e164 gate weight as a function of token position, marking quotation spans

### Expected outcome
If e164 turns off during KJV quotations and turns on for commentary → the most
controlled proof possible. Same document, same window, same position — the only
variable is whether the text is verbatim-KJV or not.

---

## Experiment 5: Jesus vs Lucifer Routing Comparison
**Priority: MEDIUM — novel theological-interpretability angle**

Compare routing profiles for texts about Jesus Christ vs texts about Lucifer/
the Devil. Do conceptually "opposed" theological figures route through the same
experts, different experts, or partially overlapping sets?

### Method
1. Use the theology corpus (Wikipedia articles about Jesus vs about Lucifer)
2. Run full observation on both subsets
3. Compare per-layer top-20 expert sets (Jaccard by layer)
4. Look for experts that fire strongly for one but not the other
5. Check if the L39-42 "voice/register" band treats them the same or differently

### Expected outcome
If Jesus and Lucifer articles route similarly → the model processes theological
content through shared infrastructure regardless of valence.
If they diverge in specific layers → the model has concept-specific routing,
which would be a striking finding.

---

## Experiment 6: Moloch / Saturn Worship Routing Analysis
**Priority: MEDIUM — ancient religion vs modern religion comparison**

Compare routing profiles for texts about ancient sacrificial religion (Moloch,
Canaanite religion, Saturn/Cronus worship) vs modern Abrahamic texts (Bible,
Quran). Does the model distinguish "ancient pagan" from "modern monotheistic"
at the routing level?

### Method
1. Use theology corpus subsets: moloch_* + saturn_* vs bible + quran samples
2. Run full observation on both
3. Compare per-layer expert profiles
4. Look for experts unique to ancient-religion texts
5. Check if e164 (the "not-memorized-scripture" expert) fires on ancient religion texts

### Expected outcome
If ancient religion texts activate e164 heavily (like Quran/Christian doctrine) →
e164 is "religious-but-not-memorized" broadly.
If ancient religion texts have distinct expert profiles → the model has
concept-level routing that distinguishes religious traditions.

---

## Experiment 7: Entropy Expert Regression
**Priority: MEDIUM — kills or confirms alternative explanation #3**

Regress per-token e164 firing on per-token loss/entropy, position, and register
features. If entropy alone explains e164 firing, the register story dissolves.

### Method
1. Run observation with per-token loss capture (compute NLL at each position)
2. For each token, record: e164 gate weight, e164 fired (yes/no), position in
   sequence, loss/entropy, register features (archaic markers, verse numbers)
3. Logistic regression: e164_fired ~ loss + position + register_features
4. If loss/entropy is the dominant predictor, e164 is an entropy expert

---

## Experiment 8: Sorted Frequency Distribution Check
**Priority: HIGH — must be done before publishing any e164 claim**

Sort the L42 frequency histograms for Bible and Quran and compare the sorted
distributions. If they match in shape but not in ID assignment, we have a
permutation bug, not a finding.

### Method
1. Extract L42 expert_frequencies[256] for all Bible samples and all Quran samples
2. Sort each frequency vector (descending)
3. Plot both sorted distributions on the same chart
4. If shapes match → permutation bug, investigate TP-2 shard mapping
5. If shapes differ → finding is real

---

## Experiment 9: Position/Length Confound Check
**Priority: HIGH — cheap and decisive**

Bible chapters average ~880 tokens; Christian literature is 16k-token windows.
If e164's firing rate rises with absolute position, "0 in the Bible" might mean
"the Bible corpus never reaches position 1500."

### Method
1. Re-window the Bible into concatenated 16k-token blocks (not per-chapter)
2. Run observation on the re-windowed Bible
3. Check if e164 now fires in the 16k Bible windows
4. If yes → position confound killed the original result
5. If no (still 0) → result hardened enormously

---

## Experiment 10: Causal Ablation of e164
**Priority: LOW-MEDIUM — converts correlation to causation**

Ablate e164 (force it out of top-6, renormalize the gate) and measure ΔNLL
per corpus. Then force-route it on KJV tokens and see what breaks.

### Method
1. Modify the MoE forward pass to exclude e164 from top-6 selection
2. Run generation/NLL computation on each corpus
3. Measure per-token NLL change vs baseline
4. Prediction: measurable damage on Quran and Christian literature, zero on KJV
5. Then reverse: force e164 into top-6 for KJV tokens, measure damage

---

## Execution order (when GPU time is available)

1. **Exp 8** (sorted freq check) — 5 min, no GPU needed if data exists
2. **Exp 9** (position confound) — 1-2 hours GPU
3. **Exp 1** (Genesis multi-translation) — 1-2 hours GPU, killer experiment
4. **Exp 3** (secular null) — 4-6 hours GPU + scraping
5. **Exp 2** (e164 context dump) — 2-3 hours GPU
6. **Exp 5** (Jesus vs Lucifer) — 4-6 hours GPU (after theology scraping)
7. **Exp 6** (Moloch/Saturn) — 4-6 hours GPU (after theology scraping)
8. **Exp 4** (quotation switch) — 2-3 hours GPU + text processing
9. **Exp 7** (entropy regression) — 2-3 hours GPU
10. **Exp 10** (causal ablation) — 4-6 hours GPU, requires code modification
