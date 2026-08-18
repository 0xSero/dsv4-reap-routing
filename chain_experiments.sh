#!/usr/bin/env bash
# Chain: wait for Exp 4b to finish -> launch Exp 1 -> launch Exp 12.
# Polls every 5 min; each stage is resume-safe (observe_religious.py skips
# completed records via completed_keys()). If a run dies (NCCL timeout),
# relaunch it with the increased timeout.
cd /Users/sero/research/deepseek-v4-flash-0731
if [ -z "${SSHPASS:-}" ]; then echo 'ERROR: set SSHPASS env var' >&2; exit 1; fi
SSH="sshpass -e ssh -o ConnectTimeout=20 -o PubkeyAuthentication=no -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node -J valentine@192.168.1.96 valentine@10.0.1.1"
log(){ echo "[$(date +%m%d-%H:%M)] $*" >> /tmp/chain_exp.log; }

relaunch() {
  local input="$1" output="$2" name="$3"
  log "relaunching $name (input=$input output=$output)"
  OBS_INPUT="$input" OBS_OUTPUT="$output" OBS_LOCAL_CORPUS="" \
    bash run_full_observation.sh --no-sidecar >> /tmp/chain_exp.log 2>&1
}

wait_for_completion() {
  local output="$1" total="$2" name="$3" input="$4"
  # output is a CONTAINER path (e.g. /obs-religious/exp4b_obs.jsonl)
  # host path is /home/valentine + output
  local host_output="/home/valentine${output}"
  local dead_count=0
  while true; do
    sleep 120  # 2 min poll
    STATUS=$($SSH "docker ps --format '{{.Names}} {{.Status}}' 2>/dev/null | grep obs-r0; n=\$(wc -l < ${host_output} 2>/dev/null || echo 0); echo \"records \$n\"" 2>/dev/null)
    [ -z "$STATUS" ] && { log "$name auth fail"; continue; }
    RUNNING=$(echo "$STATUS" | head -1 | grep -c "Up")
    RECORDS=$(echo "$STATUS" | sed -n 2p | awk '{print $2}')
    log "$name running=$RUNNING ${RECORDS:-0}/${total}"
    if [ "${RECORDS:-0}" -ge "$total" ]; then log "$name COMPLETE"; return 0; fi
    if [ "$RUNNING" = "0" ]; then
      dead_count=$((dead_count + 1))
      if [ "$dead_count" -ge 2 ]; then
        log "$name dead (confirmed after 2 polls) — relaunching"
        relaunch "$input" "$output" "$name"
        dead_count=0
      else
        log "$name not running (poll $dead_count/2, waiting to confirm)"
      fi
    else
      dead_count=0
    fi
  done
}

# Stage 1: wait for Exp 4b (351 records)
log "waiting for Exp 4b (351 records)"
wait_for_completion "/obs-religious/exp4b_obs.jsonl" 351 "exp4b" "/obs-religious/exp4b_capped.jsonl"

# Stage 2: launch Exp 1 (150 records)
log "launching Exp 1 (150 records)"
OBS_INPUT="/obs-religious/exp1_translations.jsonl" \
OBS_OUTPUT="/obs-religious/exp1_obs.jsonl" \
OBS_LOCAL_CORPUS="" \
  bash run_full_observation.sh --no-sidecar >> /tmp/chain_exp.log 2>&1
wait_for_completion "/obs-religious/exp1_obs.jsonl" 150 "exp1" "/obs-religious/exp1_translations.jsonl"

# Stage 3: launch Exp 12 (222 records)
log "launching Exp 12 (222 records)"
OBS_INPUT="/obs-religious/exp12_digit_minimal_pairs.jsonl" \
OBS_OUTPUT="/obs-religious/exp12_obs.jsonl" \
OBS_LOCAL_CORPUS="" \
  bash run_full_observation.sh --no-sidecar >> /tmp/chain_exp.log 2>&1
wait_for_completion "/obs-religious/exp12_obs.jsonl" 222 "exp12" "/obs-religious/exp12_digit_minimal_pairs.jsonl"

log "ALL EXPERIMENT RUNS COMPLETE"
echo "All experiments complete. Pulling results..."

# Pull results to Mac
sshpass -e scp -o ConnectTimeout=20 -o PubkeyAuthentication=no -o StrictHostKeyChecking=no \
  -o IdentitiesOnly=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node \
  -J valentine@192.168.1.96 \
  'valentine@10.0.1.1:/home/valentine/obs-religious/exp4b_obs.jsonl' \
  /Users/sero/research/deepseek-v4-flash-0731/ 2>>/tmp/chain_exp.log
sshpass -e scp -o ConnectTimeout=20 -o PubkeyAuthentication=no -o StrictHostKeyChecking=no \
  -o IdentitiesOnly=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node \
  -J valentine@192.168.1.96 \
  'valentine@10.0.1.1:/home/valentine/obs-religious/exp1_obs.jsonl' \
  /Users/sero/research/deepseek-v4-flash-0731/ 2>>/tmp/chain_exp.log
sshpass -e scp -o ConnectTimeout=20 -o PubkeyAuthentication=no -o StrictHostKeyChecking=no \
  -o IdentitiesOnly=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node \
  -J valentine@192.168.1.96 \
  'valentine@10.0.1.1:/home/valentine/obs-religious/exp12_obs.jsonl' \
  /Users/sero/research/deepseek-v4-flash-0731/ 2>>/tmp/chain_exp.log

log "RESULTS PULLED TO MAC"
