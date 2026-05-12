from .replay_buffer import UniformReplayBuffer
from .per_buffer import PERBuffer
from .semantic_buffer import SemanticPERBuffer
from .bidirectional_buffer import BidirectionalSemanticBuffer
from .vlm_rb_buffer import VLMRBBuffer


def _make_per(cfg):
    cap = cfg["replay"]["capacity"]
    return PERBuffer(
        capacity=cap,
        alpha=cfg["replay"]["per_alpha"],
        beta_start=cfg["replay"]["per_beta_start"],
        beta_end=cfg["replay"]["per_beta_end"],
        beta_anneal_steps=cfg["replay"]["per_beta_anneal_steps"],
        epsilon=cfg["replay"]["per_epsilon"],
    )


def _make_semantic(cfg):
    cap = cfg["replay"]["capacity"]
    return SemanticPERBuffer(
        capacity=cap,
        alpha=cfg["replay"]["per_alpha"],
        beta_start=cfg["replay"]["per_beta_start"],
        beta_end=cfg["replay"]["per_beta_end"],
        beta_anneal_steps=cfg["replay"]["per_beta_anneal_steps"],
        epsilon=cfg["replay"]["per_epsilon"],
        semantic_boost=cfg["replay"]["semantic_boost"],
        semantic_alpha=cfg["replay"]["semantic_alpha"],
    )


def _make_vlm_rb(cfg):
    """Build a Sharony-VLM-RB priority buffer.

    The clip scorer is built lazily (deferred to train.py via
    `buffer.vlm_score_fn = make_vlm_rb_scorer(...)`) so that
    `make_buffer` stays side-effect-free and doesn't require a VLM
    API key to import. For smoke tests, the buffer can be left with
    `vlm_score_fn=None` (degenerates to plain PER on the priority
    distribution branch) or have a stub scorer assigned by the test.
    """
    cap = cfg["replay"]["capacity"]
    return VLMRBBuffer(
        capacity=cap,
        alpha=cfg["replay"]["per_alpha"],
        beta_start=cfg["replay"]["per_beta_start"],
        beta_end=cfg["replay"]["per_beta_end"],
        beta_anneal_steps=cfg["replay"]["per_beta_anneal_steps"],
        epsilon=cfg["replay"]["per_epsilon"],
        clip_length=cfg["replay"].get("vlm_rb_clip_length", 32),
        vlm_score_fn=None,
        task_description=cfg["replay"].get("task_description", "robotic manipulation"),
        mixture_lambda_start=cfg["replay"].get("vlm_rb_lambda_start", 0.0),
        mixture_lambda_end=cfg["replay"].get("vlm_rb_lambda_end", 0.5),
        mixture_anneal_steps=cfg["replay"].get("vlm_rb_lambda_anneal_steps", 500_000),
        vlm_call_interval=cfg["replay"].get("vlm_call_interval", 10),
    )


def _make_bidir(cfg):
    cap = cfg["replay"]["capacity"]
    # Reuse semantic_boost as the default for both directions if specific
    # keys aren't set in the config.
    default_boost = cfg["replay"].get("semantic_boost", 10.0)
    return BidirectionalSemanticBuffer(
        capacity=cap,
        alpha=cfg["replay"]["per_alpha"],
        beta_start=cfg["replay"]["per_beta_start"],
        beta_end=cfg["replay"]["per_beta_end"],
        beta_anneal_steps=cfg["replay"]["per_beta_anneal_steps"],
        epsilon=cfg["replay"]["per_epsilon"],
        failure_boost=cfg["replay"].get("failure_boost", default_boost),
        success_boost=cfg["replay"].get("success_boost", default_boost),
    )


def make_buffer(cfg):
    rtype    = cfg["replay"]["type"]
    capacity = cfg["replay"]["capacity"]

    # HER types: the underlying buffer is constructed first;
    # HERBuffer wrapping happens in train.py after env is created.
    if rtype in ("uniform", "her", "cf_her"):
        return UniformReplayBuffer(capacity)
    elif rtype in ("per", "her_per"):
        return _make_per(cfg)
    elif rtype == "cf_her_per":
        # CF-HER stacked on top of PER: the underlying buffer is a
        # PERBuffer (proportional-priority sampling + IS correction +
        # sum-tree), and CounterfactualHERBuffer wraps it in train.py.
        # Synthetic Verified-CF / oracle / VLM transitions land in the
        # buffer at max-priority (PERBuffer.push default), so PER will
        # initially over-sample them — exactly the behaviour we want
        # (novel terminal successes get sampled more until their TD
        # error decays).
        return _make_per(cfg)
    elif rtype in ("semantic_per", "her_semantic_per"):
        return _make_semantic(cfg)
    elif rtype in ("bidir", "her_bidir"):
        return _make_bidir(cfg)
    elif rtype in ("vlm_rb", "her_vlm_rb"):
        # Sharony et al. (2026) VLM-RB baseline. The clip scorer is
        # attached in train.py once `task_description` and the env
        # are known.
        return _make_vlm_rb(cfg)
    else:
        raise ValueError(f"Unknown replay type: {rtype}")
