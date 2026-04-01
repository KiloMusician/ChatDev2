"""
agents/rl/ppo.py — PPO (Proximal Policy Optimization) for Terminal Depths
=========================================================================
Pure-numpy implementation — no PyTorch/JAX required.

Architecture:
    PolicyNetwork:  obs(20) → hidden → hidden → logits(22) → softmax
    ValueNetwork:   obs(20) → hidden → hidden → scalar

Training loop:
    1. collect_rollout():  run N steps in env, record (obs, action, reward, value, done)
    2. compute_gae():      compute advantages using Generalized Advantage Estimation
    3. update():           PPO clip update — gradient ascent on policy, MSE on value

Usage:
    env = TerminalDepthsEnv(server_url="http://localhost:8008")
    agent = PPO()
    agent.train(env, n_episodes=50, steps_per_episode=200)

Design choice — hidden layer width:
    See the TODO block below. The hidden layer size is the key architecture
    decision you need to make before training begins.
"""

from __future__ import annotations

import json
import os
import time
from typing import List, Tuple

import numpy as np

from agents.rl.environment import ACTIONS, OBS_DIM, TerminalDepthsEnv

# ─────────────────────────────────────────────────────────────────────────────
# Linear layer (numpy — no autograd)
# ─────────────────────────────────────────────────────────────────────────────

class LinearLayer:
    """Single affine layer: y = x @ W + b"""

    def __init__(self, in_dim: int, out_dim: int, seed: int = 0) -> None:
        rng = np.random.default_rng(seed)
        # Xavier / Glorot initialisation — keeps gradient scale stable
        scale = np.sqrt(2.0 / (in_dim + out_dim))
        self.W: np.ndarray = rng.normal(0, scale, (in_dim, out_dim))
        self.b: np.ndarray = np.zeros(out_dim)
        # Gradient accumulators (filled by backprop)
        self.dW: np.ndarray = np.zeros_like(self.W)
        self.db: np.ndarray = np.zeros_like(self.b)

    def forward(self, x: np.ndarray) -> np.ndarray:
        self._x = x  # cache for backward pass
        return x @ self.W + self.b

    def backward(self, grad_out: np.ndarray) -> np.ndarray:
        self.dW = self._x.T @ grad_out
        self.db = grad_out.sum(axis=0)
        return grad_out @ self.W.T

    def step(self, lr: float) -> None:
        self.W += lr * self.dW
        self.b += lr * self.db
        self.dW[:] = 0
        self.db[:] = 0


# ─────────────────────────────────────────────────────────────────────────────
# Policy network  (obs → action probabilities)
# ─────────────────────────────────────────────────────────────────────────────

class PolicyNetwork:
    """
    Maps a game observation vector to a probability distribution over actions.

    Architecture:  Linear(OBS_DIM→H) → ReLU → Linear(H→H) → ReLU → Linear(H→n_actions) → Softmax
    Hidden width defaults to 128 — good balance for 20-dim obs / 22 actions.
    """

    N_ACTIONS = len(ACTIONS)

    def __init__(self, hidden_size: int = 128, seed: int = 0) -> None:
        self.hidden_size = hidden_size
        self.l1 = LinearLayer(OBS_DIM,     hidden_size, seed=seed)
        self.l2 = LinearLayer(hidden_size, hidden_size, seed=seed + 1)
        self.l3 = LinearLayer(hidden_size, self.N_ACTIONS, seed=seed + 2)

    def _forward(self, x: np.ndarray) -> np.ndarray:
        h1 = np.maximum(0, self.l1.forward(x))       # ReLU after first hidden layer
        h2 = np.maximum(0, self.l2.forward(h1))      # ReLU after second hidden layer
        logits = self.l3.forward(h2)                  # final linear projection → logits
        # Numerically stable softmax: subtract max before exp
        logits = logits - logits.max(axis=-1, keepdims=True)
        exp_logits = np.exp(logits)
        probs = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)
        return probs

    def __call__(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.float32)
        if x.ndim == 1:
            return self._forward(x[np.newaxis, :])[0]
        return self._forward(x)

    def sample_action(self, obs: np.ndarray) -> Tuple[int, float]:
        """Sample an action; return (action_index, log_prob)."""
        probs = self(obs)
        probs = np.clip(probs, 1e-8, 1.0)
        probs /= probs.sum()
        action = int(np.random.choice(self.N_ACTIONS, p=probs))
        log_prob = float(np.log(probs[action]))
        return action, log_prob

    def log_prob(self, obs: np.ndarray, actions: np.ndarray) -> np.ndarray:
        """Batch log-probability of given actions under current policy."""
        probs = self(obs)
        probs = np.clip(probs, 1e-8, 1.0)
        idx = np.arange(len(actions))
        return np.log(probs[idx, actions])

    def save(self, path: str) -> None:
        np.savez(path, l1W=self.l1.W, l1b=self.l1.b,
                 l2W=self.l2.W, l2b=self.l2.b,
                 l3W=self.l3.W, l3b=self.l3.b)

    def load(self, path: str) -> None:
        d = np.load(path + ".npz")
        self.l1.W, self.l1.b = d["l1W"], d["l1b"]
        self.l2.W, self.l2.b = d["l2W"], d["l2b"]
        self.l3.W, self.l3.b = d["l3W"], d["l3b"]


# ─────────────────────────────────────────────────────────────────────────────
# Value network  (obs → expected return)
# ─────────────────────────────────────────────────────────────────────────────

class ValueNetwork:
    """
    Maps a game observation to a scalar value estimate (expected cumulative reward).

    Architecture:  Linear(OBS_DIM→H) → ReLU → Linear(H→H) → ReLU → Linear(H→1)

    Architecture:  Linear(OBS_DIM→H) → ReLU → Linear(H→H) → ReLU → Linear(H→1)
    Outputs a raw scalar (no activation) — used directly as V(s) in GAE.
    """

    def __init__(self, hidden_size: int = 128, seed: int = 42) -> None:
        self.l1 = LinearLayer(OBS_DIM,     hidden_size, seed=seed)
        self.l2 = LinearLayer(hidden_size, hidden_size, seed=seed + 1)
        self.l3 = LinearLayer(hidden_size, 1,           seed=seed + 2)

    def _forward(self, x: np.ndarray) -> np.ndarray:
        h1 = np.maximum(0, self.l1.forward(x))       # ReLU after first hidden layer
        h2 = np.maximum(0, self.l2.forward(h1))      # ReLU after second hidden layer
        value = self.l3.forward(h2)                   # linear projection → scalar (shape: batch×1)
        return value

    def __call__(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.float32)
        if x.ndim == 1:
            return self._forward(x[np.newaxis, :])[0, 0]
        return self._forward(x)[:, 0]


# ─────────────────────────────────────────────────────────────────────────────
# PPO trainer
# ─────────────────────────────────────────────────────────────────────────────

class PPO:
    """
    Proximal Policy Optimization (numpy, no autograd).

    Key hyperparameters:
        gamma (γ):    discount factor — how much future rewards count (0.99 = long horizon)
        lam (λ):      GAE smoothing — trades variance vs bias in advantage estimates
        clip_eps (ε): PPO clip ratio — limits how far policy updates in one step
        lr_pi:        policy learning rate
        lr_v:         value learning rate
    """

    def __init__(
        self,
        hidden_size: int = 128,
        gamma: float = 0.99,
        lam: float = 0.95,
        clip_eps: float = 0.2,
        lr_pi: float = 3e-4,
        lr_v: float = 1e-3,
        n_epochs: int = 4,
        seed: int = 0,
    ) -> None:
        self.policy = PolicyNetwork(hidden_size, seed=seed)
        self.value  = ValueNetwork(hidden_size, seed=seed + 100)
        self.gamma    = gamma
        self.lam      = lam
        self.clip_eps = clip_eps
        self.lr_pi    = lr_pi
        self.lr_v     = lr_v
        self.n_epochs = n_epochs
        self._episode_rewards: list[float] = []

    # ── Rollout collection ────────────────────────────────────────────────────

    def collect_rollout(
        self,
        env: TerminalDepthsEnv,
        n_steps: int = 256,
    ) -> dict:
        """Run n_steps in env; return dict of arrays for PPO update."""
        obs_buf:      list[np.ndarray] = []
        action_buf:   list[int]        = []
        logprob_buf:  list[float]      = []
        reward_buf:   list[float]      = []
        value_buf:    list[float]      = []
        done_buf:     list[float]      = []

        obs, _ = env.reset()
        for _ in range(n_steps):
            obs_arr = np.array(obs, dtype=np.float32)
            action, log_prob = self.policy.sample_action(obs_arr)
            value = float(self.value(obs_arr))

            next_obs, reward, done, truncated, _ = env.step(action)

            obs_buf.append(obs_arr)
            action_buf.append(action)
            logprob_buf.append(log_prob)
            reward_buf.append(float(reward))
            value_buf.append(value)
            done_buf.append(float(done or truncated))

            obs = next_obs
            if done or truncated:
                obs, _ = env.reset()

        # Bootstrap value for last state
        last_value = float(self.value(np.array(obs, dtype=np.float32)))

        return {
            "obs":      np.array(obs_buf,     dtype=np.float32),
            "actions":  np.array(action_buf,  dtype=np.int32),
            "logprobs": np.array(logprob_buf, dtype=np.float32),
            "rewards":  np.array(reward_buf,  dtype=np.float32),
            "values":   np.array(value_buf,   dtype=np.float32),
            "dones":    np.array(done_buf,    dtype=np.float32),
            "last_value": last_value,
        }

    # ── Generalized Advantage Estimation ─────────────────────────────────────

    def compute_gae(
        self,
        rewards: np.ndarray,
        values: np.ndarray,
        dones: np.ndarray,
        last_value: float,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute GAE advantages and discounted returns.

        GAE(γ, λ) smoothly interpolates between:
            λ=0  →  TD(0) residuals  (low variance, high bias)
            λ=1  →  Monte-Carlo      (high variance, low bias)

        Returns:
            advantages : shape (T,) — used in policy loss
            returns    : shape (T,) — used in value loss (target)
        """
        T = len(rewards)
        advantages = np.zeros(T, dtype=np.float32)
        last_gae   = 0.0

        # Bootstrap next-step values
        next_values = np.append(values[1:], last_value)

        for t in reversed(range(T)):
            nonterminal  = 1.0 - dones[t]
            delta        = rewards[t] + self.gamma * next_values[t] * nonterminal - values[t]
            last_gae     = delta + self.gamma * self.lam * nonterminal * last_gae
            advantages[t] = last_gae

        returns = advantages + values
        return advantages, returns

    # ── PPO update step ───────────────────────────────────────────────────────

    def update(self, batch: dict) -> dict:
        """Run n_epochs PPO clip updates on one rollout batch."""
        obs       = batch["obs"]
        actions   = batch["actions"]
        old_lp    = batch["logprobs"]
        advantages, returns = self.compute_gae(
            batch["rewards"], batch["values"],
            batch["dones"],   batch["last_value"],
        )

        # Normalize advantages (reduces variance)
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        pi_losses: list[float] = []
        v_losses:  list[float] = []

        for _ in range(self.n_epochs):
            # ── Policy loss (PPO clip) ────────────────────────────────────
            new_lp  = self.policy.log_prob(obs, actions)
            ratio   = np.exp(new_lp - old_lp)
            clipped = np.clip(ratio, 1 - self.clip_eps, 1 + self.clip_eps)
            pi_loss = -np.minimum(ratio * advantages, clipped * advantages).mean()
            pi_losses.append(float(pi_loss))

            # ── Manual gradient step on policy via finite differences ─────
            # (Full backprop through numpy layers is complex; we approximate
            #  with a REINFORCE-style gradient that PPO bounds via the clip.)
            eps_fd = 1e-4
            for layer in (self.policy.l1, self.policy.l2, self.policy.l3):
                for param, grad_attr in ((layer.W, "dW"), (layer.b, "db")):
                    grad = np.zeros_like(param)
                    it = np.nditer(param, flags=["multi_index"])
                    while not it.finished:
                        idx = it.multi_index
                        orig = param[idx]
                        param[idx] = orig + eps_fd
                        new_lp_p = self.policy.log_prob(obs, actions)
                        ratio_p  = np.exp(new_lp_p - old_lp)
                        clipped_p = np.clip(ratio_p, 1-self.clip_eps, 1+self.clip_eps)
                        loss_p = -np.minimum(ratio_p*advantages, clipped_p*advantages).mean()
                        param[idx] = orig - eps_fd
                        new_lp_m = self.policy.log_prob(obs, actions)
                        ratio_m  = np.exp(new_lp_m - old_lp)
                        clipped_m = np.clip(ratio_m, 1-self.clip_eps, 1+self.clip_eps)
                        loss_m = -np.minimum(ratio_m*advantages, clipped_m*advantages).mean()
                        param[idx] = orig
                        grad[idx] = (loss_p - loss_m) / (2 * eps_fd)
                        it.iternext()
                    setattr(layer, grad_attr, -grad)  # ascent → negate loss gradient
                    layer.step(self.lr_pi)

            # ── Value loss (MSE) ──────────────────────────────────────────
            v_pred = self.value(obs)
            v_loss = ((v_pred - returns) ** 2).mean()
            v_losses.append(float(v_loss))
            # Gradient step on value network (also finite differences)
            for layer in (self.value.l1, self.value.l2, self.value.l3):
                for param, grad_attr in ((layer.W, "dW"), (layer.b, "db")):
                    grad = np.zeros_like(param)
                    it = np.nditer(param, flags=["multi_index"])
                    while not it.finished:
                        idx = it.multi_index
                        orig = param[idx]
                        param[idx] = orig + eps_fd
                        loss_p = ((self.value(obs) - returns) ** 2).mean()
                        param[idx] = orig - eps_fd
                        loss_m = ((self.value(obs) - returns) ** 2).mean()
                        param[idx] = orig
                        grad[idx] = (loss_p - loss_m) / (2 * eps_fd)
                        it.iternext()
                    setattr(layer, grad_attr, grad)
                    layer.step(self.lr_v)

        return {
            "pi_loss": np.mean(pi_losses),
            "v_loss":  np.mean(v_losses),
            "mean_reward": float(batch["rewards"].mean()),
            "mean_advantage": float(advantages.mean()),
        }

    # ── Training loop ─────────────────────────────────────────────────────────

    def train(
        self,
        env: TerminalDepthsEnv,
        n_episodes: int = 50,
        steps_per_episode: int = 128,
        save_dir: str = "state/rl",
        verbose: bool = True,
    ) -> list[dict]:
        """Main training loop. Returns per-episode stats."""
        os.makedirs(save_dir, exist_ok=True)
        history: list[dict] = []

        for ep in range(n_episodes):
            t0 = time.time()
            batch = self.collect_rollout(env, steps_per_episode)
            stats = self.update(batch)
            stats["episode"]     = ep + 1
            stats["elapsed"]     = round(time.time() - t0, 2)
            stats["total_reward"] = float(batch["rewards"].sum())
            history.append(stats)
            self._episode_rewards.append(stats["total_reward"])

            if verbose:
                print(
                    f"[PPO ep {ep+1:3d}/{n_episodes}] "
                    f"reward={stats['total_reward']:+7.1f}  "
                    f"pi_loss={stats['pi_loss']:.4f}  "
                    f"v_loss={stats['v_loss']:.4f}  "
                    f"({stats['elapsed']}s)"
                )

            # Save checkpoint every 10 episodes
            if (ep + 1) % 10 == 0:
                self.policy.save(f"{save_dir}/policy_ep{ep+1}")
                with open(f"{save_dir}/history.json", "w") as f:
                    json.dump(history, f, indent=2)

        return history

    def status(self) -> dict:
        """Return current training status (for /api/agent/rl/status)."""
        return {
            "episodes_trained": len(self._episode_rewards),
            "last_reward": self._episode_rewards[-1] if self._episode_rewards else None,
            "avg_reward_last10": (
                float(np.mean(self._episode_rewards[-10:]))
                if len(self._episode_rewards) >= 10 else None
            ),
            "policy_hidden_size": self.policy.hidden_size,
            "n_actions": PolicyNetwork.N_ACTIONS,
            "obs_dim": OBS_DIM,
        }


# ─────────────────────────────────────────────────────────────────────────────
# PPOAgent — convenience wrapper with obs_dim/action_dim interface
# ─────────────────────────────────────────────────────────────────────────────

class PPOAgent:
    """Thin wrapper around PPO using the obs_dim/action_dim interface.

    Used by agents/player.py and the RL status endpoint so callers don't need
    to know the internal PPO constructor signature.
    """

    def __init__(
        self,
        obs_dim: int = OBS_DIM,
        action_dim: int = len(ACTIONS),
        hidden_size: int = 128,
        seed: int = 0,
    ) -> None:
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self._ppo = PPO(hidden_size=hidden_size, seed=seed)

    def select_action(self, obs: "np.ndarray") -> "Tuple[int, float]":
        return self._ppo.policy.sample_action(
            np.asarray(obs, dtype=np.float32)
        )

    def get_value(self, obs: "np.ndarray") -> float:
        return float(self._ppo.value(np.asarray(obs, dtype=np.float32)))

    def status(self) -> dict:
        return self._ppo.status()


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "status":
        agent = PPO()
        print(json.dumps(agent.status(), indent=2))
        sys.exit(0)

    print("Terminal Depths PPO Agent")
    print("─" * 40)
    print("Before training, implement PolicyNetwork._forward and ValueNetwork._forward")
    print("See the TODO block in ppo.py for guidance.")
    print()
    print("Then run:")
    print("  env = TerminalDepthsEnv(server_url='http://localhost:8008')")
    print("  agent = PPO(hidden_size=128)  # or 64, 256")
    print("  agent.train(env, n_episodes=10, steps_per_episode=64)")
