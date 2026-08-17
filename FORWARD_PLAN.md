# Forward Plan: resolving the H6 routing axis without recreating the original confounds

**Scope.** This is a design for the next experimental phase, not a claim that
any pending result has already been obtained.  The central question is now
mechanistic: what input property causes the pre-registered H6 experts to be
routed?  It is *not* whether a religion has an expert.  The current evidence
supports a large format-associated routing effect and a well-supported absence
of a detectable religion-organized effect; it does not yet identify the format
variable or establish that the H6 experts are necessary for prediction.

## 0. Rules that apply to every next experiment

### 0.1 Freeze the analysis contract before inspecting pending outputs

Create a small, versioned `analysis/h6_registry.csv` before analysing Exp 4.
It must record `layer`, `expert`, the data used for selection, the selection
rule, and its original verse/prose effect.  The six documented replication
anchors are:

| ID | Layer | Expert | status |
|---|---:|---:|---|
| H6-A1 | 21 | 42 | primary anchor |
| H6-A2 | 22 | 105 | primary anchor |
| H6-A3 | 23 | 113 | primary anchor |
| H6-A4 | 30 | 198 | primary anchor |
| H6-A5 | 32 | 254 | primary anchor |
| H6-A6 | 41 | 147 | primary anchor |

The full 13+ cell cluster can be included only if every added cell satisfies a
written criterion using the *existing* core/Christian observations and is
chosen without looking at Exp 4 or ablation outcomes.  Until that registry is
frozen, report the six anchors as the confirmatory family and any enlarged
cluster as exploratory.  Do not select cells by their Exp 4 contrast.

For all studies, save a run manifest with corpus/source hashes, tokenizer and
checkpoint revision, harness commit/hash, TP world size, exact hook mode,
random seeds, exclusions, and the per-layer `freq_sum == seqlen * 6`
invariant.  Recompute rates from `observation.layers["<layer>"]` and never
from an unverified derived table.  Make the source document (or independent
document block), rather than the individual token, the replication unit.
Tokens within a window share context and cannot be treated as thousands of
independent observations.

### 0.2 Reconcile documentation before making a new headline

The brief reports 5,044 records/57.7M tokens and calls Exp 14 complete, while
the older narrative contains 22.2M-token and incomplete-wave wording and
EXPERIMENTS_V2 still says to run Exp 14.  Produce one machine-generated
`analysis/data_manifest.json` from the raw JSONL files before the next report:
file SHA-256, row count, token count, categories, date, and whether the
Exp-14 model/output can be reproduced.  The current brief is the operational
description, but a result should cite the manifest, not a prose total.

### 0.3 Common reporting standard

For every primary contrast report the raw numerator/denominator, rate per
million tokens, effect estimate on its natural scale (rate ratio or
Delta-NLL), 95% confidence interval, and a document-cluster bootstrap interval
(at least 10,000 resamples).  P-values are secondary.  Use one pre-specified
primary composite endpoint per experiment; correct individual-anchor
follow-ups with Benjamini-Hochberg FDR at 0.05.  A non-significant result is
not evidence of no effect: use an equivalence interval or report that the data
are inconclusive.

Run the schema/invariant audit and a blind token-span audit before statistics:
randomly inspect at least 10 Exp-4 annotations against decoded tokens, verify
that all spans are `[start_tok, end_tok)`, non-overlapping and in bounds, and
have a human-readable source locator.  Audit both quote and commentary labels.

## 1. Exp 4: quotation-switch analysis and necessary corpus repair

### The immediate issue: the supplied corpus is a pilot, not yet decisive

The supplied 30-row manifest contains 36 marked quote spans totalling **419
tokens** (range 7--16 tokens).  That is adequate to validate raw top-k capture
and annotation alignment, but not to support the promised per-expert decisive
test.  At a commentary routing rate of 10,000/M (1%), 419 quote tokens yield
about four expected routings for an anchor; even at 90,000/M, it yields about
38.  Boundary dependence and document clustering make the effective sample
smaller still.  A zero in this pilot would have a wide upper confidence bound,
not prove that an expert switches off.

Treat the current run as **Exp 4a, a feasibility pilot**.  It can identify a
large, visually obvious switch and validate the analysis pipeline.  Do not
publish it as the decisive within-document result.  Build **Exp 4b** before
making a confirmatory claim:

- Annotate at least 10,000 usable quote tokens across roughly 100 or more
  quote blocks from at least 30 independent source documents.  Prefer
  quotations of 50+ tokens; preserve source locators and annotation decisions.
- Give each quote block a same-document commentary comparator of equal token
  length, sampled from the same 16k window and matched on position (for
  example, nearest eligible block in the same 2k-token band), digit fraction,
  newline/heading status, punctuation fraction, and preceding-context length.
  Do not call the rest of the window a control: quote and commentary have
  different local features despite sharing a window.
- Exclude a pre-specified 64-token buffer on each side of every quote boundary
  from the primary endpoint.  Then repeat with 0, 32, 128, and 256-token
  buffers as a sensitivity analysis.  A causal transformer can carry a quote's
  context forward, so post-quote tokens are especially unsuitable as
  unbuffered commentary controls.
- Before full collection, run a conditional Monte-Carlo power calculation
  using the observed commentary rates and the document-level overdispersion
  from Exp 4a.  Target 80% power to distinguish a 5x suppression (quote /
  commentary rate ratio = 0.20) from no switch for the composite.  Increase
  the 10,000-token target if the simulated power is lower.  This is a precision
  target, not a license to stop early for significance.

### Primary endpoint and test

Raw capture supplies top-k identities, so the confirmatory response is the
binary event `I(layer, expert, token is in top-6)`; do not imply per-token
REAP or gate-weight evidence unless the capture format actually persists those
quantities.  For each anchor, quote block, and matched commentary block,
compute its routing count and exposure.  Standardize each anchor by its
commentary mean and take the mean of the six log rate ratios as the frozen
**H6 composite**.

Fit the confirmatory model at block level, not token level:

```
Y[b,e] ~ beta-binomial(N[b], p[b,e])
logit p[b,e] = alpha[e] + beta[e] * quote[b]
                + gamma * local_covariates[b]
                + u[source_document] + u[window]
```

`Y` is the number of routed tokens and `N` the usable tokens.  The
beta-binomial absorbs extra-binomial variation; source and window effects
respect the matched design.  Fit a hierarchical version in which the six
`beta[e]` values partially pool around the composite effect.  As a
model-light check, use a paired block-label permutation test: within each
quote/comparator matched set, swap the labels, recompute the composite, and
compare the observed statistic with 100,000 valid permutations.  Bootstrap
source documents, not spans or tokens, for intervals.

The confirmatory decision rule is deliberately three-way:

- **Strong support for a local verse/prose switch:** composite rate ratio <=
  0.20 and its 95% interval lies below 0.50, with the permutation test in the
  predicted direction and at least four of six anchors directionally
  suppressed after FDR correction.
- **Evidence against a local switch:** the equivalence interval is wholly
  inside 0.80--1.25 for the composite after Exp 4b's precision target is met.
  This says the label is not locally switching routing at this resolution; it
  does not identify the alternative cause.
- **Otherwise:** inconclusive.  Preserve the format-associated observation and
  move to the controlled format-edit experiment rather than relabeling H6.

Model quote position using a restricted cubic spline and include local digit,
punctuation, newline/heading, and quote-length covariates as robustness checks.
The matched/permutation analysis remains primary, because a regression cannot
rescue bad matching.  Repeat the analysis after dropping each source document
and after splitting documents in half; a result driven by one anthology or
editor is not a general H6 result.

### Exp 4 graphics

The principal wiki figure should be a **paired forest plot**: one row per
anchor plus the frozen composite, showing quote/commentary rate ratio and
95% document-bootstrap interval on a log scale, with raw counts beside it.
Pair it with a small slope/raincloud panel of the 30+ document-level composite
effects so readers can see heterogeneity rather than only an aggregate.

Add a secondary boundary-aligned event study: for each routed anchor, plot
mean routing probability in token bins around quote start and end, with a
shaded excluded boundary band and cluster-bootstrap intervals.  This makes a
real switch, gradual contextual carryover, and a uniform document-level effect
visually distinguishable.  Show representative decoded spans only after the
quantitative figure; examples are explanation, not evidence.

## 2. Exp 13: scoped H6 ablation

### Question and intervention

Exp 13 asks a narrow causal question: are the pre-registered H6 routing paths
important for next-token prediction, and is any importance format-selective?
It must not modify checkpoint files.  Implement a temporary, logged inference
hook in the existing TP2 observation/evaluation code and remove it after the
run.  The existing two-Spark TP2 setup is sufficient; no different serving
stack is required.  Both ranks must apply the same global registry, each only
zeroing its locally sharded experts before the normal all-reduce.  Confirm that
the unablated hook path is bitwise/within-tolerance identical to the normal
evaluation path before collecting results.

Use the six anchors in Section 0 as the first locked cluster, spanning layers
21, 22, 23, 30, 32, and 41.  Do not ablate the loosely described `13+` cluster
until its membership has been frozen independently and Exp 4b/Exp 15 confirms
that it is the same phenomenon.  Run a dose series: each anchor separately,
then the ordered cumulative sets of 1, 3, and all 6 anchors.  This reveals
whether an apparent cluster effect is one crucial expert, diffuse redundancy,
or a broad damage artifact.

Run two explicitly different interventions, labelled separately:

1. **Contribution knockout (primary):** retain the original top-6 selection
   and gate weights, but set the chosen expert's output contribution to zero.
   This measures the harm of removing the contribution without silently
   changing the gate's decision.
2. **Route-mask compensation (secondary):** mask selected experts before
   top-k, choose replacements, and renormalize exactly as the normal gate
   would.  This measures whether the model can compensate with another expert.

Never describe the second mode as the same ablation.  The two modes answer
different questions.

### Corpus, baselines, and outcome

Use held-out material never used to select H6: at least 100 independent
document blocks each from digit-stripped KJV verse, public-domain secular
verse, Christian prose, and public-domain secular prose.  Use 512--1,024
token teacher-forced blocks, balanced on length, digit rate, and source where
possible; keep blocks from the same document in the same split.  Quote spans
from Exp 4b may supply an additional within-document stratum, but they should
not replace the broader held-out set.

For every exact token sequence, evaluate the same sequence in these modes:

- unmodified baseline;
- sham hook (registry lookup and branch, no expert zeroed);
- each H6 dose under contribution knockout;
- matched-control cluster(s) under contribution knockout;
- route-mask compensation for the full H6 cluster.

The primary outcome is per-block `Delta-NLL = NLL(ablation) - NLL(baseline)`
in nats/token.  Secondary outcomes are change in true-token probability,
top-1/top-5 agreement, KL divergence from baseline final distribution, and
whether loss is localized around H6 routing events.  Compute full final logits
and teacher-forced loss; the observation harness deliberately bypasses the
vocabulary head, so it cannot be reused unchanged.  To avoid the known giant
vocabulary-by-16k allocation, evaluate short fixed blocks or stream the head
and cross-entropy in token chunks while preserving the exact final logits.

Fit the primary paired mixed model:

```
Delta-NLL[i] = a + b_format * prose[i] + b_mode * H6[i]
               + b_interaction * prose[i] * H6[i]
               + matched covariates + u[source_document] + error[i]
```

Equivalently, model the paired H6-minus-sham loss delta and test the prose
minus-verse difference.  The primary causal estimand is `b_interaction`:
greater damage on prose than verse.  Use a two-sided document-cluster bootstrap
interval and a paired source-stratified permutation test.  Report the absolute
loss effect as well as the interaction; a statistically detectable but
microscopic loss change is not a mechanistic headline.

### Controls that make the claim interpretable

- **Execution control:** the sham hook must give a negligible delta within a
  pre-set numerical tolerance.
- **Size/layer/activity-matched control:** create 20 random six-expert control
  clusters with one expert at each H6 layer, sampled before evaluation from
  non-H6, non-digit experts matched to H6 baseline routing frequency and REAP
  on prose.  Compare H6 to this control distribution, not one convenient
  random cluster.
- **Specificity positive control:** on a small digit-minimal-pair subset,
  ablate a pre-registered digit cluster.  It should preferentially affect
  digit-bearing inputs, demonstrating that the evaluator can recover a
  known format-specific effect.
- **Randomness and implementation controls:** `eval()` mode, fixed seed,
  identical tokenization/order, source hash, rank-by-rank registry logging,
  and an all-reduce/invariant check.  Repeat a fixed 10-block set from a fresh
  process; nondeterminism is reported, not averaged away.

Interpretation: a prose-selective H6 loss increase beyond the matched-control
distribution supports a causal contribution to prose processing.  Equal damage
on verse and prose says H6 is not format-selectively necessary.  No measurable
damage with a narrow interval is evidence of redundancy or a correlational
routing marker, not evidence that the routing observation was false.

## 3. Priority, dependencies, and parallel work

The two Sparks form one TP2 job, so GPU experiments should be queued, not
run in parallel.  CPU data curation, annotation, and analysis can proceed in
parallel with the one active TP2 job.

| Order | Work | Why it comes here | GPU |
|---:|---|---|---|
| P0 | Rebuild data manifest; freeze H6 registry; audit Exp-4 labels/raw capture; reproduce/verify Exp 14 | prevents another stale-table or indexing claim | none |
| P1 | Analyse Exp 4a and run its power simulation | tells us whether the pending data answer anything beyond feasibility | none after capture |
| P2 | Build/annotate Exp 4b and build the balanced secular/format corpus | the actual decisive within-document test needs more exposure | none |
| P3 | Run Exp 1 and Exp 12 sequentially | cheap checks; Exp 1 probes register, Exp 12 is a specificity control | low |
| P4 | Run Exp 4b with raw top-k capture; derive Exp 11 contexts from this same capture | avoids a redundant Exp 11 rerun | moderate |
| P5 | Run the controlled format-edit experiment and the secular factorial (Exp 3) | distinguishes lineation, apparatus, register, and religion | moderate |
| P6 | Run Exp 13 only if H6 registry/format behavior replicate | causal work is worthwhile only on a stable target | moderate |
| P7 | Re-run residual-norm-normalized sensitivity only if that result remains in scope | required for any sensitivity/Jacobian wording, not for H6 | low |

Exp 1 should be analysed as verse-level paired contrasts, not five corpus
means; all translations are still verse-form, so a null result is informative
about register only, not a proof about lineation.  Exp 12 is demoted as planned:
it is a negative-control/mechanism validation, not a gate for H6.  Exp 11 is
an explanatory context analysis with a blinded coding rubric; it cannot select
or redefine the primary H6 cluster.

For Exp 1, use the frozen H6 composite on matched verse blocks and fit a
translation fixed effect with verse/block and source random effects.  The
pre-specified contrast is BBE versus KJV; other translation contrasts are
FDR-controlled.  Report a within-verse paired permutation test and an
equivalence interval for a practically small register effect.  For Exp 12,
analyse every original chapter/window as a three-condition matched set
(digit-free, restored citation, random numerals).  The digit-expert composite
should be tested with a condition-label permutation or paired beta-binomial
model; its planned pattern is both digit conditions above digit-free, with a
pre-specified restored-versus-random equivalence test.  In the same data, the
H6 composite has an equivalence test, not a null p-value, to support its
digit-independence.  The Exp-14 reproduction should use a document-level
hierarchical model with digit fraction, punctuation fraction, sentence length,
type-token ratio, and declared format plus tradition effects; retain only
pre-declared transformations and check residuals, collinearity, and
leave-source-out stability.

Go/no-go gates:

1. If Exp 4a shows malformed raw capture or annotations, fix the harness and
   rerun a small validation sample before any full run.
2. If Exp 4b has insufficient power or fails the span audit, extend it; do not
   substitute a pooled-token p-value.
3. If Exp 4b and Exp 15 disagree, retain the neutral term **H6
format-associated routing axis** and investigate the discrepancy before
ablation.
4. If Exp 4b and Exp 15 replicate, proceed to the registered ablation.

## 4. New experiments that close the remaining alternatives

### Exp 15: controlled format-edit factorial (highest-value new experiment)

Quotation status bundles vocabulary, semantics, source era, author, local
position, typography, and citation practice.  Create public-domain source
blocks and edit the *same underlying words* into controlled presentations:

| Factor | Levels |
|---|---|
| Lineation | original lines / paragraphs with line breaks removed |
| Editorial apparatus | absent / added neutral headings, footnotes, or citations with digits controlled |
| Register | original / paired public-domain translation or carefully documented conservative modernization |
| Content domain | religious / secular |

Use a fractional factorial only if every retained contrast is balanced; the
cleanest initial version is a 2x2 lineation-by-apparatus design on 50+ base
passages, with each base passage rendered in all conditions.  Preserve token
counts as closely as possible and calculate all local covariates after
tokenization.  Test the H6 composite with a within-passage mixed model and
source-block permutation.  This can identify a formatting driver directly;
Exp 1 cannot, because translations change wording as well as register.

### Exp 16: secular, religious, and format factorial (replace a simple Exp 3)

Build four balanced public-domain cells: secular verse, secular prose,
religious verse, and religious prose.  Sample many independent authors rather
than a few famous works, balance window length/digit rate/language, and hold
out whole authors.  Estimate format, religious-domain, and format-by-domain
effects with a hierarchical negative-binomial/beta-binomial model.  The key
test is whether the format effect replicates in secular writing and whether a
religious-domain coefficient remains within a pre-set practical equivalence
bound after format covariates.  Validate by leave-one-author-out and
leave-one-tradition-out prediction.  This is materially stronger than asking
whether Milton happens to look like the Bible.

### Exp 17: quote-boundary and context-carryover study

Using Exp 4b, estimate routing before a quote, inside it, and after it at
several distances.  Compare before/after asymmetry.  Because the transformer
is causal, an after-quote elevation may represent retained context rather than
classification of the current token.  This is a direct test of a missing
alternative in the simple span comparison.

### Exp 18: distinguish gate selection from expert contribution

For H6 anchors, collect (where feasible) gate rank/weight, selection frequency,
expert-output norm, and contribution norm on the controlled corpus.  A high
selection rate with negligible contribution would be a routing marker; a large
contribution plus a prose-specific ablation effect is mechanistic evidence.
Keep this separate from REAP averages, which should not be substituted for
per-token causal evidence.

### Exp 19: make the religion null an equivalence result

Re-fit the covariate model with document/source random effects and tradition
effects, using only pre-declared covariates.  Set a smallest effect size of
interest before fitting (for example, a residual tradition rate ratio outside
0.80--1.25 for the H6 composite, subject to power).  Use two one-sided tests
and a 90% interval for equivalence, plus leave-one-source/tradition-out
validation.  The valid conclusion becomes “no residual tradition effect larger
than the stated practical bound in this corpus,” not the stronger and
unfalsifiable “the model has no religion representation.”

### Exp 20: validate that late prediction emergence is not a lens artifact

The rank-agreement curve is useful, but a single tunneled lens may have its own
depth-dependent behavior.  On document-disjoint train/test splits, compare the
existing lens with a simple independently trained linear probe at selected
layers (for example 0, 18, 19, 30, 37, 42).  Report held-out cross-entropy,
top-1 agreement, calibration, and the incremental change by layer.  This does
not turn intermediate probabilities into beliefs; it tests whether “late
emergence” survives a second readout family.

## 5. Visualization and publication plan

Keep the wiki-style presentation, but make every claim auditable from the
page.  The existing five charts establish the discovery landscape.  Add these
in order:

1. **Evidence and status table.** One compact table for every hypothesis:
   claim, unit of replication, controls, effect/interval, current status,
   raw-data link, and what would falsify it.  Prominently retain the H3 and
   specialist retractions.
2. **Exp 4 paired forest + event study.** The confirmatory figure described in
   Section 1, with raw quote/control exposures.  This is the essential H6
   figure; do not use a decorative heatmap in its place.
3. **Format factorial coefficient plot.** Standardized within-passage effects
   and intervals for lineation, apparatus, register, domain, and interactions.
   It makes the mechanism alternatives comparable on one scale.
4. **Covariate/tradition forest plot.** Coefficients with intervals from the
   document-level hierarchical model, followed by a leave-one-source-out
   stability panel.  It communicates the religion null as bounded precision,
   not absence inferred from a large p-value.
5. **Ablation specificity/dose plot.** Delta-NLL distributions by input format
   for baseline/sham, every H6 dose, and the distribution of matched random
   clusters.  Use the same y-axis and show absolute nats/token.
6. **Expert registry view.** A sortable dense table/heatmap of every frozen
   H6 cell: original selection evidence, Exp-4b rate ratio, format-edit effect,
   and ablation effect.  This prevents a composite from hiding a single-cell
   story.
7. **Routing-geometry null view.** A corpus similarity matrix or two-dimensional
   embedding with source/format labels and a label-permutation test, accompanied
   by the actual Jaccard values.  It should show the lack of family clustering
   without overstating a low-dimensional visualization.
8. **Lens robustness panel.** Existing agreement curve with document-bootstrap
   intervals plus the independent-probe comparison and a calibration inset.

Every figure needs a caption that states the observation unit, number of
documents/tokens, whether a result is confirmatory or exploratory, and a link
to the exact data/code manifest.  Log axes must state how zeros are handled;
never make zeros visually look like measured small non-zero rates.

## 6. Narrative arc for a technical audience

Lead with the honest result, not the original excitement:

1. **Question and scale:** instrument a 43-layer, top-6 MoE across religious
   and matched text to ask whether routing respects religious tradition.
2. **Forensic reversal:** two attractive specialist claims failed raw-data and
   confound checks.  The KJV zero was digit removal; a purported Qur'an expert
   was a digit expert; routing concentration was a length-sensitive statistic
   with the wrong predictive sign.  Retractions are the method working.
3. **What survives:** a large, cross-tradition, digit- and length-robust H6
   association, plus a routing backbone that does not cluster by religion and
   a late-emerging prediction curve.  Use the neutral term
   “format-associated” until the intervention studies resolve its cause.
4. **Decisive design rather than rhetoric:** show the within-document
   quotation, controlled formatting, secular factorial, and ablation logic.
   Make the current 419-token quotation annotation a transparent pilot and
   explain the Exp-4b repair.  That is more credible than treating a small
   p-value as decisive.
5. **Causal and null conclusions, carefully bounded:** if supported, say that
   a frozen H6 set is recruited by specified format features and makes a
   measurable format-selective contribution to next-token prediction.  Say
   only that no residual tradition effect above the registered practical bound
   was observed in these corpora.  Do not claim that a model has no theology,
   beliefs, or religion representation in any broader sense.
6. **Reusable lesson:** MoE routing analyses need within-source controls,
   exposure-aware statistics, document-level replication, and independent
   causal tests.  “Expert X fires on corpus Y” is a hypothesis generator, not
   an interpretation.

The paper's contribution is therefore not “we found Bible/Qur'an experts.” It
is a correctness-first account of how an apparent semantic routing story
collapsed under data audit, what robust format-sensitive routing remained, and
the controlled experiments required to turn that observation into a mechanism.
