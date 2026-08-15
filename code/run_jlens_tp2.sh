#!/usr/bin/env bash
# run_jlens_tp2.sh — Launch the J-lens (logit + bounded Jacobian) TP2 run
# across the DS4 spark pair. Run AFTER Phase 2 observation completes.
#
# Usage:
#   ./run_jlens_tp2.sh
#
# SSH path: Mac -> 557f (192.168.1.96, key) -> de5c (10.0.1.1, password)
set -euo pipefail

HEAD="valentine@10.0.1.1"
WORKER="root@192.168.1.96"
JUMP="-J valentine@192.168.1.96"
export SSHPASS='$SSHPASS_ENV'
SSH_HEAD="sshpass -e ssh -o ConnectTimeout=30 -o PubkeyAuthentication=no -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node $JUMP"
SCP_HEAD="sshpass -e scp -o ConnectTimeout=30 -o PubkeyAuthentication=no -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node $JUMP"
SSH_WORKER="ssh -o ConnectTimeout=30 -o BatchMode=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"
SCP_WORKER="scp -o ConnectTimeout=30 -o BatchMode=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"

# NCCL env common to both ranks — proven on this pair: IB/RoCE unusable in the
# container, socket transport is the only reliable path.
NCCL_ENV="-e NCCL_SOCKET_IFNAME=enp1s0f0np0 -e NCCL_DEBUG=WARN \
  -e NCCL_IB_DISABLE=1 -e NCCL_NET=SOCKET \
  -e NCCL_SOCKET_NTHREADS=4 -e NCCL_NSOCKS_PERTHREAD=4 \
  -e TORCH_NCCL_ENABLE_MONITORING=0 -e TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC=1800 \
  -e TORCH_NCCL_DUMP_ON_TIMEOUT=0 -e GLOO_SOCKET_IFNAME=enp1s0f0np0"

IMG="local/dspark-vllm-gx10:proven-0731"
INF_DIR="/models/deepseek-ai/DeepSeek-V4-Flash-0731/inference"
CKPT_HEAD="/models-converted/dsv4-mp2"
CKPT_WORKER="/models-converted/dsv4-mp2-worker"
CONFIG="${INF_DIR}/config.json"
CORPUS="/obs-religious/all_religious.jsonl"
OUTPUT_DIR="/obs-religious/jlens_output"
MASTER_PORT=29558

echo "=== Phase 4: J-lens TP2 Orchestration ==="
echo "Time: $(date)"

# Step 1: Stop any prior jlens containers
echo "--- Stopping prior jlens containers ---"
$SSH_HEAD "$HEAD" "docker rm -f jlens-r0 2>/dev/null && echo 'removed jlens-r0' || echo 'jlens-r0 not present'" 2>&1
$SSH_WORKER "$WORKER" "docker rm -f jlens-r1 2>/dev/null && echo 'removed jlens-r1' || echo 'jlens-r1 not present'" 2>&1

# Step 2: Also stop any observation containers if still running
echo "--- Stopping any obs containers ---"
$SSH_HEAD "$HEAD" "docker rm -f obs-r0 2>/dev/null && echo 'removed obs-r0' || echo 'obs-r0 not present'" 2>&1
$SSH_WORKER "$WORKER" "docker rm -f obs-r1 2>/dev/null && echo 'removed obs-r1' || echo 'obs-r1 not present'" 2>&1

# Step 3: DEPLOY the jlens scripts from THIS Mac to both nodes
echo "--- Deploying jlens scripts ---"
$SCP_WORKER "$PWD/run_jlens.py" "$WORKER:/home/valentine/obs-religious/run_jlens.py"
$SCP_WORKER "$PWD/jlens_dsv4.py" "$WORKER:/home/valentine/obs-religious/jlens_dsv4.py"
$SCP_HEAD "$PWD/run_jlens.py" "$HEAD:/home/valentine/obs-religious/run_jlens.py"
$SCP_HEAD "$PWD/jlens_dsv4.py" "$HEAD:/home/valentine/obs-religious/jlens_dsv4.py"

# Step 3b: Verify prerequisites — real content checks
echo "--- Verifying prerequisites ---"
$SSH_HEAD "$HEAD" "
  test -f /home/valentine${CKPT_HEAD}/model0-mp2.safetensors && echo 'ckpt_head OK' || { echo 'CKPT_HEAD MISSING'; exit 1; }
  grep -q 'DSV4.sparse_attn' /home/valentine/obs-religious/jlens_dsv4.py && echo 'jlens_adapter_head FIXED' || { echo 'JLENS_ADAPTER_HEAD OLD VERSION'; exit 1; }
" 2>&1
$SSH_WORKER "$WORKER" "
  test -f /home/valentine${CKPT_WORKER}/model1-mp2.safetensors && echo 'ckpt_worker OK' || { echo 'CKPT_WORKER MISSING'; exit 1; }
  grep -q 'DSV4.sparse_attn' /home/valentine/obs-religious/jlens_dsv4.py && echo 'jlens_adapter_worker FIXED' || { echo 'JLENS_ADAPTER_WORKER OLD VERSION'; exit 1; }
" 2>&1

# Step 4: Create output dir on head
$SSH_HEAD "$HEAD" "mkdir -p /home/valentine${OUTPUT_DIR} && echo 'output_dir ready'" 2>&1

# Step 5: Launch rank 1 (worker) FIRST
echo "--- Launching jlens-r1 (worker, rank 1) ---"
$SSH_WORKER "$WORKER" "
docker run -d --name jlens-r1 --gpus all --network host --ipc=host \
  --entrypoint bash --ulimit nofile=65536:65536 \
  -v /home/valentine/models:/models \
  -v /home/valentine/models-converted:/models-converted \
  -v /home/valentine/obs-religious:/obs-religious \
  -e WORLD_SIZE=2 -e RANK=1 -e LOCAL_RANK=0 \
  -e MASTER_ADDR=10.0.1.1 -e MASTER_PORT=${MASTER_PORT} \
  ${NCCL_ENV} \
  '$IMG' -c 'ulimit -n 65536 && cd /obs-religious && python3 -u run_jlens.py \
    --inference-dir ${INF_DIR} \
    --checkpoint ${CKPT_WORKER} \
    --config ${CONFIG} \
    --corpus ${CORPUS} \
    --output ${OUTPUT_DIR} \
    --max-prompts-per-text 10 \
    --max-seq-len 1024 \
    --jacobian-n-proj 16 \
    --jacobian-source-layers 0,10,20,30,42 2>&1 | tee /obs-religious/jlens_r1.log'
echo 'jlens-r1 launched'
" 2>&1

sleep 3

# Step 6: Launch rank 0 (head)
echo "--- Launching jlens-r0 (head, rank 0) ---"
$SSH_HEAD "$HEAD" "
docker run -d --name jlens-r0 --gpus all --network host --ipc=host \
  --entrypoint bash --ulimit nofile=65536:65536 \
  -v /home/valentine/models:/models \
  -v /home/valentine/models-converted:/models-converted \
  -v /home/valentine/obs-religious:/obs-religious \
  -e WORLD_SIZE=2 -e RANK=0 -e LOCAL_RANK=0 \
  -e MASTER_ADDR=10.0.1.1 -e MASTER_PORT=${MASTER_PORT} \
  ${NCCL_ENV} \
  '$IMG' -c 'ulimit -n 65536 && cd /obs-religious && python3 -u run_jlens.py \
    --inference-dir ${INF_DIR} \
    --checkpoint ${CKPT_HEAD} \
    --config ${CONFIG} \
    --corpus ${CORPUS} \
    --output ${OUTPUT_DIR} \
    --max-prompts-per-text 10 \
    --max-seq-len 1024 \
    --jacobian-n-proj 16 \
    --jacobian-source-layers 0,10,20,30,42 2>&1 | tee /obs-religious/jlens_r0.log'
echo 'jlens-r0 launched'
" 2>&1

echo "--- Both jlens ranks launched at $(date) ---"
echo "Model loading will take ~90 minutes, then J-lens computation begins."
echo "Output will appear at: /home/valentine${OUTPUT_DIR}/ on head node"
echo "To check progress:"
echo "  $SSH_HEAD '$HEAD' 'ls -la /home/valentine${OUTPUT_DIR}/ 2>/dev/null; docker logs --tail 5 jlens-r0'"
echo "  $SSH_WORKER '$WORKER' 'docker logs --tail 5 jlens-r1'"
