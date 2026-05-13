"""Project-overview video (45-90s MP4 + GIF) for the README.

Renders 6 scenes as 1280x720 PNGs in `agent_reports/videos/_scenes/`,
then uses ffmpeg to stitch them into:
  - agent_reports/videos/project_overview.mp4   (H.264, yuv420p, GitHub-safe)
  - agent_reports/videos/project_overview.gif   (10fps, 600px wide, looped)

Design notes:
- NeurIPS-adjacent style for figures (sans-serif, CB-safe palette), but this
  is a portfolio piece so we DO use chart titles, big text, and crossfades.
- Re-uses pre-rendered `agent_reports/figs/fig_envs.png` so we never touch
  MuJoCo while training is in flight on the GPU.
- Scene 5 builds its own bar chart (we draw the bars at full height; the
  crossfade-into-still effect is the "reveal"). Per-seed dots and HER ref
  line match `make_fig_headline_v2.py` so the numbers stay consistent.

Run:
    .venv/bin/python agent_reports/make_video_overview.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent          # agent_reports/
PROJECT = ROOT.parent                            # repo root
FIGS = ROOT / "figs"
OUT_DIR = ROOT / "videos"
SCENES_DIR = OUT_DIR / "_scenes"
OUT_DIR.mkdir(exist_ok=True)
SCENES_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
W, H = 1280, 720          # 720p
DPI = 100                  # → figsize = (12.8, 7.2)
FIGSIZE = (W / DPI, H / DPI)
FPS = 30

mpl.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "savefig.dpi": DPI,
})

# CB-safe palette (Tableau Color Blind 10) — same as make_fig_headline_v2.py
PALETTE = {
    "Uniform":       "#ABABAB",
    "PER":           "#006BA4",
    "HER":           "#FF800E",
    "Oracle-CF":     "#A2C8EC",
    "vlm_cf (ours)": "#2CA02C",
}
ACCENT = "#FFC857"      # warm yellow for callouts on dark bg
INK = "#F5F5F5"         # off-white text on black
MUTED = "#9aa0a6"


def new_fig(facecolor="black"):
    fig = plt.figure(figsize=FIGSIZE, dpi=DPI, facecolor=facecolor)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_facecolor(facecolor)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return fig, ax


def save_scene(fig, name: str):
    path = SCENES_DIR / f"{name}.png"
    fig.savefig(path, dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  wrote {path.name}")
    return path


# ---------------------------------------------------------------------------
# Scene 1: Title card
# ---------------------------------------------------------------------------
def scene_title():
    fig, ax = new_fig("black")
    ax.text(0.5, 0.66,
            "VLM-Verified Counterfactual Hindsight",
            ha="center", va="center",
            fontsize=36, color=INK, fontweight="bold")
    ax.text(0.5, 0.55,
            "for Sparse-Reward Manipulation",
            ha="center", va="center",
            fontsize=26, color=INK, fontweight="light")
    # accent rule
    ax.plot([0.30, 0.70], [0.46, 0.46], color=ACCENT, linewidth=2.2)
    ax.text(0.5, 0.36,
            "CS 285 Final Project   ·   UC Berkeley",
            ha="center", va="center",
            fontsize=18, color=MUTED, style="italic")
    ax.text(0.5, 0.18,
            "Daniel Grant",
            ha="center", va="center",
            fontsize=14, color=MUTED)
    return save_scene(fig, "scene1_title")


# ---------------------------------------------------------------------------
# Scene 2: 3 Fetch envs — reuse fig_envs.png as a single composed panel
# ---------------------------------------------------------------------------
def _extract_env_cells(src_png: Path):
    """Pull individual env screenshots out of fig_envs.png (1942x1674, 3x3).

    Returns dict env_name -> list of 3 numpy frames [initial, mid, final].
    Cell coordinates determined empirically. We strip the per-cell row labels
    by cropping ~7% off the bottom of each cell.
    """
    if not src_png.exists():
        return None
    img = np.asarray(Image.open(src_png).convert("RGB"))
    ih, iw, _ = img.shape
    # Manual crop coordinates — fig_envs has ~3% L/R margin, ~7% top header,
    # ~3% bottom padding, equal-sized cells inside. We aim for the IMAGE area
    # of each cell, dropping the row-label text below each image.
    pad_top = 0.075
    pad_bot = 0.035
    pad_lr = 0.035
    inner_h = ih * (1 - pad_top - pad_bot)
    inner_w = iw * (1 - 2 * pad_lr)
    cell_h = inner_h / 3
    cell_w = inner_w / 3
    label_strip = 0.18  # fraction of cell height to remove (caption "Mid (t=24)" etc.)

    envs = ["FetchPush", "FetchPickAndPlace", "FetchSlide"]
    cells: dict[str, list] = {e: [] for e in envs}
    for r in range(3):
        for c, env in enumerate(envs):
            y0 = int(ih * pad_top + r * cell_h)
            y1 = int(y0 + cell_h * (1 - label_strip))
            x0 = int(iw * pad_lr + c * cell_w)
            x1 = int(x0 + cell_w)
            cells[env].append(img[y0:y1, x0:x1])
    return cells


def scene_envs():
    fig = plt.figure(figsize=FIGSIZE, dpi=DPI, facecolor="black")
    bg = fig.add_axes([0, 0, 1, 1])
    bg.set_xticks([]); bg.set_yticks([])
    for sp in bg.spines.values():
        sp.set_visible(False)
    bg.set_facecolor("black")
    bg.text(0.5, 0.93,
            "Three sparse-reward Fetch tasks",
            ha="center", va="center",
            fontsize=26, color=INK, fontweight="bold",
            transform=bg.transAxes)
    bg.text(0.5, 0.86,
            "+1 only on success — otherwise 0 reward",
            ha="center", va="center",
            fontsize=14, color=MUTED, style="italic",
            transform=bg.transAxes)

    env_names = ["FetchPush", "FetchPickAndPlace", "FetchSlide"]
    env_subs = ["slide block to target",
                "grasp + 3D place",
                "ballistic release"]
    cells = _extract_env_cells(FIGS / "fig_envs.png")

    # 3 inset axes for the three "mid" screenshots
    panel_y = 0.20
    panel_h = 0.56
    panel_w = 0.27
    gap = (1 - 3 * panel_w) / 4
    for i, (env, sub) in enumerate(zip(env_names, env_subs)):
        x = gap + i * (panel_w + gap)
        ax = fig.add_axes([x, panel_y, panel_w, panel_h])
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_facecolor("#101010")
        for sp in ax.spines.values():
            sp.set_edgecolor("#666666")
            sp.set_linewidth(0.8)
        if cells is not None:
            ax.imshow(cells[env][1])  # mid frame
        # Title (env name) above each panel
        bg.text(x + panel_w / 2, panel_y + panel_h + 0.04, env,
                ha="center", va="center",
                fontsize=18, color=INK, fontweight="bold",
                transform=bg.transAxes)
        # Subtitle below
        bg.text(x + panel_w / 2, panel_y - 0.04, sub,
                ha="center", va="center",
                fontsize=12, color=MUTED, style="italic",
                transform=bg.transAxes)

    bg.text(0.5, 0.06,
            "We train on three classic Fetch benchmarks with binary success rewards.",
            ha="center", va="center",
            fontsize=13, color=MUTED, transform=bg.transAxes)
    return save_scene(fig, "scene2_envs")


# ---------------------------------------------------------------------------
# Scene 3: The problem
# ---------------------------------------------------------------------------
def scene_problem():
    fig, ax = new_fig("black")
    ax.text(0.5, 0.82,
            "The Problem",
            ha="center", va="center",
            fontsize=20, color=ACCENT, fontweight="bold",
            family="DejaVu Sans")

    ax.text(0.5, 0.66,
            "Sparse rewards mean",
            ha="center", va="center",
            fontsize=24, color=INK)
    ax.text(0.5, 0.55,
            "70–90% of training episodes",
            ha="center", va="center",
            fontsize=34, color=INK, fontweight="bold")
    ax.text(0.5, 0.45,
            "get zero learning signal.",
            ha="center", va="center",
            fontsize=28, color=INK)

    ax.plot([0.30, 0.70], [0.36, 0.36], color=ACCENT, linewidth=1.8)

    ax.text(0.5, 0.27,
            "Our solution",
            ha="center", va="center",
            fontsize=18, color=MUTED, style="italic")
    ax.text(0.5, 0.16,
            "Foundation models as credit-assignment oracles.",
            ha="center", va="center",
            fontsize=22, color=PALETTE["vlm_cf (ours)"], fontweight="bold")
    return save_scene(fig, "scene3_problem")


# ---------------------------------------------------------------------------
# Scene 4: Method illustration
# ---------------------------------------------------------------------------
def scene_method():
    fig, ax = new_fig("black")
    ax.text(0.5, 0.93,
            "How verified counterfactual hindsight works",
            ha="center", va="center",
            fontsize=22, color=INK, fontweight="bold")

    # Stage box helper
    def stage_box(cx, cy, w, h, title, sub, fill="#1c1c1c", edge=MUTED, title_color=INK):
        box = FancyBboxPatch(
            (cx - w / 2, cy - h / 2), w, h,
            boxstyle="round,pad=0.005,rounding_size=0.012",
            linewidth=1.4, edgecolor=edge, facecolor=fill, zorder=2,
        )
        ax.add_patch(box)
        ax.text(cx, cy + h * 0.18, title,
                ha="center", va="center",
                fontsize=14, color=title_color, fontweight="bold", zorder=3)
        ax.text(cx, cy - h * 0.20, sub,
                ha="center", va="center",
                fontsize=10.5, color=MUTED, zorder=3)

    # Layout: 4 stages left→right
    y = 0.55
    w = 0.20
    h = 0.26
    xs = [0.13, 0.37, 0.62, 0.87]

    stage_box(xs[0], y, w, h,
              "Failed rollout",
              "5 sparse keyframes",
              edge="#aa3939")
    # Mini trajectory inside box 1
    traj_x = np.linspace(xs[0] - w * 0.35, xs[0] + w * 0.35, 5)
    traj_y = y + 0.03 + np.array([0.00, 0.015, -0.01, -0.025, -0.045])
    ax.plot(traj_x, traj_y, "o-", color="#e57373",
            markersize=5, linewidth=1.4, zorder=4)
    ax.text(xs[0] + w * 0.40, traj_y[-1] - 0.02, "x", fontsize=11,
            color="#e57373", fontweight="bold", zorder=4)

    stage_box(xs[1], y, w, h,
              "VLM proposes",
              "counterfactual goal",
              edge=PALETTE["PER"])
    ax.text(xs[1], y + 0.005, '"target was\nat (0.4, 1.1, 0.5)"',
            ha="center", va="center",
            fontsize=9.5, color=PALETTE["PER"], style="italic",
            zorder=4)

    stage_box(xs[2], y, w, h,
              "Sim-fork verifies",
              "physics replay",
              edge=ACCENT)
    ax.text(xs[2], y - 0.005,
            "would have succeeded?",
            ha="center", va="center",
            fontsize=9.5, color=ACCENT, style="italic", zorder=4)

    stage_box(xs[3], y, w, h,
              "Verified CF",
              "→ replay buffer",
              edge=PALETTE["vlm_cf (ours)"])
    ax.text(xs[3], y + 0.005, "ok",
            ha="center", va="center",
            fontsize=18, color=PALETTE["vlm_cf (ours)"],
            fontweight="bold", zorder=4)

    # Arrows between stages
    for a, b in zip(xs[:-1], xs[1:]):
        arr = FancyArrowPatch(
            (a + w / 2 + 0.005, y), (b - w / 2 - 0.005, y),
            arrowstyle="->", mutation_scale=18,
            color=INK, linewidth=1.6, zorder=3,
        )
        ax.add_patch(arr)

    # Decision branch under stage 3 — verified vs. rejected
    ax.annotate("",
                xy=(xs[2], 0.22), xytext=(xs[2], y - h / 2 - 0.01),
                arrowprops=dict(arrowstyle="-", color=MUTED,
                                linewidth=1.2, linestyle=(0, (3, 2))),
                zorder=2)
    ax.text(xs[2] - 0.10, 0.18, "rejected (~50%)",
            ha="center", va="center",
            fontsize=10.5, color="#e57373")
    ax.text(xs[2] + 0.10, 0.18, "kept (~50%)",
            ha="center", va="center",
            fontsize=10.5, color=PALETTE["vlm_cf (ours)"])

    # Bottom takeaway
    ax.text(0.5, 0.08,
            "Foundation-model labels never enter learning unsafely — the sim is the judge.",
            ha="center", va="center",
            fontsize=13, color=INK, style="italic")

    return save_scene(fig, "scene4_method")


# ---------------------------------------------------------------------------
# Scene 5: Headline results
# ---------------------------------------------------------------------------
ENVS_5 = ["FetchPush", "FetchPickAndPlace", "FetchSlide"]

SEED_DATA = {
    ("HER", "FetchPush"):              [0.700, 0.450, 0.700],
    ("HER", "FetchPickAndPlace"):      [0.100, 0.050, 0.400],
    ("HER", "FetchSlide"):             [0.200, 0.100, 0.250],
    ("Oracle-CF", "FetchPush"):        [0.300, 0.250, 0.600],
    ("Oracle-CF", "FetchPickAndPlace"):[0.30, 0.90, 0.55],
    ("Oracle-CF", "FetchSlide"):       [0.200, 0.200, 0.150],
    ("vlm_cf (ours)", "FetchPush"):    [1.00, 0.95, 0.90],
    ("vlm_cf (ours)", "FetchPickAndPlace"): [0.35, 0.35, 0.50],
    ("vlm_cf (ours)", "FetchSlide"):   [0.25, 0.70, 0.70],
}
SUMMARY_5 = {
    ("Uniform", "FetchPush"): (0.08, 0.05),
    ("Uniform", "FetchPickAndPlace"): (0.07, 0.05),
    ("Uniform", "FetchSlide"): (0.08, 0.07),
    ("PER", "FetchPush"): (0.95, 0.02),
    ("PER", "FetchPickAndPlace"): (0.10, 0.04),
    ("PER", "FetchSlide"): (0.10, 0.06),
}
METHODS_5 = ["Uniform", "PER", "HER", "Oracle-CF", "vlm_cf (ours)"]


def _agg5(method, env):
    seeds = SEED_DATA.get((method, env))
    if seeds is not None:
        arr = np.asarray(seeds, dtype=float)
        return float(arr.mean()), float(arr.std(ddof=1) / np.sqrt(arr.size)), arr
    if (method, env) in SUMMARY_5:
        m, s = SUMMARY_5[(method, env)]
        return float(m), float(s), None
    return None, None, None


def scene_results():
    # Dark figure, embedded white chart panel so the bars pop
    fig = plt.figure(figsize=FIGSIZE, dpi=DPI, facecolor="black")
    bg = fig.add_axes([0, 0, 1, 1])
    bg.set_xticks([])
    bg.set_yticks([])
    for sp in bg.spines.values():
        sp.set_visible(False)
    bg.set_facecolor("black")

    bg.text(0.5, 0.945,
            "Headline results: success rate by method (n=3 seeds)",
            ha="center", va="center",
            fontsize=20, color=INK, fontweight="bold",
            transform=bg.transAxes)
    bg.text(0.5, 0.895,
            "vlm_cf (ours) decisively beats baselines on Slide and matches the best on Push.",
            ha="center", va="center",
            fontsize=13, color=MUTED, style="italic",
            transform=bg.transAxes)

    # Chart panel — slightly off-white so it reads as a card on the dark bg
    ax = fig.add_axes([0.085, 0.18, 0.83, 0.62])
    ax.set_facecolor("#fafafa")
    for sp in ax.spines.values():
        sp.set_edgecolor("#444444")
        sp.set_linewidth(0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors="#222222", labelsize=11)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="#dddddd", linewidth=0.6, zorder=0)

    x = np.arange(len(ENVS_5))
    n = len(METHODS_5)
    bar_w = 0.82 / n

    drawn = set()
    for i, m in enumerate(METHODS_5):
        offset = (i - (n - 1) / 2) * bar_w
        for j, env in enumerate(ENVS_5):
            mean, se, seeds = _agg5(m, env)
            if mean is None:
                continue
            xpos = x[j] + offset
            ax.bar(xpos, mean, bar_w,
                   yerr=se, color=PALETTE[m],
                   edgecolor="white", linewidth=0.5,
                   error_kw=dict(elinewidth=0.8, capsize=2.5,
                                 capthick=0.8, ecolor="#222222"),
                   label=m if m not in drawn else None, zorder=3)
            drawn.add(m)
            if seeds is not None:
                rng = np.random.default_rng(42 + i * 17 + j * 3)
                jitter = rng.uniform(-bar_w * 0.22, bar_w * 0.22, size=seeds.size)
                ax.scatter(np.full_like(seeds, xpos) + jitter, seeds,
                           s=14, color="white",
                           edgecolors="#222222", linewidths=0.6,
                           zorder=5, clip_on=True)

    # HER dashed reference per env
    for j, env in enumerate(ENVS_5):
        mean, _, _ = _agg5("HER", env)
        if mean is None:
            continue
        ax.hlines(mean, x[j] - 0.40, x[j] + 0.40,
                  colors="#555555", linestyles=(0, (4, 2)),
                  linewidth=1.0, alpha=0.7, zorder=2)

    ax.set_xticks(x)
    ax.set_xticklabels(ENVS_5, color="#222222", fontsize=12)
    ax.set_ylabel("Final success rate", color="#222222", fontsize=12)
    ax.set_ylim(0, 1.10)
    ax.set_yticks(np.arange(0, 1.01, 0.2))

    # In-chart legend (top of plot, against the white card background)
    leg = ax.legend(loc="upper left", bbox_to_anchor=(0.02, 0.99),
                    ncols=1, frameon=True, fontsize=8.5,
                    columnspacing=1.0, handlelength=1.2,
                    facecolor="white", edgecolor="#cccccc",
                    framealpha=0.95)
    for txt in leg.get_texts():
        txt.set_color("#222222")
    leg.get_frame().set_linewidth(0.5)

    bg.text(0.5, 0.05,
            "Bars: mean ± SE   ·   Dots: per-seed runs   ·   Dashed: HER reference",
            ha="center", va="center",
            fontsize=11, color=MUTED, style="italic",
            transform=bg.transAxes)

    return save_scene(fig, "scene5_results")


# ---------------------------------------------------------------------------
# Scene 6: Closing
# ---------------------------------------------------------------------------
def scene_closing():
    fig, ax = new_fig("black")
    ax.text(0.5, 0.70,
            "Code, paper, and figures",
            ha="center", va="center",
            fontsize=22, color=MUTED)
    ax.text(0.5, 0.58,
            "github.com/DJRGVC/RL_project_185",
            ha="center", va="center",
            fontsize=30, color=INK, fontweight="bold",
            family="DejaVu Sans Mono")
    ax.plot([0.25, 0.75], [0.50, 0.50], color=ACCENT, linewidth=1.8)
    ax.text(0.5, 0.42,
            "Paper: arXiv (forthcoming)",
            ha="center", va="center",
            fontsize=18, color=INK)
    ax.text(0.5, 0.30,
            "CS 285  ·  UC Berkeley  ·  Spring 2026",
            ha="center", va="center",
            fontsize=14, color=MUTED, style="italic")
    ax.text(0.5, 0.18,
            "Daniel Grant",
            ha="center", va="center",
            fontsize=12, color=MUTED)
    return save_scene(fig, "scene6_closing")


# ---------------------------------------------------------------------------
# Encode: scene PNGs → MP4 with crossfades → GIF
# ---------------------------------------------------------------------------
SCENE_DURATIONS = [
    ("scene1_title",   4.0),
    ("scene2_envs",   10.0),
    ("scene3_problem", 8.0),
    ("scene4_method", 10.0),
    ("scene5_results",12.0),
    ("scene6_closing", 6.0),
]
CROSSFADE = 0.6  # seconds


def _scale_pad_filter(in_label: str, out_label: str) -> str:
    """ffmpeg filter to force 1280x720 yuv420p safe geometry."""
    return (
        f"[{in_label}]scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps={FPS},"
        f"format=yuv420p[{out_label}]"
    )


def encode_mp4(out_mp4: Path) -> Path:
    """Build the MP4 with xfade crossfades between consecutive scenes."""
    inputs = []
    for name, dur in SCENE_DURATIONS:
        png = SCENES_DIR / f"{name}.png"
        # `-loop 1 -t dur` → still image looped for dur seconds
        # Add crossfade headroom on every clip except the last (xfade consumes
        # `offset + duration` from the next clip's start). We pad each clip's
        # duration by CROSSFADE on its tail except the final, then the xfade
        # overlap eats it back.
        clip_t = dur if name == SCENE_DURATIONS[-1][0] else dur + CROSSFADE
        inputs += ["-loop", "1", "-t", f"{clip_t:.3f}", "-i", str(png)]

    # Build filter_complex
    # Normalize each input
    n = len(SCENE_DURATIONS)
    parts = []
    for i in range(n):
        parts.append(_scale_pad_filter(f"{i}:v", f"v{i}"))

    # Chain xfade: start with v0, then for each subsequent clip i, do
    #   xfade=transition=fade:duration=CROSSFADE:offset=<cumulative>
    # offset is measured in the *current* output stream timeline.
    cur_label = "v0"
    cum_offset = 0.0
    for i in range(1, n):
        prev_dur = SCENE_DURATIONS[i - 1][1]
        # offset = cumulative duration of cur stream minus crossfade
        cum_offset += prev_dur
        next_label = f"x{i}"
        parts.append(
            f"[{cur_label}][v{i}]xfade=transition=fade:"
            f"duration={CROSSFADE:.3f}:offset={cum_offset:.3f}[{next_label}]"
        )
        cur_label = next_label

    filter_complex = ";".join(parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", f"[{cur_label}]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "20",
        "-movflags", "+faststart",
        str(out_mp4),
    ]
    print("  ffmpeg (mp4) ...")
    subprocess.run(cmd, check=True, capture_output=True)
    return out_mp4


def encode_gif(in_mp4: Path, out_gif: Path) -> Path:
    """Two-pass palette GIF: better quality than naive single-pass."""
    palette = OUT_DIR / "_palette.png"
    print("  ffmpeg (gif palette) ...")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(in_mp4),
        "-vf", f"fps=10,scale=600:-1:flags=lanczos,palettegen=stats_mode=diff",
        str(palette),
    ], check=True, capture_output=True)
    print("  ffmpeg (gif assemble) ...")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(in_mp4), "-i", str(palette),
        "-filter_complex",
        "fps=10,scale=600:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5",
        "-loop", "0",
        str(out_gif),
    ], check=True, capture_output=True)
    palette.unlink(missing_ok=True)
    return out_gif


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found on PATH; install ffmpeg first.")

    print("Rendering scenes ...")
    scene_title()
    scene_envs()
    scene_problem()
    scene_method()
    scene_results()
    scene_closing()

    out_mp4 = OUT_DIR / "project_overview.mp4"
    out_gif = OUT_DIR / "project_overview.gif"
    encode_mp4(out_mp4)
    encode_gif(out_mp4, out_gif)

    mp4_mb = out_mp4.stat().st_size / 1e6
    gif_mb = out_gif.stat().st_size / 1e6
    print()
    print(f"MP4: {out_mp4}  ({mp4_mb:.2f} MB)")
    print(f"GIF: {out_gif}  ({gif_mb:.2f} MB)")
    total = sum(d for _, d in SCENE_DURATIONS) + (len(SCENE_DURATIONS) - 1) * 0  # crossfades overlap
    print(f"Total runtime ≈ {total:.0f}s")


if __name__ == "__main__":
    main()
