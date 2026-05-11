"""
Soft Actor-Critic (SAC) with automatic entropy tuning.
Haarnoja et al. 2018 / 2019. Supports both uniform and importance-weighted updates.
"""
import os
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Normal

LOG_SIG_MAX = 2
LOG_SIG_MIN = -5


# ─────────────────────────────────────────────────────────────── networks ──

class MLP(nn.Module):
    def __init__(self, input_dim: int, output_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.net(x)


class GaussianPolicy(nn.Module):
    def __init__(self, obs_dim: int, action_dim: int, hidden_dim: int = 256,
                 action_scale: float = 1.0):
        super().__init__()
        self.trunk = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
        )
        self.mean_head = nn.Linear(hidden_dim, action_dim)
        self.log_std_head = nn.Linear(hidden_dim, action_dim)
        self.action_scale = action_scale

    def forward(self, obs):
        h = self.trunk(obs)
        mean = self.mean_head(h)
        log_std = self.log_std_head(h).clamp(LOG_SIG_MIN, LOG_SIG_MAX)
        return mean, log_std

    def sample(self, obs):
        mean, log_std = self(obs)
        std = log_std.exp()
        dist = Normal(mean, std)
        x_t = dist.rsample()
        y_t = torch.tanh(x_t)
        action = y_t * self.action_scale
        # Numerically stable log_prob of tanh-squashed Gaussian
        log_prob = dist.log_prob(x_t) - torch.log(
            self.action_scale * (1 - y_t.pow(2)) + 1e-6
        )
        log_prob = log_prob.sum(dim=-1, keepdim=True)
        mean_action = torch.tanh(mean) * self.action_scale
        return action, log_prob, mean_action


class TwinQNetwork(nn.Module):
    def __init__(self, obs_dim: int, action_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.q1 = MLP(obs_dim + action_dim, 1, hidden_dim)
        self.q2 = MLP(obs_dim + action_dim, 1, hidden_dim)

    def forward(self, obs, action):
        x = torch.cat([obs, action], dim=-1)
        return self.q1(x), self.q2(x)

    def q_min(self, obs, action):
        q1, q2 = self(obs, action)
        return torch.min(q1, q2)


# ─────────────────────────────────────────────────────────────────── SAC ──

class SAC:
    def __init__(
        self,
        obs_dim: int,
        action_dim: int,
        action_scale: float = 1.0,
        hidden_dim: int = 256,
        lr_actor: float = 3e-4,
        lr_critic: float = 3e-4,
        lr_alpha: float = 3e-4,
        gamma: float = 0.98,
        tau: float = 0.005,
        init_temperature: float = 0.2,
        auto_entropy_tuning: bool = True,
        device: str = "cpu",
    ):
        self.gamma = gamma
        self.tau = tau
        self.auto_entropy_tuning = auto_entropy_tuning
        self.device = torch.device(device)

        self.actor = GaussianPolicy(obs_dim, action_dim, hidden_dim, action_scale).to(self.device)
        self.critic = TwinQNetwork(obs_dim, action_dim, hidden_dim).to(self.device)
        self.critic_target = TwinQNetwork(obs_dim, action_dim, hidden_dim).to(self.device)
        self.critic_target.load_state_dict(self.critic.state_dict())
        for p in self.critic_target.parameters():
            p.requires_grad = False

        self.actor_optim = torch.optim.Adam(self.actor.parameters(), lr=lr_actor)
        self.critic_optim = torch.optim.Adam(self.critic.parameters(), lr=lr_critic)

        if auto_entropy_tuning:
            self.target_entropy = -float(action_dim)
            self.log_alpha = torch.tensor(math.log(init_temperature),
                                          requires_grad=True, device=self.device)
            self.alpha_optim = torch.optim.Adam([self.log_alpha], lr=lr_alpha)
            self.alpha = self.log_alpha.exp().item()
        else:
            self.alpha = init_temperature

        self.total_updates = 0

    # ── public interface ──────────────────────────────────────────────────

    @torch.no_grad()
    def select_action(self, obs: np.ndarray, deterministic: bool = False) -> np.ndarray:
        obs_t = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
        if deterministic:
            _, _, action = self.actor.sample(obs_t)
        else:
            action, _, _ = self.actor.sample(obs_t)
        return action.cpu().numpy().squeeze(0)

    def update(self, batch: dict) -> dict:
        obs      = torch.FloatTensor(batch["obs"]).to(self.device)
        action   = torch.FloatTensor(batch["action"]).to(self.device)
        reward   = torch.FloatTensor(batch["reward"]).unsqueeze(-1).to(self.device)
        next_obs = torch.FloatTensor(batch["next_obs"]).to(self.device)
        done     = torch.FloatTensor(batch["done"]).unsqueeze(-1).to(self.device)
        weights  = torch.FloatTensor(batch.get("weights", np.ones(len(obs)))).unsqueeze(-1).to(self.device)

        # ── critic update ──
        with torch.no_grad():
            next_action, next_log_pi, _ = self.actor.sample(next_obs)
            q1_next, q2_next = self.critic_target(next_obs, next_action)
            q_next = torch.min(q1_next, q2_next) - self.alpha * next_log_pi
            q_target = reward + (1.0 - done) * self.gamma * q_next

        q1, q2 = self.critic(obs, action)
        td_errors = 0.5 * (q1 - q_target).abs() + 0.5 * (q2 - q_target).abs()
        critic_loss = (weights * (F.mse_loss(q1, q_target, reduction="none") +
                                  F.mse_loss(q2, q_target, reduction="none"))).mean()

        self.critic_optim.zero_grad()
        critic_loss.backward()
        nn.utils.clip_grad_norm_(self.critic.parameters(), max_norm=1.0)
        self.critic_optim.step()

        # ── actor update ──
        pi, log_pi, _ = self.actor.sample(obs)
        q_pi = self.critic.q_min(obs, pi)
        actor_loss = (self.alpha * log_pi - q_pi).mean()

        self.actor_optim.zero_grad()
        actor_loss.backward()
        nn.utils.clip_grad_norm_(self.actor.parameters(), max_norm=1.0)
        self.actor_optim.step()

        # ── alpha update ──
        alpha_loss = torch.tensor(0.0)
        if self.auto_entropy_tuning:
            alpha_loss = -(self.log_alpha * (log_pi + self.target_entropy).detach()).mean()
            self.alpha_optim.zero_grad()
            alpha_loss.backward()
            self.alpha_optim.step()
            self.alpha = self.log_alpha.exp().item()

        # ── soft target update ──
        with torch.no_grad():
            for p, p_t in zip(self.critic.parameters(), self.critic_target.parameters()):
                p_t.data.lerp_(p.data, self.tau)

        self.total_updates += 1
        return {
            "critic_loss": critic_loss.item(),
            "actor_loss": actor_loss.item(),
            "alpha_loss": alpha_loss.item(),
            "alpha": self.alpha,
            "td_errors": td_errors.detach().cpu().numpy().squeeze(-1),
        }

    # ── persistence ──────────────────────────────────────────────────────

    def save(self, path: str):
        os.makedirs(path, exist_ok=True)
        torch.save({
            "actor": self.actor.state_dict(),
            "critic": self.critic.state_dict(),
            "critic_target": self.critic_target.state_dict(),
            "log_alpha": self.log_alpha if self.auto_entropy_tuning else None,
        }, os.path.join(path, "sac.pt"))

    def load(self, path: str):
        ckpt = torch.load(os.path.join(path, "sac.pt"), map_location=self.device)
        self.actor.load_state_dict(ckpt["actor"])
        self.critic.load_state_dict(ckpt["critic"])
        self.critic_target.load_state_dict(ckpt["critic_target"])
        if self.auto_entropy_tuning and ckpt["log_alpha"] is not None:
            self.log_alpha.data.copy_(ckpt["log_alpha"].data)
            self.alpha = self.log_alpha.exp().item()
