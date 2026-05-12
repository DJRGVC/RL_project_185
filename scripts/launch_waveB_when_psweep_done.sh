#!/usr/bin/env bash
# launch_waveB_when_psweep_done.sh — sequential firer for Wave B (B1 → B2 → B3)
#
# Waits for the VLM-CF p_counterfactual sweep (launched by
# scripts/launch_psweep_when_ready.sh) to fully drain, then fires three
# Modal entrypoints back-to-back, waiting for each to drain before the
# next launches:
#
#   B1: modal_app.py::run_path_c_waveB_her_per     (9 runs, no VLM)
#   B2: modal_app.py::run_path_c_waveB_sharony     (9 runs, Sonnet 4.5)
#   B3: modal_app.py::run_path_c_waveB_2x2         (12 runs, Sonnet 4.5)
#
# Polls every 5 minutes. State (app IDs, current wave) is persisted to
# ~/.local/state/waveB_state.json so the watcher can be killed and
# restarted without losing track. Logs to ~/.local/state/waveB_launcher.log.
#
# Usage (background, surviving terminal close):
#   nohup bash scripts/launch_waveB_when_psweep_done.sh \
#     > ~/.local/state/waveB_launcher.log 2>&1 &
#   echo $! > ~/.local/state/waveB_launcher.pid
#
# Constraints:
#   - DOES NOT touch the p-sweep watcher (PID 236126) or its lock file.
#   - DOES NOT fire if its own lock file is present (idempotent).
#   - Tags every run with the wave-specific tag for one-shot W&B filter.
set -euo pipefail

PROJECT_ROOT="/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185"
VENV_ACTIVATE="${PROJECT_ROOT}/.venv/bin/activate"
STATE_DIR="${HOME}/.local/state"
STATE_FILE="${STATE_DIR}/waveB_state.json"
LOCK_FILE="${PROJECT_ROOT}/agent_reports/_WAVE_B_LAUNCHED.lock"
LAUNCHED_MD="${PROJECT_ROOT}/agent_reports/_WAVE_B_LAUNCHED.md"
POLL_SECONDS=300        # 5 minutes

# Tag base used by the p-sweep — we detect completion by checking that no
# ephemeral semantic-per Modal app is running. (We do NOT depend on the
# p-sweep launcher writing a "done" marker — it doesn't.)
PSWEEP_TAG_BASE="path_c_vlm_cf_psweep_2026-05-12"

mkdir -p "${STATE_DIR}"

# Refuse to launch twice from the same machine.
if [[ -f "${LOCK_FILE}" ]]; then
    echo "[$(date -Iseconds)] lock file present at ${LOCK_FILE}; Wave B already fired. Exiting."
    exit 1
fi

cd "${PROJECT_ROOT}"
# shellcheck disable=SC1090
source "${VENV_ACTIVATE}"

log() { echo "[$(date -Iseconds)] $*"; }

# Returns 0 if Modal has no ephemeral semantic-per apps running.
# Matches the strict policy used by launch_psweep_when_ready.sh.
is_modal_free() {
    local listing
    listing=$(modal app list 2>&1 || true)
    if [[ -z "${listing}" ]]; then
        log "modal app list returned empty output; assuming busy"
        return 1
    fi
    local live
    live=$(printf '%s\n' "${listing}" \
        | grep -E "ephemeral|running" \
        | grep -E "semantic-p" \
        || true)
    if [[ -z "${live}" ]]; then
        return 0
    fi
    log "still in flight: $(printf '%s' "${live}" | tr '\n' ';')"
    return 1
}

# Persist a state snapshot (best-effort, JSON-ish, no jq dependency).
write_state() {
    local wave="$1"
    local app_id="$2"
    local status="$3"
    cat > "${STATE_FILE}" <<EOF
{
  "current_wave": "${wave}",
  "current_app_id": "${app_id}",
  "status": "${status}",
  "updated_at": "$(date -Iseconds)",
  "watcher_pid": $$
}
EOF
}

# Wait until Modal is free (no ephemeral semantic-p apps), then add a 60s
# settle. Used between waves AND at the very start to wait out the p-sweep.
wait_for_modal_free() {
    local label="$1"
    log "waiting for Modal to drain (${label})…"
    local attempts=0
    while true; do
        attempts=$((attempts + 1))
        if is_modal_free; then
            log "Modal free for ${label} (attempt ${attempts}). Settle 60s…"
            sleep 60
            if is_modal_free; then
                log "Modal confirmed free for ${label}."
                return 0
            fi
            log "race detected — a new app appeared during settle; resuming poll"
        fi
        sleep "${POLL_SECONDS}"
    done
}

# Fire one wave. Args: <wave-label> <modal-entrypoint>
fire_wave() {
    local wave="$1"
    local entrypoint="$2"
    local launch_log="${PROJECT_ROOT}/agent_reports/_WAVE_B_${wave}_LAUNCH_OUT.txt"

    write_state "${wave}" "" "launching"
    log "firing ${wave}: modal run --detach modal_app.py::${entrypoint}"
    set +e
    modal run --detach "modal_app.py::${entrypoint}" > "${launch_log}" 2>&1
    local rc=$?
    set -e
    log "${wave} modal run exit code: ${rc}"

    local app_id
    app_id=$(grep -oE 'ap-[A-Za-z0-9]+' "${launch_log}" | head -n 1 || true)
    if [[ -z "${app_id}" ]]; then
        app_id="<unknown — see ${launch_log}>"
    fi
    log "${wave} launched as app ${app_id}"
    write_state "${wave}" "${app_id}" "in_flight"
    echo "${app_id}"
}

log "============================================================"
log "Wave B watcher starting."
log "PID=$$  poll=${POLL_SECONDS}s  state_file=${STATE_FILE}"
log "Plan: B1 (HER+PER) → B2 (Sharony VLM-RB) → B3 (2x2 numeric)"
log "============================================================"

write_state "init" "" "waiting_for_psweep"

# ── Wait for the p-sweep to fully drain. ──────────────────────────────────────
wait_for_modal_free "p-sweep drain (pre-B1)"

# Belt & suspenders: mark the lock BEFORE firing so a crashing modal run
# can't trigger a re-fire if the watcher gets restarted.
touch "${LOCK_FILE}"

# ── B1: HER+PER ───────────────────────────────────────────────────────────────
B1_APP_ID=$(fire_wave "B1" "run_path_c_waveB_her_per")

# ── Wait for B1 to drain, then fire B2. ───────────────────────────────────────
wait_for_modal_free "B1 drain (pre-B2)"

B2_APP_ID=$(fire_wave "B2" "run_path_c_waveB_sharony")

# ── Wait for B2 to drain, then fire B3. ───────────────────────────────────────
wait_for_modal_free "B2 drain (pre-B3)"

B3_APP_ID=$(fire_wave "B3" "run_path_c_waveB_2x2")

# ── Wait for B3 to drain so the final state file shows completion. ────────────
wait_for_modal_free "B3 drain (final)"

write_state "done" "" "all_waves_completed"

LAUNCHED_AT=$(date -Iseconds)

cat > "${LAUNCHED_MD}" <<EOF
# Wave B (B1 → B2 → B3) — LAUNCHED & DRAINED

- **Completed at (local):** ${LAUNCHED_AT}
- **Watcher PID:** $$
- **State file:** \`${STATE_FILE}\`

## Modal app IDs

| Wave | Entrypoint                              | App ID         |
|------|-----------------------------------------|----------------|
| B1   | run_path_c_waveB_her_per                | ${B1_APP_ID}   |
| B2   | run_path_c_waveB_sharony                | ${B2_APP_ID}   |
| B3   | run_path_c_waveB_2x2                    | ${B3_APP_ID}   |

## W&B filter URLs

- B1: https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=path_c_her_per_2026-05-13
- B2: https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=path_c_sharony_vlmrb_2026-05-13
- B3: https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=path_c_2x2_2026-05-13

## Generated by

\`scripts/launch_waveB_when_psweep_done.sh\` running under nohup. See
\`${HOME}/.local/state/waveB_launcher.log\` for the full watcher trace.
EOF

log "wrote ${LAUNCHED_MD}"
log "watcher done. exiting cleanly."
exit 0
