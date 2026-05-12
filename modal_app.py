"""
modal_app.py — Run training on Modal A10G GPUs.

Single debug run:
    modal run modal_app.py --config configs/semantic_per.yaml

Single run with overrides:
    modal run modal_app.py --config configs/per.yaml --extra "env.name=FetchPush-v4 training.seed=1"

Full 54-job ablation (all parallel, 50 GPUs) — MUST use --detach:
    modal run --detach modal_app.py::run_ablation

Before running, create a Modal secret named "semantic-per-secrets" at modal.com/secrets
with the following keys:
    OPENAI_API_KEY
    WANDB_API_KEY
    WANDB_ENTITY
    WANDB_PROJECT
"""
from typing import List, Optional
import modal

# ── Modal primitives ──────────────────────────────────────────────────────────

APP_NAME     = "semantic-per"
VOLUME_NAME  = "semantic-per-volume"
SECRET_NAME  = "semantic-per-secrets"
RESULTS_DIR  = "/results"
GPU_TYPE     = "A10G"
TIMEOUT      = 24 * 3600  # 24 hours

app    = modal.App(APP_NAME)
volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)
secret = modal.Secret.from_name(SECRET_NAME)

# ── Container image ───────────────────────────────────────────────────────────
# MuJoCo needs OSMesa for headless rendering (no display in cloud containers).
# MUJOCO_GL=osmesa tells MuJoCo to use the software renderer instead of EGL/GLX.
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "libgl1-mesa-glx",
        "libgl1-mesa-dev",
        "libglfw3",
        "libglfw3-dev",
        "libosmesa6-dev",
        "patchelf",
        "ffmpeg",
        "git",
    )
    .pip_install_from_requirements("requirements.txt")
    .env({
        "MUJOCO_GL": "osmesa",
        "PYOPENGL_PLATFORM": "osmesa",
    })
    # Add project source into the image (Modal 1.x API)
    .add_local_dir("src", "/root/src")
    .add_local_dir("configs", "/root/configs")
    .add_local_file("train.py", "/root/train.py")
    .add_local_file("evaluate.py", "/root/evaluate.py")
)


# ── Core training function ────────────────────────────────────────────────────

@app.function(
    image=image,
    gpu=GPU_TYPE,
    secrets=[secret],
    volumes={RESULTS_DIR: volume},
    timeout=TIMEOUT,
    retries=1,
)
def train_remote(config_path: str, overrides: Optional[List[str]] = None):
    """Run one training job on a remote A10G GPU.

    Args:
        config_path: Path to YAML config relative to project root.
                     e.g. "configs/semantic_per.yaml"
        overrides:   List of "key.subkey=value" CLI-style overrides.
                     e.g. ["env.name=FetchPush-v4", "training.seed=42"]
    """
    import sys
    sys.path.insert(0, "/root")  # project root inside container

    overrides = list(overrides or [])
    # Redirect outputs to the persistent volume so data survives container restarts
    overrides += [
        f"logging.log_dir={RESULTS_DIR}/logs",
        f"logging.checkpoint_dir={RESULTS_DIR}/checkpoints",
        "logging.use_wandb=true",
    ]

    from train import load_config, train
    cfg = load_config(config_path, overrides)
    train(cfg)


# ── Full ablation launcher ────────────────────────────────────────────────────

@app.function(
    image=image,
    secrets=[secret],
    timeout=300,  # launcher itself is fast; workers run independently
)
def run_ablation():
    """Spawn all 54 training jobs in parallel (6 methods × 3 envs × 3 seeds).

    Methods: uniform, per, semantic_per (fixed), her, her_per, her_semantic_per
    With 50 GPUs available all jobs run simultaneously.
    """
    ENVS = [
        "FetchPickAndPlace-v4",
        "FetchPush-v4",
        "FetchSlide-v4",
    ]
    METHODS = [
        ("configs/semantic_per_heuristic.yaml", "semantic_per_heuristic_v2"),
    ]
    SEEDS = [42, 123, 999]

    spawned = []
    for env_name in ENVS:
        env_slug = env_name.lower().replace("-v4", "").replace("fetch", "fetch_")
        for config_path, method_name in METHODS:
            for seed in SEEDS:
                run_name = f"{method_name}_{env_slug}_seed{seed}"
                overrides = [
                    f"env.name={env_name}",
                    f"training.seed={seed}",
                    f"logging.run_name={run_name}",
                ]
                train_remote.spawn(config_path, overrides)
                spawned.append(run_name)
                print(f"Spawned: {run_name}")

    print(f"\nLaunched {len(spawned)} jobs in parallel.")
    print("Monitor progress at https://wandb.ai")
    return spawned


# ── Local entrypoint ──────────────────────────────────────────────────────────

@app.local_entrypoint()
def main(
    config: str = "configs/semantic_per.yaml",
    extra: str = "",
):
    """Launch a single remote training run for debugging.

    Examples:
        modal run modal_app.py
        modal run modal_app.py --config configs/per.yaml
        modal run modal_app.py --config configs/uniform.yaml --extra "env.name=FetchPush-v4"
    """
    overrides = extra.split() if extra else []
    train_remote.remote(config, overrides)


@app.local_entrypoint()
def spawn(
    config: str = "configs/oracle_cf.yaml",
    extra: str = "",
):
    """Spawn (fire-and-forget) a remote training run.

    Used by scripts/path_c_orchestrator.py to launch Phase 2 VLM-CF jobs
    onto Modal without blocking the orchestrator process.

    Example:
        modal run --detach modal_app.py::spawn --config configs/vlm_cf.yaml \\
            --extra "env.name=FetchPickAndPlace-v4 training.seed=42 ..."
    """
    overrides = extra.split() if extra else []
    train_remote.spawn(config, overrides)


@app.local_entrypoint()
def run_path_c_phase2():
    """Spawn all Phase 2 (VLM-CF) jobs from the Path C overnight plan."""
    import json
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "agent_reports", "overnight_path_c_plan.json")) as f:
        plan = json.load(f)
    p2 = plan["phase2_vlm"]
    common = p2.get("common_overrides", [])
    per_task = p2.get("_per_task_vlm_models", {})
    spawned = 0
    for run in p2["runs"]:
        overrides = list(common) + [
            f"env.name={run['env']}",
            f"training.seed={run['seed']}",
            f"logging.run_name={run['run_name']}",
        ]
        pt = per_task.get(run["env"])
        if pt:
            overrides.append(f"replay.vlm_provider={pt['vlm_provider']}")
            overrides.append(f"replay.vlm_model={pt['vlm_model']}")
        train_remote.spawn(run["config"], overrides)
        spawned += 1
        print(f"spawned: {run['run_name']}")
    print(f"\nLaunched {spawned} Path C Phase 2 jobs onto Modal.")
    print("Track progress at https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=path_c_overnight_2026-05-11")
