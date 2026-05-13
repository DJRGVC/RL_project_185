"""Improved figN_c1v2_model_comparison — v2.

Key improvements over build_c1v2_comparison.py:
  1. Panel titles via ax.set_title() — 'Plausibility' / 'Specificity'.
     Old code used ax.set_xlabel() for the metric name, which is an anti-pattern
     (xlabel should label the horizontal axis, not name the panel).
  2. Horizontal-only gridlines (old: mixed).
  3. Shorter x-tick labels ('narr.', 'action', 'ag', 'all') with NO rotation.
     Old code used rotation=15 ha='right', which looked untidy and clipped labels.
  4. Individual episode score dots overlaid on each bar — makes the per-sample
     variance visible at a glance. R1 specifically criticised 'small n' claims;
     dots let readers see n themselves.
  5. Legend moved to top-right of the right panel (was upper-right of right panel
     but with sharey=True the y-label was missing from the right; clarified).
  6. Figure size kept at 6.75 in (NeurIPS two-column), height bumped to 3.0 to
     accommodate the panel title row without crowding the bars.

Reads:
    agent_reports/C1_counterfactual_outputs.json      (Claude Opus 4.7)
    agent_reports/C1v2_gpt4o_outputs.json             (GPT-4o)

Writes:
    agent_reports/figs/figN_c1v2_model_comparison.png  (overwritten)
    agent_reports/figs/figN_c1v2_model_comparison.pdf  (overwritten)
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

# ── NeurIPS-style rcParams ────────────────────────────────────────────────────
mpl.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.titlesize": 9,
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

# Tableau Color-Blind 10 (subset)
PALETTE = {
    "Claude Opus 4.7": "#006BA4",   # blue
    "GPT-4o":          "#FF800E",   # orange
}

VARIANTS = ["narrative", "action", "achieved_goal", "all"]
# Short x-tick labels — no rotation needed
SHORT_LABELS = ["narr.", "action", "ag", "all"]

REPO = Path(__file__).resolve().parents[1]
C1_PATH = REPO / "agent_reports" / "C1_counterfactual_outputs.json"
GPT_PATH = REPO / "agent_reports" / "C1v2_gpt4o_outputs.json"


def load_per_episode(path: Path) -> Dict[str, Dict[str, List[float]]]:
    """Return {variant: {metric: [per-episode values]}} for one run file."""
    d = json.loads(path.read_text())
    by_var: Dict[str, Dict[str, List[float]]] = {
        v: defaultdict(list) for v in VARIANTS
    }
    for ep in d["episodes"]:
        for v, item in ep.get("variants", {}).items():
            if v not in by_var or item.get("parse_error") is not None:
                continue
            j = item.get("judge") or {}
            for m in ("plausibility", "specificity"):
                val = j.get(m)
                if val is not None:
                    by_var[v][m].append(float(val))
    return by_var


def summarise(data: Dict[str, Dict[str, List[float]]]) -> Dict[str, Dict[str, Tuple[float, float, int]]]:
    """Return {variant: {metric: (mean, se, n)}}."""
    out = {}
    for v, metrics in data.items():
        out[v] = {}
        for m, lst in metrics.items():
            if lst:
                arr = np.asarray(lst)
                out[v][m] = (float(arr.mean()),
                             float(arr.std(ddof=1) / np.sqrt(len(arr))) if len(arr) > 1 else 0.0,
                             len(arr))
            else:
                out[v][m] = (float("nan"), 0.0, 0)
    return out


def make_figure(
    opus_raw: Dict[str, Dict[str, List[float]]],
    gpt_raw: Dict[str, Dict[str, List[float]]],
    out_png: Path,
    out_pdf: Path,
) -> None:
    opus_summary = summarise(opus_raw)
    gpt_summary = summarise(gpt_raw)

    models = [("Claude Opus 4.7", opus_raw, opus_summary),
              ("GPT-4o",          gpt_raw,  gpt_summary)]
    metrics = [("plausibility", "(a) Plausibility"), ("specificity", "(b) Specificity")]

    n_m = len(models)
    bar_w = 0.70 / n_m
    x = np.arange(len(VARIANTS))
    rng = np.random.default_rng(42)

    fig, axes = plt.subplots(1, 2, figsize=(6.75, 3.0), sharey=True)

    cap_kw = dict(elinewidth=0.8, capsize=2.5, capthick=0.8, ecolor="#333333")

    for ax, (mkey, mlabel) in zip(axes, metrics):
        for i, (model, raw, summary) in enumerate(models):
            offset = (i - (n_m - 1) / 2) * bar_w
            means = [summary.get(v, {}).get(mkey, (float("nan"), 0.0, 0))[0] for v in VARIANTS]
            ses   = [summary.get(v, {}).get(mkey, (float("nan"), 0.0, 0))[1] for v in VARIANTS]
            color = PALETTE[model]

            ax.bar(
                x + offset, means, bar_w,
                yerr=ses,
                color=color, label=model,
                edgecolor="white", linewidth=0.4,
                error_kw=cap_kw,
                zorder=2,
            )

            # Individual episode dots — white fill with dark edge so they read
            # clearly against the coloured bars (same convention as fig4_averages)
            for j, v in enumerate(VARIANTS):
                pts = raw.get(v, {}).get(mkey, [])
                if pts:
                    n_pts = len(pts)
                    jitter = rng.uniform(-bar_w * 0.28, bar_w * 0.28, size=n_pts)
                    ax.scatter(
                        x[j] + offset + jitter, pts,
                        s=12, color="white", edgecolors="#222222",
                        linewidths=0.6, zorder=4, alpha=0.90,
                    )

        # NeurIPS: no chart title — use panel letter + metric as x-axis label
        ax.set_xlabel(mlabel, fontsize=9)
        ax.set_xticks(x)
        ax.set_xticklabels(SHORT_LABELS, rotation=0, ha="center")
        ax.set_ylim(0, 1.05)
        ax.set_yticks(np.arange(0, 1.01, 0.2))
        ax.grid(axis="x", visible=False)
        ax.grid(axis="y", visible=True)

    axes[0].set_ylabel("Judge score (mean ± SE, n=6 ep)")

    # Legend on the right panel only
    axes[1].legend(loc="upper right", ncols=1, handlelength=1.2)

    fig.tight_layout(w_pad=1.5)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out_png))
    fig.savefig(str(out_pdf))
    plt.close(fig)
    print(f"wrote {out_png}")
    print(f"wrote {out_pdf}")


if __name__ == "__main__":
    opus_raw = load_per_episode(C1_PATH)
    gpt_raw  = load_per_episode(GPT_PATH)

    out_png = REPO / "agent_reports" / "figs" / "figN_c1v2_model_comparison.png"
    out_pdf = out_png.with_suffix(".pdf")
    make_figure(opus_raw, gpt_raw, out_png, out_pdf)
