"""Sweep analysis: read output/ and emit metrics + plots."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src import analysis, config as cfg_mod, records

log = logging.getLogger("analyze")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument("--runs-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    records.configure_logging()

    cfg = cfg_mod.load(args.config)
    runs_root = args.runs_root or cfg.output_dir
    output_dir = args.output_dir or (cfg.output_dir / "analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    runs = analysis.discover_runs(runs_root)
    log.info("runs_root=%s runs_found=%d", runs_root, len(runs))
    if not runs:
        raise SystemExit("No runs found.")
    for r in runs:
        log.info("  %s/%s/seed%d", r["task"], r["variant"], r["seed"])

    curves = analysis.load_eval_curves(runs)
    curves.to_csv(output_dir / "curves.csv", index=False)
    log.info("loaded %d eval points", len(curves))

    per_run = analysis.steps_to_threshold_per_run(curves, cfg.eval.success_thresholds)
    per_run.to_csv(output_dir / "per_run.csv", index=False)
    metrics = analysis.summarize(per_run, cfg.eval.success_thresholds)
    records.write_json(output_dir / "efficiency.json", metrics)
    analysis.print_summary(metrics, cfg.eval.success_thresholds)
    analysis.plot_all(curves, per_run, cfg.eval.success_thresholds, output_dir / "plots")

    summaries = analysis.load_run_summaries(runs)
    manifest = {
        "captured_at_utc": records.utc_now_iso(),
        "n_runs": len(runs),
        "missing_summaries": [
            f"{r['task']}/{r['variant']}/seed{r['seed']}"
            for r in runs if not (r.get("summary_path") and r["summary_path"].exists())
        ],
        "compute_aggregate": analysis.aggregate_compute(summaries),
        "runs": summaries,
    }
    records.write_json(output_dir / "manifest.json", manifest)
    agg = manifest["compute_aggregate"]
    if agg:
        log.info("compute: %d runs wall=%.1fh cost=$%.2f",
                 agg["n_runs"], agg["wall_hours_total"], agg["cost_usd_total"])
    log.info("wrote analysis -> %s", output_dir)


if __name__ == "__main__":
    main()
