"""MetaWorld v3 env factory + scripted-policy lookup."""

from __future__ import annotations

import random

import metaworld
import numpy as np
from metaworld.policies import ENV_POLICY_MAP


def make_env(
    task_name: str,
    seed: int,
    max_episode_steps: int | None = None,
    camera_name: str | None = None,
):
    """Return ``(env, train_tasks)``. Renders only when needed."""
    mt1 = metaworld.MT1(task_name, seed=seed)
    env_cls = mt1.train_classes[task_name]
    kwargs = {}
    if camera_name is not None:
        kwargs["render_mode"] = "rgb_array"
        kwargs["camera_name"] = camera_name
    env = env_cls(**kwargs)
    if max_episode_steps is not None and hasattr(env, "max_path_length"):
        env.max_path_length = max_episode_steps
    return env, mt1.train_tasks


def reset_with_task(env, tasks, rng: random.Random) -> tuple[np.ndarray, dict]:
    task = rng.choice(tasks)
    env.set_task(task)
    obs, info = env.reset()
    return np.asarray(obs, dtype=np.float32), info


def make_policy(task_name: str):
    if task_name not in ENV_POLICY_MAP:
        raise KeyError(f"No scripted policy for task {task_name!r}.")
    return ENV_POLICY_MAP[task_name]()


def noisy_action(
    scripted_action: np.ndarray,
    rng: np.random.Generator,
    noise: float,
    action_low: np.ndarray,
    action_high: np.ndarray,
) -> np.ndarray:
    if noise <= 0.0:
        return np.clip(scripted_action, action_low, action_high)
    random_action = rng.uniform(action_low, action_high)
    if noise >= 1.0:
        return random_action
    mixed = (1.0 - noise) * scripted_action + noise * random_action
    return np.clip(mixed, action_low, action_high)
