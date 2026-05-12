"""
BidirectionalSemanticBuffer — boost BOTH failure and success windows.

Extends PER with two per-slot multiplicative weights:

    success_weight  : boosted around an oracle-identified "best progress" timestep
    failure_weight  : boosted around an oracle-identified failure timestep

The final stored priority is::

    priority = TD_priority * success_weight * failure_weight

Both default to 1.0, so the buffer degrades to plain PER when no semantic
info has been applied to a slot.

Behavior per episode outcome:
    - Successful episode: only success_weight is applied (failure_window is
                          not invoked by train.py for successful episodes).
    - Failed episode:     both can be applied — success on the best-progress
                          timestep and failure on the contact-loss / ballistic
                          / argmin timestep.

Sits alongside SemanticPERBuffer (which only boosts failure). It is the direct
test of our hypothesis that boosting failure helps *beyond* what boosting
success alone (Sharony et al. 2026, arXiv 2602.01915) provides.

Implementation detail: we store the raw per-slot TD priority in a sibling
array `_td_priority` so that whenever a weight changes we can re-blend
exactly (priority := td * w_fail * w_succ) without having to invert a stale
sum-tree leaf.
"""
import numpy as np
from .per_buffer import PERBuffer


class BidirectionalSemanticBuffer(PERBuffer):
    def __init__(
        self,
        capacity: int,
        alpha: float = 0.6,
        beta_start: float = 0.4,
        beta_end: float = 1.0,
        beta_anneal_steps: int = 500_000,
        epsilon: float = 1e-6,
        failure_boost: float = 10.0,
        success_boost: float = 10.0,
    ):
        super().__init__(capacity, alpha, beta_start, beta_end,
                         beta_anneal_steps, epsilon)
        self.failure_boost = failure_boost
        self.success_boost = success_boost
        self._failure_weight = np.ones(capacity, dtype=np.float32)
        self._success_weight = np.ones(capacity, dtype=np.float32)
        # Track raw TD-priority component so re-blends are exact.
        self._td_priority    = np.full(capacity, self._max_priority ** self.alpha,
                                       dtype=np.float64)
        self._episode_start = 0

    # ── episode tracker (used by train.py) ───────────────────────────────

    def get_episode_start(self) -> int:
        return self._episode_start

    def mark_episode_start(self):
        self._episode_start = self._ptr

    # ── overrides ────────────────────────────────────────────────────────

    def push(self, obs, action, reward, next_obs, done):
        idx = self._ptr
        # We bypass PERBuffer.push's sum-tree write so we can apply weights
        # in one pass (preserving the priority = td * w_fail * w_succ invariant).
        if not self._storage:
            self._init_storage(obs, action, reward, next_obs, done)
        self._storage["obs"][idx]      = obs
        self._storage["action"][idx]   = action
        self._storage["reward"][idx]   = float(reward)
        self._storage["next_obs"][idx] = next_obs
        self._storage["done"][idx]     = float(done)
        self._ptr  = (idx + 1) % self.capacity
        self._size = min(self._size + 1, self.capacity)
        # Reset semantic weights for the overwritten slot.
        self._failure_weight[idx] = 1.0
        self._success_weight[idx] = 1.0
        td_p = self._max_priority ** self.alpha
        self._td_priority[idx] = td_p
        # weights are 1.0 here, so priority == td_p
        self._sum_tree.update(idx, td_p)

    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        """Re-blend priority := td * w_fail * w_succ for each updated slot."""
        td_priorities = (np.abs(td_errors) + self.epsilon) ** self.alpha
        self._max_priority = max(self._max_priority, float(td_priorities.max()))
        for idx, td_p in zip(indices, td_priorities):
            self._td_priority[idx] = td_p
            blended = td_p * self._failure_weight[idx] * self._success_weight[idx]
            self._sum_tree.update(idx, blended)

    # ── public API: episode-level semantic boosts ────────────────────────

    def apply_failure_priority(
        self,
        episode_start_idx: int,
        episode_length: int,
        failure_timestep: int,
        window: int = 5,
    ):
        """Boost failure_weight for transitions in [t_fail-W, t_fail+W]."""
        self._apply_window(self._failure_weight, self.failure_boost,
                           episode_start_idx, episode_length,
                           failure_timestep, window)

    def apply_success_priority(
        self,
        episode_start_idx: int,
        episode_length: int,
        success_timestep: int,
        window: int = 5,
    ):
        """Boost success_weight for transitions in [t_succ-W, t_succ+W]."""
        self._apply_window(self._success_weight, self.success_boost,
                           episode_start_idx, episode_length,
                           success_timestep, window)

    # Backward-compat alias so train.py's existing semantic-priority hook
    # also works for this buffer (semantic_priority == failure_priority here).
    def apply_semantic_priority(
        self,
        episode_start_idx: int,
        episode_length: int,
        failure_timestep: int,
        window: int = 5,
    ):
        self.apply_failure_priority(episode_start_idx, episode_length,
                                    failure_timestep, window)

    # ── internals ────────────────────────────────────────────────────────

    def _apply_window(
        self,
        weight_array: np.ndarray,
        boost: float,
        episode_start_idx: int,
        episode_length: int,
        center_t: int,
        window: int,
    ):
        t_lo = max(0, center_t - window)
        t_hi = min(episode_length - 1, center_t + window)
        for local_t in range(t_lo, t_hi + 1):
            buf_idx = (episode_start_idx + local_t) % self.capacity
            weight_array[buf_idx] = boost
        # Recompute blended priorities for the whole episode (≤50 entries → cheap).
        for local_t in range(episode_length):
            buf_idx = (episode_start_idx + local_t) % self.capacity
            td_p = self._td_priority[buf_idx]
            blended = td_p * self._failure_weight[buf_idx] * self._success_weight[buf_idx]
            self._sum_tree.update(buf_idx, blended)
