"""I/O helpers + run instrumentation: jsonl/json/yaml, env snapshot, wall budget."""

from __future__ import annotations

import contextlib
import dataclasses
import datetime
import json
import logging
import os
import platform
import socket
import sys
from collections import defaultdict
from pathlib import Path
from time import perf_counter
from typing import Any, Iterator

import yaml

_LOG_FORMAT = "%(asctime)s %(name)-22s %(levelname)-5s %(message)s"
_LOG_DATEFMT = "%H:%M:%S"


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if getattr(root, "_cs285_configured", False):
        return
    logging.basicConfig(format=_LOG_FORMAT, datefmt=_LOG_DATEFMT, level=level, force=True)
    root._cs285_configured = True  # type: ignore[attr-defined]


def append(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row, default=_default) + "\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, default=_default) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    try:
        lines = Path(path).read_text().splitlines()
    except FileNotFoundError:
        return []
    return [json.loads(ln) for ln in lines if ln.strip()]


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=_default))


def write_yaml_snapshot(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(obj, sort_keys=False))


def cfg_to_dict(cfg) -> dict:
    def conv(v):
        if dataclasses.is_dataclass(v):
            return {k: conv(getattr(v, k)) for k in v.__dataclass_fields__}
        if isinstance(v, Path):
            return str(v)
        if isinstance(v, tuple):
            return list(v)
        if isinstance(v, dict):
            return {k: conv(v2) for k, v2 in v.items()}
        return v
    return conv(cfg)


def _default(o):
    if hasattr(o, "item"):
        return o.item()
    if hasattr(o, "tolist"):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(f"not serialisable: {type(o)}")


def utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def environment_snapshot() -> dict:
    info: dict[str, Any] = {
        "captured_at_utc": utc_now_iso(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "hostname": socket.gethostname(),
        "cpu_count": os.cpu_count(),
        "env": {k: os.environ[k] for k in ("MUJOCO_GL", "CUDA_VISIBLE_DEVICES", "MODAL_TASK_ID") if k in os.environ},
    }
    try:
        import torch  # noqa: PLC0415
        info["torch"] = torch.__version__
        info["cuda_runtime"] = getattr(torch.version, "cuda", None)
        info["cudnn"] = torch.backends.cudnn.version() if torch.cuda.is_available() else None
        if torch.cuda.is_available():
            info["gpus"] = [
                {
                    "name": torch.cuda.get_device_name(i),
                    "total_mem_gb": round(torch.cuda.get_device_properties(i).total_memory / 1e9, 2),
                    "capability": torch.cuda.get_device_capability(i),
                }
                for i in range(torch.cuda.device_count())
            ]
        else:
            info["gpus"] = []
    except Exception as exc:  # noqa: BLE001
        info["torch_error"] = repr(exc)
    for mod in ("metaworld", "mujoco", "gymnasium", "numpy", "pandas", "scipy"):
        try:
            m = __import__(mod)
            info[mod.lower()] = getattr(m, "__version__", "unknown")
        except ImportError:
            info[mod.lower()] = None
    return info


class WallBudget:
    """Accumulate wall-time per category. ``with budget.measure("env_step"):``"""

    def __init__(self) -> None:
        self.totals: dict[str, float] = defaultdict(float)
        self.counts: dict[str, int] = defaultdict(int)

    @contextlib.contextmanager
    def measure(self, key: str) -> Iterator[None]:
        t0 = perf_counter()
        try:
            yield
        finally:
            self.totals[key] += perf_counter() - t0
            self.counts[key] += 1

    def add(self, key: str, seconds: float) -> None:
        self.totals[key] += float(seconds)
        self.counts[key] += 1

    def as_dict(self) -> dict[str, dict[str, float]]:
        return {
            k: {"total_s": self.totals[k], "count": self.counts[k],
                "mean_s": self.totals[k] / self.counts[k] if self.counts[k] else 0.0}
            for k in sorted(self.totals)
        }


def percentiles(values, qs=(5, 25, 50, 75, 95)) -> dict[str, float]:
    import numpy as np  # noqa: PLC0415
    arr = np.asarray(values, dtype=np.float64).ravel()
    if arr.size == 0:
        return {f"p{q}": float("nan") for q in qs} | {"mean": float("nan"), "std": float("nan"), "n": 0}
    out = {f"p{q}": float(np.percentile(arr, q)) for q in qs}
    out["mean"] = float(arr.mean())
    out["std"] = float(arr.std(ddof=0))
    out["n"] = int(arr.size)
    return out
