#!/usr/bin/env python3
"""stream_to_hf.py — Streaming sidecar that tails the observation JSONL and
uploads fixed-size parquet shards to a private HuggingFace dataset.

CPU/network only — zero GPU impact. Runs as a separate process alongside the
GPU observation harness. Watches the run PID for liveness; flushes a final
partial shard when the run exits.

Resume: reads a small state file ``{"uploaded": N, "shard": M}`` and resumes
by uploaded row count (NOT shard×size — early shards can be irregular).

Usage:
  python3 stream_to_hf.py \\
    --input /path/to/observations.jsonl \\
    --state /path/to/stream_state.json \\
    --repo 0xSero/deepseek-v4-flash-religious-reap-observations \\
    --run-pid $RUN_PID \\
    --shard-rows 200 [--token $HF_TOKEN] [--private]

The JSONL rows are the observe_religious.py output:
  {category, sample_index, seqlen, source, elapsed_s,
   observation: {layers: {"0".."42": {gate_weights[256], activation_norms[256],
     reap_score[256], routed_experts[], expert_frequencies[256],
     freq_sum, freq_sum_ok, expect_freq_sum}}}}
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


# ---------------------------------------------------------------------------
# Schema — flattened enough for parquet efficiency but preserving all per-layer
# arrays. Each row = one observation sample. The layers dict is stored as a
# JSON string column (or we could explode to one-row-per-layer; for analysis
# we keep one-row-per-sample with nested JSON for compactness).
# ---------------------------------------------------------------------------
SCHEMA = pa.schema([
    ("category", pa.string()),
    ("sample_index", pa.int32()),
    ("seqlen", pa.int32()),
    ("source", pa.string()),
    ("elapsed_s", pa.float32()),
    ("observation_json", pa.string()),   # full observation dict as JSON
])


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--state", required=True, type=Path)
    p.add_argument("--repo", required=True, help="HF dataset repo id")
    p.add_argument("--run-pid", type=int, default=0,
                   help="PID of the GPU harness; 0 = no liveness watch")
    p.add_argument("--shard-rows", type=int, default=200)
    p.add_argument("--token", default=os.getenv("HF_TOKEN", ""))
    p.add_argument("--private", action="store_true", default=True)
    p.add_argument("--poll-interval", type=float, default=5.0)
    return p.parse_args()


def load_state(path: Path) -> dict:
    if path.is_file():
        return json.loads(path.read_text())
    return {"uploaded": 0, "shard": 0}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state))
    os.replace(tmp, path)
    os.sync()


def upload_shard(local_path: Path, repo: str, shard_name: str,
                 token: str, private: bool) -> bool:
    """Upload a single parquet shard to HF dataset repo under data/."""
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=token or None)
        api.upload_file(
            path_or_fileobj=str(local_path),
            path_in_repo=f"data/{shard_name}",
            repo_id=repo,
            repo_type="dataset",
            token=token or None,
        )
        return True
    except Exception as exc:
        print(json.dumps({"event": "upload_error", "shard": shard_name,
                          "error": str(exc)}), flush=True)
        return False


def ensure_repo(repo: str, token: str, private: bool) -> None:
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=token or None)
        api.create_repo(repo_id=repo, repo_type="dataset", private=private,
                        exist_ok=True, token=token or None)
    except Exception as exc:
        print(json.dumps({"event": "repo_ensure_error", "error": str(exc)}),
              flush=True)


def read_jsonl_rows(path: Path, start_line: int) -> list[str]:
    """Read lines [start_line:] from the JSONL file."""
    rows: list[str] = []
    if not path.is_file():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i < start_line:
                continue
            if line.strip():
                rows.append(line)
    return rows


def shard_to_parquet(rows: list[str], out_path: Path) -> int:
    """Convert a list of JSONL row strings to a parquet file. Returns row count."""
    cats, sidxs, seqlens, srcs, elap, obs = [], [], [], [], [], []
    for line in rows:
        row = json.loads(line)
        cats.append(row.get("category", ""))
        sidxs.append(int(row.get("sample_index", 0)))
        seqlens.append(int(row.get("seqlen", 0)))
        srcs.append(row.get("source") or "")
        elap.append(float(row.get("elapsed_s", 0.0)))
        obs.append(json.dumps(row.get("observation", {}), separators=(",", ":")))
    table = pa.table({
        "category": cats,
        "sample_index": sidxs,
        "seqlen": seqlens,
        "source": srcs,
        "elapsed_s": elap,
        "observation_json": obs,
    }, schema=SCHEMA)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, out_path, compression="zstd")
    return len(rows)


def run_liveness(pid: int) -> bool:
    if pid <= 0:
        return True  # no liveness watch configured
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def main() -> None:
    args = parse_args()
    state = load_state(args.state)
    ensure_repo(args.repo, args.token, args.private)

    print(json.dumps({"event": "sidecar_start", "uploaded": state["uploaded"],
                       "shard": state["shard"], "pid": args.run_pid}),
          flush=True)

    # Track which line we've read up to. The JSONL is append-only, so line
    # number == number of rows in the file. We resume by uploaded count:
    # lines [0:uploaded] are already in shards.
    lines_consumed = state["uploaded"]
    buffer: list[str] = []

    while True:
        # Read new lines beyond what we've consumed
        new_rows = read_jsonl_rows(args.input, lines_consumed)
        if new_rows:
            buffer.extend(new_rows)
            lines_consumed += len(new_rows)
            print(json.dumps({"event": "tailed", "new": len(new_rows),
                              "buffered": len(buffer),
                              "consumed": lines_consumed}), flush=True)

        # Flush full shards
        while len(buffer) >= args.shard_rows:
            chunk = buffer[:args.shard_rows]
            buffer = buffer[args.shard_rows:]
            shard_name = f"shard-{state['shard']:05d}.parquet"
            local = args.state.parent / "shards" / shard_name
            n = shard_to_parquet(chunk, local)
            ok = upload_shard(local, args.repo, shard_name,
                              args.token, args.private)
            if ok:
                state["uploaded"] += n
                state["shard"] += 1
                save_state(args.state, state)
                print(json.dumps({"event": "shard_uploaded",
                                  "shard": shard_name, "rows": n,
                                  "total_uploaded": state["uploaded"]}),
                      flush=True)
            else:
                # Re-buffer the chunk for retry on next poll
                buffer = chunk + buffer
                break

        alive = run_liveness(args.run_pid)
        if not alive:
            # Flush remaining partial shard
            if buffer:
                shard_name = f"shard-{state['shard']:05d}.parquet"
                local = args.state.parent / "shards" / shard_name
                n = shard_to_parquet(buffer, local)
                ok = upload_shard(local, args.repo, shard_name,
                                  args.token, args.private)
                if ok:
                    state["uploaded"] += n
                    state["shard"] += 1
                    save_state(args.state, state)
                    print(json.dumps({"event": "final_shard",
                                      "shard": shard_name, "rows": n,
                                      "total_uploaded": state["uploaded"]}),
                          flush=True)
            print(json.dumps({"event": "sidecar_done",
                              "total_uploaded": state["uploaded"],
                              "total_shards": state["shard"]}), flush=True)
            return

        time.sleep(args.poll_interval)


if __name__ == "__main__":
    main()
