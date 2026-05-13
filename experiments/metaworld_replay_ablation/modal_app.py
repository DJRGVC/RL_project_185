"""Modal app for the sparse-reward SAC sweep.

Three entrypoints:

* ``smoke`` — one short run per variant on one task. Validates the path.
* ``sweep`` — full ``tasks × variants × seeds`` fan-out across H100 concurrency.
* ``run`` — single ``(task, variant, seed)`` run, parameters from CLI flags.

Run locally::

    uv run modal run modal_app.py::smoke
    uv run modal run modal_app.py::sweep
    uv run modal run modal_app.py::run --task drawer-open-v3 --variant per --seed 0
"""

from __future__ import annotations

from pathlib import Path

import modal

APP_NAME = "cs285"
VOLUME_NAME = "cs285-data"
REMOTE_OUT = "/data/runs"

LOCAL_DIR = Path(__file__).resolve().parent

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "git", "libgl1", "libegl1", "libosmesa6", "libglfw3",
        "libxxf86vm1", "libxfixes3", "libxi6", "libxrender1",
        "libxkbcommon0", "libsm6", "ffmpeg",
    )
    .uv_sync(uv_project_dir=str(LOCAL_DIR))
    .env({"MUJOCO_GL": "egl"})
    .add_local_dir(str(LOCAL_DIR / "src"), remote_path="/app/src")
    .add_local_file(str(LOCAL_DIR / "config.yaml"), remote_path="/app/config.yaml")
    .add_local_file(str(LOCAL_DIR / "train.py"), remote_path="/app/train.py")
)

vol = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)
app = modal.App(APP_NAME, image=image)


@app.function(
    gpu="L4",
    volumes={"/data": vol},
    timeout=60 * 60 * 5,
    memory=32 * 1024,
)
def train_one(
    task: str,
    variant: str,
    seed: int,
    total_steps: int | None = None,
    output_subdir: str = "",
) -> dict:
    import os
    import sys

    os.chdir("/app")
    sys.path.insert(0, "/app")
    out = REMOTE_OUT + (f"/{output_subdir}" if output_subdir else "")
    Path(out).mkdir(parents=True, exist_ok=True)

    from train import main as train_main

    argv = sys.argv[:]
    sys.argv = [
        "train",
        "--config", "/app/config.yaml",
        "--task", task,
        "--variant", variant,
        "--seed", str(seed),
        "--output-dir", out,
    ]
    if total_steps is not None:
        sys.argv += ["--total-steps", str(total_steps)]
    try:
        summary = train_main()
        return {"status": "ok", "summary": summary or {}}
    finally:
        sys.argv = argv
        vol.commit()


@app.local_entrypoint()
def run(task: str, variant: str, seed: int = 0, total_steps: int = 0) -> None:
    """One (task, variant, seed) run from the CLI."""
    train_one.remote(task, variant, seed, total_steps=total_steps or None)


@app.local_entrypoint()
def smoke(
    task: str = "drawer-open-v3",
    total_steps: int = 20000,
) -> None:
    """One short run per variant on a single task. Validates the path."""
    print(f"smoke: task={task} variants=4 total_steps={total_steps}", flush=True)
    failures: list[str] = []
    handles = []
    for variant in ("uniform", "per", "demo-replay", "demo-priority"):
        handles.append((variant, train_one.spawn(
            task, variant, 0, total_steps=total_steps, output_subdir="smoke",
        )))
    for variant, h in handles:
        try:
            r = h.get()
            s = r.get("summary", {}) if isinstance(r, dict) else {}
            print(f"  {variant:>15s}: final_success={s.get('final_success_rate')} "
                  f"wall={s.get('wall_s', 0):.0f}s cost=${s.get('cost_estimate_usd', 0):.2f}")
        except Exception as exc:  # noqa: BLE001
            print(f"  {variant:>15s}: FAILED {exc}")
            failures.append(variant)
    if failures:
        raise SystemExit(f"smoke: FAILED variants {failures}")
    print("smoke: OK — pull with `modal volume get cs285-data /runs/smoke ./output/smoke`")


@app.local_entrypoint()
def sweep(
    tasks: str = "",
    variants: str = "",
    seeds: str = "",
) -> None:
    """Full sweep. Empty args = config.yaml defaults."""
    import yaml
    cfg = yaml.safe_load(Path("config.yaml").read_text())
    task_list = [t.strip() for t in tasks.split(",") if t.strip()] or list(cfg["tasks"])
    variant_list = [v.strip() for v in variants.split(",") if v.strip()] or list(cfg["variants"])
    seed_list = (
        [int(s.strip()) for s in seeds.split(",") if s.strip()]
        if seeds else list(int(x) for x in cfg["seeds"])
    )

    combos = [
        {"task": t, "variant": v, "seed": s}
        for t in task_list for v in variant_list for s in seed_list
    ]
    print(f"dispatching {len(combos)} runs across Modal:")
    for c in combos:
        print(f"  task={c['task']} variant={c['variant']} seed={c['seed']}")
    handles = [train_one.spawn(**c) for c in combos]
    failures = 0
    for h in handles:
        try:
            r = h.get()
            s = r.get("summary", {}) if isinstance(r, dict) else {}
            print(f"finished: {s.get('task')}/{s.get('variant')}/seed{s.get('seed')} "
                  f"final_success={s.get('final_success_rate')}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAILED: {exc}")
    if failures:
        raise SystemExit(f"{failures}/{len(handles)} runs failed.")
