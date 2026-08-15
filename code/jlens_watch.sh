#!/usr/bin/env bash
# Single slow poller (15 min) to respect de5c auth rate-limiting.
cd /Users/sero/research/deepseek-v4-flash-0731
export SSHPASS='$SSHPASS_ENV'
SSH="sshpass -e ssh -o ConnectTimeout=20 -o PubkeyAuthentication=no -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node -J valentine@192.168.1.96 valentine@10.0.1.1"
while true; do
  sleep 900
  OUT=$($SSH 'docker ps -a --format "{{.Names}} {{.Status}}" | grep jlens-r0; docker logs jlens-r0 2>&1 | grep -c all_done; ls /home/valentine/obs-religious/jlens_output/*.jsonl 2>/dev/null | wc -l; for f in /home/valentine/obs-religious/jlens_output/*.jsonl; do wc -l < $f; done' 2>/dev/null)
  if [ -z "$OUT" ]; then echo "[$(date +%H:%M)] auth failed, waiting" >> /tmp/jlens_watch.log; continue; fi
  RUNNING=$(echo "$OUT" | head -1 | grep -c "Up")
  ALLDONE=$(echo "$OUT" | sed -n 2p)
  echo "[$(date +%H:%M)] running=$RUNNING alldone=$ALLDONE :: $(echo "$OUT" | tail -n +3 | tr '\n' ' ')" >> /tmp/jlens_watch.log
  if [ "$ALLDONE" != "0" ]; then echo COMPLETE >> /tmp/jlens_watch.log; exit 0; fi
  if [ "$RUNNING" = "0" ]; then
    echo "[$(date +%H:%M)] dead — relaunching" >> /tmp/jlens_watch.log
    bash run_jlens_tp2.sh >> /tmp/jlens_watch.log 2>&1
    sleep 900
  fi
done
