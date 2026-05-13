"""Morning consolidation headline figure.

Methods × envs grouped-bar chart with mean ± SE error bars and per-seed dots.
Includes a horizontal annotation for the pre-registered KILL band
(HER mean + 0.10 on FetchPickAndPlace).

All data are pulled from W&B (entity d-grant-uc-berkeley, project RL_project)
across tags path_c_overnight_2026-05-11, path_a_pivot_2026-05-12,
oracle_cf_pushfix. NeurIPS-style rcParams; two-column width.

Run from project root with venv active:
    python agent_reports/make_fig_morning_headline.py
"""
from __future__ import annotations

import json
import pathlib
import sys

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
    "legend.fontsize": 7.5,
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

# Tableau Color Blind 10 (CB-safe)
CB_PALETTE = {
    "HER":                    "#006BA4",  # blue
    "Oracle-CF":              "#FF800E",  # orange
    "Oracle-CF (fix, Push)":  "#A2C8EC",  # light blue (Push-only post-fix)
    "Path A Bidir":           "#595959",  # dark gray
}

# Final eval-success seeds for each cell, pulled from W&B (see source notes).
# n=3 for HER / Oracle-CF cells; n=2 for Path A Bidir cells (only s42 + s123 ran).
DATA = {
    "HER": {
        "FetchPush":           [0.450, 0.600, 0.600],   # s123, s42, s999
        "FetchPickAndPlace":   [0.050, 0.050, 0.400],   # s42, s123, s999
        "FetchSlide":          [0.200, 0.050, 0.050],   # s42, s123, s999
    },
    "Oracle-CF": {
        # Pre-fix Push values shown for reference; we use the post-fix Push
        # numbers in the dedicated post-fix series so Oracle-CF here is the
        # original Phase-1 oracle without the midpoint correction.
        "FetchPush":           [0.100, 0.350, 0.200],   # pre-fix, KILL band only
        "FetchPickAndPlace":   [0.100, 0.050, 0.200],   # s42, s123, s999
        "FetchSlide":          [0.200, 0.200, 0.150],   # s42, s123, s999
    },
    "Oracle-CF (fix, Push)": {
        "FetchPush":           [0.300, 0.250, 0.600],   # post-fix s42, s123, s999
        "FetchPickAndPlace":   [],                        # not run (intentional)
        "FetchSlide":          [],
    },
    "Path A Bidir": {
        # 6 runs (3 envs × 2 seeds), 300k steps.
        "FetchPush":           [0.400, 0.000],          # s42, s123
        "FetchPickAndPlace":   [0.000, 0.000],
        "FetchSlide":          [0.000, 0.000],
    },
}

ENVS = ["FetchPush", "FetchPickAndPlace", "FetchSlide"]
METHODS = list(CB_PALETTE.keys())

# Pre-registered kill threshold: Oracle-CF needs HER + 0.10 on FetchPickAndPlace.
KILL_DELTA = 0.10
HER_PNP_MEAN = float(np.mean(DATA["HER"]["FetchPickAndPlace"]))  # 0.1667
KILL_THRESHOLD = HER_PNP_MEAN + KILL_DELTA  # 0.2667


def _mean_se(values: list[float]) -> tuple[float, float]:
    if not values:
        return (np.nan, 0.0)
    arr = np.array(values, dtype=float)
    if len(arr) == 1:
        return (float(arr[0]), 0.0)
    return (float(arr.mean()), float(arr.std(ddof=1) / np.sqrt(len(arr))))


def make_figure(out_png: str, out_pdf: str) -> None:
    fig, ax = plt.subplots(figsize=(6.75, 3.0))
    x = np.arange(len(ENVS))
    n_methods = len(METHODS)
    bar_w = 0.78 / n_methods

    # Pre-registered kill threshold on FetchPickAndPlace (HER mean + 0.10).
    # Drawn as a muted dashed line; label placed in the figure caption, not
    # inline, per NeurIPS convention (no verbose text annotations on plots).
    pnp_idx = ENVS.index("FetchPickAndPlace")
    cluster_left = pnp_idx - 0.45
    cluster_right = pnp_idx + 0.45
    ax.hlines(
        KILL_THRESHOLD, cluster_left, cluster_right,
        colors="#595959", linestyles=(0, (4, 2)), linewidth=1.0, zorder=4,
        label=f"kill bar (PnP, HER+0.10)",
    )

    for i, m in enumerate(METHODS):
        offset = (i - (n_methods - 1) / 2) * bar_w
        means = []
        ses = []
        seed_arrays = []
        for env in ENVS:
            mu, se = _mean_se(DATA[m][env])
            means.append(mu)
            ses.append(se)
            seed_arrays.append(DATA[m][env])

        # mask NaN for absent cells so bars don't render at 0
        means_arr = np.array(means, dtype=float)
        ses_arr = np.array(ses, dtype=float)
        valid = ~np.isnan(means_arr)
        means_plot = np.where(valid, means_arr, 0)
        ses_plot = np.where(valid, ses_arr, 0)

        # Make the post-fix Push bar hatched so it reads as a "spotlight" overlay
        hatch = "///" if m == "Oracle-CF (fix, Push)" else None
        ax.bar(
            x + offset,
            means_plot,
            bar_w,
            yerr=ses_plot,
            color=CB_PALETTE[m],
            edgecolor="white",
            linewidth=0.4,
            label=m,
            hatch=hatch,
            error_kw=dict(elinewidth=0.7, capsize=2.0, capthick=0.7,
                          ecolor="#333333"),
            zorder=3,
        )

        # Per-seed dots (deterministic horizontal jitter inside each bar)
        rng = np.random.default_rng(7 + i * 13)
        for j, env in enumerate(ENVS):
            if not valid[j]:
                continue
            seeds = seed_arrays[j]
            if not seeds:
                continue
            xj = x[j] + offset + rng.uniform(-bar_w * 0.22, bar_w * 0.22, size=len(seeds))
            ax.scatter(
                xj, seeds,
                s=11, color="white", edgecolors="#222222",
                linewidths=0.6, zorder=5, clip_on=False,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(ENVS)
    ax.set_ylabel("Final eval success rate (mean $\\pm$ SE)")
    ax.set_ylim(0, 0.85)
    ax.set_yticks(np.arange(0, 0.81, 0.2))
    ax.grid(axis="x", visible=False)

    # Legend: 4 bar methods + kill-bar line + seed-dot proxy
    ax.scatter([], [], s=11, color="white", edgecolors="#222222",
               linewidths=0.6, label="individual seeds")
    ax.legend(
        loc="upper right", ncols=2, columnspacing=0.9,
        handlelength=1.4, handletextpad=0.4, borderpad=0.4,
    )

    fig.savefig(out_png)
    fig.savefig(out_pdf)
    plt.close(fig)


def main() -> None:
    figs_dir = pathlib.Path(__file__).parent / "figs"
    figs_dir.mkdir(exist_ok=True)
    out_png = str(figs_dir / "fig_morning_headline.png")
    out_pdf = str(figs_dir / "fig_morning_headline.pdf")
    make_figure(out_png, out_pdf)
    # Print a quick summary so the caller can sanity-check the means.
    print("Means and SEs (n in brackets):")
    for m in METHODS:
        row = []
        for env in ENVS:
            mu, se = _mean_se(DATA[m][env])
            n = len(DATA[m][env])
            row.append(f"{env}={mu:.3f}±{se:.3f}[n={n}]" if n > 0 else f"{env}=NA")
        print(f"  {m:24s} " + "  ".join(row))
    print(f"HER PnP mean = {HER_PNP_MEAN:.4f}; KILL threshold = {KILL_THRESHOLD:.4f}")
    print(f"Wrote: {out_png}\n       {out_pdf}")


if __name__ == "__main__":
    main()
