"""
VLM clip scorer for the Sharony-VLM-RB baseline.

Provides a callable ``score_clip(frames, task_description) -> float in [0, 1]``
that asks a vision-language model "Does this 32-frame clip contain a clear
instance of goal satisfaction?" and returns a soft confidence value.

The prompt wording matches Sharony et al. (2026, arXiv 2602.01915) §3.2 as
closely as our reproduction allows. We support two providers:

  - ``"anthropic"`` (default) using ``claude-sonnet-4-5`` to match our
    Phase 2 attempt 5 deployment.
  - ``"openai"`` for ``gpt-4o`` / ``gpt-4o-mini`` parity with our other
    VLM baselines.

Sharony et al. use a frozen PerceptionLM (Cho et al. 2025); that model
is not API-accessible and would require local-GPU hosting outside our
budget. We acknowledge this as a modelling-choice difference in
``agent_reports/_SHARONY_BASELINE_IMPL.md``.

Returned scalar p_VLM ∈ [0, 1] is the soft confidence that the clip
contains a clear instance of goal satisfaction, parsed from the
``{"goal_satisfied": "yes"|"no", "confidence": float}`` JSON response.
We map: ``yes`` → confidence; ``no`` → 1 - confidence; parse failure → 0.0.
"""
from __future__ import annotations

import base64
import io
import json
import logging
import os
import re
from typing import Any, Callable, List, Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


# Sharony's wording (verbatim where the project page exposed it). We
# adapt for Fetch by templating in ``{task_description}`` rather than
# hard-coding "doorkey" / "scene".
VLM_RB_SCORE_PROMPT = """You are scoring a short video clip from a robotics manipulation episode.

Task description: {task_description}

You are shown {n_frames} consecutive frames from the clip (chronological).

QUESTION: Does this clip contain a clear instance of goal satisfaction
anywhere in it? Look for contact between the gripper / object and the
goal region, plus displacement that suggests the task was achieved
within these frames.

Respond with ONLY a JSON object — no prose, no markdown:
{{
  "goal_satisfied": "yes" or "no",
  "confidence": <float in [0, 1]>,
  "reasoning": "<one short sentence>"
}}
"""


# Reuse the JSON extractor pattern from counterfactual.py.
_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}", re.MULTILINE)


def _extract_json(text: str) -> dict:
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n", "", s)
        s = re.sub(r"\n```$", "", s)
        s = s.strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        m = _JSON_BLOCK_RE.search(s)
        if not m:
            raise
        return json.loads(m.group(0))


def _frame_to_base64(frame: np.ndarray, quality: int = 75) -> str:
    img = Image.fromarray(np.asarray(frame, dtype=np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _downsample_frames(frames: List[Any], max_frames: int) -> List[np.ndarray]:
    """Keep at most `max_frames` frames, uniformly spaced through the clip.

    Sharony uses L=32 frames directly. We default ``max_frames=8`` so a
    32-frame clip fits comfortably in a single VLM call without
    blowing the token budget. The exact downsample ratio is reported
    in ``agent_reports/_SHARONY_BASELINE_IMPL.md``.
    """
    if not frames:
        return []
    arrs: List[np.ndarray] = []
    for f in frames:
        if hasattr(f, "convert"):
            arrs.append(np.asarray(f.convert("RGB")))
        else:
            arrs.append(np.asarray(f))
    if len(arrs) <= max_frames:
        return arrs
    idxs = np.linspace(0, len(arrs) - 1, num=max_frames, dtype=int)
    return [arrs[i] for i in idxs]


def _parse_score(text: str) -> float:
    """Parse the VLM JSON and return p_VLM ∈ [0, 1].

    Returns 0.0 (no goal satisfaction) on parse failure rather than
    raising — callers treat a failed score as "no positive signal".
    """
    try:
        data = _extract_json(text)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[VLM-RB scorer] JSON parse failed: {e}")
        return 0.0
    label = str(data.get("goal_satisfied", "")).strip().lower()
    try:
        conf = float(data.get("confidence", 0.5))
    except (TypeError, ValueError):
        conf = 0.5
    conf = float(np.clip(conf, 0.0, 1.0))
    if label == "yes":
        return conf
    if label == "no":
        return 1.0 - conf
    # Ambiguous label — treat as 0.5 weighted by reported confidence.
    return 0.5


def make_vlm_rb_scorer(
    provider: str = "anthropic",
    model: Optional[str] = None,
    max_tokens: int = 256,
    temperature: float = 0.0,
    image_detail: str = "low",
    max_frames_per_clip: int = 8,
) -> Callable[[List[Any], str], float]:
    """Build a synchronous clip scorer for :class:`VLMRBBuffer`.

    Returns a callable matching the buffer's ``vlm_score_fn`` signature:
    ``fn(clip_frames, task_description) -> float in [0, 1]``.

    Parameters
    ----------
    provider
        ``"anthropic"`` (default, Sonnet 4.5) or ``"openai"`` (gpt-4o).
    model
        Override the default model id for the provider.
    max_frames_per_clip
        Downsample the 32-frame clip to this many frames before the
        VLM call to keep the call cheap. Default 8.
    """
    provider = provider.lower()
    if provider == "anthropic":
        try:
            import anthropic  # noqa: F401
        except ImportError as e:  # pragma: no cover
            raise ImportError("pip install anthropic>=0.18.0") from e
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Either export it or use "
                "provider='openai'."
            )
        from anthropic import Anthropic
        client = Anthropic()
        if model is None:
            model = "claude-sonnet-4-5"

        def _score_anthropic(clip_frames: List[Any], task_description: str) -> float:
            frames = _downsample_frames(clip_frames, max_frames_per_clip)
            if not frames:
                return 0.0
            prompt = VLM_RB_SCORE_PROMPT.format(
                task_description=task_description,
                n_frames=len(frames),
            )
            content: List[dict] = []
            for i, frame in enumerate(frames):
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": _frame_to_base64(frame),
                    },
                })
                content.append({"type": "text", "text": f"[Frame {i} above]"})
            content.append({"type": "text", "text": prompt})

            kwargs: dict = dict(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": content}],
            )
            # Newer Claude models deprecate `temperature`; keep it
            # only for older ones (mirror counterfactual.py).
            if "opus-4-7" not in model and "sonnet-4-5" not in model:
                kwargs["temperature"] = temperature
            resp = client.messages.create(**kwargs)
            return _parse_score(resp.content[0].text.strip())

        return _score_anthropic

    if provider == "openai":
        try:
            from openai import OpenAI
        except ImportError as e:  # pragma: no cover
            raise ImportError("pip install openai>=1.10.0") from e
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY not set.")
        client = OpenAI()
        if model is None:
            model = "gpt-4o"

        def _score_openai(clip_frames: List[Any], task_description: str) -> float:
            frames = _downsample_frames(clip_frames, max_frames_per_clip)
            if not frames:
                return 0.0
            prompt = VLM_RB_SCORE_PROMPT.format(
                task_description=task_description,
                n_frames=len(frames),
            )
            content: List[dict] = [{"type": "text", "text": prompt}]
            for i, frame in enumerate(frames):
                b64 = _frame_to_base64(frame)
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b64}",
                        "detail": image_detail,
                    },
                })
                content.append({"type": "text", "text": f"[Frame {i} above]"})

            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": content}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return _parse_score(resp.choices[0].message.content.strip())

        return _score_openai

    raise ValueError(f"Unknown VLM-RB scorer provider: {provider}")


def make_stub_scorer(seed: Optional[int] = None) -> Callable[[List[Any], str], float]:
    """Return a deterministic random-uniform scorer for smoke tests.

    No network calls; returns ``np.random.uniform(0, 1)`` per clip.
    Useful for verifying buffer mechanics on CPU.
    """
    rng = np.random.default_rng(seed)

    def _stub(_frames: List[Any], _task_description: str) -> float:
        return float(rng.uniform(0.0, 1.0))

    return _stub
