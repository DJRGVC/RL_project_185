"""
VLM Counterfactual Reasoning for Credit Assignment (Path C).

Where `localizer.py` asks the VLM "which frame contains the failure?",
this module asks a fundamentally different question:

    "Given this failed trajectory, what should the robot have done
    differently at the critical frame so the episode would have succeeded?"

The VLM's answer — a desired achieved_goal, a corrective action, or a
free-form prescription — can be consumed as a hindsight relabeling target
or as a guidance vector. We treat the VLM as a counterfactual oracle and
emit structured JSON containing the proposed correction.

Supported providers:
  - openai (gpt-4o / gpt-4-turbo)         — primary
  - anthropic (claude-opus-4-x, sonnet)   — backup

This module does NOT depend on `localizer.py`; we re-implement small
utilities so the two stay independent and `localizer.py` is untouched.

Prompt variants (chosen at construction or query time):
  - "narrative":     free-form one-sentence correction
  - "action":        delta action vector [Δx, Δy, Δz, Δgrip] at the critical frame
  - "achieved_goal": target 3D position the object should have reached
  - "all":           query all three in a single call, returning a unified dict

Output schema (the keys present depend on the variant; absent keys map to None):

    {
        "explanation":         str,            # always present
        "corrective_action":   [dx,dy,dz,dg]   # variant in {"action","all"}
        "corrective_position": [x, y, z],      # variant in {"achieved_goal","all"}
        "confidence":          float in [0,1], # VLM self-reported (may be 0.5 default)
        "variant":             str,            # which prompt was used
        "raw_response":        str,            # raw VLM text for debugging
    }
"""
from __future__ import annotations

import base64
import io
import json
import logging
import os
import random
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Prompt templates
# ──────────────────────────────────────────────────────────────────────────────
#
# All templates assume the VLM has been given K keyframes in chronological
# order. {failure_frame_index} is the (0-indexed) keyframe identified as the
# critical failure moment (from `GoalDistanceLocalizer` or `VLMFailureLocalizer`).
# {failure_frame_pct} is its timestep fraction through the episode.

NARRATIVE_PROMPT = """You are analyzing a robotic manipulation trajectory.

Task: {task_description}

{K} keyframes from a FAILED episode are shown in chronological order.
Frame-to-timestep mapping:
{frame_index_map}

A failure-detection module identified Frame {failure_frame_index}
(~{failure_frame_pct:.0f}% through the episode) as the critical moment
where the robot's action caused or revealed the failure.

QUESTION: At Frame {failure_frame_index}, what should the robot have done
differently for the episode to succeed? Be specific about the corrective
behaviour in physical terms (e.g. "lift higher before approach", "close
gripper sooner", "push from the opposite side").

Respond with ONLY a JSON object:
{{
  "explanation": "<one concise sentence describing the corrective behaviour>",
  "confidence": <float in [0,1], your confidence that this correction would have led to success>
}}
"""

ACTION_PROMPT = """You are analyzing a robotic manipulation trajectory.

Task: {task_description}

The robot's action space is a 4-D vector: (Δx, Δy, Δz, gripper_command).
  - Δx, Δy, Δz ∈ [-1, 1] are end-effector velocity commands (negative = move
    in the -axis direction). Units: a value of 1.0 corresponds to roughly
    5 cm/step. The 'x' axis points away from the robot, 'y' to the left,
    'z' upward.
  - gripper_command ∈ [-1, 1]: -1 = close, +1 = open.

{K} keyframes from a FAILED episode are shown in chronological order.
Frame-to-timestep mapping:
{frame_index_map}

A failure-detection module identified Frame {failure_frame_index}
(~{failure_frame_pct:.0f}% through the episode) as the critical moment.

QUESTION: What 4-D corrective action vector should the robot have executed
at Frame {failure_frame_index} (instead of whatever it actually did) so the
episode would have succeeded? Provide a single delta-action [Δx, Δy, Δz, grip].

Be conservative: prefer small in-distribution deltas. If the failure is a
released-too-early issue, use grip≈-1. If it's a missed-target issue, point
the (Δx,Δy,Δz) toward the goal as seen in the frames.

Respond with ONLY a JSON object:
{{
  "corrective_action": [<dx>, <dy>, <dz>, <grip>],
  "explanation": "<one concise sentence>",
  "confidence": <float in [0,1]>
}}
"""

ACHIEVED_GOAL_PROMPT = """You are analyzing a robotic manipulation trajectory.

Task: {task_description}

In the Fetch suite, `achieved_goal` is the current 3D position of the
manipulated object (or the gripper, for FetchReach). The episode succeeds
when ||achieved_goal − desired_goal|| < 5 cm. The Fetch workspace coords
range roughly: x ∈ [1.05, 1.55] m, y ∈ [0.4, 1.1] m, z ∈ [0.4, 0.85] m
(the table surface is at z ≈ 0.42 m).

{K} keyframes from a FAILED episode are shown in chronological order.
Frame-to-timestep mapping:
{frame_index_map}

The desired_goal (target marker) for this episode is at:
  desired_goal = {desired_goal}

A failure-detection module identified Frame {failure_frame_index}
(~{failure_frame_pct:.0f}% through the episode) as the critical moment.

QUESTION: At Frame {failure_frame_index}, what 3D position SHOULD the object
have reached for the episode trajectory to be on track for success? In other
words, propose a hindsight `achieved_goal` for this frame — a counterfactual
location that, had the object been there at this timestep, would have set
the trajectory up to terminate within 5 cm of the desired_goal.

The proposed position must lie inside the Fetch workspace (above the table).

Respond with ONLY a JSON object:
{{
  "corrective_position": [<x>, <y>, <z>],
  "explanation": "<one concise sentence>",
  "confidence": <float in [0,1]>
}}
"""

ALL_PROMPT = """You are analyzing a robotic manipulation trajectory.

Task: {task_description}

{K} keyframes from a FAILED episode are shown in chronological order.
Frame-to-timestep mapping:
{frame_index_map}

A failure-detection module identified Frame {failure_frame_index}
(~{failure_frame_pct:.0f}% through the episode) as the critical moment.

Context for the action and goal spaces:
  - Action: 4-D delta vector (Δx, Δy, Δz, gripper) with components in [-1,1].
    Each unit ≈ 5 cm/step end-effector motion; gripper -1=close / +1=open.
  - achieved_goal / desired_goal: 3-D object (or gripper) positions in metres.
    The workspace spans roughly x∈[1.05,1.55], y∈[0.4,1.1], z∈[0.4,0.85].
  - desired_goal for this episode = {desired_goal}.

Provide a unified counterfactual:
  (a) the 3D position the object should have been at this frame
      (`corrective_position`),
  (b) the 4-D action the robot should have executed at this frame
      (`corrective_action`),
  (c) a one-sentence physical explanation.

Respond with ONLY a JSON object:
{{
  "corrective_position": [<x>, <y>, <z>],
  "corrective_action": [<dx>, <dy>, <dz>, <grip>],
  "explanation": "<one concise sentence>",
  "confidence": <float in [0,1]>
}}
"""


PROMPT_TEMPLATES: Dict[str, str] = {
    "narrative":     NARRATIVE_PROMPT,
    "action":        ACTION_PROMPT,
    "achieved_goal": ACHIEVED_GOAL_PROMPT,
    "all":           ALL_PROMPT,
}


# ──────────────────────────────────────────────────────────────────────────────
# Data class for the result
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class CounterfactualResult:
    variant: str
    explanation: str
    confidence: float
    corrective_position: Optional[List[float]] = None
    corrective_action: Optional[List[float]] = None
    raw_response: str = ""
    parse_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _frame_to_base64(frame: np.ndarray, quality: int = 85) -> str:
    img = Image.fromarray(frame.astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _build_frame_index_map(timestep_indices: List[int], total_steps: int) -> str:
    lines = []
    for i, t in enumerate(timestep_indices):
        pct = 100.0 * t / max(total_steps - 1, 1)
        lines.append(f"  Frame {i}: timestep {t} (~{pct:.0f}% through episode)")
    return "\n".join(lines)


_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}", re.MULTILINE)


def _extract_json(text: str) -> Dict[str, Any]:
    """Robust JSON extractor. Handles markdown code fences and prose padding."""
    s = text.strip()
    # Strip ```json ... ``` or ``` ... ```
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n", "", s)
        s = re.sub(r"\n```$", "", s)
        s = s.strip()
    # If still not JSON-only, find the first {...} balanced block
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        match = _JSON_BLOCK_RE.search(s)
        if not match:
            raise
        return json.loads(match.group(0))


def _coerce_vec(v: Any, expected_len: int) -> Optional[List[float]]:
    if v is None:
        return None
    if isinstance(v, dict):
        # e.g. {"x":..,"y":..,"z":..}  or {"dx":..,...,"grip":..}
        keys = ["x", "y", "z", "grip"] if expected_len == 4 else ["x", "y", "z"]
        try:
            return [float(v[k]) for k in keys[:expected_len]]
        except (KeyError, TypeError):
            return None
    try:
        out = [float(x) for x in v]
    except (TypeError, ValueError):
        return None
    if len(out) != expected_len:
        return None
    return out


# ──────────────────────────────────────────────────────────────────────────────
# Main class
# ──────────────────────────────────────────────────────────────────────────────


class CounterfactualLocalizer:
    """VLM-based counterfactual reasoning over failed trajectories.

    Usage:

        loc = CounterfactualLocalizer(provider="openai", model="gpt-4o")
        res = loc.query(
            frames=keyframes,                # List[np.ndarray]
            timestep_indices=[0, 12, 25, 37, 49],
            task_description="A robot arm must push a block to a goal.",
            total_steps=50,
            failure_timestep=37,             # output of GoalDistanceLocalizer
            desired_goal=np.array([1.30, 0.75, 0.42]),
            variant="all",                   # or "narrative"/"action"/"achieved_goal"
        )
        # res.corrective_position, res.corrective_action, res.explanation, ...
    """

    SUPPORTED_VARIANTS = list(PROMPT_TEMPLATES.keys())

    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.0,
        image_detail: str = "low",
    ):
        self.provider = provider.lower()
        if model is None:
            model = "gpt-4o" if self.provider == "openai" else "claude-opus-4-7"
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.image_detail = image_detail
        self._client = None
        self._init_client()

    # ── client setup ──────────────────────────────────────────────────────

    def _init_client(self):
        if self.provider == "openai":
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("pip install openai>=1.10.0")
            if not os.getenv("OPENAI_API_KEY"):
                raise RuntimeError(
                    "OPENAI_API_KEY not set. Either export it or construct with "
                    "provider='anthropic' and ANTHROPIC_API_KEY set."
                )
            self._client = OpenAI()
        elif self.provider == "anthropic":
            try:
                import anthropic
            except ImportError:
                raise ImportError("pip install anthropic>=0.18.0")
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise RuntimeError("ANTHROPIC_API_KEY not set.")
            self._client = anthropic.Anthropic()
        else:
            raise ValueError(f"Unknown VLM provider: {self.provider}")

    # ── public API ────────────────────────────────────────────────────────

    def query(
        self,
        frames: List[np.ndarray],
        timestep_indices: List[int],
        task_description: str,
        total_steps: int,
        failure_timestep: int,
        desired_goal: Optional[np.ndarray] = None,
        variant: str = "all",
        retries: int = 1,
    ) -> CounterfactualResult:
        """Query the VLM for a counterfactual at the failure moment.

        Args:
            frames: K RGB frames (uint8 H x W x 3) in chronological order.
            timestep_indices: actual buffer timestep for each frame.
            task_description: natural-language task summary.
            total_steps: total steps in this episode (for the index-map %).
            failure_timestep: timestep identified as the failure point.
            desired_goal: optional 3-D goal vector — required for the
                'achieved_goal' and 'all' variants.
            variant: which prompt template to use.
            retries: number of additional attempts on JSON parse failure.
        """
        if variant not in PROMPT_TEMPLATES:
            raise ValueError(
                f"Unknown variant '{variant}'. Choose from {self.SUPPORTED_VARIANTS}."
            )
        if variant in ("achieved_goal", "all") and desired_goal is None:
            raise ValueError(
                f"Variant '{variant}' requires `desired_goal` to be provided."
            )

        # ── map failure_timestep -> nearest keyframe index ─────────────
        failure_frame_index = int(
            np.argmin(np.abs(np.asarray(timestep_indices) - failure_timestep))
        )
        failure_frame_pct = 100.0 * failure_timestep / max(total_steps - 1, 1)

        prompt = PROMPT_TEMPLATES[variant].format(
            task_description=task_description,
            K=len(frames),
            frame_index_map=_build_frame_index_map(timestep_indices, total_steps),
            failure_frame_index=failure_frame_index,
            failure_frame_pct=failure_frame_pct,
            desired_goal=(
                None if desired_goal is None
                else [float(x) for x in np.asarray(desired_goal).tolist()]
            ),
        )

        last_err: Optional[Exception] = None
        for attempt in range(retries + 1):
            try:
                if self.provider == "openai":
                    text = self._call_openai(frames, prompt)
                else:
                    text = self._call_anthropic(frames, prompt)
                return self._parse(text, variant)
            except Exception as e:
                last_err = e
                logger.warning(
                    f"[CF variant={variant}] attempt {attempt + 1} failed: {e}"
                )
                time.sleep(0.5 + random.random())

        # Failure: return a result with the parse_error filled.
        return CounterfactualResult(
            variant=variant,
            explanation=f"VLM call/parse failed: {last_err}",
            confidence=0.0,
            raw_response="",
            parse_error=str(last_err),
        )

    # ── provider calls ────────────────────────────────────────────────────

    def _call_openai(self, frames: List[np.ndarray], prompt: str) -> str:
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
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return resp.choices[0].message.content.strip()

    def _call_anthropic(self, frames: List[np.ndarray], prompt: str) -> str:
        content: List[Dict[str, Any]] = []
        for i, frame in enumerate(frames):
            b64 = _frame_to_base64(frame)
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": b64,
                },
            })
            content.append({"type": "text", "text": f"[Frame {i} above]"})
        content.append({"type": "text", "text": prompt})

        kwargs: Dict[str, Any] = dict(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": content}],
        )
        # Claude Opus 4.7 deprecated `temperature`; pass it only for older models.
        if "opus-4-7" not in self.model:
            kwargs["temperature"] = self.temperature
        resp = self._client.messages.create(**kwargs)
        return resp.content[0].text.strip()

    # ── parsing ───────────────────────────────────────────────────────────

    @staticmethod
    def _parse(text: str, variant: str) -> CounterfactualResult:
        data = _extract_json(text)
        explanation = str(data.get("explanation", "")).strip()
        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        corrective_position = _coerce_vec(data.get("corrective_position"), 3)
        corrective_action = _coerce_vec(data.get("corrective_action"), 4)

        # Sanity: variants require certain fields. If missing, log but don't fail.
        if variant in ("achieved_goal", "all") and corrective_position is None:
            logger.warning(f"[CF variant={variant}] missing corrective_position")
        if variant in ("action", "all") and corrective_action is None:
            logger.warning(f"[CF variant={variant}] missing corrective_action")

        return CounterfactualResult(
            variant=variant,
            explanation=explanation,
            confidence=confidence,
            corrective_position=corrective_position,
            corrective_action=corrective_action,
            raw_response=text,
            parse_error=None,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Plausibility judge (uses Claude Opus 4.7 by default; cheap text-only call)
# ──────────────────────────────────────────────────────────────────────────────


JUDGE_PROMPT = """You are evaluating whether a proposed COUNTERFACTUAL CORRECTION
for a failed robot manipulation episode is physically plausible.

Task: {task_description}

The trajectory failed. At the critical timestep (~{failure_frame_pct:.0f}%
through the episode), the object was at:
  achieved_goal_at_failure = {achieved_goal}
and the target was at:
  desired_goal = {desired_goal}

A VLM proposed the following counterfactual:
  variant: {variant}
  corrective_position: {corrective_position}
  corrective_action:   {corrective_action}
  explanation:         "{explanation}"

Workspace bounds (approximate, in metres):
  x ∈ [1.05, 1.55], y ∈ [0.4, 1.1], z ∈ [0.4, 0.85]; table surface z≈0.42.
Action bounds: each component in [-1, 1], gripper -1=close +1=open.

Evaluate the counterfactual on three axes:
  1. plausibility (0-1): is the suggestion physically reasonable for the task
     and within workspace/action limits?
  2. goal_progress (0-1): would applying this correction MOVE the achieved_goal
     CLOSER to the desired_goal compared with the actual failure point?
  3. specificity (0-1): is the explanation concrete and actionable (vs. vague)?

Respond with ONLY a JSON object:
{{
  "plausibility":   <float 0-1>,
  "goal_progress":  <float 0-1>,
  "specificity":    <float 0-1>,
  "verdict": "<one sentence>"
}}
"""


def judge_counterfactual(
    result: CounterfactualResult,
    task_description: str,
    failure_frame_pct: float,
    achieved_goal: np.ndarray,
    desired_goal: np.ndarray,
    model: str = "claude-opus-4-7",
) -> Dict[str, Any]:
    """Use Claude Opus as a judge to score counterfactual plausibility.

    Text-only call (cheap). Returns dict with plausibility/goal_progress/
    specificity floats and a one-sentence verdict.
    """
    import anthropic
    client = anthropic.Anthropic()
    prompt = JUDGE_PROMPT.format(
        task_description=task_description,
        failure_frame_pct=failure_frame_pct,
        achieved_goal=[float(x) for x in np.asarray(achieved_goal).tolist()],
        desired_goal=[float(x) for x in np.asarray(desired_goal).tolist()],
        variant=result.variant,
        corrective_position=result.corrective_position,
        corrective_action=result.corrective_action,
        explanation=result.explanation,
    )
    try:
        kwargs: Dict[str, Any] = dict(
            model=model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        if "opus-4-7" not in model:
            kwargs["temperature"] = 0.0
        resp = client.messages.create(**kwargs)
        text = resp.content[0].text.strip()
        return _extract_json(text)
    except Exception as e:
        return {"plausibility": None, "goal_progress": None, "specificity": None,
                "verdict": f"judge failed: {e}"}


# ──────────────────────────────────────────────────────────────────────────────
# Adapter for agent C2's CounterfactualHERBuffer signature
# ──────────────────────────────────────────────────────────────────────────────


def make_counterfactual_fn(
    provider: str = "anthropic",
    model: Optional[str] = None,
    variant: str = "all",
    task_description: str = "robotic manipulation",
    K_keyframes: int = 5,
    min_confidence: float = 0.5,
    reject_teleport_radius_m: float = 0.05,
    return_action: bool = False,
):
    """Build the callback function agent C2 expects.

    C2's interface contract (see `agent_reports/C2_counterfactual_mechanism.md`):

        def localize_counterfactual(
            achieved_goals: np.ndarray,    # (T, goal_dim)
            desired_goal:   np.ndarray,    # (goal_dim,)
            keyframes:      Optional[List] = None,   # PIL.Image or np.ndarray
        ) -> Optional[List[Tuple[int, np.ndarray, float]]]:
            '''Returns list of (frame_index, corrective_goal_xyz, confidence) or None.'''

    Wraps `CounterfactualLocalizer` with the gating rules recommended by
    this report (Section 6):
      - reject if VLM confidence < `min_confidence`,
      - reject `achieved_goal` collapse: drop if
        ‖cf_pos − desired_goal‖ < `reject_teleport_radius_m`.

    Returns None on any VLM failure (parse error / API exception) so the
    SAC buffer can fall back to vanilla HER.

    Parameters
    ----------
    return_action
        If True, the returned tuples are 4-tuples
        `(frame_index, corrective_goal_xyz, confidence, corrective_action_4d
        or None)` so the verified-CF provider can pipe the proposed
        4-vector into N1's simulator verification gate. Default False
        preserves the original 3-tuple contract used by the vanilla VLM
        and oracle providers — backwards-compatible with C2's stub.
    """
    loc = CounterfactualLocalizer(provider=provider, model=model)

    def localize_counterfactual(
        achieved_goals: np.ndarray,
        desired_goal: np.ndarray,
        keyframes: Optional[List[Any]] = None,
    ) -> Optional[List[Tuple[int, np.ndarray, float]]]:
        if keyframes is None or len(keyframes) == 0:
            return None
        # Accept PIL or numpy frames; convert PIL → numpy.
        frames = []
        for kf in keyframes:
            if hasattr(kf, "convert"):                                   # PIL
                frames.append(np.array(kf.convert("RGB")))
            else:
                frames.append(np.asarray(kf))

        T = len(achieved_goals)
        # Uniform timestep mapping for the keyframes.
        if len(frames) == 1:
            ts_indices = [T // 2]
        else:
            ts_indices = [int(round(i * (T - 1) / (len(frames) - 1)))
                          for i in range(len(frames))]

        # Failure timestep: use the existing heuristic (closest approach /
        # ballistic detection) — fall back to mid-episode if degenerate.
        from .localizer import GoalDistanceLocalizer
        fl = GoalDistanceLocalizer()
        failure_t, _, _ = fl.localize_failure(
            achieved_goals=list(np.asarray(achieved_goals)),
            desired_goal=np.asarray(desired_goal),
        )
        if failure_t < max(2, T // 5):
            failure_t = T // 2

        try:
            res = loc.query(
                frames=frames,
                timestep_indices=ts_indices,
                task_description=task_description,
                total_steps=T,
                failure_timestep=failure_t,
                desired_goal=np.asarray(desired_goal),
                variant=variant,
            )
        except Exception as e:
            logger.warning(f"[counterfactual_fn] VLM call failed: {e}")
            return None

        if res.parse_error is not None:
            return None
        if res.confidence < min_confidence:
            return None
        if res.corrective_position is None:
            return None

        cf_pos = np.asarray(res.corrective_position, dtype=np.float32)
        # Reject the desired_goal-teleport collapse (failure-mode F1).
        if np.linalg.norm(cf_pos - np.asarray(desired_goal)) < reject_teleport_radius_m:
            return None

        if return_action:
            # 4-tuple form: includes corrective_action (may be None if the
            # variant did not request it / parsing failed).
            ca = (np.asarray(res.corrective_action, dtype=np.float32)
                  if res.corrective_action is not None else None)
            return [(int(failure_t), cf_pos, float(res.confidence), ca)]

        return [(int(failure_t), cf_pos, float(res.confidence))]

    return localize_counterfactual
