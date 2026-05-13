"""
Agent N2 — independent semantic-correctness judge for cross-task validation.

For each VLM failure-reasoning string, ask an independent judge (Claude
Opus 4.7) whether the reasoning describes a task-typical failure mode
for the env in question. This corroborates the keyword-rubric scoring
in n2_validate_cross_task.py.

Budget: 12 episodes × 1 judge call = 12 calls (~$0.45 at $0.04/call).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("n2_judge")


TASK_FAILURE_MODES = {
    "FetchPush-v4": (
        "Common task-typical failure modes for FetchPush: (i) pushed block "
        "off the table edge; (ii) end-effector missed the block / went past "
        "it; (iii) pushed the block in the wrong direction (away from target); "
        "(iv) never made effective contact with the block."
    ),
    "FetchPickAndPlace-v4": (
        "Common task-typical failure modes for FetchPickAndPlace: (i) gripper "
        "failed to grasp the block (closed on empty space); (ii) gripper "
        "knocked the block off the table; (iii) grasped but dropped the block; "
        "(iv) lifted but moved in the wrong direction relative to the target."
    ),
    "FetchSlide-v4": (
        "Common task-typical failure modes for FetchSlide: (i) puck slid past "
        "/ short of the distant target; (ii) end-effector struck the puck in "
        "the wrong direction; (iii) end-effector missed the puck entirely; "
        "(iv) puck stopped due to insufficient strike force or wrong angle."
    ),
}


def judge_one(client, model: str, env_name: str, reasoning: str) -> dict:
    rubric = TASK_FAILURE_MODES[env_name]
    prompt = (
        f"You are evaluating whether a VLM correctly identified a failure mode "
        f"in a robotic-manipulation episode.\n\n"
        f"Task environment: {env_name}\n\n"
        f"{rubric}\n\n"
        f"The VLM produced this one-sentence failure annotation:\n"
        f'"{reasoning}"\n\n'
        f"Evaluate the annotation on:\n"
        f"  - task_relevant (0 or 1): Does the reasoning describe a failure "
        f"mode that is plausibly task-specific for this environment?\n"
        f"  - physically_plausible (0 or 1): Is the described failure mode "
        f"physically realizable in the env?\n"
        f"  - confidence (0..1): Your confidence in the above scores.\n\n"
        f"Respond with ONLY a JSON object: "
        f'{{"task_relevant": 0|1, "physically_plausible": 0|1, "confidence": <float>, '
        f'"explanation": "<one sentence>"}}'
    )
    response = client.messages.create(
        model=model,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1])
    return json.loads(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(REPO_ROOT / "agent_reports" / "N2_cross_task_validation_outputs.json"))
    parser.add_argument("--model", default="claude-opus-4-7")
    args = parser.parse_args()

    import anthropic
    client = anthropic.Anthropic()

    with open(args.input) as f:
        d = json.load(f)

    # Resume mode: keep existing successful judgements; only retry the failed/missing ones.
    existing = {j["index"]: j for j in d.get("judgements", []) if "task_relevant" in j}
    judgements = list(existing.values())
    todo_indices = [i for i, ep in enumerate(d["episodes"]) if i not in existing]
    logger.info(f"Resuming: {len(existing)} judgements already saved, {len(todo_indices)} to retry")

    for i in todo_indices:
        ep = d["episodes"][i]
        env = ep["env_name"]
        reasoning = ep["vlm"].get("reasoning", "")
        if not reasoning or "ERROR" in reasoning:
            judgements.append({"index": i, "env": env, "error": "missing reasoning"})
            continue
        try:
            time.sleep(30.0)  # heavy jitter to stay under 5 RPM (3 retries left)
            j = judge_one(client, args.model, env, reasoning)
            j["index"] = i
            j["env"] = env
            j["reasoning"] = reasoning
            judgements.append(j)
            logger.info(
                f"  [{env}] task_relevant={j.get('task_relevant')} "
                f"phys_plausible={j.get('physically_plausible')} conf={j.get('confidence')}"
            )
        except Exception as e:
            logger.error(f"  judge call failed: {e}")
            judgements.append({"index": i, "env": env, "error": str(e)})

    # Aggregate.
    summary = {}
    envs = sorted(set(j.get("env", "?") for j in judgements))
    for env in envs:
        rows = [j for j in judgements if j.get("env") == env and "task_relevant" in j]
        n = len(rows)
        n_task = sum(j.get("task_relevant", 0) for j in rows)
        n_phys = sum(j.get("physically_plausible", 0) for j in rows)
        summary[env] = {
            "n": n,
            "task_relevant_rate": n_task / n if n else 0.0,
            "phys_plausible_rate": n_phys / n if n else 0.0,
        }
        logger.info(f"{env}: task_relevant={n_task}/{n}, phys_plausible={n_phys}/{n}")

    d["judgements"] = judgements
    d["semantic_summary"] = summary
    with open(args.input, "w") as f:
        json.dump(d, f, indent=2)
    logger.info(f"Saved to {args.input}")


if __name__ == "__main__":
    main()
