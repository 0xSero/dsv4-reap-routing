#!/usr/bin/env bash
# run_full_observation.sh — Orchestrate the TP2 observation run
# across the original DGX Spark pair (de5c + 557f, IB network 10.0.1.x).
#
# Prerequisites (verified at launch time):
#   - Converted checkpoint model{0,1}-mp2.safetensors exist on both nodes
#   - Full corpus all_religious.jsonl pushed to both nodes
#   - observe_religious.py (with NCCL init AFTER model loading) on both nodes
#   - earlyoom running on both nodes
#
# Usage:
#   ./run_full_observation.sh                # full 1482-sample run
#   ./run_full_observation.sh --smoke         # smoke test (2 samples)
#   ./run_full_observation.sh --limit 10       # custom limit
#   ./run_full_observation.sh --no-sidecar     # disable HF streaming
#
# SSH path: Mac -> 557f (192.168.1.96, key) -> de5c (10.0.1.1, password)
set -euo pipefail

HEAD="valentine@10.0.1.1"
WORKER="root@192.168.1.96"
JUMP="-J valentine@192.168.1.96"
if [ -z "${SSHPASS:-}" ]; then echo "ERROR: set SSHPASS env var before running" >&2; exit 1; fi
SSH_HEAD="sshpass -e ssh -o ConnectTimeout=15 -o PubkeyAuthentication=no -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node $JUMP"
SCP_HEAD="sshpass -e scp -o ConnectTimeout=15 -o PubkeyAuthentication=no -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node $JUMP"
SSH_WORKER="ssh -o ConnectTimeout=15 -o BatchMode=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"
SCP_WORKER="scp -o ConnectTimeout=15 -o BatchMode=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"

IMG="local/dspark-vllm-gx10:proven-0731"
INF_DIR="/models/deepseek-ai/DeepSeek-V4-Flash-0731/inference"
CKPT_HEAD="/models-converted/dsv4-mp2"
CKPT_WORKER="/models-converted/dsv4-mp2-worker"
CONFIG="${INF_DIR}/config.json"
INPUT="${OBS_INPUT:-/obs-religious/all_religious.jsonl}"
OUTPUT="${OBS_OUTPUT:-/obs-religious/full_obs.jsonl}"
LOCAL_CORPUS="${OBS_LOCAL_CORPUS:-}"   # if set, scp'd to both nodes first
MASTER_PORT=29556

# NCCL env vars — force socket transport (IB/RoCE not available in container)
# Tested: NCCL_IB_DISABLE=1 + NCCL_NET=SOCKET works, without it NCCL falls
# back to socket flakily and all_reduce fails with "Bad address" / "socket progress error"
NCCL_ENV=(
  -e NCCL_SOCKET_IFNAME=enp1s0f0np0
  -e NCCL_DEBUG=WARN
  -e NCCL_IB_DISABLE=1
  -e NCCL_NET=SOCKET
  -e NCCL_SOCKET_NTHREADS=1
  -e NCCL_NSOCKS_PERTHREAD=1
  -e NCCL_TIMEOUT=600
  -e TORCH_NCCL_ENABLE_MONITORING=0
  -e TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC=600
  -e TORCH_NCCL_DUMP_ON_TIMEOUT=0
  -e GLOO_SOCKET_IFNAME=enp1s0f0np0
)

# Parse args
LIMIT_ARG=""
RUN_SIDECAR=true
for arg in "$@"; do
  case "$arg" in
    --smoke)         LIMIT_ARG="--limit 2"; OUTPUT="/obs-religious/smoke_obs.jsonl" ;;
    --limit)         shift; LIMIT_ARG="--limit $1" ;;
    --no-sidecar)    RUN_SIDECAR=false ;;
  esac
done

echo "=== Phase 2 TP2 Observation (de5c rank0 + 557f rank1, IB 10.0.1.x) ==="
echo "Time: $(date)"
echo "Limit: ${LIMIT_ARG:-full (1482 samples)}"
echo "Output: ${OUTPUT}"

# Step 1: Stop any prior containers
echo "--- Stopping prior containers ---"
$SSH_HEAD "$HEAD" "docker rm -f obs-r0 2>/dev/null && echo 'removed obs-r0' || echo 'obs-r0 not present'" 2>&1
$SSH_WORKER "$WORKER" "docker rm -f obs-r1 2>/dev/null && echo 'removed obs-r1' || echo 'obs-r1 not present'" 2>&1

# Step 2: DEPLOY the harness from THIS Mac to both nodes (previous versions
# only "verified" a stale marker — Mac edits never reached the nodes).
echo "--- Deploying observe_religious.py ---"
$SCP_WORKER "$PWD/observe_religious.py" "$WORKER:/home/valentine/obs-religious/observe_religious.py"
$SCP_HEAD "$PWD/observe_religious.py" "$HEAD:/home/valentine/obs-religious/observe_religious.py"

# Step 2a: Deploy corpus override (if requested) to both nodes
if [[ -n "${LOCAL_CORPUS}" ]]; then
  echo "--- Deploying corpus ${LOCAL_CORPUS} -> ${INPUT} ---"
  $SCP_WORKER "$LOCAL_CORPUS" "$WORKER:/home/valentine${INPUT}"
  $SCP_HEAD "$LOCAL_CORPUS" "$HEAD:/home/valentine${INPUT}"
fi

# Step 2b: Verify prerequisites — with a REAL content check this time:
# the deployed file must NOT contain the buggy frequencies all_reduce.
echo "--- Verifying prerequisites ---"
$SSH_HEAD "$HEAD" "
  test -f /home/valentine${CKPT_HEAD}/model0-mp2.safetensors && echo 'ckpt_head OK' || { echo 'CKPT_HEAD MISSING'; exit 1; }
  test -f /home/valentine${INPUT} && echo 'corpus_head OK' || { echo 'CORPUS_HEAD MISSING'; exit 1; }
  test -f /home/valentine/obs-religious/observe_religious.py && echo 'harness_head OK' || { echo 'HARNESS_HEAD MISSING'; exit 1; }
  ! grep -q 'all_reduce(frequencies)' /home/valentine/obs-religious/observe_religious.py && grep -q 'freq_debug' /home/valentine/obs-religious/observe_religious.py && echo 'harness_head FIXED' || { echo 'HARNESS_HEAD OLD VERSION'; exit 1; }
" 2>&1
$SSH_WORKER "$WORKER" "
  test -f /home/valentine${CKPT_WORKER}/model1-mp2.safetensors && echo 'ckpt_worker OK' || { echo 'CKPT_WORKER MISSING'; exit 1; }
  test -f /home/valentine${INPUT} && echo 'corpus_worker OK' || { echo 'CORPUS_WORKER MISSING'; exit 1; }
  test -f /home/valentine/obs-religious/observe_religious.py && echo 'harness_worker OK' || { echo 'HARNESS_WORKER MISSING'; exit 1; }
  ! grep -q 'all_reduce(frequencies)' /home/valentine/obs-religious/observe_religious.py && grep -q 'freq_debug' /home/valentine/obs-religious/observe_religious.py && echo 'harness_worker FIXED' || { echo 'HARNESS_WORKER OLD VERSION'; exit 1; }
" 2>&1

# Step 3: Clean prior output
echo "--- Prior output handling ---"
# Resume-safe: only delete output on smoke runs. Full runs resume from the
# fsynced JSONL via completed_keys() — never throw away good records.
if [[ "${LIMIT_ARG}" == "--limit 2" ]]; then
  $SSH_HEAD "$HEAD" "rm -f /home/valentine${OUTPUT} 2>/dev/null; echo cleaned_head" 2>&1
  $SSH_WORKER "$WORKER" "rm -f /home/valentine${OUTPUT} 2>/dev/null; echo cleaned_worker" 2>&1
else
  N_HEAD=$($SSH_HEAD "$HEAD" "wc -l < /home/valentine${OUTPUT} 2>/dev/null || echo 0" 2>/dev/null)
  echo "resuming: ${N_HEAD} records already on head (will be skipped)"
fi

# Step 4: Launch rank 1 (worker, 557f) FIRST so it's ready for rendezvous
echo "--- Launching obs-r1 (worker, rank 1, 557f) ---"
$SSH_WORKER "$WORKER" "
docker run -d --name obs-r1 --gpus all --network host --ipc=host \
  --ulimit nofile=65536:65536 \
  --entrypoint bash \
  -v /home/valentine/models:/models \
  -v /home/valentine/models-converted:/models-converted \
  -v /home/valentine/obs-religious:/obs-religious \
  -e WORLD_SIZE=2 -e RANK=1 -e LOCAL_RANK=0 \
  -e MASTER_ADDR=10.0.1.1 -e MASTER_PORT=${MASTER_PORT} \
  ${NCCL_ENV[@]} \
  '$IMG' -c 'ulimit -n 65536 && cd /obs-religious && python3 -u observe_religious.py \
    --inference-dir ${INF_DIR} \
    --checkpoint ${CKPT_WORKER} \
    --config ${CONFIG} \
    --input-jsonl ${INPUT} \
    --output-jsonl ${OUTPUT} \
    --max-seq-len 16384 ${LIMIT_ARG} 2>&1 | tee /obs-religious/full_r1.log'
echo 'obs-r1 launched'
" 2>&1

sleep 3

# Step 5: Launch rank 0 (head, de5c)
echo "--- Launching obs-r0 (head, rank 0, de5c) ---"
$SSH_HEAD "$HEAD" "
docker run -d --name obs-r0 --gpus all --network host --ipc=host \
  --ulimit nofile=65536:65536 \
  --entrypoint bash \
  -v /home/valentine/models:/models \
  -v /home/valentine/models-converted:/models-converted \
  -v /home/valentine/obs-religious:/obs-religious \
  -e WORLD_SIZE=2 -e RANK=0 -e LOCAL_RANK=0 \
  -e MASTER_ADDR=10.0.1.1 -e MASTER_PORT=${MASTER_PORT} \
  ${NCCL_ENV[@]} \
  '$IMG' -c 'ulimit -n 65536 && cd /obs-religious && python3 -u observe_religious.py \
    --inference-dir ${INF_DIR} \
    --checkpoint ${CKPT_HEAD} \
    --config ${CONFIG} \
    --input-jsonl ${INPUT} \
    --output-jsonl ${OUTPUT} \
    --max-seq-len 16384 ${LIMIT_ARG} 2>&1 | tee /obs-religious/full_r0.log'
echo 'obs-r0 launched'
" 2>&1

echo "--- Both ranks launched. Model loading ~10 min, then NCCL rendezvous. ---"
echo "Monitor rank0: $SSH_HEAD '$HEAD' 'docker logs --tail 10 obs-r0'"
echo "Monitor rank1: $SSH_WORKER '$WORKER' 'docker logs --tail 10 obs-r1'"
echo "Output: /home/valentine${OUTPUT} on both nodes"

# Step 6: Start HF streaming sidecar (optional, full runs only)
if [ "$RUN_SIDECAR" = true ] && [ -z "$LIMIT_ARG" ]; then
  echo "--- Starting HF streaming sidecar ---"
  LOCAL_FIFO="/tmp/obs_full.jsonl"
  rm -f "$LOCAL_FIFO"
  mkfifo "$LOCAL_FIFO"

  ($SSH_HEAD "$HEAD" "tail -f /home/valentine${OUTPUT}" > "$LOCAL_FIFO" 2>/dev/null) &
  TAIL_PID=$!

  python3 "$(dirname "$0")/stream_to_hf.py" \
    --input "$LOCAL_FIFO" \
    --state "$(dirname "$0")/stream_state.json" \
    --repo "0xSero/deepseek-v4-flash-religious-reap-observations" \
    --run-pid "$TAIL_PID" \
    --shard-rows 200 \
    --private &
  SIDECAR_PID=$!
  echo "Sidecar PID: $SIDECAR_PID, Tail PID: $TAIL_PID"
fi

echo "--- Orchestration complete. Ranks are running. ---"
