#!/bin/bash
# Run all baseline comparisons with 3 seeds each.
# Results land in logs/ and checkpoints/.

set -e
ENVS=("FetchPickAndPlace-v4" "FetchPush-v4" "FetchSlide-v4")
SEEDS=(42 123 999)

for env in "${ENVS[@]}"; do
  for seed in "${SEEDS[@]}"; do
    ENV_SLUG=$(echo $env | tr '[:upper:]' '[:lower:]' | tr '/' '-')

    # Uniform replay (baseline)
    python train.py --config configs/uniform.yaml \
      env.name=$env training.seed=$seed \
      logging.run_name=uniform_${ENV_SLUG}_seed${seed} &

    # TD-error PER (baseline)
    python train.py --config configs/per.yaml \
      env.name=$env training.seed=$seed \
      logging.run_name=per_${ENV_SLUG}_seed${seed} &

    # Semantic PER (ours)
    python train.py --config configs/semantic_per.yaml \
      env.name=$env training.seed=$seed \
      logging.run_name=semantic_per_${ENV_SLUG}_seed${seed} &

    wait  # one env-seed triple at a time; remove 'wait' for full parallelism
  done
done

echo "All runs complete."
