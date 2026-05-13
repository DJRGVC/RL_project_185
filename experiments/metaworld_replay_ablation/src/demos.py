"""Collect expert demos via MetaWorld's scripted policies.

One demo = one episode rolled out with the scripted policy (at configurable
action-noise). Returns a flat list of transitions ready for buffer.add().
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass

import numpy as np

from src import env as env_mod
from src.config import DemosCfg, EnvCfg

log = logging.getLogger(__name__)


@dataclass
class Transition:
    obs: np.ndarray
    action: np.ndarray
    reward: float
    next_obs: np.ndarray
    done: bool


def collect(task: str, sparse_reward: bool, cfg: DemosCfg, env_cfg: EnvCfg,
            seed: int) -> tuple[list[Transition], dict]:
    """Roll out ``cfg.episodes_per_task`` expert episodes for ``task``.

    Returns ``(transitions, stats)`` where stats describes success rate /
    counts / mean return for sanity-checking the demos themselves.
    """
    env, train_tasks = env_mod.make_env(task, seed, env_cfg.max_episode_steps,
                                         camera_name=env_cfg.camera_name)
    policy = env_mod.make_policy(task)
    rng_py = random.Random(seed)
    rng_np = np.random.default_rng(seed)
    act_low = env.action_space.low.astype(np.float32)
    act_high = env.action_space.high.astype(np.float32)

    transitions: list[Transition] = []
    n_success = 0
    returns: list[float] = []

    for ep in range(cfg.episodes_per_task):
        obs, _ = env_mod.reset_with_task(env, train_tasks, rng_py)
        ep_return = 0.0
        ep_success = False
        for _ in range(env_cfg.max_episode_steps):
            scripted = policy.get_action(obs).astype(np.float32)
            action = env_mod.noisy_action(scripted, rng_np, cfg.noise, act_low, act_high)
            next_obs, reward, terminated, truncated, info = env.step(action)
            next_obs = np.asarray(next_obs, dtype=np.float32)
            success = bool(info.get("success", False))
            ep_success = ep_success or success
            r = float(success) if sparse_reward else float(reward)
            ep_return += r
            transitions.append(Transition(
                obs=obs.copy(), action=action.copy(), reward=r,
                next_obs=next_obs.copy(), done=bool(terminated),
            ))
            obs = next_obs
            if terminated or truncated:
                break
        returns.append(ep_return)
        n_success += int(ep_success)

    env.close()
    stats = {
        "episodes": cfg.episodes_per_task,
        "transitions": len(transitions),
        "successes": n_success,
        "success_rate": n_success / max(cfg.episodes_per_task, 1),
        "mean_return": float(np.mean(returns)) if returns else 0.0,
        "noise": cfg.noise,
    }
    log.info("[%s] demos: %d eps, %d transitions, success_rate=%.0f%%, mean_return=%.2f",
             task, stats["episodes"], stats["transitions"],
             stats["success_rate"] * 100, stats["mean_return"])
    return transitions, stats
