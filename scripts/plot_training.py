"""
Live single-run training dashboard from W&B.

Generates a 2x3 grid of training plots from one W&B run.
Can poll continuously while training is in progress.

Usage:
    # One-shot plot of a completed or in-progress run
    python scripts/plot_training.py --run_id <wandb_run_id>

    # Live mode — re-fetches and re-plots every 60 seconds
    python scripts/plot_training.py --run_id <wandb_run_id> --refresh 60

    # Find your run_id in the W&B dashboard URL:
    # https://wandb.ai/<entity>/<project>/runs/<run_id>
"""
import argparse
import os
import time

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ── config ────────────────────────────────────────────────────────────────────

DASHBOARD_METRICS = [
    # (wandb_key,               title,                    ylabel)
    ("loss/critic",             "Critic Loss",            "Loss"),
    ("loss/actor",              "Actor Loss",             "Loss"),
    ("train/alpha",             "Entropy Temperature",    "Alpha"),
    ("train/episode_return",    "Episode Return",         "Return"),
    ("eval/success_rate",       "Eval Success Rate",      "Success Rate"),
    ("eval/mean_return",        "Eval Mean Return",       "Return"),
]

VLM_METRIC = "vlm/failure_timestep"

plt.rcParams.update({
    "figure.dpi": 150,
    "font.size": 10,
    "axes.grid": True,
    "axes.grid.alpha": 0.3,
    "grid.linestyle": "--",
})


# ── data fetching ─────────────────────────────────────────────────────────────

def fetch_run_history(run_id: str, project: str, entity: str, keys: list):
    """Download run history from W&B API. Returns a dict of {key: (steps, values)}."""
    import wandb
    path = "/".join(filter(None, [entity, project, run_id]))
    api  = wandb.Api()
    run  = api.run(path)

    fetch_keys = keys + ["global_step"]
    history = run.history(keys=fetch_keys, pandas=True)

    result = {}
    if "global_step" not in history.columns:
        return result, run.name, run.state

    history = history.dropna(subset=["global_step"]).sort_values("global_step")
    steps = history["global_step"].values

    for key in keys:
        if key in history.columns:
            vals = history[key].values
            mask = ~np.isnan(vals)
            if mask.any():
                result[key] = (steps[mask], vals[mask])

    return result, run.name, run.state


# ── plotting ──────────────────────────────────────────────────────────────────

def smooth(values: np.ndarray, window: int) -> np.ndarray:
    if window <= 1 or len(values) < window:
        return values
    kernel = np.ones(window) / window
    return np.convolve(values, kernel, mode="valid")


def plot_dashboard(history: dict, run_name: str, run_state: str,
                   out_path: str, smooth_w: int = 5):
    """2×3 subplot dashboard of the six core metrics."""
    fig = plt.figure(figsize=(16, 8))
    gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

    max_step = 0
    for key, _, _ in DASHBOARD_METRICS:
        if key in history:
            max_step = max(max_step, history[key][0].max())

    status_str = f"  [{run_state}  |  step {max_step:,.0f}]"
    fig.suptitle(f"Training Dashboard — {run_name}{status_str}", fontsize=13)

    for idx, (key, title, ylabel) in enumerate(DASHBOARD_METRICS):
        ax = fig.add_subplot(gs[idx // 3, idx % 3])
        ax.set_title(title)
        ax.set_xlabel("Environment Steps")
        ax.set_ylabel(ylabel)

        if key not in history:
            ax.text(0.5, 0.5, "No data yet", transform=ax.transAxes,
                    ha="center", va="center", color="gray")
            continue

        steps, values = history[key]
        smoothed = smooth(values, smooth_w)
        steps_s  = steps[:len(smoothed)]

        ax.plot(steps, values, alpha=0.2, color="#888888", linewidth=0.8)
        ax.plot(steps_s, smoothed, color="#2196F3", linewidth=2)

    plt.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Dashboard saved: {out_path}  (step={max_step:,.0f}, state={run_state})")


def plot_vlm_panel(history: dict, out_path: str):
    """Two-panel VLM analysis: rolling mean timestep + histogram."""
    if VLM_METRIC not in history:
        return

    steps, values = history[VLM_METRIC]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    # Rolling mean of failure timestep over training
    window = max(1, len(values) // 20)
    rolled = smooth(values, window)
    ax1.plot(steps[:len(rolled)], rolled, color="#6ACC65", linewidth=2)
    ax1.set_xlabel("Environment Steps")
    ax1.set_ylabel("Failure Timestep")
    ax1.set_title("VLM Failure Timestep (rolling mean)")

    # Distribution histogram
    ax2.hist(values, bins=min(25, len(values)), color="#6ACC65",
             alpha=0.8, edgecolor="white")
    ax2.set_xlabel("Failure Timestep")
    ax2.set_ylabel("Count")
    ax2.set_title("Failure Timestep Distribution")

    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"VLM panel saved: {out_path}")


# ── main ──────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_id",  required=True,
                        help="W&B run ID (from the dashboard URL)")
    parser.add_argument("--project", default=os.environ.get("WANDB_PROJECT", "semantic-per"))
    parser.add_argument("--entity",  default=os.environ.get("WANDB_ENTITY", ""))
    parser.add_argument("--out_dir", default="results/live/")
    parser.add_argument("--smooth",  type=int, default=5,
                        help="Smoothing window for plots (1 = no smoothing)")
    parser.add_argument("--refresh", type=int, default=0,
                        help="Re-fetch every N seconds. 0 = run once and exit.")
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    all_keys = [k for k, _, _ in DASHBOARD_METRICS] + [VLM_METRIC]

    iteration = 0
    while True:
        iteration += 1
        print(f"\n[fetch #{iteration}] Fetching run '{args.run_id}' from W&B...")

        try:
            history, run_name, run_state = fetch_run_history(
                args.run_id, args.project, args.entity, all_keys
            )
        except Exception as e:
            print(f"Error fetching run: {e}")
            if args.refresh <= 0:
                break
            print(f"Retrying in {args.refresh}s...")
            time.sleep(args.refresh)
            continue

        dashboard_path = os.path.join(args.out_dir, "dashboard.png")
        vlm_path       = os.path.join(args.out_dir, "vlm_panel.png")

        plot_dashboard(history, run_name, run_state, dashboard_path, args.smooth)
        plot_vlm_panel(history, vlm_path)

        if run_state == "finished" or args.refresh <= 0:
            break

        print(f"Refreshing in {args.refresh}s... (Ctrl+C to stop)")
        time.sleep(args.refresh)

    print(f"\nDone. Plots in: {args.out_dir}")


if __name__ == "__main__":
    main()
