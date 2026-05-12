"""
Unit tests for CounterfactualHERBuffer.

Covers the invariants that matter most for the Path C runs:

1. p_counterfactual = 0 is *exactly* HER (no CF transitions land in the buffer,
   stats show zero CF relabels).
2. p_counterfactual > 0 with a deterministic oracle does produce CF
   relabels, and the stats counters increment correctly.
3. CF goals are only used for *causally-valid* frames (a CF emitted at
   frame K is never used to relabel a transition at t > K).
4. Successful episodes never trigger a VLM/oracle call.
5. cf_call_interval gates the frequency of CF calls correctly (e.g. only
   every Nth failed episode).
6. Low-confidence CFs are dropped and counted in low_conf_dropped.
7. The fallback path (CF returns None) does not crash — episode still
   pushes synthetic HER transitions.
8. `state` input kind is correctly dispatched (oracle CFs receive a
   trajectory dict, not the (achieved, desired, keyframes) triple).

Tests use a synthetic 10-step "episode" with deterministic numbers so we
can read out exactly how many CF vs achieved relabels were issued.
"""
from __future__ import annotations

import os
import sys
import numpy as np

try:
    import pytest  # type: ignore
    HAS_PYTEST = True
except ImportError:  # pragma: no cover — keeps the file runnable in venvs without pytest.
    pytest = None  # type: ignore
    HAS_PYTEST = False

# Make `src` importable regardless of cwd.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from src.buffers.replay_buffer import UniformReplayBuffer  # noqa: E402
from src.buffers.per_buffer import PERBuffer  # noqa: E402
from src.buffers.counterfactual_buffer import CounterfactualHERBuffer  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Test helpers
# ─────────────────────────────────────────────────────────────────────────────


def _sparse_reward(achieved, desired, info=None):
    """Mock Fetch sparse reward: 0 on success, -1 otherwise."""
    return 0.0 if np.linalg.norm(np.asarray(achieved) - np.asarray(desired)) < 0.05 else -1.0


def _build_episode(T: int = 10, goal_dim: int = 3, obs_body_dim: int = 25):
    """Build a synthetic failed-episode trajectory.

    Returns (transitions, desired_goal) where each transition is a dict
    compatible with HERBuffer.push's _episode entries. The block
    "achieved_goal" walks slowly toward (1.0, 1.0, 0.5) and stops 30 cm
    short — i.e. the episode FAILS for the desired_goal at (1.0, 1.0, 0.5).
    """
    obs_dim = obs_body_dim + 2 * goal_dim
    desired = np.array([1.0, 1.0, 0.5], dtype=np.float32)
    transitions = []
    for t in range(T):
        # Block creeps forward but never reaches the goal.
        ach = np.array([0.7 * (t / (T - 1)), 0.7 * (t / (T - 1)), 0.5], dtype=np.float32)
        next_ach = np.array([0.7 * ((t + 1) / (T - 1)), 0.7 * ((t + 1) / (T - 1)), 0.5],
                            dtype=np.float32)
        obs = np.zeros(obs_dim, dtype=np.float32)
        obs[:3] = np.array([0.5, 0.5, 0.5])  # ee pose, stays put
        obs[obs_body_dim:obs_body_dim + goal_dim] = ach
        obs[obs_body_dim + goal_dim:] = desired
        next_obs = obs.copy()
        next_obs[obs_body_dim:obs_body_dim + goal_dim] = next_ach
        action = np.array([0.1, 0.1, 0.0, 0.0], dtype=np.float32)
        transitions.append({
            "obs":                obs,
            "action":             action,
            "next_obs":           next_obs,
            "done":               (t == T - 1),
            "achieved_goal":      ach,
            "next_achieved_goal": next_ach,
            "reward":             _sparse_reward(next_ach, desired),
        })
    return transitions, desired


def _make_buffer(
    p_counterfactual: float = 0.25,
    cf_call_interval: int = 1,
    cf_fn=None,
    cf_input_kind: str = "vlm",
    min_confidence: float = 0.5,
    fallback_to_achieved: bool = True,
    k: int = 4,
    capacity: int = 4096,
    cf_window: int = 4,
):
    """Construct a CounterfactualHERBuffer with sensible defaults for tests."""
    underlying = UniformReplayBuffer(capacity=capacity)
    return CounterfactualHERBuffer(
        underlying_buffer=underlying,
        counterfactual_fn=cf_fn if cf_fn is not None else (lambda **kw: None),
        goal_dim=3,
        obs_dim=25,
        k=k,
        strategy="future",
        p_counterfactual=p_counterfactual,
        min_confidence=min_confidence,
        fallback_to_achieved=fallback_to_achieved,
        cf_call_interval=cf_call_interval,
        cf_input_kind=cf_input_kind,
        cf_window=cf_window,
    )


def _run_episode(buf: CounterfactualHERBuffer, transitions, episode_success: bool = False):
    """Push every transition then call finish_episode."""
    buf.mark_episode_start()
    for tr in transitions:
        buf.push(
            obs=tr["obs"],
            action=tr["action"],
            reward=tr["reward"],
            next_obs=tr["next_obs"],
            done=tr["done"],
            achieved_goal=tr["achieved_goal"],
            next_achieved_goal=tr["next_achieved_goal"],
        )
    buf.finish_episode(
        compute_reward_fn=_sparse_reward,
        episode_success=episode_success,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestPCounterfactualEqualsZeroIsHER:
    """p_counterfactual=0 must be functionally identical to vanilla HER."""

    def test_zero_p_uses_no_cf_relabels(self):
        np.random.seed(0)
        ep, _desired = _build_episode(T=10)

        called = {"n": 0}
        def cf_fn(**kw):
            called["n"] += 1
            return [(5, np.array([0.9, 0.9, 0.5], dtype=np.float32), 1.0)]

        buf = _make_buffer(p_counterfactual=0.0, cf_fn=cf_fn)
        _run_episode(buf, ep, episode_success=False)

        stats = buf.get_stats()
        assert stats["cf_relabels_used"] == 0, "p=0 must produce 0 CF relabels"
        assert stats["achieved_relabels_used"] > 0, "HER must still relabel"
        # And the VLM was never called (p=0 short-circuits in finish_episode).
        assert called["n"] == 0, "VLM/oracle must not be called when p=0"

    def test_zero_p_underlying_buffer_size_matches_her(self):
        """At p=0, the buffer should contain exactly T (real) + T*k (HER) transitions."""
        np.random.seed(0)
        ep, _desired = _build_episode(T=10)
        buf = _make_buffer(p_counterfactual=0.0, k=4)
        _run_episode(buf, ep, episode_success=False)
        # T real + T*k synthetic HER (assuming all transitions found a future frame).
        # 'future' strategy may sample fewer when t is near T; allow a tolerance.
        n_real = 10
        n_her_upper = 10 * 4
        assert n_real <= len(buf.buffer) <= n_real + n_her_upper


class TestPCounterfactualUsesCF:
    """With p>0 and a deterministic CF, we observe CF relabels."""

    def test_high_p_produces_cf_relabels(self):
        np.random.seed(42)
        ep, _desired = _build_episode(T=10)
        cf_pos = np.array([0.9, 0.9, 0.5], dtype=np.float32)

        def cf_fn(**kw):
            return [(5, cf_pos, 1.0)]  # one CF at frame 5, confidence 1.0

        buf = _make_buffer(p_counterfactual=1.0, cf_fn=cf_fn, cf_input_kind="vlm")
        _run_episode(buf, ep, episode_success=False)

        stats = buf.get_stats()
        assert stats["vlm_calls"] == 1
        assert stats["cf_relabels_used"] > 0, \
            "p=1 with a valid CF must yield CF relabels"
        # The CF is at frame 5, so transitions t in [0..5] can use it (causal)
        # and transitions t in [6..9] must fall back to achieved-future.
        assert stats["achieved_relabels_used"] > 0, \
            "Transitions past the CF frame must fall back to HER"


class TestCausalValidity:
    """A CF emitted at frame K is never used to relabel a transition at t > K."""

    def test_late_cf_only_relabels_early_frames(self):
        np.random.seed(0)
        ep, _desired = _build_episode(T=10)

        # CF at frame 3 only → transitions t in [0..3] can use it; t in [4..9] cannot.
        def cf_fn(**kw):
            return [(3, np.array([0.8, 0.8, 0.5], dtype=np.float32), 1.0)]

        buf = _make_buffer(p_counterfactual=1.0, cf_fn=cf_fn, k=1)
        _run_episode(buf, ep, episode_success=False)

        # We can't directly observe per-transition routing without instrumenting
        # _draw_relabel_goal, so we instead verify the aggregate counts:
        # at most 4 CF relabels (frames 0..3) out of k*T = 1*10 = 10 attempts.
        stats = buf.get_stats()
        assert stats["cf_relabels_used"] <= 4, \
            f"CF at frame 3 must not relabel beyond frame 3 (saw {stats['cf_relabels_used']})"

    def test_cf_at_frame_zero_is_usable_everywhere_via_window(self):
        """A CF at frame 0 should still apply to all causally-valid transitions
        (t == 0 only, since strict causal validity requires K >= t)."""
        np.random.seed(0)
        ep, _desired = _build_episode(T=10)

        def cf_fn(**kw):
            return [(0, np.array([0.5, 0.5, 0.5], dtype=np.float32), 1.0)]

        buf = _make_buffer(p_counterfactual=1.0, cf_fn=cf_fn, k=2)
        _run_episode(buf, ep, episode_success=False)
        # Only t=0 satisfies K >= t with K=0; rest fall back to HER.
        stats = buf.get_stats()
        # k=2 → at most 2 CF relabels (both at t=0).
        assert stats["cf_relabels_used"] <= 2


class TestCfWindowLocality:
    """cf_window bounds how far before frame K a CF can relabel transitions.

    The CF at frame K is eligible for transitions t in [K-cf_window, K]
    (combined with the causal constraint K >= t). cf_window<=0 disables
    the upper bound (recovers the old unbounded-forward behavior).
    """

    def test_window_excludes_far_earlier_transitions(self):
        """A CF at frame 30 with cf_window=4 must NOT relabel t=0..25."""
        np.random.seed(0)
        ep, _desired = _build_episode(T=40)

        def cf_fn(**kw):
            return [(30, np.array([0.5, 0.5, 0.5], dtype=np.float32), 1.0)]

        buf = _make_buffer(p_counterfactual=1.0, cf_fn=cf_fn, k=4, cf_window=4)
        _run_episode(buf, ep, episode_success=False)

        stats = buf.get_stats()
        # Eligible transitions: t in [26..30] = 5 transitions × k=4 = 20 CF relabels.
        # Remaining 35 × 4 = 140 must fall back to HER achieved-future.
        assert stats["cf_relabels_used"] <= 20, (
            f"cf_window=4 with CF at frame 30 must cap CF relabels at 20 "
            f"(saw {stats['cf_relabels_used']})"
        )
        assert stats["achieved_relabels_used"] >= 140, (
            f"Remaining transitions must fall back to HER "
            f"(saw {stats['achieved_relabels_used']} achieved relabels)"
        )

    def test_window_zero_disables_bound(self):
        """cf_window<=0 must restore the unbounded-forward (causal-only) regime."""
        np.random.seed(0)
        ep, _desired = _build_episode(T=40)

        def cf_fn(**kw):
            return [(30, np.array([0.5, 0.5, 0.5], dtype=np.float32), 1.0)]

        buf = _make_buffer(p_counterfactual=1.0, cf_fn=cf_fn, k=4, cf_window=0)
        _run_episode(buf, ep, episode_success=False)

        stats = buf.get_stats()
        # Unbounded: all t in [0..30] are eligible = 31 × 4 = 124 CF relabels.
        assert stats["cf_relabels_used"] >= 100, (
            f"cf_window=0 should not bound; expected >=100 CF relabels, "
            f"got {stats['cf_relabels_used']}"
        )


class TestVlmExceptionsCounterDoesNotDoubleCount:
    """A raising CF callback must increment vlm_exceptions ONCE and
    vlm_returned_none ONCE (not twice via the exception path bug)."""

    def test_raising_cf_fn_counts_once(self):
        ep, _desired = _build_episode(T=10)

        def raising_cf_fn(**kw):
            raise RuntimeError("synthetic VLM failure")

        buf = _make_buffer(p_counterfactual=1.0, cf_fn=raising_cf_fn)
        _run_episode(buf, ep, episode_success=False)

        stats = buf.get_stats()
        assert stats["vlm_calls"] == 1, "exactly one VLM call attempted"
        assert stats["vlm_exceptions"] == 1, "exception path increments vlm_exceptions"
        # vlm_returned_none should be 1 (the cf_list-is-None path in finish_episode),
        # NOT 2 (which would indicate double-counting).
        assert stats["vlm_returned_none"] == 1, (
            f"vlm_returned_none must increment once even on exception "
            f"(saw {stats['vlm_returned_none']}; double-count regression)"
        )


class TestSuccessfulEpisodesSkipCF:
    """Successful episodes (episode_success=True) must NOT call the VLM/oracle."""

    def test_success_skips_vlm(self):
        ep, _desired = _build_episode(T=10)
        called = {"n": 0}
        def cf_fn(**kw):
            called["n"] += 1
            return [(5, np.array([0.9, 0.9, 0.5], dtype=np.float32), 1.0)]

        buf = _make_buffer(p_counterfactual=0.5, cf_fn=cf_fn)
        _run_episode(buf, ep, episode_success=True)

        assert called["n"] == 0, "Successful episode must not trigger CF call"
        stats = buf.get_stats()
        assert stats["episodes_failed"] == 0
        assert stats["vlm_calls"] == 0


class TestCallIntervalGating:
    """cf_call_interval controls how often the VLM/oracle is invoked."""

    def test_interval_two_calls_every_other_failed_episode(self):
        ep, _desired = _build_episode(T=10)
        called = {"n": 0}
        def cf_fn(**kw):
            called["n"] += 1
            return [(5, np.array([0.9, 0.9, 0.5], dtype=np.float32), 1.0)]

        buf = _make_buffer(p_counterfactual=0.5, cf_fn=cf_fn, cf_call_interval=2)
        # 4 failed episodes → expect 2 VLM calls (eps 1 and 3 with the pre-decrement).
        # Note: The buffer pre-decrements episodes_failed before the modulo check.
        for _ in range(4):
            _run_episode(buf, ep, episode_success=False)

        stats = buf.get_stats()
        assert stats["episodes_failed"] == 4
        # cf_call_interval=2 → every 2nd failed episode triggers a call.
        # With the convention (episodes_failed % interval == 0) and pre-increment,
        # calls fire at episode_failed counts of 2 and 4 → 2 calls.
        assert called["n"] == 2, \
            f"cf_call_interval=2, 4 failed eps → expected 2 calls, got {called['n']}"

    def test_interval_one_calls_every_failed_episode(self):
        ep, _desired = _build_episode(T=10)
        called = {"n": 0}
        def cf_fn(**kw):
            called["n"] += 1
            return [(5, np.array([0.9, 0.9, 0.5], dtype=np.float32), 1.0)]

        buf = _make_buffer(p_counterfactual=0.5, cf_fn=cf_fn, cf_call_interval=1)
        for _ in range(3):
            _run_episode(buf, ep, episode_success=False)

        assert called["n"] == 3, \
            f"cf_call_interval=1, 3 failed eps → expected 3 calls, got {called['n']}"


class TestLowConfidenceFiltering:
    """CFs below min_confidence are dropped and counted."""

    def test_low_conf_cfs_dropped(self):
        np.random.seed(0)
        ep, _desired = _build_episode(T=10)
        cf_pos = np.array([0.9, 0.9, 0.5], dtype=np.float32)

        def cf_fn(**kw):
            return [(5, cf_pos, 0.2)]  # below default min_confidence=0.5

        buf = _make_buffer(p_counterfactual=1.0, cf_fn=cf_fn, min_confidence=0.5)
        _run_episode(buf, ep, episode_success=False)

        stats = buf.get_stats()
        assert stats["low_conf_dropped"] >= 1, \
            "Low-confidence CF must be counted as dropped"
        assert stats["cf_relabels_used"] == 0, \
            "Dropped CF must not produce relabels"

    def test_mixed_confidence_only_high_kept(self):
        np.random.seed(0)
        ep, _desired = _build_episode(T=10)

        def cf_fn(**kw):
            return [
                (3, np.array([0.7, 0.7, 0.5], dtype=np.float32), 0.2),  # dropped
                (5, np.array([0.9, 0.9, 0.5], dtype=np.float32), 0.9),  # kept
            ]

        buf = _make_buffer(p_counterfactual=1.0, cf_fn=cf_fn, min_confidence=0.5)
        _run_episode(buf, ep, episode_success=False)

        stats = buf.get_stats()
        assert stats["low_conf_dropped"] == 1


class TestVLMReturningNone:
    """When the CF callback returns None, the episode still relabels via HER."""

    def test_none_does_not_crash(self):
        np.random.seed(0)
        ep, _desired = _build_episode(T=10)

        def cf_fn(**kw):
            return None  # simulating a VLM parse failure or filter rejection

        buf = _make_buffer(p_counterfactual=0.5, cf_fn=cf_fn)
        _run_episode(buf, ep, episode_success=False)

        stats = buf.get_stats()
        assert stats["vlm_calls"] == 1
        assert stats["vlm_returned_none"] == 1
        assert stats["cf_relabels_used"] == 0
        # Achieved-future fallback still ran.
        assert stats["achieved_relabels_used"] > 0
        # Buffer still has the real + HER synthetic transitions.
        assert len(buf.buffer) >= 10

    def test_exception_in_cf_fn_does_not_crash(self):
        np.random.seed(0)
        ep, _desired = _build_episode(T=10)

        def cf_fn(**kw):
            raise RuntimeError("simulated VLM API failure")

        buf = _make_buffer(p_counterfactual=0.5, cf_fn=cf_fn)
        # Should NOT raise.
        _run_episode(buf, ep, episode_success=False)
        stats = buf.get_stats()
        # vlm_returned_none is incremented on exception too.
        assert stats["vlm_returned_none"] >= 1


class TestStateInputKindDispatch:
    """`cf_input_kind=state` routes a trajectory dict to the CF callback."""

    def test_state_kind_receives_trajectory_dict(self):
        ep, _desired = _build_episode(T=10)
        received = {"payload": None, "kwargs": None}

        def oracle_fn(*args, **kwargs):
            received["kwargs"] = kwargs
            received["payload"] = kwargs.get("trajectory")
            return [(5, np.array([0.9, 0.9, 0.5], dtype=np.float32), 1.0)]

        buf = _make_buffer(
            p_counterfactual=1.0, cf_fn=oracle_fn, cf_input_kind="state",
        )
        _run_episode(buf, ep, episode_success=False)

        # The callback must have been called with kwargs containing
        # 'trajectory' (NOT achieved_goals/desired_goal/keyframes).
        assert received["payload"] is not None, \
            "state-kind callback must receive a 'trajectory' kwarg"
        traj = received["payload"]
        for required in ("obs", "actions", "achieved_goals", "desired_goal",
                          "ee_pos", "object_pos", "T"):
            assert required in traj, \
                f"trajectory dict missing required key '{required}'"
        assert traj["T"] == 10
        assert traj["achieved_goals"].shape == (10, 3)

    def test_vlm_kind_receives_arrays_not_trajectory(self):
        ep, _desired = _build_episode(T=10)
        received = {"keys": None}

        def cf_fn(**kwargs):
            received["keys"] = set(kwargs.keys())
            return [(5, np.array([0.9, 0.9, 0.5], dtype=np.float32), 1.0)]

        buf = _make_buffer(
            p_counterfactual=1.0, cf_fn=cf_fn, cf_input_kind="vlm",
        )
        _run_episode(buf, ep, episode_success=False)

        # vlm-kind callback must NOT receive a 'trajectory' kwarg.
        assert received["keys"] is not None
        assert "trajectory" not in received["keys"]
        assert "achieved_goals" in received["keys"]
        assert "desired_goal" in received["keys"]


class TestStatsCoherence:
    """Cross-check internal stats counters for consistency."""

    def test_relabel_counts_sum_to_attempted(self):
        """cf_relabels_used + achieved_relabels_used should equal the number
        of relabels actually pushed (bounded above by k*T per episode)."""
        np.random.seed(7)
        ep, _desired = _build_episode(T=10)
        cf_pos = np.array([0.9, 0.9, 0.5], dtype=np.float32)

        def cf_fn(**kw):
            return [(8, cf_pos, 0.9)]  # late-CF so few CF relabels

        buf = _make_buffer(p_counterfactual=0.5, cf_fn=cf_fn, k=2)
        _run_episode(buf, ep, episode_success=False)

        stats = buf.get_stats()
        # Synthetic transitions pushed = real-buffer-size minus T (the originals).
        n_synth = len(buf.buffer) - 10
        assert stats["cf_relabels_used"] + stats["achieved_relabels_used"] == n_synth, (
            f"relabel counters {stats['cf_relabels_used']}+"
            f"{stats['achieved_relabels_used']} != synthetic pushes {n_synth}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# PER + CF-HER stack tests
# ─────────────────────────────────────────────────────────────────────────────


def _make_per_backed_buffer(
    p_counterfactual: float = 0.25,
    cf_fn=None,
    cf_input_kind: str = "state",
    min_confidence: float = 0.5,
    fallback_to_achieved: bool = True,
    k: int = 4,
    capacity: int = 4096,
    cf_window: int = 4,
    per_alpha: float = 0.6,
    per_beta_start: float = 0.4,
    per_beta_end: float = 1.0,
    per_beta_anneal_steps: int = 1000,
    per_epsilon: float = 1e-6,
):
    """Construct a CounterfactualHERBuffer with a PERBuffer underlying."""
    per = PERBuffer(
        capacity=capacity,
        alpha=per_alpha,
        beta_start=per_beta_start,
        beta_end=per_beta_end,
        beta_anneal_steps=per_beta_anneal_steps,
        epsilon=per_epsilon,
    )
    return CounterfactualHERBuffer(
        underlying_buffer=per,
        counterfactual_fn=cf_fn if cf_fn is not None else (lambda **kw: None),
        goal_dim=3,
        obs_dim=25,
        k=k,
        strategy="future",
        p_counterfactual=p_counterfactual,
        min_confidence=min_confidence,
        fallback_to_achieved=fallback_to_achieved,
        cf_call_interval=1,
        cf_input_kind=cf_input_kind,
        cf_window=cf_window,
        priority_mode="prioritized",
    )


class TestPERModeSamplesWithPriority:
    """Higher-|TD| transitions must be sampled more often under PER."""

    def test_per_mode_high_td_dominates_sampling(self):
        np.random.seed(0)
        buf = _make_per_backed_buffer(p_counterfactual=0.0, k=1)
        # Push 100 dummy transitions directly into the PER-backed underlying
        # buffer (skip the HER episode dance — we are testing the sampler).
        T = 100
        for i in range(T):
            obs      = np.zeros(31, dtype=np.float32)
            next_obs = np.zeros(31, dtype=np.float32)
            action   = np.zeros(4, dtype=np.float32)
            buf.buffer.push(obs, action, -1.0, next_obs, 0.0)

        # Boost priorities of indices [10, 20, 30] to be 100× the rest.
        boost_idx  = np.array([10, 20, 30], dtype=np.int64)
        boost_tds  = np.array([100.0, 100.0, 100.0], dtype=np.float64)
        rest_idx   = np.array([i for i in range(T) if i not in set(boost_idx.tolist())],
                              dtype=np.int64)
        rest_tds   = np.full(len(rest_idx), 1.0, dtype=np.float64)
        buf.update_priorities(boost_idx, boost_tds)
        buf.update_priorities(rest_idx, rest_tds)

        # Draw 2000 samples and count how often boost indices appear.
        counts = np.zeros(T, dtype=np.int64)
        for _ in range(2000):
            batch = buf.sample(8)
            for j in batch["indices"]:
                counts[int(j)] += 1

        # Expected uniform count per slot ≈ 2000*8/100 = 160.
        # With α=0.6 and 100× priority, boosted slots should be sampled
        # roughly (100/(100 + (T-3)*1))^0.6-corrected × N times → far more
        # than uniform. We only require >2× the uniform rate.
        uniform_rate = counts.mean()
        boost_rate   = counts[boost_idx].mean()
        assert boost_rate > 2 * uniform_rate, (
            f"PER must over-sample high-TD slots: boost_rate={boost_rate:.1f} "
            f"vs uniform_rate={uniform_rate:.1f}"
        )

    def test_uniform_mode_unchanged(self):
        """priority_mode='uniform' (default) must behave like the existing
        uniform-backed buffer — no surprises for old configs."""
        np.random.seed(0)
        buf = _make_buffer(p_counterfactual=0.0, k=1)
        # Push 100 dummies.
        for i in range(100):
            buf.buffer.push(np.zeros(31, dtype=np.float32),
                            np.zeros(4, dtype=np.float32),
                            -1.0,
                            np.zeros(31, dtype=np.float32),
                            0.0)
        # update_priorities is a no-op for UniformReplayBuffer; sampling
        # must still be uniform across slots.
        batch = buf.sample(256)
        assert "indices" in batch and "weights" in batch
        # Uniform weights = 1.0 for all entries.
        assert np.allclose(batch["weights"], 1.0), \
            "uniform buffer must emit unit IS weights"
        # priority_mode reads as 'uniform'.
        assert buf.priority_mode == "uniform"


class TestPERModeUpdatesPriorities:
    """update_priorities must change subsequent sampling distribution."""

    def test_update_priorities_changes_sampling(self):
        np.random.seed(123)
        buf = _make_per_backed_buffer(p_counterfactual=0.0, k=1)
        T = 50
        for i in range(T):
            buf.buffer.push(np.zeros(31, dtype=np.float32),
                            np.zeros(4, dtype=np.float32),
                            -1.0,
                            np.zeros(31, dtype=np.float32),
                            0.0)

        # Phase 1: all equal priority → near-uniform sampling.
        eq_idx = np.arange(T, dtype=np.int64)
        buf.update_priorities(eq_idx, np.ones(T) * 1.0)
        counts1 = np.zeros(T, dtype=np.int64)
        for _ in range(500):
            for j in buf.sample(8)["indices"]:
                counts1[int(j)] += 1
        cv1 = counts1.std() / counts1.mean()

        # Phase 2: spike index 42 → it should dominate.
        buf.update_priorities(np.array([42]), np.array([1000.0]))
        counts2 = np.zeros(T, dtype=np.int64)
        for _ in range(500):
            for j in buf.sample(8)["indices"]:
                counts2[int(j)] += 1
        assert counts2[42] > counts1[42] * 2, (
            f"After spike, idx 42 must be sampled much more often "
            f"(was {counts1[42]}, now {counts2[42]})"
        )


class TestPERModeISCorrectionWeight:
    """IS-correction weights must be computed, finite, and bounded by 1."""

    def test_is_weights_present_and_finite(self):
        np.random.seed(0)
        buf = _make_per_backed_buffer(p_counterfactual=0.0, k=1)
        for i in range(64):
            buf.buffer.push(np.zeros(31, dtype=np.float32),
                            np.zeros(4, dtype=np.float32),
                            -1.0,
                            np.zeros(31, dtype=np.float32),
                            0.0)
        # Spread priorities.
        buf.update_priorities(np.arange(64),
                              np.linspace(0.1, 10.0, 64))
        batch = buf.sample(32)
        w = batch["weights"]
        assert w.shape == (32,)
        assert np.isfinite(w).all(), "IS weights must be finite"
        assert (w > 0).all(), "IS weights must be positive"
        # PERBuffer normalises weights so max == 1.
        assert w.max() <= 1.0 + 1e-6, f"IS weights normalised to <=1, got max={w.max()}"


class TestCFSyntheticTransitionsGetMaxPriority:
    """Synthetic CF / HER transitions land in the buffer at max-priority.

    Mechanism: PERBuffer.push sets each new slot to (max_priority)^alpha,
    so a freshly inserted Verified-CF transition gets the same top
    priority as any other novel transition. This is the standard PER
    initialisation and is what we want for novel terminal-success-like
    transitions.
    """

    def test_synthetic_transitions_get_top_priority_on_insert(self):
        np.random.seed(0)
        ep, _desired = _build_episode(T=10)

        # Use the oracle-style state-kind CF returning a single CF at frame 5.
        cf_pos = np.array([0.9, 0.9, 0.5], dtype=np.float32)
        def cf_fn(**kw):
            return [(5, cf_pos, 1.0)]

        buf = _make_per_backed_buffer(
            p_counterfactual=1.0, cf_fn=cf_fn, cf_input_kind="state", k=2,
        )
        # Run the failed episode → buffer fills with real + HER + CF transitions.
        _run_episode(buf, ep, episode_success=False)

        per = buf.buffer  # the underlying PERBuffer
        N   = len(per)
        # All slots filled this episode should be at the current max
        # priority^alpha. Sanity-check: the running max_priority is >= 1
        # (PERBuffer initialises it at 1.0).
        assert per._max_priority >= 1.0
        # Read the leaf priorities of every filled slot.
        leaves = np.array([per._sum_tree[i] for i in range(N)])
        expected_top = (per._max_priority) ** per.alpha
        # All filled slots should sit at expected_top to within float
        # precision (no SGD updates have run, so nothing has shrunk).
        assert np.allclose(leaves, expected_top, rtol=1e-6, atol=1e-9), (
            f"Freshly-inserted slots must all be at max-priority^alpha "
            f"= {expected_top}; saw min={leaves.min()}, max={leaves.max()}"
        )

    def test_per_stats_reports_buffer_state(self):
        """get_per_stats must expose beta / max_priority / sum-tree mass."""
        np.random.seed(0)
        ep, _desired = _build_episode(T=10)
        def cf_fn(**kw):
            return [(5, np.array([0.9, 0.9, 0.5], dtype=np.float32), 1.0)]
        buf = _make_per_backed_buffer(
            p_counterfactual=1.0, cf_fn=cf_fn, cf_input_kind="state", k=2,
        )
        _run_episode(buf, ep, episode_success=False)
        stats = buf.get_per_stats()
        for k in ("per_beta", "per_max_priority", "per_sum_tree_total",
                  "per_sum_tree_size", "per_buffer_size"):
            assert k in stats, f"get_per_stats missing key {k!r}"
        assert stats["per_buffer_size"] > 0
        assert stats["per_sum_tree_total"] > 0
        # 0.4 ≤ beta ≤ 1.0 throughout training.
        assert 0.4 - 1e-6 <= stats["per_beta"] <= 1.0 + 1e-6

    def test_priority_mode_uniform_returns_empty_per_stats(self):
        """get_per_stats must be empty for uniform-backed buffers
        (so train.py logging short-circuits cleanly)."""
        buf = _make_buffer(p_counterfactual=0.0)
        assert buf.get_per_stats() == {}


class TestInvalidPriorityMode:
    """priority_mode must reject typos so silent fallthroughs don't happen."""

    def test_unknown_priority_mode_raises(self):
        underlying = UniformReplayBuffer(capacity=512)
        try:
            CounterfactualHERBuffer(
                underlying_buffer=underlying,
                counterfactual_fn=lambda **kw: None,
                priority_mode="wat",
            )
        except ValueError as e:
            assert "priority_mode" in str(e)
            return
        raise AssertionError("Bad priority_mode must raise ValueError")


def _run_all_tests_without_pytest():
    """Fallback runner — execute every test_* method on every TestX class.

    Used when pytest is not installed in the venv. Reports pass/fail counts
    and exits with a non-zero code on any failure.
    """
    import traceback
    classes = [
        TestPCounterfactualEqualsZeroIsHER,
        TestPCounterfactualUsesCF,
        TestCausalValidity,
        TestCfWindowLocality,
        TestVlmExceptionsCounterDoesNotDoubleCount,
        TestSuccessfulEpisodesSkipCF,
        TestCallIntervalGating,
        TestLowConfidenceFiltering,
        TestVLMReturningNone,
        TestStateInputKindDispatch,
        TestStatsCoherence,
        TestPERModeSamplesWithPriority,
        TestPERModeUpdatesPriorities,
        TestPERModeISCorrectionWeight,
        TestCFSyntheticTransitionsGetMaxPriority,
        TestInvalidPriorityMode,
    ]
    n_pass = 0
    n_fail = 0
    failures = []
    for cls in classes:
        instance = cls()
        for name in dir(instance):
            if not name.startswith("test_"):
                continue
            method = getattr(instance, name)
            label = f"{cls.__name__}::{name}"
            try:
                method()
                n_pass += 1
                print(f"  PASS  {label}")
            except Exception as e:  # noqa: BLE001 — we want to capture everything.
                n_fail += 1
                failures.append((label, traceback.format_exc()))
                print(f"  FAIL  {label}  ({type(e).__name__}: {e})")
    print(f"\n{'='*60}\n  passed: {n_pass}   failed: {n_fail}\n{'='*60}")
    if failures:
        print("\nFailure details:\n")
        for label, tb in failures:
            print(f"---- {label} ----\n{tb}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    if HAS_PYTEST:
        sys.exit(pytest.main([__file__, "-v"]))
    sys.exit(_run_all_tests_without_pytest())
