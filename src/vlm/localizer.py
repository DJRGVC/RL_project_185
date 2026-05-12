"""
VLM-based semantic failure localization.

Supports:
  - OpenAI  (gpt-4o, gpt-4-turbo)
  - Anthropic (claude-3-5-sonnet-20241022, claude-opus-4-6)

Given K keyframes from a failed episode and a task description, the VLM
identifies which frame index contains the critical failure event. We map
this back to an approximate buffer timestep for priority assignment.
"""
import json
import base64
import logging
import random
import time
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image
import io

logger = logging.getLogger(__name__)


class GoalDistanceLocalizer:
    """Heuristic failure localizer using ground-truth state geometry.

    Two-phase logic:
      1. Ballistic detection — if the object is thrown and moves freely
         (velocity peaks early and remains elevated after peak), the causal
         failure is the throw moment, not the closest approach. Used for
         tasks like FetchSlide where the agent loses contact mid-episode.
      2. Closest-approach fallback — for contact tasks (FetchPush,
         FetchPickAndPlace) where the agent maintains contact, argmin
         distance to the goal identifies the divergence point correctly.

    No API calls. Uses only achieved_goal trajectory (object position).
    """

    # Fraction of peak velocity that must persist after the peak to
    # classify the episode as ballistic (throw-and-release).
    BALLISTIC_RATIO   = 0.35
    # Minimum peak displacement per step to bother checking (noise floor).
    MIN_PEAK_DISP     = 0.008
    # How many steps after the peak to average for post-peak velocity.
    POST_PEAK_WINDOW  = 6

    def localize_failure(
        self,
        achieved_goals: List[np.ndarray],
        desired_goal: np.ndarray,
        **kwargs,
    ) -> Tuple[int, float, str]:
        positions = np.array(achieved_goals)  # (T, goal_dim)

        # ── ballistic phase detection ──────────────────────────────────
        if len(positions) > 4:
            displacements = np.linalg.norm(np.diff(positions, axis=0), axis=1)  # (T-1,)
            peak_t   = int(np.argmax(displacements))
            peak_vel = float(displacements[peak_t])

            if peak_vel > self.MIN_PEAK_DISP and peak_t < len(displacements) - self.POST_PEAK_WINDOW:
                post_window = displacements[peak_t + 1: peak_t + 1 + self.POST_PEAK_WINDOW]
                post_mean   = float(np.mean(post_window))
                if post_mean > self.BALLISTIC_RATIO * peak_vel:
                    # Object keeps moving after peak → agent released it here
                    reasoning = (
                        f"Ballistic throw at t={peak_t} "
                        f"(peak disp={peak_vel:.4f}, post-peak mean={post_mean:.4f}); "
                        f"agent lost causal control here."
                    )
                    return peak_t, 1.0, reasoning

        # ── closest-approach fallback ──────────────────────────────────
        distances = np.array([np.linalg.norm(ag - desired_goal) for ag in achieved_goals])
        failure_t = int(np.argmin(distances))
        reasoning = (
            f"Closest approach at t={failure_t} "
            f"(dist={float(distances[failure_t]):.3f}); "
            f"agent diverged from goal after this point."
        )
        return failure_t, 1.0, reasoning


def _frame_to_base64(frame: np.ndarray) -> str:
    img = Image.fromarray(frame.astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


class VLMFailureLocalizer:
    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o",
        max_tokens: int = 512,
        temperature: float = 0.0,
        prompt_template: Optional[str] = None,
    ):
        self.provider = provider
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = None

        self.prompt_template = prompt_template or (
            "You are analyzing a robotic manipulation trajectory.\n"
            "Task: {task_description}\n\n"
            "You are shown {K} keyframes from an episode that FAILED (the robot did not achieve the goal).\n"
            "The frames are shown in chronological order. Frame indices map to approximate timestep fractions:\n"
            "{frame_index_map}\n\n"
            "Identify the keyframe index (0-indexed) where the robot's action MOST CLEARLY caused or "
            "revealed the failure — the critical decision point or contact failure moment.\n\n"
            "If the failure point is ambiguous or cannot be determined from these frames, "
            'set failure_frame_index to null.\n\n'
            "Respond with ONLY a JSON object: "
            '{{"failure_frame_index": <int or null>, "reasoning": "<one sentence>"}}'
        )

        self._init_client()

    def _init_client(self):
        if self.provider == "openai":
            try:
                from openai import OpenAI
                self._client = OpenAI()
            except ImportError:
                raise ImportError("pip install openai>=1.10.0")
        elif self.provider == "anthropic":
            try:
                import anthropic
                self._client = anthropic.Anthropic()
            except ImportError:
                raise ImportError("pip install anthropic>=0.18.0")
        else:
            raise ValueError(f"Unknown VLM provider: {self.provider}")

    def localize_failure(
        self,
        frames: List[np.ndarray],
        timestep_indices: List[int],
        task_description: str,
        total_steps: int,
    ) -> Tuple[int, float, str]:
        """Query VLM to identify the failure timestep.

        Args:
            frames: List of K RGB frames (H x W x 3 uint8).
            timestep_indices: Actual buffer timestep for each frame.
            task_description: Natural language task description.
            total_steps: Total steps in this episode.

        Returns:
            (failure_timestep, confidence, reasoning)
            failure_timestep: estimated buffer timestep of failure
            confidence: 1.0 (VLM doesn't return confidence; extend as needed)
            reasoning: VLM's one-sentence explanation
        """
        from src.utils.keyframes import build_frame_index_map

        K = len(frames)
        frame_index_map = build_frame_index_map(timestep_indices, total_steps)
        prompt = self.prompt_template.format(
            task_description=task_description,
            K=K,
            frame_index_map=frame_index_map,
        )

        try:
            # Jitter to avoid rate-limit collisions across parallel runs
            time.sleep(random.uniform(0.5, 3.0))

            if self.provider == "openai":
                failure_frame_idx, reasoning = self._query_openai(frames, prompt)
            else:
                failure_frame_idx, reasoning = self._query_anthropic(frames, prompt)

            failure_frame_idx = max(0, min(K - 1, failure_frame_idx))
            failure_timestep = timestep_indices[failure_frame_idx]
            logger.debug(f"VLM failure frame {failure_frame_idx} → timestep {failure_timestep}: {reasoning}")
            return failure_timestep, 1.0, reasoning

        except Exception as e:
            logger.warning(f"VLM call failed: {e}. Defaulting to last-third of episode.")
            fallback_t = int(0.67 * total_steps)
            return fallback_t, 0.0, f"VLM error fallback: {e}"

    # ── provider implementations ──────────────────────────────────────────

    def _query_openai(self, frames: List[np.ndarray], prompt: str) -> Tuple[int, str]:
        content = [{"type": "text", "text": prompt}]
        for i, frame in enumerate(frames):
            b64 = _frame_to_base64(frame)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}",
                    "detail": "low",
                },
            })
            content.append({"type": "text", "text": f"[Frame {i} above]"})

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": content}],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        text = response.choices[0].message.content.strip()
        return self._parse_response(text)

    def _query_anthropic(self, frames: List[np.ndarray], prompt: str) -> Tuple[int, str]:
        content = []
        for i, frame in enumerate(frames):
            b64 = _frame_to_base64(frame)
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
            })
            content.append({"type": "text", "text": f"[Frame {i} above]"})
        content.append({"type": "text", "text": prompt})

        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{"role": "user", "content": content}],
        )
        text = response.content[0].text.strip()
        return self._parse_response(text)

    @staticmethod
    def _parse_response(text: str) -> Tuple[int, str]:
        """Parse JSON response from VLM."""
        # Strip markdown code fences if present
        clean = text.strip()
        if clean.startswith("```"):
            lines = clean.splitlines()
            clean = "\n".join(lines[1:-1]) if len(lines) > 2 else clean

        data = json.loads(clean)
        raw = data["failure_frame_index"]
        if raw is None:
            raise ValueError(f"VLM returned unknown: {data.get('reasoning', '')}")
        frame_idx = int(raw)
        reasoning = str(data.get("reasoning", ""))
        return frame_idx, reasoning
