# DeepSeek-V4-Flash-0731 REAP observation harness — container image
#
# Runs the read-only expert-routing observation (observe_religious.py) for one
# TP rank. Designed for the DGX Spark (GB10, sm121a/aarch64) pair: build once,
# run as rank 0 on the head node and rank 1 on the worker, joined by NCCL over
# the ConnectX link.
#
# Build:
#   docker build -t dsv4-reap-obs:latest .
# Run (head, rank 0):
#   docker run -d --name obs-r0 --privileged --network host \
#     -v /path/to/converted-ckpt:/ckpt -v /path/to/obs-religious:/obs-religious \
#     -e RANK=0 -e WORLD_SIZE=2 -e MASTER_ADDR=10.0.1.1 \
#     dsv4-reap-obs:latest
# Run (worker, rank 1): same with -e RANK=1 -e MASTER_ADDR=10.0.1.1
#
# Inputs (volume /obs-religious):  <corpus>.jsonl  rows: {category, sample_index, token_ids}
# Outputs (same volume):           <corpus>_obs.jsonl  rows: {category, sample_index, seqlen,
#                                  source, observation:{layers:{"0".."42":{gate_weights[256],
#                                  activation_norms[256], reap_score[256], routed_experts[],
#                                  expert_frequencies[256]}}}}
# Fail-closed: sum(expert_frequencies)==seqlen*6 asserted per layer per record;
# per-sample fsync; resume-safe (skips already-written (category, sample_index)).

FROM ghcr.io/anemll/dspark-vllm-gx10:0.1.1

WORKDIR /workspace
COPY code/ /workspace/

# pinned tokenizer is fetched at first run into /workspace/tokenizer
ENV TOKENIZER_ID=deepseek-ai/DeepSeek-V4-Flash-0731 \
    TOKENIZER_REV=9e165c30e2704aec5d9d593cce3eebd58bbef1cb \
    CKPT_DIR=/ckpt/converted-mp2 \
    INPUT=/obs-religious/corpus.jsonl \
    OUTPUT=/obs-religious/corpus_obs.jsonl

# observe_religious.py takes --input/--output/--ckpt/--tokenizer; rank/-world
# come from the TP env (RANK, WORLD_SIZE, MASTER_ADDR, MASTER_PORT).
CMD ["python3", "/workspace/observe_religious.py", \
     "--input", "/obs-religious/corpus.jsonl", \
     "--output", "/obs-religious/corpus_obs.jsonl", \
     "--ckpt", "/ckpt", "--max-seqlen", "16384"]
