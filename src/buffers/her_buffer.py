"""
Hindsight Experience Replay (HER) — Andrychowicz et al. 2017.

Wraps any underlying replay buffer (Uniform, PER, SemanticPER) and adds
hindsight relabeling: for each real transition, k synthetic transitions are
created by substituting the achieved goal as the desired goal, turning failed
episodes into successful ones.

Strategy 'future': for transition t, sample k goals from timesteps > t in the
same episode. This is the most sample-efficient strategy per the original paper.
"""
import numpy as np
from .replay_buffer import UniformReplayBuffer
from .per_buffer import PERBuffer
from .semantic_buffer import SemanticPERBuffer


class HERBuffer:
    def __init__(
        self,
        underlying_buffer,
        goal_dim: int = 3,
        obs_dim: int = 25,
        k: int = 4,
        strategy: str = "future",
    ):
        self.buffer   = underlying_buffer
        self.goal_dim = goal_dim
        self.obs_dim  = obs_dim
        self.k        = k
        self.strategy = strategy
        self._episode: list = []   # temp storage for current episode

    # ── public interface mirrors underlying buffer ────────────────────────

    def mark_episode_start(self):
        self._episode = []
        if hasattr(self.buffer, "mark_episode_start"):
            self.buffer.mark_episode_start()

    def push(self, obs, action, reward, next_obs, done,
             achieved_goal=None, next_achieved_goal=None):
        """Push real transition and cache for HER relabeling."""
        self.buffer.push(obs, action, reward, next_obs, done)
        if achieved_goal is not None:
            self._episode.append({
                "obs":               obs,
                "action":            action,
                "next_obs":          next_obs,
                "done":              done,
                "achieved_goal":     np.array(achieved_goal, dtype=np.float32),
                "next_achieved_goal": np.array(next_achieved_goal, dtype=np.float32),
            })

    def finish_episode(self, compute_reward_fn):
        """Relabel episode transitions and push synthetic successes."""
        ep = self._episode
        T  = len(ep)
        if T == 0:
            return

        for t, tr in enumerate(ep):
            # Sample k future achieved goals
            if self.strategy == "future":
                future_t = np.random.randint(t, T, size=min(self.k, T - t))
            elif self.strategy == "final":
                future_t = np.full(self.k, T - 1, dtype=int)
            else:
                future_t = np.random.randint(0, T, size=self.k)

            for fi in future_t:
                new_goal = ep[fi]["achieved_goal"]

                # Relabel desired_goal in obs (last goal_dim entries)
                new_obs      = tr["obs"].copy()
                new_next_obs = tr["next_obs"].copy()
                new_obs[-self.goal_dim:]      = new_goal
                new_next_obs[-self.goal_dim:] = new_goal

                # Recompute sparse reward for new goal
                new_reward = float(compute_reward_fn(
                    tr["next_achieved_goal"], new_goal, {}
                ))

                self.buffer.push(new_obs, tr["action"], new_reward,
                                 new_next_obs, tr["done"])

        self._episode = []

    # ── delegate everything else to underlying buffer ─────────────────────

    def sample(self, batch_size: int) -> dict:
        return self.buffer.sample(batch_size)

    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        self.buffer.update_priorities(indices, td_errors)

    def apply_semantic_priority(self, *args, **kwargs):
        if hasattr(self.buffer, "apply_semantic_priority"):
            self.buffer.apply_semantic_priority(*args, **kwargs)

    def get_episode_start(self) -> int:
        if hasattr(self.buffer, "get_episode_start"):
            return self.buffer.get_episode_start()
        return self.buffer._ptr

    @property
    def _ptr(self):
        return self.buffer._ptr

    def __len__(self):
        return len(self.buffer)
