#!/usr/bin/env python3
"""generate_report.py — Phase 5: Generate the wiki-style research report.

Reads the Phase 3 analysis outputs and Phase 4 J-lens outputs to produce
a single self-contained HTML report in dense documentation style (per
AGENTS.md: minimal color, minimal ornamentation, reference-page structure).

Usage:
  python3 generate_report.py \
    --analysis outputs/ \
    --jlens jlens_output/ \
    --html report.html \
    [--obs full_obs.jsonl]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

TEXT_LABELS = {
    "bible": "Bible (KJV)",
    "quran": "Quran (Rodwell)",
    "tao": "Tao Te Ching (Legge)",
    "gita": "Bhagavad Gita (Arnold)",
    "dhamma": "Dhammapada (Müller)",
    "bofm": "Book of Mormon",
    "analects": "Analects (Legge)",
    "upanishads": "Upanishads (Paramananda)",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--analysis", required=True, type=Path,
                   help="Directory with analyze_experts.py outputs")
    p.add_argument("--jlens", type=Path, default=None,
                   help="Directory with J-lens outputs")
    p.add_argument("--html", required=True, type=Path,
                   help="Output HTML report path")
    p.add_argument("--obs", type=Path, default=None,
                   help="Observation JSONL (for invariant verification)")
    return p.parse_args()


def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def df_to_html_table(df: pd.DataFrame, max_rows: int = 50) -> str:
    rows = []
    rows.append("<table class='dense'><thead><tr>")
    for col in df.columns:
        rows.append(f"<th>{esc(col)}</th>")
    rows.append("</tr></thead><tbody>")
    for _, row in df.head(max_rows).iterrows():
        rows.append("<tr>")
        for col in df.columns:
            val = row[col]
            if isinstance(val, float):
                rows.append(f"<td>{val:.6f}</td>")
            else:
                rows.append(f"<td>{esc(val)}</td>")
        rows.append("</tr>")
    if len(df) > max_rows:
        rows.append(f"<tr><td colspan='{len(df.columns)}'>... {len(df) - max_rows} more rows</td></tr>")
    rows.append("</tbody></table>")
    return "".join(rows)


def verify_invariants(obs_path: Path) -> dict:
    """Verify the Σ expert_frequencies == seqlen × top_k invariant and
    no duplicate (category, sample_index)."""
    results = {"total_samples": 0, "invariant_violations": 0, "duplicates": 0}
    seen = set()
    violations = []
    for line in obs_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = (row["category"], row["sample_index"])
        if key in seen:
            results["duplicates"] += 1
        seen.add(key)
        results["total_samples"] += 1
        seqlen = row["seqlen"]
        layers = row["observation"]["layers"]
        for lname, ldata in layers.items():
            freq_sum = ldata.get("freq_sum", sum(ldata["expert_frequencies"]))
            expected = seqlen * 6  # top_k = 6
            if freq_sum != expected:
                if len(violations) < 5:
                    violations.append(f"layer {lname}: sum={freq_sum} expected={expected}")
                results["invariant_violations"] += 1
    results["violation_details"] = violations[:5]
    return results


def main() -> None:
    args = parse_args()

    sections = []

    # --- Header ---
    sections.append(f"""<h1>Religious-Text REAP Observation + J-Space on DeepSeek-V4-Flash-0731</h1>
<div class='meta'>
  <p><strong>Model:</strong> <code>deepseek-ai/DeepSeek-V4-Flash-0731</code> (revision <code>9e165c30…bbef1cb</code>)</p>
  <p><strong>Architecture:</strong> 43 backbone layers, 256 routed experts, top-6 routing, sqrtsoftplus, route_scale 1.5, hidden 4096, hc_mult 4</p>
  <p><strong>Corpus:</strong> 8 English religious texts (Bible KJV, Quran Rodwell, Tao Te Ching, Bhagavad Gita, Dhammapada, Book of Mormon, Analects, Upanishads), per-book/chapter, 1482 samples</p>
  <p><strong>Compute:</strong> TP2 across two DS4-flash DGX Sparks (GB10, 128 GB unified memory each)</p>
  <p><strong>Date:</strong> 2026-08-13</p>
  <p><strong>Mission:</strong> Read-only research — observation only, no quantization or pruning.</p>
</div>""")

    # --- Invariant verification ---
    if args.obs and args.obs.is_file():
        inv = verify_invariants(args.obs)
        status = "✓ PASS" if inv["invariant_violations"] == 0 and inv["duplicates"] == 0 else "✗ FAIL"
        sections.append(f"""<h2>Integrity Verification</h2>
<table class='dense'>
<tr><th>Check</th><th>Result</th></tr>
<tr><td>Total samples</td><td>{inv['total_samples']}</td></tr>
<tr><td>Σ freq == seqlen×top_k invariant</td><td>{inv['invariant_violations']} violations {status if inv['invariant_violations'] == 0 else '✗'}</td></tr>
<tr><td>Duplicate (category, sample_index)</td><td>{inv['duplicates']} {status if inv['duplicates'] == 0 else '✗'}</td></tr>
</table>""")

    # --- Phase 3: Expert rankings ---
    rankings_path = args.analysis / "expert_rankings.csv"
    if rankings_path.is_file():
        df = pd.read_csv(rankings_path)
        sections.append("<h2>Expert Activation Rankings</h2>")
        sections.append("<p>Top experts per text by REAP saliency score, activation norm, and gate affinity.</p>")
        # Show top 10 per text per metric
        for text in df["text"].unique():
            label = TEXT_LABELS.get(text, text)
            sub = df[df["text"] == text].head(30)
            sections.append(f"<h3>{esc(label)}</h3>")
            sections.append(df_to_html_table(sub, max_rows=30))

    # --- Cross-text Jaccard ---
    jaccard_path = args.analysis / "cross_text_jaccard.csv"
    if jaccard_path.is_file():
        df = pd.read_csv(jaccard_path)
        sections.append("<h2>Cross-Religious Comparison (Jaccard Overlap)</h2>")
        sections.append("<p>Jaccard overlap of top-20 REAP experts between texts. Higher = more shared expert usage.</p>")
        # Pivot to matrix
        try:
            mat = df.pivot(index="text_a", columns="text_b", values="jaccard")
            sections.append(df_to_html_table(mat.reset_index(), max_rows=20))
        except Exception:
            sections.append(df_to_html_table(df, max_rows=100))

    # --- Per-layer top-k ---
    per_layer_path = args.analysis / "per_layer_topk.csv"
    if per_layer_path.is_file():
        df = pd.read_csv(per_layer_path)
        sections.append("<h2>Per-Layer Top Experts</h2>")
        sections.append("<p>Top-10 REAP experts per layer per text. Shows layerwise specialization.</p>")
        sections.append(df_to_html_table(df, max_rows=100))

    # --- Phase 4: J-lens ---
    if args.jlens and args.jlens.is_dir():
        jlens_summary = args.jlens / "jlens_summary.json"
        if jlens_summary.is_file():
            summary = json.loads(jlens_summary.read_text())
            sections.append(f"""<h2>J-Space / Jacobian Lens Findings</h2>
<div class='meta'>
  <p><strong>Method:</strong> {esc(summary.get('method', {}).get('logit_lens', 'N/A'))}</p>
  <p><strong>Jacobian:</strong> {esc(summary.get('method', {}).get('bounded_jacobian', 'N/A'))}</p>
  <p><strong>Samples analyzed:</strong> {summary.get('n_samples', '?')} across {len(summary.get('texts', []))} texts</p>
</div>""")
        # Link to the detailed viewer
        sections.append("<p>See the <a href='jlens_viewer.html'>interactive J-space viewer</a> for per-layer top-token evolution and Jacobian sensitivity.</p>")

    # --- Footer ---
    sections.append("""<hr>
<div class='meta'>
  <p>Generated by generate_report.py. All artifacts under <code>/Users/sero/research/deepseek-v4-flash-0731/</code>.</p>
  <p>Dataset: <code>0xSero/deepseek-v4-flash-religious-reap-observations</code> (private HuggingFace dataset).</p>
</div>""")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Religious-Text REAP + J-Space — DeepSeek-V4-Flash-0731</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
         max-width: 1100px; margin: 2rem auto; padding: 0 1rem;
         color: #1a1a1a; background: #fff; line-height: 1.5; }}
  h1 {{ font-size: 1.4rem; border-bottom: 2px solid #333; padding-bottom: .3rem; }}
  h2 {{ font-size: 1.2rem; margin-top: 2rem; border-bottom: 1px solid #ccc; }}
  h3 {{ font-size: 1rem; margin-top: 1.2rem; }}
  table.dense {{ border-collapse: collapse; width: 100%; font-size: 0.82rem; margin: 0.5rem 0; }}
  table.dense th, table.dense td {{ border: 1px solid #ddd; padding: 3px 6px; text-align: left; }}
  table.dense th {{ background: #f5f5f5; font-weight: 600; }}
  table.dense tr:nth-child(even) {{ background: #fafafa; }}
  code {{ font-family: "SF Mono", "Menlo", monospace; font-size: 0.85rem; }}
  .meta {{ font-size: 0.85rem; color: #555; margin-bottom: 1rem; }}
  .meta p {{ margin: 0.2rem 0; }}
  hr {{ border: none; border-top: 1px solid #ccc; margin-top: 2rem; }}
  a {{ color: #0066cc; }}
</style>
</head>
<body>
{''.join(sections)}
</body>
</html>"""

    args.html.parent.mkdir(parents=True, exist_ok=True)
    args.html.write_text(html, encoding="utf-8")
    print(f"Wrote {args.html}")


if __name__ == "__main__":
    main()
