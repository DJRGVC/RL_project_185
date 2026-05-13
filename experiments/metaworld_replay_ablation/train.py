"""Train SAC on one (task, variant, seed) triple."""

from __future__ import annotations

import argparse
from pathlib import Path

from src import config as cfg_mod, records, trainer


def main() -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument("--task", required=True)
    parser.add_argument("--variant", required=True, choices=list(cfg_mod.VARIANTS))
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--total-steps", type=int, default=None,
                        help="Override total_steps (smoke tests).")
    args = parser.parse_args()
    records.configure_logging()

    base = cfg_mod.load(args.config)
    if args.total_steps is not None:
        base = cfg_mod.with_overrides(base, total_steps=args.total_steps)
    run = cfg_mod.RunCfg(
        task=args.task, variant=args.variant, seed=args.seed,
        output_dir=args.output_dir or base.output_dir,
        base=base,
    )
    return trainer.train(run)


if __name__ == "__main__":
    main()
