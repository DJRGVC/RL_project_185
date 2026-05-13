"""SAC training loop. Variant selects the replay-priority strategy."""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from time import perf_counter

import numpy as np
import torch

from src import demos as demos_mod
from src import env as env_mod
from src import records
from src.config import RunCfg
from src.replay import PrioritizedReplayBuffer
from src.sac import Agent

log = logging.getLogger(__name__)

PROGRESS_EVERY = 5000
GPU_USD_PER_HOUR = 0.80  # Modal L4

# Variants that pre-load expert demos into the buffer.
DEMO_VARIANTS = {"demo-replay", "demo-priority"}
# Variants that update priorities by |TD error| during training.
PER_UPDATE_VARIANTS = {"per"}


def train(cfg: RunCfg) -> dict:
    records.configure_logging()
    run_dir = cfg.run_dir()
    run_dir.mkdir(parents=True, exist_ok=True)
    train_log = run_dir / "train.jsonl"
    eval_log = run_dir / "eval.jsonl"
    tag = f"{cfg.task}/{cfg.variant}/seed{cfg.seed}"
    started_at = records.utc_now_iso()
    env_info = records.environment_snapshot()

    records.write_yaml_snapshot(run_dir / "config.snapshot.yaml", records.cfg_to_dict(cfg.base))
    records.write_json(run_dir / "manifest.json", {
        "task": cfg.task, "variant": cfg.variant, "seed": cfg.seed,
        "total_steps": cfg.total_steps, "sparse_reward": cfg.sparse_reward,
        "started_at_utc": started_at, "environment": env_info,
    })
    log.info("[%s] run_dir=%s", tag, run_dir)
    log.info("[%s] torch=%s metaworld=%s mujoco=%s",
             tag, env_info.get("torch"), env_info.get("metaworld"), env_info.get("mujoco"))
    for g in env_info.get("gpus") or []:
        log.info("[%s] gpu=%s mem=%sGB cc=%s", tag, g["name"], g["total_mem_gb"], g["capability"])

    rng_py = random.Random(cfg.seed)
    rng_np = np.random.default_rng(cfg.seed)
    torch.manual_seed(cfg.seed)

    env, train_tasks = env_mod.make_env(
        cfg.task, cfg.seed, cfg.env.max_episode_steps, camera_name=cfg.env.camera_name,
    )
    eval_env, eval_tasks = env_mod.make_env(
        cfg.task, cfg.seed + 31337, cfg.env.max_episode_steps, camera_name=cfg.env.camera_name,
    )

    obs_dim = int(np.prod(env.observation_space.shape))
    act_dim = int(np.prod(env.action_space.shape))
    act_low = env.action_space.low.astype(np.float32)
    act_high = env.action_space.high.astype(np.float32)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log.info("[%s] device=%s obs_dim=%d act_dim=%d", tag, device, obs_dim, act_dim)

    agent = Agent(obs_dim, act_dim, act_low, act_high, cfg.sac, device)
    buffer = PrioritizedReplayBuffer(
        capacity=cfg.replay.capacity, obs_dim=obs_dim, act_dim=act_dim,
        per_alpha=cfg.replay.per_alpha, priority_epsilon=cfg.replay.priority_epsilon,
        default_priority=cfg.replay.default_priority, rng=rng_np,
    )

    # Demo pre-loading.
    demo_stats: dict | None = None
    if cfg.variant in DEMO_VARIANTS:
        log.info("[%s] collecting %d expert demos (noise=%.2f)",
                 tag, cfg.demos.episodes_per_task, cfg.demos.noise)
        t_demos = perf_counter()
        transitions, demo_stats = demos_mod.collect(
            task=cfg.task, sparse_reward=cfg.sparse_reward,
            cfg=cfg.demos, env_cfg=cfg.env, seed=cfg.seed + 7919,
        )
        # demo-priority pins demos at cfg.replay.demo_priority. demo-replay
        # inserts them at default priority so they're sampled like any other
        # transition.
        prio = cfg.replay.demo_priority if cfg.variant == "demo-priority" else None
        for tr in transitions:
            buffer.add(tr.obs, tr.action, tr.reward, tr.next_obs, tr.done,
                       is_demo=(cfg.variant == "demo-priority"), priority=prio)
        log.info("[%s] demos loaded in %.0fs (buffer=%d)",
                 tag, perf_counter() - t_demos, len(buffer))
        demo_stats["load_s"] = perf_counter() - t_demos

    obs, _ = env_mod.reset_with_task(env, train_tasks, rng_py)
    ep_step = ep_count = 0
    ep_return = 0.0
    ep_success = False

    budget = records.WallBudget()
    t0 = perf_counter()

    for step in range(1, cfg.total_steps + 1):
        if step <= cfg.sac.start_steps:
            action = rng_np.uniform(act_low, act_high).astype(np.float32)
        else:
            with budget.measure("agent_act"):
                action = np.clip(agent.act(obs, deterministic=False), act_low, act_high).astype(np.float32)

        with budget.measure("env_step"):
            next_obs, reward, terminated, truncated, info = env.step(action)
        next_obs = np.asarray(next_obs, dtype=np.float32)
        success = bool(info.get("success", False))
        ep_success = ep_success or success
        reward = float(success) if cfg.sparse_reward else float(reward)
        buffer.add(obs, action, reward, next_obs, bool(terminated))
        obs = next_obs
        ep_step += 1
        ep_return += reward

        if terminated or truncated:
            obs, _ = env_mod.reset_with_task(env, train_tasks, rng_py)
            ep_count += 1
            records.append(train_log, {
                "kind": "episode", "step": step, "ep": ep_count,
                "ep_return": ep_return, "ep_success": ep_success, "ep_length": ep_step,
            })
            ep_step = 0
            ep_return = 0.0
            ep_success = False

        if step >= cfg.sac.update_after and step % cfg.sac.update_every == 0 and len(buffer) >= cfg.sac.batch_size:
            beta = _beta(step, cfg)
            with budget.measure("buffer_sample"):
                batch = buffer.sample(cfg.sac.batch_size, beta)
            with budget.measure("agent_update"):
                stats = agent.update(batch)
            if cfg.variant in PER_UPDATE_VARIANTS:
                buffer.update_priorities(batch.indices, stats.td_errors)
            if step % 1000 == 0:
                pri = buffer.priorities[:len(buffer)]
                records.append(train_log, {
                    "kind": "update", "step": step, "beta": float(beta),
                    "buf_size": int(len(buffer)),
                    "buf_priorities": records.percentiles(pri) if len(buffer) else {},
                    "sampled_priorities": records.percentiles(pri[batch.indices]),
                    "is_weights": {"mean": stats.is_weight_mean, "max": stats.is_weight_max},
                    "q_loss": stats.q_loss, "pi_loss": stats.pi_loss,
                    "alpha_loss": stats.alpha_loss, "alpha": stats.alpha,
                    "q1_mean": stats.q1_mean, "q2_mean": stats.q2_mean,
                    "target_q_mean": stats.target_q_mean,
                    "log_prob_mean": stats.log_prob_mean, "log_prob_std": stats.log_prob_std,
                    "action_abs_mean": stats.action_abs_mean,
                    "action_saturation": stats.action_saturation,
                    "critic_grad_norm": stats.critic_grad_norm,
                    "actor_grad_norm": stats.actor_grad_norm,
                    "td_abs": records.percentiles(np.abs(stats.td_errors)),
                })

        if step % PROGRESS_EVERY == 0 and step % cfg.eval.every_steps != 0:
            _log_progress(tag, step, cfg, buffer, ep_count, t0)

        if step % cfg.eval.every_steps == 0:
            with budget.measure("evaluate"):
                eval_stats = _evaluate(agent, eval_env, eval_tasks, cfg, rng_py)
            records.append(eval_log, {"step": step, "eval_episodes": cfg.eval.episodes, **eval_stats})
            _log_progress(tag, step, cfg, buffer, ep_count, t0, eval_stats=eval_stats)

    env.close()
    eval_env.close()

    wall_s = perf_counter() - t0
    eval_curve = records.read_jsonl(eval_log)
    summary = {
        "task": cfg.task, "variant": cfg.variant, "seed": cfg.seed,
        "total_steps": cfg.total_steps, "sparse_reward": cfg.sparse_reward,
        "started_at_utc": started_at, "finished_at_utc": records.utc_now_iso(),
        "wall_s": wall_s, "wall_hours": wall_s / 3600,
        "wall_breakdown": budget.as_dict(),
        "steps_per_second": cfg.total_steps / wall_s if wall_s else 0.0,
        "ep_count": ep_count,
        "demo_stats": demo_stats,
        "final_success_rate": eval_curve[-1]["success_rate"] if eval_curve else None,
        "final_mean_return": eval_curve[-1]["mean_return"] if eval_curve else None,
        "final_mean_ep_length": eval_curve[-1].get("mean_ep_length") if eval_curve else None,
        "eval_curve": eval_curve,
        "gpu_usd_per_hour": GPU_USD_PER_HOUR,
        "cost_estimate_usd": (wall_s / 3600) * GPU_USD_PER_HOUR,
    }
    records.write_json(run_dir / "summary.json", summary)
    log.info("[%s] done wall=%.0fs (%.2fh) cost=$%.2f final_success=%s",
             tag, wall_s, wall_s / 3600, summary["cost_estimate_usd"], summary["final_success_rate"])
    if budget.totals:
        log.info("[%s] wall_breakdown: %s", tag,
                 " ".join(f"{k}={v:.0f}s" for k, v in sorted(budget.totals.items(), key=lambda kv: -kv[1])))
    return summary


def _log_progress(tag, step, cfg, buffer, ep_count, t0, *, eval_stats=None):
    now = perf_counter()
    rate = step / max(now - t0, 1e-6)
    eta = (cfg.total_steps - step) / max(rate, 1e-6)
    if eval_stats:
        log.info("[%s] step=%7d success=%.2f return=%.2f ep_len=%.0f elapsed=%.0fs eta=%.0fs",
                 tag, step, eval_stats["success_rate"], eval_stats["mean_return"],
                 eval_stats["mean_ep_length"], now - t0, eta)
    else:
        log.info("[%s] step=%7d buf=%d ep=%d elapsed=%.0fs eta=%.0fs (%.1fk/s)",
                 tag, step, len(buffer), ep_count, now - t0, eta, rate / 1000)


def _evaluate(agent, env, tasks, cfg: RunCfg, rng: random.Random) -> dict:
    successes = 0
    returns: list[float] = []
    lengths: list[int] = []
    first_success_steps: list[int] = []
    for _ in range(cfg.eval.episodes):
        obs, _ = env_mod.reset_with_task(env, tasks, rng)
        ep_return = 0.0
        ep_success = False
        first_success: int | None = None
        for t in range(cfg.env.max_episode_steps):
            action = agent.act(obs, deterministic=True).astype(np.float32)
            obs, reward, terminated, truncated, info = env.step(action)
            obs = np.asarray(obs, dtype=np.float32)
            ep_return += float(info.get("success", False)) if cfg.sparse_reward else float(reward)
            if info.get("success", False):
                if not ep_success:
                    first_success = t + 1
                ep_success = True
            if terminated or truncated:
                break
        successes += int(ep_success)
        returns.append(ep_return)
        lengths.append(t + 1)
        if first_success is not None:
            first_success_steps.append(first_success)
    n = max(len(returns), 1)
    return {
        "success_rate": successes / n,
        "mean_return": float(np.mean(returns)) if returns else 0.0,
        "std_return": float(np.std(returns, ddof=0)) if returns else 0.0,
        "mean_ep_length": float(np.mean(lengths)) if lengths else 0.0,
        "mean_steps_to_first_success": float(np.mean(first_success_steps)) if first_success_steps else None,
        "n_successes": successes,
        "n_episodes": n,
    }


def _beta(step: int, cfg: RunCfg) -> float:
    frac = min(1.0, step / max(cfg.total_steps, 1))
    return cfg.replay.per_beta_start + frac * (cfg.replay.per_beta_end - cfg.replay.per_beta_start)
