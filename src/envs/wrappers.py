"""
Environment factory and wrappers for Gymnasium-Robotics Fetch tasks.

Gymnasium-Robotics Fetch environments:
  FetchReach-v4       - reach a target position (easiest)
  FetchPush-v4        - push a block to a goal
  FetchSlide-v4       - slide a puck across a frictionless table
  FetchPickAndPlace-v4 - pick up a block and place at goal (hardest)

All have sparse binary rewards: 0 if goal reached, -1 otherwise.
Observation dict: {observation, achieved_goal, desired_goal}
We flatten to a single vector for the policy network.
"""
import numpy as np
import gymnasium as gym
import gymnasium_robotics  # registers Fetch environments with gymnasium
from typing import Optional, List


TASK_DESCRIPTIONS = {
    "FetchReach-v4":
        "A robot arm must move its gripper to a floating target position in 3D space.",
    "FetchPush-v4":
        "A robot arm must push a block on a table to a target position.",
    "FetchSlide-v4":
        "A robot arm must hit a puck so that it slides to a distant target on a frictionless table.",
    "FetchPickAndPlace-v4":
        "A robot arm must pick up a block from the table and place it at a floating target position.",
}


class FlattenGoalObs(gym.ObservationWrapper):
    """Flatten Dict observation {observation, achieved_goal, desired_goal} → 1D array.

    Also stores obs_dim and goal_dim as attributes, and exposes the last
    achieved_goal via self.last_achieved_goal for HER relabeling.
    """

    def __init__(self, env):
        super().__init__(env)
        obs_space = env.observation_space
        self.obs_dim  = obs_space["observation"].shape[0]
        self.goal_dim = obs_space["achieved_goal"].shape[0]
        total_dim = self.obs_dim + self.goal_dim * 2
        self.observation_space = gym.spaces.Box(
            low=-np.inf, high=np.inf, shape=(total_dim,), dtype=np.float32
        )
        self.last_achieved_goal: np.ndarray = np.zeros(self.goal_dim, dtype=np.float32)

    def observation(self, obs):
        self.last_achieved_goal = obs["achieved_goal"].astype(np.float32)
        return np.concatenate([
            obs["observation"],
            obs["achieved_goal"],
            obs["desired_goal"],
        ]).astype(np.float32)


class FrameCapture(gym.Wrapper):
    """
    Captures rendered RGB frames each step and exposes them via `episode_frames`.
    Only renders if render_mode='rgb_array' was passed at env creation.
    """

    def __init__(self, env):
        super().__init__(env)
        self.episode_frames: List[np.ndarray] = []

    def reset(self, **kwargs):
        self.episode_frames = []
        obs, info = self.env.reset(**kwargs)
        frame = self.env.render()
        if frame is not None:
            self.episode_frames.append(frame)
        return obs, info

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        frame = self.env.render()
        if frame is not None:
            self.episode_frames.append(frame)
        return obs, reward, terminated, truncated, info


def make_env(
    env_name: str,
    max_episode_steps: Optional[int] = None,
    render_mode: str = "rgb_array",
    seed: Optional[int] = None,
    capture_frames: bool = True,
) -> gym.Env:
    """Create and wrap a Gymnasium-Robotics Fetch environment.

    Args:
        env_name: One of the Fetch-* env IDs (e.g. 'FetchPickAndPlace-v4').
        max_episode_steps: Override the default episode length (default: 50).
        render_mode: 'rgb_array' for frame capture, 'human' for display.
        seed: Optional RNG seed.
        capture_frames: Whether to wrap with FrameCapture.

    Returns:
        Wrapped gymnasium environment with flat observations.
    """
    kwargs = {}
    # Only request rendering when we actually need frames — otherwise MuJoCo's
    # offscreen context fails on machines without OSMesa/EGL (defensive: keeps
    # heuristic-only / no-frames runs on minimal images from crashing).
    if capture_frames:
        kwargs["render_mode"] = render_mode
    if max_episode_steps is not None:
        kwargs["max_episode_steps"] = max_episode_steps

    env = gym.make(env_name, **kwargs)
    env = FlattenGoalObs(env)
    if capture_frames and render_mode == "rgb_array":
        env = FrameCapture(env)

    if seed is not None:
        env.reset(seed=seed)

    return env


def get_task_description(env_name: str) -> str:
    return TASK_DESCRIPTIONS.get(env_name, f"Robotic manipulation task: {env_name}")
