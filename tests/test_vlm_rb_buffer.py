"""
Unit tests for :class:`src.buffers.vlm_rb_buffer.VLMRBBuffer`.

Covers the invariants that matter for our Sharony-VLM-RB reproduction:

 1. Buffer mechanics: push/sample/update_priorities run end-to-end on a
    100-transition synthetic episode.
 2. Clip formation: episodes are partitioned into ⌈T/L⌉ contiguous clips
    and every transition within a clip receives the same p_VLM score.
 3. Score caching: ``apply_vlm_rb_scoring`` with ``force_scores=[...]``
    writes the per-clip scores into the right buffer slots.
 4. Priority update: ``update_priorities`` re-blends to
    ``(|TD| · p_VLM + ε)^α`` so a clip with score 0.0 has lower
    priority than one with score 1.0 at equal |TD|.
 5. Mixture-with-uniform sampling: with λ_t=0 the buffer samples
    uniformly; with λ_t=1 it samples by priority (high-score clips
    over-sampled vs. low-score clips at equal |TD|).
 6. λ_t anneal: after ``mixture_anneal_steps`` sample() calls, λ_t hits
    ``mixture_lambda_end``.
 7. Stub-scorer integration: invoking ``apply_vlm_rb_scoring`` *without*
    ``force_scores`` and with a stub scorer still updates priorities and
    bumps the call-count counter.

All tests run on a tiny buffer (capacity 512, clip_length 8) so the
suite is sub-second.
"""
from __future__ import annotations

import os
import sys

import numpy as np

try:
    import pytest  # type: ignore
    HAS_PYTEST = True
except ImportError:  # pragma: no cover
    pytest = None  # type: ignore
    HAS_PYTEST = False

# Make `src` importable regardless of cwd.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from src.buffers.vlm_rb_buffer import VLMRBBuffer  # noqa: E402
from src.vlm.vlm_rb_scorer import make_stub_scorer  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _push_episode(buf: VLMRBBuffer, T: int, obs_dim: int = 4, action_dim: int = 2):
    """Push a synthetic T-step episode and return the start ring-buffer index."""
    buf.mark_episode_start()
    start = buf._ptr
    rng = np.random.default_rng(0)
    for t in range(T):
        obs = rng.normal(size=obs_dim).astype(np.float32)
        action = rng.normal(size=action_dim).astype(np.float32)
        next_obs = rng.normal(size=obs_dim).astype(np.float32)
        reward = float(rng.normal())
        done = float(t == T - 1)
        buf.push(obs, action, reward, next_obs, done)
    return start


def _make_buffer(**overrides) -> VLMRBBuffer:
    kwargs = dict(
        capacity=512,
        alpha=0.6,
        beta_start=0.4,
        beta_end=1.0,
        beta_anneal_steps=10_000,
        epsilon=1e-6,
        clip_length=8,
        vlm_score_fn=None,
        task_description="unit-test",
        mixture_lambda_start=0.0,
        mixture_lambda_end=0.5,
        mixture_anneal_steps=10_000,
        vlm_call_interval=1,
    )
    kwargs.update(overrides)
    return VLMRBBuffer(**kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_push_sample_update_smoke():
    """End-to-end smoke: push, sample, update — nothing raises."""
    buf = _make_buffer()
    _push_episode(buf, T=100)
    assert len(buf) == 100

    batch = buf.sample(32)
    assert batch["obs"].shape == (32, 4)
    assert batch["indices"].shape == (32,)
    assert batch["weights"].shape == (32,)
    assert np.all(batch["weights"] > 0)

    td = np.random.uniform(-1, 1, size=32).astype(np.float32)
    buf.update_priorities(batch["indices"], td)


def test_clip_formation_with_force_scores():
    """Each clip's p_VLM score must propagate to all transitions in it."""
    buf = _make_buffer(clip_length=8)
    start = _push_episode(buf, T=24)  # 3 clips of 8

    forced = [0.1, 0.5, 0.9]
    buf.apply_vlm_rb_scoring(
        episode_start_idx=start,
        episode_length=24,
        episode_frames=None,
        force_scores=forced,
    )

    # Slots 0..7 → 0.1, 8..15 → 0.5, 16..23 → 0.9
    for local_t in range(24):
        buf_idx = (start + local_t) % buf.capacity
        clip = local_t // 8
        expected = forced[clip]
        assert np.isclose(buf._clip_score[buf_idx], expected), (
            f"slot {buf_idx} (clip {clip}): got {buf._clip_score[buf_idx]} "
            f"expected {expected}"
        )


def test_clip_formation_with_short_final_clip():
    """Last clip may be shorter than L — must still be scored cleanly."""
    buf = _make_buffer(clip_length=8)
    T = 20  # → clips of size [8, 8, 4]
    n_clips_expected = (T + 7) // 8
    assert n_clips_expected == 3
    start = _push_episode(buf, T=T)
    forced = [0.2, 0.4, 0.6]
    buf.apply_vlm_rb_scoring(
        episode_start_idx=start,
        episode_length=T,
        episode_frames=None,
        force_scores=forced,
    )
    # Final clip occupies slots 16..19 only.
    for local_t in range(16, 20):
        buf_idx = (start + local_t) % buf.capacity
        assert np.isclose(buf._clip_score[buf_idx], 0.6)


def test_priority_increases_with_clip_score_at_equal_td():
    """For equal |TD|, a higher p_VLM_clip ⇒ strictly higher priority."""
    buf = _make_buffer(clip_length=4)
    start = _push_episode(buf, T=8)
    # Two clips: clip 0 score 0.1, clip 1 score 0.9.
    buf.apply_vlm_rb_scoring(
        episode_start_idx=start,
        episode_length=8,
        force_scores=[0.1, 0.9],
    )
    # Same |TD|=1.0 for all 8 transitions.
    idxs = np.array([(start + t) % buf.capacity for t in range(8)],
                    dtype=np.int64)
    td = np.ones(8, dtype=np.float32)
    buf.update_priorities(idxs, td)

    p_lo = float(buf._sum_tree[int(idxs[0])])  # clip 0
    p_hi = float(buf._sum_tree[int(idxs[4])])  # clip 1
    assert p_hi > p_lo, f"hi={p_hi} should exceed lo={p_lo}"


def test_lambda_anneal_endpoints():
    """λ_t anneals linearly start→end over `mixture_anneal_steps`."""
    buf = _make_buffer(
        mixture_lambda_start=0.0,
        mixture_lambda_end=0.5,
        mixture_anneal_steps=100,
    )
    _push_episode(buf, T=50)

    # Before any sample(): λ ≈ start.
    assert np.isclose(buf._current_lambda(), 0.0)

    # After many samples: λ saturates at end.
    for _ in range(200):
        _ = buf.sample(8)
    assert np.isclose(buf._current_lambda(), 0.5)


def test_mixture_sampling_uniform_at_lambda_zero():
    """With λ=0 the buffer must sample uniformly regardless of priorities."""
    buf = _make_buffer(
        clip_length=4,
        mixture_lambda_start=0.0,
        mixture_lambda_end=0.0,  # always uniform
        mixture_anneal_steps=1,
    )
    start = _push_episode(buf, T=8)
    # Crank clip 1 to score 1.0 with huge |TD|; clip 0 stays at score 0.
    buf.apply_vlm_rb_scoring(
        episode_start_idx=start, episode_length=8,
        force_scores=[0.0, 1.0],
    )
    idxs = np.array([(start + t) % buf.capacity for t in range(8)],
                    dtype=np.int64)
    td = np.array([0.01, 0.01, 0.01, 0.01, 100.0, 100.0, 100.0, 100.0],
                  dtype=np.float32)
    buf.update_priorities(idxs, td)

    counts = np.zeros(8, dtype=int)
    for _ in range(2000):
        batch = buf.sample(8)
        for i in batch["indices"]:
            local_t = (int(i) - start) % buf.capacity
            if 0 <= local_t < 8:
                counts[local_t] += 1
    # Uniform sampling: each slot should be hit roughly equally.
    # Tolerate 25% slack since the buffer also contains the older (None-
    # init'd) slots not pushed in this episode — but in this test we
    # only pushed 8 transitions so size==8 and all picks land here.
    mean = counts.mean()
    assert all(0.7 * mean <= c <= 1.3 * mean for c in counts), (
        f"counts not uniform: {counts}"
    )


def test_mixture_sampling_priority_at_lambda_one():
    """With λ=1 the buffer must over-sample high-clip-score slots at equal |TD|."""
    buf = _make_buffer(
        clip_length=4,
        mixture_lambda_start=1.0,
        mixture_lambda_end=1.0,
        mixture_anneal_steps=1,
    )
    start = _push_episode(buf, T=8)
    # Clip 0 score 0.05, clip 1 score 0.95 — same |TD|=1.0
    buf.apply_vlm_rb_scoring(
        episode_start_idx=start, episode_length=8,
        force_scores=[0.05, 0.95],
    )
    idxs = np.array([(start + t) % buf.capacity for t in range(8)],
                    dtype=np.int64)
    td = np.ones(8, dtype=np.float32)
    buf.update_priorities(idxs, td)

    clip0_count = 0
    clip1_count = 0
    for _ in range(2000):
        batch = buf.sample(8)
        for i in batch["indices"]:
            local_t = (int(i) - start) % buf.capacity
            if 0 <= local_t < 4:
                clip0_count += 1
            elif 4 <= local_t < 8:
                clip1_count += 1
    assert clip1_count > clip0_count * 2, (
        f"high-score clip should be over-sampled: clip0={clip0_count}, "
        f"clip1={clip1_count}"
    )


def test_stub_scorer_invokes_and_counts():
    """With a real stub scorer wired, calls increment the counters."""
    buf = _make_buffer(clip_length=4)
    buf.vlm_score_fn = make_stub_scorer(seed=42)
    start = _push_episode(buf, T=12)  # 3 clips
    buf.apply_vlm_rb_scoring(
        episode_start_idx=start, episode_length=12,
        episode_frames=[np.zeros((4, 4, 3), dtype=np.uint8)] * 12,
    )
    assert buf.stats["vlm_rb_clip_call_count"] == 3
    assert buf.stats["vlm_rb_clips_scored"] == 3
    assert buf.stats["vlm_rb_calls_failed"] == 0


def test_no_scorer_degrades_to_per_priorities():
    """With vlm_score_fn=None and no force_scores, clip scores stay at 1.0
    (no boost) so priorities collapse to standard PER."""
    buf = _make_buffer(clip_length=4, vlm_score_fn=None)
    start = _push_episode(buf, T=8)
    # apply_vlm_rb_scoring with no scorer and no force_scores: defaults to 1.0.
    buf.apply_vlm_rb_scoring(
        episode_start_idx=start, episode_length=8,
        episode_frames=None,
    )
    # All clip scores remain 1.0.
    for local_t in range(8):
        buf_idx = (start + local_t) % buf.capacity
        assert buf._clip_score[buf_idx] == 1.0


if __name__ == "__main__":
    # Allow `python tests/test_vlm_rb_buffer.py` for venvs without pytest.
    test_push_sample_update_smoke()
    test_clip_formation_with_force_scores()
    test_clip_formation_with_short_final_clip()
    test_priority_increases_with_clip_score_at_equal_td()
    test_lambda_anneal_endpoints()
    test_mixture_sampling_uniform_at_lambda_zero()
    test_mixture_sampling_priority_at_lambda_one()
    test_stub_scorer_invokes_and_counts()
    test_no_scorer_degrades_to_per_priorities()
    print("All VLM-RB buffer tests passed.")
