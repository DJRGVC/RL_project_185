"""NeurIPS-style headline bar chart v4 — horizon-annotated, palette-consistent.

Differences from v3:
  - Each method's training horizon is annotated next to its name in the legend
    AND, to make the cross-horizon nature unmissable, under each clustered bar
    we draw a tiny italic-gray "horizon stamp" for the per-(env, method) cell.
  - Palette aligned with `make_fig_learning_curves_v2.py`:
        vlm_cf      -> CB10 blue   (#006BA4)
        verified_cf -> Okabe purple (#CC79A7)
        Oracle-CF   -> Okabe green  (#009E73)
        HER         -> CB10 orange  (#FF800E)
        PER         -> CB10 mid-blue (#5F9ED1)   <-- moved off #006BA4 so vlm_cf
                                                    can own that color
        Uniform     -> neutral gray  (#ABABAB)
  - Caption (set in the .tex) will be updated to flag heterogeneous horizons.

Run from project root with project venv active:
    .venv/bin/python agent_reports/make_fig_headline_v4.py

Outputs:
    agent_reports/figs/fig_headline_v4.png
    agent_reports/figs/fig_headline_v4.pdf
"""
from __future__ import annotations

import pathlib

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

# --- NeurIPS-style rcParams -------------------------------------------------
mpl.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "legend.frameon": False,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": "#dddddd",
    "grid.linewidth": 0.5,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

ENVS = ["FetchPush", "FetchPickAndPlace", "FetchSlide"]

# ---------------------------------------------------------------------------
# Data — kept consistent with v3 so seed-level numbers match the paper text.
# ---------------------------------------------------------------------------
SEEDS = {
    ("Uniform", "FetchPush"): None,
    ("Uniform", "FetchPickAndPlace"): None,
    ("Uniform", "FetchSlide"): None,
    ("PER", "FetchPush"): None,
    ("PER", "FetchPickAndPlace"): None,
    ("PER", "FetchSlide"): None,
    ("HER", "FetchPush"): [0.700, 0.450, 0.700],
    ("HER", "FetchPickAndPlace"): [0.100, 0.050, 0.400],
    ("HER", "FetchSlide"): [0.200, 0.100, 0.250],
    ("Oracle-CF", "FetchPush"): [0.300, 0.250, 0.600],
    ("Oracle-CF", "FetchPickAndPlace"): [0.30, 0.90, 0.55],
    ("Oracle-CF", "FetchSlide"): [0.200, 0.200, 0.150],
    ("vlm_cf", "FetchPush"): [1.00, 0.95, 0.90],
    ("vlm_cf", "FetchPickAndPlace"): [0.35, 0.35, 0.50],
    ("vlm_cf", "FetchSlide"): [0.25, 0.70, 0.70],
    ("verified_cf", "FetchPush"):        [0.65, 0.90, 1.00],
    ("verified_cf", "FetchPickAndPlace"): [0.25, 0.30, 0.50],
    ("verified_cf", "FetchSlide"):       [0.60, 0.65, 0.60],
}

SUMMARY_MEAN_SE = {
    ("Uniform", "FetchPush"): (0.08, 0.05),
    ("Uniform", "FetchPickAndPlace"): (0.07, 0.05),
    ("Uniform", "FetchSlide"): (0.08, 0.07),
    ("PER", "FetchPush"): (0.95, 0.02),
    ("PER", "FetchPickAndPlace"): (0.10, 0.04),
    ("PER", "FetchSlide"): (0.10, 0.06),
}

# Per-(method, env) horizons, used for the tiny italic stamp below each bar
# AND for the legend annotation. Cross-horizon: yes, that's the whole point of
# this figure being explicit about it.
HORIZON_PER_CELL = {
    ("Uniform", "FetchPush"): "3M",
    ("Uniform", "FetchPickAndPlace"): "3M",
    ("Uniform", "FetchSlide"): "3M",
    ("PER", "FetchPush"): "3M",
    ("PER", "FetchPickAndPlace"): "3M",
    ("PER", "FetchSlide"): "3M",
    ("HER", "FetchPush"): "250k",
    ("HER", "FetchPickAndPlace"): "250k",
    ("HER", "FetchSlide"): "250k",
    ("Oracle-CF", "FetchPush"): "250k",
    ("Oracle-CF", "FetchPickAndPlace"): "1M",
    ("Oracle-CF", "FetchSlide"): "250k",
    ("vlm_cf", "FetchPush"): "500k",
    ("vlm_cf", "FetchPickAndPlace"): "500k",
    ("vlm_cf", "FetchSlide"): "500k",
    ("verified_cf", "FetchPush"): "500k",
    ("verified_cf", "FetchPickAndPlace"): "500k",
    ("verified_cf", "FetchSlide"): "500k",
}

# Method-level summary horizon for the legend.
HORIZON_LEGEND = {
    "Uniform":     "3M",
    "PER":         "3M",
    "HER":         "250k",
    "Oracle-CF":   "250k/1M",
    "vlm_cf":      "500k",
    "verified_cf": "500k",
}


def _agg(method: str, env: str):
    seeds = SEEDS.get((method, env))
    if seeds is not None and len(seeds) > 0:
        arr = np.asarray(seeds, dtype=float)
        mean = float(arr.mean())
        se = float(arr.std(ddof=1) / np.sqrt(arr.size)) if arr.size > 1 else 0.0
        return mean, se, arr
    if (method, env) in SUMMARY_MEAN_SE:
        m, s = SUMMARY_MEAN_SE[(method, env)]
        return float(m), float(s), None
    return None, None, None


METHODS = ["Uniform", "PER", "HER", "Oracle-CF", "vlm_cf", "verified_cf"]

# CB-safe palette, unified across all figures (headline + learning curves +
# C1v2 / cross-task as much as the data those figures encode allows).
PALETTE = {
    "Uniform":     "#ABABAB",   # neutral gray (uniform replay)
    "PER":         "#5F9ED1",   # CB10 mid-blue (baseline PER)
    "HER":         "#FF800E",   # CB10 orange   (HER baseline)
    "Oracle-CF":   "#009E73",   # Okabe-Ito bluish-green (oracle upper envelope)
    "vlm_cf":      "#006BA4",   # CB10 dark blue (our main method)
    "verified_cf": "#CC79A7",   # Okabe-Ito reddish-purple (our verified method)
}

DISPLAY = {
    "Uniform":     "Uniform",
    "PER":         "PER",
    "HER":         "HER",
    "Oracle-CF":   "Oracle-CF",
    "vlm_cf":      "vlm_cf (ours)",
    "verified_cf": "verified_cf (ours)",
}


def fig_headline_v4(out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    x = np.arange(len(ENVS))
    n = len(METHODS)
    bar_w = 0.86 / n

    drawn = set()

    for i, m in enumerate(METHODS):
        offset = (i - (n - 1) / 2) * bar_w
        for j, env in enumerate(ENVS):
            mean, se, seeds = _agg(m, env)
            if mean is None:
                continue
            xpos = x[j] + offset
            ax.bar(
                xpos, mean, bar_w,
                yerr=se, color=PALETTE[m],
                edgecolor="white", linewidth=0.4,
                error_kw=dict(elinewidth=0.7, capsize=2.0,
                              capthick=0.7, ecolor="#333333"),
                label=f"{DISPLAY[m]} ({HORIZON_LEGEND[m]})" if m not in drawn else None,
                zorder=3,
            )
            drawn.add(m)

            if seeds is not None and seeds.size > 0:
                rng = np.random.default_rng(42 + i * 17 + j * 3)
                jitter = rng.uniform(-bar_w * 0.22, bar_w * 0.22, size=seeds.size)
                ax.scatter(
                    np.full_like(seeds, xpos) + jitter,
                    seeds,
                    s=12, color="white",
                    edgecolors="#222222", linewidths=0.6,
                    zorder=5, clip_on=True,
                )

            # Per-cell horizon stamp: tiny italic-gray text just BELOW the
            # x-axis under each bar. This is the bulletproof bit — the bars
            # themselves now carry the training horizon.
            h_label = HORIZON_PER_CELL.get((m, env))
            if h_label is not None:
                ax.annotate(
                    h_label,
                    xy=(xpos, 0),
                    xytext=(0, -2),
                    textcoords="offset points",
                    ha="center", va="top",
                    fontsize=6.0, color="#777777", style="italic",
                    annotation_clip=False,
                )

    # HER per-env reference dashed line (helps within-env reading).
    her_line_added = False
    for j, env in enumerate(ENVS):
        mean, _, _ = _agg("HER", env)
        if mean is None:
            continue
        x_left = x[j] - 0.45
        x_right = x[j] + 0.45
        ax.hlines(
            mean, x_left, x_right,
            colors="#555555", linestyles=(0, (4, 2)),
            linewidth=0.9, alpha=0.7, zorder=2,
            label="HER reference (250k)" if not her_line_added else None,
        )
        her_line_added = True

    ax.set_xticks(x)
    # Bump env tick labels down a touch to make room for the per-cell horizon
    # stamps written between bars and tick labels.
    ax.tick_params(axis="x", pad=10)
    ax.set_xticklabels(ENVS)
    ax.set_ylabel("Final success rate (mean +/- SE, n=3)")
    ax.set_ylim(0, 1.08)
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.grid(axis="x", visible=False)

    handles, labels = ax.get_legend_handles_labels()
    seed_proxy = ax.scatter([], [], s=12, color="white",
                            edgecolors="#222222", linewidths=0.6,
                            label="individual seeds")
    handles.append(seed_proxy)
    labels.append("individual seeds")

    leg = ax.legend(
        handles, labels,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.20),
        ncols=4, columnspacing=1.2,
        handlelength=1.4, handletextpad=0.5,
        borderpad=0.4, labelspacing=0.4,
    )

    # Below-legend note: explicit cross-horizon flag.
    ax.annotate(
        "Italic gray stamp under each bar = training horizon for that cell. "
        "Cross-horizon comparisons should be read as efficiency claims, not "
        "asymptotic dominance.",
        xy=(0.5, -0.40), xycoords="axes fraction",
        ha="center", va="top",
        fontsize=6.8, color="#666666", style="italic",
        wrap=True,
    )

    fig.savefig(out_path, bbox_extra_artists=(leg,))
    plt.close(fig)


if __name__ == "__main__":
    figs_dir = pathlib.Path(__file__).parent / "figs"
    figs_dir.mkdir(exist_ok=True)
    png = figs_dir / "fig_headline_v4.png"
    pdf = figs_dir / "fig_headline_v4.pdf"
    fig_headline_v4(str(png))
    fig_headline_v4(str(pdf))
    print(f"wrote {png}")
    print(f"wrote {pdf}")
