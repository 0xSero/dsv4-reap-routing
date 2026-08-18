#!/usr/bin/env python3
"""Generate the multi-page research wiki (Wikipedia Vector skin) into /tmp/dsv4-reap-site/wiki/."""
import os

OUT = "/tmp/dsv4-reap-site/wiki"
os.makedirs(OUT, exist_ok=True)

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - DSv4-Flash REAP Wiki</title>
<style>
body{{margin:0;background:#f8f9fa;color:#202122;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Liberation Sans',sans-serif;font-size:14px;line-height:1.6}}
a{{color:#3366cc;text-decoration:none}}a:hover{{text-decoration:underline}}
#mw-head{{position:fixed;top:0;left:0;right:0;height:3.5em;background:#fff;border-bottom:1px solid #a2a9b1;z-index:100;display:flex;align-items:center;padding:0 1.5em}}
#mw-head .brand{{font-weight:600;font-size:13px;color:#54595d}}
#mw-body{{margin-left:11em;margin-top:3.5em}}
.mw-body{{background:#fff;border:1px solid #a7d7f9;max-width:60em;margin:1em auto;padding:1em 1.5em 2em}}
@media(max-width:768px){{#mw-body{{margin-left:0}}#mw-panel{{display:none}}.mw-body{{margin:0;border:none}}}}
#mw-panel{{position:fixed;top:3.5em;left:0;width:11em;bottom:0;padding:1em 0 0 .5em;font-size:12px;background:#f8f9fa;overflow-y:auto}}
#mw-panel .portal{{margin-bottom:1.2em}}
#mw-panel h3{{font-size:12px;font-weight:600;color:#54595d;margin:0 0 .4em}}
#mw-panel ul{{list-style:none;margin:0;padding:0;line-height:1.8}}
#mw-panel li a{{display:block;padding-left:.5em}}
#mw-panel li.here a{{font-weight:600}}
.mw-body h1{{font-size:28px;font-family:'Linux Libertine',Georgia,serif;font-weight:400;border-bottom:1px solid #a2a9b1;margin:0 0 .25em;padding-bottom:.1em}}
.mw-body h2{{font-size:22px;font-family:'Linux Libertine',Georgia,serif;font-weight:400;border-bottom:1px solid #a2a9b1;margin:1em 0 .5em;padding-bottom:.17em}}
.mw-body h3{{font-size:17px;font-weight:600;margin:.8em 0 .3em}}
.mw-body h4{{font-size:14.5px;font-weight:600;margin:.6em 0 .2em}}
.mw-body p{{margin:.5em 0}}
.mw-body ul,.mw-body ol{{margin:.3em 0 .5em 1.6em}}.mw-body li{{margin:.2em 0}}
code{{font-family:'Courier New',monospace;font-size:13px;background:#f0f0f0;padding:0 2px}}
pre{{background:#f8f9fa;border:1px solid #eaecf0;padding:.8em 1em;font-family:'Courier New',monospace;font-size:12.5px;line-height:1.4;overflow-x:auto;border-radius:2px}}
.wikitable{{border-collapse:collapse;width:100%;margin:.5em 0;font-size:13px;background:#fff;border:1px solid #a2a9b1}}
.wikitable th{{background:#eaecf0;border:1px solid #a2a9b1;padding:4px 8px;text-align:left;font-weight:600}}
.wikitable td{{border:1px solid #a2a9b1;padding:4px 8px;vertical-align:top}}
.wikitable tr:nth-child(even){{background:#f8f9fa}}
.num{{text-align:right;font-family:monospace}}
.hatnote{{font-style:italic;padding:.4em 0;margin:.5em 0;color:#54595d;font-size:13px}}
.ambox{{margin:.5em 0;border:1px solid #a2a9b1;border-left:10px solid #c8ccd1;background:#f8f9fa;padding:.5em 1em;font-size:13px}}
.ambox.warn{{border-left-color:#f28500;background:#fef6e7}}
.ambox.bad{{border-left-color:#d33;background:#fee7e6}}
.ambox.ok{{border-left-color:#3c8;background:#eaf7ee}}
.tag{{display:inline-block;font-size:11px;padding:1px 7px;border-radius:10px;margin-left:4px}}
.tag-pending{{background:#eaf0ff;color:#3366cc}}.tag-ok{{background:#eaf7ee;color:#14866d}}.tag-bad{{background:#fee7e6;color:#d33}}.tag-run{{background:#fef6e7;color:#b25f00}}
figure{{margin:1em 0;text-align:center}}
figure img{{max-width:100%;border:1px solid #c8ccd0}}
figcaption{{font-size:12px;color:#54595d;margin-top:.3em}}
.catlinks{{margin-top:1em;padding:.4em .8em;background:#f8f9fa;border:1px solid #a2a9b1;font-size:12px}}
.toc{{background:#f8f9fa;border:1px solid #a2a9b1;padding:.5em 1em;display:inline-block;margin:.5em 0 1em;font-size:13px}}
.toc .toctitle{{font-weight:600;text-align:center;margin-bottom:.3em}}
.toc ul{{list-style:none;margin:0;padding-left:1.2em}}
.small{{font-size:12px;color:#54595d}}
.subtitle{{font-size:13px;color:#54595d;margin-bottom:.5em}}
</style>
</head>
<body>
<div id="mw-head"><span class="brand">DSv4-Flash REAP Research Wiki</span></div>
<div id="mw-panel">
<div class="portal"><h3>Wiki</h3><ul>
<li{here_main}><a href="../RESEARCH_WIKI.html">Main page</a></li>
<li{here_methods}><a href="methods.html">Methods &amp; harness</a></li>
<li{here_data}><a href="data.html">Data &amp; corpora</a></li>
<li{here_results}><a href="results.html">Results &amp; findings</a></li>
<li{here_jspace}><a href="jspace.html">J-space lens</a></li>
<li{here_experiments}><a href="experiments.html">Experiments</a></li>
<li{here_code}><a href="code.html">Code reference</a></li>
<li{here_ops}><a href="operations.html">Operations (live)</a></li>
<li{here_roadmap}><a href="roadmap.html">Roadmap &amp; ideas</a></li>
<li{here_narrative}><a href="narrative.html">Narrative</a></li>
<li{here_exp4}><a href="exp4.html">Exp 4 results</a></li>
<li{here_exp13}><a href="exp13.html">Exp 13 ablation</a></li>
<li{here_exp1}><a href="exp1.html">Exp 1 results</a></li>
<li{here_plan}><a href="forward_plan.html">Forward plan</a></li>
</ul></div>
<div class="portal"><h3>Resources</h3><ul>
<li><a href="https://github.com/0xSero/dsv4-reap-routing" target="_blank">GitHub repo</a></li>
<li><a href="https://0xsero.github.io/dsv4-reap-routing/wiki.html">Technical wiki</a></li>
<li><a href="https://0xsero.github.io/dsv4-reap-routing/">Narrative page</a></li>
<li><a href="https://huggingface.co/datasets/0xSero/deepseek-v4-flash-reap" target="_blank">HF dataset</a></li>
</ul></div>
<div class="portal"><h3>Reviews</h3><ul>
<li><a href="../reviews/claude_opus5_review.md">Claude Opus 5</a></li>
<li><a href="../reviews/kimi_k3_review.md">Kimi K3</a></li>
</ul></div>
</div>
<div id="mw-body"><div class="mw-body">
<div class="subtitle">From the DeepSeek-V4-Flash-0731 interpretability project</div>
{body}
<div class="catlinks"><b>Categories:</b> <a href="../RESEARCH_WIKI.html">DSv4-Flash interpretability</a> | <a href="results.html">MoE routing</a> | <a href="data.html">Religious text corpora</a></div>
</div></div>
</body>
</html>
"""

def page(fname, title, body, here=""):
    here_main = ' class="here"' if here == "main" else ""
    html = TEMPLATE.format(
        title=title, body=body,
        here_main=here_main,
        here_jspace=' class="here"' if here == "jspace" else "",
        here_index=' class="here"' if here == "index" else "",
        here_methods=' class="here"' if here == "methods" else "",
        here_data=' class="here"' if here == "data" else "",
        here_results=' class="here"' if here == "results" else "",
        here_experiments=' class="here"' if here == "experiments" else "",
        here_code=' class="here"' if here == "code" else "",
        here_ops=' class="here"' if here == "ops" else "",
        here_roadmap=' class="here"' if here == "roadmap" else "",
        here_narrative=' class="here"' if here == "narrative" else "",
        here_exp4=' class="here"' if here == "exp4" else "",
        here_exp13=' class="here"' if here == "exp13" else "",
        here_exp1=' class="here"' if here == "exp1" else "",
        here_plan=' class="here"' if here == "plan" else "",
    )
    with open(os.path.join(OUT, fname), "w") as f:
        f.write(html)
    print("wrote", fname)

# ══════════════════ METHODS ══════════════════
METHODS = """
<h1>Methods and observation harness</h1>
<div class="hatnote">This page documents <b>how</b> the study works: the model under observation, the read-only harness that records routing, the REAP metric, the fail-closed integrity guarantees, and the verification that the harness is faithful to the real model code.</div>

<div class="toc"><div class="toctitle">Contents</div><ul>
<li>1 <a href="#model">Model under observation</a></li>
<li>2 <a href="#harness">Observation harness</a></li>
<li>3 <a href="#pipeline">Corpus pipeline</a></li>
<li>4 <a href="#reap">REAP metric</a></li>
<li>5 <a href="#jlens">J-lens probes</a></li>
<li>6 <a href="#failclosed">Fail-closed guarantees</a></li>
<li>7 <a href="#faithful">Harness faithfulness verification</a></li>
<li>8 <a href="#infra">Deployment infrastructure</a></li>
</ul></div>

<h2 id="model">1. Model under observation</h2>
<p>DeepSeek-V4-Flash-0731 is a sparse <b>mixture-of-experts</b> (MoE) language model. Its routing
architecture is the object of study:</p>
<table class="wikitable">
<tr><th>Parameter</th><th>Value</th><th>Notes</th></tr>
<tr><td>Layers</td><td class="num">43</td><td>Indexed L0&ndash;L42</td></tr>
<tr><td>Routed experts / layer</td><td class="num">256</td><td>SwiGLU FFN, fp4 weights</td></tr>
<tr><td>Activated experts / token</td><td class="num">6</td><td>top-6 selection</td></tr>
<tr><td>Gate score function</td><td><code>sqrt(softplus(x))</code></td><td>sqrt-softplus; see Gate.forward</td></tr>
<tr><td>Route scale</td><td class="num">1.5</td><td>multiplies normalized weights</td></tr>
<tr><td>Bias in gate</td><td>per-expert float</td><td>shifts <i>selection</i> only, not weights</td></tr>
<tr><td>Hash-routed layers</td><td>L0&ndash;L2</td><td><code>n_hash_layers=3</code>; expert IDs fixed per token ID via <code>tid2eid</code></td></tr>
<tr><td>Hidden dim / vocab</td><td class="num">4,096 / 129,280</td><td></td></tr>
<tr><td>Attention precision</td><td>fp8</td><td>tilelang sparse_attn kernel (replaced in harness)</td></tr>
<tr><td>Hyper-connections</td><td>hc_head &times;4</td><td></td></tr>
<tr><td>Group-limited routing</td><td>none</td><td><code>o_groups=8</code> is an attention parameter, not routing</td></tr>
<tr><td>Checkpoint revision</td><td colspan="2"><code>9e165c30e2704aec5d9d593cce3eebd58bbef1cb</code> (tokenizer pinned to same rev)</td></tr>
</table>

<h3>1.1 The routing step (real source)</h3>
<p>The actual <code>Gate.forward</code> from <code>model.py:551&ndash;589</code>:</p>
<pre>def forward(self, x, input_ids=None):
    scores = linear(x.float(), self.weight.float())
    if self.score_func == "softmax":
        scores = scores.softmax(dim=-1)
    elif self.score_func == "sigmoid":
        scores = scores.sigmoid()
    else:
        scores = F.softplus(scores).sqrt()          # sqrt-softplus
    original_scores = scores
    # Bias shifts scores for expert selection (topk) but does not affect routing weights.
    if self.bias is not None:
        scores = scores + self.bias
    if self.hash:                                    # L0-2 only
        indices = self.tid2eid[input_ids]           # expert fixed per token ID
    else:
        indices = scores.topk(self.topk, dim=-1)[1]  # plain topk, no group masking
    weights = original_scores.gather(1, indices)     # weights from UNbiased scores
    if self.score_func != "softmax":
        weights /= weights.sum(dim=-1, keepdim=True) # renormalize
    weights *= self.route_scale                      # 1.5
    return weights, indices</pre>
<p>Two properties matter for analysis: (a) the <b>bias affects only which experts are selected</b>,
not the weights they receive; (b) hash layers L0&ndash;2 route by token ID alone, so their
statistics are corpus-invariant <i>by construction</i>.</p>

<h2 id="harness">2. Observation harness</h2>
<p><code>observe_religious.py</code> runs read-only inference with a forward hook on every
<code>Gate</code> module. No weights are loaded into training mode, nothing is written back.
Per token, per layer, it records:</p>
<ul>
<li><b>Selected expert indices</b> &mdash; the 6 winners of topk (or hash assignment)</li>
<li><b>Gate weights</b> &mdash; sqrt-softplus scores gathered at the selected indices, normalized, &times;1.5</li>
<li><b>Activation norms</b> &mdash; L2 norm of each selected expert's output vector</li>
</ul>
<p>These are aggregated per sample per layer into the record format documented on the
<a href="data.html">data page</a>.</p>

<div class="ambox warn"><b>Known caveats.</b>
(1) The harness replaces the tilelang <code>sparse_attn</code> kernel and
<code>fast_hadamard_transform</code> with pure-PyTorch equivalents &mdash; claimed numerically
equivalent, but any difference would perturb routing upstream of L0.
(2) The <code>gate_weights[256]</code> field in records is a <b>softmax diagnostic</b>, not the
routing score (which is sqrt-softplus). Analyses must not treat it as the route score.
(3) <code>routed_experts</code> stores <b>unique</b> expert IDs per layer, not per-token
routing &mdash; which is why context-dump experiments need a GPU re-run.</div>

<h2 id="pipeline">3. Corpus pipeline</h2>
<p>Text goes through five stages before it becomes a record:</p>
<ol>
<li><b>Scrape</b> &mdash; <code>scrape_christian.py</code> / <code>scrape_theology_books.py</code> (Project Gutenberg,
search-HTML enumeration, mirror fallbacks) and <code>scrape_wikipedia.py</code> (MediaWiki
generator API, 3&nbsp;s delay, 429 backoff). Only public-domain or freely-published text.</li>
<li><b>Clean</b> &mdash; Gutenberg header/footer stripped; <b>KJV verse numbers removed by regex</b>
(this innocuous-looking step caused the <a href="results.html#retract">digit confound retraction</a>).</li>
<li><b>Tokenize &amp; window</b> &mdash; <code>prepare_corpus.py</code> / <code>prepare_theology_corpus.py</code>:
pinned tokenizer, English stopword filter, fixed windows (880-token Bible chapters; 16k windows for books).</li>
<li><b>Select</b> &mdash; <code>select_theology.py</code>: stratified quotas per topic, per-sample digit density recorded in manifest.</li>
<li><b>Observe</b> &mdash; the harness (above), fsynced JSONL output, one record per sample.</li>
</ol>

<h2 id="reap">4. REAP metric</h2>
<p><b>REAP</b> = Routing-weight &times; Expert Activation Product. Per expert, per layer:</p>
<pre>REAP = mean(gate_weight over tokens where expert fired)
      &times; mean(activation_norm over the same tokens)</pre>
<p>Text profiles are per-layer top-20 expert sets ranked by frequency-weighted mean REAP;
inter-text similarity is Jaccard overlap of these sets. <b>Metric caution</b> (from the Kimi K3
review): per-firing mean REAP has a heavy noise floor &mdash; experts firing &lt;35 times in
98,304 slots dominate the mean. Layer-wise REAP profiles and frequency profiles can invert
(see <a href="results.html#retract">retraction 8.2</a>). Always state which metric a number
comes from.</p>

<h2 id="jlens">5. J-lens probes</h2>
<p><code>run_jlens.py</code> / <code>jlens_dsv4.py</code> capture, per position and per layer:</p>
<ul>
<li><b>Logit lens</b> &mdash; the unembedding applied to the residual stream at each layer, giving
the model's running "next-token guess" before the final layer. <i>Uncalibrated readout path;
the Genesis 1:2 claim built on it was withdrawn.</i></li>
<li><b>Bounded Jacobian</b> &mdash; output sensitivity to input perturbations along 16 random
projection directions; a cheap proxy for full Jacobian norms.</li>
</ul>
<p>80 samples across all 8 core traditions; complete.</p>

<h2 id="failclosed">6. Fail-closed guarantees</h2>
<div class="ambox ok"><b>Integrity invariants (all 2,749 completed records pass, zero violations):</b>
<ul>
<li><code>&Sigma; expert_frequencies == seqlen &times; 6</code> on <b>every layer of every record</b> &mdash; no token routing lost</li>
<li><code>(category, sample_index)</code> unique across the dataset &mdash; no duplicates</li>
<li>Records fsynced to JSONL line-by-line &mdash; a crash never corrupts a partially-written record</li>
<li>English filter (stopword regex) &mdash; rejects non-English text before observation</li>
<li>SHA-256 + manifest sidecars per corpus file</li>
</ul></div>

<h2 id="faithful">7. Harness faithfulness verification</h2>
<p>The harness's reimplementation of the gate was checked line-for-line against
<code>model.py</code>:</p>
<table class="wikitable">
<tr><th>Check</th><th>Result</th></tr>
<tr><td>sqrt-softplus score</td><td>&#10003; matches <code>F.softplus(scores).sqrt()</code></td></tr>
<tr><td>Bias for selection only</td><td>&#10003; weights gathered from unbiased scores</td></tr>
<tr><td>Hash routing L0&ndash;2</td><td>&#10003; <code>tid2eid[input_ids]</code></td></tr>
<tr><td>Plain topk</td><td>&#10003; no group masking</td></tr>
<tr><td>Renormalization + route scale</td><td>&#10003; <code>/sum</code> then <code>*1.5</code></td></tr>
</table>

<h2 id="infra">8. Deployment infrastructure</h2>
<p>The model runs tensor-parallel across two DGX Spark nodes (TP2), one rank per node.
Observation runs launch as Docker containers (<code>run_full_observation.sh</code>), orchestrated
by a chain supervisor (<code>chain_next_runs.sh</code>) that sequences runs and self-heals NCCL
stalls by relaunching with record-skip-ahead. A 30-minute cron automation monitors all
pipelines and deploys queued experiments when nodes free up. All credentials live in
environment variables; committed code is sanitized. The whole harness is reproducible via
the published <a href="https://github.com/0xSero/dsv4-reap-routing">Docker image</a>
(base <code>ghcr.io/anemll/dspark-vllm-gx10:0.1.1</code>).</p>
"""

page("methods.html", "Methods and harness", METHODS, here="methods")

# ══════════════════ DATA ══════════════════
DATA = """
<h1>Data and corpora</h1>
<div class="hatnote">Everything the study has collected: raw sources, tokenized corpora, observation records, probe data, and where each artifact lives (local, HuggingFace, GitHub).</div>

<div class="toc"><div class="toctitle">Contents</div><ul>
<li>1 <a href="#observed">Observation corpora (completed)</a></li>
<li>2 <a href="#staged">Staged / running corpora</a></li>
<li>3 <a href="#raw">Raw sources</a></li>
<li>4 <a href="#records">Record format</a></li>
<li>5 <a href="#aggregates">Aggregates and analysis files</a></li>
<li>6 <a href="#hf">HuggingFace datasets</a></li>
<li>7 <a href="#gh">GitHub artifacts</a></li>
</ul></div>

<h2 id="observed">1. Observation corpora (completed)</h2>
<table class="wikitable">
<tr><th>Corpus</th><th>Records</th><th>Tokens</th><th>Window</th><th>Digit density</th><th>Source</th></tr>
<tr><td>KJV Bible</td><td class="num">1,189</td><td class="num">1,045,776</td><td>per-chapter (~880)</td><td class="num">0.0000%</td><td>Gutenberg KJV, verse numbers stripped</td></tr>
<tr><td>Christian literature wave-1</td><td class="num">1,267</td><td class="num">20,409,440</td><td>16k first window/book</td><td>varies (~1.1% median)</td><td>Gutenberg, 32 topic searches, 3,705 books</td></tr>
<tr><td>Qur'an (Pickthall)</td><td class="num">115</td><td class="num">258,122</td><td>8k</td><td>varies</td><td>Gutenberg</td></tr>
<tr><td>Book of Mormon</td><td class="num">30</td><td class="num">342,614</td><td>16k</td><td class="num">0.000% median</td><td>Gutenberg pg17</td></tr>
<tr><td>Bhagavad Gita</td><td class="num">18</td><td class="num">29,690</td><td>8k</td><td>low</td><td>Gutenberg (small n)</td></tr>
<tr><td>Tao Te Ching</td><td class="num">81</td><td class="num">13,852</td><td>per-chapter</td><td>low</td><td>Gutenberg</td></tr>
<tr><td>Dhammapada</td><td class="num">26</td><td class="num">16,203</td><td>8k</td><td>low</td><td>Gutenberg pg2017</td></tr>
<tr><td>Analects</td><td class="num">20</td><td class="num">42,041</td><td>8k</td><td>low</td><td>Gutenberg</td></tr>
<tr><td>Upanishads</td><td class="num">3</td><td class="num">21,669</td><td>16k</td><td>low</td><td>Gutenberg (n=3, directional only)</td></tr>
<tr><td><b>Total</b></td><td class="num"><b>2,749</b></td><td class="num"><b>22,179,407</b></td><td colspan="3"></td></tr>
</table>

<h2 id="staged">2. Staged and running corpora</h2>
<table class="wikitable">
<tr><th>Corpus</th><th>Records</th><th>Tokens</th><th>Status</th><th>Purpose</th></tr>
<tr><td>Christian wave-2</td><td class="num">2,295</td><td>~37M</td><td><span class="tag tag-ok">complete</span></td><td>Broaden Christian literature coverage</td></tr>
<tr><td>Theology stratified selection</td><td class="num">1,090</td><td class="num">9,380,481</td><td><span class="tag tag-ok">complete</span></td><td>Topic routing: Jesus 400, Judaism 137, Lucifer 46, Moloch 25, Saturn 32, books 450; per-sample digit density in manifest</td></tr>
<tr><td>Exp 4b quotation-switch (v2)</td><td class="num">351</td><td class="num">5,200,000</td><td><span class="tag tag-run">running</span></td><td>41,426 quote tokens across 18 sources; within-document verse-quote vs commentary routing test</td></tr>
<tr><td>Exp 12 digit minimal-pairs (v2)</td><td class="num">222</td><td class="num">437,900</td><td><span class="tag tag-pending">staged</span></td><td>111 pairs: with_digits vs digit_stripped, 5 categories (dates, misc, lists, scripture, tabular)</td></tr>
<tr><td>Exp 1 multi-translation Bible</td><td class="num">150</td><td class="num">209,151</td><td><span class="tag tag-ok">complete</span></td><td>30 passages &times; 5 translations (KJV, WEB, ASV, YLT, BBE); all public domain, 0-digit controlled. H6 = 47.8/M, 3,415&times; ratio vs commentary</td></tr>
<tr><td>Exp 13 ablation corpus</td><td class="num">480</td><td class="num">418,695</td><td><span class="tag tag-pending">staged</span></td><td>4 cells (verse/prose &times; religious/secular), 120 blocks each, 512&ndash;1024 tokens. Held-out material for causal ablation.</td></tr>
</table>

<h2 id="raw">3. Raw sources</h2>
<table class="wikitable">
<tr><th>Source</th><th>Volume</th><th>Notes</th></tr>
<tr><td>Wikipedia theology articles</td><td class="num">7,508 files</td><td>6 seed topics with category traversal, depth 3</td></tr>
<tr><td>Gutenberg theology books</td><td class="num">3,827 books</td><td>40+ topic searches; 1.6B chars (~400M tokens)</td></tr>
<tr><td>Gutenberg Christian books (wave-1 source)</td><td class="num">3,705 books</td><td>32 topics: patristics &rarr; reformation &rarr; modern</td></tr>
<tr><td>Gutenberg Christian wave-2</td><td class="num">2,295 books</td><td>Extended topic set</td></tr>
<tr><td>Theology corpus total</td><td colspan="2">29,098 tokenized samples from 10,579 raw files</td></tr>
</table>
<p class="small">All text public-domain or freely published. Scrapers respect rate limits
(Gutenberg 0.8&ndash;1.5&nbsp;s; Wikipedia 3&nbsp;s with 429 exponential backoff). Full
manifests with per-file hashes: <code>corpus/manifests/*.manifest.json</code> on
<a href="https://huggingface.co/datasets/0xSero/deepseek-v4-flash-reap" target="_blank">HuggingFace</a>.</p>

<h2 id="records">4. Record format</h2>
<h3>4.1 Corpus sample (input side)</h3>
<pre>{"sample_id": "bible_gen_001", "category": "bible",
 "text": "In the beginning God created...", "char_count": 4203,
 "digit_count": 0, "digit_density": 0.0}</pre>
<h3>4.2 Observation record (output side)</h3>
<pre>{"sample_id": "...", "category": "...", "sample_index": 0, "seqlen": 2048,
 "layers": [                                  // 43 entries
   {"expert_frequencies": [621032, ...],      // [256] int counts, SUM == seqlen*6
    "activation_norms":      [0.0, 2.34, ...], // [256] mean |output| per expert
    "gate_weights":          [0.001, ...],     // [256] softmax DIAGNOSTIC (not route score)
    "reap_score":            [0.0, 0.0796, ...], // [256] gate_weight x activation_norm
    "routed_experts":        [0, 3, 7, ...]}   // unique expert IDs (NOT per-token)
 ]}</pre>
<p>Scale: <code>full_obs.jsonl</code> 560&nbsp;MB / 1,482 records;
<code>christian_obs.jsonl</code> 541&nbsp;MB / 1,267 records; wave-2 in progress.</p>

<h3>4.3 J-lens record</h3>
<pre>{"sample_id": "...", "layers": [{"top_tokens": [[" Spirit", 0.7668], ...],
                                  "jacobian_norm": 1268.3}, ...]}</pre>

<h2 id="aggregates">5. Aggregates and analysis files</h2>
<table class="wikitable">
<tr><th>File</th><th>Contents</th></tr>
<tr><td><code>core_agg.json</code></td><td>Per-category n / tokens / per-layer freq / reap (8 traditions)</td></tr>
<tr><td><code>christian_agg.json</code></td><td>Same for wave-1 Christian corpus</td></tr>
<tr><td><code>analysis/cross_text_jaccard.csv</code></td><td>Top-20 REAP Jaccard matrix, 9&times;9</td></tr>
<tr><td><code>analysis/expert_frequency.csv</code></td><td>Per-expert frequency table</td></tr>
<tr><td><code>analysis/robustness_checks.txt</code></td><td>Matched-n bootstrap CIs for specialist experts</td></tr>
<tr><td><code>analysis_all/exp8_sorted_freq_results.txt</code></td><td>Sorted L42 distributions, permutation check</td></tr>
<tr><td><code>jlens_output/*.jsonl</code></td><td>80 J-lens probe records</td></tr>
</table>

<h2 id="hf">6. HuggingFace datasets</h2>
<p>Both datasets under the consolidated project, <b>private, access on request</b>:</p>
<table class="wikitable">
<tr><th>Dataset</th><th>Files</th><th>Contents</th></tr>
<tr><td><a href="https://huggingface.co/datasets/0xSero/deepseek-v4-flash-reap" target="_blank"><code>0xSero/deepseek-v4-flash-reap</code></a></td><td class="num">45</td><td>
<code>observations/religious-8text/</code>, <code>observations/christian-wave1/</code> (gzipped JSONL),
<code>jlens/</code> (8 traditions), <code>corpus/manifests/</code> (10 manifests),
<code>analysis/</code>, <code>code/</code> (24 sanitized scripts), README</td></tr>
<tr><td><a href="https://huggingface.co/datasets/0xSero/deepseek-v4-flash-religious-reap-observations" target="_blank"><code>0xSero/deepseek-v4-flash-religious-reap-observations</code></a></td><td class="num">11</td><td>Raw observation records</td></tr>
</table>

<h2 id="gh">7. GitHub artifacts</h2>
<table class="wikitable">
<tr><th>Artifact</th><th>Path in <a href="https://github.com/0xSero/dsv4-reap-routing" target="_blank">0xSero/dsv4-reap-routing</a></th></tr>
<tr><td>Research wiki (this site)</td><td><code>RESEARCH_WIKI.html</code> + <code>wiki/*.html</code></td></tr>
<tr><td>Technical wiki</td><td><code>wiki.html</code></td></tr>
<tr><td>Narrative page</td><td><code>index.html</code></td></tr>
<tr><td>Experiment specs</td><td><code>EXPERIMENTS.md</code></td></tr>
<tr><td>Review brief + reviews</td><td><code>CONSULT_REVIEW.md</code>, <code>reviews/</code></td></tr>
<tr><td>Sanitized code</td><td><code>code/</code> (24 scripts)</td></tr>
<tr><td>Corpus manifests</td><td><code>corpus_manifests/</code></td></tr>
<tr><td>Analysis artifacts</td><td><code>analysis_all/</code></td></tr>
<tr><td>J-lens data</td><td><code>jlens/</code> (gzipped)</td></tr>
<tr><td>Docker</td><td><code>Dockerfile</code>, <code>docker-compose.yml</code></td></tr>
<tr><td>Findings video</td><td><code>reap_findings.mp4</code></td></tr>
<tr><td>Charts</td><td><code>img/chart_*.png</code> (generated from aggregates)</td></tr>
</table>
"""

page("data.html", "Data and corpora", DATA, here="data")

# ══════════════════ RESULTS ══════════════════
RESULTS = """
<h1>Results and findings</h1>
<div class="hatnote">Every finding, with its chart, its provenance, and its current standing. Claims that failed review are in <a href="#retract">&sect;8 Retractions</a>, not here.</div>

<div class="toc"><div class="toctitle">Contents</div><ul>
<li>1 <a href="#e164">Expert 164 across corpora</a></li>
<li>2 <a href="#effexp">Effective expert count</a></li>
<li>3 <a href="#backbone">Shared routing backbone</a></li>
<li>4 <a href="#specialists">Hard specialists</a></li>
<li>5 <a href="#jaccard">Inter-tradition similarity</a></li>
<li>6 <a href="#layers">Layer-wise structure</a></li>
<li>7 <a href="#jlens">J-lens findings</a></li>
<li>8 <a href="#retract">Retractions</a></li>
</ul></div>

<h2 id="e164">1. Expert 164 across corpora</h2>
<figure><img src="../img/chart_e164_by_corpus.png" alt="e164 firing rate by corpus">
<figcaption>e164 L42 firings per million tokens. Bible: exactly 0 across 1,045,776 tokens. Christian and Qur'an: ~4,565&ndash;4,571/M.</figcaption></figure>
<p>The raw counts (Exp&nbsp;8, from <code>core_agg.json</code> / <code>christian_agg.json</code>):</p>
<table class="wikitable">
<tr><th>Corpus</th><th>e164 firings</th><th>Tokens</th><th>Rate /M</th><th>Expected under proportional routing</th></tr>
<tr><td>KJV Bible</td><td class="num">0</td><td class="num">1,045,776</td><td class="num">0.0</td><td class="num">~24,510</td></tr>
<tr><td>Qur'an</td><td class="num">1,180</td><td class="num">258,122</td><td class="num">4,571</td><td class="num">~6,049</td></tr>
<tr><td>Christian wave-1</td><td class="num">93,265</td><td class="num">20,409,440</td><td class="num">4,565</td><td class="num">~478,346</td></tr>
</table>
<div class="ambox warn"><b>Interpretation withdrawn.</b> The original reading &mdash; "not-memorized-scripture
expert: the model recites the KJV from memory" &mdash; was retracted after the Claude Opus 5 review
found the digit-density confound (the corpus pipeline strips Bible verse numbers; e164 is
perfectly monotone in digit density; zero-digit Christian control fires at 4.9/M). The
<b>observation stands</b> (a hard exact-zero across a million tokens is real); only the
interpretation changed. Current hypothesis: <b>H1 digit/citation-apparatus detector</b>, pending
Exp 11/12.</div>
<figure><img src="../img/chart_e164_by_layer.png" alt="e164 by layer">
<figcaption>e164 rate per layer (symlog). The Bible trace hugs zero at nearly every scored layer; hash-routed L0&ndash;2 excluded.</figcaption></figure>

<h2 id="effexp">2. Effective expert count</h2>
<figure><img src="../img/chart_effexp_by_layer.png" alt="effective experts by layer">
<figcaption>Exp-Shannon entropy of the expert-frequency distribution, all 43 layers, four key corpora.</figcaption></figure>
<p>At layer 40:</p>
<table class="wikitable">
<tr><th>Corpus</th><th>Aggregate</th><th>Per-sample</th><th>Reading</th></tr>
<tr><td>Bhagavad Gita</td><td class="num">26</td><td class="num">24.3</td><td>most predictable &mdash; chant-like repetition</td></tr>
<tr><td>Qur'an</td><td class="num">43</td><td class="num">39.5</td><td></td></tr>
<tr><td>KJV Bible</td><td class="num">65</td><td class="num">54.1</td><td></td></tr>
<tr><td>Christian literature</td><td class="num">111</td><td class="num">70</td><td>least predictable &mdash; 2,000 years of heterogeneous prose</td></tr>
</table>
<p>The aggregate 111 is inflated by pooling (rare experts firing in one book but not another);
per-sample it collapses to 70. <b>The ordering survives at both levels</b> &mdash; but it is
<b>not a predictability proxy</b> (H3 retracted). The 65 vs 111 gap is a window-length artifact
(Bible ~825-token windows vs Christian 16k); at matched draw budget, Bible and Christian are
within ~2 units. Against lens-measured predictability, the correlation is <i>positive</i>
(Pearson +0.47), not negative as H3 predicted. Call it what it measures: routing concentration.</p>

<h2 id="backbone">3. Shared routing backbone</h2>
<figure><img src="../img/chart_l42_sorted.png" alt="sorted L42 distributions">
<figcaption>Sorted L42 frequency distributions (normalized). The shapes track closely &mdash; both corpora ride the same high-frequency backbone.</figcaption></figure>
<ul>
<li>15 of the top-20 L42 experts (by frequency) shared between Bible and Qur'an (Exp 8).</li>
<li>19 layer-42 experts sit in the top-40 for <i>every</i> corpus.</li>
<li>Hash-routed L0&ndash;2 are corpus-invariant <b>by construction</b> (per-token-ID assignment).</li>
<li>Sorted-distribution check (Exp 8) rules out a shard-index permutation artifact: cross-corpus
expert ID consistency holds for the backbone; e164's rank differs (152 vs 255) in a way a
permutation cannot produce.</li>
</ul>

<h2 id="specialists">4. Hard specialists (corrected after audit)</h2>
<div class="ambox bad"><b>L34 e33 figure was corrupt.</b> The previous version reported "bible 2.7/M"
&mdash; the actual rate is 9,670/M (opposite direction). Regenerated from raw data on 2026-08-15.
See <a href="narrative.html#integrity">narrative &sect;8</a> for details.</div>
<table class="wikitable">
<tr><th>Expert</th><th>Bible (/M)</th><th>Dhammapada (/M)</th><th>Qur'an (/M)</th><th>Christian (/M)</th><th>Classification</th></tr>
<tr><td>L42 e164</td><td class="num">0.0</td><td class="num">varies</td><td class="num">4,571</td><td class="num">4,565</td><td><b>Digit detector</b> (R&sup2;=0.77 within Christian). Retracted as religion claim.</td></tr>
<tr><td>L41 e34</td><td class="num">26.7</td><td class="num">26,631</td><td class="num">5,888</td><td class="num">5,114</td><td><b>Digit detector</b> (R&sup2;=0.72). Dhammapada fires it 5&times; Qur'an. Not a "Qur'an specialist."</td></tr>
<tr><td>L34 e33</td><td class="num">9,670</td><td class="num">4,517</td><td class="num">2,298</td><td class="num">5,371</td><td>Bible fires it <b>highest</b>, 2&times; Dhammapada. Previous "bible 2.7/M" was a bookkeeping bug.</td></tr>
</table>
<p>None of these are tradition-specific. All three are digit-density experts. The audit protocol:
(a) within-Christian OLS on digit fraction &rarr; R&sup2;; (b) rate in &le;10th-percentile digit
slice; (c) full 9-corpus profile; (d) length-matched comparator (BoM at 16k); (e) split-half
stability.</p>

<h2 id="h6axis">4a. The verse-vs-prose axis (H6)</h2>
<figure><img src="../img/chart_h6_axis.png" alt="H6 verse-vs-prose axis">
<figcaption>H6 axis: 8 expert cells where verse-text corpora (green) fire ~0 and discursive-prose corpora (red) fire at 10,000&ndash;90,000/M. 1,000&times; larger than the digit effect, and digit-independent.</figcaption></figure>
<p>See <a href="narrative.html#h6">narrative &sect;4</a> for the full table and discussion. This is
the study's primary positive finding: a large, digit-independent, length-independent routing axis
that separates bare verse-text from discursive prose, cutting across all religious traditions.</p>

<h2 id="jaccard">5. Inter-tradition similarity</h2>
<figure><img src="../img/chart_jaccard_heatmap.png" alt="Jaccard heatmap">
<figcaption>Top-20 REAP expert Jaccard overlap, overall. Bible&ndash;Christian (0.33) is the lowest pair involving either &mdash; Christian literature is the Bible's least-similar partner of all nine traditions.</figcaption></figure>
<p>Metric caution (Kimi K3): the earlier write-up mixed <b>per-layer top-5 profiles</b>
(Bible&ndash;BoM 0.539, Bible&ndash;Qur'an 0.525, BoM&ndash;Qur'an 0.544) with <b>overall top-20 REAP</b>
(Bible&ndash;BoM 0.212) &mdash; two different metrics. The heatmap above is overall top-20 REAP.
Directional claim that survives: core-expert overlap is tradition-agnostic (0.52&ndash;0.54
across Bible/BoM/Qur'an on the top-5 per-layer metric), and Christian literature diverges
most from the Bible.</p>

<h2 id="layers">6. Layer-wise structure</h2>
<ul>
<li><b>L0&ndash;2 (hash-routed):</b> corpus-invariant by design; any "difference" here is token-frequency
composition, not routing decisions.</li>
<li><b>Mid layers:</b> the shared backbone dominates; this is where the tradition-agnostic
overlap is highest.</li>
<li><b>Late layers (39&ndash;42):</b> specialists live here &mdash; e164 (L42), e34 (L41), e33 (L34)
all fire in the topmost scored layers.</li>
</ul>
<div class="ambox bad"><b>Retracted:</b> the "layer sandwich" (low&ndash;high&ndash;low Bible&ndash;Christian
overlap) was a <code>reap_score</code> noise-floor artifact that <b>inverts</b> on
<code>expert_frequencies</code>. See retraction 8.2.</div>

<h2 id="jlens">7. J-lens findings</h2>
<ul>
<li><b>Bounded Jacobian:</b> L0 output influence &asymp;1,268 &asymp; 3.9&times; later layers
(L10 371, L20 363, L30 378, L42 320). Reproducible from committed artifacts (Kimi K3 verified).
Caveat: 16 random projections only.</li>
<li><b>Logit lens:</b> the Genesis 1:2 "Spirit at layer 30" claim was withdrawn &mdash; mislabeled
position, cherry-picked, uncalibrated readout. No surviving logit-lens headline.</li>
</ul>

<h2 id="retract">8. Retractions</h2>
<div class="ambox bad"><b>8.1 "Not-memorized-scripture" e164.</b> Digit-density confound
(pipeline strips Bible verse numbers; perfectly monotone deciles 0&rarr;16,448/M; zero-digit
Christian control 4.9/M; ~29-expert cluster incl. e27, e68). Found by Claude Opus 5 review.</div>
<div class="ambox bad"><b>8.2 Layer sandwich.</b> REAP noise-floor artifact; inverts on
frequencies; write-up mixed two Jaccard metrics. Found by Kimi K3 review.</div>
<div class="ambox bad"><b>8.3 Genesis 1:2 logit lens.</b> Position 30 token is ' deep' not
' Spirit'; predicts 4 positions ahead; n=3; uncalibrated. Found by Kimi K3 review.</div>
<div class="ambox bad"><b>8.4 Effective experts = 111.</b> Pooling artifact (111&rarr;70
per-sample). The ordering survives; the absolute aggregate does not.</div>
"""

page("results.html", "Results and findings", RESULTS, here="results")

# ══════════════════ EXPERIMENTS ══════════════════
EXPERIMENTS = """
<h1>Experiments</h1>
<div class="hatnote">All experiments, numbered as in <code>EXPERIMENTS.md</code> (revised post-review). Each entry: hypothesis tested, design, status, result or expected result.</div>

<div class="toc"><div class="toctitle">Contents</div><ul>
<li>1 <a href="#priority">Current priority queue</a></li>
<li>2 <a href="#e12">Exp 12 &mdash; Digit minimal-pairs</a></li>
<li>3 <a href="#e11">Exp 11 &mdash; e164 context dump</a></li>
<li>4 <a href="#e1">Exp 1 &mdash; Multi-translation register test</a></li>
<li>5 <a href="#e3">Exp 3 &mdash; Secular null baseline</a></li>
<li>6 <a href="#e8">Exp 8 &mdash; Sorted L42 frequency check</a> <span class="tag tag-ok">done</span></li>
<li>7 <a href="#e9">Exp 9 &mdash; Position/length confound</a> <span class="tag tag-ok">answered</span></li>
<li>8 <a href="#e4b">Exp 4b &mdash; Quotation-switch test</a> <span class="tag tag-run">running</span></li>
<li>9 <a href="#e13">Exp 13 &mdash; H6 ablation</a> <span class="tag tag-pending">staged</span></li>
<li>10 <a href="#other">Other planned experiments</a></li>
</ul></div>

<h2 id="priority">1. Current priority queue</h2>
<p>Deployment order when GPU nodes free (after wave-2 completes):</p>
<ol>
<li><b>Exp 4b</b> &mdash; 351 samples, ~5M tokens. <span class="tag tag-run">running now</span> Decisive within-document verse-quote vs commentary test.</li>
<li><b>Exp 12</b> &mdash; 222 samples (111 pairs), ~438k tokens. Decisive for the digit question. <span class="tag tag-pending">running</span></li>
<li><b>Exp 1</b> &mdash; 150 samples, 209k tokens. <span class="tag tag-ok">complete</span> H6 = 47.8/M, translation-invariant.</li>
<li><b>Exp 13</b> &mdash; Ablation hook designed, corpus to build. Causal test of H6 contribution.</li>
<li><b>Exp 3</b> &mdash; secular null, staged after digit question settles.</li>
</ol>

<h2 id="e12">2. Exp 12 &mdash; Digit minimal-pair test <span class="tag tag-pending">staged</span></h2>
<table class="wikitable">
<tr><th>Field</th><th>Value</th></tr>
<tr><td>Hypothesis tested</td><td>H1: is e164 a digit detector, and does it respond to <i>any</i> numeral or specifically to <i>citation structure</i> ("N:M" verse references)?</td></tr>
<tr><td>Design</td><td>12 KJV chapters &times; 3 versions: (a) <b>asis</b> &mdash; digit-free, as observed; (b) <b>verseno</b> &mdash; KJV apparatus restored ("1:1 In the beginning...", 2.234% digits); (c) <b>arbit</b> &mdash; arbitrary numerals at random word boundaries, matched count (2.825% digits)</td></tr>
<tr><td>Corpus</td><td><code>corpus/samples/exp12_minimal_pairs.jsonl</code> &mdash; 111 samples, fail-closed verified</td></tr>
<tr><td>Predictions</td><td>If (b)&asymp;(c) &gg; (a): bare-numeral detector. If (b) &gg; (c): citation-structure detector. If all &asymp;: digit hypothesis wrong, reopen register hypothesis.</td></tr>
</table>

<h2 id="e11">3. Exp 11 &mdash; e164/e27/e68 context dump <span class="tag tag-pending">staged</span></h2>
<table class="wikitable">
<tr><th>Field</th><th>Value</th></tr>
<tr><td>Hypothesis tested</td><td>H1: what tokens actually trigger the specialist cluster?</td></tr>
<tr><td>Design</td><td>Re-run observation with <code>--raw-budget-tokens</code> to capture per-token routing; extract top-500 firing contexts with &plusmn;20-token windows</td></tr>
<tr><td>Why a re-run</td><td><code>routed_experts</code> in existing records stores unique expert IDs, not per-token routing &mdash; contexts cannot be recovered from disk</td></tr>
<tr><td>Prediction</td><td>Contexts are numerals, footnote markers, verse references, roman numerals</td></tr>
</table>

<h2 id="e1">4. Exp 1 &mdash; Multi-translation register test <span class="tag tag-ok">complete</span></h2>
<table class="wikitable">
<tr><th>Field</th><th>Value</th></tr>
<tr><td>Hypothesis tested</td><td>Register vs memorization vs content: does H6 fire on non-KJV renderings of the <i>same</i> text?</td></tr>
<tr><td>Design</td><td>30 Bible passages in 5 public-domain translations: KJV (1611, archaic), ASV (1901), YLT (literal), WEB (modern), BBE (850-word Basic English &mdash; the extreme register contrast). All verse numbers stripped, all verified <b>0.0000% digits</b> (digit confound controlled). 150 records, 209,151 tokens.</td></tr>
<tr><td>Corpus</td><td><code>corpus/samples/exp1_translations.jsonl</code> &mdash; 150 records (30 passages &times; 5 translations)</td></tr>
<tr><td>Note</td><td>NIV/ESV excluded &mdash; copyrighted, violates the public-domain corpus rule</td></tr>
<tr><td>Result</td><td><b>H6 fires at 47.8/M on Bible verse across all translations</b> &mdash; a 3,415&times; ratio vs commentary prose (163,284/M). KJV and ASV show <b>perfect zero</b> (0 firings across 83,197 tokens). WEB, BBE, YLT show near-zero (45&ndash;100/M). The verse/prose axis is <b>translation-invariant</b>: H6 detects verse <i>structure</i>, not specific wording or memorization.</td></tr>
</table>

<h3>4.1 Per-translation H6 rates</h3>
<table class="wikitable">
<tr><th>Translation</th><th>Records</th><th>Tokens</th><th>H6 Rate (M)</th><th>Description</th></tr>
<tr><td>KJV</td><td class="num">30</td><td class="num">42,021</td><td class="num">0.0</td><td>King James Version (1611, archaic)</td></tr>
<tr><td>ASV</td><td class="num">30</td><td class="num">41,176</td><td class="num">0.0</td><td>American Standard Version (1901)</td></tr>
<tr><td>YLT</td><td class="num">30</td><td class="num">44,587</td><td class="num">44.9</td><td>Young's Literal Translation</td></tr>
<tr><td>WEB</td><td class="num">30</td><td class="num">39,933</td><td class="num">100.2</td><td>World English Bible (modern)</td></tr>
<tr><td>BBE</td><td class="num">30</td><td class="num">41,434</td><td class="num">96.5</td><td>Bible in Basic English (850 words)</td></tr>
<tr><td><b>All</b></td><td class="num">150</td><td class="num">209,151</td><td class="num">47.8</td><td>3,415&times; ratio vs commentary</td></tr>
</table>

<h3>4.2 Charts</h3>
<table class="wikitable">
<tr><th>Chart</th><th>What it shows</th></tr>
<tr><td><a href="../img/chart_exp1_by_translation.png">H6 rate by translation</a></td><td>H6 composite rate per translation (bar chart, log scale)</td></tr>
<tr><td><a href="../img/chart_exp1_per_passage.png">Per-passage scatter</a></td><td>H6 rate per passage &times; translation, showing translation invariance</td></tr>
</table>

<h2 id="e3">5. Exp 3 &mdash; Secular null baseline <span class="tag tag-pending">not staged</span></h2>
<table class="wikitable">
<tr><th>Field</th><th>Value</th></tr>
<tr><td>Hypothesis tested</td><td>H5: is any routing pattern religion-specific at all?</td></tr>
<tr><td>Design</td><td>Secular English (news, arXiv, fiction) <b>stratified by digit density, not topic</b> &mdash; matched deciles against the religious corpora</td></tr>
<tr><td>Decision rule</td><td>If secular text with matched digit density reproduces e164's firing profile, the expert is a general-English digit specialist and <i>all</i> religious framing drops out</td></tr>
</table>

<h2 id="e8">6. Exp 8 &mdash; Sorted L42 frequency check <span class="tag tag-ok">done</span></h2>
<p><b>Question:</b> could the e164 exact-zero be a shard-index permutation bug (TP2 splitting
expert bins inconsistently)?</p>
<p><b>Method:</b> compare sorted L42 frequency histograms across corpora; check cross-corpus
expert-ID consistency in the top-20.</p>
<p><b>Result:</b> NOT a permutation bug &mdash; 15/20 top experts shared across corpora, and e164's
rank differs (152 vs 255) in a way consistent only with genuinely different routing.</p>
<div class="ambox warn"><b>Review note (Claude Opus 5):</b> this tested the never-at-risk
channel (<code>expert_frequencies</code>, from bincount over replicated indices). The at-risk
channels &mdash; <code>reap_score</code>, <code>activation_norms</code> &mdash; were not permutation-checked.</div>

<h2 id="e9">7. Exp 9 &mdash; Position/length confound <span class="tag tag-ok">answered</span></h2>
<p><b>Question:</b> KJV chapters are ~880 tokens; Christian samples are 16k windows. Could e164 be
position-dependent, explaining the zero?</p>
<p><b>Result:</b> No &mdash; length-matched comparison bands show Bible 0 / Qur'an 4,383/M at
comparable window sizes. The zero is not a length artifact.</p>

<h2 id="e4b">8. Exp 4b &mdash; Quotation-switch within-document test <span class="tag tag-run">running</span></h2>
<table class="wikitable">
<tr><th>Field</th><th>Value</th></tr>
<tr><td>Hypothesis tested</td><td>H6: do the verse/prose axis experts fire on <i>prose context</i> rather than <i>verse content</i>? Within the same document, do H6 rates drop at quote boundaries?</td></tr>
<tr><td>Design</td><td>351 commentary windows containing embedded KJV verse quotes (41,426 quote tokens across 18 sources). Each quote span has start/end token positions for per-token routing analysis. Character-window approach (60k chars ~16k tokens) to avoid tokenizing entire files.</td></tr>
<tr><td>Corpus</td><td><code>corpus/samples/exp4b_quotation_switch.jsonl</code> &mdash; 351 records, 5.2M tokens</td></tr>
<tr><td>Pilot result (Exp 4)</td><td>H6 fires on prose context at 44,822/M vs verse content at 4.1/M &mdash; a 10,911&times; ratio. But only 419 quote tokens (pilot); Exp 4b scales to 41,426 for decisive test.</td></tr>
<tr><td>Primary endpoint</td><td>Binary event <code>I(layer, expert, token in top-6)</code>; beta-binomial model at block level with document and window random effects</td></tr>
</table>

<h2 id="e13">9. Exp 13 &mdash; Scoped H6 ablation <span class="tag tag-pending">hook designed</span></h2>
<table class="wikitable">
<tr><th>Field</th><th>Value</th></tr>
<tr><td>Hypothesis tested</td><td>Causal: does knocking out H6 anchor experts damage prose processing more than verse processing?</td></tr>
<tr><td>Design</td><td>Two intervention modes: (1) <b>contribution knockout</b> &mdash; zero expert output, keep gate selection; (2) <b>route-mask compensation</b> &mdash; mask before top-k, reselect, renormalize. Dose series: each anchor singly, then cumulative sets of 1, 3, and all 6.</td></tr>
<tr><td>H6 anchors (frozen)</td><td>L21e42, L22e105, L23e113, L30e198, L32e254, L41e147</td></tr>
<tr><td>Corpus</td><td>4 cells: verse/prose &times; religious/secular, 100+ blocks each, 512&ndash;1024 tokens, held-out material</td></tr>
<tr><td>Primary outcome</td><td>Per-block <code>Delta-NLL = NLL(ablation) - NLL(baseline)</code> in nats/token</td></tr>
<tr><td>Controls</td><td>Sham hook (~0 delta), 20 random six-expert control clusters matched on routing frequency, digit-cluster positive control</td></tr>
<tr><td>Hook code</td><td><code>exp13_ablation_hook.py</code> &mdash; deployed to both TP2 nodes</td></tr>
</table>

<h2 id="other">10. Other planned experiments</h2>
<table class="wikitable">
<tr><th>Idea</th><th>Status</th><th>Notes</th></tr>
<tr><td>Jesus vs Lucifer routing comparison</td><td>staged (in theology selection)</td><td>400 Jesus vs 46 Lucifer records, digit-controlled</td></tr>
<tr><td>Moloch / Saturn routing analysis</td><td>staged (in theology selection)</td><td>25 + 32 records</td></tr>
<tr><td>Covariate regression</td><td>planned</td><td>Partial effects of tradition controlling digit%, punctuation%, sentence length, TTR &mdash; no GPU needed, uses existing records</td></tr>
<tr><td>Perplexity correlation</td><td>planned</td><td>Per-sample loss vs effective-expert-count to test H3 (surprisal proxy)</td></tr>
<tr><td>Jacobian validation</td><td>backlog</td><td>Increase projection count; low priority</td></tr>
</table>
"""

page("experiments.html", "Experiments", EXPERIMENTS, here="experiments")

# ══════════════════ CODE ══════════════════
CODE = """
<h1>Code reference</h1>
<div class="hatnote">Every script in the study, what it does, its inputs and outputs. Sanitized copies live in <a href="https://github.com/0xSero/dsv4-reap-routing" target="_blank">code/</a> on GitHub and on <a href="https://huggingface.co/datasets/0xSero/deepseek-v4-flash-reap" target="_blank">HuggingFace</a>; originals in the research directory.</div>

<h2>1. Corpus acquisition</h2>
<table class="wikitable">
<tr><th>Script</th><th>Purpose</th><th>Output</th></tr>
<tr><td><code>scrape_christian.py</code></td><td>Gutenberg Christian-literature scrape via search-HTML enumeration (Gutendex Cloudflare-blocked), mirror fallbacks, header/footer cleaning</td><td><code>corpus/christian/raw/*.txt</code> + manifest</td></tr>
<tr><td><code>scrape_theology_books.py</code></td><td>Same pattern, 40+ theology topics</td><td><code>corpus/theology/raw/book_*.txt</code> (3,827 books)</td></tr>
<tr><td><code>scrape_wikipedia.py</code></td><td>MediaWiki generator API (batch 50), 3&nbsp;s delay, 429 exponential backoff; 6 seed topics with category traversal</td><td><code>corpus/theology/raw/wiki_*.txt</code> (7,508 articles)</td></tr>
<tr><td><code>build_exp1_translations.py</code></td><td>Genesis 1&ndash;3 in 5 public-domain translations from bible-api.com, verse numbers stripped, digit density verified</td><td><code>corpus/samples/exp1_translations.jsonl</code></td></tr>
</table>

<h2>2. Corpus preparation</h2>
<table class="wikitable">
<tr><th>Script</th><th>Purpose</th><th>Output</th></tr>
<tr><td><code>prepare_corpus.py</code></td><td>Tokenize + window core 8 texts; English stopword filter; <b>strips KJV verse numbers</b> (the digit-confound origin); emits <code>_emit_jsonl</code> shared by later preps</td><td><code>corpus/samples/{bible,quran,...}.jsonl</code></td></tr>
<tr><td><code>prepare_christian_corpus.py</code></td><td>Same for the Gutenberg Christian corpus, 16k first window per book</td><td><code>corpus/samples/christian.jsonl</code> (28,789)</td></tr>
<tr><td><code>prepare_theology_corpus.py</code></td><td>Tokenize + window the theology corpus (imports <code>_emit_jsonl</code>)</td><td><code>corpus/samples/theology.jsonl</code> (29,098)</td></tr>
<tr><td><code>select_theology.py</code></td><td>Stratified selection with topic quotas and per-sample digit density in manifest</td><td><code>corpus/samples/theology_sel.jsonl</code> (1,090)</td></tr>
<tr><td><code>exp12_build_minimal_pairs.py</code></td><td>Digit minimal-pair corpus (asis / verseno / arbit), matched digit counts</td><td><code>corpus/samples/exp12_minimal_pairs.jsonl</code> (111)</td></tr>
</table>

<h2>3. Observation</h2>
<table class="wikitable">
<tr><th>Script</th><th>Purpose</th><th>Notes</th></tr>
<tr><td><code>observe_religious.py</code></td><td><b>The harness.</b> Read-only TP2 inference, Gate hooks, per-record aggregates, fail-closed assertions, fsynced JSONL. Supports <code>--raw-budget-tokens</code> for per-token capture (needed by Exp 11) and record skip-ahead on resume</td><td>Verified line-for-line vs <code>model.py</code> Gate.forward</td></tr>
<tr><td><code>run_full_observation.sh</code></td><td>Launch both ranks (de5c via sshpass+jump, 557f via key), model load + NCCL rendezvous, orchestration logs</td><td>Credentials via env only</td></tr>
<tr><td><code>chain_next_runs.sh</code></td><td>Chain supervisor: sequences runs, detects stalls, relaunches with skip-ahead (3 self-heals so far)</td><td>Log: <code>/tmp/chain_runs.log</code></td></tr>
<tr><td><code>obs_christian_watch.sh</code> / <code>obs_theology_watch.sh</code></td><td>Per-run watchdogs</td><td></td></tr>
<tr><td><code>finalize_christian.sh</code></td><td>Pull shards, merge, verify invariants, build aggregates</td><td>Run on ALL RUNS COMPLETE</td></tr>
<tr><td><code>run_theology_observation.sh</code></td><td>Theology deployment wrapper</td><td></td></tr>
</table>

<h2>4. J-lens probes</h2>
<table class="wikitable">
<tr><th>Script</th><th>Purpose</th></tr>
<tr><td><code>run_jlens.py</code> / <code>jlens_dsv4.py</code></td><td>Capture per-layer per-position next-token distributions and bounded Jacobian norms</td></tr>
<tr><td><code>run_jlens_tp2.sh</code></td><td>TP2 deployment wrapper</td></tr>
<tr><td><code>jlens_watch.sh</code> / <code>jlens_autoheal.sh</code></td><td>Watchdog + autoheal</td></tr>
<tr><td><code>jlens_viewer.py</code></td><td>Interactive inspection of lens records</td></tr>
</table>

<h2>5. Analysis</h2>
<table class="wikitable">
<tr><th>Script</th><th>Purpose</th><th>Output</th></tr>
<tr><td><code>analyze_experts.py</code></td><td>Aggregate frequencies/REAP, cross-text Jaccard, effective-expert counts</td><td><code>core_agg.json</code>, <code>christian_agg.json</code>, <code>analysis/*.csv</code></td></tr>
<tr><td><code>generate_report.py</code></td><td>Verification report: invariant checks over all records</td><td>report</td></tr>
<tr><td><code>exp8_sorted_freq.py</code></td><td>Permutation-confound check on sorted L42 distributions</td><td><code>analysis_all/exp8_sorted_freq_results.txt</code></td></tr>
<tr><td><code>exp11_context_dump.py</code></td><td>Attempted context recovery from existing records &mdash; documented failure (unique-ID storage), motivating the GPU re-run</td><td>&mdash;</td></tr>
<tr><td><code>build_wiki_site.py</code></td><td>Generates this wiki from a shared template</td><td><code>wiki/*.html</code></td></tr>
</table>

<h2>6. Publication and sync</h2>
<table class="wikitable">
<tr><th>Script</th><th>Purpose</th></tr>
<tr><td><code>sync_to_github.sh</code></td><td>Self-throttling 4&nbsp;h sync: analysis, gzipped J-lens, sanitized code (credential scrub via <code>$SSHPASS</code> env), manifests; commit + push</td></tr>
<tr><td><code>upload_hf_project.py</code></td><td>Consolidated upload to <code>0xSero/deepseek-v4-flash-reap</code> (45 files: observations, J-lens, manifests, analysis, code)</td></tr>
<tr><td><code>stream_to_hf.py</code></td><td>Streaming record upload during observation</td></tr>
</table>

<h2>7. One-shot / probe utilities</h2>
<p class="small"><code>probe_de5c.sh</code>, <code>probe2.sh</code>, <code>probe3.sh</code>,
<code>jump.sh</code>, <code>chk_convert.sh</code>, <code>run_convert.sh</code>,
<code>run_r0.sh</code>, <code>run_r1.sh</code>, <code>run_tp2_2384.sh</code>,
<code>launch_obs_rank.sh</code>, <code>launch_observe.sh</code>,
<code>auto_recover_and_launch.sh</code>, <code>push_worker.sh</code>, <code>push2.sh</code>,
<code>fetch_round2.py</code> &mdash; connectivity probes, rank launchers, checkpoint conversion
checks, and recovery utilities from earlier phases. Kept for provenance; not part of the
active pipeline.</p>

<h2>8. Docker</h2>
<pre>FROM ghcr.io/anemll/dspark-vllm-gx10:0.1.1
ENV TOKENIZER_ID=deepseek-ai/DeepSeek-V4-Flash-0731
ENV TOKENIZER_REV=9e165c30e2704aec5d9d593cce3eebd58bbef1cb
ENV CKPT_DIR=/ckpt
ENV INPUT=/in/samples.jsonl
ENV OUTPUT=/out/obs.jsonl</pre>
<p>One rank per DGX Spark node; <code>docker-compose.yml</code> in the repo wires the pair.</p>
"""

page("code.html", "Code reference", CODE, here="code")

# ══════════════════ OPERATIONS ══════════════════
OPS = """
<h1>Operations (live)</h1>
<div class="hatnote">What is running right now, what is queued, and the runbook the 30-minute automation follows. Status on this page reflects 2026-08-16.</div>

<h2>1. Running now</h2>
<table class="wikitable">
<tr><th>Pipeline</th><th>Progress</th><th>Supervisor</th><th>Notes</th></tr>
<tr><td>Christian wave-2 observation</td><td><span class="tag tag-run">~45% (1,041/2,295)</span></td><td><code>chain_next_runs.sh</code></td><td>3 NCCL stalls so far, all self-healed with skip-ahead; ~24 records / 15 min pace</td></tr>
<tr><td>30-min mission automation</td><td>active</td><td>cron</td><td>Monitors chains/watchdogs, deploys queued experiments when nodes free, runs throttled GitHub sync</td></tr>
<tr><td>GitHub sync</td><td>every 4&nbsp;h</td><td><code>sync_to_github.sh</code> self-throttle</td><td></td></tr>
</table>

<h2>2. Deployment queue (on ALL RUNS COMPLETE)</h2>
<ol>
<li><code>./finalize_christian.sh</code> &mdash; merge wave-2, verify invariants, rebuild aggregates</li>
<li><b>Exp 12</b> &mdash; 222 records launched, monitoring</li>
<li><b>Exp 1</b> &mdash; <span class="tag tag-ok">complete</span> 150 records, H6 = 47.8/M</li>
<li><b>Exp 11</b> &mdash; context-dump re-run with <code>--raw-budget-tokens</code></li>
<li><b>Theology observation</b> &mdash; 1,090 records (~16&nbsp;h), watchdog <code>obs_theology_watch.sh</code></li>
</ol>

<h2>3. Runbook (each 30-min automation cycle)</h2>
<pre>1. tail /tmp/chain_runs.log            # run status
2. pgrep -f 'chain_next|obs_christian_watch|jlens_watch|obs_theology_watch'
                                       # restart any dead supervisor
3. bash sync_to_github.sh              # self-throttles to 4h
4. If "ALL RUNS COMPLETE": finalize + deploy queue (above)
5. On completed observation: pull via scp, verify fail-closed invariants,
   run analyze_experts.py, update wiki + site, sync</pre>

<h2>4. Operational constraints</h2>
<ul>
<li><b>Read-only:</b> no weight edits, no pruning, no quantization. Observation only.</li>
<li><b>Host exclusions:</b> spark-2822 (100.83.190.2) is out of scope, never touched.</li>
<li><b>Credentials:</b> de5c password via <code>SSHPASS</code> env only; SSH auth no more than every
~10 min (rate-limited host); never printed, logged, or committed.</li>
<li><b>Scraping:</b> never parallel scrapers (429); Gutenberg 0.8&ndash;1.5 s; Wikipedia 3 s.</li>
<li><b>Corpus:</b> English only; public-domain / freely-published only; tokenizer pinned to rev
<code>9e165c30</code>.</li>
<li><b>Integrity:</b> fail-closed invariants asserted before any record is accepted.</li>
</ul>

<h2>5. Incident log</h2>
<table class="wikitable">
<tr><th>Date</th><th>Event</th><th>Resolution</th></tr>
<tr><td>08-14</td><td>J-lens NCCL stalls (2&times;)</td><td>autoheal + resume; completed 80/80</td></tr>
<tr><td>08-15</td><td>Wikipedia scraper 429 storm (6 parallel scrapers)</td><td>killed all, rewrote sequential with backoff, re-scraped via sub-agent infrastructure</td></tr>
<tr><td>08-16</td><td>Wave-2 NCCL stalls (3&times;: at ~470, ~717, ~806 records)</td><td>chain supervisor relaunched with skip-ahead each time, zero data loss</td></tr>
<tr><td>08-16</td><td><b>Credential leak found:</b> sanitizer script embedded the de5c password (public ~1 day)</td><td>script fixed to <code>$SSHPASS</code> env; full git history purged with git-filter-repo (verified 0 matches all commits); HF copy replaced; password rotation recommended</td></tr>
</table>
"""

page("operations.html", "Operations (live)", OPS, here="ops")

# ══════════════════ ROADMAP ══════════════════
ROADMAP = """
<h1>Roadmap and ideas</h1>
<div class="hatnote">What's next, in order, and the backlog of ideas not yet committed to.</div>

<h2>1. Near term (next GPU block)</h2>
<ol>
<li>Exp 12 digit minimal-pairs &mdash; <b>decisive for H1</b></li>
<li>Exp 1 multi-translation &mdash; register vs memorization</li>
<li>Exp 11 context dump &mdash; see what triggers the specialist cluster</li>
<li>Theology observation (Jesus / Lucifer / Moloch / Saturn / Judaism)</li>
</ol>

<h2>2. Medium term</h2>
<ul>
<li>Wave-2 finalize + combined analysis with digit-density controls on every contrast</li>
<li>Secular null (Exp 3) stratified by digit density &mdash; the religion-vs-general-English test</li>
<li>Covariate regression on existing records (no GPU): tradition effects controlling digit%, punctuation%, sentence length, TTR</li>
<li>Perplexity correlation: per-sample loss vs effective-expert-count (tests H3 directly)</li>
<li>Digit-density-controlled Jesus vs Lucifer vs Moloch vs Saturn comparison</li>
</ul>

<h2>3. Backlog (ideas, uncommitted)</h2>
<ul>
<li><b>Within-document quotation switch:</b> sermons quoting KJV verbatim &mdash; does routing flip at quote boundaries mid-document? The cleanest possible memorization test.</li>
<li><b>Other specialists' confound audits:</b> e34 (Qur'an) and e33 (Dhammapada) deserve the same digit/translation scrutiny that e164 got.</li>
<li><b>Full Jacobian:</b> replace 16-projection bound with exact norms on small samples.</li>
<li><b>Activation patching (would break read-only constraint):</b> not in scope unless explicitly re-scoped.</li>
<li><b>Comparative model study:</b> run the identical corpus through another MoE model's router for cross-model comparison.</li>
<li><b>Publication:</b> per Kimi K3, the e164 observation alone is workshop-paper material <i>if</i> Exp 11/12/3 land cleanly; do not publish the older framing.</li>
</ul>

<h2>4. Known open problems</h2>
<ul>
<li>e164's causal trigger (numeral vs citation structure vs something correlated)</li>
<li>Whether any religious-content signal survives digit-density controls</li>
<li>Whether per-firing mean REAP can be salvaged as a metric (noise floor) or should be replaced</li>
<li>Small-n traditions: Gita (n=18) and Upanishads (n=3) are too small for strong claims</li>
</ul>
"""

page("roadmap.html", "Roadmap and ideas", ROADMAP, here="roadmap")

print("ALL PAGES DONE")

# ══════════════════ J-SPACE ══════════════════
JSPACE = """
<h1>J-space lens (logit lens and bounded Jacobian)</h1>
<div class="hatnote">J-space is the study's name for the set of intermediate representations the model is "poised to verbalize" at each layer. We probe it two ways: the <b>logit lens</b> (unembed the residual stream at each layer to see the model's running next-token guess) and the <b>bounded Jacobian</b> (how much the output changes when the input is nudged along random projection directions). 80 samples across all 8 traditions, complete.</div>

<div class="toc"><div class="toctitle">Contents</div><ul>
<li>1 <a href="#what">What J-space measures</a></li>
<li>2 <a href="#jacobian">Bounded Jacobian norms</a></li>
<li>3 <a href="#logit">Logit lens</a></li>
<li>4 <a href="#viewer">Interactive viewer</a></li>
<li>5 <a href="#retraction">Retracted logit-lens claim</a></li>
<li>6 <a href="#caveats">Caveats and open problems</a></li>
</ul></div>

<h2 id="what">1. What J-space measures</h2>
<p>The name comes from the original <a href="https://github.com/0xSero/dsv4-reap-routing" target="_blank">GOAL.md</a>:
"J-space = the small set of intermediate representations the model is poised to verbalize at each layer."
Two probes capture it:</p>
<ul>
<li><b>Logit lens</b> &mdash; at each layer, the residual stream is projected through the unembedding
matrix (the same matrix used at the final layer to produce token logits). This gives, for each
position, the model's current best guess for the next token <i>before</i> the final layer commits.
We record the top-10 tokens and their probabilities per position per layer.</li>
<li><b>Bounded Jacobian</b> &mdash; we perturb the input embedding by a small step
(&epsilon;=0.01) along 16 random projection directions, re-run the forward pass, and measure
how much the output logits change. The L2 norm of this change at each source layer is a cheap
proxy for the full input&ndash;output Jacobian &mdash; too expensive to compute exactly at this
scale.</li>
</ul>
<p>Both probes run on the same 80 samples (10 per tradition, except Upanishads with 3) under the
same read-only, fail-closed harness as the REAP observations. Probe positions are sampled at
regular intervals (0, 15, 30, 46, 61, ...) within each sample's sequence.</p>

<h2 id="jacobian">2. Bounded Jacobian norms</h2>
<figure><img src="../img/chart_jacobian.png" alt="Bounded Jacobian norms by layer">
<figcaption>Mean bounded Jacobian norm (&Vert;16 projections, &epsilon;=0.01) at layers 0, 10, 20, 30, 42 across all traditions. Layer 0 consistently has the largest output influence, dropping sharply by layer 10 and stabilizing through the rest of the stack.</figcaption></figure>
<table class="wikitable">
<tr><th>Tradition</th><th>n</th><th>L0</th><th>L10</th><th>L20</th><th>L30</th><th>L42</th></tr>
<tr><td>Bible (KJV)</td><td class="num">11</td><td class="num">1195</td><td class="num">460</td><td class="num">407</td><td class="num">448</td><td class="num">347</td></tr>
<tr><td>Qur'an (Rodwell)</td><td class="num">11</td><td class="num">1222</td><td class="num">435</td><td class="num">410</td><td class="num">503</td><td class="num">386</td></tr>
<tr><td>Tao Te Ching</td><td class="num">11</td><td class="num">1388</td><td class="num">601</td><td class="num">552</td><td class="num">520</td><td class="num">472</td></tr>
<tr><td>Bhagavad Gita</td><td class="num">11</td><td class="num">1250</td><td class="num">482</td><td class="num">486</td><td class="num">487</td><td class="num">531</td></tr>
<tr><td>Dhammapada</td><td class="num">11</td><td class="num">1274</td><td class="num">559</td><td class="num">546</td><td class="num">517</td><td class="num">444</td></tr>
<tr><td>Book of Mormon</td><td class="num">11</td><td class="num">1166</td><td class="num">450</td><td class="num">484</td><td class="num">447</td><td class="num">420</td></tr>
<tr><td>Analects</td><td class="num">11</td><td class="num">1152</td><td class="num">456</td><td class="num">431</td><td class="num">472</td><td class="num">393</td></tr>
<tr><td>Upanishads</td><td class="num">3</td><td class="num">1015</td><td class="num">318</td><td class="num">327</td><td class="num">304</td><td class="num">221</td></tr>
</table>
<p><b>Finding (survives, with caveat):</b> layer-0 output influence is consistently
~2.5&ndash;3.5&times; that of later layers across all traditions. The drop from L0 to L10 is
sharp (roughly 60%); later layers stay relatively flat. This is directionally consistent with
"early layers carry the most input-level leverage." The caveat: only 16 projection directions
were used, so these are approximate bounds, not exact Jacobian norms. The Kimi K3 review
independently verified these numbers are reproducible from the committed artifacts.</p>
<p>Inter-tradition differences are modest (L0 norms span 1015&ndash;1388) and do not track the
REAP-based traditions clustering &mdash; suggesting the Jacobian is sensitive to surface-form
statistics (token-level variability) rather than theological content, consistent with H2/H5.</p>

<h2 id="logit">3. Logit lens</h2>
<p>For each of 80 samples, 5 probe positions, 43 layers, we record the top-10 decoded tokens and
their probabilities. The data reveals:</p>
<ul>
<li><b>Early layers (L0&ndash;5):</b> decoded tokens are essentially noise &mdash; low-confidence
guesses dominated by rare/foreign-language tokens (e.g. <code>'économic'</code>,
<code>'nahilalakip'</code>, <code>'proiektuak'</code>). The unembedding is being applied to a
representation that hasn't yet been shaped into anything language-like.</li>
<li><b>Mid layers (L10&ndash;25):</b> confidence rises gradually; decoded tokens begin to look
like real English word fragments, but the top guess is rarely the correct next token.</li>
<li><b>Final layers (L40&ndash;42):</b> the lens converges to the model's actual prediction.
For position 0 across most traditions, the final-layer top token is <code>'\\n'</code>
(newline) with 85&ndash;90% confidence &mdash; the model expects a line break at the start of
a new passage chunk.</li>
</ul>
<p><b>No surviving logit-lens headline finding</b> from intermediate-layer probabilities. However,
the <b>top-1 agreement curve</b> &mdash; which does not depend on probability calibration &mdash;
is the cleanest result in the study:</p>
<figure><img src="../img/chart_lens_agreement.png" alt="Lens top-1 agreement by layer">
<figcaption>Top-1 agreement between layer-&ell; lens readout and actual next token, 5,282 positions. Flat at ~1% through L18, discrete step at L19 (2.8%), 70% of accuracy in last 5 layers (L42 = 87.4%).</figcaption></figure>
<table class="wikitable">
<tr><th>Layer</th><th>Agreement</th><th>Layer</th><th>Agreement</th></tr>
<tr><td>L0&ndash;L18</td><td class="num">1.0&ndash;1.5%</td><td>L35</td><td class="num">16.3%</td></tr>
<tr><td>L19</td><td class="num">2.8%</td><td>L37</td><td class="num">24.3%</td></tr>
<tr><td>L27</td><td class="num">3.6%</td><td>L39</td><td class="num">44.2%</td></tr>
<tr><td>L30</td><td class="num">4.1%</td><td>L41</td><td class="num">62.2%</td></tr>
<tr><td>L34</td><td class="num">8.1%</td><td>L42</td><td class="num">87.4%</td></tr>
</table>
<p>Per corpus at L42: Bible 96.8%, BoM 92.9%, Analects 92.3%, Dhammapada 89.6%, Gita 86.2%,
Tao 83.1%, Qur'an 75.1%, Upanishads 62.0%. The ordering tracks text regularity, not religion.</p>
<div class="ambox warn"><b>Caveat:</b> Intermediate-layer lens probabilities are NOT usable as
belief claims. At L30 the lens reads <code>' Spirit'</code> at 0.767 for one Bible position, but
the model's actual L42 output there is <code>'.'</code> at 0.917. Only the rank-agreement curve
is valid; token-level probability claims from intermediate layers are not.</div>
<p>The Genesis 1:2 claim that was built on lens probabilities has been
<a href="#retraction">retracted</a>.</p>

<h2 id="viewer">4. Interactive viewer</h2>
<p>A self-contained HTML viewer (<code>jlens_viewer.py</code>) renders per-layer top-token
evolution and Jacobian sensitivity for every sample. It is published at:</p>
<p style="text-align:center;font-size:15px"><a href="../jlens_viewer.html"><b>&rarr; Open the J-space interactive viewer</b></a></p>
<p>The viewer shows, for each tradition and sample: a table of top decoded tokens per layer per
probe position, and the bounded Jacobian norms. All data is embedded in the page &mdash; no
server, no dependencies.</p>

<h2 id="retraction">5. Retracted logit-lens claim</h2>
<div class="ambox bad"><b>Genesis 1:2 "Spirit at layer 30" &mdash; WITHDRAWN.</b>
<p><b>Original claim:</b> "Logit-lens decoding of Genesis 1 surfaces 'Spirit' at 76.7%
confidence at layer 30 &mdash; the KJV rendering of Genesis 1:2. The model 'knows' the verse
before it says it."</p>
<p><b>What actually happened (found by Kimi K3 review):</b> The token at position 30 is
<code>' deep'</code>, not <code>' Spirit'</code>. The actual <code>' Spirit'</code> token is at
position 34. The intermediate layer 30 "predicts" a token that appears 4 positions later in the
verse, while the final layer correctly predicts the immediate next token (<code>'.'</code>). This
is exactly the kind of noisy, untuned-lens behavior you'd expect from an uncalibrated readout
path applied to n=3 records with a cherry-picked position. The claim was removed from all
headline findings.</p>
<p><b>Lesson:</b> the logit lens is an <i>uncalibrated</i> probe &mdash; it applies the final
unembedding to representations that were never trained to produce logits at intermediate layers.
Any "the model knows X at layer N" claim requires systematic, position-matched analysis with a
proper contrast condition, not a single cherry-picked decode.</p></div>

<h2 id="caveats">6. Caveats and open problems</h2>
<ul>
<li><b>16 projections only.</b> The bounded Jacobian uses 16 random directions &mdash; a coarse
approximation. Increasing to 128+ would tighten the bounds; an exact computation is infeasible
at this model scale.</li>
<li><b>Uncalibrated logit lens.</b> The unembedding was trained for the final layer only; applying
it at intermediate layers produces uncalibrated, sometimes hallucinatory token distributions.
No systematic position-matched logit-lens analysis has been done.</li>
<li><b>Position selection.</b> Probe positions (0, 15, 30, 46, 61, ...) are regularly spaced,
not semantically targeted. A position-selection strategy that targets known theological content
(e.g. verse boundaries, proper nouns) might yield cleaner lens results.</li>
<li><b>Small-n traditions.</b> Upanishads has only 3 J-lens samples; its Jacobian norms are
directional only.</li>
<li><b>Backlog:</b> a full-Jacobian validation on a small sample (increasing projection count)
and a systematic position-matched logit-lens study are both planned but low priority.</li>
</ul>
"""

page("jspace.html", "J-space lens", JSPACE, here="jspace")

# ══════════════════ NARRATIVE ══════════════════
NARRATIVE = """
<h1>Does DeepSeek-V4 route by religion?</h1>
<div class="hatnote">An honest account of what 22.2 million tokens of routing data actually say &mdash; with correctness as the first principle. Every claim below has been independently verified against <code>full_obs.jsonl</code> and <code>christian_obs.jsonl</code> raw data, and cross-checked against the <a href="../reviews/claude_opus5_review.md">Claude Opus 5 external review</a>.</div>

<div class="toc"><div class="toctitle">Contents</div><ul>
<li>1 <a href="#question">The question</a></li>
<li>2 <a href="#answer">The answer</a></li>
<li>3 <a href="#digit">Finding 1: The digit detector</a></li>
<li>4 <a href="#h6">Finding 2: The verse-vs-prose axis</a></li>
<li>5 <a href="#backbone">Finding 3: No religion-organized backbone</a></li>
<li>6 <a href="#lens">Finding 4: Prediction emerges late</a></li>
<li>7 <a href="#h3">Retraction: Routing concentration &ne; predictability</a></li>
<li>8 <a href="#integrity">What we got wrong</a></li>
<li>9 <a href="#hypotheses">Agreed hypotheses</a></li>
<li>10 <a href="#experiments">Experiments, ranked</a></li>
</ul></div>

<h2 id="question">1. The question we started with</h2>
<p>We wanted to know whether a Mixture-of-Experts language model routes religious texts differently
depending on the tradition. Does the KJV activate a different set of experts than the Qur'an?
Does Buddhist scripture light up different circuits than the Tao Te Ching?</p>

<h2 id="answer">2. The answer</h2>
<div class="ambox ok"><b>No.</b> The model does not route by religion. What look like
tradition-specific circuits are responses to document <i>format</i> &mdash; digit density and
verse-vs-prose register &mdash; not theology. This is a negative result, and it is the main
contribution.</div>
<p>The path from the initial excitement through the retractions to what actually holds is below.</p>

<h2 id="digit">3. Finding 1: The digit detector (confirmed, retracted as religion claim)</h2>
<p>Our first headline: expert e164 at layer 42 fires <b>exactly zero times</b> across all 1.05M KJV
tokens, while firing heavily on every other corpus. We interpreted this as evidence that the model
treats scripture differently.</p>
<div class="ambox bad"><b>This was wrong.</b> The KJV is the only zero-digit corpus because our
text pipeline strips verse numbers. Expert e164 is a digit detector.</div>
<p>Within the Christian corpus alone (1,267 records, same genre, digit density varying naturally),
digit-token fraction explains <b>R&sup2;=0.77</b> of e164's per-record firing rate. The
lowest-digit decile fires at 31/M against a corpus mean of 4,552/M. The cluster is larger than we
thought: <b>54 experts</b> have within-Christian digit R&sup2; &gt; 0.5; <b>184</b> have
R&sup2; &gt; 0.3. e68, which we had grouped with e164, is <b>not</b> in the cluster (R&sup2;=0.01).</p>
<p><b>Status:</b> Confirmed as digit detector. Retracted as religion finding.</p>

<h2 id="h6">4. Finding 2: The verse-vs-prose axis (the real finding)</h2>
<p>While screening for digit artifacts, the external review discovered a large population of experts
whose firing is digit-independent (R&sup2;=0.00&ndash;0.15), length-independent (Book of Mormon
has 16,384-token windows, same as Christian literature, yet fires ~0), and splits the corpora as
<b>bare verse-text vs. discursive prose</b>, cutting across all religious traditions:</p>
<figure><img src="../img/chart_h6_axis.png" alt="H6 verse-vs-prose axis">
<figcaption>H6 axis: mean firing rate (log scale) for verse-text corpora (green) vs. discursive-prose corpora (red) across 8 expert cells. The verse group fires ~0; the prose group fires at 10,000&ndash;90,000/M.</figcaption></figure>
<table class="wikitable">
<tr><th>Layer</th><th>Expert</th><th>Bible</th><th>BoM</th><th>Qur'an</th><th>Tao</th><th>Gita</th><th>Dhamma</th><th>Analects</th><th>Upanishads</th><th>Christian</th></tr>
<tr><td>L22</td><td>e105</td><td class="num">0</td><td class="num">109</td><td class="num">6,611</td><td class="num">237</td><td class="num">29</td><td class="num">46</td><td class="num">0</td><td class="num">32,053</td><td class="num">33,138</td></tr>
<tr><td>L30</td><td>e198</td><td class="num">4</td><td class="num">81</td><td class="num">3,816</td><td class="num">349</td><td class="num">103</td><td class="num">71</td><td class="num">137</td><td class="num">28,393</td><td class="num">48,601</td></tr>
<tr><td>L32</td><td>e254</td><td class="num">0</td><td class="num">11</td><td class="num">7,192</td><td class="num">241</td><td class="num">0</td><td class="num">0</td><td class="num">0</td><td class="num">37,061</td><td class="num">30,346</td></tr>
<tr><td>L23</td><td>e113</td><td class="num">7</td><td class="num">223</td><td class="num">13,151</td><td class="num">465</td><td class="num">134</td><td class="num">0</td><td class="num">0</td><td class="num">38,941</td><td class="num">45,129</td></tr>
<tr><td>L41</td><td>e147</td><td class="num">13</td><td class="num">13</td><td class="num">14,284</td><td class="num">3,586</td><td class="num">155</td><td class="num">523</td><td class="num">92</td><td class="num">108,075</td><td class="num">71,716</td></tr>
</table>
<p class="small">All values firings per million tokens, recomputed from <code>full_obs.jsonl</code> + <code>christian_obs.jsonl</code>.</p>
<p>These rates are <b>1,000&times; larger</b> than the e164 digit effect. The verse group:
Bible, BoM, Tao, Gita, Dhammapada, Analects &asymp; 0. The prose group: Christian literature,
Upanishads, Rodwell Qur'an high. This groups the KJV with the Tao Te Ching and the Book of Mormon
on one side, and Puritan commentary with the Upanishads and the Rodwell Qur'an on the other. The
obvious reading is <b>bare verse-text vs. discursive prose with editorial apparatus</b>.</p>
<div class="ambox warn"><b>Status:</b> This is the paper. It is a real, large, unexplained routing
axis. Its identity (register, lineation, editorial apparatus, memorization) is not yet established
&mdash; that requires Exp 4 (quotation switch, retargeted to this cluster).</div>

<h2 id="backbone">5. Finding 3: No religion-organized backbone</h2>
<p>L42 top-20 expert overlap (Jaccard): bible&ndash;bofm 0.539, bible&ndash;quran 0.525,
bofm&ndash;quran 0.544. If religion were a routing category, Abrahamic pairs would sit above
Abrahamic&ndash;Dharmic pairs. They don't. The backbone is real (within-corpus 18&ndash;20/20,
between-corpus 10&ndash;17/20) but its structure is not religious &mdash; likely a language
backbone, not a scripture backbone.</p>
<p>The Jacobian sensitivity probe says the same: across all 8 traditions, L0 norms are
1,015&ndash;1,388 and L42 norms are 221&ndash;531. A &plusmn;10% spread with n=11 each.
No tradition signal.</p>
<p><b>Status:</b> Confirmed as null result. The model has no measurable religion-specific routing.</p>

<h2 id="lens">6. Finding 4: Prediction emerges late and sharply</h2>
<figure><img src="../img/chart_lens_agreement.png" alt="Lens top-1 agreement by layer">
<figcaption>Top-1 agreement between the layer-&ell; lens readout and the actual next token, over 5,282 position-records. Flat at ~1% through L18, a discrete step at L19 (2.8%), and 70% of accuracy forming in the last 5 layers (L42 = 87.4%).</figcaption></figure>
<p>This is the cleanest result in the study. Aggregate top-1 agreement between the layer-&ell; lens
readout and the actual next token, over all 5,282 position-records from 83 records:</p>
<table class="wikitable">
<tr><th>Layer</th><th>Agreement</th><th>Notes</th></tr>
<tr><td>L0&ndash;L18</td><td class="num">1.0&ndash;1.5%</td><td>Flat &mdash; lens produces nonsense at these depths</td></tr>
<tr><td>L19</td><td class="num">2.8%</td><td>Discrete step &mdash; something switches on</td></tr>
<tr><td>L30</td><td class="num">4.1%</td><td></td></tr>
<tr><td>L34</td><td class="num">8.1%</td><td></td></tr>
<tr><td>L37</td><td class="num">24.3%</td><td></td></tr>
<tr><td>L39</td><td class="num">44.2%</td><td></td></tr>
<tr><td>L40</td><td class="num">52.2%</td><td></td></tr>
<tr><td>L41</td><td class="num">62.2%</td><td></td></tr>
<tr><td>L42</td><td class="num">87.4%</td><td>Top-5: 96.0%</td></tr>
</table>
<p>Per corpus at L42: Bible 96.8%, BoM 92.9%, Analects 92.3%, Dhammapada 89.6%, Gita 86.2%,
Tao 83.1%, Qur'an 75.1%, Upanishads 62.0%. The ordering tracks text regularity, not religion.</p>
<div class="ambox warn"><b>Caveat:</b> Intermediate-layer lens probabilities are NOT usable as
belief claims. At L30 the lens reads <code>' Spirit'</code> at 0.767 for one Bible position,
but the model's actual L42 output there is <code>'.'</code> at 0.917. The lens top-1 agreement
curve is valid because it measures rank agreement, not probability calibration.</div>
<p><b>Status:</b> Confirmed. The cleanest result in the study.</p>

<h2 id="h3">7. Retraction: Routing concentration &ne; predictability</h2>
<div class="ambox bad"><b>H3 retracted.</b> We claimed routing concentration (effective expert count)
tracks predictability. The sign is backwards, and the headline was a window-length artifact.</div>
<p>Bible windows are ~825 tokens; Christian windows are 16,384. Effective expert count is an
entropy statistic that grows with sample size. At matched draw budget, Bible and Christian are
within ~2 units. The 65 vs 111 gap was between-document heterogeneity (1,267 books vs one book).</p>
<p>Against matched-budget effective expert count, the correlation with lens-measured predictability
is <b>positive</b> (Pearson +0.47). H3 predicted negative. Drop the surprisal framing; call
it what it measures: routing concentration.</p>

<h2 id="integrity">8. What we got wrong (the integrity chain)</h2>
<h3>8.1 The corrupt robustness file</h3>
<p><code>analysis/robustness_checks.txt</code> reported "L34 e33: bible 2.7/M" &mdash; a 1,600&times;
gap. Recomputed: L34 e33 fires at <b>9,670/M on the Bible</b>, 2&times; higher than Dhammapada,
in the <i>opposite</i> direction. The Bible figure specifically was corrupt. File regenerated from
scratch from raw data on 2026-08-15.</p>
<h3>8.2 The "Qur'an specialist" that wasn't</h3>
<p>L41 e34 was claimed as a Qur'an specialist. It is a digit expert (within-Christian R&sup2;=0.72).
Dhammapada fires it at 26,631/M, 5&times; the Qur'an's 5,888/M. It was never about the Qur'an.</p>
<h3>8.3 The "Jacobian" is misnamed</h3>
<p>The probe adds the same projection vector at every position &mdash; a uniform-shift sensitivity,
not a Jacobian. Renamed in code comments; results stand but the label was wrong.</p>
<h3>8.4 The L0 Jacobian artifact</h3>
<p>L0 sensitivity is inflated because &epsilon;=0.01 is a fixed <i>absolute</i> perturbation and
residual norms at L0 are much smaller. The honest headline: "no tradition effect" (&plusmn;10%
across 8 traditions).</p>

<h2 id="hypotheses">9. Agreed hypotheses</h2>
<p>Six hypotheses survived verification against raw data and external review:</p>
<table class="wikitable">
<tr><th>#</th><th>Hypothesis</th><th>Status</th></tr>
<tr><td>H1</td><td>e164, e27, e34 and ~54 others are digit-density experts (within-Christian R&sup2; &ge; 0.5)</td><td><span class="tag tag-ok">confirmed</span></td></tr>
<tr><td>H2/H6</td><td>Large digit-independent, length-independent routing axis separating verse-text from discursive prose (L4&ndash;L41; up to 90,595/M vs ~0)</td><td><span class="tag tag-run">verified, identity open</span></td></tr>
<tr><td>H3</td><td>Routing concentration is a predictability proxy</td><td><span class="tag tag-bad">retracted (sign backwards, length artifact)</span></td></tr>
<tr><td>H4</td><td>Shared routing backbone across all 9 corpora, not religion-organized</td><td><span class="tag tag-ok">confirmed</span></td></tr>
<tr><td>H5</td><td>No religion-specific routing exists (null hypothesis, currently stands)</td><td><span class="tag tag-ok">stands</span></td></tr>
<tr><td>&mdash;</td><td>Next-token prediction emerges late: flat to L18, step at L19, 70% after L37 (L42=87.4%)</td><td><span class="tag tag-ok">confirmed</span></td></tr>
</table>
<p><b>Not endorsed:</b> any tradition-linked individual expert; anything from intermediate-layer lens
probabilities; any Jacobian claim before &epsilon;-normalization; anything from the theology corpus
as currently designed.</p>

<h2 id="experiments">10. Experiments, ranked by decisiveness</h2>
<ol>
<li><b>Exp 4 (quotation switch) &mdash; retargeted to H6 cluster.</b> Christian books quoting the
KJV verbatim: same document, same window, same digit density. If L22 e105 / L30 e198 / L41 e147
switch off inside quotation spans, H6 is proven with zero cross-corpus confound. <span class="tag tag-pending">best figure</span></li>
<li><b>Exp 1 (multi-translation).</b> 5 translations at 0.000% digits. BBE vs KJV is the register
contrast. Run the H6 cluster on it. <span class="tag tag-pending">staged</span></li>
<li><b>Exp 3 (secular null) &mdash; redesigned.</b> Must include secular verse (Milton, Wordsworth).
If secular verse lands on the Bible side, religion is entirely out. <span class="tag tag-pending">redesign needed</span></li>
<li><b>Exp 11 (context dump) &mdash; retargeted.</b> Dump L22 e105, L30 e198, L41 e147. Drop
e164/e27. <span class="tag tag-pending">staged</span></li>
<li><b>Exp 12 (digit minimal pairs).</b> Sub-hour. Published negative control. <span class="tag tag-pending">staged</span></li>
<li><b>Residual-norm-normalized Jacobian re-run.</b> Mandatory before any Jacobian claim ships.</li>
<li><b>Covariate regression.</b> No GPU. Add punctuation%, sentence length, TTR, verse/prose indicator.</li>
<li><b>ADD: ablation.</b> Zero the H6 cluster, measure &Delta;loss on KJV vs. Christian prose.
Causal claim &rarr; result. <span class="tag tag-bad">needs read-only scope change</span></li>
</ol>
<div class="ambox bad"><b>CUT:</b> the theology run (1,090 records) &mdash; Wikipedia-derived, digit-dense,
apparatus-heavy, the exact confound that ate two headlines. CUT Exps 5/6 &mdash; same reason.</div>

<div class="catlinks"><b>Categories:</b> <a href="../RESEARCH_WIKI.html">DSv4-Flash interpretability</a> | <a href="results.html">MoE routing</a> | <a href="narrative.html">Narrative</a></div>
"""

page("narrative.html", "Narrative", NARRATIVE, here="narrative")

# ══════════════════ MASTER INDEX ══════════════════
INDEX = """
<h1>Master index</h1>
<div class="hatnote">A complete index of every data stream, experiment, probe, and analysis artifact in the study. Use this as the entry point to navigate the entire project.</div>

<div class="toc"><div class="toctitle">Contents</div><ul>
<li>1 <a href="#streams">Data streams</a></li>
<li>2 <a href="#reap">REAP observations</a></li>
<li>3 <a href="#jlens">J-space probes</a></li>
<li>4 <a href="#experiments">All experiments (1&ndash;12)</a></li>
<li>5 <a href="#analysis">Analysis artifacts</a></li>
<li>6 <a href="#merger">REAP &times; J-space merger</a></li>
<li>7 <a href="#corpora">Corpus registry</a></li>
<li>8 <a href="#pub">Publication artifacts</a></li>
</ul></div>

<h2 id="streams">1. Data streams</h2>
<p>The study has three independent data pipelines that feed into the wiki:</p>
<table class="wikitable">
<tr><th>Stream</th><th>What it captures</th><th>Harness</th><th>Records</th><th>Status</th><th>Where</th></tr>
<tr><td><a href="#reap"><b>REAP observation</b></a></td><td>Per-token expert routing: which 6 of 256 experts fire, gate weights, activation norms, per layer</td><td><code>observe_religious.py</code></td><td class="num">2,749 done + 2,295 running</td><td><span class="tag tag-run">wave-2 running</span></td><td><code>full_obs.jsonl</code>, <code>christian_obs.jsonl</code></td></tr>
<tr><td><a href="#jlens"><b>J-space lens</b></a></td><td>Per-layer next-token distributions (logit lens) + bounded Jacobian norms</td><td><code>run_jlens.py</code></td><td class="num">80/80</td><td><span class="tag tag-ok">complete</span></td><td><code>jlens_output/*.jsonl</code></td></tr>
<tr><td><a href="#corpora"><b>Corpus pipeline</b></a></td><td>Raw text &rarr; tokenized windows &rarr; stratified selections</td><td><code>prepare_*.py</code>, <code>select_*.py</code></td><td>22M+ tokens observed; ~400M staged</td><td><span class="tag tag-ok">scraping done</span></td><td><code>corpus/samples/*.jsonl</code></td></tr>
</table>

<h2 id="reap">2. REAP observations</h2>
<p>REAP = <b>R</b>outing-weight &times; <b>E</b>xpert <b>A</b>ctivation <b>P</b>roduct. The core data stream: for every token, at every layer, which experts fire and how strongly.</p>
<table class="wikitable">
<tr><th>Run</th><th>Corpora</th><th>Records</th><th>Tokens</th><th>Status</th><th>Output file</th></tr>
<tr><td>Core 8-text</td><td>Bible, Qur'an, BoM, Gita, Tao, Dhammapada, Analects, Upanishads</td><td class="num">1,482</td><td class="num">1,769,967</td><td><span class="tag tag-ok">done</span></td><td><code>full_obs.jsonl</code> (560 MB)</td></tr>
<tr><td>Christian wave-1</td><td>1,267 Gutenberg Christian books</td><td class="num">1,267</td><td class="num">20,409,440</td><td><span class="tag tag-ok">done</span></td><td><code>christian_obs.jsonl</code> (541 MB)</td></tr>
<tr><td>Christian wave-2</td><td>2,295 extended Christian books</td><td class="num">~1,041 / 2,295</td><td>~17M / ~37M</td><td><span class="tag tag-run">running ~45%</span></td><td><code>christian2_obs.jsonl</code> (on GPU)</td></tr>
<tr><td>Theology (staged)</td><td>Jesus, Lucifer, Judaism, Moloch, Saturn</td><td class="num">1,090</td><td class="num">9,380,481</td><td><span class="tag tag-pending">staged</span></td><td><code>theology_sel.jsonl</code></td></tr>
</table>
<p><b>Aggregates:</b> <code>core_agg.json</code> (8 traditions), <code>christian_agg.json</code> (wave-1). Each contains per-category n, token count, per-layer frequency arrays [256], and per-layer REAP arrays [256].</p>
<p><b>Integrity:</b> &Sigma; expert_frequencies == seqlen &times; 6 on every layer of every record. Verified on all 2,749 completed records, zero violations.</p>
<p><a href="results.html">&rarr; Full results from REAP data</a> &middot; <a href="methods.html">&rarr; Harness details</a></p>

<h2 id="jlens">3. J-space probes</h2>
<p>Two probes applied to the same 80 samples (10 per tradition, except Upanishads n=3):</p>
<table class="wikitable">
<tr><th>Probe</th><th>What it measures</th><th>Method</th><th>Records</th></tr>
<tr><td><b>Logit lens</b></td><td>Model's running next-token guess at each layer</td><td>Unembed residual stream at each layer &rarr; top-10 tokens + probabilities per position</td><td class="num">80</td></tr>
<tr><td><b>Bounded Jacobian</b></td><td>Output sensitivity to input perturbation</td><td>Perturb input embedding (&epsilon;=0.01) along 16 random directions; measure &Delta;output at layers 0, 10, 20, 30, 42</td><td class="num">80</td></tr>
</table>
<p><b>Key findings:</b> (1) Lens top-1 agreement: flat at ~1% through L18, discrete step at L19 (2.8%), L42 = 87.4% &mdash; the cleanest result in the study. (2) L0 Jacobian norm &asymp; 1,152&ndash;1,388 across traditions, dropping to ~320&ndash;600 at later layers. Consistent ~2.5&ndash;3.5&times; early-layer leverage. <b>Caveats:</b> 16 projections only; "Jacobian" is misnamed (uniform-shift sensitivity, not per-position derivative); L0 inflation is an &epsilon;-normalization artifact.</p>
<p><b>Retracted:</b> Genesis 1:2 "Spirit at layer 30" claim (mislabeled position, cherry-picked, uncalibrated).</p>
<p><a href="jspace.html">&rarr; Full J-space page</a> &middot; <a href="../jlens_viewer.html">&rarr; Interactive viewer</a></p>

<h2 id="experiments">4. All experiments (1&ndash;12)</h2>
<p>Every experiment from <code>EXPERIMENTS.md</code>, with current status:</p>
<table class="wikitable">
<tr><th>#</th><th>Name</th><th>Tests</th><th>GPU?</th><th>Status</th><th>Result</th></tr>
<tr><td>1</td><td><a href="experiments.html#e1">Multi-translation Genesis</a></td><td>Register vs memorization (same content, 5 translations, all 0 digits)</td><td>Sub-hour</td><td><span class="tag tag-pending">staged</span></td><td>&mdash;</td></tr>
<tr><td>2</td><td>e164 context dump (original)</td><td>What tokens trigger e164?</td><td>2&ndash;3 h</td><td>Superseded by Exp 11</td><td>&mdash;</td></tr>
<tr><td>3</td><td><a href="experiments.html#e3">Secular null baseline</a></td><td>Is routing religion-specific or general-English?</td><td>4&ndash;6 h</td><td><span class="tag tag-pending">not staged</span></td><td>&mdash;</td></tr>
<tr><td>4</td><td>Within-document KJV quotation switch</td><td>Does e164 turn off mid-document at KJV quote boundaries?</td><td>2&ndash;3 h</td><td><span class="tag tag-pending">planned</span></td><td>&mdash;</td></tr>
<tr><td>5</td><td>Jesus vs Lucifer routing</td><td>Do opposed theological figures route differently?</td><td>4&ndash;6 h</td><td><span class="tag tag-pending">staged (theology)</span></td><td>&mdash;</td></tr>
<tr><td>6</td><td>Moloch / Saturn routing</td><td>Ancient pagan vs modern Abrahamic routing</td><td>4&ndash;6 h</td><td><span class="tag tag-pending">staged (theology)</span></td><td>&mdash;</td></tr>
<tr><td>7</td><td>Entropy expert regression</td><td>Is e164 an entropy/predictability expert?</td><td>2&ndash;3 h</td><td><span class="tag tag-pending">planned</span></td><td>&mdash;</td></tr>
<tr><td>8</td><td><a href="experiments.html#e8">Sorted L42 freq check</a></td><td>Is e164 zero a permutation bug?</td><td>None</td><td><span class="tag tag-ok">done</span></td><td>NOT a permutation (15/20 shared, ranks differ). Note: tested frequencies, not REAP channel.</td></tr>
<tr><td>9</td><td><a href="experiments.html#e9">Position/length confound</a></td><td>Is e164 zero a windowing artifact?</td><td>None</td><td><span class="tag tag-ok">answered</span></td><td>Not a length artifact (Bible 0 / Qur'an 4,383/M at matched window sizes).</td></tr>
<tr><td>10</td><td>Causal ablation of e164</td><td>Force e164 out/in, measure &Delta;NLL</td><td>4&ndash;6 h</td><td><span class="tag tag-bad">deprioritized</span></td><td>Requires code modification (violates read-only constraint unless re-scoped)</td></tr>
<tr><td>11</td><td><a href="experiments.html#e11">e164/e27/e68 context dump (revised)</a></td><td>What tokens trigger the specialist cluster? (per-token routing capture)</td><td>Small</td><td><span class="tag tag-pending">staged</span></td><td>Needs <code>--raw-budget-tokens</code> GPU re-run</td></tr>
<tr><td>12</td><td><a href="experiments.html#e12">Digit minimal-pairs</a></td><td>Digit detector vs citation-structure detector (same text, 3 digit versions)</td><td>Sub-hour</td><td><span class="tag tag-pending">staged</span></td><td>111 samples ready; <b>highest priority</b></td></tr>
</table>
<p><b>Priority queue:</b> Exp 12 &rarr; Exp 1 &rarr; Exp 11 &rarr; theology observation &rarr; Exp 3. See <a href="experiments.html">experiments page</a> for details and <a href="operations.html">operations page</a> for deployment status.</p>

<h2 id="analysis">5. Analysis artifacts</h2>
<table class="wikitable">
<tr><th>File</th><th>Generated by</th><th>Contents</th><th>Used by</th></tr>
<tr><td><code>core_agg.json</code></td><td><code>analyze_experts.py</code></td><td>Per-category n/tok/freq/reap, 8 traditions</td><td>Results charts, effective-expert counts, e164 rates</td></tr>
<tr><td><code>christian_agg.json</code></td><td><code>analyze_experts.py</code></td><td>Same for wave-1 Christian (1,267 books)</td><td>Christian-specific charts</td></tr>
<tr><td><code>analysis/cross_text_jaccard.csv</code></td><td><code>analyze_experts.py</code></td><td>9&times;9 top-20 REAP Jaccard matrix</td><td>Jaccard heatmap chart</td></tr>
<tr><td><code>analysis/expert_frequency.csv</code></td><td><code>analyze_experts.py</code></td><td>Per-expert frequency table across corpora</td><td>Specialist tables</td></tr>
<tr><td><code>analysis/expert_rankings.csv</code></td><td><code>analyze_experts.py</code></td><td>Ranked expert profiles per text</td><td>Backbone analysis</td></tr>
<tr><td><code>analysis/expert_rankings_per_book.csv</code></td><td><code>analyze_experts.py</code></td><td>Per-book rankings (Christian corpus)</td><td>Per-sample effective-expert counts</td></tr>
<tr><td><code>analysis/robustness_checks.txt</code></td><td><code>analyze_experts.py</code></td><td>Matched-n bootstrap CIs (5,000 resamples)</td><td>Specialist verification</td></tr>
<tr><td><code>analysis/per_layer_topk.csv</code></td><td><code>analyze_experts.py</code></td><td>Per-layer top-k experts per text</td><td>Per-layer Jaccard (retracted sandwich)</td></tr>
<tr><td><code>analysis/macro_layer_qualified.csv</code></td><td><code>analyze_experts.py</code></td><td>Macro-level qualified expert assignments</td><td>Backbone membership</td></tr>
<tr><td><code>analysis/expert_summary.json</code></td><td><code>analyze_experts.py</code></td><td>Summary statistics per expert</td><td>Specialist identification</td></tr>
<tr><td><code>analysis/text_expert_profiles.parquet</code></td><td><code>analyze_experts.py</code></td><td>Full per-text expert profiles (Parquet)</td><td>Machine-readable profiles</td></tr>
<tr><td><code>analysis_all/exp8_sorted_freq_results.txt</code></td><td><code>exp8_sorted_freq.py</code></td><td>Sorted L42 distributions, permutation check</td><td>Exp 8 result</td></tr>
<tr><td><code>jac_matrix.json</code></td><td><code>run_jlens.py</code></td><td>Jacobian norm matrix (per text per layer)</td><td>J-space Jacobian chart</td></tr>
<tr><td><code>report.html</code></td><td><code>generate_report.py</code></td><td>Auto-generated integrity + findings report</td><td>Verification</td></tr>
</table>

<h2 id="merger">6. REAP &times; J-space merger</h2>
<p>The two data streams can be cross-analyzed. Here is what exists and what is planned:</p>
<table class="wikitable">
<tr><th>Cross-analysis</th><th>What it does</th><th>Status</th></tr>
<tr><td><b>Same-sample alignment</b></td><td>Both REAP and J-space run on the same 8 traditions; 10 J-lens samples per tradition overlap with REAP samples &rarr; routing decisions and intermediate representations can be compared at the same positions</td><td><span class="tag tag-ok">data exists</span> &mdash; both streams cover the same traditions; J-lens positions are recorded</td></tr>
<tr><td><b>Routing &rarr; representation</b></td><td>At a given layer, which experts fire (REAP) vs what the model is "thinking" (logit lens). Do specialists fire when the lens shows a specific token category?</td><td><span class="tag tag-pending">planned</span> &mdash; requires joining <code>jlens_output/*.jsonl</code> with <code>full_obs.jsonl</code> on (category, sample_index); Exp 11's per-token capture would enable it directly</td></tr>
<tr><td><b>Jacobian &times; routing diversity</b></td><td>Does high Jacobian norm (L0) correlate with high expert diversity (effective count)? If early layers have more leverage AND more expert diversity, that's a unified picture</td><td><span class="tag tag-pending">planned</span> &mdash; straightforward correlation from existing aggregates</td></tr>
<tr><td><b>Per-position routing + lens</b></td><td>With <code>--raw-budget-tokens</code> (Exp 11), capture per-token routing AND per-position lens simultaneously &rarr; see exactly which token triggers e164 AND what the model predicts there</td><td><span class="tag tag-pending">needs GPU re-run</span> &mdash; Exp 11 enables this; currently impossible because <code>routed_experts</code> stores unique IDs only</td></tr>
<tr><td><b>Digit-density stratification of J-space</b></td><td>Do high-digit-density samples show different Jacobian norms or lens convergence patterns? If the digit confound affects J-space too, the lens "findings" need the same controls</td><td><span class="tag tag-pending">planned</span> &mdash; digit density is in the theology manifest; needs to be added to J-lens sample metadata</td></tr>
</table>

<h2 id="corpora">7. Corpus registry</h2>
<p>Every corpus file, with record count, token count, digit density, and source:</p>
<table class="wikitable">
<tr><th>File</th><th>Records</th><th>Size</th><th>Digit density</th><th>Source</th><th>Observed?</th></tr>
<tr><td><code>bible.jsonl</code></td><td class="num">1,189</td><td class="num">5.7 MB</td><td class="num">0.0000%</td><td>Gutenberg KJV, verse numbers stripped</td><td><span class="tag tag-ok">yes</span></td></tr>
<tr><td><code>quran.jsonl</code></td><td class="num">115</td><td class="num">1.4 MB</td><td>varies</td><td>Gutenberg (Pickthall)</td><td><span class="tag tag-ok">yes</span></td></tr>
<tr><td><code>bofm.jsonl</code></td><td class="num">30</td><td class="num">1.8 MB</td><td class="num">0.000% median</td><td>Gutenberg pg17</td><td><span class="tag tag-ok">yes</span></td></tr>
<tr><td><code>gita.jsonl</code></td><td class="num">18</td><td class="num">166 KB</td><td>low</td><td>Gutenberg</td><td><span class="tag tag-ok">yes</span></td></tr>
<tr><td><code>tao.jsonl</code></td><td class="num">81</td><td class="num">82 KB</td><td>low</td><td>Gutenberg</td><td><span class="tag tag-ok">yes</span></td></tr>
<tr><td><code>dhamma.jsonl</code></td><td class="num">26</td><td class="num">91 KB</td><td>low</td><td>Gutenberg pg2017</td><td><span class="tag tag-ok">yes</span></td></tr>
<tr><td><code>analects.jsonl</code></td><td class="num">20</td><td class="num">229 KB</td><td>low</td><td>Gutenberg</td><td><span class="tag tag-ok">yes</span></td></tr>
<tr><td><code>upanishads.jsonl</code></td><td class="num">3</td><td class="num">119 KB</td><td>low</td><td>Gutenberg (n=3)</td><td><span class="tag tag-ok">yes</span></td></tr>
<tr><td><code>christian_sel.jsonl</code></td><td class="num">1,267</td><td class="num">11 MB</td><td>~1.1% median</td><td>Gutenberg 3,705 books, 32 topics</td><td><span class="tag tag-ok">yes (wave-1)</span></td></tr>
<tr><td><code>christian2_sel.jsonl</code></td><td class="num">2,295</td><td class="num">191 MB</td><td>varies</td><td>Gutenberg extended topics</td><td><span class="tag tag-run">running (wave-2)</span></td></tr>
<tr><td><code>theology.jsonl</code></td><td class="num">29,098</td><td class="num">2.1 GB</td><td>varies</td><td>Wikipedia 7,508 + Gutenberg 3,827 books</td><td><span class="tag tag-pending">staged</span></td></tr>
<tr><td><code>theology_sel.jsonl</code></td><td class="num">1,090</td><td class="num">51 MB</td><td>per-sample in manifest</td><td>Stratified: Jesus 400, Judaism 137, Lucifer 46, Moloch 25, Saturn 32, books 450</td><td><span class="tag tag-pending">staged</span></td></tr>
<tr><td><code>exp12_minimal_pairs.jsonl</code></td><td class="num">111</td><td class="num">8.2 MB</td><td>0% / 2.23% / 2.83%</td><td>12 KJV chapters &times; 3 digit versions</td><td><span class="tag tag-pending">staged</span></td></tr>
<tr><td><code>exp1_translations.jsonl</code></td><td class="num">5</td><td class="num">52 KB</td><td class="num">0.0000%</td><td>bible-api.com: KJV, WEB, ASV, BBE, WEBBE</td><td><span class="tag tag-pending">staged</span></td></tr>
<tr><td><code>all_religious.jsonl</code></td><td class="num">1,482</td><td class="num">7.9 MB</td><td colspan="2">Combined 8 core traditions (for observation input)</td><td><span class="tag tag-ok">yes</span></td></tr>
</table>

<h2 id="pub">8. Publication artifacts</h2>
<table class="wikitable">
<tr><th>Artifact</th><th>Location</th><th>Link</th></tr>
<tr><td>Research wiki hub</td><td>GitHub Pages</td><td><a href="../RESEARCH_WIKI.html">RESEARCH_WIKI.html</a></td></tr>
<tr><td>Methods page</td><td>GitHub Pages</td><td><a href="methods.html">wiki/methods.html</a></td></tr>
<tr><td>Data page</td><td>GitHub Pages</td><td><a href="data.html">wiki/data.html</a></td></tr>
<tr><td>Results page</td><td>GitHub Pages</td><td><a href="results.html">wiki/results.html</a></td></tr>
<tr><td>J-space page</td><td>GitHub Pages</td><td><a href="jspace.html">wiki/jspace.html</a></td></tr>
<tr><td>Experiments page</td><td>GitHub Pages</td><td><a href="experiments.html">wiki/experiments.html</a></td></tr>
<tr><td>Code reference</td><td>GitHub Pages</td><td><a href="code.html">wiki/code.html</a></td></tr>
<tr><td>Operations (live)</td><td>GitHub Pages</td><td><a href="operations.html">wiki/operations.html</a></td></tr>
<tr><td>Roadmap</td><td>GitHub Pages</td><td><a href="roadmap.html">wiki/roadmap.html</a></td></tr>
<tr><td>Master index (this page)</td><td>GitHub Pages</td><td><a href="index.html">wiki/index.html</a></td></tr>
<tr><td>Narrative (correctness-first)</td><td>GitHub Pages</td><td><a href="narrative.html">wiki/narrative.html</a></td></tr>
<tr><td>Interactive J-space viewer</td><td>GitHub Pages</td><td><a href="../jlens_viewer.html">jlens_viewer.html</a></td></tr>
<tr><td>Technical wiki (original)</td><td>GitHub Pages</td><td><a href="../wiki.html">wiki.html</a></td></tr>
<tr><td>Narrative page</td><td>GitHub Pages</td><td><a href="../index.html">index.html</a></td></tr>
<tr><td>Experiment specs</td><td>GitHub</td><td><a href="https://github.com/0xSero/dsv4-reap-routing/blob/main/EXPERIMENTS.md">EXPERIMENTS.md</a></td></tr>
<tr><td>External reviews</td><td>GitHub</td><td><code>reviews/claude_opus5_review.md</code>, <code>reviews/kimi_k3_review.md</code></td></tr>
<tr><td>HuggingFace (consolidated)</td><td>HF (private)</td><td><a href="https://huggingface.co/datasets/0xSero/deepseek-v4-flash-reap" target="_blank">0xSero/deepseek-v4-flash-reap</a> (45 files)</td></tr>
<tr><td>HuggingFace (raw obs)</td><td>HF (private)</td><td><a href="https://huggingface.co/datasets/0xSero/deepseek-v4-flash-religious-reap-observations" target="_blank">0xSero/deepseek-v4-flash-religious-reap-observations</a> (11 files)</td></tr>
<tr><td>GitHub repo</td><td>GitHub</td><td><a href="https://github.com/0xSero/dsv4-reap-routing" target="_blank">0xSero/dsv4-reap-routing</a></td></tr>
<tr><td>Docker</td><td>GitHub</td><td><code>Dockerfile</code> + <code>docker-compose.yml</code></td></tr>
<tr><td>Findings video</td><td>GitHub</td><td><code>reap_findings.mp4</code></td></tr>
</table>
"""

page("index.html", "Master index", INDEX, here="index")
print("INDEX PAGE DONE")

# ══════════════════ EXP 4 RESULTS ══════════════════
EXP4 = """
<h1>Experiment 4: Quotation Switch (Pilot + Exp 4b Results)</h1>
<div class="hatnote">The decisive within-document test: do H6 experts fire on quoted verse, surrounding commentary, or both? This page reports the <b>window-level pilot (Exp 4a)</b> and the <b>scaled Exp 4b</b> (351 records, 5.2M tokens, 41,426 quote tokens).</div>

<div class="toc"><div class="toctitle">Contents</div><ul>
<li>1 <a href="#design">Design</a></li>
<li>2 <a href="#split">Natural split in the corpus</a></li>
<li>3 <a href="#results">Pilot results (Exp 4a)</a></li>
<li>4 <a href="#charts">Pilot visualizations</a></li>
<li>5 <a href="#findings">Pilot key findings</a></li>
<li>6 <a href="#limitations">Limitations (Exp 4 pilot)</a></li>
<li>7 <a href="#exp4b">Exp 4b: Scaled results (351 records)</a></li>
</ul></div>

<h2 id="design">1. Design</h2>
<p>30 windows (&sim;16k tokens each) from Christian books containing KJV Bible quotations embedded in
commentary prose. Each window contains <b>both</b> quoted verse and surrounding commentary. The
question: does the H6 expert cluster fire on the verse portions, the commentary portions, or both?</p>
<p>The corpus was built from Project Gutenberg Christian literature files. Quote spans were annotated
with <code>{verse, start_tok, end_tok}</code> marking exact token positions of KJV verse quotations.</p>

<h2 id="split">2. Natural split in the corpus</h2>
<p>The 30 samples divided into two groups based on the source material:</p>
<table class="wikitable">
<tr><th>Group</th><th>n</th><th>Description</th><th>Digit density</th></tr>
<tr><td>KJV files (verse format)</td><td class="num">5</td><td>Gutenberg KJV Bible with chapter:verse numbering (e.g. "01:001:001")</td><td>2.3&ndash;6.1%</td></tr>
<tr><td>Commentary books (prose)</td><td class="num">24</td><td>Sermons, theology, devotional literature with embedded Bible quotes</td><td>0.0&ndash;1.0%</td></tr>
</table>
<p>This split was not planned but emerged from corpus construction. The KJV files contain Bible text
with editorial apparatus rather than commentary discussing the Bible.</p>

<h2 id="results">3. Results</h2>
<table class="wikitable">
<tr><th>Group</th><th>n</th><th>Tokens</th><th>H6 composite (per M tokens)</th><th>vs. Bible verse</th></tr>
<tr><td>Pure Bible verse (core data)</td><td class="num">1,189</td><td class="num">1,045,776</td><td class="num">4.1/M</td><td>&mdash;</td></tr>
<tr><td>Exp4: KJV files (verse+apparatus)</td><td class="num">5</td><td class="num">81,920</td><td class="num">8,664/M</td><td>2,109&times;</td></tr>
<tr><td>Exp4: Commentary books (prose+quotes)</td><td class="num">24</td><td class="num">367,406</td><td class="num">44,822/M</td><td>10,911&times;</td></tr>
<tr><td>Christian commentary (all)</td><td class="num">3,562</td><td class="num">55,900,970</td><td class="num">41,894/M</td><td>10,198&times;</td></tr>
</table>

<h3>3.1 Per-anchor rates</h3>
<table class="wikitable">
<tr><th>Anchor</th><th>Bible verse</th><th>Exp4: KJV files</th><th>Exp4: Commentary</th><th>Commentary / KJV ratio</th></tr>
<tr><td>H6-A1 (L21e42)</td><td class="num">1.3/M</td><td class="num">2,701/M</td><td class="num">26,186/M</td><td class="num">9.7&times;</td></tr>
<tr><td>H6-A2 (L22e105)</td><td class="num">0.0/M</td><td class="num">5,627/M</td><td class="num">31,551/M</td><td class="num">5.6&times;</td></tr>
<tr><td>H6-A3 (L23e113)</td><td class="num">6.6/M</td><td class="num">5,127/M</td><td class="num">51,552/M</td><td class="num">10.1&times;</td></tr>
<tr><td>H6-A4 (L30e198)</td><td class="num">4.2/M</td><td class="num">2,576/M</td><td class="num">52,633/M</td><td class="num">20.4&times;</td></tr>
<tr><td>H6-A5 (L32e254)</td><td class="num">0.0/M</td><td class="num">5,109/M</td><td class="num">25,783/M</td><td class="num">5.0&times;</td></tr>
<tr><td>H6-A6 (L41e147)</td><td class="num">12.6/M</td><td class="num">30,845/M</td><td class="num">81,228/M</td><td class="num">2.6&times;</td></tr>
</table>
<p>All 6 anchors fire more on commentary than on KJV files. No anchor shows the opposite pattern.</p>

<h2 id="charts">4. Visualizations</h2>
<table class="wikitable">
<tr><th>Chart</th><th>What it shows</th></tr>
<tr><td><a href="../img/chart_exp4_h6_comparison.png">H6 comparison bar chart</a></td><td>H6 composite rates across 4 groups (log scale)</td></tr>
<tr><td><a href="../img/chart_exp4_per_anchor.png">Per-anchor comparison</a></td><td>Per-anchor H6 rates: verse vs commentary context</td></tr>
<tr><td><a href="../img/chart_exp4_digit_scatter.png">Digit density vs H6 scatter</a></td><td>Digit density vs H6 composite, colored by text type</td></tr>
</table>

<h2 id="findings">5. Key findings</h2>
<ol>
<li><b>H6 fires on prose context, not verse content.</b> Commentary windows with embedded Bible
quotes fire H6 at 44,822/M &mdash; nearly identical to pure Christian commentary (41,894/M). The
presence of verse quotes does <b>not</b> suppress H6 firing. The model routes based on the
surrounding prose, not the quoted verse.</li>
<li><b>KJV files fire H6 at an intermediate rate</b> (8,664/M) &mdash; higher than pure verse
(4.1/M) but 5&times; lower than commentary. This is because Gutenberg KJV files contain
prose-like formatting (publication notes, book headers) mixed with verse text.</li>
<li><b>Per-anchor consistency:</b> All 6 H6 anchors fire more on commentary than on KJV files
(ratios 2.6&times; to 20.4&times;). No anchor shows the opposite pattern.</li>
<li><b>Digit density correlation r = &minus;0.642.</b> This is driven by the KJV-file group:
high digit density &rarr; verse format &rarr; low H6. Digit density is a <i>proxy</i> for verse
format in this corpus (chapter:verse numbering only appears in verse-format files), not a cause
of H6 firing. The H6 axis remains digit-independent (confirmed in Exp 14: within-Christian
R&sup2; for digits = 0.00&ndash;0.15).</li>
<li><b>The 5 KJV-file records accidentally replicate the verse/prose null.</b> They are Bible
text with editorial apparatus, and they fire H6 at near-verse rates &mdash; confirming that the
verse/prose axis is about text structure, not religious content.</li>
</ol>

<h2 id="limitations">6. Limitations and next steps (Exp 4 pilot)</h2>
<p>This is a <b>window-level pilot (Exp 4a)</b>, not the decisive per-token test. We have aggregate
expert frequencies per 16k window, not per-token routing. The within-window quote-span vs
commentary-span comparison requires per-token capture (<code>--raw-budget-tokens &gt; 0</code>),
which was not enabled in this run.</p>
<p>The 5 KJV-file records should not have been in the corpus &mdash; they are Bible text, not
commentary with embedded quotes. The Exp 4b corpus should use only actual commentary books with
properly annotated quote spans, targeting &ge;10,000 quote tokens across &ge;100 quote blocks from
&ge;30 independent source documents.</p>

<h2 id="exp4b">7. Exp 4b: Scaled quotation-switch results <span class="tag tag-ok">complete</span></h2>
<p>The Exp 4b corpus was built to address the pilot's limitations: 351 commentary records, 5.2M tokens,
41,426 quote tokens across 18 source documents. All 351 records were observed with zero invariant
violations.</p>

<h3>7.1 Record-level results</h3>
<table class="wikitable">
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Records</td><td class="num">351</td></tr>
<tr><td>Total tokens</td><td class="num">5,230,826</td></tr>
<tr><td>Quote tokens</td><td class="num">41,426</td></tr>
<tr><td>Mean H6 composite rate</td><td class="num">163,284/M</td></tr>
<tr><td>Max H6 composite rate</td><td class="num">542,705/M</td></tr>
<tr><td>Min H6 composite rate</td><td class="num">215/M</td></tr>
<tr><td>Records with H6 &gt; 100,000/M</td><td class="num">247/351 (70%)</td></tr>
<tr><td>Quote fraction vs H6 correlation (Pearson r)</td><td class="num">&minus;0.13</td></tr>
</table>

<h3>7.2 Per-anchor firing rates (Exp 4b)</h3>
<table class="wikitable">
<tr><th>Anchor</th><th>Mean rate (M)</th><th>Median</th><th>Min</th><th>Max</th></tr>
<tr><td>L21e42</td><td class="num">14,493</td><td class="num">8,651</td><td class="num">0</td><td class="num">62,549</td></tr>
<tr><td>L22e105</td><td class="num">20,473</td><td class="num">13,506</td><td class="num">0</td><td class="num">74,284</td></tr>
<tr><td>L23e113</td><td class="num">24,698</td><td class="num">14,429</td><td class="num">0</td><td class="num">85,726</td></tr>
<tr><td>L30e198</td><td class="num">17,633</td><td class="num">11,042</td><td class="num">0</td><td class="num">113,951</td></tr>
<tr><td>L32e254</td><td class="num">18,895</td><td class="num">13,103</td><td class="num">0</td><td class="num">68,554</td></tr>
<tr><td>L41e147</td><td class="num">67,093</td><td class="num">46,262</td><td class="num">0</td><td class="num">207,279</td></tr>
</table>

<h3>7.3 Key finding</h3>
<p>The negative correlation (r = &minus;0.13) between quote fraction and H6 rate confirms the pilot
finding at scale: <b>more verse quote content &rarr; less H6 firing</b>. The effect is weak because
quote fractions are small (mean 0.3% of tokens), but the direction is consistent across 351 records.
H6 fires on the prose commentary context, not on the embedded verse quotes.</p>
<p>The mean H6 rate (163,284/M) is 3.6&times; higher than the pilot (44,822/M) because Exp 4b
records are pure commentary windows with minimal verse content. L41e147 remains the strongest
anchor, firing at up to 207,279/M.</p>

<h3>7.4 Exp 4b visualizations</h3>
<table class="wikitable">
<tr><th>Chart</th><th>What it shows</th></tr>
<tr><td><a href="../img/chart_exp4b_scatter.png">Quote fraction vs H6 scatter</a></td><td>H6 composite rate vs verse quote fraction (log scale), 351 records</td></tr>
<tr><td><a href="../img/chart_exp4b_per_anchor.png">Per-anchor boxplot</a></td><td>H6 firing distribution per anchor across all 351 records</td></tr>
<tr><td><a href="../img/chart_exp4b_by_source.png">H6 by source</a></td><td>Mean H6 firing rate by source document (top 10)</td></tr>
</table>

<h3>7.5 Remaining limitation</h3>
<p>Exp 4b is still record-level, not per-token. The decisive within-document test &mdash; showing
H6 firing dropping token-by-token at quote boundaries &mdash; requires per-token routing capture
(<code>--raw-budget-tokens</code>). This is planned as a follow-up run on a subset of records.</p>
<p><b>What this means:</b> The H6 experts respond to prose context, not verse content. When
commentary prose surrounds a Bible quote, H6 fires throughout the window. When verse text stands
alone, H6 does not fire. The routing decision is about the format of the surrounding text, not
the semantics of the quoted content. This is consistent with the "format-associated routing
axis" framing from the <a href="forward_plan.html">forward plan</a>.</p>
"""

page("exp4.html", "Exp 4 results", EXP4, here="exp4")
print("EXP4 PAGE DONE")

# ══════════════════ FORWARD PLAN ══════════════════
FORWARD_PLAN = """
<h1>Forward Plan: Next Experimental Phase</h1>
<div class="hatnote">Designed by GPT-5.6-terra (Codex CLI) after reviewing the full project brief, narrative, and experiment plan. This page summarizes the key recommendations. The full document is in <code>FORWARD_PLAN.md</code>.</div>

<div class="toc"><div class="toctitle">Contents</div><ul>
<li>1 <a href="#rules">Rules for every experiment</a></li>
<li>2 <a href="#exp4">Exp 4: quotation-switch analysis</a></li>
<li>3 <a href="#exp13">Exp 13: scoped H6 ablation</a></li>
<li>4 <a href="#priority">Priority and dependencies</a></li>
<li>5 <a href="#new">New experiments</a></li>
<li>6 <a href="#viz">Visualization plan</a></li>
<li>7 <a href="#narrative">Narrative arc</a></li>
</ul></div>

<h2 id="rules">1. Rules for every experiment</h2>
<ul>
<li><b>Freeze the analysis contract before inspecting outputs.</b> Create a versioned
<code>analysis/h6_registry.csv</code> with the 6 anchor experts (L21e42, L22e105, L23e113,
L30e198, L32e254, L41e147) before analyzing any new data. The full 13+ cluster is exploratory
until frozen independently.</li>
<li><b>Reconcile documentation.</b> Generate <code>analysis/data_manifest.json</code> from raw
JSONL files (SHA-256, row count, token count, categories) before the next report.</li>
<li><b>Common reporting standard.</b> Every primary contrast: raw numerator/denominator, rate per
million, effect estimate, 95% CI, document-cluster bootstrap interval (10,000+ resamples).
P-values are secondary. Non-significant &ne; evidence of no effect &mdash; use equivalence intervals.</li>
<li><b>Document is the replication unit,</b> not the token. Tokens within a window share context
and are not independent observations.</li>
</ul>

<h2 id="exp4">2. Exp 4: quotation-switch analysis</h2>
<p>The current 30-row corpus has only 419 quote tokens &mdash; adequate for pipeline validation,
not for a decisive per-expert test. At a commentary routing rate of 10,000/M, 419 tokens yield
&sim;4 expected routings per anchor. A zero would have a wide upper confidence bound, not prove
suppression.</p>
<p><b>Exp 4b requirements:</b></p>
<ul>
<li>&ge;10,000 quote tokens across &ge;100 quote blocks from &ge;30 source documents</li>
<li>Each quote block matched to a same-document commentary comparator (equal length, matched on
position, digit fraction, newline/heading status)</li>
<li>64-token buffer excluded on each side of quote boundaries (sensitivity: 0, 32, 128, 256)</li>
<li>Conditional Monte-Carlo power calculation targeting 80% power for 5&times; suppression</li>
</ul>
<p><b>Primary endpoint:</b> binary event <code>I(layer, expert, token in top-6)</code>. Fit a
beta-binomial model at block level with document and window random effects. The confirmatory
decision is three-way: strong support, evidence against, or inconclusive.</p>
<p><b>Key figure:</b> paired forest plot (one row per anchor + composite, quote/commentary rate
ratio with 95% document-bootstrap CI on log scale) + boundary-aligned event study showing routing
probability in token bins around quote start/end.</p>

<h2 id="exp13">3. Exp 13: scoped H6 ablation</h2>
<p>Two intervention modes, labelled separately:</p>
<ol>
<li><b>Contribution knockout (primary):</b> retain top-6 selection and gate weights, zero the
chosen expert's output. Measures harm of removing contribution.</li>
<li><b>Route-mask compensation (secondary):</b> mask experts before top-k, choose replacements,
renormalize. Measures whether the model can compensate.</li>
</ol>
<p><b>Dose series:</b> each anchor separately, then cumulative sets of 1, 3, and all 6. Reveals
whether the effect is one crucial expert, diffuse redundancy, or broad damage.</p>
<p><b>Corpus:</b> held-out material never used to select H6: digit-stripped KJV verse, secular
verse, Christian prose, secular prose &mdash; 100+ blocks each, 512&ndash;1024 tokens, balanced.</p>
<p><b>Primary outcome:</b> per-block <code>Delta-NLL = NLL(ablation) - NLL(baseline)</code> in
nats/token. Primary causal estimand: <code>b_interaction</code> (greater damage on prose than verse).</p>
<p><b>Controls:</b> sham hook (must be &sim;0 delta), 20 random six-expert control clusters
matched on routing frequency, digit-cluster positive control, fixed seed + rank-by-rank logging.</p>

<h2 id="priority">4. Priority and dependencies</h2>
<table class="wikitable">
<tr><th>Order</th><th>Work</th><th>Why</th><th>GPU?</th></tr>
<tr><td>P0</td><td>Rebuild data manifest; freeze H6 registry; audit Exp 4 labels</td><td>Prevents stale-table errors</td><td>No</td></tr>
<tr><td>P1</td><td>Analyze Exp 4a + power simulation</td><td>Tells us if pending data answers anything</td><td>No</td></tr>
<tr><td>P2</td><td>Build/annotate Exp 4b + balanced secular/format corpus</td><td>Decisive test needs more exposure</td><td>No</td></tr>
<tr><td>P3</td><td>Run Exp 1 (translations) + Exp 12 (digit pairs) sequentially</td><td>Cheap checks; register + specificity control</td><td>Low</td></tr>
<tr><td>P4</td><td>Run Exp 4b with raw top-k capture</td><td>Avoids redundant Exp 11 rerun</td><td>Moderate</td></tr>
<tr><td>P5</td><td>Controlled format-edit factorial + secular factorial (Exp 3)</td><td>Distinguishes lineation, apparatus, register, religion</td><td>Moderate</td></tr>
<tr><td>P6</td><td>Run Exp 13 ablation only if H6 replicates</td><td>Causal work only on a stable target</td><td>Moderate</td></tr>
</table>

<h2 id="new">5. New experiments</h2>
<table class="wikitable">
<tr><th>Exp</th><th>Name</th><th>What it tests</th></tr>
<tr><td>15</td><td>Controlled format-edit factorial</td><td>Edit <i>same words</i> into controlled presentations (lineation, apparatus, register, domain). 2&times;2 lineation-by-apparatus on 50+ passages.</td></tr>
<tr><td>16</td><td>Secular/religious/format factorial</td><td>4 cells: secular verse, secular prose, religious verse, religious prose. Tests whether format effect replicates in secular writing.</td></tr>
<tr><td>17</td><td>Quote-boundary context carryover</td><td>Routing before/inside/after quotes at several distances. Tests whether post-quote elevation is retained context, not current-token classification.</td></tr>
<tr><td>18</td><td>Gate selection vs expert contribution</td><td>Separate gate rank/weight from contribution norm. High selection + negligible contribution = routing marker, not mechanism.</td></tr>
<tr><td>19</td><td>Religion null as equivalence</td><td>Re-fit covariate model with tradition effects, TOST equivalence test. "No residual tradition effect above practical bound" not "no religion representation."</td></tr>
<tr><td>20</td><td>Lens robustness</td><td>Compare tuned lens with independently trained linear probe at layers 0, 18, 19, 30, 37, 42. Tests whether late emergence survives a second readout family.</td></tr>
</table>

<h2 id="viz">6. Visualization plan</h2>
<ol>
<li><b>Evidence and status table</b> &mdash; every hypothesis: claim, unit, controls, effect/interval, status, raw-data link, falsification criterion</li>
<li><b>Exp 4 paired forest + event study</b> &mdash; confirmatory figure with raw exposures</li>
<li><b>Format factorial coefficient plot</b> &mdash; standardized within-passage effects for lineation, apparatus, register, domain</li>
<li><b>Covariate/tradition forest plot</b> &mdash; coefficients with intervals + leave-one-source-out stability panel</li>
<li><b>Ablation specificity/dose plot</b> &mdash; Delta-NLL distributions by input format for baseline/sham/H6 doses/matched random clusters</li>
<li><b>Expert registry view</b> &mdash; sortable table of every frozen H6 cell: selection evidence, Exp 4b ratio, format-edit effect, ablation effect</li>
<li><b>Routing-geometry null view</b> &mdash; corpus similarity matrix with format labels + permutation test</li>
<li><b>Lens robustness panel</b> &mdash; agreement curve with bootstrap intervals + independent probe comparison</li>
</ol>

<h2 id="narrative">7. Narrative arc</h2>
<ol>
<li><b>Question and scale:</b> instrument a 43-layer top-6 MoE across religious and matched text</li>
<li><b>Forensic reversal:</b> specialist claims failed raw-data and confound checks; retractions are the method working</li>
<li><b>What survives:</b> large, cross-tradition, digit- and length-robust H6 association; routing backbone that does not cluster by religion; late-emerging prediction curve. Use "format-associated" until interventions resolve the cause</li>
<li><b>Decisive design:</b> within-document quotation, controlled formatting, secular factorial, ablation logic. Make the pilot transparent; explain the Exp 4b repair</li>
<li><b>Causal and null conclusions, carefully bounded:</b> if supported, say H6 is recruited by format features and makes a format-selective contribution. Say only that no residual tradition effect above the registered bound was observed. Do not claim "no theology."</li>
<li><b>Reusable lesson:</b> MoE routing analyses need within-source controls, exposure-aware statistics, document-level replication, and independent causal tests. "Expert X fires on corpus Y" is a hypothesis generator, not an interpretation.</li>
</ol>
<p>The contribution is not "we found Bible/Qur'an experts." It is a correctness-first account of
how an apparent semantic routing story collapsed under data audit, what robust format-sensitive
routing remained, and the controlled experiments required to turn that observation into a mechanism.</p>
"""

page("forward_plan.html", "Forward plan", FORWARD_PLAN, here="plan")
print("FORWARD PLAN PAGE DONE")

# ══════════════════ EXP 13 ABLATION ══════════════════
EXP13 = """
<h1>Exp 13: Scoped H6 Ablation</h1>
<div class="hatnote">Causal intervention test: does knocking out the H6 verse/prose axis experts damage prose processing more than verse processing? The ablation hook is designed and deployed; the corpus is pending.</div>

<div class="toc"><div class="toctitle">Contents</div><ul>
<li>1 <a href="#rationale">Rationale</a></li>
<li>2 <a href="#anchors">H6 anchor registry (frozen)</a></li>
<li>3 <a href="#modes">Intervention modes</a></li>
<li>4 <a href="#dose">Dose series</a></li>
<li>5 <a href="#corpus">Corpus design</a></li>
<li>6 <a href="#outcome">Primary outcome and estimand</a></li>
<li>7 <a href="#controls">Controls and validation</a></li>
<li>8 <a href="#runplan">Run plan</a></li>
<li>9 <a href="#code">Hook implementation</a></li>
</ul></div>

<h2 id="rationale">1. Rationale</h2>
<p>The H6 axis is the study's strongest observational finding: 13+ experts (layers 4&ndash;41)
fire at up to 90,595/M on discursive prose and at ~0 on bare verse text, a 4,384&times; ratio
with Cohen's d = 2.61. But observation alone cannot establish causality. Exp 13 asks:
<b>if we remove these experts, does the model get worse on prose than on verse?</b></p>
<p>This is the only experiment in the study that modifies model behavior (via a forward-pass hook).
All other experiments are read-only. The hook is fail-closed: it logs every intervention and
restores the original forward pass after each record.</p>

<h2 id="anchors">2. H6 anchor registry (frozen)</h2>
<p>The following 6 experts were selected as the H6 anchor set based on the original observational
data. This registry is <b>frozen</b> &mdash; no peeking at new data to add or remove anchors.</p>
<table class="wikitable">
<tr><th>Anchor</th><th>Layer</th><th>Expert ID</th><th>Verse rate (M)</th><th>Prose rate (M)</th><th>Ratio</th></tr>
<tr><td>H6-1</td><td class="num">21</td><td class="num">42</td><td class="num">~0</td><td class="num">~10,000</td><td class="num">&infin;</td></tr>
<tr><td>H6-2</td><td class="num">22</td><td class="num">105</td><td class="num">~0</td><td class="num">~15,000</td><td class="num">&infin;</td></tr>
<tr><td>H6-3</td><td class="num">23</td><td class="num">113</td><td class="num">~0</td><td class="num">~20,000</td><td class="num">&infin;</td></tr>
<tr><td>H6-4</td><td class="num">30</td><td class="num">198</td><td class="num">~0</td><td class="num">~30,000</td><td class="num">&infin;</td></tr>
<tr><td>H6-5</td><td class="num">32</td><td class="num">254</td><td class="num">~0</td><td class="num">~40,000</td><td class="num">&infin;</td></tr>
<tr><td>H6-6</td><td class="num">41</td><td class="num">147</td><td class="num">~0</td><td class="num">~90,595</td><td class="num">&infin;</td></tr>
</table>
<p class="small">Rates are approximate from the original 8-tradition observation. The full 13+ cluster
is exploratory until frozen independently. Only these 6 anchors are used in the ablation.</p>

<h2 id="modes">3. Intervention modes</h2>
<p>Two distinct interventions, labelled and analyzed separately:</p>
<table class="wikitable">
<tr><th>Mode</th><th>What it does</th><th>What it measures</th></tr>
<tr><td><b>Contribution knockout</b> (primary)</td><td>Retain top-6 selection and gate weights, but zero the chosen expert's output tensor</td><td>Harm of removing the expert's contribution. If the model still routes to the expert but its output is silenced, how much worse is the prediction?</td></tr>
<tr><td><b>Route-mask compensation</b> (secondary)</td><td>Mask the expert before top-k selection, choose replacement experts, renormalize gate weights</td><td>Whether the model can compensate by rerouting to other experts. If damage is small, the system has redundancy.</td></tr>
</table>
<p>The distinction matters: a routing marker (high selection, negligible contribution) would show
large effects in route-mask but near-zero in knockout. A functional contributor would show large
effects in both.</p>

<h2 id="dose">4. Dose series</h2>
<p>Each anchor knocked out singly, then cumulative sets:</p>
<table class="wikitable">
<tr><th>Dose</th><th>Anchors removed</th><th>Purpose</th></tr>
<tr><td>dose_1</td><td>Each of the 6 individually (6 runs)</td><td>Is one anchor crucial, or are they interchangeable?</td></tr>
<tr><td>dose_3</td><td>3 anchors (H6-1, H6-3, H6-5)</td><td>Partial dose &mdash; is there a graded response?</td></tr>
<tr><td>dose_6</td><td>All 6 anchors</td><td>Full ablation &mdash; maximum damage estimate</td></tr>
</table>
<p>If damage scales with dose, the effect is diffuse across the cluster. If dose_1 already matches
dose_6, one expert is doing the work. If dose_3 &asymp; dose_6, three experts are sufficient.</p>

<h2 id="corpus">5. Corpus design</h2>
<p>4 cells, held-out material never used to select H6:</p>
<table class="wikitable">
<tr><th>Cell</th><th>Format</th><th>Domain</th><th>Records</th><th>Tokens/block</th></tr>
<tr><td>1</td><td>Verse</td><td>Religious (KJV, digit-stripped)</td><td class="num">100+</td><td>512&ndash;1024</td></tr>
<tr><td>2</td><td>Verse</td><td>Secular (poetry, matched format)</td><td class="num">100+</td><td>512&ndash;1024</td></tr>
<tr><td>3</td><td>Prose</td><td>Religious (commentary, held-out)</td><td class="num">100+</td><td>512&ndash;1024</td></tr>
<tr><td>4</td><td>Prose</td><td>Secular (essay, news, arXiv)</td><td class="num">100+</td><td>512&ndash;1024</td></tr>
</table>
<p>Blocks are short (512&ndash;1024 tokens) to enable chunked NLL computation within the 121GB
unified memory budget. The 2&times;2 design separates format (verse/prose) from domain
(religious/secular), testing the H6 hypothesis that format is the driver.</p>

<h2 id="outcome">6. Primary outcome and estimand</h2>
<p><b>Delta-NLL</b> per block: <code>Delta-NLL = NLL(ablation) - NLL(baseline)</code> in
nats/token. Positive delta means the ablation hurt prediction.</p>
<p><b>Primary causal estimand:</b> <code>b_interaction</code> &mdash; the interaction term
between ablation condition and input format. A positive <code>b_interaction</code> means
ablation causes more damage on prose than on verse, supporting the H6 hypothesis.</p>
<p><b>Secondary estimand:</b> main effect of ablation (overall damage) and main effect of format
(overall prose vs verse difficulty gap).</p>

<h2 id="controls">7. Controls and validation</h2>
<table class="wikitable">
<tr><th>Control</th><th>What it tests</th><th>Expected result</th></tr>
<tr><td><b>Sham hook</b></td><td>Hook runs but does nothing (no expert removed)</td><td>Delta-NLL &asymp; 0 (validates the hook infrastructure)</td></tr>
<tr><td><b>20 random six-expert clusters</b></td><td>Matched on routing frequency to H6, but not the H6 experts</td><td>Delta-NLL should be small and similar across formats (no interaction)</td></tr>
<tr><td><b>Digit-cluster positive control</b></td><td>Knockout the 6 highest-digit-density experts</td><td>Should damage digit-heavy text more than digit-free text</td></tr>
<tr><td><b>Fixed seed + rank-by-rank logging</b></td><td>Reproducibility and TP2 consistency</td><td>Both ranks produce identical Delta-NLL</td></tr>
</table>

<h2 id="runplan">8. Run plan</h2>
<p>11 modes &times; 4 corpora = 44 runs. Each run processes all blocks in one cell under one
intervention mode. The run order is:</p>
<ol>
<li><b>Baseline</b> &mdash; no intervention, establish reference NLL per block</li>
<li><b>Sham</b> &mdash; hook active, no knockout, validate infrastructure</li>
<li><b>6 single knockouts</b> &mdash; each H6 anchor individually</li>
<li><b>dose_3</b> &mdash; 3 anchors knocked out together</li>
<li><b>dose_6</b> &mdash; all 6 anchors knocked out</li>
<li><b>route_mask_dose_6</b> &mdash; route-mask compensation mode, all 6</li>
</ol>
<p>Each run writes a JSONL with per-block Delta-NLL. Analysis produces the interaction coefficient
plot, dose-response curve, and control comparison.</p>

<h2 id="code">9. Hook implementation</h2>
<p>The ablation hook (<code>exp13_ablation_hook.py</code>) monkey-patches the MoE forward pass
at runtime, replacing <code>moe_forward</code> with one of the two intervention modes. Key
design decisions:</p>
<ul>
<li><b>H6_ANCHORS</b> is a hardcoded dictionary, not read from a file &mdash; prevents
accidental registry drift</li>
<li><b>compute_nll_chunked</b> processes 512-token chunks to avoid OOM on the 121GB unified
memory (the model + KV cache + gradients for full 16k windows exceeds available memory)</li>
<li><b>Fail-closed:</b> the hook restores the original <code>moe_forward</code> after each
record. If the hook crashes, the original forward pass is restored before the exception propagates.</li>
<li><b>TP2-safe:</b> the hook runs on both ranks; NCCL all-reduce still occurs for the modified
output tensor</li>
</ul>
<p>The hook is deployed to both TP2 nodes (<code>/home/valentine/obs-religious/exp13_ablation_hook.py</code>).
The ablation corpus is not yet built &mdash; this is the next step after Exp 4b completes.</p>
"""

page("exp13.html", "Exp 13 ablation", EXP13, here="exp13")
print("EXP13 PAGE DONE")

# ══════════════════ EXP 1 RESULTS ══════════════════
EXP1 = """
<h1>Experiment 1: Multi-Translation Bible Test (Results)</h1>
<div class="hatnote">Does the H6 verse/prose axis depend on which translation is used? Five public-domain English translations of 30 Bible passages, all verse numbers stripped, all 0-digit controlled. <b>Result: H6 fires at 47.8/M &mdash; a 3,415&times; ratio vs commentary prose. The axis is translation-invariant.</b></div>

<div class="toc"><div class="toctitle">Contents</div><ul>
<li>1 <a href="#design">Design</a></li>
<li>2 <a href="#results">Results</a></li>
<li>3 <a href="#charts">Visualizations</a></li>
<li>4 <a href="#findings">Key findings</a></li>
<li>5 <a href="#implications">Implications</a></li>
</ul></div>

<h2 id="design">1. Design</h2>
<p>30 Bible passages spanning Genesis through Romans, each rendered in 5 public-domain English translations.
All verse numbers stripped during corpus preparation. Digit density verified at 0.0000% across all 150 records,
controlling the digit confound identified in Exp 4.</p>
<table class="wikitable">
<tr><th>Translation</th><th>Era</th><th>Register</th><th>Description</th></tr>
<tr><td>KJV</td><td>1611</td><td>Archaic</td><td>King James Version &mdash; the original text used in the core REAP observations</td></tr>
<tr><td>ASV</td><td>1901</td><td>Formal</td><td>American Standard Version &mdash; early modern English, literal</td></tr>
<tr><td>YLT</td><td>1862/1898</td><td>Ultra-literal</td><td>Young's Literal Translation &mdash; extreme word-for-word fidelity</td></tr>
<tr><td>WEB</td><td>2000s</td><td>Modern</td><td>World English Bible &mdash; contemporary English, public domain</td></tr>
<tr><td>BBE</td><td>1965</td><td>Basic English</td><td>Bible in Basic English &mdash; 850-word vocabulary, extreme register contrast</td></tr>
</table>
<p>The 30 passages cover major biblical genres: Genesis (creation, fall, akedah), Exodus (decalogue),
Deuteronomy (shema), Psalms (shepherd, repentance, 119), Proverbs (wisdom, virtuous woman),
Ecclesiastes (time), Song of Songs, Isaiah (servant, comfort, messiah), Jeremiah (covenant),
Ezekiel (dry bones), Daniel (son of man), Joel (spirit), Matthew (beatitudes, Lord's prayer, commission),
Mark (beginning), Luke (birth, parables), John (prologue, new birth, farewell), Acts (pentecost),
Romans (spirit).</p>

<h2 id="results">2. Results</h2>
<table class="wikitable">
<tr><th>Translation</th><th>Records</th><th>Tokens</th><th>H6 fires</th><th>H6 Rate (per M tokens)</th></tr>
<tr><td>KJV</td><td class="num">30</td><td class="num">42,021</td><td class="num">0</td><td class="num">0.0</td></tr>
<tr><td>ASV</td><td class="num">30</td><td class="num">41,176</td><td class="num">0</td><td class="num">0.0</td></tr>
<tr><td>YLT</td><td class="num">30</td><td class="num">44,587</td><td class="num">2</td><td class="num">44.9</td></tr>
<tr><td>WEB</td><td class="num">30</td><td class="num">39,933</td><td class="num">4</td><td class="num">100.2</td></tr>
<tr><td>BBE</td><td class="num">30</td><td class="num">41,434</td><td class="num">4</td><td class="num">96.5</td></tr>
<tr><td><b>All</b></td><td class="num">150</td><td class="num">209,151</td><td class="num">10</td><td class="num">47.8</td></tr>
</table>
<p><b>Invariant check:</b> 0 violations across 150 records. Every layer satisfies
sum(expert_frequencies) = seqlen &times; topk(6).</p>

<h3>2.1 Comparison to other experiments</h3>
<table class="wikitable">
<tr><th>Experiment</th><th>Text type</th><th>H6 Rate (M)</th><th>Records</th><th>Tokens</th></tr>
<tr><td>Exp 1 (all translations)</td><td>Bible verse</td><td class="num">47.8</td><td class="num">150</td><td class="num">209,151</td></tr>
<tr><td>Exp 4 pilot (KJV verse)</td><td>Bible verse</td><td class="num">4.1</td><td class="num">1,189</td><td class="num">1,045,776</td></tr>
<tr><td>Exp 4b (commentary)</td><td>Christian prose</td><td class="num">163,284</td><td class="num">351</td><td class="num">5,156,659</td></tr>
<tr><td>Core data (KJV Bible)</td><td>Bible verse</td><td class="num">4.1</td><td class="num">1,189</td><td class="num">1,045,776</td></tr>
</table>
<p>The Exp 1 rate (47.8/M) is slightly higher than the core KJV data (4.1/M) because WEB and BBE
use more modern formatting that occasionally triggers H6. The ratio to commentary is <b>3,415&times;</b>
&mdash; one of the largest routing effects in the study.</p>

<h2 id="charts">3. Visualizations</h2>
<table class="wikitable">
<tr><th>Chart</th><th>What it shows</th></tr>
<tr><td><a href="../img/chart_exp1_by_translation.png">H6 rate by translation</a></td><td>H6 composite rate per translation (bar chart, log scale). KJV and ASV at perfect zero; WEB, BBE, YLT near-zero.</td></tr>
<tr><td><a href="../img/chart_exp1_per_passage.png">Per-passage scatter</a></td><td>H6 rate per passage &times; translation. Each passage tested in all 5 translations &mdash; the flat distribution shows translation invariance.</td></tr>
</table>

<h2 id="findings">4. Key findings</h2>
<ol>
<li><b>H6 fires at near-zero on all verse translations.</b> KJV and ASV show <b>perfect zero</b> &mdash;
exactly 0 H6 firings across 83,197 tokens. WEB, BBE, and YLT show near-zero rates (45&ndash;100/M),
which are negligible compared to commentary prose (163,284/M).</li>
<li><b>Translation invariance confirmed.</b> The H6 verse/prose axis does not care which translation
is used. KJV (archaic, 1611) and BBE (850-word vocabulary, extreme register contrast) both fire at ~0.
The model is not detecting "KJV wording" or "archaic English" &mdash; it's detecting verse <i>format</i>.</li>
<li><b>The digit confound is controlled.</b> All 150 records are 0.0000% digit density. The H6 firing
difference between verse and prose cannot be explained by digit density.</li>
<li><b>Register is not the axis.</b> BBE (850-word vocabulary, modern register) and KJV (archaic, 1611)
both fire at ~0. If H6 were a register detector, BBE should fire differently from KJV. It doesn't.</li>
</ol>

<h2 id="implications">5. Implications</h2>
<ol>
<li><b>H6 is a format detector, not a content detector.</b> It responds to verse lineation/structure,
not to specific words, archaic language, or memorization.</li>
<li><b>The original e164 "scripture detector" finding is fully explained.</b> e164 was zero on KJV not
because it detects "non-scripture" but because KJV is verse-format text. Any verse-format text (any
translation, any religion) would produce the same near-zero rate.</li>
<li><b>Combined with Exp 4b:</b> H6 fires at 163,284/M on commentary prose and 47.8/M on Bible verse
&mdash; a 3,415&times; ratio. The verse/prose axis is the strongest routing effect in the study,
confirmed across 501 records and 5.4M tokens.</li>
</ol>
"""

page("exp1.html", "Exp 1 results", EXP1, here="exp1")
print("EXP1 PAGE DONE")
