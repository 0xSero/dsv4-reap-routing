#!/usr/bin/env bash
# Chain: wait for wave-1 Christian obs (1267) -> resume J-lens -> wave-2 obs.
# Polls every 15 min; each stage is resume-safe, so interruption is harmless.
cd /Users/sero/research/deepseek-v4-flash-0731
export SSHPASS='$SSHPASS_ENV'
SSH="sshpass -e ssh -o ConnectTimeout=20 -o PubkeyAuthentication=no -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node -J valentine@192.168.1.96 valentine@10.0.1.1"
log(){ echo "[$(date +%m%d-%H:%M)] $*" >> /tmp/chain_runs.log; }

# Stage 1: wait for wave-1 (obs_christian_watch.sh relaunches it; exit when done)
while true; do
  sleep 900
  N=$($SSH 'wc -l < /home/valentine/obs-religious/christian_obs.jsonl 2>/dev/null || echo 0' 2>/dev/null)
  [ -z "$N" ] && { log "auth fail"; continue; }
  log "wave1 $N/1267"
  [ "$N" -ge 1267 ] && break
done
pkill -f obs_christian_watch.sh 2>/dev/null
log "wave1 COMPLETE"

# Stage 2: J-lens (resume-desync fixed; watchdog relaunches on NCCL death)
nohup ./jlens_watch.sh >> /tmp/jlens_watch.log 2>&1 &
log "jlens watchdog restarted"
while true; do
  sleep 900
  DONE=$($SSH 'docker logs jlens-r0 2>&1 | grep -c all_done' 2>/dev/null)
  [ -z "$DONE" ] && { log "auth fail"; continue; }
  N=$($SSH 'cat /home/valentine/obs-religious/jlens_output/*_jlens.jsonl 2>/dev/null | wc -l' 2>/dev/null)
  log "jlens done_flag=$DONE samples=${N:-0}/80"
  [ "${DONE:-0}" -ge 1 ] && break
done
pkill -f jlens_watch.sh 2>/dev/null
log "jlens COMPLETE — copying output"
sshpass -e scp -o ConnectTimeout=20 -o PubkeyAuthentication=no -o StrictHostKeyChecking=no \
  -o IdentitiesOnly=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node \
  -J valentine@192.168.1.96 \
  'valentine@10.0.1.1:/home/valentine/obs-religious/jlens_output/*.jsonl' jlens_output/ 2>>/tmp/chain_runs.log
mkdir -p jlens_output
log "jlens output copied to Mac"

# Stage 3: wave-2 Christian obs
export OBS_INPUT="/obs-religious/christian2_sel.jsonl"
export OBS_OUTPUT="/obs-religious/christian2_obs.jsonl"
export OBS_LOCAL_CORPUS="$PWD/corpus/samples/christian2_sel.jsonl"
bash run_full_observation.sh --no-sidecar >> /tmp/chain_runs.log 2>&1
log "wave2 launched"

# Stage 3 watchdog
while true; do
  sleep 900
  OUT=$($SSH 'docker ps -a --format "{{.Names}} {{.Status}}" | grep obs-r0; n=$(wc -l < /home/valentine/obs-religious/christian2_obs.jsonl 2>/dev/null || echo 0); echo "records $n"' 2>/dev/null)
  [ -z "$OUT" ] && { log "auth fail"; continue; }
  RUNNING=$(echo "$OUT" | head -1 | grep -c "Up")
  RECORDS=$(echo "$OUT" | sed -n 2p | awk '{print $2}')
  log "wave2 running=$RUNNING ${RECORDS:-0}/2295"
  if [ "${RECORDS:-0}" -ge 2295 ]; then log "wave2 COMPLETE"; break; fi
  if [ "$RUNNING" = "0" ]; then
    log "wave2 dead — relaunching"
    bash run_full_observation.sh --no-sidecar >> /tmp/chain_runs.log 2>&1
  fi
done
log "ALL RUNS COMPLETE"
