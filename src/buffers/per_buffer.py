"""
Prioritized Experience Replay (PER) — Schaul et al. 2015.
Uses a sum-tree for O(log n) priority updates and O(log n) stratified sampling.
Importance-sampling (IS) weights correct for the non-uniform sampling bias.
"""
import numpy as np
from .replay_buffer import UniformReplayBuffer


class SumTree:
    """Binary sum-tree backed by a flat array. Leaves occupy [capacity-1, 2*capacity-1)."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.tree = np.zeros(2 * capacity, dtype=np.float64)

    def update(self, leaf_idx: int, priority: float):
        idx = leaf_idx + self.capacity
        delta = priority - self.tree[idx]
        self.tree[idx] = priority
        while idx > 1:
            idx //= 2
            self.tree[idx] += delta

    def update_batch(self, leaf_idxs: np.ndarray, priorities: np.ndarray):
        for i, p in zip(leaf_idxs, priorities):
            self.update(i, p)

    def sample(self, value: float) -> int:
        idx = 1
        while idx < self.capacity:
            left = 2 * idx
            if value <= self.tree[left]:
                idx = left
            else:
                value -= self.tree[left]
                idx = left + 1
        return idx - self.capacity  # return leaf index

    @property
    def total(self) -> float:
        return self.tree[1]

    def __getitem__(self, leaf_idx: int) -> float:
        return self.tree[leaf_idx + self.capacity]


class PERBuffer(UniformReplayBuffer):
    """Prioritized Experience Replay with IS correction."""

    def __init__(
        self,
        capacity: int,
        alpha: float = 0.6,
        beta_start: float = 0.4,
        beta_end: float = 1.0,
        beta_anneal_steps: int = 500_000,
        epsilon: float = 1e-6,
    ):
        super().__init__(capacity)
        self.alpha = alpha
        self.beta = beta_start
        self.beta_start = beta_start
        self.beta_end = beta_end
        self.beta_anneal_steps = beta_anneal_steps
        self.epsilon = epsilon
        self._sum_tree = SumTree(capacity)
        self._max_priority = 1.0
        self._step = 0

    # ── overrides ────────────────────────────────────────────────────────

    def push(self, obs, action, reward, next_obs, done):
        idx = self._ptr
        super().push(obs, action, reward, next_obs, done)
        self._sum_tree.update(idx, self._max_priority ** self.alpha)

    def sample(self, batch_size: int) -> dict:
        self._anneal_beta()
        total = self._sum_tree.total
        segment = total / batch_size

        idxs = np.empty(batch_size, dtype=np.int64)
        for i in range(batch_size):
            mass = np.random.uniform(segment * i, segment * (i + 1))
            idxs[i] = self._sum_tree.sample(mass)

        priorities = np.array([self._sum_tree[i] for i in idxs], dtype=np.float64)
        probs = priorities / total
        weights = (self._size * probs) ** (-self.beta)
        weights /= weights.max()

        batch = self._make_batch(idxs)
        batch["weights"]  = weights.astype(np.float32)
        batch["indices"]  = idxs
        return batch

    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        priorities = (np.abs(td_errors) + self.epsilon) ** self.alpha
        self._sum_tree.update_batch(indices, priorities)
        self._max_priority = max(self._max_priority, priorities.max())

    # ── helpers ──────────────────────────────────────────────────────────

    def _anneal_beta(self):
        self._step += 1
        frac = min(1.0, self._step / self.beta_anneal_steps)
        self.beta = self.beta_start + frac * (self.beta_end - self.beta_start)
