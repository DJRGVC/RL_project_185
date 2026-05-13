"""Generate presentation figures for 9pm team review."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

OUT = Path("/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/figs")
OUT.mkdir(parents=True, exist_ok=True)

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

# ============================================================
# Source of truth: README.md results table (3 seeds x 4 methods x 3 envs)
# Mean and std taken directly from the project README. SE = std / sqrt(3).
# ============================================================
ENVS = ["FetchPush", "FetchPickAndPlace", "FetchSlide"]
METHODS = [
    ("Uniform",                "#9aa7b1"),
    ("PER",                    "#5a8fbf"),
    ("Semantic PER (GPT-4o)",  "#d99151"),
    ("Semantic PER (Oracle)",  "#3aa66e"),
]
# (env, method) -> (mean, std)
DATA = {
    ("FetchPush",         "Uniform"):                (0.083, 0.085),
    ("FetchPush",         "PER"):                    (0.950, 0.041),
    ("FetchPush",         "Semantic PER (GPT-4o)"):  (0.167, 0.170),
    ("FetchPush",         "Semantic PER (Oracle)"):  (0.700, 0.356),

    ("FetchPickAndPlace", "Uniform"):                (0.067, 0.094),
    ("FetchPickAndPlace", "PER"):                    (0.100, 0.071),
    ("FetchPickAndPlace", "Semantic PER (GPT-4o)"):  (0.200, 0.187),
    ("FetchPickAndPlace", "Semantic PER (Oracle)"):  (0.383, 0.306),

    ("FetchSlide",        "Uniform"):                (0.083, 0.118),
    ("FetchSlide",        "PER"):                    (0.100, 0.108),
    ("FetchSlide",        "Semantic PER (GPT-4o)"):  (0.550, 0.402),
    ("FetchSlide",        "Semantic PER (Oracle)"):  (0.167, 0.118),
}
N_SEEDS = 3
SE = lambda sd: sd / np.sqrt(N_SEEDS)


# ============================================================
# Figure 1: headline grouped bar chart
# ============================================================
def fig_headline():
    fig, ax = plt.subplots(figsize=(8.5, 4.0), dpi=170)
    n_methods = len(METHODS)
    n_envs = len(ENVS)
    bar_w = 0.20
    x = np.arange(n_envs)

    for i, (method, color) in enumerate(METHODS):
        means = [DATA[(env, method)][0] for env in ENVS]
        ses   = [SE(DATA[(env, method)][1]) for env in ENVS]
        offset = (i - (n_methods - 1) / 2) * bar_w
        bars = ax.bar(
            x + offset, means, bar_w,
            yerr=ses, capsize=3,
            label=method, color=color, edgecolor="white", linewidth=0.8,
            error_kw={"ecolor": "#444", "linewidth": 1.2},
        )
        # value labels above each bar
        for b, m in zip(bars, means):
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.03,
                    f"{m:.2f}", ha="center", va="bottom", fontsize=8, color="#333")

    ax.set_xticks(x)
    ax.set_xticklabels(ENVS, fontsize=10)
    ax.set_ylabel("Final success rate (eval, 20 ep)")
    ax.set_ylim(0, 1.10)
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.set_title("Existing ablation: 4 methods x 3 envs x 3 seeds (mean ± SE)", pad=10)
    ax.legend(loc="upper right", ncol=2, fontsize=8.5, frameon=True, framealpha=0.92)
    # subtle annotation for the standout finding
    ax.axhline(0, color="#bbb", linewidth=0.5)
    fig.tight_layout()
    out = OUT / "fig1_headline_success.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


# ============================================================
# Figure 2: differentiation table vs Sharony et al. 2602.01915
# ============================================================
def fig_differentiation():
    rows = [
        ("Axis",                 "VLM-RB (Sharony et al., Feb 2026)",                  "Ours (Path A + C)"),
        ("Signal direction",     "Success / goal-satisfaction",                        "Failure causation"),
        ("Granularity",          "32-frame sub-trajectory clip score",                 "Single causal timestep + bounded window"),
        ("TD blending",          "Mixture-with-uniform; lambda warm-up 0 -> 0.5",      "Multiplicative weight on |delta|, no warm-up"),
        ("VLM model",            "Frozen PerceptionLM (open-weights, async worker)",   "GPT-4o API + Claude (Path C); heuristic oracle"),
        ("Benchmark",            "MiniGrid DoorKey + OGBench Scene 3/4/5 (UR5e)",      "Gymnasium-Robotics Fetch (Push, PickPlace, Slide)"),
        ("Headroom analysis",    "None",                                               "Privileged-state Oracle quantifies VLM-attributable gap"),
        ("Counterfactual reuse", "Re-weights observed transitions only",               "Path C generates synthetic transitions from VLM goals"),
    ]
    fig, ax = plt.subplots(figsize=(11.0, 4.4), dpi=170)
    ax.axis("off")

    n_rows = len(rows)
    n_cols = 3
    col_widths = [0.16, 0.42, 0.42]
    col_x = np.concatenate(([0.0], np.cumsum(col_widths)))[:-1]
    row_h = 1.0 / n_rows

    for r, row in enumerate(rows):
        y_top = 1.0 - r * row_h
        y_bot = y_top - row_h
        for c, txt in enumerate(row):
            x0 = col_x[c]
            w  = col_widths[c]
            # header row styling
            if r == 0:
                ax.add_patch(plt.Rectangle((x0, y_bot), w, row_h,
                                           facecolor="#2c3e50", edgecolor="white"))
                ax.text(x0 + 0.01, y_bot + row_h/2, txt,
                        ha="left", va="center", color="white",
                        fontsize=10, fontweight="bold")
            else:
                fc = "#ecf2f6" if r % 2 == 0 else "#ffffff"
                ax.add_patch(plt.Rectangle((x0, y_bot), w, row_h,
                                           facecolor=fc, edgecolor="#d6dde2", linewidth=0.6))
                # first column bold
                weight = "bold" if c == 0 else "normal"
                color = "#2c3e50" if c == 0 else "#22313f"
                ax.text(x0 + 0.01, y_bot + row_h/2, txt,
                        ha="left", va="center", color=color,
                        fontsize=9.0, fontweight=weight, wrap=True)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.suptitle("Method comparison: VLM-RB vs. our work", y=1.00,
                 fontsize=12, fontweight="bold", color="#2c3e50")
    fig.tight_layout()
    out = OUT / "fig2_differentiation_table.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


# ============================================================
# Figure 3: Path A + Path C "what was built tonight" status box
# ============================================================
def fig_paths_status():
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), dpi=170)

    panels = [
        {
            "ax": axes[0],
            "title": "Path A  —  Causal failure localization",
            "color": "#3aa66e",
            "items": [
                ("A1 HER baselines",
                 "27 Modal jobs launched (her / her_per / her_semantic_per)",
                 ["3 methods x 3 envs x 3 seeds, heuristic localizer (no API cost)",
                  "First eval success points landing (~40k/1M steps)",
                  "Modal app ap-RlxdhxgDoMSFobTyggIZG8, tag her_baselines"]),
                ("A2 Oracle v3 (contact-aware)",
                 "Ballistic -> contact-loss -> argmin phase precedence",
                 ["New phase fires on contact-loss when object still off-goal",
                  "Validated on synthetic + real Fetch random-action rollouts",
                  "Degrades to v2 if ee/obj positions unavailable"]),
                ("A2 BidirectionalSemanticBuffer",
                 "Boost SUCCESS-like + FAILURE-causing transitions",
                 ["priority = TD * w_failure * w_success (multiplicative)",
                  "p=0 ablation cleanly recovers PER",
                  "configs/bidir.yaml + Modal verification runs launched"]),
            ],
        },
        {
            "ax": axes[1],
            "title": "Path C  —  Counterfactual VLM reasoning",
            "color": "#d99151",
            "items": [
                ("C1 Prompt prototyping",
                 "3 variants tested on 4 failed Fetch episodes",
                 ["narrative: plausibility 0.79 (Claude Opus 4.7 judge)",
                  "action 4-vec: 0.55  |  achieved_goal: bimodal by task",
                  "Anthropic backend live; OpenAI path implemented"]),
                ("C2 SAC-integration mechanism",
                 "Counterfactual-HER relabeling picked over shaping / aux head",
                 ["p_counterfactual=0 exactly recovers vanilla HER",
                  "Stub CounterfactualHERBuffer (~250 LOC) imports cleanly",
                  "Oracle-CF upper-bound experiment is the cheapest kill-test"]),
                ("Scoop check (L1 + L2)",
                 "Differentiation vs Sharony 2602.01915 holds",
                 ["No published VLM-counterfactual-for-RL prior art found",
                  "Closest neighbours: CAST (VLA labels), CoSo (tokens), HInt",
                  "L1 has citation-ready Related Work paragraph (~155 words)"]),
            ],
        },
    ]

    for p in panels:
        ax = p["ax"]
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        # Title bar
        ax.add_patch(plt.Rectangle((0, 0.92), 1.0, 0.08,
                                   facecolor=p["color"], edgecolor="white"))
        ax.text(0.02, 0.96, p["title"], ha="left", va="center",
                color="white", fontsize=12, fontweight="bold")

        # Items
        n = len(p["items"])
        block_h = 0.90 / n
        for j, (label, head, bullets) in enumerate(p["items"]):
            y_top = 0.91 - j * block_h
            y_bot = y_top - block_h + 0.01
            ax.add_patch(plt.Rectangle((0, y_bot), 1.0, block_h - 0.01,
                                       facecolor="#f8fafb", edgecolor="#d6dde2", linewidth=0.6))
            ax.text(0.02, y_top - 0.025, label,
                    ha="left", va="top", fontsize=9.5, fontweight="bold", color=p["color"])
            ax.text(0.02, y_top - 0.075, head,
                    ha="left", va="top", fontsize=9.0, color="#22313f")
            for k, b in enumerate(bullets):
                ax.text(0.04, y_top - 0.115 - k * 0.045,
                        "- " + b,
                        ha="left", va="top", fontsize=8.4, color="#3a4a59")

    fig.suptitle("What was built tonight (2026-05-11)", fontsize=13,
                 fontweight="bold", color="#2c3e50", y=1.01)
    fig.tight_layout()
    out = OUT / "fig3_paths_status.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


# ============================================================
# Figure 4: average + per-env compact summary (single row)
# ============================================================
def fig_averages():
    fig, ax = plt.subplots(figsize=(7.0, 3.2), dpi=170)
    # Average over envs
    avgs = []
    ses  = []
    labels = []
    colors = []
    for method, color in METHODS:
        means = [DATA[(env, method)][0] for env in ENVS]
        # SE of mean across envs (we have 3 means each from 3 seeds; treat env-average as a rough cross-env spread)
        stds  = [DATA[(env, method)][1] for env in ENVS]
        avg = float(np.mean(means))
        # combined SE: average of SE(per env)
        avg_se = float(np.mean([s / np.sqrt(N_SEEDS) for s in stds]))
        avgs.append(avg); ses.append(avg_se); labels.append(method); colors.append(color)

    bars = ax.barh(np.arange(len(METHODS)), avgs, xerr=ses,
                   color=colors, edgecolor="white", linewidth=1.0, capsize=3,
                   error_kw={"ecolor": "#444", "linewidth": 1.2})
    for i, (b, m) in enumerate(zip(bars, avgs)):
        ax.text(b.get_width() + 0.015, b.get_y() + b.get_height()/2,
                f"{m:.3f}", va="center", fontsize=9, color="#22313f")
    ax.set_yticks(np.arange(len(METHODS)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, 0.55)
    ax.set_xlabel("Avg final success rate across 3 Fetch envs")
    ax.set_title("Average across envs (3 seeds, mean ± mean(SE))", pad=8)
    fig.tight_layout()
    out = OUT / "fig4_averages.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    fig_headline()
    fig_differentiation()
    fig_paths_status()
    fig_averages()
    print("done")
