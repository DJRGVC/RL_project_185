"""
C1v2 — Re-run C1's prompt variants on REAL failed eval episodes.

Loads the pickled failed episodes (collected by `collect_real_failed_episodes.py`
from a partially-trained SAC+HER policy) and queries the VLM with all four
prompt variants `{narrative, action, achieved_goal, all}` under two providers
`{anthropic (Claude Opus 4.7), openai (GPT-4o)}`. Each VLM output is then
scored by the Claude Opus judge along (plausibility, goal_progress, specificity).

Output: agent_reports/C1v2_real_data_outputs.json + agent_reports/C1v2_real_data_scores.csv

Budget:
    10 episodes × 4 variants × 2 providers = 80 VLM generation calls
    + 80 judge calls (all-Claude judge, ~$0.01-0.02 / call text-only)
    = ~160 calls total, well under the $5 cap.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import pickle
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("MUJOCO_GL", "egl")

# Source the API keys if they exist as files (matches the project convention).
def _maybe_source_key_file(env_name: str, key_path: Path) -> None:
    if os.getenv(env_name):
        return
    if key_path.exists():
        os.environ[env_name] = key_path.read_text().strip()

_maybe_source_key_file("ANTHROPIC_API_KEY", Path.home() / ".anthropic_key")
_maybe_source_key_file("OPENAI_API_KEY", Path.home() / ".openai_key")

from src.envs.wrappers import get_task_description          # noqa: E402
from src.utils.keyframes import select_keyframes            # noqa: E402
from src.vlm.localizer import GoalDistanceLocalizer         # noqa: E402
from src.vlm.counterfactual import (                        # noqa: E402
    CounterfactualLocalizer, judge_counterfactual,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("c1v2_real_data_eval")


def localize_failure_t(achieved_goals: List[np.ndarray], desired_goal: np.ndarray,
                       episode_length: int) -> tuple[int, str]:
    """Same heuristic localizer + mid-clip rule that C1 used."""
    fl = GoalDistanceLocalizer()
    failure_t, _, reasoning = fl.localize_failure(
        achieved_goals=achieved_goals, desired_goal=desired_goal,
    )
    if failure_t < max(2, episode_length // 5):
        failure_t = episode_length // 2
        reasoning += " [clipped to mid-episode for VLM input]"
    return int(failure_t), reasoning


def run_episode_variants(
    ep: Dict[str, Any],
    loc: CounterfactualLocalizer,
    variants: List[str],
    K: int,
    do_judge: bool,
    judge_model: str,
) -> Dict[str, Any]:
    """Run all 4 prompt variants on one episode (single provider)."""
    env_name = ep["env_name"]
    task_description = get_task_description(env_name)
    frames_all = ep["frames"]
    achieved_goals = ep["achieved_goals"]
    desired_goal = ep["desired_goal"]
    episode_length = ep["episode_length"]

    failure_t, fl_reasoning = localize_failure_t(achieved_goals, desired_goal, episode_length)
    selected_frames, selected_indices = select_keyframes(
        frames_all, k=K, strategy="uniform"
    )
    total_steps = len(frames_all)
    failure_frame_pct = 100.0 * failure_t / max(episode_length - 1, 1)
    achieved_goal_at_failure = achieved_goals[failure_t]

    result: Dict[str, Any] = {
        "env_name": env_name,
        "seed": ep["seed"],
        "episode_length": episode_length,
        "total_frames": total_steps,
        "task_description": task_description,
        "desired_goal": desired_goal.tolist(),
        "achieved_goal_at_failure": achieved_goal_at_failure.tolist(),
        "achieved_goal_final": achieved_goals[-1].tolist(),
        "final_dist_m": float(np.linalg.norm(achieved_goals[-1] - desired_goal)),
        "failure_timestep": failure_t,
        "failure_frame_pct": failure_frame_pct,
        "heuristic_reasoning": fl_reasoning,
        "keyframe_indices": selected_indices,
        "variants": {},
    }

    for variant in variants:
        logger.info(f"    [variant={variant}] querying VLM...")
        t0 = time.time()
        try:
            r = loc.query(
                frames=selected_frames,
                timestep_indices=selected_indices,
                task_description=task_description,
                total_steps=total_steps,
                failure_timestep=failure_t,
                desired_goal=desired_goal,
                variant=variant,
                retries=1,
            )
        except Exception as e:
            logger.warning(f"      VLM exception: {e}")
            r = None
        elapsed = time.time() - t0

        if r is None:
            item = {
                "variant": variant,
                "explanation": f"VLM call exception",
                "confidence": 0.0,
                "corrective_position": None,
                "corrective_action": None,
                "parse_error": "vlm-call-failed",
                "raw_response": "",
                "wall_time_seconds": elapsed,
                "judge": None,
            }
        else:
            item = r.to_dict()
            item["wall_time_seconds"] = elapsed
            logger.info(
                f"      parsed: pos={r.corrective_position} "
                f"action={r.corrective_action} conf={r.confidence} ({elapsed:.1f}s)"
            )

            if do_judge and r.parse_error is None:
                try:
                    judge = judge_counterfactual(
                        result=r,
                        task_description=task_description,
                        failure_frame_pct=failure_frame_pct,
                        achieved_goal=achieved_goal_at_failure,
                        desired_goal=desired_goal,
                        model=judge_model,
                    )
                    item["judge"] = judge
                    logger.info(
                        f"      judge: plaus={judge.get('plausibility')} "
                        f"prog={judge.get('goal_progress')} "
                        f"spec={judge.get('specificity')}"
                    )
                except Exception as e:
                    logger.warning(f"      judge failed: {e}")
                    item["judge"] = {"error": str(e)}
            else:
                item["judge"] = None
        result["variants"][variant] = item

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode_pickles", nargs="+", required=True,
                        help="Paths to pickled failed episodes.")
    parser.add_argument("--providers", nargs="+",
                        default=["anthropic", "openai"],
                        help="VLM providers to evaluate.")
    parser.add_argument("--variants", nargs="+",
                        default=["narrative", "action", "achieved_goal", "all"],
                        help="Prompt variants to run.")
    parser.add_argument("--K", type=int, default=5)
    parser.add_argument("--judge_model", default="claude-opus-4-7",
                        help="Plausibility judge model (always anthropic).")
    parser.add_argument("--out_json", default="agent_reports/C1v2_real_data_outputs.json")
    parser.add_argument("--out_csv", default="agent_reports/C1v2_real_data_scores.csv")
    parser.add_argument("--no_judge", action="store_true")
    args = parser.parse_args()

    # Sanity check API keys
    if "anthropic" in args.providers and not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY missing; set or place ~/.anthropic_key")
    if "openai" in args.providers and not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY missing; set or place ~/.openai_key")
    if not os.getenv("ANTHROPIC_API_KEY") and not args.no_judge:
        raise RuntimeError("Judge requires ANTHROPIC_API_KEY.")

    # Load all episodes
    all_eps: List[Dict[str, Any]] = []
    for p in args.episode_pickles:
        with open(p, "rb") as f:
            eps = pickle.load(f)
            all_eps.extend(eps)
    logger.info(f"Loaded {len(all_eps)} episodes from {len(args.episode_pickles)} pickle(s)")
    logger.info(f"  Envs: {set(e['env_name'] for e in all_eps)}")
    logger.info(f"  Final dist range: "
                f"{min(e['final_dist'] for e in all_eps):.3f} - "
                f"{max(e['final_dist'] for e in all_eps):.3f} m")

    # Total budget
    do_judge = not args.no_judge
    n_calls = len(all_eps) * len(args.variants) * len(args.providers) * (2 if do_judge else 1)
    logger.info(f"Projected API calls: {n_calls}")

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)

    # Per-provider loop
    all_outputs: Dict[str, Any] = {
        "meta": {
            "providers": args.providers,
            "variants": args.variants,
            "judge_model": args.judge_model,
            "K": args.K,
            "n_episodes": len(all_eps),
            "envs": sorted(set(e["env_name"] for e in all_eps)),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "note": (
                "Failed eval episodes collected from a partially-trained "
                "SAC+HER policy (50k steps PickAndPlace, 30k Push). "
                "Same prompt variants and judge as C1 ablation, now run "
                "across both Claude Opus 4.7 and GPT-4o."
            ),
        },
        "episodes": [],
    }

    # We index outputs by (provider, episode_index) so the JSON has a flat list
    for ep_idx, ep in enumerate(all_eps):
        ep_record = {
            "ep_idx": ep_idx,
            "env_name": ep["env_name"],
            "seed": ep["seed"],
            "checkpoint": ep["checkpoint"],
            "providers": {},
        }
        for provider in args.providers:
            model = "gpt-4o" if provider == "openai" else "claude-opus-4-7"
            logger.info("=" * 70)
            logger.info(f"ep {ep_idx+1}/{len(all_eps)} | provider={provider} | "
                        f"env={ep['env_name']} seed={ep['seed']}")
            loc = CounterfactualLocalizer(provider=provider, model=model)
            try:
                provider_result = run_episode_variants(
                    ep, loc, variants=args.variants, K=args.K,
                    do_judge=do_judge, judge_model=args.judge_model,
                )
            except Exception as e:
                logger.error(f"  provider-level exception: {e}", exc_info=True)
                provider_result = {"error": str(e)}
            ep_record["providers"][provider] = provider_result

        all_outputs["episodes"].append(ep_record)

        # Stream to disk after each episode
        with open(args.out_json, "w") as f:
            json.dump(all_outputs, f, indent=2, default=_json_default)
        logger.info(f"  wrote {args.out_json}")

    # ── CSV summary (one row per (ep, provider, variant)) ──
    with open(args.out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "ep_idx", "env_name", "seed", "provider", "variant",
            "confidence", "plausibility", "goal_progress", "specificity",
            "parse_ok", "cf_pos_x", "cf_pos_y", "cf_pos_z",
            "cf_act_dx", "cf_act_dy", "cf_act_dz", "cf_act_grip",
            "explanation_snippet",
        ])
        for ep_rec in all_outputs["episodes"]:
            for provider, prov_res in ep_rec["providers"].items():
                if "variants" not in prov_res:
                    continue
                for variant, item in prov_res["variants"].items():
                    judge = item.get("judge") or {}
                    pos = item.get("corrective_position") or [None, None, None]
                    act = item.get("corrective_action") or [None, None, None, None]
                    w.writerow([
                        ep_rec["ep_idx"], ep_rec["env_name"], ep_rec["seed"],
                        provider, variant,
                        item.get("confidence"),
                        judge.get("plausibility") if isinstance(judge, dict) else None,
                        judge.get("goal_progress") if isinstance(judge, dict) else None,
                        judge.get("specificity")  if isinstance(judge, dict) else None,
                        int(item.get("parse_error") is None),
                        pos[0], pos[1], pos[2],
                        act[0], act[1], act[2], act[3],
                        (item.get("explanation") or "")[:120],
                    ])

    logger.info(f"\nWrote {args.out_json}")
    logger.info(f"Wrote {args.out_csv}")
    logger.info("DONE.")


def _json_default(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer)):
        return float(o)
    raise TypeError(f"Not JSON serializable: {type(o)}")


if __name__ == "__main__":
    main()
