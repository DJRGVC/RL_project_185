"""
Semantic PER — extends PER with VLM-grounded failure localization.

After each episode the VLM returns a failure timestep t_fail.
Transitions in [t_fail - W, t_fail + W] receive a priority multiplier of
`semantic_boost`. This signal is blended with the TD-error priority:

    final_priority = semantic_alpha * semantic_priority
                   + (1 - semantic_alpha) * td_priority

Both components are normalized before blending so neither dominates by scale.
"""
import numpy as np
from .per_buffer import PERBuffer


class SemanticPERBuffer(PERBuffer):
    def __init__(
        self,
        capacity: int,
        alpha: float = 0.6,
        beta_start: float = 0.4,
        beta_end: float = 1.0,
        beta_anneal_steps: int = 500_000,
        epsilon: float = 1e-6,
        semantic_boost: float = 10.0,
        semantic_alpha: float = 0.7,
    ):
        super().__init__(capacity, alpha, beta_start, beta_end,
                         beta_anneal_steps, epsilon)
        self.semantic_boost = semantic_boost
        self.semantic_alpha = semantic_alpha
        # Per-transition semantic multiplier (default 1.0 = no boost)
        self._semantic_weight = np.ones(capacity, dtype=np.float32)

    # ── episode-level VLM callback ────────────────────────────────────────

    def apply_semantic_priority(
        self,
        episode_start_idx: int,
        episode_length: int,
        failure_timestep: int,
        window: int = 5,
    ):
        """Boost sampling priority for transitions near the identified failure.

        Args:
            episode_start_idx: index in the ring buffer where the episode begins.
            episode_length: number of transitions in the episode.
            failure_timestep: VLM-identified timestep of failure (0-indexed within episode).
            window: half-width of the boosted region.
        """
        t_lo = max(0, failure_timestep - window)
        t_hi = min(episode_length - 1, failure_timestep + window)

        for local_t in range(t_lo, t_hi + 1):
            buf_idx = (episode_start_idx + local_t) % self.capacity
            self._semantic_weight[buf_idx] = self.semantic_boost

        # Recompute blended priorities for the whole episode
        for local_t in range(episode_length):
            buf_idx = (episode_start_idx + local_t) % self.capacity
            self._recompute_priority(buf_idx)

    def _recompute_priority(self, buf_idx: int):
        td_p    = self._sum_tree[buf_idx]
        # Multiplicative: semantic weight scales TD priority, degrades to PER when weight=1
        blended = td_p * self._semantic_weight[buf_idx]
        self._sum_tree.update(buf_idx, blended)

    # ── overrides ────────────────────────────────────────────────────────

    def push(self, obs, action, reward, next_obs, done):
        idx = self._ptr
        super().push(obs, action, reward, next_obs, done)
        # Reset semantic weight when slot is overwritten
        self._semantic_weight[idx] = 1.0

    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        """Update TD-error priority then scale by semantic weight multiplicatively."""
        priorities = (np.abs(td_errors) + self.epsilon) ** self.alpha
        self._max_priority = max(self._max_priority, priorities.max())
        for idx, td_p in zip(indices, priorities):
            self._sum_tree.update(idx, td_p * self._semantic_weight[idx])

    # ── episode tracker (used by train.py) ───────────────────────────────

    def get_episode_start(self) -> int:
        """Return the buffer index of the first transition of the current episode."""
        return self._episode_start if hasattr(self, "_episode_start") else self._ptr

    def mark_episode_start(self):
        self._episode_start = self._ptr
