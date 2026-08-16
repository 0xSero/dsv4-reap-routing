# REAP Routing Analysis — DeepSeek-V4-Flash-0731 on Religious Texts

Read-only interpretability study of MoE expert routing (43 layers × 256 routed
experts, top-6) across religious corpora, running TP2 on a DGX Spark (GB10)
pair. No weights modified.

**Site (wiki + narrative):** https://0xsero.github.io/dsv4-reap-routing/

## Data — one HuggingFace project

All observations, J-lens probes, corpus manifests, analysis and code live in a
single private HF dataset (access on request):
**`0xSero/deepseek-v4-flash-reap`** — https://huggingface.co/datasets/0xSero/deepseek-v4-flash-reap

| Subdataset | Contents |
|---|---|
| `observations/religious-8text/` | REAP activations, 8 scriptures (1,482 records) |
| `observations/christian-wave1/` | Christian literature, 1,267 records / 20.4M tokens |
| `jlens/` | Logit-lens + bounded Jacobians, 80 samples × 8 traditions |
| `corpus/manifests/`, `corpus/theology/` | Corpus manifests + theology scraping manifests (~113M tokens scraped: Jesus, Lucifer, Judaism, Moloch, Saturn) |
| `analysis/` | Rankings, Jaccard matrices, robustness checks (incl. permutation-confound kill) |
| `code/` | Sanitized harness scripts |

Large raw archives are also on GitHub Releases (`raw-observations-v1`,
`christian-wave1-v1`).

## Docker

The observation harness ships as a container (build from this repo — see
`Dockerfile` / `docker-compose.yml`). Base image
`ghcr.io/anemll/dspark-vllm-gx10:0.1.1` (GB10/sm121a). One rank per node,
NCCL over the ConnectX link; `run_full_observation.sh` orchestrates both ranks.

```bash
docker build -t dsv4-reap-obs:latest .
docker run -d --name obs-r0 --privileged --network host \
  -v $CKPT:/ckpt -v $OBS:/obs-religious \
  -e RANK=0 -e WORLD_SIZE=2 -e MASTER_ADDR=10.0.1.1 dsv4-reap-obs:latest
```

## Headline findings

- **Final-layer surface-form specialists** (corrected 2026-08-16 after external
  review): a cluster of L42 experts (e164, e27, e68, ~29 more) is gated
  near-perfectly by digit density — monotone 0→16,448/M across digit deciles
  within a single corpus. Not a memorization detector (see wiki §9).
- **Routing overlap carries no doctrinal information**: upanishads↔christian
  (0.477) > bofm↔christian (0.436) > bible↔christian (0.326).
- **Per-sample effective experts@L40**: Gita 24 < Qur'an 40 < Bible 54 —
  predictability narrows the palette (Christian's 111 was a pooling artifact).
- Withdrawn after review: "not-memorized-scripture e164", the layer sandwich
  (reap_score artifact; inverts on frequencies), the Genesis logit-lens claim.
  Full correction log: wiki §9 + reviews/.

## Status

- 8-text observation: DONE. Christian wave-1: DONE. J-lens: DONE (80/80).
- Christian wave-2 (2,295 books): running. Theology corpus (~113M tokens):
  scraped, observation queued. Experiments: see `EXPERIMENTS.md`.
