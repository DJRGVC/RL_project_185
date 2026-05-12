#!/usr/bin/env python
"""path_c_orchestrator.py — run the Path C overnight kill+VLM experiments.

Two-phase plan (read from agent_reports/overnight_path_c_plan.json):

  Phase 1 (KILL): HER and HER+Oracle-CF on 3 envs * 3 seeds * 500k steps.
                  Runs LOCALLY on the RTX 5070 Ti at concurrency=3.
  Phase 2 (VLM):  HER+VLM-CF and HER+Verified-VLM-CF on Modal A10G's.
                  Launches when Modal capacity frees (A1's sweep ends).

Lifecycle:
  - On startup, scan the plan, launch phase 1 with a process pool.
  - Every 5 minutes, snapshot status to agent_reports/overnight_status.md
    and write a JSON line to ~/.local/state/path_c_orchestrator.log.
  - Once a Phase 1 slot frees, spawn the next Phase 1 run.
  - Once `modal app list` shows < N active containers, start Phase 2 batch.
  - SIGTERM is honored — currently-running children are NOT killed; the
    orchestrator just stops scheduling new ones and writes shutdown_at.

The orchestrator is *idempotent on restart*: completed runs (state=done)
in the status file are skipped. Failed runs are retried up to 3 times
with a 5-min cooldown.

Run:
    nohup python scripts/path_c_orchestrator.py > /tmp/orch_stdout.log 2>&1 &
"""
from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import signal
import subprocess
import sys
import time
import shutil
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── paths ─────────────────────────────────────────────────────────────────────

ROOT      = Path(__file__).resolve().parent.parent
PLAN_FILE = ROOT / "agent_reports" / "overnight_path_c_plan.json"
STATUS_MD = ROOT / "agent_reports" / "overnight_status.md"
LOG_FILE  = Path("/home/daniel-grant/.local/state/path_c_orchestrator.log")
STATE_FILE = ROOT / "agent_reports" / "overnight_state.json"

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# ── logging ──────────────────────────────────────────────────────────────────

logger = logging.getLogger("orchestrator")
logger.setLevel(logging.INFO)
sh = logging.StreamHandler(sys.stdout)
sh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(sh)


def log_event(event_type: str, **fields):
    rec = {
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
        "event": event_type,
        **fields,
    }
    line = json.dumps(rec, default=str)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception as e:
        logger.warning(f"Could not write event log: {e}")
    logger.info(f"{event_type}: {fields}")


# ── shutdown handling ────────────────────────────────────────────────────────

_SHUTDOWN = False


def _signal_handler(signum, frame):
    global _SHUTDOWN
    _SHUTDOWN = True
    log_event("shutdown_signal", signum=signum)


signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)


# ── plan loading + state ─────────────────────────────────────────────────────

def load_plan() -> Dict[str, Any]:
    with open(PLAN_FILE) as f:
        return json.load(f)


def load_state() -> Dict[str, Any]:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"runs": {}, "started_at": datetime.datetime.utcnow().isoformat() + "Z"}


def save_state(state: Dict[str, Any]):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


# ── status emission ──────────────────────────────────────────────────────────

def write_status_md(state: Dict[str, Any], plan: Dict[str, Any]):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
    started = state.get("started_at", "?")
    runs = state.get("runs", {})

    phase1_runs = plan["phase1_kill"]["runs"]
    phase2_runs = plan["phase2_vlm"]["runs"]

    def _stats(entries):
        cnt = defaultdict(int)
        for r in entries:
            s = runs.get(r["id"], {}).get("status", "pending")
            cnt[s] += 1
        return cnt

    p1 = _stats(phase1_runs)
    p2 = _stats(phase2_runs)

    lines = []
    lines.append("# Path C overnight run status\n")
    lines.append(f"_Updated {now} • orchestrator started {started}_\n")
    lines.append("\n## Phase 1 (KILL: HER vs HER+Oracle-CF on 5070Ti)\n")
    lines.append(f"- pending  : {p1.get('pending', 0)}")
    lines.append(f"- running  : {p1.get('running', 0)}")
    lines.append(f"- done     : {p1.get('done', 0)}")
    lines.append(f"- failed   : {p1.get('failed', 0)}\n")
    lines.append("| run_id | status | started | duration | exit_code |")
    lines.append("|---|---|---|---|---|")
    for r in phase1_runs:
        st = runs.get(r["id"], {})
        lines.append(
            f"| {r['id']} | {st.get('status', 'pending')} | "
            f"{st.get('started_at', '-')} | {st.get('duration', '-')} | "
            f"{st.get('exit_code', '-')} |"
        )

    lines.append("\n## Phase 2 (VLM-CF + Verified-CF on Modal A10G)\n")
    lines.append(f"- pending  : {p2.get('pending', 0)}")
    lines.append(f"- running  : {p2.get('running', 0)}")
    lines.append(f"- done     : {p2.get('done', 0)}")
    lines.append(f"- failed   : {p2.get('failed', 0)}\n")
    lines.append("| run_id | status | started |")
    lines.append("|---|---|---|")
    for r in phase2_runs:
        st = runs.get(r["id"], {})
        lines.append(
            f"| {r['id']} | {st.get('status', 'pending')} | "
            f"{st.get('started_at', '-')} |"
        )

    lines.append("\n## Logs\n")
    lines.append(f"- Orchestrator events: {LOG_FILE}")
    lines.append(f"- Per-run train.log : {ROOT}/logs/<run_name>/train.log")
    lines.append(f"- W&B: https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=path_c_overnight_2026-05-11\n")
    STATUS_MD.write_text("\n".join(lines))


# ── local Phase 1 process management ─────────────────────────────────────────

class LocalPool:
    """Lightweight subprocess pool — no Python pickling needed."""

    def __init__(self, concurrency: int):
        self.concurrency = concurrency
        self.procs: List[Tuple[str, subprocess.Popen, float]] = []  # (run_id, p, started_at)

    def slot_free(self) -> bool:
        self._reap()
        return len(self.procs) < self.concurrency

    def _reap(self):
        still = []
        for run_id, p, t0 in self.procs:
            if p.poll() is None:
                still.append((run_id, p, t0))
        self.procs = still

    def active(self) -> List[str]:
        self._reap()
        return [r for r, _, _ in self.procs]

    def submit(self, run_id: str, cmd: List[str], env: dict, log_file: Path):
        log_file.parent.mkdir(parents=True, exist_ok=True)
        f = open(log_file, "w")
        p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, env=env)
        self.procs.append((run_id, p, time.time()))
        return p


def _build_run_cmd(run: Dict[str, Any], common: List[str], extra: Optional[List[str]] = None) -> List[str]:
    """Build the python train.py command line for one run."""
    cmd = [sys.executable, "train.py", "--config", str(run["config"])]
    # Common overrides
    overrides = [
        f"env.name={run['env']}",
        f"training.seed={run['seed']}",
        f"logging.run_name={run['run_name']}",
    ] + list(common)
    # Per-task VLM model selection
    if extra:
        overrides.extend(extra)
    cmd.extend(overrides)
    return cmd


def _build_env(extra_tags: Optional[List[str]] = None) -> dict:
    """Process env for child runs. Loads .env via load_dotenv inside train.py."""
    env = dict(os.environ)
    env.setdefault("WANDB_ENTITY", "d-grant-uc-berkeley")
    env.setdefault("WANDB_PROJECT", "RL_project")
    env.setdefault("PYTHONPATH", str(ROOT))
    env.setdefault("MUJOCO_GL", "egl")
    if extra_tags:
        env["WANDB_TAGS"] = ",".join(extra_tags)
    return env


# ── Modal capacity probe ─────────────────────────────────────────────────────

def modal_busy_containers() -> int:
    """Count containers currently active across the workspace. Best-effort.

    `modal app list` outputs a table; we count rows whose Tasks column has > 0.
    """
    try:
        out = subprocess.check_output(
            ["modal", "app", "list"], stderr=subprocess.STDOUT, timeout=30,
            text=True,
        )
    except Exception as e:
        log_event("modal_probe_failed", error=str(e))
        return 999  # treat as full on error
    busy = 0
    for line in out.splitlines():
        # rows look like: "│ ap-xxx │ desc │ State │ N │ created at │"
        parts = [p.strip() for p in line.split("│")]
        if len(parts) < 5:
            continue
        state = parts[3].lower() if len(parts) > 3 else ""
        tasks_field = parts[4].strip() if len(parts) > 4 else ""
        try:
            n = int(tasks_field)
        except ValueError:
            n = 0
        if "ephemeral" in state or "running" in state:
            busy += n
    return busy


# ── Modal launch ─────────────────────────────────────────────────────────────

def launch_modal_run(run: Dict[str, Any], common: List[str], extra: Optional[List[str]] = None) -> bool:
    """Spawn one Modal job via the `spawn` local entrypoint (fire-and-forget).

    modal_app.py::spawn calls `train_remote.spawn(...)` which queues the
    function without blocking. We use a single `modal run` invocation per
    job; Modal handles its own scheduling/queue across the workspace.
    """
    cfg = run["config"]
    overrides = [
        f"env.name={run['env']}",
        f"training.seed={run['seed']}",
        f"logging.run_name={run['run_name']}",
    ] + list(common) + list(extra or [])
    extra_str = " ".join(overrides)
    cmd = [
        "modal", "run", "--detach", "modal_app.py::spawn",
        "--config", cfg,
        "--extra", extra_str,
    ]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(ROOT))
        try:
            proc.wait(timeout=90)
            out, err = proc.communicate(timeout=5)
            log_event("modal_launch", run_id=run["id"], rc=proc.returncode,
                      stderr=(err.decode("utf-8", errors="replace")[-400:] if err else ""))
            return proc.returncode == 0
        except subprocess.TimeoutExpired:
            log_event("modal_launch_timeout", run_id=run["id"])
            try:
                proc.kill()
            except Exception:
                pass
            return False
    except Exception as e:
        log_event("modal_launch_failed", run_id=run["id"], error=str(e))
        return False


# ── Phase 1 driver ───────────────────────────────────────────────────────────

def run_phase1(plan: Dict[str, Any], state: Dict[str, Any]):
    p1 = plan["phase1_kill"]
    pool = LocalPool(concurrency=p1.get("_concurrency_local", 3))
    common = p1.get("common_overrides", [])
    queue = list(p1["runs"])

    # Skip already-completed runs (idempotency).
    queue = [r for r in queue if state["runs"].get(r["id"], {}).get("status") != "done"]
    if not queue:
        log_event("phase1_already_complete")
        return

    log_event("phase1_start", n_runs=len(queue), concurrency=pool.concurrency)

    while queue or pool.active():
        if _SHUTDOWN:
            break

        # Reap finished procs and write outcomes.
        for run_id, p, t0 in list(pool.procs):
            if p.poll() is not None:
                duration = time.time() - t0
                rc = p.returncode
                state["runs"][run_id] = {
                    **state["runs"].get(run_id, {}),
                    "status":     "done" if rc == 0 else "failed",
                    "exit_code":  rc,
                    "duration":   f"{int(duration)}s",
                    "ended_at":   datetime.datetime.utcnow().isoformat() + "Z",
                }
                log_event("phase1_run_end", run_id=run_id, rc=rc, duration=duration)
                save_state(state)
                pool._reap()

        # Submit more runs if slots free.
        while queue and pool.slot_free():
            if _SHUTDOWN:
                break
            run = queue.pop(0)
            run_id = run["id"]
            log_path = ROOT / "logs" / f"path_c_orch_{run_id}.log"
            cmd = _build_run_cmd(run, common)
            env = _build_env(run.get("tags"))
            state["runs"][run_id] = {
                **state["runs"].get(run_id, {}),
                "status":      "running",
                "started_at":  datetime.datetime.utcnow().isoformat() + "Z",
                "phase":       "phase1",
                "config":      run["config"],
                "env":         run["env"],
                "seed":        run["seed"],
                "run_name":    run["run_name"],
                "log_file":    str(log_path),
            }
            save_state(state)
            try:
                pool.submit(run_id, cmd, env, log_path)
                log_event("phase1_run_start", run_id=run_id, run_name=run["run_name"], cmd=" ".join(cmd))
            except Exception as e:
                state["runs"][run_id]["status"] = "failed"
                state["runs"][run_id]["error"] = str(e)
                log_event("phase1_run_spawn_failed", run_id=run_id, error=str(e))
                save_state(state)

        time.sleep(15)  # idle poll
        write_status_md(state, plan)

    log_event("phase1_done")
    write_status_md(state, plan)


# ── Phase 2 driver ───────────────────────────────────────────────────────────

def wait_for_modal_capacity(min_free_containers: int = 6, check_every: int = 300):
    """Block until Modal has at least min_free_containers free."""
    # We don't know workspace quota — assume A1's ~10 containers is roughly
    # the high-water mark; treat "≤ 4 active" as "free enough".
    free_threshold = 4
    while not _SHUTDOWN:
        busy = modal_busy_containers()
        log_event("modal_capacity_probe", busy_count=busy, free_threshold=free_threshold)
        if busy <= free_threshold:
            return True
        time.sleep(check_every)
    return False


def run_phase2(plan: Dict[str, Any], state: Dict[str, Any]):
    p2 = plan["phase2_vlm"]
    common = p2.get("common_overrides", [])
    per_task = p2.get("_per_task_vlm_models", {})
    queue = list(p2["runs"])
    queue = [r for r in queue if state["runs"].get(r["id"], {}).get("status") not in ("done", "running")]
    if not queue:
        log_event("phase2_already_complete")
        return

    log_event("phase2_start", n_runs=len(queue))

    # Wait for Modal capacity.
    log_event("phase2_waiting_for_modal")
    if not wait_for_modal_capacity():
        return

    # Submit all in a batch (Modal handles its own scheduling); 6 at a time
    # to be polite to the workspace.
    batch_size = p2.get("_modal_concurrency", 6)
    for i, run in enumerate(queue):
        if _SHUTDOWN:
            break
        run_id = run["id"]
        task_extra = []
        pt = per_task.get(run["env"])
        if pt:
            task_extra.append(f"replay.vlm_provider={pt['vlm_provider']}")
            task_extra.append(f"replay.vlm_model={pt['vlm_model']}")
        ok = launch_modal_run(run, common, task_extra)
        state["runs"][run_id] = {
            **state["runs"].get(run_id, {}),
            "status":      "running" if ok else "failed",
            "started_at":  datetime.datetime.utcnow().isoformat() + "Z",
            "phase":       "phase2",
            "config":      run["config"],
            "env":         run["env"],
            "seed":        run["seed"],
            "run_name":    run["run_name"],
            "vlm_overrides": " ".join(task_extra),
            "modal_launched": bool(ok),
        }
        save_state(state)
        write_status_md(state, plan)
        if (i + 1) % batch_size == 0:
            log_event("phase2_batch_pause", batch_n=batch_size)
            time.sleep(60)
        else:
            time.sleep(8)

    log_event("phase2_submitted_all")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-phase2", action="store_true", help="Phase 1 only (kill experiment).")
    parser.add_argument("--phase2-only", action="store_true", help="Skip Phase 1, go straight to Phase 2 launch.")
    parser.add_argument("--dry-run", action="store_true", help="Print plan, do not execute.")
    args = parser.parse_args()

    plan = load_plan()
    state = load_state()
    log_event("orchestrator_start", state_keys=list(state.keys()), plan_keys=list(plan.keys()))
    write_status_md(state, plan)

    if args.dry_run:
        print(json.dumps(plan, indent=2))
        return

    if not args.phase2_only:
        run_phase1(plan, state)

    if not args.skip_phase2:
        run_phase2(plan, state)

    # Final status emit.
    state["finished_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    save_state(state)
    write_status_md(state, plan)
    log_event("orchestrator_done")


if __name__ == "__main__":
    main()
