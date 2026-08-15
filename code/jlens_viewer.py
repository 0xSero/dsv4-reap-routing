#!/usr/bin/env python3
"""jlens_viewer.py — Generate a plain wiki-style HTML viewer for J-lens readouts.

Reads the per-text J-lens JSONL files and produces a single self-contained
HTML page showing per-layer top-token evolution and bounded Jacobian norms.
Matches the user's AGENTS.md preference for dense, documentation-style
presentation: minimal color, minimal ornamentation, reference-page structure.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TEXTS = ["bible", "quran", "tao", "gita", "dhamma", "bofm", "analects", "upanishads"]
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
    p.add_argument("--input", required=True, type=Path,
                   help="Directory with *_jlens.jsonl files")
    p.add_argument("--output", required=True, type=Path,
                   help="Output HTML file path")
    return p.parse_args()


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_layer_table(lens_data: dict, n_show: int = 5) -> str:
    """Render a compact table of top tokens per layer for the first few positions."""
    layers = lens_data.get("layers", {})
    positions = lens_data.get("positions", [])
    if not positions:
        return "<p>No position data.</p>"

    # Show a few representative positions
    show_pos = positions[:n_show] if len(positions) > n_show else positions

    rows = []
    for layer_idx in sorted(layers.keys(), key=int):
        top_tokens = layers[layer_idx].get("top_tokens", [])
        cells = []
        for pos_idx, pos in enumerate(show_pos):
            if pos_idx >= len(top_tokens):
                continue
            tokens = top_tokens[pos_idx][:3]  # top 3
            token_str = " ".join(f"{esc(t)}({p:.3f})" for t, p in tokens)
            cells.append(f"<td>{token_str}</td>")
        rows.append(f"<tr><td>{layer_idx}</td>{''.join(cells)}</tr>")

    header = "<tr><th>Layer</th>" + "".join(
        f"<th>Pos {p}</th>" for p in show_pos
    ) + "</tr>"
    return f"<table class='dense'><thead>{header}</thead><tbody>{''.join(rows)}</tbody></table>"


def render_jacobian(jac_data: dict) -> str:
    """Render bounded Jacobian norms as a compact bar-like table."""
    norms = jac_data.get("jacobian_norms", {})
    if not norms:
        return "<p>No Jacobian data.</p>"

    rows = []
    for layer in sorted(norms.keys(), key=int):
        layer_norms = norms[layer]
        mean_norm = sum(layer_norms) / len(layer_norms) if layer_norms else 0
        max_norm = max(layer_norms) if layer_norms else 0
        # Simple text bar
        bar_len = int(mean_norm * 100) if mean_norm > 0 else 0
        bar = "█" * min(bar_len, 40)
        rows.append(
            f"<tr><td>{layer}</td><td>{mean_norm:.6f}</td>"
            f"<td>{max_norm:.6f}</td><td><code>{bar}</code></td></tr>"
        )
    return (
        f"<table class='dense'><thead><tr>"
        f"<th>Layer</th><th>Mean ‖J‖₂</th><th>Max ‖J‖₂</th><th>Bar</th>"
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table>"
        f"<p class='note'>{esc(jac_data.get('note', ''))}</p>"
    )


def main() -> None:
    args = parse_args()
    sections = []

    for text in TEXTS:
        jsonl_path = args.input / f"{text}_jlens.jsonl"
        if not jsonl_path.is_file():
            continue
        label = TEXT_LABELS.get(text, text)

        samples = []
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                samples.append(json.loads(line))

        if not samples:
            continue

        # Show first sample in detail
        first = samples[0]
        lens = first.get("lens", {})

        body = f"<h2>{esc(label)}</h2>"
        body += f"<p>Samples analyzed: {len(samples)}. "
        body += f"Showing first: <code>{first['category']}#{first['sample_index']}</code> "
        body += f"(seqlen={first['seqlen']}).</p>"

        body += "<h3>Logit Lens — Top Tokens per Layer</h3>"
        body += render_layer_table(lens)

        if "bounded_jacobian" in lens:
            body += "<h3>Bounded Jacobian — Perturbation Sensitivity per Layer</h3>"
            body += render_jacobian(lens["bounded_jacobian"])

        # Summary across all samples for this text
        body += "<h3>All Samples</h3><table class='dense'><thead><tr>"
        body += "<th>Category</th><th>Idx</th><th>Seqlen</th><th>Time(s)</th></tr></thead><tbody>"
        for s in samples[:50]:  # cap
            body += (
                f"<tr><td>{esc(s['category'])}</td>"
                f"<td>{s['sample_index']}</td>"
                f"<td>{s['seqlen']}</td>"
                f"<td>{s.get('elapsed_s', '?')}</td></tr>"
            )
        if len(samples) > 50:
            body += f"<tr><td colspan='4'>... {len(samples) - 50} more</td></tr>"
        body += "</tbody></table>"

        sections.append(body)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>J-Space Lens — DeepSeek-V4-Flash-0731 — Religious Texts</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
         max-width: 1100px; margin: 2rem auto; padding: 0 1rem;
         color: #1a1a1a; background: #fff; line-height: 1.5; }}
  h1 {{ font-size: 1.4rem; border-bottom: 2px solid #333; padding-bottom: .3rem; }}
  h2 {{ font-size: 1.2rem; margin-top: 2rem; border-bottom: 1px solid #ccc; }}
  h3 {{ font-size: 1rem; margin-top: 1.2rem; }}
  table.dense {{ border-collapse: collapse; width: 100%; font-size: 0.85rem; margin: 0.5rem 0; }}
  table.dense th, table.dense td {{ border: 1px solid #ddd; padding: 3px 6px; text-align: left; }}
  table.dense th {{ background: #f5f5f5; font-weight: 600; }}
  table.dense tr:nth-child(even) {{ background: #fafafa; }}
  code {{ font-family: "SF Mono", "Menlo", monospace; font-size: 0.85rem; }}
  .note {{ font-size: 0.8rem; color: #666; font-style: italic; }}
  .meta {{ font-size: 0.8rem; color: #555; margin-bottom: 1rem; }}
</style>
</head>
<body>
<h1>J-Space Lens — DeepSeek-V4-Flash-0731</h1>
<div class="meta">
  Model: <code>deepseek-ai/DeepSeek-V4-Flash-0731</code> rev
  <code>9e165c30…bbef1cb</code><br>
  Method: Logit lens (hc_head → RMSNorm → lm_head per layer) +
  bounded finite-difference Jacobian (custom fp4/fp8 kernels lack backward).<br>
  Corpus: 8 English religious texts, per-book/chapter. Generated 2026-08-13.
</div>
{''.join(sections)}
</body>
</html>"""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
