#!/usr/bin/env bash
# Post-run pipeline: run when wave-2 completes (chain supervisor logs
# "ALL RUNS COMPLETE"). Pulls all observation outputs to the Mac, runs the
# expert analysis over the combined Christian records, regenerates the
# wiki-style report, and publishes artifacts to the private HF dataset.
set -euo pipefail
cd /Users/sero/research/deepseek-v4-flash-0731
export SSHPASS='$SSHPASS_ENV'
SCP="scp -o ConnectTimeout=20 -o PubkeyAuthentication=no -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -o IdentityFile=$HOME/.ssh/dgx-spark-node -J valentine@192.168.1.96"

$SCP 'valentine@10.0.1.1:/home/valentine/obs-religious/christian_obs.jsonl' .
$SCP 'valentine@10.0.1.1:/home/valentine/obs-religious/christian2_obs.jsonl' .
cat christian_obs.jsonl christian2_obs.jsonl > christian_all_obs.jsonl

# dedupe + fail-closed verify (category, sample_index) unique, Σfreq==seqlen*6
python3 - <<'EOF'
import json, sys
seen=set(); out=[]
bad=0
for ln in open('christian_all_obs.jsonl'):
    r=json.loads(ln); key=(r['category'], r['sample_index'])
    if key in seen: continue
    seen.add(key)
    for l in r['observation']['layers'].values():
        if sum(l['expert_frequencies'])!=r['seqlen']*6: bad+=1
    out.append(ln)
open('christian_all_obs.jsonl','w').writelines(out)
print(f"records={len(out)} dup_skipped implicit invariant_violations={bad}")
assert bad==0, "FREQ_SUM_INVARIANT_VIOLATION"
EOF

python3 analyze_experts.py --obs christian_all_obs.jsonl --out analysis_christian
python3 generate_report.py --analysis analysis/ --analysis-christian analysis_christian/ \
  --jlens jlens_output/ --obs full_obs.jsonl --html report.html 2>&1 | tail -3 || \
python3 generate_report.py --analysis analysis/ --jlens jlens_output/ --obs full_obs.jsonl --html report.html | tail -3

python3 stream_to_hf.py --help >/dev/null 2>&1 && \
  python3 - <<'EOF'
from huggingface_hub import HfApi
api = HfApi()
for f in ["christian_obs.jsonl", "christian2_obs.jsonl"]:
    api.upload_file(path_or_fileobj=f, path_in_repo=f"christian/{f}",
                    repo_id="0xSero/deepseek-v4-flash-religious-reap-observations",
                    repo_type="dataset")
print("HF upload done")
EOF
echo "FINALIZE COMPLETE"
