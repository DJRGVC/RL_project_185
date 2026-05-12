"""
VLM-RB — Sharony et al. (2026) "VLM-Guided Experience Replay" baseline.

Reference: Sharony, Jurgenson, Krupnik, Di Castro, Mannor.
"VLM-Guided Experience Replay." arXiv:2602.01915 (Feb 2026).

This is a *faithful approximation* of VLM-RB for head-to-head comparison
against our failure-direction methods on Gymnasium-Robotics Fetch. We
reproduce the three load-bearing components of Sharony's recipe:

  1. Clip-level VLM scoring.
       Episodes are partitioned into contiguous sub-trajectories of
       length L=32 frames; each clip receives one scalar
       p_VLM ∈ [0,1] = P(clip contains clear instance of goal
       satisfaction).

  2. Continuous-control priority blend.
       q^P(i) ∝ p_VLM_i · |δ_i|  (multiplicative inside the priority
       distribution; Sharony §4 "Continuous Control").

  3. Mixture-with-uniform sampling, λ-warmup.
       q_t(i) = λ_t · q^P(i) + (1 − λ_t) · q^U(i)
       with λ linearly annealed 0 → 0.5 over `mixture_anneal_steps`.

Implementation notes / differences from the published method:

  - Sharony runs the VLM in an asynchronous worker writing priorities
    back into a Perception-LM-1B-class model on the training machine
    (~12% throughput overhead). We expose `vlm_score_fn` as a synchronous
    callable invoked on `mark_episode_end` to keep the buffer's behaviour
    deterministic and avoid coupling the buffer to thread state. The
    training loop can choose to off-thread the scorer if desired.

  - Sharony's paper uses a frozen open-weights PerceptionLM. We accept
    any `(frames, task_description) -> List[float] in [0,1]` callable;
    `src.vlm.vlm_rb_scorer.make_vlm_rb_scorer(...)` provides a
    Sonnet-4.5-backed implementation matching Sharony's prompt wording.

  - The buffer's sum-tree stores `(p_VLM_clip · |δ| + ε)^α`, i.e. the
    multiplicative form from Sharony §4.2. Mixture-with-uniform is then
    applied at sampling time (not folded into the sum-tree) so the
    uniform component remains exact.

  - Default α=0.6 matches Sharony (and our PERBuffer default).
"""
from __future__ import annotations

import logging
from typing import Any, Callable, List, Optional

import numpy as np

from .per_buffer import PERBuffer

logger = logging.getLogger(__name__)


# Sentinel default until a clip is first scored: keep the clip at
# uniform weight (1.0) so unscored transitions sample like vanilla PER.
DEFAULT_CLIP_SCORE: float = 1.0


class VLMRBBuffer(PERBuffer):
    """Sharony VLM-RB priority buffer.

    Parameters
    ----------
    capacity
        Number of transition slots.
    alpha, beta_start, beta_end, beta_anneal_steps, epsilon
        Standard PER parameters (see :class:`PERBuffer`).
    clip_length
        Number of consecutive transitions that form one VLM-scored clip.
        Sharony et al. use L=32 frames.
    vlm_score_fn
        Callable ``fn(clip_frames, task_description) -> float in [0, 1]``
        returning the VLM's P(goal satisfaction) for the clip. May be
        ``None`` if no scoring is wired (buffer degenerates to PER).
    task_description
        Natural-language task description passed to the scorer.
    mixture_lambda_start, mixture_lambda_end
        Linear warm-up of λ_t over `mixture_anneal_steps` *sample()
        calls*. Sharony reports λ_max=0.5.
    mixture_anneal_steps
        Warm-up horizon for λ_t (in sample() calls).
    vlm_call_interval
        Run the VLM scorer once every N episodes. Default 10 trades cost
        for coverage similarly to our other VLM baselines.
    """

    def __init__(
        self,
        capacity: int,
        alpha: float = 0.6,
        beta_start: float = 0.4,
        beta_end: float = 1.0,
        beta_anneal_steps: int = 500_000,
        epsilon: float = 1e-6,
        clip_length: int = 32,
        vlm_score_fn: Optional[Callable[[List[Any], str], float]] = None,
        task_description: str = "robotic manipulation",
        mixture_lambda_start: float = 0.0,
        mixture_lambda_end: float = 0.5,
        mixture_anneal_steps: int = 500_000,
        vlm_call_interval: int = 10,
    ):
        super().__init__(
            capacity=capacity,
            alpha=alpha,
            beta_start=beta_start,
            beta_end=beta_end,
            beta_anneal_steps=beta_anneal_steps,
            epsilon=epsilon,
        )
        self.clip_length = int(clip_length)
        self.vlm_score_fn = vlm_score_fn
        self.task_description = task_description
        self.mixture_lambda_start = float(mixture_lambda_start)
        self.mixture_lambda_end = float(mixture_lambda_end)
        self.mixture_anneal_steps = int(mixture_anneal_steps)
        self.vlm_call_interval = int(vlm_call_interval)

        # Per-slot VLM clip score (defaults to 1.0 = no boost).
        self._clip_score = np.full(capacity, DEFAULT_CLIP_SCORE, dtype=np.float32)
        # Track raw TD priority component (so weight updates can be exact).
        self._td_priority = np.full(
            capacity, self._max_priority ** self.alpha, dtype=np.float64
        )

        # Episode bookkeeping
        self._episode_start: int = 0
        self._episode_count: int = 0

        # Diagnostics
        self.stats: dict = {
            "vlm_rb_clip_call_count": 0,
            "vlm_rb_clips_scored": 0,
            "vlm_rb_calls_failed": 0,
            "vlm_rb_avg_clip_score": float(DEFAULT_CLIP_SCORE),
            "vlm_rb_lambda_t": float(mixture_lambda_start),
        }
        # Running sum / count for the average clip score metric.
        self._score_sum: float = 0.0
        self._score_count: int = 0

    # ── episode tracker (used by train.py, mirroring SemanticPER) ────────

    def get_episode_start(self) -> int:
        return self._episode_start

    def mark_episode_start(self):
        self._episode_start = self._ptr

    # ── overrides ────────────────────────────────────────────────────────

    def push(self, obs, action, reward, next_obs, done):
        idx = self._ptr
        # Initialise storage / advance pointer via the uniform base; do
        # the priority bookkeeping ourselves so we keep the
        # priority = (TD · clip_score)^α invariant exact.
        from .replay_buffer import UniformReplayBuffer

        UniformReplayBuffer.push(self, obs, action, reward, next_obs, done)

        # Reset clip score for the overwritten slot — until a real VLM
        # call scores its clip, the transition behaves like vanilla PER.
        self._clip_score[idx] = DEFAULT_CLIP_SCORE
        td_p = self._max_priority ** self.alpha
        self._td_priority[idx] = td_p
        # priority = (TD · clip_score)^α; clip_score=1 so this is just TD.
        self._sum_tree.update(idx, td_p)

    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        """Re-blend priority := (|TD| · p_VLM_clip + ε)^α.

        Note: we follow Sharony §4.2 by combining TD-error and clip
        score *inside* the priority exponent (`(|δ|·p_VLM + ε)^α`)
        rather than as a product of two independent (·)^α terms.
        """
        td_abs = np.abs(td_errors).astype(np.float64)
        idxs = np.asarray(indices, dtype=np.int64)
        max_td = 0.0
        for idx, td_a in zip(idxs, td_abs):
            score = float(self._clip_score[idx])
            # Sharony: q^P ∝ p_VLM · |δ|; we add ε before the α-exponent so
            # priority never collapses to 0 when both signals are tiny.
            blended = (td_a * score + self.epsilon) ** self.alpha
            self._td_priority[idx] = blended
            self._sum_tree.update(idx, blended)
            if td_a > max_td:
                max_td = float(td_a)
        # Track the raw max |δ| so new-slot priority on push() stays
        # within a reasonable upper envelope (matches PERBuffer).
        if max_td > 0.0:
            self._max_priority = max(self._max_priority, max_td + self.epsilon)

    def sample(self, batch_size: int) -> dict:
        """Mixture-with-uniform sampling: q_t = λ·q^P + (1−λ)·q^U."""
        self._anneal_beta()
        lam = self._current_lambda()
        self.stats["vlm_rb_lambda_t"] = float(lam)

        # Decide each slot's source: priority vs. uniform.
        # Approximate the mixture by drawing ~Bernoulli(λ) per slot.
        n_size = max(1, self._size)
        use_priority = np.random.random(batch_size) < lam
        n_p = int(use_priority.sum())
        n_u = batch_size - n_p

        idxs_p = np.empty(n_p, dtype=np.int64)
        if n_p > 0:
            total = self._sum_tree.total
            if total <= 0:
                # All-zero priorities (only possible pre-update); fall back to uniform
                idxs_p = np.random.randint(0, n_size, size=n_p).astype(np.int64)
            else:
                segment = total / n_p
                for i in range(n_p):
                    mass = np.random.uniform(segment * i, segment * (i + 1))
                    idxs_p[i] = self._sum_tree.sample(mass)

        idxs_u = (np.random.randint(0, n_size, size=n_u).astype(np.int64)
                  if n_u > 0 else np.empty(0, dtype=np.int64))

        idxs = np.empty(batch_size, dtype=np.int64)
        idxs[use_priority] = idxs_p
        idxs[~use_priority] = idxs_u

        # IS weights against the *mixture* distribution.
        # q_t(i) = λ · p_i/total  + (1-λ) · 1/N
        priorities = np.array([self._sum_tree[int(i)] for i in idxs],
                              dtype=np.float64)
        total = max(self._sum_tree.total, 1e-12)
        q_p = priorities / total
        q_u = np.full_like(q_p, 1.0 / n_size)
        q_mix = lam * q_p + (1.0 - lam) * q_u
        # Clip to avoid divide-by-zero blowing up the IS weight.
        q_mix = np.clip(q_mix, 1e-12, None)
        weights = (n_size * q_mix) ** (-self.beta)
        weights /= weights.max()

        batch = self._make_batch(idxs)
        batch["weights"] = weights.astype(np.float32)
        batch["indices"] = idxs
        return batch

    # ── episode-level VLM scoring entry point ────────────────────────────

    def apply_vlm_rb_scoring(
        self,
        episode_start_idx: int,
        episode_length: int,
        episode_frames: Optional[List[Any]] = None,
        force_scores: Optional[List[float]] = None,
    ):
        """Score the just-finished episode's clips and update priorities.

        Partitions the episode into ⌈T / L⌉ contiguous clips of length
        `clip_length` (the final clip may be shorter than L). For each
        clip, invokes ``vlm_score_fn(clip_frames, task_description)`` and
        writes the score onto every buffer slot belonging to that clip.

        Parameters
        ----------
        episode_start_idx
            Ring-buffer index of the episode's first transition (i.e.
            ``mark_episode_start()`` snapshot).
        episode_length
            Number of transitions in the episode.
        episode_frames
            List of rendered frames. Length should equal
            ``episode_length + 1`` (frames-per-step + final reset frame)
            or ``episode_length``; we slice with whatever is given.
        force_scores
            For tests / smoke runs: skip the VLM call and use these
            scalar scores per clip directly. If provided, must contain
            ⌈T/L⌉ entries.
        """
        if episode_length <= 0:
            return
        # Bump call counter regardless of whether a real VLM is wired.
        self._episode_count += 1

        # Partition into clips of size clip_length (last may be short).
        L = self.clip_length
        n_clips = (episode_length + L - 1) // L

        # Decide each clip's score.
        scores: List[float] = []
        if force_scores is not None:
            if len(force_scores) != n_clips:
                raise ValueError(
                    f"force_scores has {len(force_scores)} entries but "
                    f"episode has {n_clips} clips (T={episode_length}, L={L})."
                )
            scores = [float(s) for s in force_scores]
        else:
            for c in range(n_clips):
                t0 = c * L
                t1 = min(episode_length, (c + 1) * L)
                clip_frames = (episode_frames[t0:t1] if episode_frames is not None
                               else [])
                self.stats["vlm_rb_clip_call_count"] += 1
                if self.vlm_score_fn is None:
                    scores.append(DEFAULT_CLIP_SCORE)
                    continue
                try:
                    s = float(self.vlm_score_fn(clip_frames, self.task_description))
                    s = float(np.clip(s, 0.0, 1.0))
                    scores.append(s)
                    self.stats["vlm_rb_clips_scored"] += 1
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"[VLM-RB] clip {c} scoring failed: {e}")
                    self.stats["vlm_rb_calls_failed"] += 1
                    scores.append(DEFAULT_CLIP_SCORE)

        # Track avg score for diagnostics.
        for s in scores:
            self._score_sum += s
            self._score_count += 1
        if self._score_count > 0:
            self.stats["vlm_rb_avg_clip_score"] = (
                self._score_sum / self._score_count
            )

        # Write clip scores onto buffer slots and re-blend priorities.
        #
        # Priority form (Sharony §4.2):  p_i = (|δ_i| · p_VLM_i + ε)^α.
        # On a clip-score update we want to rescale the current priority
        # to reflect the new p_VLM without re-querying the agent for |δ|.
        # We rescale in priority-space by (new/prev) **outside** the α-
        # exponent. This is a small bias relative to the exact form
        # (the exact form would require ((|δ|·new + ε) / (|δ|·prev + ε))^α
        # which depends on |δ|), but it preserves relative ordering and
        # the *exact* form is recovered on the very next
        # update_priorities() call, which re-derives priority from |δ|.
        for c, s in enumerate(scores):
            t0 = c * L
            t1 = min(episode_length, (c + 1) * L)
            for local_t in range(t0, t1):
                buf_idx = (episode_start_idx + local_t) % self.capacity
                prev_score = max(float(self._clip_score[buf_idx]), 1e-12)
                prev_priority = self._td_priority[buf_idx]
                # Update stored score first, then rescale priority.
                self._clip_score[buf_idx] = s
                scaled = prev_priority * (s / prev_score)
                self._td_priority[buf_idx] = scaled
                self._sum_tree.update(buf_idx, scaled)

    # ── helpers ──────────────────────────────────────────────────────────

    def _current_lambda(self) -> float:
        if self.mixture_anneal_steps <= 0:
            return self.mixture_lambda_end
        frac = min(1.0, self._step / max(1, self.mixture_anneal_steps))
        return self.mixture_lambda_start + frac * (
            self.mixture_lambda_end - self.mixture_lambda_start
        )

    def get_vlm_rb_stats(self) -> dict:
        """Return diagnostics for W&B logging."""
        return {
            f"buffer/{k}": v for k, v in self.stats.items()
        }
