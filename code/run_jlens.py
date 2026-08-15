#!/usr/bin/env python3
"""run_jlens.py — Driver for J-lens (logit lens + bounded Jacobian) on the
religious corpus using DeepSeek-V4-Flash-0731.

Runs TP1 (single node, rank 0) — the logit lens does NOT require the full MoE
forward across TP2 because:
  - The residual stream is identical regardless of TP sharding (each rank
    computes its expert shard and all_reduces the result).
  - Running TP1 means only rank-0's checkpoint (model0-mp2) is loaded, which
    covers half the experts. The shared expert + attention + embeddings are
    fully present in the rank-0 shard.
  - For the logit lens (unembedding intermediate residuals), this is sufficient:
    the residual is the all-reduced sum, and we capture it post-layer.

However, for FAITHFUL residuals (matching the full model), we need TP2.
This driver supports both:
  - TP1 (faster, approximate): only loads model0-mp2, runs single-rank forward.
    Expert outputs from rank-1's experts are missing → residual is approximate.
  - TP2 (faithful): requires both ranks via torchrun.

**For this research, we use TP2** (the same pair as observation) to ensure
faithful residuals. The driver is launched via torchrun on the head node,
similar to launch_observe.sh but with this script.

Usage (TP2, launched on the pair):
  torchrun --nnodes=2 --nproc-per-node=1 ... run_jlens.py \\
    --inference-dir /models/.../inference \\
    --checkpoint /models-converted/dsv4-mp2 \\
    --config /models/.../inference/config.json \\
    --corpus /obs-religious/all_religious.jsonl \\
    --output /obs-religious/jlens_output/ \\
    --max-prompts-per-text 20 \\
    --max-seq-len 1024

The corpus is stratified: for each of the 8 texts, select up to --max-prompts-per-text
representative samples (evenly spaced). For each selected sample, run:
  1. Logit lens: per-layer top-k decoded tokens at sampled positions.
  2. Bounded Jacobian: finite-diff Jacobian norms for a subset of layers.

Output: one JSONL file per text under --output, plus a combined summary.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import torch


TEXTS = ["bible", "quran", "tao", "gita", "dhamma", "bofm", "analects", "upanishads"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--inference-dir", required=True, type=Path)
    p.add_argument("--checkpoint", required=True, type=Path)
    p.add_argument("--config", required=True, type=Path)
    p.add_argument("--corpus", required=True, type=Path,
                   help="Merged JSONL with all religious samples")
    p.add_argument("--output", required=True, type=Path,
                   help="Output directory for J-lens JSONL files")
    p.add_argument("--max-prompts-per-text", type=int, default=20)
    p.add_argument("--max-seq-len", type=int, default=1024,
                   help="Truncate samples to this length for lens (J-lens uses short prompts)")
    p.add_argument("--top-k", type=int, default=10)
    p.add_argument("--jacobian-source-layers", type=str, default=None,
                   help="Comma-separated layer indices for bounded Jacobian (default: every 5th)")
    p.add_argument("--jacobian-n-proj", type=int, default=64)
    p.add_argument("--no-jacobian", action="store_true",
                   help="Skip bounded Jacobian (logit lens only)")
    p.add_argument("--limit-positions", type=int, default=64,
                   help="Max positions to decode per sample (evenly sampled)")
    return p.parse_args()


def load_corpus_by_text(corpus_path: Path) -> dict[str, list[dict]]:
    """Load the merged corpus and group by text (first part of category before _)."""
    by_text: dict[str, list[dict]] = {t: [] for t in TEXTS}
    for line in corpus_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        cat = row["category"]
        # Determine which text this belongs to
        text = _classify_category(cat)
        if text:
            by_text[text].append(row)
    return by_text


def _classify_category(cat: str) -> str | None:
    """Map a category string to one of the 8 texts."""
    cat_lower = cat.lower()
    # Bible: book_chapter format (genesis_c001, psalms_c150, etc.)
    # Check for biblical book patterns
    bible_books = [
        "genesis", "exodus", "leviticus", "numbers", "deuteronomy",
        "joshua", "judges", "ruth", "samuel", "kings", "chronicles",
        "ezra", "nehemiah", "esther", "job", "psalms", "proverbs",
        "ecclesiastes", "song", "isaiah", "jeremiah", "lamentations",
        "ezekiel", "daniel", "hosea", "joel", "amos", "obadiah",
        "jonah", "micah", "nahum", "habakkuk", "zephaniah", "haggai",
        "zechariah", "malachi", "matthew", "mark", "luke", "john",
        "acts", "romans", "corinthians", "galatians", "ephesians",
        "philippians", "colossians", "thessalonians", "timothy", "titus",
        "philemon", "hebrews", "james", "peter", "jude", "revelation",
    ]
    for book in bible_books:
        if cat_lower.startswith(book):
            return "bible"
    if cat_lower.startswith("sura_"):
        return "quran"
    if cat_lower.startswith("tao_ch_"):
        return "tao"
    if cat_lower.startswith("gita_ch_"):
        return "gita"
    if cat_lower.startswith("ch_") and "the_" in cat_lower:
        return "dhamma"
    if cat_lower in ("1_nephi", "2_nephi", "3_nephi", "4_nephi", "alma",
                     "enos", "ether", "helaman", "jacob", "jarom",
                     "mormon", "moroni", "mosiah", "omni", "words_of_mormon"):
        return "bofm"
    if cat_lower.startswith("book_"):
        return "analects"
    if cat_lower in ("isa", "katha", "kena"):
        return "upanishads"
    # Fallback: gita/tao with bare ch_ prefix (pre-fixed in merged corpus)
    if cat_lower.startswith("gita_"):
        return "gita"
    if cat_lower.startswith("tao_"):
        return "tao"
    return None


def stratify_samples(samples: list[dict], max_n: int) -> list[dict]:
    """Select up to max_n samples evenly spaced across the list."""
    if len(samples) <= max_n:
        return samples
    step = len(samples) / max_n
    indices = [int(i * step) for i in range(max_n)]
    # Ensure last sample is included
    if (len(samples) - 1) not in indices:
        indices.append(len(samples) - 1)
    return [samples[i] for i in indices]


def select_positions(seqlen: int, max_positions: int) -> list[int]:
    """Select up to max_positions evenly-spaced positions, always including the last."""
    if seqlen <= max_positions:
        return list(range(seqlen))
    step = seqlen / max_positions
    positions = [int(i * step) for i in range(max_positions)]
    if (seqlen - 1) not in positions:
        positions.append(seqlen - 1)
    return positions


def main() -> None:
    args = parse_args()
    world_size = int(os.getenv("WORLD_SIZE", "1"))
    rank = int(os.getenv("RANK", "0"))

    if rank == 0:
        print(json.dumps({"event": "jlens_start", "world_size": world_size,
                          "max_prompts_per_text": args.max_prompts_per_text}),
              flush=True)

    if world_size > 1:
        import torch.distributed as dist
        dist.init_process_group("nccl")

    # Only rank 0 does the lens work (it has the full model after all_reduce)
    # Actually, for TP2, BOTH ranks must load their shard and run forward
    # together. The lens captures happen on rank 0 after all_reduce.
    # For simplicity and memory, we run the lens on rank 0 only after
    # the TP2 forward completes. Rank 1 just participates in the forward.

    # Load model
    from jlens_dsv4 import load_model, apply_lens
    model, tokenizer = load_model(
        args.inference_dir,
        args.checkpoint,
        args.config,
        rank=rank,
        world_size=world_size,
        max_seq_len=args.max_seq_len,
    )

    if rank == 0:
        args.output.mkdir(parents=True, exist_ok=True)
# Both ranks run the identical lens loop in lockstep (all expert forwards
# all_reduce across ranks). apply_lens is deterministic (fixed seed), so
# rank 1 reproduces rank 0's exact forward sequence. Only rank 0 writes.

    # Load and stratify corpus
    by_text = load_corpus_by_text(args.corpus)

    # Resume keys must be IDENTICAL on both ranks: rank 0 reads the output
    # files (they live on the head node's disk) and broadcasts the done set,
    # otherwise rank 0 skips done samples while rank 1 still runs their
    # forwards, desynchronizing the very first collective (NCCL timeout).
    done_by_text = {t: set() for t in TEXTS}
    if rank == 0:
        for t in TEXTS:
            p = args.output / f"{t}_jlens.jsonl"
            if p.is_file():
                for line in p.read_text().splitlines():
                    if line.strip():
                        r = json.loads(line)
                        done_by_text[t].add((r["category"], r["sample_index"]))
    if world_size > 1:
        import torch.distributed as dist
        payload = [{t: sorted(map(list, k)) for t, k in done_by_text.items()}]
        dist.broadcast_object_list(payload, src=0)
        if rank != 0:
            done_by_text = {t: {tuple(k) for k in v}
                            for t, v in payload[0].items()}
    jacobian_layers = None
    if args.jacobian_source_layers:
        jacobian_layers = [int(x) for x in args.jacobian_source_layers.split(",")]

    all_results = []
    for text in TEXTS:
        samples = by_text.get(text, [])
        if not samples:
            print(json.dumps({"event": "no_samples", "text": text}), flush=True)
            continue
        selected = stratify_samples(samples, args.max_prompts_per_text)
        print(json.dumps({"event": "text_start", "text": text,
                           "available": len(samples),
                           "selected": len(selected)}), flush=True)

        text_output = args.output / f"{text}_jlens.jsonl"
        done_keys = done_by_text.get(text, set())

        for idx, sample in enumerate(selected):
            key = (sample["category"], sample["sample_index"])
            if key in done_keys:
                continue

            # Truncate tokens to max_seq_len
            token_ids = sample["token_ids"][:args.max_seq_len]
            input_ids = torch.tensor([token_ids], dtype=torch.long, device="cuda")
            positions = select_positions(len(token_ids), args.limit_positions)

            started = time.time()
            try:
                result = apply_lens(
                    model, tokenizer, input_ids,
                    top_k=args.top_k,
                    positions=positions,
                    jacobian_source_layers=jacobian_layers,
                    jacobian_n_proj=args.jacobian_n_proj,
                    do_jacobian=not args.no_jacobian,
                )
            except torch.cuda.OutOfMemoryError:
                torch.cuda.empty_cache()
                print(json.dumps({"event": "oom_skip", "text": text,
                                   "key": key, "seqlen": len(token_ids)}),
                      flush=True)
                continue

            output = {
                "category": sample["category"],
                "sample_index": sample["sample_index"],
                "seqlen": len(token_ids),
                "text": text,
                "elapsed_s": round(time.time() - started, 3),
                "lens": result,
            }
            if rank == 0:
                with text_output.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(output, separators=(",", ":")) + "\n")
                    f.flush()
                    os.fsync(f.fileno())
                all_results.append(output)

            print(json.dumps({
                "event": "sample_done", "text": text,
                "idx": idx + 1, "total": len(selected),
                "category": sample["category"],
                "seqlen": len(token_ids),
                "elapsed_s": output["elapsed_s"],
            }), flush=True)

        print(json.dumps({"event": "text_done", "text": text,
                           "output": str(text_output)}), flush=True)

    # Write combined summary
    summary_path = args.output / "jlens_summary.json"
    if rank != 0:
        print(json.dumps({"event": "rank1_loop_done"}), flush=True)
    else:
        summary = {
            "n_samples": len(all_results),
            "texts": TEXTS,
            "max_prompts_per_text": args.max_prompts_per_text,
            "max_seq_len": args.max_seq_len,
            "top_k": args.top_k,
            "jacobian": not args.no_jacobian,
            "jacobian_n_proj": args.jacobian_n_proj if not args.no_jacobian else 0,
            "model": "deepseek-ai/DeepSeek-V4-Flash-0731",
            "revision": "9e165c30e2704aec5d9d593cce3eebd58bbef1cb",
            "method": {
                "logit_lens": "hc_head → RMSNorm → lm_head(full_logits=True) per layer",
                "bounded_jacobian": (
                    "finite-difference random projection; "
                    f"{args.jacobian_n_proj} directions per source layer; "
                    "autograd-based jlens.fit not applicable (custom fp4/fp8 kernels lack backward)"
                ) if not args.no_jacobian else "skipped",
            },
        }
        summary_path.write_text(json.dumps(summary, indent=2))
        print(json.dumps({"event": "all_done", "n_samples": len(all_results),
                          "summary": str(summary_path)}), flush=True)

    if world_size > 1:
        import torch.distributed as dist
        dist.destroy_process_group()


if __name__ == "__main__":
    main()
