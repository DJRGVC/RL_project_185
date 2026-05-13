"""NeurIPS-style figure for Agent N2: cross-task VLM-signal transferability.

Three side-by-side metrics, per env:
  1. Parse rate: VLM produces a well-formed JSON / valid keyframe index.
  2. Independent judge: VLM reasoning describes a task-relevant failure mode.
  3. Tolerant keyframe agreement (±1 keyframe slot) with the heuristic oracle.

Saves to agent_reports/figs/figN2_cross_task_transfer.{png,pdf}.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

# --- NeurIPS-style rcParams (matches feedback memory) ---------------------
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

# Tableau Color Blind 10
COL_PARSE = "#006BA4"          # blue
COL_JUDGE = "#FF800E"          # orange
COL_AGREE = "#5F9ED1"          # light blue

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "agent_reports" / "N2_cross_task_validation_outputs.json"

with open(DATA) as f:
    d = json.load(f)

# Order envs as Push, PickAndPlace, Slide (task-difficulty ordering).
ENV_ORDER = ["FetchPush-v4", "FetchPickAndPlace-v4", "FetchSlide-v4"]
ENV_LABELS = ["FetchPush", "FetchPickPlace", "FetchSlide"]

def _se(p, n):
    if n == 0:
        return 0.0
    return float(np.sqrt(p * (1 - p) / n))

parse_rates, judge_rates, agree_rates = [], [], []
parse_se, judge_se, agree_se = [], [], []
# Per-episode values for jitter dots (0.0 or 1.0 per episode).
parse_dots, judge_dots, agree_dots = [], [], []
for env in ENV_ORDER:
    rows = [r for r in d["episodes"] if r["env_name"] == env]
    n = len(rows)
    # Parse rate.
    n_parsed = sum(1 for r in rows if r["vlm"]["parsed"])
    parse_rates.append(n_parsed / n if n else 0.0)
    parse_se.append(_se(parse_rates[-1], n))
    parse_dots.append([1.0 if r["vlm"]["parsed"] else 0.0 for r in rows])
    # Tolerant agreement (±1 keyframe slot).
    n_tol = sum(1 for r in rows if r["agreement"]["tolerant_keyframe"])
    agree_rates.append(n_tol / n if n else 0.0)
    agree_se.append(_se(agree_rates[-1], n))
    agree_dots.append([1.0 if r["agreement"]["tolerant_keyframe"] else 0.0 for r in rows])
    # Independent judge: task_relevant.
    jrows = [j for j in d.get("judgements", []) if j.get("env") == env and "task_relevant" in j]
    n_j = len(jrows)
    n_jp = sum(j.get("task_relevant", 0) for j in jrows)
    judge_rates.append(n_jp / n_j if n_j else 0.0)
    judge_se.append(_se(judge_rates[-1], n_j))
    judge_dots.append([float(j.get("task_relevant", 0)) for j in jrows])

# Set up grouped bar chart.
fig, ax = plt.subplots(figsize=(6.75, 2.6))
x = np.arange(len(ENV_LABELS))
bar_w = 0.27

rng = np.random.default_rng(42)

cap = dict(capsize=2.5, capthick=0.8, elinewidth=0.8)
ax.bar(x - bar_w, parse_rates, bar_w, yerr=parse_se,
       label="Parse rate", color=COL_PARSE, edgecolor="white",
       linewidth=0.6, error_kw=cap)
ax.bar(x, judge_rates, bar_w, yerr=judge_se,
       label="Task-relevant (judge)", color=COL_JUDGE, edgecolor="white",
       linewidth=0.6, error_kw=cap)
ax.bar(x + bar_w, agree_rates, bar_w, yerr=agree_se,
       label="Tolerant kf agreement", color=COL_AGREE, edgecolor="white",
       linewidth=0.6, error_kw=cap)

# Per-episode dots overlaid on each bar group.
jitter_scale = 0.06
for i, xi in enumerate(x):
    n_ep = len(parse_dots[i])
    jit = rng.uniform(-jitter_scale, jitter_scale, n_ep)
    # Parse dots.
    ax.scatter(xi - bar_w + jit, parse_dots[i],
               s=12, color="white", edgecolors="#333333", linewidths=0.6,
               zorder=5, clip_on=False)
    # Judge dots.
    jit = rng.uniform(-jitter_scale, jitter_scale, len(judge_dots[i]))
    ax.scatter(xi + jit, judge_dots[i],
               s=12, color="white", edgecolors="#333333", linewidths=0.6,
               zorder=5, clip_on=False)
    # Agreement dots.
    jit = rng.uniform(-jitter_scale, jitter_scale, len(agree_dots[i]))
    ax.scatter(xi + bar_w + jit, agree_dots[i],
               s=12, color="white", edgecolors="#333333", linewidths=0.6,
               zorder=5, clip_on=False)

ax.set_xticks(x)
ax.set_xticklabels(ENV_LABELS)
ax.set_ylabel("Rate")
ax.set_ylim(0, 1.12)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
# Horizontal gridlines only (suppress vertical grid introduced by rcParams default).
ax.grid(False)
ax.yaxis.grid(True, color="#dddddd", linewidth=0.5)
ax.set_axisbelow(True)

ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.4), ncol=3, frameon=False)

# Annotate sample size below the x-axis label.
n_per_env = [sum(1 for r in d["episodes"] if r["env_name"] == env) for env in ENV_ORDER]
ax.text(0.5, -0.2, f"n = {n_per_env[0]} episodes per env",
        transform=ax.transAxes, ha="center", va="top",
        fontsize=8, color="#555555")

out_dir = REPO / "agent_reports" / "figs"
out_dir.mkdir(parents=True, exist_ok=True)
for ext in ("png", "pdf"):
    p = out_dir / f"figN2_cross_task_transfer.{ext}"
    plt.savefig(p)
    print("Wrote", p)
plt.close()

# Print rates for inclusion in the report.
print("\nPer-env rates:")
for label, env, p, j, a in zip(ENV_LABELS, ENV_ORDER, parse_rates, judge_rates, agree_rates):
    n = sum(1 for r in d["episodes"] if r["env_name"] == env)
    print(f"  {label:18s} (n={n}): parse={p:.2f}, judge={j:.2f}, tolerant_agree={a:.2f}")
