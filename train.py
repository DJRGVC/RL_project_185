"""
Main training loop for Semantic Failure Localization + Prioritized Experience Replay.

Usage:
    python train.py --config configs/semantic_per.yaml
    python train.py --config configs/per.yaml
    python train.py --config configs/uniform.yaml

    # Override individual settings:
    python train.py --config configs/semantic_per.yaml env.name=FetchPush-v3 training.seed=1
"""
import os
import copy
import argparse
import logging
import random
import time
from typing import Optional

import numpy as np
import torch
import yaml

# Load .env file if present (local dev). Modal secrets overlay these at runtime.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── project imports ───────────────────────────────────────────────────────
from src.agents import SAC
from src.buffers import make_buffer
from src.buffers.semantic_buffer import SemanticPERBuffer
from src.buffers.her_buffer import HERBuffer
from src.envs.wrappers import make_env, get_task_description
from src.vlm import VLMFailureLocalizer, GoalDistanceLocalizer
from src.utils.keyframes import select_keyframes
from src.utils.logger import TrainingLogger

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────── config util ──

def deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_config(path: str, overrides: list) -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f)

    # Handle "defaults" inheritance
    if "defaults" in cfg:
        base_file = cfg.pop("defaults")
        if isinstance(base_file, list):
            base_file = base_file[0]
        base_path = os.path.join(os.path.dirname(path), f"{base_file}.yaml")
        with open(base_path) as f:
            base = yaml.safe_load(f)
        cfg = deep_merge(base, cfg)

    # Apply CLI overrides: key.subkey=value
    for ov in overrides:
        key_path, _, value = ov.partition("=")
        keys = key_path.split(".")
        node = cfg
        for k in keys[:-1]:
            node = node.setdefault(k, {})
        # Attempt type coercion
        try:
            node[keys[-1]] = yaml.safe_load(value)
        except Exception:
            node[keys[-1]] = value

    return cfg


# ─────────────────────────────────────────────────── evaluation ──

def evaluate(agent: SAC, env_name: str, n_episodes: int, max_steps: int, seed: int) -> dict:
    eval_env = make_env(env_name, max_episode_steps=max_steps,
                        render_mode="rgb_array", capture_frames=False)
    successes = []
    returns   = []

    for ep in range(n_episodes):
        obs, _ = eval_env.reset(seed=seed + ep + 10000)
        ep_return = 0.0
        done = False
        while not done:
            action = agent.select_action(obs, deterministic=True)
            obs, reward, terminated, truncated, info = eval_env.step(action)
            ep_return += reward
            done = terminated or truncated
        successes.append(float(info.get("is_success", 0.0)))
        returns.append(ep_return)

    eval_env.close()
    return {
        "success_rate": float(np.mean(successes)),
        "mean_return":  float(np.mean(returns)),
        "std_return":   float(np.std(returns)),
    }


# ─────────────────────────────────────────────────── main loop ──

def train(cfg: dict):
    # ── seeds ──
    seed = cfg["training"]["seed"]
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    logger.info(f"Device: {device}")

    # ── environment ──
    env_name   = cfg["env"]["name"]
    max_steps  = cfg["env"]["max_episode_steps"]
    task_desc  = get_task_description(env_name)

    replay_type = cfg["replay"]["type"]
    is_semantic = replay_type in ("semantic_per", "her_semantic_per")
    use_her     = replay_type in ("her", "her_per", "her_semantic_per")
    env = make_env(env_name, max_episode_steps=max_steps,
                   render_mode="rgb_array", capture_frames=is_semantic)
    obs, _ = env.reset(seed=seed)

    obs_dim    = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]
    action_scale = float(env.action_space.high[0])

    logger.info(f"Env: {env_name}  |  obs_dim={obs_dim}  action_dim={action_dim}")

    # ── agent ──
    sac_cfg = cfg["sac"]
    agent = SAC(
        obs_dim=obs_dim,
        action_dim=action_dim,
        action_scale=action_scale,
        hidden_dim=sac_cfg["hidden_dim"],
        lr_actor=sac_cfg["lr_actor"],
        lr_critic=sac_cfg["lr_critic"],
        lr_alpha=sac_cfg["lr_alpha"],
        gamma=sac_cfg["gamma"],
        tau=sac_cfg["tau"],
        init_temperature=sac_cfg["init_temperature"],
        auto_entropy_tuning=sac_cfg["auto_entropy_tuning"],
        device=device,
    )

    # ── replay buffer ──
    replay = make_buffer(cfg)
    if use_her:
        goal_dim = getattr(env, "goal_dim", 3)
        obs_dim_base = getattr(env, "obs_dim", obs_dim - goal_dim * 2)
        replay = HERBuffer(
            underlying_buffer=replay,
            goal_dim=goal_dim,
            obs_dim=obs_dim_base,
            k=cfg["replay"].get("her_k", 4),
            strategy=cfg["replay"].get("her_strategy", "future"),
        )

    # ── failure localizer (semantic PER only) ──
    vlm = None
    use_heuristic_localizer = False
    if is_semantic:
        vlm_provider = cfg["replay"].get("vlm_provider", "openai")
        if vlm_provider == "heuristic":
            vlm = GoalDistanceLocalizer()
            use_heuristic_localizer = True
        else:
            vlm_cfg = cfg.get("vlm", {})
            vlm = VLMFailureLocalizer(
                provider=vlm_provider,
                model=cfg["replay"]["vlm_model"],
                max_tokens=vlm_cfg.get("max_tokens", 512),
                temperature=vlm_cfg.get("temperature", 0.0),
                prompt_template=vlm_cfg.get("prompt_template"),
            )

    # ── logger ──
    run_name      = cfg.get("logging", {}).get("run_name", cfg["replay"]["type"])
    wandb_entity  = os.environ.get("WANDB_ENTITY", cfg.get("logging", {}).get("wandb_entity") or "")
    wandb_project = os.environ.get("WANDB_PROJECT", cfg.get("logging", {}).get("project", "semantic-per"))
    on_modal      = os.environ.get("MODAL_ENVIRONMENT") is not None
    use_wandb     = cfg.get("logging", {}).get("use_wandb", False) or on_modal

    train_log = TrainingLogger(
        log_dir=cfg.get("logging", {}).get("log_dir", "logs/"),
        run_name=run_name if f"seed{seed}" in run_name else f"{run_name}_seed{seed}",
        use_tensorboard=cfg.get("logging", {}).get("use_tensorboard", True),
        use_wandb=use_wandb,
        wandb_project=wandb_project,
        wandb_entity=wandb_entity or None,
        config=cfg,
    )

    # ── training state ──
    total_steps    = cfg["training"]["total_steps"]
    warmup_steps   = cfg["training"]["warmup_steps"]
    eval_interval  = cfg["training"]["eval_interval"]
    save_interval  = cfg["training"]["save_interval"]
    log_interval   = cfg["training"]["log_interval"]
    batch_size     = sac_cfg["batch_size"]
    updates_per    = sac_cfg["updates_per_step"]
    ckpt_dir       = cfg.get("logging", {}).get("checkpoint_dir", "checkpoints/")

    ep_obs              = obs
    ep_return           = 0.0
    ep_steps            = 0
    ep_count            = 0
    ep_start_time       = time.time()
    ep_start_idx        = 0
    ep_achieved_goals   = []   # for heuristic localizer
    goal_dim            = getattr(env, "goal_dim", 3)
    vlm_call_interval   = cfg["replay"].get("vlm_call_interval", 1)

    critic_losses  = []
    actor_losses   = []
    alpha_losses   = []
    alphas         = []
    td_errors_buf  = []
    best_success   = 0.0

    logger.info(f"Starting training: {total_steps:,} steps")

    for global_step in range(1, total_steps + 1):

        # ── mark episode start ──
        if ep_steps == 0:
            ep_start_idx = replay._ptr if hasattr(replay, "_ptr") else 0
            if use_her:
                replay.mark_episode_start()
            elif is_semantic and isinstance(replay, SemanticPERBuffer):
                replay.mark_episode_start()

        # ── action selection ──
        if global_step <= warmup_steps:
            action = env.action_space.sample()
        else:
            action = agent.select_action(ep_obs)

        # ── environment step ──
        # Extract achieved/desired goals directly from obs (avoids wrapper attr delegation issues)
        prev_achieved = ep_obs[-goal_dim*2:-goal_dim].copy() if goal_dim > 0 else None
        next_obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        next_achieved = next_obs[-goal_dim*2:-goal_dim].copy() if goal_dim > 0 else None

        # Track achieved goals for heuristic localizer
        if use_heuristic_localizer:
            ep_achieved_goals.append(prev_achieved)

        # Store transition (use terminated for done flag, not truncated)
        if use_her:
            replay.push(ep_obs, action, float(reward), next_obs, float(terminated),
                        achieved_goal=prev_achieved, next_achieved_goal=next_achieved)
        else:
            replay.push(ep_obs, action, float(reward), next_obs, float(terminated))

        ep_obs     = next_obs
        ep_return += reward
        ep_steps  += 1

        # ── critic updates ──
        if global_step > warmup_steps and len(replay) >= batch_size:
            for _ in range(updates_per):
                batch = replay.sample(batch_size)
                update_info = agent.update(batch)
                replay.update_priorities(batch["indices"], update_info["td_errors"])
                critic_losses.append(update_info["critic_loss"])
                actor_losses.append(update_info["actor_loss"])
                alpha_losses.append(update_info["alpha_loss"])
                alphas.append(update_info["alpha"])
                td_errors_buf.extend(np.abs(update_info["td_errors"]).tolist())

        # ── episode end ──
        if done:
            ep_count += 1
            ep_success = float(info.get("is_success", 0.0))
            ep_duration = time.time() - ep_start_time

            # ── HER relabeling ──
            if use_her:
                replay.finish_episode(env.unwrapped.compute_reward)

            # ── failure localization ──
            if (is_semantic and vlm is not None
                    and not ep_success
                    and ep_count % vlm_call_interval == 0):
                try:
                    window = cfg["replay"]["vlm_failure_window"]

                    if use_heuristic_localizer:
                        # Use ground-truth goal distances — no API call needed
                        desired_goal = ep_obs[-goal_dim:]
                        fail_t, conf, reason = vlm.localize_failure(
                            achieved_goals=ep_achieved_goals,
                            desired_goal=desired_goal,
                        )
                        failure_frame_img = None
                    else:
                        # Use VLM with keyframes
                        frames = getattr(env, "episode_frames", [])
                        k = cfg["replay"]["vlm_keyframes"]
                        kf_frames, kf_indices = select_keyframes(frames, k, strategy="uniform")
                        if not kf_frames:
                            raise ValueError("No frames captured")
                        fail_t, conf, reason = vlm.localize_failure(
                            kf_frames, kf_indices, task_desc, total_steps=ep_steps
                        )
                        try:
                            failure_frame_img = kf_frames[kf_indices.index(fail_t)]
                        except ValueError:
                            failure_frame_img = kf_frames[-1]
                        train_log.log_image(
                            "vlm/failure_keyframe", failure_frame_img, global_step,
                            caption=f"ep={ep_count} fail_t={fail_t}: {reason}",
                        )

                    replay.apply_semantic_priority(
                        episode_start_idx=ep_start_idx,
                        episode_length=ep_steps,
                        failure_timestep=fail_t,
                        window=window,
                    )
                    train_log.log_vlm_call(
                        step=global_step,
                        episode=ep_count,
                        failure_timestep=fail_t,
                        episode_length=ep_steps,
                        confidence=conf,
                        reasoning=reason,
                        failure_frame=failure_frame_img,
                    )
                except Exception as e:
                    logger.warning(f"VLM error (ep {ep_count}): {e}")

            # ── logging ──
            train_log.log({
                "train/episode_return": ep_return,
                "train/episode_steps":  ep_steps,
                "train/success":        ep_success,
                "train/buffer_size":    len(replay),
                "train/episode_duration": ep_duration,
            }, global_step, prefix="")

            # ── reset ──
            ep_obs, _ = env.reset()
            ep_return        = 0.0
            ep_steps         = 0
            ep_start_time    = time.time()
            ep_achieved_goals = []

        # ── periodic logging ──
        if global_step % log_interval == 0 and critic_losses:
            metrics = {
                "loss/critic":    np.mean(critic_losses),
                "loss/actor":     np.mean(actor_losses),
                "loss/alpha":     np.mean(alpha_losses),
                "train/alpha":    np.mean(alphas),
                "train/td_error": np.mean(td_errors_buf) if td_errors_buf else 0.0,
            }
            train_log.log(metrics, global_step)
            train_log.print_summary(global_step, metrics)
            critic_losses.clear()
            actor_losses.clear()
            alpha_losses.clear()
            alphas.clear()
            td_errors_buf.clear()

        # ── evaluation ──
        if global_step % eval_interval == 0:
            eval_metrics = evaluate(
                agent, env_name, cfg["training"]["eval_episodes"], max_steps, seed
            )
            train_log.log(eval_metrics, global_step, prefix="eval")
            train_log.print_summary(global_step, {"step": global_step, **eval_metrics})

            if eval_metrics["success_rate"] > best_success:
                best_success = eval_metrics["success_rate"]
                ckpt_path = os.path.join(ckpt_dir, run_name, "best")
                agent.save(ckpt_path)
                logger.info(f"New best success rate: {best_success:.3f}")
                train_log.log_checkpoint_artifact(
                    checkpoint_dir=ckpt_path,
                    name=f"{run_name}_best",
                    step=global_step,
                )

        # ── checkpoint ──
        if global_step % save_interval == 0:
            agent.save(os.path.join(ckpt_dir, run_name, f"step_{global_step}"))

    env.close()
    agent.save(os.path.join(ckpt_dir, run_name, "final"))
    train_log.close()
    logger.info(f"Training complete. Best success rate: {best_success:.3f}")
    return best_success


# ─────────────────────────────────────────────────── entrypoint ──

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    args, overrides = parser.parse_known_args()

    cfg = load_config(args.config, overrides)
    train(cfg)
