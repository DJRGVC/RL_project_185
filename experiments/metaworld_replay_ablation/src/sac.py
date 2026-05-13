"""SAC: actor + twin critic + automatic temperature tuning."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from src.config import SacCfg
from src.networks import Actor, Critic
from src.replay import Batch


@dataclass
class UpdateStats:
    q_loss: float
    pi_loss: float
    alpha_loss: float
    alpha: float
    td_errors: np.ndarray
    q1_mean: float
    q2_mean: float
    target_q_mean: float
    log_prob_mean: float
    log_prob_std: float
    action_abs_mean: float
    action_saturation: float
    critic_grad_norm: float
    actor_grad_norm: float
    is_weight_mean: float
    is_weight_max: float


class Agent:
    def __init__(self, obs_dim, act_dim, act_low, act_high, cfg: SacCfg, device):
        self.cfg = cfg
        self.device = device
        self.act_dim = act_dim
        act_low_t = torch.as_tensor(act_low, dtype=torch.float32, device=device)
        act_high_t = torch.as_tensor(act_high, dtype=torch.float32, device=device)

        self.actor = Actor(obs_dim, act_dim, cfg.hidden_sizes, act_low_t, act_high_t).to(device)
        self.critic = Critic(obs_dim, act_dim, cfg.hidden_sizes).to(device)
        self.critic_target = Critic(obs_dim, act_dim, cfg.hidden_sizes).to(device)
        self.critic_target.load_state_dict(self.critic.state_dict())
        for p in self.critic_target.parameters():
            p.requires_grad_(False)

        self.actor_opt = torch.optim.Adam(self.actor.parameters(), lr=cfg.lr_actor)
        self.critic_opt = torch.optim.Adam(self.critic.parameters(), lr=cfg.lr_critic)

        target_entropy = cfg.target_entropy if cfg.target_entropy is not None else -float(act_dim)
        self.target_entropy = float(target_entropy)
        self.log_alpha = torch.tensor(0.0, requires_grad=True, device=device)
        self.alpha_opt = torch.optim.Adam([self.log_alpha], lr=cfg.lr_alpha)

    @property
    def alpha(self) -> torch.Tensor:
        return self.log_alpha.exp()

    @torch.no_grad()
    def act(self, obs: np.ndarray, deterministic: bool = False) -> np.ndarray:
        obs_t = torch.as_tensor(obs, dtype=torch.float32, device=self.device).unsqueeze(0)
        a = self.actor.deterministic(obs_t) if deterministic else self.actor.sample(obs_t)[0]
        return a.squeeze(0).cpu().numpy()

    def update(self, batch: Batch) -> UpdateStats:
        device = self.device
        obs = torch.as_tensor(batch.obs, dtype=torch.float32, device=device)
        action = torch.as_tensor(batch.action, dtype=torch.float32, device=device)
        reward = torch.as_tensor(batch.reward, dtype=torch.float32, device=device)
        next_obs = torch.as_tensor(batch.next_obs, dtype=torch.float32, device=device)
        done = torch.as_tensor(batch.done, dtype=torch.float32, device=device)
        weights = torch.as_tensor(batch.weights, dtype=torch.float32, device=device).unsqueeze(-1)

        with torch.no_grad():
            next_a, next_logp = self.actor.sample(next_obs)
            q1_t, q2_t = self.critic_target(next_obs, next_a)
            q_t = torch.min(q1_t, q2_t) - self.alpha * next_logp
            target = reward + (1 - done) * self.cfg.gamma * q_t

        q1, q2 = self.critic(obs, action)
        td1 = q1 - target
        td2 = q2 - target
        q_loss = (weights * (td1.pow(2) + td2.pow(2))).mean()
        self.critic_opt.zero_grad(set_to_none=True)
        q_loss.backward()
        critic_grad_norm = _grad_norm(self.critic.parameters())
        self.critic_opt.step()

        new_a, logp = self.actor.sample(obs)
        q1_pi, q2_pi = self.critic(obs, new_a)
        q_pi = torch.min(q1_pi, q2_pi)
        pi_loss = (self.alpha.detach() * logp - q_pi).mean()
        self.actor_opt.zero_grad(set_to_none=True)
        pi_loss.backward()
        actor_grad_norm = _grad_norm(self.actor.parameters())
        self.actor_opt.step()

        alpha_loss = -(self.log_alpha * (logp.detach() + self.target_entropy)).mean()
        self.alpha_opt.zero_grad(set_to_none=True)
        alpha_loss.backward()
        self.alpha_opt.step()

        with torch.no_grad():
            for p, p_t in zip(self.critic.parameters(), self.critic_target.parameters()):
                p_t.data.mul_(1 - self.cfg.tau).add_(p.data, alpha=self.cfg.tau)

        td_errors = 0.5 * (td1.detach() + td2.detach()).squeeze(-1).cpu().numpy()
        scaled = (new_a.detach() - self.actor.act_bias) / torch.clamp(self.actor.act_scale, min=1e-8)
        saturation = (scaled.abs() > 0.99).float().mean().item()
        return UpdateStats(
            q_loss=float(q_loss.item()),
            pi_loss=float(pi_loss.item()),
            alpha_loss=float(alpha_loss.item()),
            alpha=float(self.alpha.item()),
            td_errors=td_errors,
            q1_mean=float(q1.detach().mean().item()),
            q2_mean=float(q2.detach().mean().item()),
            target_q_mean=float(target.detach().mean().item()),
            log_prob_mean=float(logp.detach().mean().item()),
            log_prob_std=float(logp.detach().std().item()),
            action_abs_mean=float(new_a.detach().abs().mean().item()),
            action_saturation=float(saturation),
            critic_grad_norm=float(critic_grad_norm),
            actor_grad_norm=float(actor_grad_norm),
            is_weight_mean=float(weights.detach().mean().item()),
            is_weight_max=float(weights.detach().max().item()),
        )


def _grad_norm(params) -> float:
    total = 0.0
    for p in params:
        if p.grad is None:
            continue
        total += p.grad.detach().data.norm(2).item() ** 2
    return total ** 0.5
