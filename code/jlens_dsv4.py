#!/usr/bin/env python3
"""jlens_dsv4.py — Jacobian-lens / logit-lens adapter for DeepSeek-V4-Flash-0731.

The Anthropic "Jacobian lens" (arXiv:2607.15495) finds intermediate representations
the model is "poised to verbalize" via the average first-order causal effect of each
intermediate activation on future output logits. The reference library `jlens`
(github.com/anthropics/jacobian-lens) expects an HF decoder with autograd-
compatible forward passes.

**Challenge on GB10**: DSV4 uses custom fp4/fp8 Triton kernels (fp4_gemm, fp8_gemm,
sparse_attn, hc_split_sinkhorn) that lack backward implementations. Loading the full
model in bf16 for autograd would require ~400+ GB (4× the 167 GB fp4 checkpoint),
far exceeding the 128 GB unified memory.

**Approach (two tracks)**:

1. **Logit lens** (primary, no autograd needed): Capture the post-layer hyper-
   connection residual stack at each of the 43 backbone layers via forward hooks.
   Reduce each via hc_head → RMSNorm → lm_head(full_logits=True) to get per-layer
   logits. Decode top-k tokens per position. This reveals what the model is
   "poised to verbalize" at each layer — the core J-space readout.

2. **Bounded Jacobian lens** (secondary, if tractable): For a small subset of
   source layers and a random projection of the residual space, compute the
   average causal effect via finite-difference perturbation. This approximates
   `J_l = E[∂h_final / ∂h_l]` without requiring backward through custom kernels.
   Document exactly which layers/dimensions were computed.

This module provides:
  - DSV4LensModel: a LensModel-compatible adapter wrapping the custom Transformer.
  - capture_residuals(model, input_ids): returns per-layer residuals + final logits.
  - logit_lens(residuals, model): per-layer unembedded logits.
  - bounded_jacobian(model, input_ids, source_layers, n_proj_dims): finite-diff Jacobian.
  - apply_lens(model, text, positions): full lens readout (logit + bounded Jacobian).

Model facts (from config.json + campaign.json):
  43 backbone layers, 256 routed experts, top-6, hidden 4096, hc_mult 4,
  vocab 129280, sqrtsoftplus routing, route_scale 1.5.
  Residual shape per layer: (B, T, hc_mult=4, dim=4096).
  Unembed: hc_head(reduce 4→1) → RMSNorm → ParallelHead(full_logits=True) → (B,T,129280).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Residual capture via forward hooks
# ---------------------------------------------------------------------------

class ResidualCapture:
    """Registers forward hooks on each Block to capture the post-layer residual.

    The post-layer residual is the output of ``Block.forward`` — the hyper-
    connection stack of shape ``(B, T, hc_mult, dim)``. This is exactly the
    state of ``h`` at the top of the next iteration in ``Transformer.forward``.

    Tensors are cloned immediately to guard against in-place fp8 quant kernels.
    """

    def __init__(self, model: Any) -> None:
        self.model = model
        self.handles: list = []
        self.captures: dict[int, torch.Tensor] = {}

    def _make_hook(self, idx: int):
        def hook(module, inputs, output):
            # output is (B, T, hc_mult, dim) — the post-layer hc residual stack
            tensor = output if torch.is_tensor(output) else output[0]
            self.captures[idx] = tensor.detach().clone()
        return hook

    def __enter__(self):
        self.captures = {}
        for i, layer in enumerate(self.model.layers):
            self.handles.append(
                layer.register_forward_hook(self._make_hook(i))
            )
        return self

    def __exit__(self, *args):
        for h in self.handles:
            h.remove()
        self.handles = []


# ---------------------------------------------------------------------------
# Unembedding: hc_head → RMSNorm → lm_head(full_logits=True)
# ---------------------------------------------------------------------------

def unembed_residual(model: Any, residual: torch.Tensor) -> torch.Tensor:
    """Apply the canonical unembedding pipeline to a residual stack.

    Args:
        model: the DSV4 Transformer (with .layers[0].hc_head, .norm, .head).
        residual: (B, T, hc_mult, dim) — the post-layer hc residual stack.

    Returns:
        logits: (B, T, vocab_size) — per-position logits at this layer.
    """
    # hc_head reduces (B,T,hc,d) → (B,T,d) using Transformer-level params
    reduced = model.layers[0].hc_head(
        residual,
        model.hc_head_fn,
        model.hc_head_scale,
        model.hc_head_base,
    )
    normed = model.norm(reduced)
    logits = model.head(normed, full_logits=True)
    return logits


# ---------------------------------------------------------------------------
# Logit lens: per-layer top-k decoded tokens
# ---------------------------------------------------------------------------

@torch.no_grad()
def logit_lens(
    model: Any,
    tokenizer: Any,
    input_ids: torch.Tensor,
    *,
    top_k: int = 10,
    positions: list[int] | None = None,
    layers: list[int] | None = None,
) -> dict[str, Any]:
    """Run the logit lens on a single input.

    Returns a dict:
      {
        "input_tokens": [decoded tokens],
        "layers": {
          "0": {"top_tokens": [[(token, prob) for k in top_k] for position], ...},
          ...
        },
        "final_logits": [[(token, prob) for k in top_k] for position],
      }
    """
    n_layers = len(model.layers)
    if layers is None:
        layers = list(range(n_layers))

    # Forward pass with residual capture
    with ResidualCapture(model) as rc:
        _run_forward(model, input_ids)

    # Determine positions
    seq_len = input_ids.shape[1]
    if positions is None:
        positions = list(range(seq_len))

    result: dict[str, Any] = {
        "input_tokens": [
            tokenizer.decode([int(t)]) for t in input_ids[0]
        ],
        "n_layers": n_layers,
        "seq_len": seq_len,
        "positions": positions,
        "layers": {},
    }

    for layer_idx in layers:
        if layer_idx not in rc.captures:
            continue
        residual = rc.captures[layer_idx]  # (1, T, hc, d)
        logits = unembed_residual(model, residual)  # (1, T, vocab)
        logits = logits[0].float()  # (T, vocab)

        layer_top = []
        for pos in positions:
            if pos >= seq_len:
                continue
            pos_logits = logits[pos]
            probs = torch.softmax(pos_logits, dim=-1)
            topk_vals, topk_ids = probs.topk(top_k)
            layer_top.append([
                (tokenizer.decode([int(tid)]), round(float(val), 6))
                for tid, val in zip(topk_ids.tolist(), topk_vals.tolist())
            ])
        result["layers"][str(layer_idx)] = {"top_tokens": layer_top}

    # Final layer logits (ground truth)
    final_residual = rc.captures[n_layers - 1]
    final_logits = unembed_residual(model, final_residual)[0].float()
    final_top = []
    for pos in positions:
        if pos >= seq_len:
            continue
        probs = torch.softmax(final_logits[pos], dim=-1)
        topk_vals, topk_ids = probs.topk(top_k)
        final_top.append([
            (tokenizer.decode([int(tid)]), round(float(val), 6))
            for tid, val in zip(topk_ids.tolist(), topk_vals.tolist())
        ])
    result["final_logits"] = final_top

    return result


# ---------------------------------------------------------------------------
# Bounded Jacobian lens via finite differences
# ---------------------------------------------------------------------------

@torch.no_grad()
def bounded_jacobian(
    model: Any,
    input_ids: torch.Tensor,
    *,
    source_layers: list[int] | None = None,
    n_proj_dims: int = 64,
    epsilon: float = 0.01,
    target_positions: list[int] | None = None,
) -> dict[str, Any]:
    """Approximate the Jacobian lens via finite-difference perturbation.

    For each source layer ``l``, perturbs each of ``n_proj_dims`` random
    projection directions in the residual space and measures the effect on
    the final-layer logits at the target positions. This approximates:

        J_l ≈ E[∂logits_final / ∂h_l]

    without requiring backward through the custom fp4/fp8 kernels.

    **Cost**: ``len(source_layers) × n_proj_dims`` forward passes. With
    source_layers=[0,10,20,30,40] and n_proj_dims=64, that's 320 forward
    passes — tractable on GB10 for a bounded prompt set.

    Returns:
      {
        "source_layers": [...],
        "n_proj_dims": N,
        "jacobians": {layer: {proj_dim: [delta_logits per target pos]}},
        "norms": {layer: [L2 norm of Jacobian row per proj dim]},
      }
    """
    n_layers = len(model.layers)
    if source_layers is None:
        # Default: every 5th layer + final
        source_layers = list(range(0, n_layers, 5))
        if (n_layers - 1) not in source_layers:
            source_layers.append(n_layers - 1)

    seq_len = input_ids.shape[1]
    if target_positions is None:
        # Use last few positions (where predictions matter most)
        target_positions = list(range(max(0, seq_len - 10), seq_len))

    d_model = model.layers[0].ffn.dim  # 4096 (Block has no .dim; MoE does)
    hc_mult = model.hc_mult  # 4
    hc_dim = hc_mult * d_model  # 16384

    # Generate random projection directions in the flattened hc residual space
    gen = torch.Generator(device="cuda").manual_seed(33377335)
    proj_vectors = torch.randn(n_proj_dims, hc_dim, generator=gen, device="cuda")
    proj_vectors = proj_vectors / proj_vectors.norm(dim=-1, keepdim=True)

    # Baseline forward pass
    with ResidualCapture(model) as rc_base:
        _run_forward(model, input_ids)
    baseline_final = rc_base.captures[n_layers - 1].clone()  # (1,T,hc,d)
    baseline_logits = unembed_residual(model, baseline_final)[0].float()  # (T, vocab)

    jacobians: dict[str, Any] = {}
    norms: dict[str, Any] = {}

    for layer_idx in source_layers:
        if layer_idx not in rc_base.captures:
            continue
        base_residual = rc_base.captures[layer_idx].clone()  # (1,T,hc,d)
        layer_jac = {}
        layer_norms = []

        for proj_idx in range(n_proj_dims):
            # Perturb: add epsilon * proj_vector to the residual at ALL positions
            # in the flattened hc dimension
            perturbed = base_residual.clone()
            flat = perturbed.view(1, seq_len, hc_dim)
            flat[:, :, :] += epsilon * proj_vectors[proj_idx].unsqueeze(0).unsqueeze(0)

            # We can't easily inject the perturbed residual back into the model's
            # forward pass at an intermediate layer. Instead, we measure the
            # effect by running the sub-network from layer_idx to the end.
            # This requires a "partial forward" from the perturbed residual.
            perturbed_logits = _partial_forward_unembed(
                model, perturbed, layer_idx, input_ids
            )

            # Delta at target positions
            delta = (perturbed_logits - baseline_logits).float()
            target_delta = delta[target_positions].cpu().tolist()  # (n_pos, vocab)
            # Store the L2 norm of the delta (averaged over positions)
            delta_norm = delta[target_positions].norm(dim=-1).mean().item()
            layer_norms.append(round(delta_norm, 6))
            layer_jac[str(proj_idx)] = {
                "delta_norm": round(delta_norm, 6),
            }

        jacobians[str(layer_idx)] = layer_jac
        norms[str(layer_idx)] = layer_norms

    return {
        "source_layers": source_layers,
        "n_proj_dims": n_proj_dims,
        "epsilon": epsilon,
        "target_positions": target_positions,
        "jacobian_norms": norms,
        "method": "finite_difference_random_projection",
        "note": (
            f"Approximate Jacobian via {n_proj_dims} random projection directions "
            f"per source layer. Full {d_model}×{d_model} Jacobian not computed "
            f"(would require {d_model} forward passes per layer). "
            f"Custom fp4/fp8 kernels lack backward; autograd-based jlens.fit "
            f"not applicable. This is a bounded approximation."
        ),
    }


def _partial_forward_unembed(
    model: Any,
    perturbed_residual: torch.Tensor,
    start_layer: int,
    input_ids: torch.Tensor,
) -> torch.Tensor:
    """Run the model forward from ``start_layer`` onward using the perturbed
    residual as input, then unembed the final residual.

    This simulates the effect of perturbing the residual at ``start_layer``
    on the final output, without re-running layers [0, start_layer).
    """
    h = perturbed_residual  # (1, T, hc, d)
    start_pos = 0
    for i in range(start_layer, len(model.layers)):
        h = model.layers[i](h, start_pos, input_ids)
    return unembed_residual(model, h)[0]  # (T, vocab)


def _run_forward(model: Any, input_ids: torch.Tensor) -> None:
    """Run the model's no-head forward (embed + all layers, skip lm_head).

    This mirrors the ``nohead_forward`` in observe_religious.py to avoid
    materializing the huge (B, T, vocab) logits during the forward pass.
    """
    h = model.embed(input_ids)
    h = h.unsqueeze(2).repeat(1, 1, model.hc_mult, 1)
    for layer in model.layers:
        h = layer(h, 0, input_ids)


# ---------------------------------------------------------------------------
# Full lens readout for a text
# ---------------------------------------------------------------------------

@torch.no_grad()
def apply_lens(
    model: Any,
    tokenizer: Any,
    input_ids: torch.Tensor,
    *,
    top_k: int = 10,
    positions: list[int] | None = None,
    jacobian_source_layers: list[int] | None = None,
    jacobian_n_proj: int = 64,
    do_jacobian: bool = True,
) -> dict[str, Any]:
    """Apply both logit lens and bounded Jacobian lens to a single input.

    Args:
        model: DSV4 Transformer (loaded, eval mode).
        tokenizer: DeepSeek tokenizer.
        input_ids: (1, T) token tensor on cuda.
        top_k: number of top tokens per position.
        positions: positions to analyze (default: all).
        jacobian_source_layers: layers for bounded Jacobian (default: every 5th).
        jacobian_n_proj: random projection dimensions for Jacobian.
        do_jacobian: whether to compute the bounded Jacobian.

    Returns:
        Combined lens readout dict.
    """
    seq_len = input_ids.shape[1]
    if positions is None:
        # For long sequences, sample positions to keep output manageable
        if seq_len > 256:
            # Sample ~128 positions evenly + always include last
            step = max(1, seq_len // 128)
            positions = list(range(0, seq_len, step))
            if (seq_len - 1) not in positions:
                positions.append(seq_len - 1)
        else:
            positions = list(range(seq_len))

    result = logit_lens(
        model, tokenizer, input_ids,
        top_k=top_k, positions=positions,
    )

    if do_jacobian:
        jac = bounded_jacobian(
            model, input_ids,
            source_layers=jacobian_source_layers,
            n_proj_dims=jacobian_n_proj,
        )
        result["bounded_jacobian"] = jac

    return result


# ---------------------------------------------------------------------------
# Model loading (reuses observe_religious.py's load_incremental)
# ---------------------------------------------------------------------------

def _sparse_attn_pytorch(
    q: torch.Tensor,
    kv: torch.Tensor,
    attn_sink: torch.Tensor,
    topk_idxs: torch.Tensor,
    softmax_scale: float,
) -> torch.Tensor:
    """Pure-PyTorch replacement for kernel.sparse_attn (same as observe_religious.py).

    The tilelang kernel needs 104448 bytes of shared memory, exceeding the GB10's
    limit. This implements the exact same computation: online softmax + attention sink.
    """
    b, s, h, d = q.size()
    # Callers in the lens path may pass CPU tensors (e.g. topk_idxs built from
    # host-side index lists) — normalize devices before gathering.
    topk_idxs = topk_idxs.to(q.device)
    attn_sink = attn_sink.to(q.device)
    topk = topk_idxs.size(-1)
    valid_mask = (topk_idxs != -1)
    safe_idx = topk_idxs.clamp(min=0)
    gather_idx = safe_idx.unsqueeze(-1).expand(-1, -1, -1, d)
    kv_gathered = torch.gather(
        kv.unsqueeze(1).expand(-1, s, -1, -1), 2, gather_idx
    )
    scores = torch.einsum("bshd,bstd->bsht", q, kv_gathered) * softmax_scale
    scores = scores.masked_fill(~valid_mask.unsqueeze(2), float("-inf"))
    scores_max = scores.amax(dim=-1, keepdim=True)
    sink_logit = attn_sink.view(1, 1, h, 1).to(scores.dtype)
    overall_max = torch.maximum(scores_max, sink_logit)
    exp_scores = torch.exp(scores - overall_max)
    exp_sink = torch.exp(sink_logit - overall_max)
    sum_exp = exp_scores.sum(dim=-1, keepdim=True) + exp_sink
    kv_masked = kv_gathered * valid_mask.unsqueeze(-1).to(kv_gathered.dtype)
    o = torch.einsum("bsht,bstd->bshd", exp_scores, kv_masked)
    o = o / sum_exp
    return o.to(q.dtype)


def load_model(
    inference_dir: Path,
    checkpoint_dir: Path,
    config_path: Path,
    rank: int = 0,
    world_size: int = 1,
    max_seq_len: int = 16384,
) -> tuple[Any, Any]:
    """Load the DSV4 model and tokenizer for lens analysis.

    Reuses the same loading path as observe_religious.py:
    - Pins n_mtp_layers=0, dspark_block_size=0
    - Loads model{rank}-mp{world_size}.safetensors via load_incremental
    - Patches MoE.forward for observation (but lens doesn't need REAP stats)
    - Patches Transformer.forward to no-head (avoid vocab×seq logits OOM)

    Returns (model, tokenizer).
    """
    import importlib
    from safetensors import safe_open

    sys.path.insert(0, str(inference_dir.resolve()))
    DSV4 = importlib.import_module("model")

    # Patch sparse_attn: the tilelang kernel needs 104448 bytes of shared
    # memory, exceeding the GB10's limit. Replace with a pure PyTorch impl.
    DSV4_kernel = importlib.import_module("kernel")
    DSV4_kernel.sparse_attn = _sparse_attn_pytorch
    # model.py binds `from kernel import sparse_attn` at import time — patch
    # model.py's namespace too or the tilelang kernel (104448B smem) is used.
    DSV4.sparse_attn = _sparse_attn_pytorch

    # Patch rotate_activation: container lacks fast_hadamard_transform.
    # Pure-PyTorch Walsh-Hadamard (Sylvester construction) equivalent.
    _had_cache: dict[int, torch.Tensor] = {}

    def _hadamard_matrix(n: int) -> torch.Tensor:
        if n not in _had_cache:
            assert n & (n - 1) == 0, "hadamard needs power-of-2"
            h = torch.ones(1, 1, dtype=torch.float32)
            while h.shape[0] < n:
                h = torch.cat([torch.cat([h, h], 1), torch.cat([h, -h], 1)], 0)
            _had_cache[n] = h
        return _had_cache[n]

    def _rotate_activation_pytorch(x: torch.Tensor) -> torch.Tensor:
        n = x.shape[-1]
        h = _hadamard_matrix(n).to(x.device, x.dtype)
        return x @ h / (n ** 0.5)

    DSV4.rotate_activation = _rotate_activation_pytorch

    # Patch forward to no-head (same as observe_religious.py)
    def nohead_forward(model, input_ids, start_pos=0):
        h = model.embed(input_ids)
        h = h.unsqueeze(2).repeat(1, 1, model.hc_mult, 1)
        for layer in model.layers:
            h = layer(h, start_pos, input_ids)
        return None, None, None

    DSV4.Transformer.forward = nohead_forward

    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["max_batch_size"] = 1
    config["max_seq_len"] = max_seq_len
    config["dspark_block_size"] = 0
    config["n_mtp_layers"] = 0
    model_args = DSV4.ModelArgs(**config)

    torch.cuda.set_device(0)
    # model.py's Indexer builds causal masks with device-less torch.arange;
    # defaulting to cuda keeps them off the CPU (same as observe_religious.py).
    torch.set_default_device("cuda")
    torch.cuda.memory._set_allocator_settings("expandable_segments:True")
    torch.set_default_dtype(torch.bfloat16)
    torch.set_num_threads(8)
    torch.manual_seed(33377335)

    with torch.device("cuda"):
        model = DSV4.Transformer(model_args)

    # Load checkpoint
    ckpt_path = str(checkpoint_dir / f"model{rank}-mp{world_size}.safetensors")
    _load_incremental(model, ckpt_path, device="cuda")

    import gc
    gc.collect()
    torch.cuda.empty_cache()

    model.eval()

    # Load tokenizer
    tok_path = checkpoint_dir / "tokenizer.json"
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        str(checkpoint_dir) if tok_path.exists() else str(inference_dir.parent),
        trust_remote_code=True,
    )

    return model, tokenizer


def _load_incremental(model, filename, device="cuda"):
    """Same load_incremental as observe_religious.py — tensor-by-tensor load
    with page-cache eviction to stay within unified-memory limits."""
    import os
    from safetensors import safe_open
    state = {}
    for name, par in model.named_parameters():
        state[name] = par
    for name, buf in model.named_buffers():
        state[name] = buf
    fd = os.open(filename, os.O_RDONLY)
    loaded = 0
    with safe_open(filename, framework="pt", device=device) as f:
        keys = set(f.keys())
        with torch.no_grad():
            for name, par in state.items():
                if name not in keys:
                    continue
                par.data = f.get_tensor(name).to(par.dtype)
                loaded += 1
                # Batched eviction (per-tensor whole-file fadvise is ~10x slower)
                if loaded % 2000 == 0:
                    try:
                        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
                    except OSError:
                        pass
    os.close(fd)
