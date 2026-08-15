#!/usr/bin/env bash
# Watchdog v2 for the Christian observation runs. Polls the WORKER container
# every 5 min via key-auth SSH (no de5c rate-limit exposure); both ranks die
# together on NCCL stall, so obs-r1 status is a full proxy. Record counts via
# de5c only every 30 min. Relaunch is resume-safe (run_full_observation.sh).
# Env: WAVES="1267:/obs-religious/christian_obs.jsonl 2295:/obs-religious/christian2_obs.jsonl"
cd /Users/sero/research/deepseek-v4-flash-0731
export SSHPASS='$SSHPASS_ENV'
SSH_WORKER="ssh -o ConnectTimeout=20 -o BatchMode=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node -o IdentitiesOnly=yes -o StrictHostKeyChecking=no root@192.168.1.96"
SSH_HEAD="sshpass -e ssh -o ConnectTimeout=20 -o PubkeyAuthentication=no -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node -J valentine@192.168.1.96 valentine@10.0.1.1"
LOG=/tmp/obs_christian_watch.log
TARGET=${TARGET_RECORDS:-1267}
OUTPUT_REMOTE=${TARGET_FILE:-/obs-religious/christian_obs.jsonl}
i=0
while true; do
  sleep 300
  UP=$($SSH_WORKER 'docker ps --format "{{.Names}} {{.Status}}" | grep -c "obs-r1 Up"' 2>/dev/null)
  [ -z "$UP" ] && { echo "[$(date +%H:%M)] worker ssh failed" >> $LOG; continue; }
  i=$((i+1))
  if [ $((i % 6)) -eq 0 ]; then
    N=$($SSH_HEAD "wc -l < /home/valentine${OUTPUT_REMOTE} 2>/dev/null || echo 0" 2>/dev/null)
    echo "[$(date +%H:%M)] up=$UP ${N:-?}/${TARGET}" >> $LOG
    [ -n "$N" ] && [ "$N" -ge "$TARGET" ] && { echo COMPLETE >> $LOG; exit 0; }
  else
    echo "[$(date +%H:%M)] up=$UP" >> $LOG
  fi
  if [ "$UP" = "0" ]; then
    echo "[$(date +%H:%M)] dead — relaunching" >> $LOG
    if [ -n "${WAVE2:-}" ]; then
      OBS_INPUT="/obs-religious/christian2_sel.jsonl" OBS_OUTPUT="/obs-religious/christian2_obs.jsonl" \
        OBS_LOCAL_CORPUS="$PWD/corpus/samples/christian2_sel.jsonl" \
        bash run_full_observation.sh --no-sidecar >> $LOG 2>&1
    else
      bash run_christian_observation.sh >> $LOG 2>&1
    fi
  fi
done
