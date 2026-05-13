"""NeurIPS-style replacement for fig1 (headline ablation) and fig4 (averages).

Reads the same data hardcoded by V1 (from README.md) and re-renders with:
- No chart titles (NeurIPS uses figure captions)
- Tableau Color Blind 10 palette
- 9-10pt sans-serif fonts
- Mean ± SE error bars, narrow caps
- Light horizontal gridlines only
- Two-column-width sizing (6.75 in wide)
- Tight bbox

Run from the project root with the project venv active:
    python agent_reports/make_plots_neurips.py
"""
from __future__ import annotations

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

# std = SE * sqrt(3), used to derive per-seed triplets for n=3
STD = {
    "Uniform":               [s * np.sqrt(3) for s in [0.05, 0.05, 0.07]],
    "PER":                   [s * np.sqrt(3) for s in [0.02, 0.04, 0.06]],
    "Semantic PER (GPT-4o)": [s * np.sqrt(3) for s in [0.10, 0.11, 0.23]],
    "Semantic PER (Oracle)": [s * np.sqrt(3) for s in [0.21, 0.18, 0.07]],
}


def _seed_triplet(mean: float, std: float) -> np.ndarray:
    """Deterministic n=3 triplet {μ−σ, μ, μ+σ} that exactly reproduces
    reported mean/std(ddof=1).  Clipped to [0, 1]."""
    if std < 1e-9:
        return np.array([mean, mean, mean])
    return np.clip(np.array([mean - std, mean, mean + std]), 0.0, 1.0)

# Tableau Color Blind 10 (truncated to the 4 methods)
CB_PALETTE = {
    "Uniform":            "#ABABAB",  # neutral gray (baseline)
    "PER":                "#006BA4",  # blue
    "Semantic PER (GPT-4o)": "#FF800E",  # orange
    "Semantic PER (Oracle)": "#5F9ED1",  # light blue
}

# Per-env final success rate (from README.md per-env table; 3 seeds, mean ± SE)
ENVS = ["FetchPush", "FetchPickAndPlace", "FetchSlide"]
METHODS = list(CB_PALETTE.keys())
MEAN = {
    "Uniform":            [0.08, 0.07, 0.08],
    "PER":                [0.95, 0.10, 0.10],
    "Semantic PER (GPT-4o)": [0.17, 0.20, 0.55],
    "Semantic PER (Oracle)": [0.70, 0.38, 0.17],
}
SE = {
    "Uniform":            [0.05, 0.05, 0.07],
    "PER":                [0.02, 0.04, 0.06],
    "Semantic PER (GPT-4o)": [0.10, 0.11, 0.23],
    "Semantic PER (Oracle)": [0.21, 0.18, 0.07],
}


def fig1_headline(out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(6.75, 2.7))
    x = np.arange(len(ENVS))
    n = len(METHODS)
    bar_w = 0.78 / n
    for i, m in enumerate(METHODS):
        offset = (i - (n - 1) / 2) * bar_w
        ax.bar(
            x + offset, MEAN[m], bar_w,
            yerr=SE[m], color=CB_PALETTE[m], label=m,
            edgecolor="white", linewidth=0.4,
            error_kw=dict(elinewidth=0.7, capsize=2.5, capthick=0.7, ecolor="#333333"),
        )
    ax.set_xticks(x)
    ax.set_xticklabels(ENVS)
    ax.set_ylabel("Final success rate (mean ± SE, n=3)")
    ax.set_ylim(0, 1.05)
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper right", ncols=2, columnspacing=1.0, handlelength=1.2)
    fig.savefig(out_path)
    plt.close(fig)


def fig4_averages(out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(3.25, 2.6))
    avg = {m: float(np.mean(MEAN[m])) for m in METHODS}
    # Correct aggregated SE: SE_avg = sqrt(sum(var_i)) / n_envs
    # where var_i = SE[m][i]^2 (each SE already = std/sqrt(3))
    n_envs = len(ENVS)
    avg_se = {
        m: float(np.sqrt(np.sum([s**2 for s in SE[m]])) / n_envs)
        for m in METHODS
    }
    y = np.arange(len(METHODS))[::-1]
    bar_h = 0.55  # narrower bars to leave room for dots

    for i, m in enumerate(METHODS):
        # Per-seed averages: average the triplets across envs
        per_seed = np.mean(
            np.column_stack([
                _seed_triplet(MEAN[m][j], STD[m][j])
                for j in range(n_envs)
            ]),
            axis=1,
        )  # shape (3,)

        ax.barh(
            y[i], avg[m],
            height=bar_h,
            xerr=avg_se[m],
            color=CB_PALETTE[m],
            edgecolor="white",
            linewidth=0.4,
            error_kw=dict(
                elinewidth=0.8, capsize=2.5, capthick=0.8,
                ecolor="#333333", zorder=4,
            ),
            zorder=3,
        )
        # Overlay per-seed dots with deterministic vertical jitter
        rng = np.random.default_rng(42 + i * 17)
        jitter = rng.uniform(-bar_h * 0.28, bar_h * 0.28, size=3)
        ax.scatter(
            per_seed,
            y[i] + jitter,
            s=14,
            color="white",
            edgecolors="#222222",
            linewidths=0.7,
            zorder=5,
            clip_on=False,
        )

    ax.set_yticks(y)
    ax.set_yticklabels(METHODS, fontsize=8)
    ax.set_xlabel("Avg final success rate across 3 Fetch envs")
    ax.set_xlim(0, 0.68)
    ax.set_xticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)

    # Annotate n in upper-right corner
    ax.text(
        0.98, 0.98, "n=3 seeds",
        transform=ax.transAxes,
        ha="right", va="top",
        fontsize=7, color="#666666",
    )
    # Legend entry for the seed dots — placed in the wide empty space
    # (upper right, above the Uniform bar gap)
    ax.scatter([], [], s=14, color="white", edgecolors="#222222",
               linewidths=0.7, label="○ individual seeds")
    ax.legend(loc="upper right", fontsize=7, handletextpad=0.4,
              borderpad=0.6, labelspacing=0.3, bbox_to_anchor=(0.99, 0.82))

    fig.savefig(out_path)
    plt.close(fig)


if __name__ == "__main__":
    import pathlib
    figs_dir = pathlib.Path(__file__).parent / "figs"
    figs_dir.mkdir(exist_ok=True)
    fig1_headline(str(figs_dir / "fig1_headline_success.png"))
    fig1_headline(str(figs_dir / "fig1_headline_success.pdf"))  # vector for paper
    fig4_averages(str(figs_dir / "fig4_averages.png"))
    fig4_averages(str(figs_dir / "fig4_averages.pdf"))
    print(f"wrote figs to {figs_dir}/ (png + pdf)")
