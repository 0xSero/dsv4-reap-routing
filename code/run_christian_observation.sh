#!/usr/bin/env bash
# Launch the Christian-corpus observation run (first window per Gutenberg book,
# 1267 samples / ~20.4M tokens ≈ 28h at ~200 tok/s). Resume-safe: reruns skip
# completed records. Uses the proven run_full_observation.sh orchestration.
#
# IMPORTANT: only run when the J-lens containers are NOT active (same nodes).
set -euo pipefail
cd "$(dirname "$0")"
export OBS_INPUT="/obs-religious/christian_sel.jsonl"
export OBS_OUTPUT="/obs-religious/christian_obs.jsonl"
export OBS_LOCAL_CORPUS="$PWD/corpus/samples/christian_sel.jsonl"
exec bash run_full_observation.sh --no-sidecar
