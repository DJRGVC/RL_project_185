#!/usr/bin/env bash
# Watcher: polls every 30s for final_project_outline.pdf to land, then signals.
REPO="/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185"
TARGET="$REPO/agent_reports/final_project_outline.pdf"
SIGNAL="$REPO/agent_reports/_OUTLINE_RECEIVED.flag"
LOG="$HOME/.local/state/outline_watcher.log"
mkdir -p "$HOME/.local/state"

echo "[$(date '+%H:%M:%S')] watcher started, polling for $TARGET" >> "$LOG"
while true; do
    if [ -f "$TARGET" ] && [ -s "$TARGET" ]; then
        SIZE=$(stat -c %s "$TARGET")
        # Wait 5 more seconds to ensure scp finished, check size stable
        sleep 5
        SIZE2=$(stat -c %s "$TARGET")
        if [ "$SIZE" = "$SIZE2" ]; then
            echo "[$(date '+%H:%M:%S')] FILE LANDED size=$SIZE bytes" >> "$LOG"
            touch "$SIGNAL"
            echo "[$(date '+%H:%M:%S')] signal flag written: $SIGNAL" >> "$LOG"
            exit 0
        fi
    fi
    sleep 30
done
