#!/usr/bin/env bash
# launch_psweep_when_ready.sh — wait for Phase 2 attempt 5 to finish, then fire
# the VLM-CF p_counterfactual sweep (18 runs × 500k steps on Modal A10G).
#
# Trigger condition: the specific Phase 2 attempt 5 app ID
# (ap-NWsFCh9kA9P0syU9JhIBAR) has zero running tasks AND no other ephemeral
# semantic-per apps are in flight. Polls every 5 minutes.
#
# Usage (background, surviving terminal close):
#   nohup bash scripts/launch_psweep_when_ready.sh \
#     > ~/.local/state/psweep_launcher.log 2>&1 &
#   echo $! > ~/.local/state/psweep_launcher.pid
#
# After successful launch the watcher writes
# agent_reports/_PSWEEP_LAUNCHED.md with the new app ID and exits 0.
set -euo pipefail

PROJECT_ROOT="/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185"
VENV_ACTIVATE="${PROJECT_ROOT}/.venv/bin/activate"
PHASE2_APP_ID="ap-NWsFCh9kA9P0syU9JhIBAR"
POLL_SECONDS=300        # 5 minutes
TAG_FILTER="path_c_vlm_cf_psweep_2026-05-12"
LAUNCHED_MD="${PROJECT_ROOT}/agent_reports/_PSWEEP_LAUNCHED.md"
LOCK_FILE="${PROJECT_ROOT}/agent_reports/_PSWEEP_LAUNCHED.lock"

# Refuse to launch twice from the same machine
if [[ -f "${LOCK_FILE}" ]]; then
    echo "[$(date -Iseconds)] lock file present at ${LOCK_FILE}; another launcher already finished or is in flight. Exiting."
    exit 1
fi

cd "${PROJECT_ROOT}"
# shellcheck disable=SC1090
source "${VENV_ACTIVATE}"

log() { echo "[$(date -Iseconds)] $*"; }

# Returns 0 if Phase 2 is FREE (no running ephemeral semantic-per apps),
# non-zero otherwise. We use `modal app list` and check (a) that the
# specific Phase 2 app ID is not in a running/ephemeral state, and
# (b) that no *other* ephemeral semantic-per app is in flight (defensive
# against another sweep racing us for the 10-GPU cap).
is_modal_free() {
    local listing
    listing=$(modal app list 2>&1 || true)
    if [[ -z "${listing}" ]]; then
        log "modal app list returned empty output; assuming busy"
        return 1
    fi
    # Drop header/footer lines that contain "App ID" or "──" decorations.
    # Then look at rows mentioning "ephemeral" and "semantic-p" (truncated name).
    local live
    live=$(printf '%s\n' "${listing}" \
        | grep -E "ephemeral|running" \
        | grep -E "semantic-p|${PHASE2_APP_ID}" \
        || true)

    if [[ -z "${live}" ]]; then
        return 0
    fi
    log "still in flight: $(printf '%s' "${live}" | tr '\n' ';')"
    return 1
}

log "watcher starting. PID=$$  poll=${POLL_SECONDS}s  phase2=${PHASE2_APP_ID}"

attempts=0
while true; do
    attempts=$((attempts + 1))
    if is_modal_free; then
        log "Modal capacity confirmed free (attempt ${attempts}). Firing sweep…"
        break
    fi
    sleep "${POLL_SECONDS}"
done

# Belt & suspenders: poll once more after 60s to avoid racing a job that
# just queued but hasn't yet shown up in `modal app list`.
sleep 60
if ! is_modal_free; then
    log "WARNING: a new ephemeral app appeared during the 60s settle. Continuing anyway"
fi

# Mark the lock BEFORE firing so a crashing modal run can't trigger a re-fire.
touch "${LOCK_FILE}"

# Launch the sweep. Capture stdout+stderr so we can pull the new app ID.
LAUNCH_LOG="${PROJECT_ROOT}/agent_reports/_PSWEEP_LAUNCH_OUT.txt"
log "running: modal run --detach modal_app.py::run_path_c_vlm_cf_psweep"
set +e
modal run --detach modal_app.py::run_path_c_vlm_cf_psweep > "${LAUNCH_LOG}" 2>&1
launch_rc=$?
set -e
log "modal run exit code: ${launch_rc}"

# Extract the new app ID from the launch output, falling back to the first
# ap-<...> string in the log.
NEW_APP_ID=$(grep -oE 'ap-[A-Za-z0-9]+' "${LAUNCH_LOG}" | head -n 1 || true)
if [[ -z "${NEW_APP_ID}" ]]; then
    NEW_APP_ID="<unknown — see ${LAUNCH_LOG}>"
fi

# ETA estimate: 500k SAC steps on A10G ≈ 4–6 hr/run. With 10-GPU cap and 18
# runs, two waves at ~5 hr each → 10 hr total. Launched ~17:00–21:00 PDT
# windows; finish window therefore lands ~03:00–07:00 PDT next morning.
LAUNCHED_AT=$(date -Iseconds)

cat > "${LAUNCHED_MD}" <<EOF
# VLM-CF p_counterfactual sweep — LAUNCHED

- **Launched at (local):** ${LAUNCHED_AT}
- **Modal entrypoint app ID:** ${NEW_APP_ID}
- **Launcher PID (watcher):** $$
- **Phase 2 attempt 5 freed (gate):** ${PHASE2_APP_ID}
- **modal run exit code:** ${launch_rc}
- **Launch stdout/stderr:** \`${LAUNCH_LOG}\`

## Sweep grid

- Env: FetchPickAndPlace-v4
- Steps per run: 500,000 (matches Phase 2)
- p_counterfactual values: 0.00, 0.10, 0.25, 0.50, 0.75, 1.00
- Seeds: 42, 123, 999
- Total runs: **6 × 3 = 18**
- VLM: Anthropic Sonnet-4.5, achieved_goal variant, cf_call_interval=16

## Expected ETA

500k SAC steps on Modal A10G ≈ 4–6 hr/run. With the 10-GPU concurrency
cap and 18 runs, the queue plays out in roughly two waves of ~5 hr each
→ **~03:00–07:00 PDT tomorrow** (morning analyst slot).

## Expected spend

- VLM API (Sonnet 4.5, cf_call_interval=16, ~1 call / 16 failed episodes):
  $180–$270 across the 18 runs (proportional to p — p=0 burns ~$0,
  p=1.0 ≈ peak rate at $20–25/run).
- Modal A10G GPU-hours: 18 × ~5 hr × \$1.10/hr ≈ \$100.
- Combined: roughly **\$180–\$270 total** (VLM dominates; p=0 runs are
  essentially free aside from the GPU spend).

## W&B filter URL

<https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=path_c_vlm_cf_psweep_2026-05-12>

## Decision rule for tomorrow

Compute mean evaluation success rate at 500k steps across 3 seeds for
each p value, then apply:

- **If SR(p=1.0) ≥ SR(p=0.25) + 0.05** → "pure VLM-CF" wins; switch the
  Path C default away from p=0.25 hybrid and re-run the production
  configs at p=1.0. The achieved_future HER backstop is no longer
  carrying the result.
- **If peak SR lands at p ∈ {0.25, 0.50}** → HER+VLM hybrid is the right
  default; keep the current production setting. The hindsight signal
  and the imagined-goal signal are complementary.
- **If SR declines monotonically with p (0.0 > 0.10 > … > 1.0)** → HER's
  hindsight guarantee dominates; the VLM-imagined goals are net-harmful
  even at low weights. Retract the "VLM-CF helps PnP" claim from §5 of
  the paper draft.

## Generated by

\`scripts/launch_psweep_when_ready.sh\` running under nohup. See
\`~/.local/state/psweep_launcher.log\` for the full watcher trace.
EOF

log "wrote ${LAUNCHED_MD}"
log "watcher done. exiting cleanly."
exit 0
