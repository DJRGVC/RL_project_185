#!/usr/bin/env bash
# One-shot relaunch of the Path A bidirectional pivot runs.
#
# Why this exists:
#   scripts/overnight_watchdog.sh::launch_path_a_pivot tried to launch 6 runs at
#   03:00 PDT using an argparse-style CLI invocation (--env / --seed /
#   --total_steps / --run_name) plus configs/bidir.yaml. train.py only accepts
#   --config and treats anything else as hydra-style key.subkey=value overrides,
#   so all 6 spawns crashed with `FileNotFoundError: configs/bidir.yaml`
#   (because configs/bidir.yaml only existed on agent/a2-oracle-bidir, not on
#   the orchestrator's branch).
#
#   This script:
#     1) assumes configs/bidir.yaml and src/buffers/bidirectional_buffer.py have
#        already been brought onto agent/pathc-lead (companion commit);
#     2) launches the 6 runs sequentially in the foreground of a single
#        background process — sequential because the local RTX 5070 Ti can
#        only host one training job at a time at full throughput;
#     3) tags the runs with WANDB_TAGS=path_a_pivot_2026-05-12,bidir_relaunch
#        so they're easy to find next to the (failed) watchdog runs.
#
# Launch with:
#   nohup scripts/relaunch_path_a_pivot.sh \
#       > ~/.local/state/path_a_relaunch.log 2>&1 &
#
# Estimated wall time: 6 runs * ~70-90 min/run on the 5070 Ti = 7-9 hours.
# Even with the first run starting at ~03:35 PDT we should have 2-3 envs done
# by 09:00 PDT.

set -uo pipefail

REPO="/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185"
STATE_DIR="$HOME/.local/state"
mkdir -p "$STATE_DIR"
LOG="$STATE_DIR/path_a_relaunch.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
}

cd "$REPO"
source .venv/bin/activate
[ -r "$HOME/.openai_key" ] && export OPENAI_API_KEY="$(cat "$HOME/.openai_key")"
[ -r "$HOME/.anthropic_key" ] && export ANTHROPIC_API_KEY="$(cat "$HOME/.anthropic_key")"
# .env carries WANDB_API_KEY etc.
[ -r "$REPO/.env" ] && { set -a; source "$REPO/.env"; set +a; }

export WANDB_TAGS="path_a_pivot_2026-05-12,bidir_relaunch"

run_one() {
    local env="$1"
    local seed="$2"
    local run_name="path_a_pivot_bidir_${env}_seed${seed}"
    local out_log="$STATE_DIR/path_a_relaunch_${env}_seed${seed}.log"

    log "→ launching $run_name (logging to $out_log)"
    python train.py \
        --config configs/bidir.yaml \
        env.name="$env" \
        training.seed="$seed" \
        training.total_steps=300000 \
        training.eval_interval=10000 \
        training.eval_episodes=5 \
        training.save_interval=50000 \
        training.log_interval=2000 \
        training.warmup_steps=2000 \
        logging.run_name="$run_name" \
        > "$out_log" 2>&1
    local rc=$?
    if [ $rc -ne 0 ]; then
        log "✗ $run_name exited with code $rc — see $out_log"
    else
        log "✓ $run_name finished cleanly"
    fi
}

log "Path A bidir pivot relaunch starting (pid $$)"
log "Sequencing: FetchPush x{42,123}, FetchPickAndPlace x{42,123}, FetchSlide x{42,123}"

# Push first (fastest task, gives us a real result earliest).
for seed in 42 123; do
    run_one FetchPush-v4 "$seed"
done
for seed in 42 123; do
    run_one FetchPickAndPlace-v4 "$seed"
done
for seed in 42 123; do
    run_one FetchSlide-v4 "$seed"
done

log "Path A bidir pivot relaunch DONE"
