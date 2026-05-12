"""
CounterfactualHERBuffer — VLM-counterfactual-as-hindsight-goal relabeling.

PROTOTYPE STUB (Path C, agent C2). NOT a runnable implementation.
This file defines the interface and design — the heavy lifting (VLM querying,
parsing, calibration) is owned by agent C1 (`src/vlm/counterfactual.py`).

Motivation
----------
Standard HER (Andrychowicz et al. 2017) relabels each transition's
`desired_goal` with an `achieved_goal` sampled from later timesteps in the
SAME failed episode. This is "what actually happened, treated as if intended."
Useful, but mode-collapsed: the agent never sees goals it would *have liked*
to reach but didn't.

Counterfactual HER asks a VLM:

    "At the critical failure frame K, the robot's achieved_goal was A_K.
     Given the desired_goal G, the trajectory's first K-1 frames, and the
     scene image, what achieved_goal G_cf at frame K would have put the
     episode on a trajectory to succeed?"

We then synthesize a transition where:
    - desired_goal := G_cf  (the VLM-imagined corrective goal)
    - reward       := compute_reward(next_achieved_goal, G_cf, info)
    - obs / next_obs have their last `goal_dim` slots overwritten with G_cf

The synthetic transition is pushed into the underlying replay buffer the
same way standard HER does. The agent thus learns: "if I were trying to
reach G_cf, this (s, a, s') transition would have been (close to) a success."

Why this could work
-------------------
HER relabeling is mathematically a counterfactual-reward generator: it asks
"what reward would this trajectory have received under a different goal?"
The choice of relabeling goal determines what skill the policy generalizes
toward. `future` strategy generalizes toward visited states; this generalizes
toward VLM-imagined corrective states. If the VLM's spatial reasoning is even
roughly correct, the synthetic goals lie OUTSIDE the achieved-state
distribution but INSIDE the success-feasible distribution — exactly the
"imagined goals" regime that Model-based HER (Yang et al. 2021) and Visual RL
with Imagined Goals (Nair et al. 2018) showed accelerates learning.

Why this might NOT work
-----------------------
- VLM 3D coordinate output is noisy. A bad G_cf is worse than no relabel.
- compute_reward is sparse (1 if ||A - G|| < 0.05 else 0). If G_cf is more
  than 5cm from any visited A, the synthetic reward is still 0 and we've
  added a non-success transition with a goal the policy never sees again.
- The "future" HER strategy is a strong baseline. The marginal gain from
  imagined goals over achieved goals depends on whether the achieved set
  covers the goal space well — Fetch tasks have small goal regions,
  arguably leaving little headroom.

Design choices documented below in the class.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from .her_buffer import HERBuffer


# ─────────────────────────────────────────────────────────────────────────────
# Type aliases — formalize the interface the VLM side (C1) must produce.
# ─────────────────────────────────────────────────────────────────────────────

# A single counterfactual: (frame_index_K, corrective_position_xyz, confidence)
Counterfactual = Tuple[int, np.ndarray, float]

# The signature of the VLM counterfactual callback. Agent C1 owns this.
# Inputs:
#   achieved_goals : (T, goal_dim) — the trajectory of object positions
#   desired_goal   : (goal_dim,)   — the original target
#   keyframes      : list of PIL/np images (optional; provider-dependent)
#   failure_t      : int           — the localizer's failure timestep, if any
# Returns:
#   list of (frame_index, corrective_goal, confidence) tuples, OR
#   None if the VLM was unable to produce a counterfactual.
CounterfactualFn = Callable[..., Optional[List[Counterfactual]]]


# ─────────────────────────────────────────────────────────────────────────────
# Main buffer class
# ─────────────────────────────────────────────────────────────────────────────

class CounterfactualHERBuffer(HERBuffer):
    """HER variant where some relabeling goals come from a VLM counterfactual.

    Behavior
    --------
    For each transition `t` in a failed episode:

      1. With probability `p_counterfactual` (default 0.25), sample one goal
         from the VLM counterfactual set instead of from the achieved-future
         set. The chosen counterfactual must satisfy frame_index >= t
         (causal: the corrective goal is for a future frame, not the past).

      2. With probability 1 - p_counterfactual, fall back to standard HER
         "future" strategy (sample an achieved goal from t..T-1).

      3. Successful episodes use standard HER only (no VLM call needed —
         the trajectory itself shows a success).

    The remaining (k-1) synthetic transitions per real transition keep the
    standard HER strategy, so we are STRICTLY a superset of HER: in the
    worst case (VLM returns garbage) we lose 1/k of the relabeling budget.

    Why mix counterfactual with achieved-future instead of replacing
    -----------------------------------------------------------------
    - Robustness to VLM errors: if `p_counterfactual = 0.25`, only 1 in 4
      synthetic transitions depends on the VLM. The remaining 3 are the
      proven HER signal.
    - Free fallback: if the VLM call fails or returns None, we degrade
      gracefully to standard HER for that episode.
    - Lets us A/B the mechanism: `p_counterfactual = 0.0` recovers HER
      exactly. This is the natural ablation experiment.

    Parameters
    ----------
    underlying_buffer
        Any base buffer with .push / .sample / .update_priorities
        (Uniform, PER, SemanticPER).
    counterfactual_fn
        The VLM callback. Agent C1's `CounterfactualLocalizer.localize`.
        Called once per failed episode in `finish_episode`.
    p_counterfactual
        Probability that any one synthetic relabel uses a VLM counterfactual
        rather than an achieved-future goal. 0.0 disables the mechanism
        (recovers vanilla HER); 1.0 uses VLM goals exclusively (risky).
    min_confidence
        Drop counterfactuals with VLM confidence below this threshold and
        fall back to achieved-future for that slot.
    fallback_to_achieved
        If True, when no usable counterfactual is found for a transition's
        time window, use standard HER. If False, skip relabeling entirely
        (more conservative but loses sample efficiency).
    cf_call_interval
        Call the VLM at most every Nth failed episode (cost control).
    """

    def __init__(
        self,
        underlying_buffer,
        counterfactual_fn: CounterfactualFn,
        goal_dim: int = 3,
        obs_dim: int = 25,
        k: int = 4,
        strategy: str = "future",
        p_counterfactual: float = 0.25,
        min_confidence: float = 0.5,
        fallback_to_achieved: bool = True,
        cf_call_interval: int = 1,
        cf_input_kind: str = "vlm",
        cf_window: int = 4,
        env_name: Optional[str] = None,
        verifier: Optional[object] = None,
        priority_mode: str = "uniform",
    ):
        super().__init__(
            underlying_buffer=underlying_buffer,
            goal_dim=goal_dim,
            obs_dim=obs_dim,
            k=k,
            strategy=strategy,
        )
        self.cf_fn               = counterfactual_fn
        self.p_counterfactual    = float(p_counterfactual)
        self.min_confidence      = float(min_confidence)
        self.fallback_to_achieved = bool(fallback_to_achieved)
        self.cf_call_interval    = int(cf_call_interval)
        # 'vlm' → cf_fn receives (achieved_goals, desired_goal, keyframes)
        # 'state' → cf_fn receives a full trajectory dict (for oracle CFs)
        self.cf_input_kind       = str(cf_input_kind)
        # When a CF is returned for a single frame K, also push the same
        # corrective goal as relabel for transitions in [K-cf_window, K+cf_window]
        # (still constrained to causal validity at draw time).
        self.cf_window           = int(cf_window)
        self.env_name            = env_name
        self.verifier            = verifier
        # priority_mode is informational. The *behaviour* is determined by the
        # underlying buffer (UniformReplayBuffer vs PERBuffer), but the explicit
        # tag lets train.py decide which diagnostics to log and lets callers
        # assert/inspect the buffer's sampling regime without isinstance gymnastics.
        # Allowed: 'uniform' | 'prioritized'.
        if priority_mode not in ("uniform", "prioritized"):
            raise ValueError(
                f"priority_mode must be 'uniform' or 'prioritized', got {priority_mode!r}"
            )
        self.priority_mode       = priority_mode

        # Diagnostics — populated as episodes finish. Read these from train.py
        # and log to W&B to debug the mechanism.
        # Semantics:
        #   vlm_calls            — every attempted invocation of the CF callback
        #   vlm_returned_none    — callback returned None or [] (no usable CFs)
        #   vlm_exceptions       — callback raised; counted separately so the
        #                          two failure modes aren't conflated in dashboards
        self.stats: Dict[str, int] = {
            "episodes_seen":         0,
            "episodes_failed":       0,
            "vlm_calls":             0,
            "vlm_returned_none":     0,
            "vlm_exceptions":        0,
            "cf_relabels_used":      0,
            "achieved_relabels_used": 0,
            "low_conf_dropped":      0,
            "verifications_attempted": 0,
            "verifications_passed":   0,
            # CF-deviation counters: tally of accepted CFs whose
            # `corrective_position` we have evaluated (running totals;
            # divide by `cf_accepted_count` to get the running mean).
            "cf_accepted_count":     0,
            "cf_in_workspace_count": 0,
        }
        # Running sums for CF deviation metrics. Kept as floats so we can emit
        # exact running means without integer truncation. Reset by
        # `reset_cf_deviation_stats()` (see below) — train.py calls this on
        # episode_reset boundaries when it wants per-window snapshots.
        self._cf_dev_sum_to_desired: float  = 0.0
        self._cf_dev_sum_to_achieved: float = 0.0
        # Fetch workspace bounds in metres (table surface z≈0.42); used as the
        # in-workspace indicator. Numbers mirror the bounds quoted in the
        # achieved_goal prompt in src/vlm/counterfactual.py so the VLM and
        # the diagnostics agree on what "in workspace" means.
        self._workspace_lo = np.array([1.05, 0.4, 0.4], dtype=np.float32)
        self._workspace_hi = np.array([1.55, 1.1, 0.85], dtype=np.float32)

    # ── public episode finish — overrides HERBuffer ─────────────────────────

    def finish_episode(
        self,
        compute_reward_fn: Callable[..., float],
        episode_success: Optional[bool] = None,
        keyframes: Optional[List] = None,
    ):
        """Relabel the cached episode and push synthetic transitions.

        Differs from HERBuffer.finish_episode in two ways:
          (a) On *failed* episodes, optionally queries the VLM for a set of
              counterfactual goals before relabeling.
          (b) For each transition's k synthetic relabels, samples each
              individually as either "VLM counterfactual" or "achieved-future"
              with probability p_counterfactual.

        Args:
            compute_reward_fn: env.unwrapped.compute_reward — sparse Fetch
                reward (achieved, desired, info) -> {0, -1}.
            episode_success: If known, skip VLM call on success.
            keyframes: Optional pre-rendered keyframes for VLM. If None, the
                callback is responsible for generating them from cached obs.
        """
        ep = self._episode
        T  = len(ep)
        if T == 0:
            return

        self.stats["episodes_seen"] += 1

        # Decide whether to query VLM for counterfactual goals.
        cf_list: Optional[List[Counterfactual]] = None
        is_failure = (episode_success is False) or (episode_success is None)

        if is_failure:
            self.stats["episodes_failed"] += 1

        should_call_vlm = (
            is_failure
            and self.p_counterfactual > 0.0
            and (self.stats["episodes_failed"] % self.cf_call_interval == 0)
        )

        if should_call_vlm:
            cf_list = self._query_vlm(ep, keyframes)
            self.stats["vlm_calls"] += 1
            if cf_list is None or len(cf_list) == 0:
                self.stats["vlm_returned_none"] += 1
                cf_list = None
            else:
                # Drop low-confidence counterfactuals.
                pre_n = len(cf_list)
                cf_list = [
                    (k_i, g, c) for (k_i, g, c) in cf_list
                    if c >= self.min_confidence
                ]
                self.stats["low_conf_dropped"] += (pre_n - len(cf_list))
                if len(cf_list) == 0:
                    cf_list = None
                else:
                    # CF-deviation diagnostics: for each accepted CF, log how
                    # far the proposed corrective_position lies from
                    #   (a) the original desired_goal       — teleport collapse
                    #       signal: small ⇒ VLM is just regurgitating the goal.
                    #   (b) the actual achieved_goal at frame K — "stay the
                    #       course" signal: small ⇒ VLM is suggesting we
                    #       continue doing what we already did (useless).
                    # The productive regime sits between the two.
                    self._update_cf_deviation_stats(ep, cf_list)

        # Standard HER loop, augmented with per-relabel counterfactual draws.
        for t, tr in enumerate(ep):
            for _ in range(self.k):
                use_cf = (
                    cf_list is not None
                    and np.random.random() < self.p_counterfactual
                )
                relabel_goal = self._draw_relabel_goal(
                    t=t,
                    T=T,
                    ep=ep,
                    cf_list=cf_list,
                    use_cf=use_cf,
                )
                if relabel_goal is None:
                    # No usable goal AND fallback disabled → skip.
                    continue

                self._push_relabeled(tr, relabel_goal, compute_reward_fn)

        self._episode = []

    # ── private helpers (skeletons) ─────────────────────────────────────────

    def _query_vlm(
        self,
        ep: List[dict],
        keyframes: Optional[List],
    ) -> Optional[List[Counterfactual]]:
        """Build inputs and call the CF provider.

        For `cf_input_kind == 'vlm'` (default), the callback receives the
        (achieved_goals, desired_goal, keyframes) tuple — matches the C1
        signature.

        For `cf_input_kind == 'state'`, the callback receives a single
        trajectory dict carrying ee_pos, object_pos, actions, achieved
        and desired goal arrays — for hand-coded oracle counterfactuals.
        """
        achieved = np.stack([tr["achieved_goal"] for tr in ep])
        # The desired_goal is in the last goal_dim entries of obs.
        desired  = ep[0]["obs"][-self.goal_dim:].astype(np.float32)
        # End-effector positions (Fetch obs convention: obs[0:3] is grip_pos).
        # Numeric prompt variants consume this; non-numeric providers ignore
        # the extra kwarg via **_unused_kwargs in their signatures.
        try:
            ee_positions = np.stack([
                np.asarray(tr["obs"][0:3], dtype=np.float32) for tr in ep
            ])
        except Exception:  # noqa: BLE001 — never crash for diagnostics.
            ee_positions = None
        try:
            if self.cf_input_kind == "state":
                trajectory = self._build_trajectory_dict(ep, desired)
                return self.cf_fn(trajectory=trajectory)
            else:
                return self.cf_fn(
                    achieved_goals=achieved,
                    desired_goal=desired,
                    keyframes=keyframes,
                    ee_positions=ee_positions,
                )
        except Exception as e:  # noqa: BLE001
            # Never crash training because the VLM had a bad day. Count the
            # exception under its own key — finish_episode() will additionally
            # see `cf_list is None` and increment `vlm_returned_none`, so the
            # two counters together tell us "calls that yielded no CFs"
            # (vlm_returned_none) and "of those, which crashed" (vlm_exceptions).
            self.stats["vlm_exceptions"] += 1
            return None

    def _build_trajectory_dict(self, ep: List[dict], desired: np.ndarray) -> Dict[str, Any]:
        """Pack episode tensors for state-based CF providers (oracle).

        Layout assumes Fetch envs: obs vector is
        [obs_body(25), achieved_goal(3), desired_goal(3)] with the
        end-effector position at obs[0:3] (Fetch convention).
        """
        T = len(ep)
        obs        = np.stack([tr["obs"] for tr in ep]).astype(np.float32)
        actions    = np.stack([tr["action"] for tr in ep]).astype(np.float32)
        achieved   = np.stack([tr["achieved_goal"] for tr in ep]).astype(np.float32)
        next_ach   = np.stack([tr["next_achieved_goal"] for tr in ep]).astype(np.float32)
        # In Fetch obs vector: 0:3 = ee_pos; achieved_goal = object_pos.
        ee_pos     = obs[:, 0:3].copy()
        object_pos = achieved.copy()
        return {
            "obs":                obs,
            "actions":            actions,
            "achieved_goals":     achieved,
            "next_achieved_goals": next_ach,
            "ee_pos":             ee_pos,
            "object_pos":         object_pos,
            "desired_goal":       np.asarray(desired, dtype=np.float32),
            "T":                  T,
            "env_name":           self.env_name,
        }

    def _draw_relabel_goal(
        self,
        t: int,
        T: int,
        ep: List[dict],
        cf_list: Optional[List[Counterfactual]],
        use_cf: bool,
    ) -> Optional[np.ndarray]:
        """Pick one relabeling goal for transition `t`. Returns None to skip.

        Counterfactual draws are constrained on two axes:
          1. Causal: only use a counterfactual whose frame_index >= t (the
             corrective goal must be for a future frame, not relabel the past
             with an already-passed corrective state).
          2. Locality: only use CFs whose frame_index is within
             [t, t + cf_window]. Without this bound a transition at t=0 could
             be relabeled with a CF at frame K=40, which is a very-long-horizon
             credit assignment problem that washes out the local signal we
             want HER to give. `cf_window <= 0` disables the upper bound
             (recovers the old unbounded-forward behavior, useful for ablation).
        """
        if use_cf and cf_list is not None:
            # Apply causal + locality filters.
            if self.cf_window > 0:
                t_max = t + self.cf_window
                valid = [(k_i, g, c) for (k_i, g, c) in cf_list
                         if t <= k_i <= t_max]
            else:
                valid = [(k_i, g, c) for (k_i, g, c) in cf_list if k_i >= t]
            if len(valid) > 0:
                valid.sort(key=lambda x: x[0])  # ascending frame index
                # Bias: pick the *nearest upcoming* CF with the higher confidence.
                weights = np.array([c / max(1, (k_i - t + 1))
                                    for (k_i, _, c) in valid], dtype=np.float64)
                weights = weights / weights.sum() if weights.sum() > 0 else None
                idx = (np.random.choice(len(valid), p=weights)
                       if weights is not None else np.random.randint(len(valid)))
                _, goal, _ = valid[idx]
                self.stats["cf_relabels_used"] += 1
                return np.asarray(goal, dtype=np.float32)
            elif not self.fallback_to_achieved:
                return None
            # else: fall through to achieved-future

        # Standard HER "future" relabel.
        if T - t <= 0:
            return None
        fi = np.random.randint(t, T)
        self.stats["achieved_relabels_used"] += 1
        return np.asarray(ep[fi]["achieved_goal"], dtype=np.float32)

    def _push_relabeled(
        self,
        tr: dict,
        new_goal: np.ndarray,
        compute_reward_fn: Callable[..., float],
    ):
        """Build the relabeled (s, a, r, s', d) tuple and push it.

        Mirrors HERBuffer.finish_episode push logic exactly — only the
        source of `new_goal` differs.
        """
        new_obs      = tr["obs"].copy()
        new_next_obs = tr["next_obs"].copy()
        new_obs[-self.goal_dim:]      = new_goal
        new_next_obs[-self.goal_dim:] = new_goal

        new_reward = float(compute_reward_fn(
            tr["next_achieved_goal"], new_goal, {}
        ))

        self.buffer.push(
            new_obs, tr["action"], new_reward, new_next_obs, tr["done"]
        )

    # ── CF deviation diagnostics ────────────────────────────────────────────

    def _update_cf_deviation_stats(
        self,
        ep: List[dict],
        cf_list: List[Counterfactual],
    ) -> None:
        """Update running-mean accumulators for CF deviation diagnostics.

        For each accepted (frame_index_K, corrective_position, _confidence)
        we increment three running totals:
          - sum_to_desired:  ||cp - desired_goal||
          - sum_to_achieved: ||cp - achieved_goal_at_K||
          - in_workspace_count: 1 if cp within Fetch bounds, 0 otherwise
        and the denominator `cf_accepted_count`. Variants that do not emit a
        `corrective_position` (narrative, action-only) yield CFs that we
        cannot evaluate here — those are skipped silently.
        """
        if len(ep) == 0:
            return
        T = len(ep)
        # desired_goal lives in the last goal_dim slots of obs.
        try:
            desired = np.asarray(
                ep[0]["obs"][-self.goal_dim:], dtype=np.float32
            )
        except Exception:
            return

        for entry in cf_list:
            # Robust unpack: oracle/VLM return 3-tuples; some providers may
            # return 4-tuples with an extra action. We only need the first
            # three fields here.
            if len(entry) == 3:
                k_i, cp, _c = entry
            elif len(entry) >= 4:
                k_i, cp, _c, *_rest = entry
            else:
                continue
            cp_arr = np.asarray(cp, dtype=np.float32)
            if cp_arr is None or cp_arr.size != self.goal_dim:
                # variant=narrative or action-only would not get this far
                # (cf_list construction would not include a position) — but
                # be defensive in case a provider drops the field.
                continue

            k_clamped = int(np.clip(int(k_i), 0, T - 1))
            try:
                ach_at_K = np.asarray(
                    ep[k_clamped]["achieved_goal"], dtype=np.float32
                )
            except Exception:
                continue

            d_des = float(np.linalg.norm(cp_arr - desired))
            d_ach = float(np.linalg.norm(cp_arr - ach_at_K))
            in_ws = int(
                np.all(cp_arr >= self._workspace_lo)
                and np.all(cp_arr <= self._workspace_hi)
            )

            self._cf_dev_sum_to_desired  += d_des
            self._cf_dev_sum_to_achieved += d_ach
            self.stats["cf_in_workspace_count"] += in_ws
            self.stats["cf_accepted_count"]     += 1

    def reset_cf_deviation_stats(self) -> None:
        """Zero the CF deviation running totals.

        Useful when train.py wants per-window snapshots (e.g. one mean per
        episode rather than one running mean from training start). Counters
        for `cf_accepted_count` / `cf_in_workspace_count` are reset together
        with the float sums so the means stay consistent.
        """
        self._cf_dev_sum_to_desired  = 0.0
        self._cf_dev_sum_to_achieved = 0.0
        self.stats["cf_accepted_count"]     = 0
        self.stats["cf_in_workspace_count"] = 0

    def get_cf_deviation_stats(self) -> Dict[str, float]:
        """Return running-mean CF deviation diagnostics (empty when no CFs).

        Keys emitted (when at least one CF has been accepted):
          - buffer/cf_corrective_pos_to_desired_dist
          - buffer/cf_corrective_pos_to_achieved_dist
          - buffer/cf_corrective_pos_in_workspace
          - buffer/cf_accepted_count
        """
        n = int(self.stats.get("cf_accepted_count", 0))
        if n <= 0:
            return {}
        return {
            "buffer/cf_corrective_pos_to_desired_dist":
                self._cf_dev_sum_to_desired / n,
            "buffer/cf_corrective_pos_to_achieved_dist":
                self._cf_dev_sum_to_achieved / n,
            "buffer/cf_corrective_pos_in_workspace":
                float(self.stats.get("cf_in_workspace_count", 0)) / n,
            "buffer/cf_accepted_count": float(n),
        }

    # ── diagnostics ─────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, int]:
        """Return accumulator dict for W&B logging."""
        return dict(self.stats)

    def get_per_stats(self) -> Dict[str, float]:
        """PER-specific diagnostics surfaced to train.py / W&B.

        Returns an empty dict when the underlying buffer is uniform.
        When priority_mode == 'prioritized' and the underlying buffer
        exposes PER internals (beta, _max_priority, _sum_tree), emit:
          - per_beta:               current IS-correction exponent
          - per_max_priority:       running max raw priority seen
          - per_sum_tree_total:     sum of all leaf priorities (≈ N * mean_p^α)
          - per_sum_tree_size:      leaf-tree capacity
          - per_buffer_size:        current number of stored transitions
        """
        if self.priority_mode != "prioritized":
            return {}
        b = self.buffer
        out: Dict[str, float] = {}
        if hasattr(b, "beta"):
            out["per_beta"] = float(b.beta)
        if hasattr(b, "_max_priority"):
            out["per_max_priority"] = float(b._max_priority)
        if hasattr(b, "_sum_tree"):
            try:
                out["per_sum_tree_total"] = float(b._sum_tree.total)
                out["per_sum_tree_size"]  = float(b._sum_tree.capacity)
            except Exception:
                pass
        out["per_buffer_size"] = float(len(b))
        return out
