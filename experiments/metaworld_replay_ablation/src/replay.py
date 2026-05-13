"""Prioritized replay buffer with optional demo-pinning.

Single source of truth for sampling. New transitions enter at the current max
priority (Schaul et al. 2016) so they're guaranteed to be sampled at least
once before priorities decay.

Demo-pinning: transitions added with ``is_demo=True`` have their priority held
at ``demo_priority`` forever — ``update_priorities`` never lowers them. This
implements the "demo-priority" variant.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Batch:
    obs: np.ndarray
    action: np.ndarray
    reward: np.ndarray
    next_obs: np.ndarray
    done: np.ndarray
    indices: np.ndarray
    weights: np.ndarray


class PrioritizedReplayBuffer:
    def __init__(
        self,
        capacity: int,
        obs_dim: int,
        act_dim: int,
        per_alpha: float,
        priority_epsilon: float,
        default_priority: float,
        rng: np.random.Generator,
    ):
        self.capacity = capacity
        self.obs = np.zeros((capacity, obs_dim), dtype=np.float32)
        self.action = np.zeros((capacity, act_dim), dtype=np.float32)
        self.reward = np.zeros((capacity, 1), dtype=np.float32)
        self.next_obs = np.zeros((capacity, obs_dim), dtype=np.float32)
        self.done = np.zeros((capacity, 1), dtype=np.float32)
        self.priorities = np.full((capacity,), default_priority, dtype=np.float64)
        self.is_demo = np.zeros((capacity,), dtype=bool)

        self.per_alpha = per_alpha
        self.priority_epsilon = priority_epsilon
        self.default_priority = default_priority
        self.rng = rng

        self._size = 0
        self._ptr = 0
        self._max_priority = float(default_priority)

    def __len__(self) -> int:
        return self._size

    def add(self, obs, action, reward, next_obs, done, *, is_demo: bool = False,
            priority: float | None = None) -> int:
        idx = self._ptr
        self.obs[idx] = obs
        self.action[idx] = action
        self.reward[idx] = reward
        self.next_obs[idx] = next_obs
        self.done[idx] = float(done)
        self.is_demo[idx] = is_demo
        p = priority if priority is not None else max(self._max_priority, self.default_priority)
        self.priorities[idx] = p
        if p > self._max_priority:
            self._max_priority = float(p)
        self._ptr = (self._ptr + 1) % self.capacity
        self._size = min(self._size + 1, self.capacity)
        return idx

    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray) -> None:
        new = (np.abs(td_errors) + self.priority_epsilon).astype(np.float64)
        # Never overwrite demo priorities — they stay pinned at their initial value.
        mask = ~self.is_demo[indices]
        if mask.any():
            self.priorities[indices[mask]] = new[mask]
            m = float(new[mask].max())
            if m > self._max_priority:
                self._max_priority = m

    def sample(self, batch_size: int, beta: float) -> Batch:
        if self._size == 0:
            raise RuntimeError("Empty buffer.")
        scaled = self.priorities[: self._size] ** self.per_alpha
        total = scaled.sum()
        probs = scaled / total if total > 0 else np.ones(self._size) / self._size
        idx = self.rng.choice(self._size, size=batch_size, replace=True, p=probs)
        weights = (self._size * probs[idx]) ** (-beta)
        weights = weights / max(weights.max(), 1e-12)
        return Batch(
            obs=self.obs[idx],
            action=self.action[idx],
            reward=self.reward[idx],
            next_obs=self.next_obs[idx],
            done=self.done[idx],
            indices=idx,
            weights=weights.astype(np.float32),
        )
