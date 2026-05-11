"""
Keyframe selection strategies for VLM querying.

Given a sequence of T RGB frames from an episode, select K representative
frames to send to the VLM. Good keyframes maximize coverage of the trajectory
while avoiding redundancy.

Strategies:
  - uniform: evenly spaced across the episode (simple, works well in practice)
  - motion: select frames with the largest pixel-difference from previous frame
  - first_last: always include t=0 and t=T-1, fill middle uniformly
"""
import numpy as np
from typing import List


def select_keyframes(
    frames: List[np.ndarray],
    k: int,
    strategy: str = "uniform",
) -> tuple[List[np.ndarray], List[int]]:
    """Select K keyframes from episode frames.

    Returns:
        (selected_frames, timestep_indices)
    """
    T = len(frames)
    if T == 0:
        return [], []
    k = min(k, T)

    if strategy == "uniform":
        indices = _uniform(T, k)
    elif strategy == "motion":
        indices = _motion(frames, k)
    elif strategy == "first_last":
        indices = _first_last(T, k)
    else:
        raise ValueError(f"Unknown keyframe strategy: {strategy}")

    return [frames[i] for i in indices], list(indices)


def _uniform(T: int, k: int) -> List[int]:
    if k == 1:
        return [T // 2]
    return [int(round(i * (T - 1) / (k - 1))) for i in range(k)]


def _motion(frames: List[np.ndarray], k: int) -> List[int]:
    """Select frames with highest frame-to-frame pixel motion."""
    T = len(frames)
    if T <= 2:
        return _uniform(T, k)

    scores = np.zeros(T)
    for t in range(1, T):
        diff = frames[t].astype(np.float32) - frames[t - 1].astype(np.float32)
        scores[t] = np.mean(np.abs(diff))

    # Always include first and last; pick k-2 highest-motion from middle
    candidates = np.argsort(scores[1:-1])[::-1] + 1  # exclude t=0 and t=T-1
    middle = sorted(candidates[:max(0, k - 2)].tolist())
    indices = sorted(set([0] + middle + [T - 1]))[:k]
    # Pad with uniform if not enough
    if len(indices) < k:
        indices = _uniform(T, k)
    return indices


def _first_last(T: int, k: int) -> List[int]:
    if k == 1:
        return [0]
    if k == 2:
        return [0, T - 1]
    middle = _uniform(T, k - 2)[1:-1]  # inner k-2 uniform points
    return sorted(set([0] + middle + [T - 1]))


def build_frame_index_map(timestep_indices: List[int], total_steps: int) -> str:
    """Build a human-readable string for the VLM prompt showing frame-to-step mapping."""
    lines = []
    for i, t in enumerate(timestep_indices):
        pct = 100.0 * t / max(total_steps - 1, 1)
        lines.append(f"  Frame {i}: timestep {t} (~{pct:.0f}% through episode)")
    return "\n".join(lines)
