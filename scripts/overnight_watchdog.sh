#!/usr/bin/env bash
# Overnight watchdog: restarts orchestrator if dead, runs pivot logic at 03:00,
# alerts if W&B logging stalls. Independent of any LLM session.
#
# Launch: nohup ~/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/scripts/overnight_watchdog.sh \
#          > ~/.local/state/overnight_watchdog.log 2>&1 &
# Stop:   pkill -f overnight_watchdog.sh
set -uo pipefail

REPO="/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185"
STATE_DIR="$HOME/.local/state"
mkdir -p "$STATE_DIR"
LOG="$STATE_DIR/overnight_watchdog.log"
PIVOT_FLAG="$STATE_DIR/path_c_pivot_to_a.flag"
ORCH_LOG="$STATE_DIR/path_c_orchestrator.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
}

# Activate venv and source keys for any python we call
source_env() {
    cd "$REPO"
    source .venv/bin/activate
    [ -r "$HOME/.openai_key" ] && export OPENAI_API_KEY="$(cat "$HOME/.openai_key")"
    [ -r "$HOME/.anthropic_key" ] && export ANTHROPIC_API_KEY="$(cat "$HOME/.anthropic_key")"
}

restart_orchestrator() {
    log "ORCHESTRATOR DEAD — restarting"
    cd "$REPO"
    source_env
    if [ -f scripts/path_c_orchestrator.py ]; then
        nohup python scripts/path_c_orchestrator.py >> "$ORCH_LOG" 2>&1 &
        log "orchestrator restarted as pid $!"
    else
        log "ERROR: scripts/path_c_orchestrator.py does not exist; cannot restart"
        echo "ORCHESTRATOR SCRIPT MISSING at $(date)" > "$REPO/agent_reports/_orchestrator_DEAD.md"
    fi
}

check_orchestrator() {
    # Returns 0 if alive, nonzero if dead
    pgrep -f "python.*path_c_orchestrator" >/dev/null 2>&1
}

check_wandb_alive() {
    # Returns 0 if at least one new run logged in last 90 min, nonzero otherwise
    source_env
    python3 -c "
import wandb, datetime, sys
try:
    api = wandb.Api()
    runs = api.runs('d-grant-uc-berkeley/RL_project',
                    filters={'tags': {'\$in': ['path_c_overnight_2026-05-11']}},
                    per_page=200)
    now = datetime.datetime.utcnow()
    recent = [r for r in runs if (now - datetime.datetime.fromisoformat(r.created_at.replace('Z',''))).total_seconds() < 5400]
    sys.exit(0 if len(recent) > 0 else 1)
except Exception as e:
    print(f'wandb check failed: {e}', file=sys.stderr)
    sys.exit(2)
"
}

run_pivot_check() {
    # At 03:00 AM, check if Oracle-CF is beating HER by 0.1. If not, write pivot flag.
    log "Running 03:00 pivot check"
    source_env
    python3 - <<'PY' 2>&1 | tee -a "$LOG"
import wandb, sys, os
try:
    api = wandb.Api()
    runs = list(api.runs('d-grant-uc-berkeley/RL_project',
                         filters={'tags': {'$in': ['path_c_overnight_2026-05-11']}},
                         per_page=200))
    # Group by method
    # Real Path C run names on W&B (from agent_reports/overnight_path_c_plan.json):
    #   HER:        path_c_kill_her_<env>_s<seed>_seed<seed>
    #   Oracle-CF:  path_c_kill_ocf_<env>_s<seed>_seed<seed>
    # Prior filters used 'path_c_kill_her_oracle' / 'oracle_cf' substrings which
    # never matched any run name → oracle_runs == [] → oracle_mean = 0.000 →
    # pivot triggered for the wrong stated reason. Documented in
    # agent_reports/_PATH_A_RELAUNCH_HANDOFF.md (Issue 3).
    her_runs = [r for r in runs if 'path_c_kill_her_' in (r.name or '')]
    oracle_runs = [r for r in runs if 'path_c_kill_ocf_' in (r.name or '')]
    def final_succ(r):
        try:
            return float(r.summary.get('eval/success_rate', r.summary.get('charts/eval/success_rate', 0.0)))
        except Exception:
            return 0.0
    her_mean = sum(map(final_succ, her_runs)) / max(len(her_runs), 1)
    oracle_mean = sum(map(final_succ, oracle_runs)) / max(len(oracle_runs), 1)
    delta = oracle_mean - her_mean
    print(f"HER mean={her_mean:.3f} (n={len(her_runs)})  Oracle-CF mean={oracle_mean:.3f} (n={len(oracle_runs)})  delta={delta:+.3f}")
    if delta < 0.10:
        print("PIVOT: Oracle-CF does not beat HER by 0.10. Writing pivot flag.")
        with open(os.path.expanduser('~/.local/state/path_c_pivot_to_a.flag'), 'w') as f:
            f.write(f"pivot_to_path_a\nher_mean={her_mean}\noracle_mean={oracle_mean}\ndelta={delta}\n")
        sys.exit(1)
    else:
        print("COMMIT: Oracle-CF passes kill criterion. Path C continues.")
        sys.exit(0)
except Exception as e:
    print(f"pivot check error: {e}")
    sys.exit(2)
PY
    if [ -f "$PIVOT_FLAG" ]; then
        log "Pivot flag written — launching Path A bidirectional runs as fallback"
        launch_path_a_pivot
    fi
}

launch_path_a_pivot() {
    cd "$REPO"
    source_env
    # Path A pivot: launch bidirectional buffer runs (A2's deliverable) locally
    # so we have SOMETHING by morning. Modal can pick up tomorrow.
    log "Launching Path A bidirectional runs (3 envs x 2 seeds locally)"
    for env in FetchPush-v4 FetchPickAndPlace-v4 FetchSlide-v4; do
        for seed in 42 123; do
            local_name="path_a_pivot_bidir_${env}_seed${seed}"
            log "  spawning $local_name"
            WANDB_TAGS="path_a_pivot_2026-05-12,bidir" \
            nohup python train.py \
                --config configs/bidir.yaml \
                --env "$env" --seed "$seed" \
                --total_steps 300000 \
                --run_name "$local_name" \
                >> "$STATE_DIR/path_a_pivot_${env}_seed${seed}.log" 2>&1 &
            sleep 5  # stagger
        done
    done
}

# Track when we last saw a wandb update — used for "stalled" alerts
LAST_WANDB_OK=$(date +%s)
PIVOT_DONE=false
PHASE2_DONE=false
PHASE2_FLAG="$STATE_DIR/phase2_launched.flag"
[ -f "$PHASE2_FLAG" ] && PHASE2_DONE=true

check_modal_free() {
    # Returns 0 (free) if A1's HER sweep has zero running containers AND no Path C Modal jobs are running yet
    source_env
    local a1_running=$(modal app list 2>/dev/null | grep -E 'semantic-per.*ephemeral.*running|semantic-per.*detached' | wc -l)
    local pathc_running=$(modal app list 2>/dev/null | grep -E 'path-c|path_c' | grep -E 'running|ephemeral' | wc -l)
    # consider free if A1 done AND no pathc already running
    [ "$a1_running" -eq 0 ] && [ "$pathc_running" -eq 0 ]
}

launch_phase2() {
    log "Modal free — launching Phase 2 (path_c VLM-CF + verified-CF on Modal)"
    cd "$REPO"
    source_env
    if [ -f modal_app.py ] && grep -q run_path_c_phase2 modal_app.py; then
        nohup modal run --detach modal_app.py::run_path_c_phase2 \
            > "$STATE_DIR/phase2_modal_launch.log" 2>&1 &
        sleep 30  # let modal cli return
        touch "$PHASE2_FLAG"
        log "Phase 2 launched, flag written"
    else
        log "ERROR: modal_app.py missing or run_path_c_phase2 not present; Phase 2 not launched"
        echo "PHASE2 LAUNCH FAILED at $(date) — modal_app.py issue" > "$REPO/agent_reports/_phase2_LAUNCH_FAILED.md"
    fi
}

log "Watchdog starting (pid $$). Phase2 status: launched=$PHASE2_DONE"

while true; do
    # 1. Orchestrator alive? Only attempt restart if it was previously running
    # (orchestrator log exists and is non-empty — proves at least one prior launch)
    if ! check_orchestrator; then
        if [ -s "$ORCH_LOG" ]; then
            log "orchestrator died (log non-empty, prior launch confirmed) — restarting"
            restart_orchestrator
        else
            log "orchestrator not yet launched by PATHC-LEAD; watchdog standing by"
        fi
    fi

    # 2. W&B logging alive?
    if check_wandb_alive; then
        LAST_WANDB_OK=$(date +%s)
    else
        STALL=$(( ($(date +%s) - LAST_WANDB_OK) / 60 ))
        if [ "$STALL" -gt 90 ]; then
            log "W&B has not logged in ${STALL} minutes"
            echo "WANDB STALLED ${STALL}m at $(date)" > "$REPO/agent_reports/_wandb_STALLED.md"
        fi
    fi

    # 3. At/after 03:00 PDT (May 12), run pivot check once
    HOUR=$(date +%H)
    DAY=$(date +%d)
    if [ "$PIVOT_DONE" = false ] && [ "$DAY" = "12" ] && [ "$HOUR" -ge "03" ]; then
        run_pivot_check
        PIVOT_DONE=true
    fi

    # 4. Try to launch Phase 2 if Modal is free and Phase 2 hasn't been launched yet
    if [ "$PHASE2_DONE" = false ]; then
        if check_modal_free; then
            log "Modal availability check: PASS — proceeding to launch Phase 2"
            launch_phase2
            PHASE2_DONE=true
        fi
    fi

    sleep 300  # check every 5 min
done
