"""
C1v2 — Collect failed eval episodes from a partially-trained SAC policy.

Loads the locally-trained `c1v2_real_data_her*` checkpoint, runs deterministic
eval rollouts, and pickles each failed episode (frames, achieved_goal
trajectory, desired_goal, etc.) so we can later run the VLM counterfactual
prompts on the same episodes across all (variant, provider) combinations.

Usage:
    MUJOCO_GL=egl python scripts/collect_real_failed_episodes.py \
        --checkpoint checkpoints/c1v2_real_data_her/final \
        --env_name FetchPickAndPlace-v4 \
        --n_episodes 6 \
        --out_path agent_reports/c1v2_real_episodes_pickandplace.pkl

Output schema (pickle, List[Dict]):
    {
        "env_name": str,
        "seed": int,
        "frames": List[np.ndarray],   # T+1 frames including reset frame
        "achieved_goals": List[np.ndarray],  # T+1 achieved_goal vectors
        "desired_goal": np.ndarray,   # constant per episode
        "episode_length": int,        # T (number of step transitions)
        "success": False,
        "final_dist": float,
        "checkpoint": str,
    }
"""
from __future__ import annotations

import argparse
import logging
import os
import pickle
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("MUJOCO_GL", "egl")

from src.envs.wrappers import make_env  # noqa: E402
from src.agents import SAC               # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("collect_real_failed_episodes")


def load_agent(checkpoint: str, env_name: str, max_episode_steps: int = 50):
    env = make_env(env_name, max_episode_steps=max_episode_steps,
                   render_mode="rgb_array", capture_frames=True)
    obs_dim = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]
    action_scale = float(env.action_space.high[0])
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    agent = SAC(
        obs_dim=obs_dim, action_dim=action_dim, action_scale=action_scale,
        hidden_dim=256, device=device,
    )
    agent.load(checkpoint)
    return agent, env


def collect_failed(
    checkpoint: str,
    env_name: str,
    n_episodes: int,
    max_attempts: int = 60,
    seed_base: int = 50000,
    stochastic: bool = True,
    max_episode_steps: int = 50,
) -> List[Dict[str, Any]]:
    """Roll out a partially-trained SAC policy and return up to n_episodes
    failed (non-success) episodes."""
    agent, env = load_agent(checkpoint, env_name, max_episode_steps=max_episode_steps)
    flat_env = env.env if hasattr(env, "env") else env
    goal_dim = flat_env.goal_dim
    obs_dim_base = flat_env.obs_dim

    out: List[Dict[str, Any]] = []
    attempts = 0
    while len(out) < n_episodes and attempts < max_attempts:
        ep_seed = int(seed_base + 17 * attempts)
        obs, _ = env.reset(seed=ep_seed)
        achieved_goals = [obs[obs_dim_base : obs_dim_base + goal_dim].copy()]
        desired_goal = obs[obs_dim_base + goal_dim :].copy()
        done = False
        steps = 0
        success = False
        while not done:
            # `deterministic=False` is a touch more diverse — generates richer
            # failure modes than the policy's pure mode.
            action = agent.select_action(obs, deterministic=not stochastic)
            obs, _r, term, trunc, info = env.step(action)
            achieved_goals.append(obs[obs_dim_base : obs_dim_base + goal_dim].copy())
            done = term or trunc
            steps += 1
            if info.get("is_success", 0):
                success = True

        attempts += 1
        if success:
            logger.info(f"  attempt {attempts}: episode succeeded — skip.")
            continue
        frames = list(env.episode_frames)
        if len(frames) < 5:
            logger.warning(f"  attempt {attempts}: only {len(frames)} frames — skip.")
            continue

        final_dist = float(np.linalg.norm(achieved_goals[-1] - desired_goal))
        out.append({
            "env_name": env_name,
            "seed": ep_seed,
            "frames": frames,
            "achieved_goals": achieved_goals,
            "desired_goal": desired_goal,
            "episode_length": steps,
            "success": False,
            "final_dist": final_dist,
            "checkpoint": checkpoint,
        })
        logger.info(
            f"  attempt {attempts}: FAILED episode collected "
            f"(seed={ep_seed}, steps={steps}, frames={len(frames)}, "
            f"final_dist={final_dist:.3f} m)"
        )
    env.close()
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--env_name", required=True)
    parser.add_argument("--n_episodes", type=int, default=6)
    parser.add_argument("--seed_base", type=int, default=50000)
    parser.add_argument("--max_attempts", type=int, default=60)
    parser.add_argument("--out_path", required=True)
    parser.add_argument("--stochastic", action="store_true",
                        help="Use stochastic (mean+noise) policy actions "
                             "for more diverse failure modes.")
    args = parser.parse_args()

    out_path = Path(args.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading {args.checkpoint} on {args.env_name}")
    eps = collect_failed(
        checkpoint=args.checkpoint,
        env_name=args.env_name,
        n_episodes=args.n_episodes,
        max_attempts=args.max_attempts,
        seed_base=args.seed_base,
        stochastic=args.stochastic,
    )
    logger.info(f"Collected {len(eps)} failed episodes")

    with open(out_path, "wb") as f:
        pickle.dump(eps, f)
    logger.info(f"Wrote {out_path}  ({out_path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
