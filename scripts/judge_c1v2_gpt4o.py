"""Post-hoc judge pass for the C1v2 GPT-4o outputs.

Reads agent_reports/C1v2_gpt4o_outputs.json (gen-only file, no judges),
adds a Claude Opus 4.7 plausibility judge to each variant entry,
writes back the same file with judge fields populated.

Designed to be safe to re-run: existing judges are kept.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
# Use the C1v2 worktree where src/vlm/counterfactual.py lives.
WORKTREE = REPO_ROOT / ".claude" / "worktrees" / "agent-a5a0e661e4795fd08"
sys.path.insert(0, str(WORKTREE))


def _maybe_source_key_file(env_name: str, key_path: Path) -> None:
    if os.getenv(env_name):
        return
    if key_path.exists():
        os.environ[env_name] = key_path.read_text().strip()


_maybe_source_key_file("ANTHROPIC_API_KEY", Path.home() / ".anthropic_key")
_maybe_source_key_file("OPENAI_API_KEY", Path.home() / ".openai_key")

from src.vlm.counterfactual import CounterfactualResult, judge_counterfactual  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("judge_c1v2")


def main():
    out_path = REPO_ROOT / "agent_reports" / "C1v2_gpt4o_outputs.json"
    with open(out_path) as f:
        data = json.load(f)

    n_eps = len(data["episodes"])
    n_done = 0
    n_skip = 0
    n_fail = 0
    for ep_idx, ep in enumerate(data["episodes"]):
        env_name = ep["env_name"]
        task_description = ep["task_description"]
        failure_frame_pct = ep["failure_frame_pct"]
        achieved_goal = np.asarray(ep["achieved_goal_at_failure"], dtype=float)
        desired_goal = np.asarray(ep["desired_goal"], dtype=float)
        for variant, item in ep["variants"].items():
            existing = item.get("judge")
            if isinstance(existing, dict) and existing.get("plausibility") is not None:
                n_skip += 1
                continue
            if item.get("parse_error") is not None:
                continue
            # Reconstruct a CounterfactualResult to feed the judge.
            r = CounterfactualResult(
                variant=variant,
                explanation=item.get("explanation", ""),
                confidence=item.get("confidence", 0.5),
                corrective_position=item.get("corrective_position"),
                corrective_action=item.get("corrective_action"),
                raw_response=item.get("raw_response", ""),
                parse_error=None,
            )
            logger.info(f"ep {ep_idx+1}/{n_eps} variant={variant} judging...")
            t0 = time.time()
            try:
                judge = judge_counterfactual(
                    result=r,
                    task_description=task_description,
                    failure_frame_pct=failure_frame_pct,
                    achieved_goal=achieved_goal,
                    desired_goal=desired_goal,
                    model="claude-opus-4-7",
                )
                item["judge"] = judge
                if isinstance(judge, dict) and judge.get("plausibility") is not None:
                    n_done += 1
                    logger.info(
                        f"  plaus={judge.get('plausibility')} "
                        f"prog={judge.get('goal_progress')} "
                        f"spec={judge.get('specificity')} "
                        f"({time.time()-t0:.1f}s)"
                    )
                else:
                    n_fail += 1
                    logger.warning(f"  judge returned null: {judge}")
            except Exception as e:
                n_fail += 1
                logger.warning(f"  judge exception: {e}")
                item["judge"] = {"error": str(e)}
        # Stream output after each episode.
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"  wrote {out_path} (so far: done={n_done} skip={n_skip} fail={n_fail})")

    logger.info(f"DONE.  done={n_done} skip={n_skip} fail={n_fail}")


if __name__ == "__main__":
    main()
