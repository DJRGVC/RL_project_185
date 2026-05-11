"""
Uniform replay buffer — standard experience replay with O(1) push and O(1) sample.
"""
import numpy as np
from typing import Dict


class UniformReplayBuffer:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self._ptr = 0
        self._size = 0
        self._storage: Dict[str, np.ndarray] = {}

    # ── storage ──────────────────────────────────────────────────────────

    def _init_storage(self, obs, action, reward, next_obs, done):
        obs_dim    = obs.shape[0]
        action_dim = action.shape[0]
        self._storage = {
            "obs":      np.zeros((self.capacity, obs_dim),    dtype=np.float32),
            "action":   np.zeros((self.capacity, action_dim), dtype=np.float32),
            "reward":   np.zeros((self.capacity,),            dtype=np.float32),
            "next_obs": np.zeros((self.capacity, obs_dim),    dtype=np.float32),
            "done":     np.zeros((self.capacity,),            dtype=np.float32),
        }

    def push(self, obs, action, reward, next_obs, done):
        if not self._storage:
            self._init_storage(obs, action, reward, next_obs, done)
        i = self._ptr
        self._storage["obs"][i]      = obs
        self._storage["action"][i]   = action
        self._storage["reward"][i]   = float(reward)
        self._storage["next_obs"][i] = next_obs
        self._storage["done"][i]     = float(done)
        self._ptr  = (i + 1) % self.capacity
        self._size = min(self._size + 1, self.capacity)

    # ── sampling ─────────────────────────────────────────────────────────

    def sample(self, batch_size: int) -> dict:
        idxs = np.random.randint(0, self._size, size=batch_size)
        return self._make_batch(idxs)

    def _make_batch(self, idxs: np.ndarray) -> dict:
        batch = {k: self._storage[k][idxs] for k in self._storage}
        batch["indices"] = idxs
        batch["weights"] = np.ones(len(idxs), dtype=np.float32)
        return batch

    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        pass  # uniform buffer ignores priority updates

    def __len__(self):
        return self._size
