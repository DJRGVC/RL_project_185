"""
Plot all comparison results across methods, environments, and seeds.

W&B backend (default):
    python scripts/plot_results.py --wandb_project semantic-per --out_dir results/plots/

TensorBoard backend (fallback):
    python scripts/plot_results.py --backend tensorboard --log_dir logs/ --out_dir results/plots/

Upload plots back to W&B as an artifact:
    python scripts/plot_results.py --upload_wandb
"""
import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ── style ─────────────────────────────────────────────────────────────────────

COLORS = {
    "uniform":      "#4878D0",
    "per":          "#EE854A",
    "semantic_per": "#6ACC65",
}
LABELS = {
    "uniform":      "Uniform Replay",
    "per":          "TD-Error PER",
    "semantic_per": "Semantic PER (Ours)",
}
METHODS = list(COLORS.keys())

plt.rcParams.update({
    "figure.dpi": 150,
    "font.size": 11,
    "axes.grid": True,
    "axes.grid.alpha": 0.3,
    "grid.linestyle": "--",
})


# ── data loading ──────────────────────────────────────────────────────────────

def smooth(values: np.ndarray, window: int = 5) -> np.ndarray:
    if window <= 1:
        return values
    kernel = np.ones(window) / window
    return np.convolve(values, kernel, mode="valid")


def interpolate_runs(runs, n_points=300):
    """Interpolate a list of (steps, values) onto a common grid."""
    all_steps = np.concatenate([s for s, _ in runs])
    grid = np.linspace(all_steps.min(), all_steps.max(), n_points)
    interpolated = [np.interp(grid, s, v) for s, v in runs]
    return grid, np.array(interpolated)


def load_wandb_data(project: str, entity: str, envs: list):
    """Load run histories from W&B API.

    Returns:
        data[metric][method][env] = [(steps, values), ...]
    """
    import wandb
    api = wandb.Api()
    runs = api.runs(f"{entity}/{project}" if entity else project)

    METRICS = [
        "eval/success_rate", "eval/mean_return",
        "loss/critic", "loss/actor", "loss/alpha",
        "train/alpha", "train/td_error", "train/episode_return",
        "vlm/failure_timestep",
    ]

    # data[metric][method][env] = list of (steps_arr, values_arr)
    data = {m: {method: {env: [] for env in envs} for method in METHODS}
            for m in METRICS}

    for run in runs:
        run_name = run.name  # e.g. "semantic_per_fetch_pickandplace_seed42"
        method = next((m for m in METHODS if run_name.startswith(m)), None)
        if method is None:
            continue
        env = next((e for e in envs if e.lower().replace("-v3", "").replace("fetch", "fetch_")
                    in run_name), None)
        if env is None:
            continue

        try:
            history = run.history(keys=METRICS + ["global_step"], pandas=True)
            history = history.dropna(subset=["global_step"])
            steps = history["global_step"].values
            for metric in METRICS:
                if metric in history.columns:
                    vals = history[metric].fillna(method="ffill").values
                    data[metric][method][env].append((steps, vals))
        except Exception:
            continue

    return data


def load_tb_data(log_dir: str, envs: list, metric: str):
    """Load one metric from TensorBoard logs. Returns data[method][env]."""
    try:
        from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
    except ImportError:
        raise ImportError("pip install tensorboard")

    result = {method: {env: [] for env in envs} for method in METHODS}
    for run_dir in sorted(os.listdir(log_dir)):
        full = os.path.join(log_dir, run_dir)
        if not os.path.isdir(full):
            continue
        method = next((m for m in METHODS if run_dir.startswith(m)), None)
        if method is None:
            continue
        env = next((e for e in envs
                    if e.lower().replace("-v3", "") in run_dir.lower()), envs[0])
        ea = EventAccumulator(full)
        ea.Reload()
        if metric not in ea.Tags().get("scalars", []):
            continue
        events = ea.Scalars(metric)
        steps  = np.array([e.step for e in events])
        values = np.array([e.value for e in events])
        result[method][env].append((steps, values))
    return result


# ── individual plot functions ─────────────────────────────────────────────────

def _plot_metric(method_data, title, ylabel, out_path, smooth_w=5, ax=None):
    """Plot one metric comparing all methods with confidence bands."""
    own_fig = ax is None
    if own_fig:
        fig, ax = plt.subplots(figsize=(8, 4.5))

    for method in METHODS:
        runs = method_data.get(method, [])
        if not runs:
            continue
        grid, mat = interpolate_runs(runs)
        mean = smooth(np.mean(mat, axis=0), smooth_w)
        std  = smooth(np.std(mat, axis=0), smooth_w)
        grid_s = grid[:len(mean)]
        color = COLORS[method]
        ax.plot(grid_s, mean, label=LABELS[method], color=color, linewidth=2)
        ax.fill_between(grid_s, mean - std, mean + std, alpha=0.2, color=color)

    ax.set_xlabel("Environment Steps")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(fontsize=9)

    if own_fig:
        plt.tight_layout()
        plt.savefig(out_path)
        plt.close(fig)
        print(f"Saved: {out_path}")


def plot_training_dashboard(method_env_data, out_dir, smooth_w=5):
    """6-panel training curve dashboard (losses + rewards)."""
    panels = [
        ("loss/critic",         "Critic Loss",            "Loss"),
        ("loss/actor",          "Actor Loss",             "Loss"),
        ("loss/alpha",          "Alpha Loss",             "Loss"),
        ("train/alpha",         "Entropy Temperature",    "Alpha"),
        ("train/td_error",      "TD Error Magnitude",     "|TD error|"),
        ("train/episode_return","Episode Return",         "Return"),
    ]

    fig = plt.figure(figsize=(18, 9))
    gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.35)

    for idx, (metric, title, ylabel) in enumerate(panels):
        ax = fig.add_subplot(gs[idx // 3, idx % 3])
        # Aggregate runs across all envs for training curves
        method_data = {}
        for method in METHODS:
            runs = []
            for env_runs in method_env_data.get(metric, {}).get(method, {}).values():
                runs.extend(env_runs)
            if runs:
                method_data[method] = runs
        _plot_metric(method_data, title, ylabel, None, smooth_w=smooth_w, ax=ax)

    handles, labels = fig.axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, fontsize=10,
               bbox_to_anchor=(0.5, 1.02))
    plt.suptitle("Training Curves — All Methods", fontsize=14, y=1.04)

    out_path = os.path.join(out_dir, "training_dashboard.png")
    plt.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")
    return out_path


def plot_eval_curves(method_env_data, envs, out_dir, smooth_w=5):
    """Eval success rate and mean return, one column per env."""
    metrics = [
        ("eval/success_rate", "Success Rate", "Success Rate"),
        ("eval/mean_return",  "Mean Return",  "Return"),
    ]
    saved = []
    for metric, title_base, ylabel in metrics:
        fig, axes = plt.subplots(1, len(envs), figsize=(6 * len(envs), 4.5),
                                 sharey=True)
        if len(envs) == 1:
            axes = [axes]
        for ax, env in zip(axes, envs):
            method_data = {m: method_env_data.get(metric, {}).get(m, {}).get(env, [])
                           for m in METHODS}
            _plot_metric(method_data, f"{title_base}\n{env}", ylabel,
                         None, smooth_w=smooth_w, ax=ax)
        plt.suptitle(f"{title_base} — Semantic PER vs Baselines", fontsize=13)
        slug = metric.replace("/", "_")
        out_path = os.path.join(out_dir, f"{slug}.png")
        plt.tight_layout()
        plt.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {out_path}")
        saved.append(out_path)
    return saved


def plot_sample_efficiency(method_env_data, envs, out_dir,
                           target_success=0.5, smooth_w=10):
    """Bar chart: steps to reach target_success per method per env."""
    metric = "eval/success_rate"
    bar_w = 0.25
    x = np.arange(len(envs))

    fig, ax = plt.subplots(figsize=(4 + 2.5 * len(envs), 4.5))
    for i, method in enumerate(METHODS):
        steps_to_threshold = []
        for env in envs:
            runs = method_env_data.get(metric, {}).get(method, {}).get(env, [])
            if not runs:
                steps_to_threshold.append(np.nan)
                continue
            grid, mat = interpolate_runs(runs)
            mean = smooth(np.mean(mat, axis=0), smooth_w)
            grid_s = grid[:len(mean)]
            crossed = np.where(mean >= target_success)[0]
            steps_to_threshold.append(grid_s[crossed[0]] if len(crossed) else np.nan)

        bars = ax.bar(x + i * bar_w, steps_to_threshold, bar_w,
                      label=LABELS[method], color=COLORS[method], alpha=0.85)
        for bar, val in zip(bars, steps_to_threshold):
            if not np.isnan(val):
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() * 1.02,
                        f"{val/1e3:.0f}k", ha="center", va="bottom", fontsize=8)

    env_labels = [e.replace("Fetch", "").replace("-v3", "") for e in envs]
    ax.set_xticks(x + bar_w)
    ax.set_xticklabels(env_labels)
    ax.set_ylabel(f"Steps to {target_success:.0%} Success")
    ax.set_title("Sample Efficiency — Steps to Threshold")
    ax.legend()
    plt.tight_layout()
    out_path = os.path.join(out_dir, "sample_efficiency.png")
    plt.savefig(out_path)
    plt.close(fig)
    print(f"Saved: {out_path}")
    return out_path


def plot_vlm_analysis(method_env_data, envs, out_dir):
    """VLM failure timestep distribution and cumulative call count."""
    metric = "vlm/failure_timestep"
    runs = []
    for env in envs:
        runs.extend(method_env_data.get(metric, {})
                    .get("semantic_per", {}).get(env, []))
    if not runs:
        print("No VLM data found — skipping vlm_analysis.png")
        return None

    all_timesteps = np.concatenate([v for _, v in runs])
    all_steps     = np.concatenate([s for s, _ in runs])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    # Histogram of failure timestep positions
    ax1.hist(all_timesteps, bins=25, color=COLORS["semantic_per"], alpha=0.8,
             edgecolor="white")
    ax1.set_xlabel("Failure Timestep (buffer index)")
    ax1.set_ylabel("Count")
    ax1.set_title("VLM Failure Timestep Distribution")

    # Cumulative VLM calls over training
    sort_idx = np.argsort(all_steps)
    sorted_steps = all_steps[sort_idx]
    ax2.plot(sorted_steps, np.arange(1, len(sorted_steps) + 1),
             color=COLORS["semantic_per"], linewidth=2)
    ax2.set_xlabel("Environment Steps")
    ax2.set_ylabel("Cumulative VLM Calls")
    ax2.set_title("Cumulative VLM Calls Over Training")

    plt.tight_layout()
    out_path = os.path.join(out_dir, "vlm_analysis.png")
    plt.savefig(out_path)
    plt.close(fig)
    print(f"Saved: {out_path}")
    return out_path


def upload_plots_to_wandb(out_dir: str, project: str, entity: str):
    """Upload all PNGs in out_dir as a W&B artifact."""
    import wandb
    run = wandb.init(project=project, entity=entity or None,
                     job_type="plotting", name="plot_results")
    artifact = wandb.Artifact("comparison_plots", type="plots")
    for fname in os.listdir(out_dir):
        if fname.endswith(".png"):
            artifact.add_file(os.path.join(out_dir, fname))
            run.log({f"plots/{fname[:-4]}": wandb.Image(os.path.join(out_dir, fname))})
    run.log_artifact(artifact)
    run.finish()
    print(f"Uploaded all plots to W&B project '{project}'")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend",       default="wandb",
                        choices=["wandb", "tensorboard"])
    parser.add_argument("--wandb_project", default=os.environ.get("WANDB_PROJECT", "semantic-per"))
    parser.add_argument("--wandb_entity",  default=os.environ.get("WANDB_ENTITY", ""))
    parser.add_argument("--log_dir",       default="logs/")
    parser.add_argument("--out_dir",       default="results/plots/")
    parser.add_argument("--smooth",        type=int, default=10)
    parser.add_argument("--target_success",type=float, default=0.5)
    parser.add_argument("--upload_wandb",  action="store_true")
    parser.add_argument("--envs", nargs="+",
                        default=["FetchPickAndPlace-v3", "FetchPush-v3", "FetchSlide-v3"])
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    # ── load data ──
    if args.backend == "wandb":
        print(f"Loading data from W&B project '{args.wandb_project}'...")
        method_env_data = load_wandb_data(args.wandb_project, args.wandb_entity, args.envs)
    else:
        print(f"Loading data from TensorBoard logs in '{args.log_dir}'...")
        tb_data = load_tb_data(args.log_dir, args.envs, "eval/success_rate")
        # Wrap in the same nested structure for compatibility
        method_env_data = {"eval/success_rate": tb_data}

    # ── generate plots ──
    plot_training_dashboard(method_env_data, args.out_dir, smooth_w=args.smooth)
    plot_eval_curves(method_env_data, args.envs, args.out_dir, smooth_w=args.smooth)
    plot_sample_efficiency(method_env_data, args.envs, args.out_dir,
                           target_success=args.target_success, smooth_w=args.smooth)
    plot_vlm_analysis(method_env_data, args.envs, args.out_dir)

    # ── individual metric plots ──
    single_metrics = [
        ("eval/success_rate",      "Eval Success Rate",   "Success Rate"),
        ("eval/mean_return",       "Eval Mean Return",    "Return"),
        ("loss/critic",            "Critic Loss",         "Loss"),
        ("loss/actor",             "Actor Loss",          "Loss"),
        ("train/alpha",            "Entropy Temperature", "Alpha"),
        ("train/td_error",         "TD Error",            "|TD error|"),
    ]
    for metric, title, ylabel in single_metrics:
        method_data = {}
        for method in METHODS:
            runs = []
            for env_runs in method_env_data.get(metric, {}).get(method, {}).values():
                runs.extend(env_runs)
            if runs:
                method_data[method] = runs
        slug = metric.replace("/", "_")
        _plot_metric(method_data, title, ylabel,
                     os.path.join(args.out_dir, f"{slug}.png"),
                     smooth_w=args.smooth)

    print(f"\nAll plots saved to: {args.out_dir}")

    if args.upload_wandb:
        upload_plots_to_wandb(args.out_dir, args.wandb_project, args.wandb_entity)


if __name__ == "__main__":
    main()
