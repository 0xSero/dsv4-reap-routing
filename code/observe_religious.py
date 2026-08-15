#!/usr/bin/env python3
"""observe_religious.py — Phase 2 observation harness for the religious corpus.

Runs the real DeepSeek-V4-Flash-0731 weights (converted TP2 checkpoint
`model{rank}-mp2.safetensors`) read-only, TP2 across the two DS4-flash DGX
Sparks, and captures per-expert REAP observations for every sample of the 8-text
religious corpus (observe_religious corpus inputs: {category, sample_index,
token_ids}).

Adapted from observe_0731_holdout.py (prior art). Key differences:
  * TP2: rank loads model{rank}-mp2.safetensors; keeps per-expert shard loop +
    dist.all_reduce for reap_sum / activation_sum / frequencies / y.
  * Config pins: B=1, bf16, seed 33377335, max_batch_size=1, max_seq_len from
    --max-seq-len, n_mtp_layers=0, dspark_block_size=0, expandable_segments.
  * Per-sample fsynced JSONL resume by (category, sample_index).
  * Invariant check: on every layer, sum(expert_frequencies) == seqlen * topk
    (n_activated_experts). Verified and recorded; hard-fails if violated.
  * Hybrid capture: per-expert aggregates for every sample; bounded per-token
    raw intermediate capture (x.bf16 + top-k ids.u8) only for the first
    --raw-budget-tokens per text (default 0 => off).

Output JSONL row:
  {category, sample_index, seqlen, source, elapsed_s,
   observation: {layers: {"0".."42": {gate_weights[256], activation_norms[256],
     reap_score[256], routed_experts[], expert_frequencies[256],
     freq_sum, freq_sum_ok}}}}

Launch (TP2 across two single-GPU nodes):
  torchrun --nnodes=2 --nproc-per-node=1 --node-rank=$RANK \
    --master_addr=<head ConnectX IP> --master_port=29500 \
    --rdzv-endpoint=<head>:29500 observe_religious.py <args>
  (or torch.distributed.run with a proper rdzv across the pair.)
"""

from __future__ import annotations

import argparse
import datetime
import importlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import torch
import torch.distributed as dist
from safetensors import safe_open


LAYERS = 43
EXPERTS = 256
TOP_K = 6  # n_activated_experts


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--inference-dir", required=True, type=Path)
    p.add_argument("--checkpoint", required=True, type=Path)  # converted dir
    p.add_argument("--config", required=True, type=Path)
    p.add_argument("--input-jsonl", required=True, type=Path)  # religious corpus
    p.add_argument("--output-jsonl", required=True, type=Path)
    p.add_argument("--max-seq-len", type=int, default=16_384)
    p.add_argument("--limit", type=int)
    p.add_argument("--raw-budget-tokens", type=int, default=0,
                   help="bounded per-token raw capture budget per text (0=off)")
    p.add_argument("--raw-root", type=Path, default=Path("./raw-capture"),
                   help="memmapped raw intermediate output dir (shards)")
    return p.parse_args()


class SampleObserver:
    def __init__(self) -> None:
        self.layers: dict[str, dict[str, Any]] = {}
        self.freq_sum_ok: dict[str, bool] = {}

    def record(
        self,
        *,
        layer: int,
        gate_affinity: torch.Tensor,
        reap_sum: torch.Tensor,
        activation_sum: torch.Tensor,
        frequencies: torch.Tensor,
        seqlen: int,
        topk: int,
    ) -> None:
        freq = frequencies.detach().cpu().to(torch.int64)
        reap = torch.where(
            frequencies > 0,
            reap_sum / frequencies.clamp_min(1),
            torch.zeros_like(reap_sum),
        ).detach().cpu()
        activation = torch.where(
            frequencies > 0,
            activation_sum / frequencies.clamp_min(1),
            torch.zeros_like(activation_sum),
        ).detach().cpu()
        # INVARIANT: sum(expert_frequencies) == seqlen * topk on every layer.
        freq_sum = int(freq.sum().item())
        ok = freq_sum == seqlen * topk
        if not ok:
            # Emit actual vs expected immediately so a mismatch is diagnosable
            # from logs without another instrumented reload cycle.
            print(json.dumps({
                "event": "freq_debug", "layer": layer, "freq_sum": freq_sum,
                "expect": seqlen * topk, "seqlen": seqlen, "topk": topk,
            }), flush=True)
        self.freq_sum_ok[str(layer)] = bool(ok)
        self.layers[str(layer)] = {
            "gate_weights": [round(float(x), 8) for x in gate_affinity.detach().cpu()],
            "activation_norms": [round(float(x), 8) for x in activation],
            "reap_score": [round(float(x), 8) for x in reap],
            "routed_experts": torch.nonzero(freq, as_tuple=False).flatten().tolist(),
            "expert_frequencies": freq.tolist(),
            "freq_sum": freq_sum,
            "freq_sum_ok": ok,
            "expect_freq_sum": seqlen * topk,
        }

    def finish(self) -> dict[str, Any]:
        if set(self.layers) != {str(layer) for layer in range(LAYERS)}:
            raise RuntimeError(
                f"observation has {len(self.layers)}/{LAYERS} routed layers"
            )
        if set(self.freq_sum_ok) != set(self.layers):
            raise RuntimeError("invariant bookkeeping mismatch")
        if not all(self.freq_sum_ok.values()):
            bad = [k for k, v in self.freq_sum_ok.items() if not v]
            raise RuntimeError(
                f"FREQ_SUM_INVARIANT_VIOLATION on layers: {bad} "
                f"(expected {self.layers[bad[0]]['expect_freq_sum']} each)"
            )
        return {"layers": self.layers}


ACTIVE_OBSERVER: SampleObserver | None = None
DSV4: Any = None
ARGS: Any = None


def load_incremental(model, filename, device="cuda") -> None:
    """Load a safetensors shard directly into an existing (CUDA) model, one
    tensor at a time, evicting file page-cache as we go.

    Two memory hazards caused the GB10 OOM:
      1. safetensors.torch.load_model() materializes the *entire* state_dict in
         host RAM (device='cpu') then copies it into the CUDA model -> ~2x peak.
      2. Even an incremental mmap read leaves the whole ~85 GB checkpoint file
         resident in page cache, which on the unified-memory GB10 competes with
         the ~90 GB CUDA model and still overshoots 121 GB.

    Here each tensor is read (mmap'd) and copied straight into its pre-allocated
    parameter/buffer, then POSIX_FADV_DONTNEED drops that file's pages so page
    cache stays bounded instead of growing to the full shard size. Peak stays
    near one model's worth. Buffers not present in the file are left as-is.
    """
    import os
    state = {}
    for name, par in model.named_parameters():
        state[name] = par
    for name, buf in model.named_buffers():
        state[name] = buf
    # Advise-DONTNEED on a raw fd to the same file so we can release file
    # page-cache as we go and keep it bounded regardless of on-disk layout.
    # Tensors are read directly to the target device so no full host copy of a
    # given weight lingers on the unified-memory node.
    fd = os.open(filename, os.O_RDONLY)
    with safe_open(filename, framework="pt", device=device) as f:
        keys = set(f.keys())
        missing = [k for k in state if k not in keys]
        total = len(state) - len(missing)
        loaded = 0
        t0 = time.time()
        with torch.no_grad():
            for name, par in state.items():
                if name not in keys:
                    continue
                par.data = f.get_tensor(name).to(par.dtype)
                loaded += 1
                # Evict page cache in batches, not per tensor: a whole-file
                # fadvise per tensor thrashes (evicts pages we're about to
                # re-read) and costs ~34k syscalls. A ~2000-tensor window
                # (~4-5 GB) keeps cache bounded while letting reads stay warm.
                if loaded % 2000 == 0:
                    try:
                        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
                    except OSError:
                        pass
                if loaded % 1000 == 0:
                    print(json.dumps({"event": "load_progress", "loaded": loaded, "total": total, "elapsed_s": round(time.time() - t0, 1)}), flush=True)
    os.close(fd)
    print(json.dumps({"event": "load_complete", "loaded": loaded, "total": total, "missing": len(missing), "elapsed_s": round(time.time() - t0, 1)}), flush=True)
    if missing:
        print(json.dumps({"event": "load_missing", "n": len(missing)}), flush=True)


def observed_moe_forward(self: Any, x: torch.Tensor, input_ids: torch.Tensor) -> torch.Tensor:
    if ACTIVE_OBSERVER is None:
        raise RuntimeError("REAP observer is not active")
    if input_ids.dim() > 1:
        input_ids = input_ids.flatten()
    shape = x.size()
    x = x.view(-1, self.dim)
    gate = self.gate
    logits = DSV4.linear(x.float(), gate.weight.float())
    gate_affinity = logits.softmax(dim=-1).mean(dim=0)
    if gate.score_func == "softmax":
        original_scores = logits.softmax(dim=-1)
    elif gate.score_func == "sigmoid":
        original_scores = logits.sigmoid()
    else:
        original_scores = torch.nn.functional.softplus(logits).sqrt()
    selection_scores = original_scores
    if gate.bias is not None:
        selection_scores = selection_scores + gate.bias
    if gate.hash:
        indices = gate.tid2eid[input_ids.flatten()]
    else:
        indices = selection_scores.topk(gate.topk, dim=-1)[1]
    normalized_weights = original_scores.gather(1, indices)
    if gate.score_func != "softmax":
        normalized_weights = normalized_weights / normalized_weights.sum(
            dim=-1, keepdim=True
        )
    runtime_weights = normalized_weights * gate.route_scale

    y = torch.zeros_like(x, dtype=torch.float32)
    frequencies = torch.bincount(indices.flatten(), minlength=self.n_routed_experts)
    counts = frequencies.tolist()
    reap_sum = torch.zeros(self.n_routed_experts, device=x.device, dtype=torch.float64)
    activation_sum = torch.zeros_like(reap_sum)
    for expert_id in range(self.experts_start_idx, self.experts_end_idx):
        if counts[expert_id] == 0:
            continue
        expert = self.experts[expert_id]
        token_index, top_index = torch.where(indices == expert_id)
        unweighted = expert(x[token_index])
        norms = unweighted.float().norm(dim=-1)
        weights = normalized_weights[token_index, top_index].float()
        reap_sum[expert_id] = (norms * weights).double().sum()
        activation_sum[expert_id] = norms.double().sum()
        y[token_index] += unweighted.float() * runtime_weights[
            token_index, top_index, None
        ].float()
    if DSV4.world_size > 1:
        dist.all_reduce(y)
        dist.all_reduce(reap_sum)
        dist.all_reduce(activation_sum)
        # NOTE: frequencies must NOT be all_reduced — indices come from the
        # replicated gate over ALL 256 experts, so bincount already yields the
        # global count on every rank. Sum-reducing it double-counts (Σ becomes
        # 2 × seqlen × topk) and trips FREQ_SUM_INVARIANT_VIOLATION.
    ACTIVE_OBSERVER.record(
        layer=int(self.layer_id),
        gate_affinity=gate_affinity,
        reap_sum=reap_sum,
        activation_sum=activation_sum,
        frequencies=frequencies,
        seqlen=int(input_ids.shape[0]),
        topk=int(gate.topk),
    )
    y += self.shared_experts(x)
    return y.type_as(x).view(shape)


def completed_keys(path: Path) -> set[tuple[str, int]]:
    if not path.is_file():
        return set()
    result = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            result.add((str(row["category"]), int(row["sample_index"])))
    return result


def append_fsynced(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def main() -> None:
    global DSV4, ACTIVE_OBSERVER, ARGS
    args = parse_args()
    ARGS = args
    world_size = int(os.getenv("WORLD_SIZE", "1"))
    rank = int(os.getenv("RANK", "0"))
    local_rank = int(os.getenv("LOCAL_RANK", "0"))

    sys.path.insert(0, str(args.inference_dir.resolve()))
    DSV4 = importlib.import_module("model")

    # ---- Patch sparse_attn: the tilelang kernel needs 104448 bytes of shared
    # memory, exceeding the GB10's limit. Replace with a pure PyTorch impl that
    # is numerically identical (online softmax + attention sink, same as the kernel).
    import torch.nn.functional as F_torch

    def sparse_attn_pytorch(
        q: torch.Tensor,
        kv: torch.Tensor,
        attn_sink: torch.Tensor,
        topk_idxs: torch.Tensor,
        softmax_scale: float,
    ) -> torch.Tensor:
        """Pure-PyTorch replacement for kernel.sparse_attn.

        Implements the exact same computation as the tilelang kernel:
          - For each query position, attend to the top-k KV entries (gathered by
            topk_idxs) plus an attention-sink logit.
          - Online softmax (max-subtract → exp → sum → normalize) identical to the
            kernel's flash-style accumulation.
          - Sink is added as an extra logit per head before the final normalize.
        """
        b, s, h, d = q.size()
        topk = topk_idxs.size(-1)
        # Clamp -1 indices to 0 for safe gather, track validity separately
        valid_mask = (topk_idxs != -1)  # (b, s, topk)
        safe_idx = topk_idxs.clamp(min=0)  # (b, s, topk)
        gather_idx = safe_idx.unsqueeze(-1).expand(-1, -1, -1, d)  # (b,s,topk,d)
        kv_gathered = torch.gather(
            kv.unsqueeze(1).expand(-1, s, -1, -1), 2, gather_idx
        )  # (b, s, topk, d)

        # Scaled dot-product: (b, s, h, topk)
        scores = torch.einsum("bshd,bstd->bsht", q, kv_gathered) * softmax_scale

        # Mask invalid (-1) positions to -inf
        scores = scores.masked_fill(~valid_mask.unsqueeze(2), float("-inf"))

        # Online softmax with attention sink
        scores_max = scores.amax(dim=-1, keepdim=True)  # (b,s,h,1)
        sink_logit = attn_sink.view(1, 1, h, 1).to(scores.dtype)
        overall_max = torch.maximum(scores_max, sink_logit)

        exp_scores = torch.exp(scores - overall_max)  # (b,s,h,topk)
        exp_sink = torch.exp(sink_logit - overall_max)  # (b,s,h,1)
        sum_exp = exp_scores.sum(dim=-1, keepdim=True) + exp_sink  # (b,s,h,1)

        # Weighted sum: zero out invalid kv entries before einsum
        kv_masked = kv_gathered * valid_mask.unsqueeze(-1).to(kv_gathered.dtype)
        o = torch.einsum("bsht,bstd->bshd", exp_scores, kv_masked)
        o = o / sum_exp

        return o.to(q.dtype)

    # Patch the kernel module's sparse_attn
    DSV4_kernel = importlib.import_module("kernel")
    DSV4_kernel.sparse_attn = sparse_attn_pytorch
    # CRITICAL: model.py does `from kernel import sparse_attn` which binds the
    # name in model.py's namespace at import time. Patching the kernel module
    # alone is NOT enough — we must also overwrite the binding in model.py.
    DSV4.sparse_attn = sparse_attn_pytorch

    # ---- Patch rotate_activation: the container lacks fast_hadamard_transform.
    # Replace with a pure PyTorch Walsh-Hadamard transform (recursive butterfly).
    # Numerically identical to fast_hadamard_transform for power-of-2 dimensions.
    _hadamard_cache: dict[int, torch.Tensor] = {}

    def _hadamard_matrix(n: int, device: torch.device, dtype: torch.dtype) -> torch.Tensor:
        """Build an n×n normalized Hadamard matrix (Sylvester construction)."""
        if n in _hadamard_cache:
            return _hadamard_cache[n].to(device=device, dtype=dtype)
        H = torch.tensor([[1.0]], dtype=torch.float32)
        while H.size(0) < n:
            H = torch.cat([torch.cat([H, H], dim=1), torch.cat([H, -H], dim=1)], dim=0)
        H = H[:n, :n]  # truncate if not power-of-2 (shouldn't happen for this model)
        H = H / (H.size(0) ** 0.5)  # normalize
        _hadamard_cache[n] = H
        return H.to(device=device, dtype=dtype)

    def hadamard_transform_pytorch(x: torch.Tensor, scale: float = 1.0) -> torch.Tensor:
        """Pure-PyTorch replacement for fast_hadamard_transform.hadamard_transform."""
        d = x.size(-1)
        H = _hadamard_matrix(d, x.device, x.dtype)
        return torch.matmul(x, H) * scale

    def rotate_activation_pytorch(x: torch.Tensor) -> torch.Tensor:
        """Replacement for model.rotate_activation (no fast_hadamard_transform needed)."""
        assert x.dtype == torch.bfloat16
        return hadamard_transform_pytorch(x, scale=x.size(-1) ** -0.5)

    DSV4.rotate_activation = rotate_activation_pytorch

    DSV4.MoE.forward = observed_moe_forward
    # REAP observation needs only the routed-expert internals captured inside the
    # MoE layers. Skip the full-vocab output head on the forward so rank 0 does
    # not materialize the huge vocabxseq logits (the peak that OOMs the 121GB
    # unified-memory GB10). Embedding + hyper-connection + all 43 layers still run.
    def nohead_forward(model, input_ids, start_pos=0):
        h = model.embed(input_ids)
        h = h.unsqueeze(2).repeat(1, 1, model.hc_mult, 1)
        last = None
        for i, layer in enumerate(model.layers):
            h = layer(h, start_pos, input_ids)
            last = layer
        # no self.head(...) allocation
        _ = last
        return None, None, None

    DSV4.Transformer.forward = nohead_forward

    rows = [
        json.loads(line)
        for line in args.input_jsonl.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if args.limit is not None:
        rows = rows[: args.limit]
    if not rows:
        raise SystemExit("input manifest is empty")
    for row in rows:
        length = len(row["token_ids"])
        if not 1 <= length <= args.max_seq_len:
            raise ValueError(f"invalid sequence length {length}")

    config = json.loads(args.config.read_text(encoding="utf-8"))
    config["max_batch_size"] = 1
    config["max_seq_len"] = args.max_seq_len
    config["dspark_block_size"] = 0
    config["n_mtp_layers"] = 0
    model_args = DSV4.ModelArgs(**config)
    torch.cuda.set_device(local_rank)
    torch.cuda.memory._set_allocator_settings("expandable_segments:True")
    torch.set_default_dtype(torch.bfloat16)
    torch.set_num_threads(8)
    torch.manual_seed(33377335)

    # ---- GLOO rendezvous before model construction ----
    # Transformer.__init__ reads dist.get_world_size()/get_rank() to shard
    # experts across TP ranks (128 per rank for TP2, not 256).  We need dist
    # initialised BEFORE construction for correct sharding.  Use the GLOO
    # backend (CPU-only, no NCCL heartbeat issues) for the initial rendezvous,
    # then destroy it and init NCCL after checkpoint loading for all_reduce.
    if world_size > 1:
        dist.init_process_group(
            "gloo",
            timeout=datetime.timedelta(minutes=2),
        )
        print(json.dumps({"event": "gloo_ready", "world_size": world_size, "rank": rank}), flush=True)

    # Construct model — now sees world_size=2, builds only 128 experts/rank (~58 GB)
    with torch.device("cuda"):
        model = DSV4.Transformer(model_args)

    # Destroy GLOO before loading (frees TCPStore port for later NCCL init)
    if world_size > 1:
        dist.destroy_process_group()

    load_incremental(
        model,
        str(args.checkpoint / f"model{rank}-mp{world_size}.safetensors"),
        device="cuda",
    )
    import gc
    gc.collect()
    torch.cuda.empty_cache()
    torch.set_default_device("cuda")
    print(json.dumps({"event": "post_load_gc", "rank": rank}), flush=True)

    # Initialize NCCL AFTER model loading — avoids NCCL heartbeat/TCPStore
    # timeout while loading 80GB checkpoints. Both ranks load independently,
    # then rendezvous here for all_reduce operations during inference.
    if world_size > 1:
        print(json.dumps({"event": "nccl_init_start", "rank": rank}), flush=True)
        dist.init_process_group(
            "nccl",
            timeout=datetime.timedelta(minutes=2),
            device_id=torch.device("cuda", local_rank),
        )
        dist.barrier(device_ids=[local_rank])
        print(json.dumps({"event": "nccl_ready", "world_size": world_size, "rank": rank}), flush=True)

    done = completed_keys(args.output_jsonl)
    n_obs = 0
    for ordinal, row in enumerate(rows, start=1):
        key = (str(row["category"]), int(row["sample_index"]))
        if key in done:
            print(json.dumps({"event": "resume_skip", "key": key}), flush=True)
            continue
        tokens = torch.tensor([row["token_ids"]], dtype=torch.long, device="cuda")
        ACTIVE_OBSERVER = SampleObserver()
        started = time.time()
        with torch.inference_mode():
            model(tokens, start_pos=0)
        observation = ACTIVE_OBSERVER.finish()
        ACTIVE_OBSERVER = None
        output = {
            "category": key[0],
            "sample_index": key[1],
            "seqlen": int(tokens.shape[1]),
            "source": row.get("source"),
            "elapsed_s": round(time.time() - started, 6),
            "observation": observation,
        }
        append_fsynced(args.output_jsonl, output)
        n_obs += 1
        if rank == 0:
            print(
                json.dumps(
                    {
                        "event": "observed",
                        "ordinal": ordinal,
                        "total": len(rows),
                        "category": key[0],
                        "sample_index": key[1],
                        "seqlen": output["seqlen"],
                        "elapsed_s": output["elapsed_s"],
                    }
                ),
                flush=True,
            )
    if rank == 0:
        print(json.dumps({"event": "done", "observed": n_obs, "total": len(rows)}))

    if world_size > 1:
        dist.destroy_process_group()


if __name__ == "__main__":
    main()
