"""Frozen-dataclass config; one `load(path)` entry."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import yaml


@dataclass(frozen=True)
class EnvCfg:
    max_episode_steps: int
    camera_name: str | None = None


@dataclass(frozen=True)
class SacCfg:
    gamma: float
    tau: float
    lr_actor: float
    lr_critic: float
    lr_alpha: float
    hidden_sizes: tuple[int, ...]
    batch_size: int
    start_steps: int
    update_after: int
    update_every: int
    target_update_every: int
    target_entropy: float | None


@dataclass(frozen=True)
class ReplayCfg:
    capacity: int
    per_alpha: float
    per_beta_start: float
    per_beta_end: float
    default_priority: float
    priority_epsilon: float
    demo_priority: float


@dataclass(frozen=True)
class DemosCfg:
    episodes_per_task: int
    noise: float


@dataclass(frozen=True)
class EvalCfg:
    every_steps: int
    episodes: int
    success_thresholds: tuple[float, ...]


@dataclass(frozen=True)
class Config:
    tasks: tuple[str, ...]
    variants: tuple[str, ...]
    seeds: tuple[int, ...]
    total_steps: int
    sparse_reward: bool
    output_dir: Path
    env: EnvCfg
    sac: SacCfg
    replay: ReplayCfg
    demos: DemosCfg
    eval: EvalCfg


VARIANTS = ("uniform", "per", "demo-replay", "demo-priority")


def load(path: Path) -> Config:
    raw = yaml.safe_load(Path(path).read_text())
    return Config(
        tasks=tuple(str(t) for t in raw["tasks"]),
        variants=tuple(str(v) for v in raw["variants"]),
        seeds=tuple(int(s) for s in raw["seeds"]),
        total_steps=int(raw["total_steps"]),
        sparse_reward=bool(raw.get("sparse_reward", True)),
        output_dir=Path(raw["output_dir"]),
        env=EnvCfg(
            max_episode_steps=int(raw["env"]["max_episode_steps"]),
            camera_name=raw["env"].get("camera_name"),
        ),
        sac=SacCfg(
            gamma=float(raw["sac"]["gamma"]),
            tau=float(raw["sac"]["tau"]),
            lr_actor=float(raw["sac"]["lr_actor"]),
            lr_critic=float(raw["sac"]["lr_critic"]),
            lr_alpha=float(raw["sac"]["lr_alpha"]),
            hidden_sizes=tuple(int(x) for x in raw["sac"]["hidden_sizes"]),
            batch_size=int(raw["sac"]["batch_size"]),
            start_steps=int(raw["sac"]["start_steps"]),
            update_after=int(raw["sac"]["update_after"]),
            update_every=int(raw["sac"]["update_every"]),
            target_update_every=int(raw["sac"]["target_update_every"]),
            target_entropy=raw["sac"].get("target_entropy"),
        ),
        replay=ReplayCfg(
            capacity=int(raw["replay"]["capacity"]),
            per_alpha=float(raw["replay"]["per_alpha"]),
            per_beta_start=float(raw["replay"]["per_beta_start"]),
            per_beta_end=float(raw["replay"]["per_beta_end"]),
            default_priority=float(raw["replay"]["default_priority"]),
            priority_epsilon=float(raw["replay"]["priority_epsilon"]),
            demo_priority=float(raw["replay"]["demo_priority"]),
        ),
        demos=DemosCfg(
            episodes_per_task=int(raw["demos"]["episodes_per_task"]),
            noise=float(raw["demos"]["noise"]),
        ),
        eval=EvalCfg(
            every_steps=int(raw["eval"]["every_steps"]),
            episodes=int(raw["eval"]["episodes"]),
            success_thresholds=tuple(float(t) for t in raw["eval"]["success_thresholds"]),
        ),
    )


@dataclass(frozen=True)
class RunCfg:
    """One SAC run."""
    task: str
    variant: str
    seed: int
    output_dir: Path
    base: Config

    @property
    def total_steps(self) -> int:
        return self.base.total_steps

    @property
    def sparse_reward(self) -> bool:
        return self.base.sparse_reward

    @property
    def env(self) -> EnvCfg:
        return self.base.env

    @property
    def sac(self) -> SacCfg:
        return self.base.sac

    @property
    def replay(self) -> ReplayCfg:
        return self.base.replay

    @property
    def demos(self) -> DemosCfg:
        return self.base.demos

    @property
    def eval(self) -> EvalCfg:
        return self.base.eval

    def run_dir(self) -> Path:
        return self.output_dir / self.task / self.variant / f"seed{self.seed}"


def with_overrides(cfg: Config, **kw) -> Config:
    return replace(cfg, **kw)
