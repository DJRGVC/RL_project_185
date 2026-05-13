"""Merge bake-off results from multiple sources into _VLM_BAKEOFF_outputs.json.

Sources:
  - _VLM_BAKEOFF_opus_only.json   (this morning's fresh opus-4-7 run on 10 eps)
  - _VLM_BAKEOFF_openai.json      (gpt-4o + gpt-5.2 run on the same 10 eps)
  - C1v2_real_data_outputs.json   (cached sonnet-4-5 data on the same 10 eps)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[1]


def normalize_call(c: Dict[str, Any]) -> Dict[str, Any]:
    return c  # already in canonical bake-off format


def extract_from_c1v2(c1v2_path: Path, model_key: str) -> List[Dict[str, Any]]:
    """Pull variant='all' from C1v2 real data outputs and reshape to bake-off format."""
    with open(c1v2_path) as f:
        d = json.load(f)
    out: List[Dict[str, Any]] = []
    for ep in d["episodes"]:
        v = ep["providers"].get(model_key, {}).get("variants", {}).get("all", {})
        prov_record = ep["providers"].get(model_key, {})
        c = {
            "env_name": ep["env_name"],
            "seed": int(ep["seed"]),
            "episode_length": prov_record.get("episode_length"),
            "task_description": prov_record.get("task_description"),
            "desired_goal": prov_record.get("desired_goal"),
            "achieved_goal_at_failure": prov_record.get("achieved_goal_at_failure"),
            "failure_timestep": prov_record.get("failure_timestep"),
            "failure_frame_pct": prov_record.get("failure_frame_pct"),
            "wall_time_seconds": v.get("wall_time_seconds"),
            "explanation": v.get("explanation"),
            "confidence": v.get("confidence"),
            "corrective_position": v.get("corrective_position"),
            "corrective_action": v.get("corrective_action"),
            "parse_error": v.get("parse_error"),
            "raw_response": v.get("raw_response"),
            "judge": v.get("judge"),
        }
        out.append(c)
    return out


def main():
    by_model: Dict[str, List[Dict[str, Any]]] = {}

    # 1. Opus 4.7 from this morning's run
    op = REPO / "agent_reports/_VLM_BAKEOFF_opus_only.json"
    with open(op) as f:
        d = json.load(f)
    by_model["anthropic:claude-opus-4-7"] = d["by_model"]["anthropic:claude-opus-4-7"]
    print(f"Opus 4.7: {len(by_model['anthropic:claude-opus-4-7'])} calls (fresh run)")

    # 2. Sonnet 4.5 from cached C1v2 (provider key was 'anthropic:claude-sonnet-4-5')
    c1v2 = REPO / "agent_reports/C1v2_real_data_outputs.json"
    sonnet_calls = extract_from_c1v2(c1v2, "anthropic:claude-sonnet-4-5")
    by_model["anthropic:claude-sonnet-4-5-20250929"] = sonnet_calls
    print(f"Sonnet 4.5: {len(sonnet_calls)} calls (cached C1v2)")

    # 3. OpenAI models (fresh run)
    oa = REPO / "agent_reports/_VLM_BAKEOFF_openai.json"
    if oa.exists():
        with open(oa) as f:
            d2 = json.load(f)
        for k, v in d2["by_model"].items():
            if isinstance(v, list):
                by_model[k] = v
                print(f"{k}: {len(v)} calls (fresh run)")
    else:
        print("WARNING: openai run output not found yet")

    # Build the merged file
    out = {
        "meta": {
            "models": list(by_model.keys()),
            "judge_model": "claude-opus-4-7",
            "K": 5,
            "n_episodes": max(len(v) for v in by_model.values()),
            "variant": "all",
            "envs": ["FetchPickAndPlace-v4", "FetchPush-v4"],
            "note": (
                "Bake-off merged from: (1) fresh opus-4-7 run 2026-05-12, "
                "(2) fresh OpenAI gpt-4o/gpt-5.2 run 2026-05-12, "
                "(3) cached C1v2 sonnet-4-5 run from 2026-05-11 "
                "(rate-limited org-cap prevented fresh sonnet run today; "
                "harness/episodes/judge are bit-identical to the C1v2 source). "
                "User requested gpt-5.5 but it is not in the OpenAI catalog; "
                "we substitute gpt-5.2 (newest available, released 2025-12-11)."
            ),
            "timestamp_merge": "2026-05-12",
        },
        "by_model": by_model,
    }
    target = REPO / "agent_reports/_VLM_BAKEOFF_outputs.json"
    with open(target, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {target}")


if __name__ == "__main__":
    main()
