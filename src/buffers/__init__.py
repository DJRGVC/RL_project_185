from .replay_buffer import UniformReplayBuffer
from .per_buffer import PERBuffer
from .semantic_buffer import SemanticPERBuffer
from .bidirectional_buffer import BidirectionalSemanticBuffer


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
    elif rtype in ("semantic_per", "her_semantic_per"):
        return _make_semantic(cfg)
    elif rtype in ("bidir", "her_bidir"):
        return _make_bidir(cfg)
    else:
        raise ValueError(f"Unknown replay type: {rtype}")
