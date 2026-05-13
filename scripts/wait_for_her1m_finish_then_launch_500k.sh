#!/usr/bin/env bash
# wait_for_her1m_finish_then_launch_500k.sh
#
# Polls every 5 minutes until all HER@1M runs (training.total_steps=1000000
# python procs from train.py) have drained, then launches the matched-horizon
# HER@500k + PER@500k baseline wave on the local GPU.
#
# Detection: pgrep -f 'python.*train.*total_steps=1000000' returning empty.
# (The in-flight HER@1M and PnP@1M jobs all match this pattern.)
#
# Side effects on launch:
#   - touch agent_reports/_HER1M_DONE.flag
#   - nohup scripts/run_matched_horizon_500k.sh in background
#   - touch agent_reports/_MATCHED_500K_LAUNCHED.flag
#   - record run-script PID into agent_reports/_MATCHED_500K_LAUNCHED.pid
#
# Idempotent: refuses to fire if _MATCHED_500K_LAUNCHED.flag already exists.
#
# Usage:
#   nohup bash scripts/wait_for_her1m_finish_then_launch_500k.sh \
#     > ~/.local/state/matched_500k_launcher.log 2>&1 &
#   echo $! > ~/.local/state/matched_500k_launcher.pid
set -uo pipefail

PROJECT_ROOT="/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185"
LAUNCHED_FLAG="${PROJECT_ROOT}/agent_reports/_MATCHED_500K_LAUNCHED.flag"
DONE_HER1M_FLAG="${PROJECT_ROOT}/agent_reports/_HER1M_DONE.flag"
RUN_SCRIPT="${PROJECT_ROOT}/scripts/run_matched_horizon_500k.sh"
RUN_LOG="${HOME}/.local/state/matched_500k_run.log"
LAUNCHER_PID_FILE="${HOME}/.local/state/matched_500k_launcher.pid"
RUN_PID_FILE="${PROJECT_ROOT}/agent_reports/_MATCHED_500K_LAUNCHED.pid"

POLL_SECONDS=300
HER1M_PATTERN='python.*train.*total_steps=1000000'

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "watcher start. PID=$$"
log "  HER@1M pattern: ${HER1M_PATTERN}"
log "  will launch:    ${RUN_SCRIPT}"
log "  poll every:     ${POLL_SECONDS}s"

if [ -f "${LAUNCHED_FLAG}" ]; then
    log "FATAL: ${LAUNCHED_FLAG} already exists — refusing to fire twice."
    exit 1
fi

while true; do
    # pgrep returns 0 if anything matched, 1 if nothing matched.
    if pgrep -f "${HER1M_PATTERN}" > /dev/null 2>&1; then
        n_alive=$(pgrep -f "${HER1M_PATTERN}" | wc -l)
        log "  still ${n_alive} HER@1M proc(s) alive; sleeping ${POLL_SECONDS}s"
        sleep "${POLL_SECONDS}"
        continue
    fi
    log "  no HER@1M procs detected — confirming with a 30s grace re-check"
    sleep 30
    if pgrep -f "${HER1M_PATTERN}" > /dev/null 2>&1; then
        log "  false alarm: HER@1M procs reappeared; resuming poll"
        continue
    fi
    break
done

log "==> HER@1M wave fully drained; firing matched-horizon launcher."
touch "${DONE_HER1M_FLAG}"

cd "${PROJECT_ROOT}"
nohup bash "${RUN_SCRIPT}" > "${RUN_LOG}" 2>&1 &
RUN_PID=$!
echo "${RUN_PID}" > "${RUN_PID_FILE}"
touch "${LAUNCHED_FLAG}"

log "==> matched-horizon run script launched: PID=${RUN_PID}, log=${RUN_LOG}"
log "    flag:  ${LAUNCHED_FLAG}"
log "    pid:   ${RUN_PID_FILE}"
log "watcher exit (clean)."
