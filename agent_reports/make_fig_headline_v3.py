"""NeurIPS-style updated headline bar chart (Figure 1 v3).

Adds verified_cf as a NEW method group alongside vlm_cf using the
Phase 2 attempt-5 final-eval seeds. All other method groups are
inherited from fig_headline_v2.

Run from project root with the project venv active:
    .venv/bin/python agent_reports/make_fig_headline_v3.py

Outputs:
    agent_reports/figs/fig_headline_v3.png
    agent_reports/figs/fig_headline_v3.pdf
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
# Data — ground-truthed against:
#   - existing fig1 (Uniform, PER): agent_reports/make_plots_neurips.py
#   - HER + Oracle-CF Phase 1: agent_reports/CODE-REVIEWER_handoff.md table
#   - Oracle-CF post-fix Push: agent_reports/MORNING_REPORT_2026-05-12.md
#   - Oracle-CF 1M PnP: brief (mean 0.583 from seeds 0.30/0.90/0.55)
#   - vlm_cf attempt-5: agent_reports/paper/main.tex §5.6(C)
#   - verified_cf Phase 2 attempt-5 (path_c_vlm_vcf_* runs, 500k steps,
#     all 9 verified in W&B 2026-05-12)
#
# Convention: seed lists are [s42, s123, s999] for n=3 seeds.
# SE is reported as std(ddof=1) / sqrt(n).
# ---------------------------------------------------------------------------

SEEDS = {
    # 36-run aggregates have no per-seed list.
    ("Uniform", "FetchPush"): None,
    ("Uniform", "FetchPickAndPlace"): None,
    ("Uniform", "FetchSlide"): None,
    ("PER", "FetchPush"): None,
    ("PER", "FetchPickAndPlace"): None,
    ("PER", "FetchSlide"): None,
    ("HER", "FetchPush"): [0.700, 0.450, 0.700],
    ("HER", "FetchPickAndPlace"): [0.100, 0.050, 0.400],
    ("HER", "FetchSlide"): [0.200, 0.100, 0.250],
    # Oracle-CF: best-available horizon per env.
    ("Oracle-CF", "FetchPush"): [0.300, 0.250, 0.600],
    ("Oracle-CF", "FetchPickAndPlace"): [0.30, 0.90, 0.55],
    ("Oracle-CF", "FetchSlide"): [0.200, 0.200, 0.150],
    # vlm_cf attempt-5 final eval numbers.
    ("vlm_cf", "FetchPush"): [1.00, 0.95, 0.90],
    ("vlm_cf", "FetchPickAndPlace"): [0.35, 0.35, 0.50],
    ("vlm_cf", "FetchSlide"): [0.25, 0.70, 0.70],
    # verified_cf Phase 2 attempt-5 final eval (500k), seeds [42, 123, 999].
    # Verified against W&B path_c_vlm_vcf_* on 2026-05-12.
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
HORIZONS = {
    "Uniform":     "3M steps",
    "PER":         "3M steps",
    "HER":         "250k steps",
    "Oracle-CF":   "250k-1M",
    "vlm_cf":      "500k steps",
    "verified_cf": "500k steps",
}
# CB-safe palette. vlm_cf keeps the green headline; verified_cf gets a
# distinct CB-safe purple (Okabe-Ito reddish-purple) so the two CF
# mechanisms are immediately readable as a pair.
PALETTE = {
    "Uniform":     "#ABABAB",   # neutral gray
    "PER":         "#006BA4",   # CB10 blue
    "HER":         "#FF800E",   # CB10 orange
    "Oracle-CF":   "#A2C8EC",   # CB10 light blue
    "vlm_cf":      "#2CA02C",   # green — vlm_cf headline
    "verified_cf": "#CC79A7",   # Okabe-Ito reddish-purple — verified_cf
}
# Display labels (markdown-style 'ours' tag retained for the two CF methods).
DISPLAY = {
    "Uniform":     "Uniform",
    "PER":         "PER",
    "HER":         "HER",
    "Oracle-CF":   "Oracle-CF",
    "vlm_cf":      "vlm_cf (ours)",
    "verified_cf": "verified_cf (ours)",
}


def fig_headline_v3(out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(6.75, 3.6))
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
                label=DISPLAY[m] if m not in drawn else None,
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

    # HER per-env reference dashed line.
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
        bbox_to_anchor=(0.5, -0.28),
        ncols=4, columnspacing=1.2,
        handlelength=1.4, handletextpad=0.5,
        borderpad=0.4, labelspacing=0.4,
    )

    row1 = "  ".join(f"{DISPLAY[m]}: {HORIZONS[m]}" for m in METHODS[:3])
    row2 = "  ".join(f"{DISPLAY[m]}: {HORIZONS[m]}" for m in METHODS[3:])
    ax.annotate(
        row1 + "\n" + row2,
        xy=(0.5, -0.105), xycoords="axes fraction",
        ha="center", va="top",
        fontsize=7, color="#555555", style="italic",
    )

    fig.savefig(out_path, bbox_extra_artists=(leg,))
    plt.close(fig)


if __name__ == "__main__":
    figs_dir = pathlib.Path(__file__).parent / "figs"
    figs_dir.mkdir(exist_ok=True)
    png = figs_dir / "fig_headline_v3.png"
    pdf = figs_dir / "fig_headline_v3.pdf"
    fig_headline_v3(str(png))
    fig_headline_v3(str(pdf))
    print(f"wrote {png}")
    print(f"wrote {pdf}")
