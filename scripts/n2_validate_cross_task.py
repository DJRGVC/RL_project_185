"""
Agent N2 — Cross-Task VLM-Signal Transferability validation.

Claim under test: a single VLM prompt template can produce semantically-correct
failure annotations on FetchPush, FetchPickAndPlace, and FetchSlide, while a
learned task-specific priority head would need retraining per task.

This is the light validation experiment for Sub-experiment 1 of the N2 design.

Protocol:
  1. Generate N failed episodes per env (3 envs × 4 episodes = 12 total).
  2. For each episode, compute the ORACLE failure timestep using
     `GoalDistanceLocalizer` (ground-truth state geometry; has ballistic
     detection for FetchSlide).
  3. Query the VLM with the SAME prompt template (the
     `VLMFailureLocalizer` default prompt) across all three envs — varying
     only the {task_description} substitution.
  4. Measure agreement between the VLM-predicted failure timestep (mapped
     back from the chosen keyframe index) and the oracle's prediction.

Agreement metric:
  - "exact-keyframe agreement": VLM picks the same keyframe as the one
    closest to the oracle's failure_t.
  - "tolerant agreement": VLM's chosen keyframe is within ±1 keyframe slot
    of the oracle's closest keyframe (i.e. ~20% of episode tolerance with
    K=5 keyframes).
  - "VLM produced ANY valid index" (parse rate).
  - "raw timestep distance": |VLM_t - oracle_t| in steps.

Budget:
  - 12 episodes × 1 VLM call/episode = 12 calls at ~$0.04/call ≈ $0.50
  - Plus 3 retries-on-failure cushion → ~$0.65 total.

Output:
  - agent_reports/N2_cross_task_validation_outputs.json (per-episode results)
  - Tabulated agreement rates per env (printed + saved)

Usage:
  ANTHROPIC_API_KEY=$(cat ~/.anthropic_key) \
      python scripts/n2_validate_cross_task.py \
      --n_episodes 4 \
      --provider anthropic --model claude-opus-4-7
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("MUJOCO_GL", "egl")

from src.envs.wrappers import make_env, get_task_description  # noqa: E402
from src.utils.keyframes import select_keyframes  # noqa: E402
from src.vlm.localizer import GoalDistanceLocalizer, VLMFailureLocalizer  # noqa: E402
from src.utils.keyframes import build_frame_index_map  # noqa: E402


# The VLMFailureLocalizer's default template has an escaping bug in str.format
# (the JSON braces are not doubled). We define a corrected version here. The
# semantic content of the prompt is IDENTICAL to the localizer's template —
# only the {{ }} escaping changes.
SAME_PROMPT_TEMPLATE = (
    "You are analyzing a robotic manipulation trajectory.\n"
    "Task: {task_description}\n\n"
    "You are shown {K} keyframes from an episode that FAILED (the robot did not achieve the goal).\n"
    "The frames are shown in chronological order. Frame indices map to approximate timestep fractions:\n"
    "{frame_index_map}\n\n"
    "Identify the keyframe index (0-indexed) where the robot's action MOST CLEARLY caused or "
    "revealed the failure — the critical decision point or contact failure moment.\n\n"
    "If the failure point is ambiguous or cannot be determined from these frames, "
    "set failure_frame_index to null.\n\n"
    "Respond with ONLY a JSON object: "
    '{{"failure_frame_index": <int or null>, "reasoning": "<one sentence>"}}'
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("n2_validate")


# Per-env heuristic policies that reliably produce failures.

def _heuristic_policy_push_pickplace(obs, obs_dim, goal_dim, rng, noise: float = 0.5):
    """Drive gripper toward block + noise."""
    gripper_pos = obs[0:3]
    achieved_goal = obs[obs_dim: obs_dim + goal_dim]
    delta = achieved_goal - gripper_pos
    a_xyz = np.clip(delta * 20.0, -1.0, 1.0)
    a_grip = -0.5 + rng.normal(scale=0.4)
    base = np.concatenate([a_xyz, [a_grip]])
    return np.clip(base + rng.normal(scale=noise, size=4), -1.0, 1.0).astype(np.float32)


def _heuristic_policy_slide(obs, obs_dim, goal_dim, rng, noise: float = 0.3):
    """For FetchSlide: aggressive forward push + noise. Reliably produces
    ballistic throws that miss the distant target."""
    gripper_pos = obs[0:3]
    achieved_goal = obs[obs_dim: obs_dim + goal_dim]
    # FetchSlide target is distant; push hard along approach direction.
    delta = achieved_goal - gripper_pos
    a_xyz = np.clip(delta * 25.0, -1.0, 1.0)  # more aggressive
    a_grip = -1.0  # always closed for slide
    base = np.concatenate([a_xyz, [a_grip]])
    return np.clip(base + rng.normal(scale=noise, size=4), -1.0, 1.0).astype(np.float32)


def collect_failed_episodes(env_name: str, n_episodes: int, seed: int = 1234,
                            max_attempts: int = 40) -> List[Dict[str, Any]]:
    env = make_env(env_name, render_mode="rgb_array", capture_frames=True)
    flat_env = env.env if hasattr(env, "env") else env
    goal_dim = flat_env.goal_dim
    obs_dim = flat_env.obs_dim
    rng = np.random.default_rng(seed)

    policy = (_heuristic_policy_slide if env_name == "FetchSlide-v4"
              else _heuristic_policy_push_pickplace)

    out: List[Dict[str, Any]] = []
    attempts = 0
    while len(out) < n_episodes and attempts < max_attempts:
        ep_seed = int(seed + 17 * attempts)
        obs, info = env.reset(seed=ep_seed)
        achieved_at_reset = obs[obs_dim: obs_dim + goal_dim].copy()
        desired_goal = obs[obs_dim + goal_dim:].copy()

        achieved_goals = [achieved_at_reset]
        done = False
        steps = 0
        success = False
        while not done:
            action = policy(obs, obs_dim, goal_dim, rng=rng)
            obs, reward, term, trunc, info = env.step(action)
            achieved_goals.append(obs[obs_dim: obs_dim + goal_dim].copy())
            done = term or trunc
            steps += 1
            if info.get("is_success", 0):
                success = True

        attempts += 1
        if success:
            continue
        frames = list(env.episode_frames)
        if len(frames) < 5:
            continue
        # For variety in failure modes on FetchSlide, sanity-check the block actually moved.
        traj = np.array(achieved_goals)
        total_disp = float(np.linalg.norm(traj[-1] - traj[0]))
        if env_name == "FetchSlide-v4" and total_disp < 0.05:
            continue  # puck didn't move; skip
        out.append({
            "env_name": env_name,
            "seed": ep_seed,
            "frames": frames,
            "achieved_goals": achieved_goals,
            "desired_goal": desired_goal,
            "episode_length": steps,
            "total_disp": total_disp,
        })
        logger.info(
            f"  collected {env_name} ep (steps={steps}, frames={len(frames)}, "
            f"final dist={np.linalg.norm(achieved_goals[-1] - desired_goal):.3f} m, "
            f"total disp={total_disp:.3f} m)"
        )
    env.close()
    return out


def run_one_episode(ep: Dict[str, Any], vlm: VLMFailureLocalizer,
                    oracle: GoalDistanceLocalizer, K: int = 5) -> Dict[str, Any]:
    env_name = ep["env_name"]
    task_description = get_task_description(env_name)
    frames_all = ep["frames"]
    achieved_goals = ep["achieved_goals"]
    desired_goal = ep["desired_goal"]
    episode_length = ep["episode_length"]

    # Oracle (heuristic — uses sim state).
    oracle_t, _, oracle_reasoning = oracle.localize_failure(
        achieved_goals=achieved_goals, desired_goal=desired_goal,
    )

    # Select K=5 uniform keyframes.
    selected_frames, selected_indices = select_keyframes(
        frames_all, k=K, strategy="uniform",
    )
    total_steps = len(frames_all)

    # Map oracle_t to nearest keyframe index for fair comparison.
    oracle_kf_index = int(np.argmin([abs(t - oracle_t) for t in selected_indices]))

    t0 = time.time()
    try:
        # Build the prompt with the SAME template across all envs.
        frame_index_map = build_frame_index_map(selected_indices, total_steps)
        prompt = SAME_PROMPT_TEMPLATE.format(
            task_description=task_description,
            K=K,
            frame_index_map=frame_index_map,
        )
        # Call the localizer's underlying query helpers directly (these
        # exist because of localizer.py's bug — its public localize_failure
        # always falls back due to a format-string KeyError on its own
        # default template).
        if vlm.provider == "openai":
            vlm_kf_index, vlm_reasoning = vlm._query_openai(selected_frames, prompt)
        else:
            vlm_kf_index, vlm_reasoning = vlm._query_anthropic(selected_frames, prompt)
        vlm_kf_index = int(max(0, min(K - 1, vlm_kf_index)))
        vlm_t = selected_indices[vlm_kf_index]
        vlm_conf = 1.0
        vlm_parsed = True
    except Exception as e:
        logger.error(f"  VLM failed: {e}")
        vlm_t, vlm_conf, vlm_reasoning = -1, 0.0, f"ERROR: {e}"
        vlm_kf_index = -1
        vlm_parsed = False

    elapsed = time.time() - t0

    # Agreement metrics (only meaningful when vlm_parsed).
    if vlm_parsed:
        exact_agree = (vlm_kf_index == oracle_kf_index)
        tolerant_agree = abs(vlm_kf_index - oracle_kf_index) <= 1
        timestep_diff = abs(vlm_t - oracle_t)
        timestep_diff_pct = 100.0 * timestep_diff / max(episode_length, 1)
    else:
        exact_agree = False
        tolerant_agree = False
        timestep_diff = float("nan")
        timestep_diff_pct = float("nan")

    return {
        "env_name": env_name,
        "seed": ep["seed"],
        "episode_length": episode_length,
        "total_steps": total_steps,
        "task_description": task_description,
        "keyframe_indices": selected_indices,
        "oracle": {
            "failure_timestep": int(oracle_t),
            "keyframe_index": int(oracle_kf_index),
            "reasoning": oracle_reasoning,
        },
        "vlm": {
            "failure_timestep": int(vlm_t) if vlm_parsed else None,
            "keyframe_index": int(vlm_kf_index) if vlm_parsed else None,
            "reasoning": vlm_reasoning,
            "confidence": float(vlm_conf),
            "parsed": vlm_parsed,
            "wall_seconds": elapsed,
        },
        "agreement": {
            "exact_keyframe": bool(exact_agree),
            "tolerant_keyframe": bool(tolerant_agree),
            "timestep_diff": float(timestep_diff) if vlm_parsed else None,
            "timestep_diff_pct": float(timestep_diff_pct) if vlm_parsed else None,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_episodes", type=int, default=4,
                        help="Failed episodes per env (3 envs total).")
    parser.add_argument("--envs", nargs="+",
                        default=["FetchPush-v4", "FetchPickAndPlace-v4", "FetchSlide-v4"])
    parser.add_argument("--provider", choices=["openai", "anthropic"], default="anthropic")
    parser.add_argument("--model", default=None)
    parser.add_argument("--K", type=int, default=5)
    parser.add_argument("--out_dir", default=str(REPO_ROOT / "agent_reports"))
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--budget", type=int, default=20,
                        help="Hard cap on TOTAL VLM calls.")
    args = parser.parse_args()

    if args.provider == "anthropic" and args.model is None:
        args.model = "claude-opus-4-7"
    elif args.provider == "openai" and args.model is None:
        args.model = "gpt-4o"

    if args.provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not set — using anthropic fallback")
        args.provider = "anthropic"
        args.model = "claude-opus-4-7"
    if args.provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("Neither OPENAI_API_KEY nor ANTHROPIC_API_KEY is set.")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "N2_cross_task_validation_outputs.json"

    n_total = args.n_episodes * len(args.envs)
    if n_total > args.budget:
        args.n_episodes = max(1, args.budget // len(args.envs))
        logger.warning(f"Clipping to {args.n_episodes} episodes/env for budget")

    logger.info("=" * 70)
    logger.info(f"N2 Cross-Task VLM Transferability Validation")
    logger.info(f"Provider: {args.provider} / model: {args.model}")
    logger.info(f"Envs: {args.envs}")
    logger.info(f"Episodes/env: {args.n_episodes}")
    logger.info(f"K keyframes: {args.K}")
    logger.info(f"Output: {out_path}")
    logger.info("=" * 70)

    oracle = GoalDistanceLocalizer()
    vlm = VLMFailureLocalizer(
        provider=args.provider, model=args.model,
        max_tokens=512, temperature=0.0,
    )
    # opus-4-7 deprecates the temperature parameter — monkey-patch the
    # provider helpers in the localizer to drop temperature when the model
    # name contains "opus-4-7".
    _strip_temp = "opus-4-7" in (args.model or "")
    if _strip_temp:
        _orig_anthropic = vlm._query_anthropic
        def _query_anthropic_no_temp(frames, prompt):
            content = []
            from src.vlm.localizer import _frame_to_base64
            for i, frame in enumerate(frames):
                b64 = _frame_to_base64(frame)
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
                })
                content.append({"type": "text", "text": f"[Frame {i} above]"})
            content.append({"type": "text", "text": prompt})
            response = vlm._client.messages.create(
                model=vlm.model,
                max_tokens=vlm.max_tokens,
                messages=[{"role": "user", "content": content}],
            )
            text = response.content[0].text.strip()
            return vlm._parse_response(text)
        vlm._query_anthropic = _query_anthropic_no_temp
        logger.info("Patched _query_anthropic to drop deprecated temperature kwarg for opus-4-7.")

    # Log the exact prompt template so we can prove "same prompt across envs".
    logger.info(f"\nPROMPT TEMPLATE (SAME ACROSS ALL ENVS):\n{SAME_PROMPT_TEMPLATE}\n")

    all_outputs: List[Dict[str, Any]] = []
    seed = args.seed
    for env_name in args.envs:
        logger.info(f"### {env_name}")
        eps = collect_failed_episodes(env_name, n_episodes=args.n_episodes, seed=seed)
        seed += 1000
        logger.info(f"  → {len(eps)} failed episodes")
        for i, ep in enumerate(eps):
            logger.info(f"--- {env_name} ep {i+1}/{len(eps)} (seed={ep['seed']}) ---")
            try:
                row = run_one_episode(ep, vlm, oracle, K=args.K)
                all_outputs.append(row)
                logger.info(
                    f"  Oracle t={row['oracle']['failure_timestep']} (kf={row['oracle']['keyframe_index']}); "
                    f"VLM t={row['vlm']['failure_timestep']} (kf={row['vlm']['keyframe_index']}); "
                    f"exact={row['agreement']['exact_keyframe']}; tolerant={row['agreement']['tolerant_keyframe']}"
                )
                # Stream to disk.
                with open(out_path, "w") as f:
                    json.dump({
                        "meta": {
                            "agent": "N2",
                            "claim": "Cross-task VLM-signal transferability",
                            "provider": args.provider,
                            "model": args.model,
                            "prompt_template": SAME_PROMPT_TEMPLATE,
                            "K": args.K,
                            "envs": args.envs,
                            "n_episodes_per_env": args.n_episodes,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                        },
                        "episodes": all_outputs,
                    }, f, indent=2, default=_json_default)
            except Exception as e:
                logger.error(f"  ep failed: {e}", exc_info=True)

    # Aggregate per env.
    logger.info("\n" + "=" * 70)
    logger.info("AGGREGATE RESULTS PER ENV (same prompt across all envs):")
    logger.info("=" * 70)
    summary: Dict[str, Dict[str, Any]] = {}
    for env_name in args.envs:
        rows = [r for r in all_outputs if r["env_name"] == env_name]
        n = len(rows)
        n_parsed = sum(1 for r in rows if r["vlm"]["parsed"])
        n_exact = sum(1 for r in rows if r["agreement"]["exact_keyframe"])
        n_tolerant = sum(1 for r in rows if r["agreement"]["tolerant_keyframe"])
        mean_step_diff = float(np.mean([r["agreement"]["timestep_diff"]
                                        for r in rows if r["agreement"]["timestep_diff"] is not None])
                               if any(r["agreement"]["timestep_diff"] is not None for r in rows)
                               else float("nan"))
        summary[env_name] = {
            "n": n,
            "parse_rate": n_parsed / n if n else 0.0,
            "exact_kf_agreement": n_exact / n if n else 0.0,
            "tolerant_kf_agreement": n_tolerant / n if n else 0.0,
            "mean_timestep_diff": mean_step_diff,
        }
        logger.info(
            f"  {env_name:24s} n={n}  parse={n_parsed}/{n}  exact_kf={n_exact}/{n}  "
            f"tolerant_kf={n_tolerant}/{n}  mean_step_diff={mean_step_diff:.1f}"
        )

    # Save final summary onto the JSON.
    with open(out_path, "r") as f:
        existing = json.load(f)
    existing["summary"] = summary
    with open(out_path, "w") as f:
        json.dump(existing, f, indent=2, default=_json_default)
    logger.info(f"\nFinal results saved to {out_path}")
    return summary


def _json_default(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer)):
        return float(o)
    raise TypeError(f"Not JSON serialisable: {type(o)}")


if __name__ == "__main__":
    main()
