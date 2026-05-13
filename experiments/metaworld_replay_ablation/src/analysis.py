"""Sweep analysis: learning curves, steps-to-threshold, bootstrap CIs."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

log = logging.getLogger(__name__)
_SEED_RE = re.compile(r"^seed(\d+)$")


def _bootstrap_ci(values, n_boot: int = 1000, seed: int = 0) -> tuple[float, float]:
    arr = np.asarray([v for v in values if v is not None and not (isinstance(v, float) and np.isnan(v))], dtype=float)
    if arr.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    boots = rng.choice(arr, size=(n_boot, arr.size), replace=True).mean(axis=1)
    return float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def discover_runs(runs_root: Path) -> list[dict]:
    """Walk ``runs_root/<task>/<variant>/seed<N>/eval.jsonl``."""
    out: list[dict] = []
    if not runs_root.exists():
        return out
    for task_dir in sorted(p for p in runs_root.iterdir() if p.is_dir()):
        for variant_dir in sorted(p for p in task_dir.iterdir() if p.is_dir()):
            for seed_dir in sorted(p for p in variant_dir.iterdir() if p.is_dir()):
                m = _SEED_RE.match(seed_dir.name)
                if not m:
                    continue
                eval_path = seed_dir / "eval.jsonl"
                if not eval_path.exists():
                    continue
                out.append({
                    "task": task_dir.name, "variant": variant_dir.name,
                    "seed": int(m.group(1)), "run_dir": seed_dir,
                    "eval_path": eval_path,
                    "summary_path": seed_dir / "summary.json",
                })
    return out


def load_eval_curves(runs: list[dict]) -> pd.DataFrame:
    rows: list[dict] = []
    for r in runs:
        for line in r["eval_path"].read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            rows.append({
                "task": r["task"], "variant": r["variant"], "seed": r["seed"],
                "step": int(d["step"]),
                "success_rate": float(d["success_rate"]),
                "mean_return": float(d["mean_return"]),
                "mean_ep_length": float(d.get("mean_ep_length", 0.0)),
            })
    return pd.DataFrame(rows)


def steps_to_threshold_per_run(curves: pd.DataFrame, thresholds: tuple[float, ...]) -> pd.DataFrame:
    rows: list[dict] = []
    for (task, variant, seed), df in curves.groupby(["task", "variant", "seed"]):
        df = df.sort_values("step")
        row = {
            "task": task, "variant": variant, "seed": int(seed),
            "final_success_rate": float(df.iloc[-1]["success_rate"]),
        }
        for t in thresholds:
            hit = df[df["success_rate"] >= t]
            row[f"steps_to_{t:g}"] = int(hit.iloc[0]["step"]) if not hit.empty else None
        rows.append(row)
    return pd.DataFrame(rows)


def summarize(per_run: pd.DataFrame, thresholds: tuple[float, ...]) -> dict[str, Any]:
    out: dict[str, Any] = {"per_task_variant": {}}
    for (task, variant), df in per_run.groupby(["task", "variant"]):
        finals = df["final_success_rate"].dropna().tolist()
        ci_lo, ci_hi = _bootstrap_ci(finals)
        entry: dict[str, Any] = {
            "n_seeds": int(len(df)),
            "seeds": sorted(int(s) for s in df["seed"].tolist()),
            "final_success_rate_mean": float(df["final_success_rate"].mean()),
            "final_success_rate_std": float(df["final_success_rate"].std(ddof=0)) if len(df) > 1 else 0.0,
            "final_success_rate_ci": [ci_lo, ci_hi],
            "final_success_rate_per_seed": dict(zip(
                [int(s) for s in df["seed"]], [float(v) for v in df["final_success_rate"]])),
        }
        for t in thresholds:
            col = f"steps_to_{t:g}"
            hit = df[col].dropna()
            lo, hi = _bootstrap_ci(hit.tolist())
            entry[f"steps_to_{t:g}"] = {
                "n_reached": int(len(hit)),
                "mean": float(hit.mean()) if len(hit) else None,
                "median": float(hit.median()) if len(hit) else None,
                "ci_lo": lo, "ci_hi": hi,
                "per_seed": dict(zip(
                    [int(s) for s in df["seed"]],
                    [None if pd.isna(v) else int(v) for v in df[col]])),
            }
        out["per_task_variant"].setdefault(task, {})[variant] = entry
    return out


def print_summary(metrics: dict, thresholds: tuple[float, ...]) -> None:
    log.info("=== sweep summary ===")
    for task, by_variant in metrics["per_task_variant"].items():
        log.info("  [%s]", task)
        for variant, s in by_variant.items():
            ci = s.get("final_success_rate_ci", [float("nan"), float("nan")])
            parts = [f"    {variant:>15s}: final={s['final_success_rate_mean']:.2f}"
                     f"±{s['final_success_rate_std']:.2f} CI=[{ci[0]:.2f},{ci[1]:.2f}]"]
            for t in thresholds:
                d = s[f"steps_to_{t:g}"]
                steps = f"{d['mean']:,.0f}" if d["mean"] is not None else "never"
                ci_t = f"[{d.get('ci_lo', float('nan')):.0f},{d.get('ci_hi', float('nan')):.0f}]"
                parts.append(f"→{t:g}: {steps} {ci_t} ({d['n_reached']}/{s['n_seeds']})")
            log.info("  ".join(parts))


def load_run_summaries(runs: list[dict]) -> list[dict]:
    out: list[dict] = []
    for r in runs:
        sp = r.get("summary_path")
        if sp and sp.exists():
            try:
                d = json.loads(sp.read_text())
            except Exception as exc:  # noqa: BLE001
                d = {"summary_error": repr(exc)}
            out.append({"task": r["task"], "variant": r["variant"], "seed": r["seed"], **d})
    return out


def aggregate_compute(summaries: list[dict]) -> dict[str, Any]:
    if not summaries:
        return {}
    walls = [s.get("wall_s") or 0.0 for s in summaries]
    costs = [s.get("cost_estimate_usd") or 0.0 for s in summaries]
    return {
        "n_runs": len(summaries),
        "wall_hours_total": sum(walls) / 3600,
        "wall_hours_mean": (sum(walls) / 3600) / len(summaries),
        "cost_usd_total": sum(costs),
        "cost_usd_mean": sum(costs) / len(summaries),
    }


def plot_all(curves: pd.DataFrame, per_run: pd.DataFrame,
             thresholds: tuple[float, ...], plots_dir: Path, dpi: int = 130) -> None:
    plots_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(context="paper", palette="viridis")

    if not curves.empty:
        g = sns.relplot(data=curves, x="step", y="success_rate", hue="variant", col="task",
                        kind="line", errorbar=("ci", 95), height=3.4, aspect=1.3, col_wrap=3)
        g.set_axis_labels("environment steps", "eval success rate")
        g.fig.suptitle("Sample efficiency by variant", y=1.02)
        g.savefig(plots_dir / "success_curves.png", dpi=dpi, bbox_inches="tight")
        plt.close(g.fig)

    if not per_run.empty:
        g = sns.catplot(data=per_run, x="variant", y="final_success_rate", col="task",
                        kind="bar", errorbar=("ci", 95), height=3.4, aspect=1.0, col_wrap=3)
        g.set_axis_labels("variant", "final eval success rate")
        g.fig.suptitle("Final success rate at training budget", y=1.02)
        for ax in g.axes.flat:
            for label in ax.get_xticklabels():
                label.set_rotation(20)
        g.savefig(plots_dir / "final_success.png", dpi=dpi, bbox_inches="tight")
        plt.close(g.fig)

    primary = thresholds[0]
    col = f"steps_to_{primary:g}"
    df = per_run.dropna(subset=[col]).copy() if col in per_run.columns else pd.DataFrame()
    if not df.empty:
        g = sns.catplot(data=df, x="variant", y=col, col="task",
                        kind="bar", errorbar=("ci", 95), height=3.4, aspect=1.0, col_wrap=3)
        g.set_axis_labels("variant", f"env steps to reach success rate {primary:g}")
        g.fig.suptitle("Sample efficiency (lower is better)", y=1.02)
        for ax in g.axes.flat:
            for label in ax.get_xticklabels():
                label.set_rotation(20)
        g.savefig(plots_dir / f"steps_to_{primary:g}.png", dpi=dpi, bbox_inches="tight")
        plt.close(g.fig)
