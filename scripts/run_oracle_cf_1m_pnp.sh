#!/usr/bin/env bash
# run_oracle_cf_1m_pnp.sh — Oracle-CF re-run on FetchPickAndPlace-v4 at 1M steps.
#
# CONTEXT
#   The 2026-05-11 Path C KILL verdict at 250k steps may be premature.
#   HER on PickAndPlace needs ~500k-1M steps to converge. This re-run
#   gives an honest verdict at the published convergence horizon.
#
#   Seeds: 42, 123, 999
#   Total steps: 1,000,000 (4x the 250k kill-experiment horizon)
#
# PARALLELISM
#   RTX 5070 Ti has ~16GB VRAM. Each SAC run uses ~5GB.
#   Seeds 42 and 123 run in parallel (~10GB). Seed 999 runs after both
#   finish. Total wallclock: ~4 hr (2 batches × ~2 hr each).
#
# PROVENANCE
#   W&B tags: path_c_kill_2026-05-11,oracle_cf_1m_pnp,oracle_cf_pushfix_followup
#   Run names: path_c_kill_ocf_pnp_1m_s{42,123,999}_seed{42,123,999}
#   Logs: ~/.local/state/oracle_cf_1m_pnp_s{seed}.log
#
# Set DRY_RUN=1 to print commands without executing.

set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

source .venv/bin/activate

SEEDS=(42 123 999)
TAG_BASE="path_c_kill_2026-05-11,oracle_cf_1m_pnp,oracle_cf_pushfix_followup"
LOG_DIR="${HOME}/.local/state"

run_one () {
  local seed="$1"
  local run_name="path_c_kill_ocf_pnp_1m_s${seed}_seed${seed}"
  local logfile="${LOG_DIR}/oracle_cf_1m_pnp_s${seed}.log"
  local cmd=(
    python train.py
    --config configs/oracle_cf.yaml
    env.name=FetchPickAndPlace-v4
    training.seed="${seed}"
    training.total_steps=1000000
    training.eval_interval=10000
    training.save_interval=50000
    training.log_interval=1000
    logging.use_wandb=true
    "logging.run_name=${run_name}"
  )
  if [[ "${DRY_RUN:-0}" == "1" ]]; then
    printf 'WANDB_TAGS=%s \\\n  %s\n\n' "${TAG_BASE}" "${cmd[*]}"
  else
    echo "[oracle_cf_1m_pnp] launching seed=${seed}, log=${logfile}"
    WANDB_TAGS="${TAG_BASE}" "${cmd[@]}" > "${logfile}" 2>&1
    echo "[oracle_cf_1m_pnp] seed=${seed} finished."
  fi
}

if [[ "${DRY_RUN:-0}" == "1" ]]; then
  echo "=== DRY RUN: 3 commands that would be executed ==="
  for seed in "${SEEDS[@]}"; do
    run_one "${seed}"
  done
  echo "=== END DRY RUN ==="
  exit 0
fi

# Batch 1: seeds 42 and 123 in parallel
echo "[oracle_cf_1m_pnp] Batch 1: seeds 42 and 123 in parallel"
run_one 42 &
PID_42=$!
run_one 123 &
PID_123=$!

wait $PID_42
echo "[oracle_cf_1m_pnp] seed=42 done (PID ${PID_42})"
wait $PID_123
echo "[oracle_cf_1m_pnp] seed=123 done (PID ${PID_123})"

# Batch 2: seed 999 sequential
echo "[oracle_cf_1m_pnp] Batch 2: seed 999"
run_one 999

echo "[oracle_cf_1m_pnp] ALL DONE: 3 seeds × 1M steps on FetchPickAndPlace-v4."
echo "W&B filter: tags=path_c_kill_2026-05-11 AND tags=oracle_cf_1m_pnp"
