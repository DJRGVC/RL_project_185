"""
VLM model bake-off — 2026-05-12.

Goal: decide whether to relaunch Phase 2 attempt 5 against newer VLMs
(claude-opus-4-7 / gpt-5.2 [substituted for the nonexistent gpt-5.5]) instead
of the current Sonnet-4.5 + GPT-4o config.

Reuses C1v2's 10 real failed-eval episodes (6 PnP + 4 Push). For each
(model, episode) we run only `variant="all"` (the variant Phase 2 attempt 5
is actually consuming) and judge with claude-opus-4-7.

Quirks handled:
  - GPT-5 family rejects `max_tokens`; we use `max_completion_tokens` and
    drop `temperature` (only default supported).
  - We do NOT mutate src/vlm/counterfactual.py because Phase 2 attempt 5 is
    actively importing it on Modal.

Outputs:
  - agent_reports/_VLM_BAKEOFF_outputs.json   (raw per-call results)
  - agent_reports/_VLM_BAKEOFF_2026-05-12.md  (verdict + recommendation)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import pickle
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("MUJOCO_GL", "egl")


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
    CounterfactualLocalizer,
    CounterfactualResult,
    PROMPT_TEMPLATES,
    _build_frame_index_map,
    _frame_to_base64,
    judge_counterfactual,
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("vlm_bakeoff")


class GPT5Localizer(CounterfactualLocalizer):
    """OpenAI localizer with GPT-5 family parameter rules.

    GPT-5 models reject `max_tokens` (must use `max_completion_tokens`) and
    only accept the default `temperature`.
    """

    def _call_openai(self, frames, prompt):  # type: ignore[override]
        content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
        for i, frame in enumerate(frames):
            b64 = _frame_to_base64(frame)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}",
                    "detail": self.image_detail,
                },
            })
            content.append({"type": "text", "text": f"[Frame {i} above]"})

        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": content}],
            max_completion_tokens=self.max_tokens,
        )
        msg = resp.choices[0].message.content
        return (msg or "").strip()


def make_localizer(provider: str, model: str) -> CounterfactualLocalizer:
    if provider == "openai" and model.startswith("gpt-5"):
        return GPT5Localizer(provider=provider, model=model)
    return CounterfactualLocalizer(provider=provider, model=model)


def localize_failure_t(achieved_goals, desired_goal, episode_length):
    fl = GoalDistanceLocalizer()
    failure_t, _, reasoning = fl.localize_failure(
        achieved_goals=achieved_goals, desired_goal=desired_goal,
    )
    if failure_t < max(2, episode_length // 5):
        failure_t = episode_length // 2
        reasoning += " [clipped to mid-episode for VLM input]"
    return int(failure_t), reasoning


def run_one_call(
    ep: Dict[str, Any],
    loc: CounterfactualLocalizer,
    K: int,
    do_judge: bool,
    judge_model: str,
) -> Dict[str, Any]:
    """Run variant='all' once on one episode and judge it."""
    env_name = ep["env_name"]
    task_description = get_task_description(env_name)
    frames_all = ep["frames"]
    achieved_goals = ep["achieved_goals"]
    desired_goal = ep["desired_goal"]
    episode_length = ep["episode_length"]

    failure_t, fl_reasoning = localize_failure_t(
        achieved_goals, desired_goal, episode_length
    )
    selected_frames, selected_indices = select_keyframes(
        frames_all, k=K, strategy="uniform"
    )
    total_steps = len(frames_all)
    failure_frame_pct = 100.0 * failure_t / max(episode_length - 1, 1)
    achieved_goal_at_failure = achieved_goals[failure_t]

    t0 = time.time()
    try:
        r = loc.query(
            frames=selected_frames,
            timestep_indices=selected_indices,
            task_description=task_description,
            total_steps=total_steps,
            failure_timestep=failure_t,
            desired_goal=desired_goal,
            variant="all",
            retries=1,
        )
    except Exception as e:
        logger.warning(f"  VLM exception: {e}")
        r = None
    elapsed = time.time() - t0

    out: Dict[str, Any] = {
        "env_name": env_name,
        "seed": int(ep["seed"]),
        "episode_length": int(episode_length),
        "task_description": task_description,
        "desired_goal": desired_goal.tolist(),
        "achieved_goal_at_failure": achieved_goal_at_failure.tolist(),
        "failure_timestep": int(failure_t),
        "failure_frame_pct": float(failure_frame_pct),
        "wall_time_seconds": elapsed,
    }

    if r is None:
        out.update({
            "explanation": "VLM call exception",
            "confidence": 0.0,
            "corrective_position": None,
            "corrective_action": None,
            "parse_error": "vlm-call-failed",
            "raw_response": "",
            "judge": None,
        })
        return out

    out.update({
        "explanation": r.explanation,
        "confidence": r.confidence,
        "corrective_position": r.corrective_position,
        "corrective_action": r.corrective_action,
        "parse_error": r.parse_error,
        "raw_response": r.raw_response,
    })

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
            out["judge"] = judge
            logger.info(
                f"  judge: plaus={judge.get('plausibility')} "
                f"prog={judge.get('goal_progress')} "
                f"spec={judge.get('specificity')}"
            )
        except Exception as e:
            logger.warning(f"  judge failed: {e}")
            out["judge"] = {"error": str(e)}
    else:
        out["judge"] = None

    return out


def aggregate(per_call: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate per-call results across episodes for one model."""
    plaus, spec, prog = [], [], []
    teleports = 0
    teleport_total = 0
    parse_ok = 0
    for c in per_call:
        if c.get("parse_error") is None:
            parse_ok += 1
        j = c.get("judge") or {}
        if isinstance(j, dict):
            for vals, key in [(plaus, "plausibility"), (spec, "specificity"),
                              (prog, "goal_progress")]:
                v = j.get(key)
                if isinstance(v, (int, float)):
                    vals.append(float(v))

        pos = c.get("corrective_position")
        dg = c.get("desired_goal")
        if pos is not None and dg is not None and len(pos) == 3 and len(dg) == 3:
            teleport_total += 1
            d = float(np.linalg.norm(np.asarray(pos) - np.asarray(dg)))
            if d < 0.05:
                teleports += 1

    def _mean(xs):
        return float(np.mean(xs)) if xs else None

    return {
        "n_calls": len(per_call),
        "parse_ok": parse_ok,
        "plausibility_mean": _mean(plaus),
        "plausibility_n": len(plaus),
        "specificity_mean": _mean(spec),
        "specificity_n": len(spec),
        "goal_progress_mean": _mean(prog),
        "goal_progress_n": len(prog),
        "teleport_rate": (teleports / teleport_total) if teleport_total else None,
        "teleport_count": teleports,
        "teleport_denom": teleport_total,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--episode_pickles", nargs="+",
        default=[
            "agent_reports/c1v2_real_episodes_pickandplace.pkl",
            "agent_reports/c1v2_real_episodes_push.pkl",
        ],
    )
    parser.add_argument(
        "--models", nargs="+",
        default=[
            "anthropic:claude-opus-4-7",
            "anthropic:claude-sonnet-4-5-20250929",
            "openai:gpt-4o",
            "openai:gpt-5.2",
        ],
        help="provider:model pairs",
    )
    parser.add_argument("--K", type=int, default=5)
    parser.add_argument("--judge_model", default="claude-opus-4-7")
    parser.add_argument("--out_json",
                        default="agent_reports/_VLM_BAKEOFF_outputs.json")
    parser.add_argument("--no_judge", action="store_true")
    parser.add_argument("--max_episodes", type=int, default=None,
                        help="optional: limit episode count for smoke runs")
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY missing")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY missing")

    all_eps: List[Dict[str, Any]] = []
    for p in args.episode_pickles:
        with open(p, "rb") as f:
            all_eps.extend(pickle.load(f))
    if args.max_episodes is not None:
        all_eps = all_eps[: args.max_episodes]
    logger.info(f"Loaded {len(all_eps)} episodes")

    out: Dict[str, Any] = {
        "meta": {
            "models": args.models,
            "judge_model": args.judge_model,
            "K": args.K,
            "n_episodes": len(all_eps),
            "variant": "all",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "envs": sorted(set(e["env_name"] for e in all_eps)),
        },
        "by_model": {},
        "aggregates": {},
    }

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)

    for spec in args.models:
        provider, model = spec.split(":", 1)
        logger.info("=" * 70)
        logger.info(f"MODEL: {provider}:{model}")
        try:
            loc = make_localizer(provider, model)
        except Exception as e:
            logger.error(f"localizer init failed: {e}")
            out["by_model"][spec] = {"error": str(e)}
            continue

        per_call: List[Dict[str, Any]] = []
        for ep_idx, ep in enumerate(all_eps):
            logger.info(
                f"  ep {ep_idx+1}/{len(all_eps)} env={ep['env_name']} "
                f"seed={ep['seed']}"
            )
            res = run_one_call(
                ep, loc,
                K=args.K,
                do_judge=not args.no_judge,
                judge_model=args.judge_model,
            )
            per_call.append(res)
            # stream to disk after every call
            out["by_model"][spec] = per_call
            out["aggregates"][spec] = aggregate(per_call)
            with open(args.out_json, "w") as f:
                json.dump(out, f, indent=2, default=_json_default)

        logger.info(f"  AGG[{spec}] = {out['aggregates'][spec]}")

    logger.info(f"\nWrote {args.out_json}")
    logger.info("Aggregates:")
    for spec, agg in out["aggregates"].items():
        logger.info(f"  {spec}: {agg}")


def _json_default(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer)):
        return float(o)
    raise TypeError(f"not serializable: {type(o)}")


if __name__ == "__main__":
    main()
