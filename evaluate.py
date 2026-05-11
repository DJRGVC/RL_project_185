"""
Evaluation script — load a checkpoint and report success rate + episode returns.

Usage:
    python evaluate.py --checkpoint checkpoints/semantic_per/best \
                       --config configs/semantic_per.yaml \
                       --episodes 100
"""
import argparse
import numpy as np
import yaml

from train import load_config, evaluate
from src.agents import SAC
from src.envs.wrappers import make_env


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True, help="Checkpoint directory (contains sac.pt)")
    parser.add_argument("--config",     required=True, help="Config file used during training")
    parser.add_argument("--episodes",   type=int, default=100)
    parser.add_argument("--seed",       type=int, default=42)
    args, overrides = parser.parse_known_args()

    cfg = load_config(args.config, overrides)

    env_name  = cfg["env"]["name"]
    max_steps = cfg["env"]["max_episode_steps"]
    sac_cfg   = cfg["sac"]

    env = make_env(env_name, max_episode_steps=max_steps, capture_frames=False)
    obs_dim    = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]
    action_scale = float(env.action_space.high[0])
    env.close()

    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"

    agent = SAC(
        obs_dim=obs_dim, action_dim=action_dim, action_scale=action_scale,
        hidden_dim=sac_cfg["hidden_dim"], device=device,
    )
    agent.load(args.checkpoint)

    results = evaluate(agent, env_name, args.episodes, max_steps, args.seed)

    print(f"\n=== Evaluation Results ({args.episodes} episodes) ===")
    print(f"  Success rate : {results['success_rate']:.3f}")
    print(f"  Mean return  : {results['mean_return']:.3f} ± {results['std_return']:.3f}")


if __name__ == "__main__":
    main()
