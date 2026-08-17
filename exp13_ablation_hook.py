#!/usr/bin/env python3
"""
Exp 13: Scoped H6 Expert Ablation Hook

This module provides two ablation modes that can be injected into the
observation harness (observe_religious.py) to measure the causal
contribution of H6 experts to next-token prediction.

MODE 1 — Contribution Knockout (primary):
    Retain original top-6 selection and gate weights.
    Zero the chosen expert's output contribution.
    Measures: harm of removing the contribution without changing the gate's decision.

MODE 2 — Route-Mask Compensation (secondary):
    Mask selected experts before top-k, choose replacements, renormalize.
    Measures: whether the model can compensate with another expert.

Both modes are implemented as drop-in replacements for observed_moe_forward.
The hook reads a registry of (layer, expert) pairs to ablate.

Usage in the harness:
    from exp13_ablation_hook import make_ablated_moe_forward, ABLATION_REGISTRY

    # Set up the registry
    ABLATION_REGISTRY.update({
        21: {42},   # H6-A1
        22: {105},  # H6-A2
        23: {113},  # H6-A3
        30: {198},  # H6-A4
        32: {254},  # H6-A5
        41: {147},  # H6-A6
    })

    # Replace the MoE forward
    DSV4.MoE.forward = make_ablated_moe_forward(mode="knockout")

    # To run the sham control (no experts ablated, but hook installed):
    ABLATION_REGISTRY.clear()
    # ... run the same inputs

DESIGN NOTES (per FORWARD_PLAN.md):
    - Does NOT modify checkpoint files. The hook is a temporary inference-time
      intervention, logged and removed after the run.
    - Both ranks must apply the same global registry, each only zeroing its
      locally sharded experts before the normal all-reduce.
    - The sham hook must give a negligible delta within a pre-set numerical
      tolerance (execution control).
    - Primary outcome: per-block Delta-NLL = NLL(ablation) - NLL(baseline)
      in nats/token. This requires the FULL output head (not nohead_forward).
    - Secondary outcomes: change in true-token probability, top-1/top-5
      agreement, KL divergence from baseline final distribution.

The harness currently uses nohead_forward (bypasses the vocab head to
avoid OOM on 121GB unified memory). For Exp 13, we need the full head.
Strategy: evaluate short fixed blocks (512-1024 tokens) or stream the
head and cross-entropy in token chunks.
"""

import json
import torch
import torch.distributed as dist
from typing import Any, Dict, Set

# ══════════════════ REGISTRY ══════════════════

# Frozen H6 anchor registry — the 6 primary anchors
H6_ANCHORS: Dict[int, Set[int]] = {
    21: {42},    # H6-A1
    22: {105},    # H6-A2
    23: {113},    # H6-A3
    30: {198},    # H6-A4
    32: {254},    # H6-A5
    41: {147},    # H6-A6
}

# Active ablation registry — mutable, set before each run
ABLATION_REGISTRY: Dict[int, Set[int]] = {}

# Dose series: cumulative sets of anchors
DOSE_SERIES = {
    "dose_1": {21: {42}},                           # 1 anchor
    "dose_3": {21: {42}, 22: {105}, 23: {113}},      # 3 anchors
    "dose_6": H6_ANCHORS.copy(),                      # all 6 anchors
}


def set_dose(dose_name: str):
    """Set the ablation registry to a specific dose."""
    ABLATION_REGISTRY.clear()
    if dose_name in DOSE_SERIES:
        ABLATION_REGISTRY.update(DOSE_SERIES[dose_name])
    elif dose_name == "sham":
        pass  # Empty registry = no ablation, but hook is installed
    elif dose_name == "single_a1":
        ABLATION_REGISTRY.update({21: {42}})
    elif dose_name == "single_a2":
        ABLATION_REGISTRY.update({22: {105}})
    elif dose_name == "single_a3":
        ABLATION_REGISTRY.update({23: {113}})
    elif dose_name == "single_a4":
        ABLATION_REGISTRY.update({30: {198}})
    elif dose_name == "single_a5":
        ABLATION_REGISTRY.update({32: {254}})
    elif dose_name == "single_a6":
        ABLATION_REGISTRY.update({41: {147}})


# ══════════════════ MODE 1: CONTRIBUTION KNOCKOUT ══════════════════

def make_ablated_moe_forward(mode: str = "knockout"):
    """Create an ablated MoE forward function.

    mode="knockout":  Zero the output of ablated experts, keep gate selection.
    mode="route_mask": Mask ablated experts before top-k, reselect, renormalize.
    """
    if mode == "knockout":
        return knockout_moe_forward
    elif mode == "route_mask":
        return route_mask_moe_forward
    else:
        raise ValueError(f"Unknown ablation mode: {mode}")


def knockout_moe_forward(self: Any, x: torch.Tensor, input_ids: torch.Tensor) -> torch.Tensor:
    """Contribution knockout: keep top-6 selection, zero ablated expert outputs.

    The gate still selects the H6 experts (so we can measure their selection
    frequency), but their contribution to the output is zeroed. This measures
    the harm of removing the contribution without silently changing the gate's
    decision.
    """
    shape = x.size()
    x = x.view(-1, self.dim)
    gate = self.gate
    logits = DSV4.linear(x.float(), gate.weight.float())

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

    # ── KNOCKOUT: zero the runtime weight for ablated experts ──
    layer_id = int(self.layer_id)
    ablated = ABLATION_REGISTRY.get(layer_id, set())
    if ablated:
        # Create a mask: for each token's top-6, check if any selected expert
        # is in the ablated set. If so, zero its weight (but keep it selected).
        for expert_id in ablated:
            mask = (indices == expert_id)
            if mask.any():
                # Zero the weight for this expert's contributions
                token_idx, top_idx = torch.where(mask)
                runtime_weights[token_idx, top_idx] = 0.0

    y = torch.zeros_like(x, dtype=torch.float32)
    frequencies = torch.bincount(indices.flatten(), minlength=self.n_routed_experts)
    counts = frequencies.tolist()

    for expert_id in range(self.experts_start_idx, self.experts_end_idx):
        if counts[expert_id] == 0:
            continue
        expert = self.experts[expert_id]
        token_index, top_index = torch.where(indices == expert_id)

        if expert_id in ablated:
            # ── KNOCKOUT: skip computing the expert output, contribute zero ──
            # The expert is "selected" (frequency counts it) but contributes nothing.
            pass
        else:
            unweighted = expert(x[token_index])
            y[token_index] += unweighted.float() * runtime_weights[
                token_index, top_index, None
            ].float()

    if DSV4.world_size > 1:
        dist.all_reduce(y)

    y += self.shared_experts(x)
    return y.type_as(x).view(shape)


# ══════════════════ MODE 2: ROUTE-MASK COMPENSATION ══════════════════

def route_mask_moe_forward(self: Any, x: torch.Tensor, input_ids: torch.Tensor) -> torch.Tensor:
    """Route-mask compensation: mask ablated experts before top-k, reselect.

    The ablated experts are removed from the candidate pool before top-k
    selection. The model picks replacement experts from the remaining pool
    and renormalizes exactly as the normal gate would. This measures whether
    the model can compensate with another expert.
    """
    shape = x.size()
    x = x.view(-1, self.dim)
    gate = self.gate
    logits = DSV4.linear(x.float(), gate.weight.float())

    if gate.score_func == "softmax":
        original_scores = logits.softmax(dim=-1)
    elif gate.score_func == "sigmoid":
        original_scores = logits.sigmoid()
    else:
        original_scores = torch.nn.functional.softplus(logits).sqrt()

    selection_scores = original_scores
    if gate.bias is not None:
        selection_scores = selection_scores + gate.bias

    # ── ROUTE MASK: set ablated experts' scores to -inf before top-k ──
    layer_id = int(self.layer_id)
    ablated = ABLATION_REGISTRY.get(layer_id, set())
    if ablated and not gate.hash:
        # Mask the ablated experts so they can't be selected
        masked_scores = selection_scores.clone()
        for expert_id in ablated:
            masked_scores[:, expert_id] = float('-inf')
        indices = masked_scores.topk(gate.topk, dim=-1)[1]
    elif gate.hash:
        indices = gate.tid2eid[input_ids.flatten()]
    else:
        indices = selection_scores.topk(gate.topk, dim=-1)[1]

    # Renormalize over the new top-k (excluding ablated experts)
    normalized_weights = original_scores.gather(1, indices)
    if gate.score_func != "softmax":
        normalized_weights = normalized_weights / normalized_weights.sum(
            dim=-1, keepdim=True
        )
    runtime_weights = normalized_weights * gate.route_scale

    y = torch.zeros_like(x, dtype=torch.float32)
    frequencies = torch.bincount(indices.flatten(), minlength=self.n_routed_experts)
    counts = frequencies.tolist()

    for expert_id in range(self.experts_start_idx, self.experts_end_idx):
        if counts[expert_id] == 0:
            continue
        expert = self.experts[expert_id]
        token_index, top_index = torch.where(indices == expert_id)
        unweighted = expert(x[token_index])
        y[token_index] += unweighted.float() * runtime_weights[
            token_index, top_index, None
        ].float()

    if DSV4.world_size > 1:
        dist.all_reduce(y)

    y += self.shared_experts(x)
    return y.type_as(x).view(shape)


# ══════════════════ NLL EVALUATION ══════════════════

def compute_nll_chunked(model, input_ids, chunk_size=512):
    """Compute per-token NLL using the full output head, chunked to avoid OOM.

    For Exp 13, we need the full vocab head (129,280) to compute cross-entropy.
    The 121GB unified memory can't hold vocab×16k logits, so we process in
    512-token chunks with teacher forcing.

    Returns: (mean_nll, per_token_nll tensor)
    """
    total_nll = 0.0
    total_tokens = 0
    per_token_nlls = []

    seq_len = input_ids.shape[1]
    for start in range(0, seq_len - 1, chunk_size):
        end = min(start + chunk_size, seq_len)
        chunk_len = end - start
        if chunk_len < 2:
            continue

        # Teacher-forced: feed tokens [0:end], predict tokens [start:end]
        # The model processes the full context up to `end`, but we only
        # compute loss on the last `chunk_len` positions.
        chunk_input = input_ids[:, :end]
        with torch.no_grad():
            logits = model.head(model.forward(chunk_input)[0])  # [1, end, vocab]
            # We only need the last chunk_len positions
            chunk_logits = logits[:, -chunk_len:, :]  # [1, chunk_len, vocab]
            chunk_targets = input_ids[:, start+1:end+1] if end < seq_len else input_ids[:, start+1:]

            # Compute cross-entropy
            loss = torch.nn.functional.cross_entropy(
                chunk_logits.reshape(-1, chunk_logits.size(-1)),
                chunk_targets.reshape(-1),
                reduction='none'
            )
            per_token_nlls.append(loss)
            total_nll += loss.sum().item()
            total_tokens += loss.numel()

    mean_nll = total_nll / max(total_tokens, 1)
    return mean_nll, torch.cat(per_token_nlls) if per_token_nlls else torch.tensor([])


# ══════════════════ RUN PLANNER ══════════════════

RUN_PLAN = {
    "modes": [
        {"name": "baseline", "mode": None, "registry": {}},
        {"name": "sham", "mode": "knockout", "registry": {}},
        {"name": "knockout_a1", "mode": "knockout", "registry": {21: {42}}},
        {"name": "knockout_a2", "mode": "knockout", "registry": {22: {105}}},
        {"name": "knockout_a3", "mode": "knockout", "registry": {23: {113}}},
        {"name": "knockout_a4", "mode": "knockout", "registry": {30: {198}}},
        {"name": "knockout_a5", "mode": "knockout", "registry": {32: {254}}},
        {"name": "knockout_a6", "mode": "knockout", "registry": {41: {147}}},
        {"name": "knockout_dose3", "mode": "knockout", "registry": {21: {42}, 22: {105}, 23: {113}}},
        {"name": "knockout_dose6", "mode": "knockout", "registry": H6_ANCHORS.copy()},
        {"name": "route_mask_dose6", "mode": "route_mask", "registry": H6_ANCHORS.copy()},
    ],
    "corpora": [
        {"name": "kjv_verse", "description": "Digit-stripped KJV verse (held-out chapters)"},
        {"name": "christian_prose", "description": "Christian commentary (held-out books)"},
        {"name": "secular_verse", "description": "Milton/Wordsworth (public domain secular verse)"},
        {"name": "secular_prose", "description": "Essays/articles (public domain secular prose)"},
    ],
    "primary_outcome": "Delta-NLL = NLL(ablation) - NLL(baseline) in nats/token",
    "primary_estimand": "b_interaction: greater damage on prose than verse",
    "controls": [
        "Sham hook must give ~0 delta (execution control)",
        "20 random six-expert control clusters matched on routing frequency",
        "Digit-cluster positive control on digit-minimal-pair subset",
        "Fixed seed, identical tokenization, rank-by-rank registry logging",
    ],
}


if __name__ == "__main__":
    print("Exp 13: Scoped H6 Ablation Hook")
    print("=" * 60)
    print(f"H6 Anchors: {H6_ANCHORS}")
    print(f"\nRun plan: {len(RUN_PLAN['modes'])} modes × {len(RUN_PLAN['corpora'])} corpora")
    print(f"Primary outcome: {RUN_PLAN['primary_outcome']}")
    print(f"Primary estimand: {RUN_PLAN['primary_estimand']}")
    print(f"\nControls:")
    for c in RUN_PLAN["controls"]:
        print(f"  - {c}")
    print(f"\nModes:")
    for m in RUN_PLAN["modes"]:
        print(f"  {m['name']:>20}: mode={m['mode']}, registry={m['registry']}")
