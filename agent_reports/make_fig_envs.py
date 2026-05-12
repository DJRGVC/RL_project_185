"""Render a paper-grade environment-screenshots figure for §5.1 Setup.

3 cols (FetchPush, FetchPickAndPlace, FetchSlide) x 3 rows (Initial, Mid, Near-goal).
Uses MuJoCo via EGL (CPU-only off-screen rendering), seed 42 for reproducibility.

Output: agent_reports/figs/fig_envs.{png,pdf}

Style: NeurIPS conventions (no global title, sans-serif, CB-safe-neutral, white bg, vector PDF).
"""
from __future__ import annotations

import os

# Force off-screen GL backend BEFORE importing mujoco/gymnasium
os.environ.setdefault("MUJOCO_GL", "egl")
# Avoid using the GPU we have a training run on (HER@1M PnP). EGL still picks
# the EGL device; we limit to CPU compute since rendering only needs the GL
# device. Training continues on its own CUDA_VISIBLE_DEVICES setting.

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import gymnasium as gym
import gymnasium_robotics  # noqa: F401  registers Fetch envs

# Output paths
OUT_DIR = "/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/figs"
os.makedirs(OUT_DIR, exist_ok=True)

# Environments and headers
ENVS = [
    ("FetchPush-v4",          "FetchPush",         "slide block to target"),
    ("FetchPickAndPlace-v4",  "FetchPickAndPlace", "grasp + 3D place"),
    ("FetchSlide-v4",         "FetchSlide",        "ballistic release on slick surface"),
]

# Timestep checkpoints (50-step horizon)
TIMESTEPS = [0, 24, 49]
ROW_LABELS = ["Initial (t=0)", "Mid (t=24)", "Final (t=49)"]


def scripted_action(env, obs):
    """Heuristic policy: move end-effector toward object, then toward goal.

    Works on the underlying FetchEnv observation dict.
    """
    grip_pos = obs["observation"][0:3]
    obj_pos  = obs["observation"][3:6]
    goal     = obs["desired_goal"]

    # Distance from gripper to object
    to_obj = obj_pos - grip_pos
    dist_to_obj = np.linalg.norm(to_obj)

    # Phase 1: approach object. Phase 2: push/carry toward goal.
    if dist_to_obj > 0.05:
        dxyz = np.clip(to_obj * 6.0, -1.0, 1.0)
        gripper = 1.0  # open
    else:
        to_goal = goal - obj_pos
        dxyz = np.clip(to_goal * 6.0, -1.0, 1.0)
        gripper = -1.0  # close (helps PickAndPlace)
    return np.array([dxyz[0], dxyz[1], dxyz[2], gripper], dtype=np.float32)


def collect_frames(env_id: str, timesteps):
    """Reset with seed=42, roll out scripted policy, capture frames at requested t."""
    env = gym.make(env_id, render_mode="rgb_array", max_episode_steps=50)
    obs, _ = env.reset(seed=42)
    frames = {}
    horizon = max(timesteps) + 1
    for t in range(horizon):
        if t in timesteps:
            frames[t] = env.render()
        action = scripted_action(env.unwrapped, obs)
        obs, _, terminated, truncated, _ = env.step(action)
        if terminated or truncated:
            # If we hit early termination, just keep rendering subsequent frames
            # without stepping further (env returns last frame).
            for tt in timesteps:
                if tt > t and tt not in frames:
                    frames[tt] = env.render()
            break
    env.close()
    return [frames[t] for t in timesteps]


def crop_center(img: np.ndarray, frac: float = 0.85) -> np.ndarray:
    """Center-crop to reduce blank surround and emphasize the workspace."""
    h, w = img.shape[:2]
    ch, cw = int(h * frac), int(w * frac)
    y0 = (h - ch) // 2
    x0 = (w - cw) // 2
    return img[y0:y0 + ch, x0:x0 + cw]


def main():
    # Collect all frames
    print("Rendering frames (this takes ~20s)...")
    grid = []  # list[col] -> list[row] of frames
    for env_id, _, _ in ENVS:
        print(f"  {env_id}")
        col_frames = collect_frames(env_id, TIMESTEPS)
        col_frames = [crop_center(f, 0.82) for f in col_frames]
        grid.append(col_frames)

    # ---- Build matplotlib figure (NeurIPS style) ----
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 8,
        "axes.linewidth": 0.6,
        "savefig.dpi": 300,
    })

    nrows, ncols = len(TIMESTEPS), len(ENVS)
    fig, axes = plt.subplots(
        nrows, ncols,
        figsize=(6.75, 5.6),
        constrained_layout=False,
    )

    # Column headers (env name + 1-line task description)
    for j, (_, name, desc) in enumerate(ENVS):
        ax = axes[0, j]
        ax.set_title(f"{name}\n{desc}", fontsize=9, fontweight="bold", pad=6)

    # Plot cells
    for j, (_, _, _) in enumerate(ENVS):
        col_frames = grid[j]
        for i, frame in enumerate(col_frames):
            ax = axes[i, j]
            ax.imshow(frame)
            ax.set_xticks([])
            ax.set_yticks([])
            # Light border
            for spine in ax.spines.values():
                spine.set_edgecolor("#888888")
                spine.set_linewidth(0.5)
            # Per-cell caption below
            ax.set_xlabel(ROW_LABELS[i], fontsize=8, labelpad=2)

    # Tight spacing; leave room for column headers
    fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.04,
                        wspace=0.08, hspace=0.22)

    # Save
    png_path = os.path.join(OUT_DIR, "fig_envs.png")
    pdf_path = os.path.join(OUT_DIR, "fig_envs.pdf")
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf_path,             bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Wrote: {png_path}")
    print(f"Wrote: {pdf_path}")


if __name__ == "__main__":
    main()
