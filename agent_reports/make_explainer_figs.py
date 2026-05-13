"""Generate diagrams for the methods explainer PDF.

Creates clean, friendly, NeurIPS-style figures for the family of
replay-buffer methods covered in the paper:
  UER -> PER -> Semantic PER -> HER -> Counterfactual HER -> Verified-CF

All figures saved as PNG at 300 DPI to agent_reports/figs/.
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle
from matplotlib.lines import Line2D
import numpy as np

# NeurIPS / CB-safe palette (Tableau CB10 - keep simple)
CB = {
    "blue":   "#0173B2",
    "orange": "#DE8F05",
    "green":  "#029E73",
    "red":    "#CC3311",
    "purple": "#9F2B68",
    "gray":   "#56575A",
    "lightgray": "#D5D9DC",
    "bg":     "#F4F6F8",
    "ink":    "#1C2630",
}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.bbox": "tight",
    "savefig.dpi": 300,
})

ROOT = Path("/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185")
FIGS = ROOT / "agent_reports" / "figs"
FIGS.mkdir(parents=True, exist_ok=True)


def _box(ax, x, y, w, h, label, color=CB["bg"], edge=CB["gray"], fontsize=9,
         bold=False, text_color=None):
    """Draw a rounded box with centered text."""
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        linewidth=1.0, edgecolor=edge, facecolor=color,
    )
    ax.add_patch(patch)
    weight = "bold" if bold else "normal"
    tc = text_color or CB["ink"]
    ax.text(x + w/2, y + h/2, label, ha="center", va="center",
            fontsize=fontsize, fontweight=weight, color=tc, wrap=True)


def _arrow(ax, xy_from, xy_to, color=CB["gray"], lw=1.2, style="->",
           connstyle="arc3,rad=0.0"):
    ax.add_patch(FancyArrowPatch(
        xy_from, xy_to, arrowstyle=style, lw=lw,
        color=color, connectionstyle=connstyle,
        mutation_scale=12,
    ))


# ---------------------------------------------------------------------------
# FIGURE 1: The problem -- episode -> buffer -> SGD; sparse reward; credit
# ---------------------------------------------------------------------------
def fig_problem():
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.set_aspect("equal")
    ax.axis("off")

    # Episode strip across the top
    ax.text(0.2, 5.55, "Episode (50 timesteps)", fontsize=10, fontweight="bold",
            color=CB["ink"])
    n = 12
    for i in range(n):
        x0 = 0.2 + i * 0.78
        is_last = (i == n - 1)
        color = CB["green"] if is_last else CB["bg"]
        _box(ax, x0, 4.85, 0.7, 0.6, f"$s_{{{i}}}$",
             color=color, fontsize=8, bold=is_last)
    # Reward label on terminal step
    ax.annotate("reward = 0/1\n(only at the end)",
                xy=(0.2 + (n-1) * 0.78 + 0.35, 5.45),
                xytext=(8.3, 5.85),
                fontsize=8.5, color=CB["red"], ha="center",
                arrowprops=dict(arrowstyle="->", color=CB["red"], lw=0.9))

    # Sparse-reward callout (left side, mid)
    _box(ax, 0.2, 2.8, 3.5, 1.3,
         "Sparse reward\n\nAgent sees 0 for every step\nuntil the very end. Then 1 (win)\nor 0 (lose). No clue mid-episode.",
         color="#FBEFD8", edge=CB["orange"], fontsize=8.5)

    # Buffer in the middle
    _box(ax, 4.2, 2.8, 2.6, 1.3,
         "Replay buffer\n\nStore every (s, a, r, s')\ntransition we have seen.\nSGD samples from this.",
         color="#E5EEF5", edge=CB["blue"], fontsize=8.5, bold=False)

    # SGD on the right
    _box(ax, 7.3, 2.8, 2.5, 1.3,
         "SGD update\n\nPick a batch -> compute loss\n-> update Q / policy.\nWhich batch helps most?",
         color="#E0F0E8", edge=CB["green"], fontsize=8.5)

    _arrow(ax, (3.7, 3.45), (4.2, 3.45), color=CB["gray"], lw=1.4)
    _arrow(ax, (6.8, 3.45), (7.3, 3.45), color=CB["gray"], lw=1.4)

    # Episode -> buffer arrow (down)
    _arrow(ax, (5.5, 4.8), (5.5, 4.15), color=CB["gray"], lw=1.4)

    # Credit assignment question at bottom
    _box(ax, 0.2, 0.6, 9.6, 1.5,
         "The credit assignment problem\n\n"
         "If the episode failed, WHICH of the 50 transitions actually mattered?\n"
         "Uniform sampling treats them all the same. The methods on the next pages each\n"
         "make a different bet about which transitions deserve more learning.",
         color="#F4ECF7", edge=CB["purple"], fontsize=9)

    plt.savefig(FIGS / "explainer_problem.png", dpi=300)
    plt.close(fig)
    print("wrote explainer_problem.png")


# ---------------------------------------------------------------------------
# FIGURE 2: Family tree
# ---------------------------------------------------------------------------
def fig_family_tree():
    fig, ax = plt.subplots(figsize=(8.0, 5.6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8.2)
    ax.axis("off")

    # Root
    _box(ax, 4.5, 7.2, 3, 0.7, "Replay buffer", color=CB["bg"],
         edge=CB["ink"], bold=True, fontsize=11)

    # On-policy vs off-policy
    _box(ax, 0.5, 5.8, 3.0, 0.7, "On-policy\n(no buffer)",
         color=CB["lightgray"], edge=CB["gray"], fontsize=8.5)
    _box(ax, 8.5, 5.8, 3.0, 0.7, "Off-policy (us)",
         color="#E5EEF5", edge=CB["blue"], bold=True, fontsize=10)

    _arrow(ax, (5.5, 7.2), (2.0, 6.5), color=CB["gray"])
    _arrow(ax, (6.5, 7.2), (10.0, 6.5), color=CB["gray"])

    # Three off-policy branches
    branch_y = 4.6
    _box(ax, 0.3, branch_y, 2.3, 0.7, "UER\nUniform replay",
         color="#FFF", edge=CB["gray"], fontsize=8.5)
    _box(ax, 4.85, branch_y, 2.3, 0.7, "PER\nTD-error priority",
         color="#FFF", edge=CB["gray"], fontsize=8.5)
    _box(ax, 9.4, branch_y, 2.3, 0.7, "HER\nRelabel goals",
         color="#FFF", edge=CB["gray"], fontsize=8.5)

    # Connectors from "Off-policy" to three branches (route around boxes)
    _arrow(ax, (9.0, 5.8), (1.45, branch_y + 0.7), color=CB["gray"],
           connstyle="arc3,rad=0.28")
    _arrow(ax, (9.5, 5.8), (6.0, branch_y + 0.7), color=CB["gray"],
           connstyle="arc3,rad=0.18")
    _arrow(ax, (10.5, 5.8), (10.55, branch_y + 0.7), color=CB["gray"])

    # PER children
    _box(ax, 3.6, 2.6, 2.3, 0.85,
         "Semantic PER\nVLM finds failure\nwindow",
         color="#E0F0E8", edge=CB["green"], fontsize=8.0)
    _box(ax, 6.05, 2.6, 2.3, 0.85,
         "OUR PATH A\nFailure-localized\nbidirectional",
         color="#E0F0E8", edge=CB["green"], bold=True, fontsize=8.0)

    _arrow(ax, (5.55, branch_y), (4.75, 3.45), color=CB["green"])
    _arrow(ax, (6.3, branch_y), (7.2, 3.45), color=CB["green"])

    # HER children
    _box(ax, 8.6, 2.6, 2.3, 0.85,
         "CF-HER\nVLM imagines\ngoal G*",
         color="#FBEFD8", edge=CB["orange"], fontsize=8.0)
    _box(ax, 11.0, 2.6, 0.9, 0.85, "", color="#FFF", edge="#FFF")  # spacer
    _box(ax, 10.95, 2.6, 0.85, 0.85, "", color="#FFF", edge="#FFF")

    _arrow(ax, (10.4, branch_y), (9.75, 3.45), color=CB["orange"])

    # Verified-CF (our Path C)
    _box(ax, 8.6, 0.8, 2.6, 0.95,
         "OUR PATH C\nVerified-CF\nsim-rollout check",
         color="#FBEFD8", edge=CB["red"], bold=True, fontsize=8.0)
    _arrow(ax, (9.75, 2.6), (9.9, 1.75), color=CB["orange"])

    # One-line summaries below
    summaries = [
        (1.45, branch_y - 0.45, "everything equal"),
        (6.0, branch_y - 0.45, "surprising > boring"),
        (10.55, branch_y - 0.45, "pretend we meant it"),
    ]
    for x, y, txt in summaries:
        ax.text(x, y, txt, ha="center", va="center", fontsize=8,
                style="italic", color=CB["gray"])

    plt.savefig(FIGS / "explainer_family_tree.png", dpi=300)
    plt.close(fig)
    print("wrote explainer_family_tree.png")


# ---------------------------------------------------------------------------
# FIGURE 3: Semantic PER mechanism diagram
# ---------------------------------------------------------------------------
def fig_semantic_per():
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4.8)
    ax.axis("off")

    n = 25
    x0, y0 = 0.3, 3.4
    w_step = 0.42
    t_star = 16
    W = 3
    for i in range(n):
        x = x0 + i * w_step
        if abs(i - t_star) <= W:
            color = CB["red"] if i == t_star else "#F8C8C0"
            edge = CB["red"]
        else:
            color = CB["bg"]
            edge = CB["gray"]
        _box(ax, x, y0, w_step - 0.06, 0.7, "",
             color=color, edge=edge, fontsize=7)

    # Title removed: NeurIPS convention — no in-canvas chart titles; move to caption.
    ax.annotate(f"t* = {t_star}\n(critical failure)",
                xy=(x0 + t_star * w_step + 0.18, y0 + 0.7),
                xytext=(x0 + t_star * w_step + 0.18, y0 + 1.8),
                fontsize=8.5, color=CB["red"], ha="center",
                arrowprops=dict(arrowstyle="->", color=CB["red"], lw=0.9))
    ax.text(x0 + t_star * w_step + 0.18, y0 - 0.45,
            f"window [t*-W, t*+W], W = {W}",
            fontsize=8.0, color=CB["red"], ha="center", style="italic")

    # VLM box on the right
    _box(ax, 7.5, 1.2, 4.2, 1.3,
         "VLM looks at frames\n\n\"the gripper missed the\nblock around step 16\"",
         color="#E0F0E8", edge=CB["green"], fontsize=8.5)

    _box(ax, 0.3, 1.2, 4.2, 1.3,
         "Prioritized sampling\n\np(i) proportional to\n|TD|^alpha * w_failure(i)",
         color="#E5EEF5", edge=CB["blue"], fontsize=8.5)

    _arrow(ax, (9.0, 2.5), (9.0, 3.4), color=CB["green"])
    _arrow(ax, (5.5, 3.4), (3.2, 2.5), color=CB["blue"])

    plt.savefig(FIGS / "explainer_semantic_per.png", dpi=300)
    plt.close(fig)
    print("wrote explainer_semantic_per.png")


# ---------------------------------------------------------------------------
# FIGURE 4: CF-HER mechanism (with honest weakness)
# ---------------------------------------------------------------------------
def fig_cf_her():
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5)
    ax.axis("off")

    # Trajectory: failed (doesn't reach G), with imagined goal G*
    # Shift trajectory up slightly to use freed space (title removed per NeurIPS: no chart titles)
    traj_x = np.linspace(0.6, 6.5, 30)
    traj_y = 3.8 + 0.3 * np.sin(traj_x * 1.5) - 0.15 * traj_x
    ax.plot(traj_x, traj_y, color=CB["blue"], lw=2.0, label="actual trajectory")
    ax.scatter([traj_x[0]], [traj_y[0]], s=40, color=CB["blue"], zorder=3)
    ax.text(traj_x[0] - 0.2, traj_y[0] + 0.2, "start", fontsize=8.5)
    # Real goal G (never reached)
    G_xy = (7.4, 4.0)
    ax.scatter(*G_xy, marker="*", s=200, color=CB["gray"], zorder=3)
    ax.text(G_xy[0] + 0.15, G_xy[1] + 0.2, "G (real goal)\n-- not reached",
            fontsize=8.5, color=CB["gray"])

    # Imagined goal G* (VLM proposes near trajectory end)
    end = (traj_x[-1], traj_y[-1])
    G_star = (end[0] + 0.3, end[1] - 0.2)
    ax.scatter(*G_star, marker="*", s=200, color=CB["orange"], zorder=3)
    ax.text(G_star[0] + 0.25, G_star[1] + 0.05,
            "G* (VLM-imagined)", fontsize=8.5, color=CB["orange"],
            ha="left", va="center")

    # Honest weakness call-out
    _box(ax, 0.4, 0.2, 11.2, 1.4,
         "Honest weakness of vanilla CF-HER:\n"
         "if the real trajectory never actually got to G*, then the reward (which we\n"
         "recompute on the relabel) is still 0. We did not actually create a winning\n"
         "transition -- we just changed which losing transition the agent is told to learn from.",
         color="#FBEFD8", edge=CB["red"], fontsize=8.5)

    # Title removed: NeurIPS convention — no in-canvas chart titles.
    # Caption in the surrounding PDF should read:
    #   "Counterfactual HER: 'what if the goal had been here?'"

    plt.savefig(FIGS / "explainer_cf_her.png", dpi=300)
    plt.close(fig)
    print("wrote explainer_cf_her.png")


# ---------------------------------------------------------------------------
# FIGURE 5: Verified-CF (our N1)
# ---------------------------------------------------------------------------
def fig_verified_cf():
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5.0)
    ax.axis("off")

    # Title removed: NeurIPS convention — no in-canvas chart titles.
    # Caption in surrounding PDF should read:
    #   "Verified-CF (our Path C, agent N1): sim-rollout acceptance gate."

    # Step 1
    _box(ax, 0.3, 3.0, 2.8, 1.6,
         "1. Snapshot sim\n\nFreeze MuJoCo state\nat failure timestep K\n(qpos, qvel, mocap).",
         color="#E5EEF5", edge=CB["blue"], fontsize=8.2)
    # Step 2
    _box(ax, 3.3, 3.0, 2.8, 1.6,
         "2. VLM proposes\ncorrective action\n\nA 4-vector action a*,\nNOT a teleport.",
         color="#E0F0E8", edge=CB["green"], fontsize=8.2)
    # Step 3
    _box(ax, 6.3, 3.0, 2.8, 1.6,
         "3. Roll out in sim\n\nExecute a* from\nsnapshot for <=50 steps.\nLet physics decide.",
         color="#F4ECF7", edge=CB["purple"], fontsize=8.2)
    # Step 4
    _box(ax, 9.3, 3.0, 2.4, 1.6,
         "4. Accept?\n\nOnly if env's\nown sparse reward\nactually fires.",
         color="#FBEFD8", edge=CB["red"], bold=True, fontsize=8.2)

    for x in [3.1, 6.1, 9.1]:
        _arrow(ax, (x, 3.8), (x + 0.2, 3.8), color=CB["gray"], lw=1.2)

    # Outcome row
    _box(ax, 0.3, 1.0, 5.8, 1.4,
         "ACCEPT: synthetic transitions reach G*\nfor real. Reward = 1 is genuine.\nThe value function trains on real signal.",
         color="#E0F0E8", edge=CB["green"], fontsize=8.2)
    _box(ax, 6.3, 1.0, 5.4, 1.4,
         "REJECT: VLM proposal failed in sim.\nDrop it. No synthetic transitions added.\nNo lie in the buffer.",
         color="#F8C8C0", edge=CB["red"], fontsize=8.2)

    ax.text(6.0, 0.45,
            "Key property: teleport is structurally impossible -- you cannot teleport a block "
            "with a 4D action.",
            fontsize=8.2, ha="center", style="italic", color=CB["ink"])

    plt.savefig(FIGS / "explainer_verified_cf.png", dpi=300)
    plt.close(fig)
    print("wrote explainer_verified_cf.png")


if __name__ == "__main__":
    fig_problem()
    fig_family_tree()
    fig_semantic_per()
    fig_cf_her()
    fig_verified_cf()
    print("\nALL FIGURES WRITTEN")
