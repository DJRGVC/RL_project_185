"""Actor (squashed Gaussian) + twin critic for SAC."""

from __future__ import annotations

import math

import torch
from torch import nn

LOG_STD_MIN = -20.0
LOG_STD_MAX = 2.0


def _mlp(in_dim: int, out_dim: int, hidden: tuple[int, ...]) -> nn.Sequential:
    layers: list[nn.Module] = []
    last = in_dim
    for h in hidden:
        layers.append(nn.Linear(last, h))
        layers.append(nn.ReLU(inplace=True))
        last = h
    layers.append(nn.Linear(last, out_dim))
    return nn.Sequential(*layers)


class Actor(nn.Module):
    def __init__(self, obs_dim, act_dim, hidden, act_low, act_high):
        super().__init__()
        self.body = _mlp(obs_dim, 2 * act_dim, hidden)
        self.act_dim = act_dim
        self.register_buffer("act_scale", (act_high - act_low) / 2.0)
        self.register_buffer("act_bias", (act_high + act_low) / 2.0)

    def forward(self, obs):
        h = self.body(obs)
        mean, log_std = h.split(self.act_dim, dim=-1)
        return mean, log_std.clamp(LOG_STD_MIN, LOG_STD_MAX)

    def sample(self, obs):
        mean, log_std = self.forward(obs)
        std = log_std.exp()
        eps = torch.randn_like(mean)
        z = mean + eps * std
        a_tanh = torch.tanh(z)
        action = a_tanh * self.act_scale + self.act_bias
        log_prob = -0.5 * (((z - mean) / std).pow(2) + 2 * log_std + math.log(2 * math.pi))
        log_prob = log_prob - torch.log(1 - a_tanh.pow(2) + 1e-6) - torch.log(self.act_scale + 1e-12)
        return action, log_prob.sum(dim=-1, keepdim=True)

    @torch.no_grad()
    def deterministic(self, obs):
        mean, _ = self.forward(obs)
        return torch.tanh(mean) * self.act_scale + self.act_bias


class Critic(nn.Module):
    """Twin Q networks."""

    def __init__(self, obs_dim, act_dim, hidden):
        super().__init__()
        self.q1 = _mlp(obs_dim + act_dim, 1, hidden)
        self.q2 = _mlp(obs_dim + act_dim, 1, hidden)

    def forward(self, obs, action):
        x = torch.cat([obs, action], dim=-1)
        return self.q1(x), self.q2(x)
