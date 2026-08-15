#!/bin/bash
# sync_to_github.sh — Sync latest research findings to GitHub site repo.
# Run every 4 hours (or manually). Designed to be called by the 30-min cron
# when 4 hours have elapsed since last sync.
set -e

SITE_DIR="/tmp/dsv4-reap-site"
RESEARCH_DIR="/Users/sero/research/deepseek-v4-flash-0731"
REPO_URL="https://github.com/0xSero/dsv4-reap-routing.git"
LAST_SYNC_FILE="/tmp/last_github_sync"
MIN_INTERVAL=14400  # 4 hours in seconds

# Check if 4 hours have passed since last sync
if [ -f "$LAST_SYNC_FILE" ]; then
    last=$(cat "$LAST_SYNC_FILE")
    now=$(date +%s)
    elapsed=$((now - last))
    if [ "$elapsed" -lt "$MIN_INTERVAL" ]; then
        echo "Last sync was ${elapsed}s ago, need ${MIN_INTERVAL}s. Skipping."
        exit 0
    fi
fi

# Clone or pull site repo
if [ ! -d "$SITE_DIR" ]; then
    git clone "$REPO_URL" "$SITE_DIR"
else
    cd "$SITE_DIR"
    git pull --rebase || true
fi

cd "$SITE_DIR"

CHANGES=0

# 1. Copy analysis files
if [ -d "$RESEARCH_DIR/analysis_all" ]; then
    for f in "$RESEARCH_DIR"/analysis_all/*; do
        bn=$(basename "$f")
        if [ ! -f "analysis_all/$bn" ] || ! diff -q "$f" "analysis_all/$bn" > /dev/null 2>&1; then
            cp "$f" "analysis_all/$bn"
            CHANGES=$((CHANGES + 1))
        fi
    done
fi

# 2. Copy J-lens data (gzip if needed)
if [ -d "$RESEARCH_DIR/jlens_output" ]; then
    mkdir -p jlens
    for f in "$RESEARCH_DIR"/jlens_output/*.jsonl; do
        bn=$(basename "$f")
        gz="jlens/${bn}.gz"
        if [ ! -f "$gz" ] || [ "$f" -nt "$gz" ]; then
            gzip -c "$f" > "$gz"
            CHANGES=$((CHANGES + 1))
        fi
    done
fi

# 3. Copy sanitized code files (check for credentials first)
mkdir -p code
for py in observe_religious.py run_jlens.py jlens_dsv4.py analyze_experts.py generate_report.py prepare_corpus.py scrape_christian.py prepare_christian_corpus.py prepare_theology_corpus.py scrape_wikipedia.py stream_to_hf.py; do
    if [ -f "$RESEARCH_DIR/$py" ]; then
        # Sanitize: check for credentials
        if grep -q 'REDACTED' "$RESEARCH_DIR/$py" 2>/dev/null; then
            sed "s/$SSHPASS_ENV/\$SSHPASS_ENV/g" "$RESEARCH_DIR/$py" > "code/$py"
        else
            cp "$RESEARCH_DIR/$py" "code/$py"
        fi
        CHANGES=$((CHANGES + 1))
    fi
done
for sh in run_full_observation.sh run_christian_observation.sh run_jlens_tp2.sh jlens_watch.sh obs_christian_watch.sh chain_next_runs.sh finalize_christian.sh sync_to_github.sh; do
    if [ -f "$RESEARCH_DIR/$sh" ]; then
        if grep -q 'REDACTED' "$RESEARCH_DIR/$sh" 2>/dev/null; then
            sed "s/$SSHPASS_ENV/\$SSHPASS_ENV/g" "$RESEARCH_DIR/$sh" > "code/$sh"
        else
            cp "$RESEARCH_DIR/$sh" "code/$sh"
        fi
        CHANGES=$((CHANGES + 1))
    fi
done

# 4. Copy corpus manifests
if [ -d "$RESEARCH_DIR/corpus/samples" ]; then
    mkdir -p corpus_manifests
    for f in "$RESEARCH_DIR"/corpus/samples/*.manifest.json; do
        bn=$(basename "$f")
        if [ ! -f "corpus_manifests/$bn" ] || ! diff -q "$f" "corpus_manifests/$bn" > /dev/null 2>&1; then
            cp "$f" "corpus_manifests/$bn"
            CHANGES=$((CHANGES + 1))
        fi
    done
fi

# 5. Copy EXPERIMENTS.md as a new wiki page
if [ -f "$RESEARCH_DIR/EXPERIMENTS.md" ]; then
    cp "$RESEARCH_DIR/EXPERIMENTS.md" "EXPERIMENTS.md"
    CHANGES=$((CHANGES + 1))
fi

# 6. Commit and push if there are changes
if [ "$CHANGES" -gt 0 ]; then
    git add -A
    git commit -m "Auto-sync: $CHANGES files updated $(date -u +%Y-%m-%dT%H:%MZ)"
    git push
    echo "Pushed $CHANGES changes to GitHub"
else
    echo "No changes to sync"
fi

# 7. Record sync time
date +%s > "$LAST_SYNC_FILE"

# 8. Verify site is live
HTTP_CODE=$(curl -sI "https://0xsero.github.io/dsv4-reap-routing/" 2>/dev/null | head -1 | awk '{print $2}')
echo "Site status: $HTTP_CODE"
