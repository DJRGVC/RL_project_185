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
def train_remote(config_path: str, overrides: Optional[List[str]] = None,
                 wandb_tags: Optional[str] = None):
    """Run one training job on a remote A10G GPU.

    Args:
        config_path: Path to YAML config relative to project root.
                     e.g. "configs/semantic_per.yaml"
        overrides:   List of "key.subkey=value" CLI-style overrides.
                     e.g. ["env.name=FetchPush-v4", "training.seed=42"]
        wandb_tags:  Optional comma-separated W&B tag list, exported as
                     WANDB_TAGS before wandb.init() (used by
                     run_path_c_vlm_cf_psweep). Backward-compatible: existing
                     callers that don't pass this leave tag derivation to
                     logger.py (method-prefix only).
    """
    import os
    import sys
    sys.path.insert(0, "/root")  # project root inside container

    # B2 fix (CODE-REVIEWER): the Modal secret bakes WANDB_ENTITY=djrgvc, but
    # the W&B API key belongs to the `d-grant` user (a member of the
    # `d-grant-uc-berkeley` team), so writes to `djrgvc/RL_project` are denied.
    # Override before any wandb import so logger.py picks up the right entity.
    # This mirrors the a1-her-baselines fix.
    os.environ["WANDB_PROJECT"] = "RL_project"
    os.environ["WANDB_ENTITY"] = "d-grant-uc-berkeley"

    if wandb_tags:
        os.environ["WANDB_TAGS"] = wandb_tags

    # Force OSMesa rendering on Modal containers. The Modal secret is built
    # from local .env which has MUJOCO_GL=egl (for the local 5070 Ti) — but
    # Modal containers have no display and no EGL libs, so we override back
    # to osmesa (matching the image env). Must come before any env.reset()
    # in train.py triggers MuJoCo's renderer initialization.
    os.environ["MUJOCO_GL"] = "osmesa"
    os.environ["PYOPENGL_PLATFORM"] = "osmesa"

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


@app.local_entrypoint()
def run_path_c_vlm_cf_psweep():
    """Spawn the 18-run VLM-CF p_counterfactual sweep on FetchPickAndPlace-v4.

    Sweep grid: p ∈ {0.00, 0.10, 0.25, 0.50, 0.75, 1.00} × 3 seeds × 500k
    steps × FetchPickAndPlace-v4. Each run uses the corresponding
    configs/vlm_cf_psweep_p{NN}.yaml (vlm_provider=anthropic, Sonnet-4.5,
    achieved_goal variant, cf_call_interval=16, reject_teleport_radius=0.05).

    Purpose: answer "does p=1.0 (pure VLM-imagined relabels) beat the
    p=0.25 production default?" The current Path C default is HER+VLM-CF
    at p=0.25, copied from the oracle-CF default. If VLM CFs are high
    enough quality, p closer to 1.0 should dominate; if HER's hindsight
    guarantee is load-bearing, the peak should sit at p=0.25–0.50.

    Tags every run with `path_c_vlm_cf_psweep_2026-05-12` so morning
    analysis can pull them with one W&B filter URL.
    """
    P_VALUES = ["00", "10", "25", "50", "75", "100"]
    SEEDS = [42, 123, 999]
    ENV_NAME = "FetchPickAndPlace-v4"
    TAG_BASE = "path_c_vlm_cf_psweep_2026-05-12"

    common_overrides = [
        f"env.name={ENV_NAME}",
        "training.total_steps=500000",
        "training.eval_interval=10000",
        "training.save_interval=100000",
        "training.log_interval=1000",
        "logging.use_wandb=true",
    ]

    spawned = 0
    for p in P_VALUES:
        config = f"configs/vlm_cf_psweep_p{p}.yaml"
        for seed in SEEDS:
            run_name = f"path_c_vlm_cf_psweep_p{p}_pp_s{seed}_seed{seed}"
            overrides = list(common_overrides) + [
                f"training.seed={seed}",
                f"logging.run_name={run_name}",
            ]
            tags = ",".join([
                TAG_BASE,
                "vlm_cf_psweep",
                f"p{p}",
                "pathc_lead",
                ENV_NAME,
            ])
            train_remote.spawn(config, overrides, wandb_tags=tags)
            spawned += 1
            print(f"spawned: {run_name}")
    print(f"\nLaunched {spawned} Path C VLM-CF p-sweep jobs onto Modal.")
    print("Track progress at "
          "https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=path_c_vlm_cf_psweep_2026-05-12")


# ── Wave B launchers (queued after p_counterfactual sweep) ────────────────────
# These three entrypoints are fired sequentially by
# scripts/launch_waveB_when_psweep_done.sh AFTER the p-sweep finishes:
#   B1: HER+PER canonical baseline (Andrychowicz + Schaul) — 9 runs
#   B2: Sharony VLM-RB head-to-head                          — 9 runs
#   B3: 2x2 numeric/blind prompt ablation on PnP             — 12 runs
# Total: 30 runs, ~18 hr wall on the Modal 10-cap, ~$310 spend.

# Env slug convention shared with overnight_path_c_plan.json:
#   FetchPickAndPlace-v4 -> "pp"
#   FetchPush-v4         -> "push"
#   FetchSlide-v4        -> "slide"
_ENV_SLUGS = {
    "FetchPickAndPlace-v4": "pp",
    "FetchPush-v4":         "push",
    "FetchSlide-v4":        "slide",
}


def _waveB_common_overrides(env_name: str):
    """Shared overrides matching the p-sweep budget (500k steps, eval cadence)."""
    return [
        f"env.name={env_name}",
        "training.total_steps=500000",
        "training.eval_interval=10000",
        "training.save_interval=100000",
        "training.log_interval=1000",
        "logging.use_wandb=true",
    ]


@app.local_entrypoint()
def run_path_c_waveB_her_per():
    """Wave B1 — HER+PER canonical baseline (Andrychowicz + Schaul).

    9 runs = 3 envs × 3 seeds × 500k steps. Closes the "missing canonical
    non-VLM comparator" gap — HER+PER is the strongest combination from
    pre-VLM-era goal-conditioned RL literature, so any VLM-CF claim must
    beat it.

    All runs tagged `path_c_her_per_2026-05-13` for one-shot W&B filter.
    """
    ENVS  = ["FetchPickAndPlace-v4", "FetchPush-v4", "FetchSlide-v4"]
    SEEDS = [42, 123, 999]
    TAG_BASE = "path_c_her_per_2026-05-13"
    CONFIG = "configs/her_per.yaml"

    spawned = 0
    for env_name in ENVS:
        env_slug = _ENV_SLUGS[env_name]
        for seed in SEEDS:
            run_name = f"path_c_her_per_{env_slug}_s{seed}_seed{seed}"
            overrides = _waveB_common_overrides(env_name) + [
                f"training.seed={seed}",
                f"logging.run_name={run_name}",
            ]
            tags = ",".join([
                TAG_BASE,
                "her_per",
                "waveB1",
                "pathc_lead",
                env_name,
            ])
            train_remote.spawn(CONFIG, overrides, wandb_tags=tags)
            spawned += 1
            print(f"spawned: {run_name}")
    print(f"\nLaunched {spawned} Wave B1 (HER+PER) jobs onto Modal.")
    print("Track progress at "
          "https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=path_c_her_per_2026-05-13")


@app.local_entrypoint()
def run_path_c_waveB_sharony():
    """Wave B2 — Sharony VLM-RB head-to-head.

    9 runs = 3 envs × 3 seeds × 500k steps using configs/vlm_rb.yaml
    (Sharony et al. 2026 baseline, commit ebce938). Closes R1 W7
    "differentiation from Sharony only methodological" with numbers.

    All runs tagged `path_c_sharony_vlmrb_2026-05-13`.
    """
    ENVS  = ["FetchPickAndPlace-v4", "FetchPush-v4", "FetchSlide-v4"]
    SEEDS = [42, 123, 999]
    TAG_BASE = "path_c_sharony_vlmrb_2026-05-13"
    CONFIG = "configs/vlm_rb.yaml"

    spawned = 0
    for env_name in ENVS:
        env_slug = _ENV_SLUGS[env_name]
        for seed in SEEDS:
            run_name = f"path_c_sharony_vlmrb_{env_slug}_s{seed}_seed{seed}"
            overrides = _waveB_common_overrides(env_name) + [
                f"training.seed={seed}",
                f"logging.run_name={run_name}",
            ]
            tags = ",".join([
                TAG_BASE,
                "sharony_vlmrb",
                "waveB2",
                "pathc_lead",
                env_name,
            ])
            train_remote.spawn(CONFIG, overrides, wandb_tags=tags)
            spawned += 1
            print(f"spawned: {run_name}")
    print(f"\nLaunched {spawned} Wave B2 (Sharony VLM-RB) jobs onto Modal.")
    print("Track progress at "
          "https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=path_c_sharony_vlmrb_2026-05-13")


@app.local_entrypoint()
def run_path_c_waveB_2x2():
    """Wave B3 — 2x2 numeric × blind prompt ablation on PnP.

    12 runs = 4 variants × 3 seeds × 500k steps on FetchPickAndPlace-v4
    (the env where VLM-CF matters most). Variants:
      - vlm_cf.yaml                 knows desired_goal × visual only
      - vlm_cf_blind.yaml           blind             × visual only
      - vlm_cf_numeric.yaml         knows desired_goal × visual + numeric
      - vlm_cf_blind_numeric.yaml   blind             × visual + numeric

    Answers: "does giving the VLM a numerical trajectory and/or hiding
    the desired_goal coords improve counterfactual relabel quality?"

    All runs tagged `path_c_2x2_2026-05-13`.
    """
    VARIANTS = [
        ("configs/vlm_cf.yaml",                "knowsgoal_visual"),
        ("configs/vlm_cf_blind.yaml",          "blind_visual"),
        ("configs/vlm_cf_numeric.yaml",        "knowsgoal_numeric"),
        ("configs/vlm_cf_blind_numeric.yaml",  "blind_numeric"),
    ]
    SEEDS = [42, 123, 999]
    ENV_NAME = "FetchPickAndPlace-v4"
    env_slug = _ENV_SLUGS[ENV_NAME]
    TAG_BASE = "path_c_2x2_2026-05-13"

    spawned = 0
    for config_path, variant_slug in VARIANTS:
        for seed in SEEDS:
            run_name = f"path_c_2x2_{variant_slug}_{env_slug}_s{seed}_seed{seed}"
            overrides = _waveB_common_overrides(ENV_NAME) + [
                f"training.seed={seed}",
                f"logging.run_name={run_name}",
            ]
            tags = ",".join([
                TAG_BASE,
                "vlm_cf_2x2",
                f"variant_{variant_slug}",
                "waveB3",
                "pathc_lead",
                ENV_NAME,
            ])
            train_remote.spawn(config_path, overrides, wandb_tags=tags)
            spawned += 1
            print(f"spawned: {run_name}")
    print(f"\nLaunched {spawned} Wave B3 (2x2 numeric ablation) jobs onto Modal.")
    print("Track progress at "
          "https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=path_c_2x2_2026-05-13")
