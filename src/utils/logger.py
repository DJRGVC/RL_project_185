"""
Training logger — writes to TensorBoard and optionally W&B.
"""
import os
import time
import logging
from typing import Dict, Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class TrainingLogger:
    def __init__(
        self,
        log_dir: str,
        run_name: str,
        use_tensorboard: bool = True,
        use_wandb: bool = False,
        wandb_project: Optional[str] = None,
        wandb_entity: Optional[str] = None,
        config: Optional[dict] = None,
    ):
        self.log_dir = os.path.join(log_dir, run_name)
        os.makedirs(self.log_dir, exist_ok=True)
        self._start_time = time.time()

        # ── TensorBoard ──────────────────────────────────────────────────────
        self._tb_writer = None
        if use_tensorboard:
            from torch.utils.tensorboard import SummaryWriter
            self._tb_writer = SummaryWriter(log_dir=self.log_dir)

        # ── W&B ──────────────────────────────────────────────────────────────
        self._wandb_run = None
        self._vlm_table = None
        if use_wandb:
            try:
                import wandb
                # Derive group from run_name prefix (method name) for W&B dashboard grouping
                method = run_name.split("_fetch")[0] if "_fetch" in run_name else run_name.split("_seed")[0]
                self._wandb_run = wandb.init(
                    project=wandb_project or "RL_project",
                    entity=wandb_entity or None,
                    name=run_name,
                    group=method,
                    config=config or {},
                    resume="allow",
                )
                # All metrics share the same x-axis in the W&B dashboard
                wandb.define_metric("global_step")
                wandb.define_metric("*", step_metric="global_step")

                # VLM call table — rows accumulated during training, uploaded at close()
                self._vlm_table = wandb.Table(
                    columns=["global_step", "episode", "failure_timestep",
                             "episode_length", "confidence", "reasoning", "keyframe"]
                )
            except Exception as e:
                logger.warning(f"W&B init failed, continuing without W&B: {e}")
                self._wandb_run = None

        # ── file logging ─────────────────────────────────────────────────────
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(os.path.join(self.log_dir, "train.log")),
            ],
        )

    # ── scalar logging ────────────────────────────────────────────────────────

    def log(self, metrics: Dict[str, Any], step: int, prefix: str = ""):
        tag = lambda k: f"{prefix}/{k}" if prefix else k
        wandb_payload = {"global_step": step}
        for k, v in metrics.items():
            if isinstance(v, (int, float, np.floating, np.integer)):
                t = tag(k)
                if self._tb_writer:
                    self._tb_writer.add_scalar(t, float(v), step)
                wandb_payload[t] = float(v)
        if self._wandb_run and len(wandb_payload) > 1:
            self._wandb_run.log(wandb_payload)

    # ── media logging ─────────────────────────────────────────────────────────

    def log_image(self, key: str, frame: np.ndarray, step: int, caption: str = ""):
        """Log a single RGB numpy frame as a W&B Image."""
        if self._wandb_run is None:
            return
        import wandb
        self._wandb_run.log({key: wandb.Image(frame, caption=caption),
                             "global_step": step})

    # ── VLM table logging ────────────────────────────────────────────────────

    def log_vlm_call(
        self,
        step: int,
        episode: int,
        failure_timestep: int,
        episode_length: int,
        confidence: float,
        reasoning: str,
        failure_frame: Optional[np.ndarray] = None,
    ):
        """Accumulate one VLM call row and log real-time scalars."""
        if self._wandb_run is None:
            return
        import wandb
        img = wandb.Image(failure_frame) if failure_frame is not None else None
        if self._vlm_table is not None:
            self._vlm_table.add_data(
                step, episode, failure_timestep, episode_length,
                confidence, reasoning, img,
            )
        # Real-time scalar charts
        self._wandb_run.log({
            "vlm/failure_timestep": failure_timestep,
            "vlm/confidence": confidence,
            "vlm/failure_pct": failure_timestep / max(episode_length, 1),
            "global_step": step,
        })

    # ── checkpoint artifact ───────────────────────────────────────────────────

    def log_checkpoint_artifact(self, checkpoint_dir: str, name: str, step: int):
        """Upload a checkpoint directory as a W&B model artifact."""
        if self._wandb_run is None:
            return
        import wandb
        artifact = wandb.Artifact(name=name, type="model", metadata={"step": step})
        artifact.add_dir(checkpoint_dir)
        self._wandb_run.log_artifact(artifact)

    # ── misc ──────────────────────────────────────────────────────────────────

    def log_hparams(self, hparams: dict, metrics: dict):
        if self._tb_writer:
            self._tb_writer.add_hparams(hparams, metrics)

    def print_summary(self, step: int, metrics: Dict[str, Any]):
        elapsed = time.time() - self._start_time
        parts = [f"step={step}", f"time={elapsed:.0f}s"]
        for k, v in metrics.items():
            if isinstance(v, float):
                parts.append(f"{k}={v:.4f}")
            else:
                parts.append(f"{k}={v}")
        logger.info("  |  ".join(parts))

    def close(self):
        if self._tb_writer:
            self._tb_writer.close()
        if self._wandb_run:
            import wandb
            # Upload accumulated VLM table as artifact + inline summary panel
            if self._vlm_table is not None and len(self._vlm_table.data) > 0:
                artifact = wandb.Artifact("vlm_calls", type="dataset")
                artifact.add(self._vlm_table, "vlm_calls")
                self._wandb_run.log_artifact(artifact)
                self._wandb_run.log({"vlm/call_table": self._vlm_table})
            self._wandb_run.finish()
