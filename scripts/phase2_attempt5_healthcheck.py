#!/usr/bin/env python
"""Health check for Phase 2 attempt 5 (split-provider VLM-CF runs).

Queries W&B for the 18 path_c_vlm runs launched on 2026-05-12 ~11:25 PDT
(18:25Z) and reports per-run:
    - state
    - global_step / total_steps (% progress)
    - cf_relabel_count / cf_vlm_returned_none (relabel health)
    - vlm_provider / vlm_model (routing sanity)
    - episode_success_rate (latest)

Usage:
    python scripts/phase2_attempt5_healthcheck.py

Exits 0 if all 18 runs are running or finished; 1 otherwise.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

import wandb


# Launch window: Phase 2 attempt 5 entrypoint started at ~2026-05-12 18:25Z.
LAUNCH_LOWER_BOUND_ISO = "2026-05-12T18:20:00Z"


def main() -> int:
    api = wandb.Api()
    runs = list(
        api.runs(
            "d-grant-uc-berkeley/RL_project",
            filters={"created_at": {"$gte": LAUNCH_LOWER_BOUND_ISO}},
            per_page=50,
        )
    )

    targets = [
        r
        for r in runs
        if r.name
        and (r.name.startswith("path_c_vlm_cf_") or r.name.startswith("path_c_vlm_vcf_"))
    ]
    targets.sort(key=lambda r: r.name or "")

    print(f"=== Phase 2 attempt 5 health check ({datetime.now(timezone.utc).isoformat()}) ===")
    print(f"Found {len(targets)} matching runs (expected 18).\n")

    bad = []
    rows = []
    for r in targets:
        cfg = r.config or {}
        replay = cfg.get("replay", {}) if isinstance(cfg.get("replay"), dict) else {}
        prov = replay.get("vlm_provider", "?")
        model = replay.get("vlm_model", "?")
        ci = replay.get("cf_call_interval", "?")

        summary = r.summary._json_dict if hasattr(r.summary, "_json_dict") else dict(r.summary)
        gs = summary.get("global_step", summary.get("_step", 0))
        cf_n = summary.get("cf_relabel_count", "-")
        cf_none = summary.get("cf_vlm_returned_none", "-")
        succ = summary.get("episode_success_rate", summary.get("eval/success_rate", "-"))

        total_steps = (
            cfg.get("training", {}).get("total_steps", 500000)
            if isinstance(cfg.get("training"), dict)
            else 500000
        )
        try:
            pct = f"{100.0 * float(gs) / float(total_steps):5.1f}%"
        except Exception:
            pct = "  ?  "

        rows.append(
            (r.name, r.state, prov, model, ci, gs, pct, cf_n, cf_none, succ)
        )

        if r.state not in {"running", "finished"}:
            bad.append((r.name, r.state))

    fmt = "{:48s} {:9s} {:10s} {:24s} ci={:>3} step={:>7} {:>6} cf_n={:>5} none={:>4} succ={}"
    for row in rows:
        print(
            fmt.format(
                str(row[0])[:48],
                str(row[1])[:9],
                str(row[2])[:10],
                str(row[3])[:24],
                str(row[4]),
                str(row[5]),
                str(row[6]),
                str(row[7]),
                str(row[8]),
                row[9],
            )
        )

    print()
    if bad:
        print(f"FAIL: {len(bad)} runs are in unexpected state:")
        for name, state in bad:
            print(f"  - {name}: {state}")
        return 1
    if len(targets) < 18:
        print(f"WARN: only {len(targets)}/18 runs registered yet (Modal cold-start lag is normal up to ~5 min).")
        return 1
    print("OK: all 18 runs running or finished.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
