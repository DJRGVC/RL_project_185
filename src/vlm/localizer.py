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

    ===== Oracle v3: three-phase logic (in priority order) =====
      1. Ballistic detection — if the object moves freely after a velocity
         peak (post-peak velocity > BALLISTIC_RATIO * peak), the causal
         failure is the throw moment. Used for FetchSlide.
      2. Contact-loss detection (NEW in v3) — for contact tasks (Push,
         PickAndPlace), find the timestep where the end-effector loses
         contact with the object while the object is still far from goal.
         This captures the dynamics failure (control loss) rather than
         the geometric near-miss.
      3. Closest-approach fallback — argmin distance, used only when
         neither ballistic nor contact-loss apply.

    No API calls. Uses ee_pos + object_pos extracted from the observation
    vector (Fetch obs structure: [0:3]=ee, [3:6]=object).
    """

    # Fraction of peak velocity that must persist after the peak to
    # classify the episode as ballistic (throw-and-release).
    BALLISTIC_RATIO   = 0.35
    # Minimum peak displacement per step to bother checking (noise floor).
    MIN_PEAK_DISP     = 0.008
    # How many steps after the peak to average for post-peak velocity.
    POST_PEAK_WINDOW  = 6

    # ===== Oracle v3 contact-loss params =====
    # Below this ee→object distance the gripper is considered in contact.
    CONTACT_DISTANCE      = 0.05
    # Minimum number of consecutive in-contact steps before "loss" counts
    # (avoids spurious losses from a brushing pass on the way to the object).
    MIN_CONTACT_RUN       = 2
    # Above this object→goal distance, the object is still meaningfully off-goal,
    # so a contact loss here is a causal failure (not just settling on goal).
    OBJECT_FAR_FROM_GOAL  = 0.10

    def localize_failure(
        self,
        achieved_goals: List[np.ndarray],
        desired_goal: np.ndarray,
        ee_positions: Optional[List[np.ndarray]] = None,
        object_positions: Optional[List[np.ndarray]] = None,
        **kwargs,
    ) -> Tuple[int, float, str]:
        """Localize the causal failure timestep using state geometry.

        Args:
            achieved_goals: list of T per-step achieved_goal vectors (object pos for
                            Push/Slide/PickPlace, ee for Reach).
            desired_goal:   final goal position.
            ee_positions:   optional list of T ee_pos vectors (for contact-aware v3).
            object_positions: optional list of T object_pos vectors (for contact-aware v3).
                              If both ee and object are provided, the v3 contact-loss
                              phase is enabled. Otherwise we degrade to v2 behavior.
        """
        positions = np.array(achieved_goals)  # (T, goal_dim)

        # ── Phase 1: ballistic detection ───────────────────────────────
        if len(positions) > 4:
            displacements = np.linalg.norm(np.diff(positions, axis=0), axis=1)  # (T-1,)
            peak_t   = int(np.argmax(displacements))
            peak_vel = float(displacements[peak_t])

            if peak_vel > self.MIN_PEAK_DISP and peak_t < len(displacements) - self.POST_PEAK_WINDOW:
                post_window = displacements[peak_t + 1: peak_t + 1 + self.POST_PEAK_WINDOW]
                post_mean   = float(np.mean(post_window))
                if post_mean > self.BALLISTIC_RATIO * peak_vel:
                    reasoning = (
                        f"[v3:ballistic] throw at t={peak_t} "
                        f"(peak disp={peak_vel:.4f}, post-peak mean={post_mean:.4f}); "
                        f"agent lost causal control here."
                    )
                    return peak_t, 1.0, reasoning

        # ── Phase 2: contact-loss detection (Oracle v3, NEW) ───────────
        if ee_positions is not None and object_positions is not None \
                and len(ee_positions) == len(object_positions) == len(positions):
            ee_arr  = np.asarray(ee_positions, dtype=np.float32)
            obj_arr = np.asarray(object_positions, dtype=np.float32)
            ee_obj_dist  = np.linalg.norm(ee_arr - obj_arr, axis=1)  # (T,)
            obj_goal_dist = np.linalg.norm(obj_arr - desired_goal, axis=1)  # (T,)
            in_contact   = ee_obj_dist < self.CONTACT_DISTANCE  # (T,) bool

            # Walk through episode finding contact-loss events:
            # a transition from in_contact at t → not-in-contact at t+1,
            # following a run of MIN_CONTACT_RUN consecutive contact steps,
            # while object is still meaningfully off-goal.
            contact_loss_t = -1
            run_len = 0
            for t in range(len(in_contact) - 1):
                if in_contact[t]:
                    run_len += 1
                else:
                    run_len = 0
                # Detect loss: contact run ended at t, and t+1 is not in contact
                if run_len >= self.MIN_CONTACT_RUN and not in_contact[t + 1] \
                        and obj_goal_dist[t] > self.OBJECT_FAR_FROM_GOAL:
                    contact_loss_t = t  # prefer the *latest* contact loss
                    run_len = 0  # reset, look for any later loss event

            if contact_loss_t >= 0:
                reasoning = (
                    f"[v3:contact-loss] t={contact_loss_t} "
                    f"(ee→obj={ee_obj_dist[contact_loss_t]:.3f}m at loss, "
                    f"obj→goal={obj_goal_dist[contact_loss_t]:.3f}m); "
                    f"gripper released object while object still off-goal."
                )
                return contact_loss_t, 1.0, reasoning

        # ── Phase 3: closest-approach fallback ─────────────────────────
        distances = np.array([np.linalg.norm(ag - desired_goal) for ag in achieved_goals])
        failure_t = int(np.argmin(distances))
        reasoning = (
            f"[v3:argmin] closest approach at t={failure_t} "
            f"(dist={float(distances[failure_t]):.3f}); "
            f"agent diverged from goal after this point."
        )
        return failure_t, 1.0, reasoning

    # ── Oracle v3 success localizer (best-progress timestep) ──────────────
    def localize_best_progress(
        self,
        achieved_goals: List[np.ndarray],
        desired_goal: np.ndarray,
        window: int = 5,
    ) -> Tuple[int, float, str]:
        """Identify the timestep of maximum windowed progress toward the goal.

        Used by BidirectionalSemanticBuffer as a proxy for what Sharony et al.'s
        VLM would mark as a "successful sub-trajectory" worth boosting. We use
        argmax(distance_reduction_over_window) instead of argmin(distance) so
        we catch *progress* (closing distance) rather than just *proximity*.
        """
        positions = np.array(achieved_goals, dtype=np.float32)
        dists = np.linalg.norm(positions - desired_goal, axis=1)
        T = len(dists)
        if T < 2:
            return 0, 0.0, "[v3:progress] degenerate episode"

        w = min(window, T - 1)
        # Distance reduction = dist[t] - dist[t+w]; positive means we got closer.
        progress = dists[:-w] - dists[w:]  # length T - w
        if len(progress) == 0:
            t = int(np.argmin(dists))
            return t, 0.5, f"[v3:progress-fallback] argmin t={t}"

        best_start = int(np.argmax(progress))
        # Mark the *center* of the progress window as the success timestep.
        best_t = best_start + w // 2
        reasoning = (
            f"[v3:progress] best progress at t={best_t} "
            f"(window dist drop {float(progress[best_start]):.3f} over {w} steps)"
        )
        return best_t, 1.0, reasoning


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
