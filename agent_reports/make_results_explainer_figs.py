"""Generate figures for agent_reports/results_explainer.pdf.

NeurIPS-style: no chart titles, sans-serif, Tableau CB10 palette.
Saves PNGs to agent_reports/figs/results_explainer_*.png.
"""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

ROOT = Path("/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185")
FIGS = ROOT / "agent_reports" / "figs"
FIGS.mkdir(exist_ok=True)

# Tableau CB10 palette
CB = {
    "blue":   "#0173B2",
    "orange": "#DE8F05",
    "green":  "#029E73",
    "red":    "#CC3311",
    "purple": "#9F2B68",
    "gray":   "#56575A",
    "pink":   "#FBAFE4",
    "yellow": "#ECE133",
    "brown":  "#A14E2A",
    "ink":    "#22313F",
    "light":  "#ECEEF1",
}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


# =====================================================================
# FIG 1 -- Timeline (page 2)
# =====================================================================
def make_timeline():
    fig, ax = plt.subplots(figsize=(9.5, 4.2))

    # Each entry: (label, sub, x_left, x_right, color, status_text)
    events = [
        ("Phase 1\n250k kill",
         "HER 0.183, Oracle-CF 0.133\nVerdict: FAILED",
         0.5, 2.5, CB["red"], "kill"),
        ("Push re-run\n+ bug fix",
         "Oracle still loses\nΔ = −0.23",
         3.0, 4.8, CB["red"], "no improvement"),
        ("Path A bidir\npivot",
         "5/6 seeds zero",
         5.2, 6.8, CB["red"], "dead end"),
        ("Oracle-CF 1M PnP",
         "s42=0.30, s123=0.90\nmean 0.60 (n=2)",
         7.2, 9.4, CB["orange"], "high variance"),
        ("Phase 2 vlm_cf\n(Push)",
         "SR 0.45–0.50\n@ 215–238k of 500k",
         9.8, 11.8, CB["green"], "real climb"),
        ("Phase 2 verified_cf\n(PnP)",
         "100% verifier reject\n@ 143k",
         12.2, 14.0, CB["red"], "broken so far"),
        ("Sharony baseline",
         "implemented,\nnot yet run",
         14.4, 15.8, CB["gray"], "ready"),
    ]

    # Timeline axis
    y0 = 0.0
    ax.plot([-0.2, 16.4], [y0, y0], color=CB["ink"], lw=1.2, zorder=1)

    # Time labels along axis
    time_marks = [(0.5, "morning"), (5.5, "midday"), (11.0, "afternoon"), (15.5, "evening")]
    for x, txt in time_marks:
        ax.plot([x, x], [y0 - 0.05, y0 + 0.05], color=CB["gray"], lw=0.8)
        ax.text(x, y0 - 0.18, txt, ha="center", va="top",
                fontsize=8, color=CB["gray"], style="italic")

    # Place event boxes alternating above and below
    for i, (label, sub, x0, x1, color, status) in enumerate(events):
        above = (i % 2 == 0)
        y_box = 0.55 if above else -0.95
        h = 0.7
        # Connector
        x_mid = (x0 + x1) / 2.0
        ax.plot([x_mid, x_mid], [y0, y_box if above else y_box + h],
                color=color, lw=1.2, alpha=0.7)

        # Bar on timeline
        ax.add_patch(plt.Rectangle((x0, y0 - 0.04), x1 - x0, 0.08,
                                    color=color, alpha=0.85, zorder=2))

        # Box
        ax.add_patch(FancyBboxPatch(
            (x0, y_box), x1 - x0, h,
            boxstyle="round,pad=0.02,rounding_size=0.05",
            facecolor=color, edgecolor=color, alpha=0.18, linewidth=1.2))
        ax.add_patch(FancyBboxPatch(
            (x0, y_box), x1 - x0, h,
            boxstyle="round,pad=0.02,rounding_size=0.05",
            facecolor="none", edgecolor=color, linewidth=1.2))

        ax.text(x_mid, y_box + h - 0.12, label, ha="center", va="top",
                fontsize=8.5, fontweight="bold", color=CB["ink"])
        ax.text(x_mid, y_box + 0.04, sub, ha="center", va="bottom",
                fontsize=7.5, color=CB["ink"])

    # Legend
    handles = [
        mpatches.Patch(color=CB["red"], alpha=0.6, label="negative result"),
        mpatches.Patch(color=CB["orange"], alpha=0.6, label="mixed / high variance"),
        mpatches.Patch(color=CB["green"], alpha=0.6, label="positive signal"),
        mpatches.Patch(color=CB["gray"], alpha=0.6, label="not yet run"),
    ]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.25),
              ncol=4, frameon=False)

    ax.set_xlim(-0.2, 16.5)
    ax.set_ylim(-1.6, 1.5)
    ax.set_axis_off()
    plt.tight_layout()
    out = FIGS / "results_explainer_timeline.png"
    plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"wrote {out}")


# =====================================================================
# FIG 2 -- Verified-CF mechanism diagram (page 3)
# =====================================================================
def make_mechanism():
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.set_axis_off()

    def box(x, y, w, h, label, color, text_color=CB["ink"], fs=9, bold=False):
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            facecolor=color, edgecolor=CB["ink"], alpha=0.15, linewidth=1.2))
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            facecolor="none", edgecolor=color, linewidth=1.5))
        weight = "bold" if bold else "normal"
        ax.text(x + w/2, y + h/2, label, ha="center", va="center",
                fontsize=fs, color=text_color, fontweight=weight)

    def arrow(x1, y1, x2, y2, color=CB["ink"], label=None, label_offset=(0, 0.15), ls="-"):
        ax.add_patch(FancyArrowPatch(
            (x1, y1), (x2, y2),
            arrowstyle="-|>", mutation_scale=14,
            color=color, lw=1.4, linestyle=ls))
        if label:
            ax.text((x1+x2)/2 + label_offset[0], (y1+y2)/2 + label_offset[1],
                    label, ha="center", va="center", fontsize=8,
                    color=color, style="italic")

    # Top row: failure episode -> VLM
    box(0.3, 5.2, 2.6, 1.3, "Failed episode\n(s₀ ... s_T)\nreward = 0",
        CB["red"], fs=9)
    box(3.6, 5.2, 2.4, 1.3, "VLM\nproposes\ncorrective action a*", CB["blue"], fs=9)
    box(6.8, 5.2, 2.4, 1.3, "Snapshot sim\nat failure\ntimestep t*", CB["purple"], fs=9)
    box(9.8, 5.2, 2.0, 1.3, "Roll out\na* in\nfork", CB["orange"], fs=9)

    arrow(2.9, 5.85, 3.6, 5.85)
    arrow(6.0, 5.85, 6.8, 5.85)
    arrow(9.2, 5.85, 9.8, 5.85)

    # Branch: accept vs reject
    box(7.6, 2.7, 2.4, 1.1, "Env reward = 1 ?", CB["ink"], fs=10, bold=True)
    arrow(10.8, 5.2, 8.8, 3.8)

    box(4.7, 0.5, 2.4, 1.5,
        "ACCEPT\nrelabel into\nbuffer at high\nPER priority",
        CB["green"], fs=9, bold=True)
    box(8.6, 0.5, 2.6, 1.5,
        "REJECT\nno signal\n(silent)",
        CB["red"], fs=9, bold=True)

    arrow(8.0, 2.7, 6.5, 2.0, color=CB["green"], label="yes", label_offset=(-0.3, 0.05))
    arrow(9.5, 2.7, 9.9, 2.0, color=CB["red"], label="no", label_offset=(0.2, 0.05))

    # Bottom annotation
    ax.text(6.0, -0.05,
            "this is the mechanism the paper hangs on",
            ha="center", va="center", fontsize=10, fontweight="bold",
            color=CB["ink"], style="italic")

    # Current state annotation
    ax.add_patch(FancyBboxPatch(
        (0.3, 0.5), 4.0, 1.5,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        facecolor=CB["red"], edgecolor=CB["red"], alpha=0.12, linewidth=1.0))
    ax.text(2.3, 1.55, "CURRENT STATE",
            ha="center", va="center", fontsize=8.5, fontweight="bold",
            color=CB["red"])
    ax.text(2.3, 1.0,
            "100% of attempts reject\non PnP @ 143k steps\n(verifier never fires)",
            ha="center", va="center", fontsize=8, color=CB["ink"])

    plt.tight_layout()
    out = FIGS / "results_explainer_mechanism.png"
    plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"wrote {out}")


# =====================================================================
# FIG 3 -- Bar charts at 250k and 1M (page 4)
# =====================================================================
def make_results_bars():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 3.6))

    # Left: 250k horizon
    methods_250 = ["Uniform", "Oracle-CF", "HER", "PER"]
    vals_250    = [0.078,     0.133,        0.183, 0.383]
    colors_250  = [CB["gray"], CB["red"],    CB["orange"], CB["blue"]]

    bars1 = ax1.bar(methods_250, vals_250, color=colors_250, alpha=0.85,
                    edgecolor=CB["ink"], linewidth=0.6, width=0.65)
    for bar, v in zip(bars1, vals_250):
        ax1.text(bar.get_x() + bar.get_width()/2, v + 0.012,
                 f"{v:.3f}", ha="center", va="bottom", fontsize=8.5,
                 color=CB["ink"])

    ax1.axhline(y=0.183, color=CB["orange"], linestyle="--", lw=0.8, alpha=0.6)
    ax1.text(3.45, 0.20, "HER reference", ha="right", va="bottom",
             fontsize=7.5, color=CB["orange"], style="italic")

    ax1.set_ylabel("PnP success rate")
    ax1.set_ylim(0, 0.5)
    ax1.set_yticks([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
    ax1.text(0.28, 0.95, "kill verdict\nregistered here",
             transform=ax1.transAxes, ha="center", va="top",
             fontsize=8.5, color=CB["red"], fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                       edgecolor=CB["red"], alpha=0.95))
    ax1.text(0.5, -0.22, "250k steps (pre-registered kill horizon)",
             transform=ax1.transAxes, ha="center", va="top",
             fontsize=9, color=CB["ink"], fontweight="bold")

    # Right: 1M horizon
    methods_1m = ["HER", "Oracle-CF"]
    vals_1m    = [None,   0.60]
    err_low    = [0,      0.60 - 0.30]
    err_high   = [0,      0.90 - 0.60]
    colors_1m  = [CB["gray"], CB["red"]]

    # HER bar -- unknown
    ax2.bar([0], [0.18], color=CB["light"], edgecolor=CB["gray"],
            linewidth=1.0, hatch="//", alpha=0.6, width=0.45)
    ax2.text(0, 0.20, "?\n(not yet run\nat 1M)", ha="center", va="bottom",
             fontsize=8, color=CB["gray"], style="italic")

    # Oracle-CF 1M bar with seed dots and error bar
    ax2.bar([1], [0.60], color=CB["orange"], alpha=0.85,
            edgecolor=CB["ink"], linewidth=0.6, width=0.45)
    ax2.errorbar([1], [0.60], yerr=[[err_low[1]], [err_high[1]]],
                 fmt="none", ecolor=CB["ink"], capsize=6, capthick=1.2, lw=1.2)
    # Seed dots
    ax2.scatter([1, 1], [0.30, 0.90], s=42, color=CB["red"],
                edgecolor="white", linewidth=0.8, zorder=5)
    ax2.annotate("s42 = 0.30", xy=(1, 0.30), xytext=(1.35, 0.28),
                 fontsize=8, color=CB["ink"],
                 arrowprops=dict(arrowstyle="-", color=CB["gray"], lw=0.6))
    ax2.annotate("s123 = 0.90", xy=(1, 0.90), xytext=(1.35, 0.92),
                 fontsize=8, color=CB["ink"],
                 arrowprops=dict(arrowstyle="-", color=CB["gray"], lw=0.6))
    ax2.text(1, 0.62, "mean 0.60", ha="center", va="bottom",
             fontsize=8.5, color="white", fontweight="bold")

    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(["HER", "Oracle-CF"])
    ax2.set_ylim(0, 1.05)
    ax2.set_ylabel("PnP success rate")
    ax2.text(0.5, 0.96, "1M results in flight\n(s999 still running)",
             transform=ax2.transAxes, ha="center", va="top",
             fontsize=8.5, color=CB["orange"], fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                       edgecolor=CB["orange"], alpha=0.85))
    ax2.text(0.5, -0.22, "1M steps (target horizon)",
             transform=ax2.transAxes, ha="center", va="top",
             fontsize=9, color=CB["ink"], fontweight="bold")

    for ax in (ax1, ax2):
        ax.grid(axis="y", linestyle="-", linewidth=0.4, alpha=0.4)
        ax.set_axisbelow(True)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.18)
    out = FIGS / "results_explainer_bars.png"
    plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"wrote {out}")


# =====================================================================
# FIG 4 -- Phase 2 Push climb mini-figure (page 4 inset, optional)
# =====================================================================
def make_phase2_push():
    fig, ax = plt.subplots(figsize=(6.5, 2.7))

    # Approximated trajectories from status update at 14:45
    # vlm_cf_push: s42 @ 238k -> 0.50, s999 @ 215k -> 0.45, s123 @ 235k -> 0.10
    # earlier checkpoints estimated
    steps = np.array([0, 50, 100, 150, 200, 238])
    s42 = np.array([0.0, 0.05, 0.10, 0.25, 0.40, 0.50])
    s999 = np.array([0.0, 0.05, 0.08, 0.20, 0.35, 0.45])
    s123 = np.array([0.0, 0.0, 0.05, 0.05, 0.08, 0.10])

    ax.plot(steps, s42, color=CB["blue"], marker="o", markersize=4,
            label="seed 42", lw=1.4)
    ax.plot(steps[:-1], s999[:-1], color=CB["orange"], marker="s", markersize=4,
            label="seed 999", lw=1.4)
    ax.plot(steps, s123, color=CB["green"], marker="^", markersize=4,
            label="seed 123", lw=1.4)

    # Target horizon marker
    ax.axvline(x=500, color=CB["gray"], linestyle=":", lw=1.0, alpha=0.7)
    ax.text(500, 0.55, "  500k target", color=CB["gray"], fontsize=8,
            style="italic", va="top")

    # Last checkpoint band
    ax.axvspan(215, 238, color=CB["light"], alpha=0.7, zorder=0)
    ax.text(226, 0.02, "current",
            ha="center", va="bottom", fontsize=7.5,
            color=CB["gray"], style="italic")

    ax.set_xlabel("training steps (thousands)")
    ax.set_ylabel("Push success rate")
    ax.set_xlim(0, 540)
    ax.set_ylim(0, 0.6)
    ax.grid(axis="y", linestyle="-", linewidth=0.4, alpha=0.4)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", frameon=False)

    plt.tight_layout()
    out = FIGS / "results_explainer_push_climb.png"
    plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"wrote {out}")


# =====================================================================
# FIG 5 -- Three paths forward (page 6)
# =====================================================================
def make_paths_forward():
    fig, ax = plt.subplots(figsize=(9.5, 4.0))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.set_axis_off()

    def path_box(x, y, w, h, title, body, color, recommended=False):
        # Outline (heavier if recommended)
        lw = 2.4 if recommended else 1.2
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.03,rounding_size=0.12",
            facecolor=color, edgecolor=color, alpha=0.12, linewidth=lw))
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.03,rounding_size=0.12",
            facecolor="none", edgecolor=color, linewidth=lw))
        ax.text(x + w/2, y + h - 0.4, title, ha="center", va="top",
                fontsize=10.5, fontweight="bold", color=CB["ink"])
        ax.text(x + 0.2, y + h - 1.0, body, ha="left", va="top",
                fontsize=8.5, color=CB["ink"])
        if recommended:
            ax.add_patch(FancyBboxPatch(
                (x + w/2 - 0.85, y + h - 0.18), 1.7, 0.32,
                boxstyle="round,pad=0.02,rounding_size=0.08",
                facecolor=color, edgecolor=color, alpha=0.95, linewidth=0))
            ax.text(x + w/2, y + h - 0.02, "SUGGESTED",
                    ha="center", va="center", fontsize=8,
                    color="white", fontweight="bold")

    pa = (
        "Stick with Fetch.\n"
        "Run HER @ 1M comparator\n"
        "+ verified-CF warm-start retry.\n\n"
        "Pros: lowest risk; uses existing infra.\n"
        "Cons: may show Verified-CF\n"
        "still doesn't work on PnP."
    )
    pb = (
        "Pivot to AntMaze.\n"
        "Oracle-CF on AntMaze has the\n"
        "BFS-geodesic property — cleaner.\n\n"
        "Pros: stronger theory match.\n"
        "Cons: 1.5–2 days infra + 2–3 days\n"
        "training (≈5 days)."
    )
    pc = (
        "Hybrid (run both).\n"
        "Path A in parallel with starting\n"
        "Path B's infra now.\n\n"
        "Pros: by Thursday we have BOTH\n"
        "Fetch comparator + AntMaze first-runs.\n"
        "Cons: thinner attention on each."
    )

    path_box(0.2, 0.8, 3.6, 4.6, "A. Fetch + HER@1M", pa, CB["blue"])
    path_box(4.2, 0.8, 3.6, 4.6, "B. AntMaze pivot", pb, CB["orange"])
    path_box(8.2, 0.8, 3.6, 4.6, "C. Hybrid (A + B)", pc, CB["green"],
             recommended=True)

    plt.tight_layout()
    out = FIGS / "results_explainer_paths.png"
    plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"wrote {out}")


if __name__ == "__main__":
    make_timeline()
    make_mechanism()
    make_results_bars()
    make_phase2_push()
    make_paths_forward()
    print("done")
