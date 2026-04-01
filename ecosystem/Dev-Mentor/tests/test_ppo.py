"""Tests for agents/rl/ppo.py — PPO neural network components."""
import math

import numpy as np

from agents.rl.ppo import (
    ACTIONS,
    OBS_DIM,
    LinearLayer,
    PolicyNetwork,
    ValueNetwork,
    PPO,
    PPOAgent,
)

_rng = np.random.default_rng(42)


# ── LinearLayer ──────────────────────────────────────────────────────────────

class TestLinearLayer:
    def test_forward_output_shape(self):
        layer = LinearLayer(8, 4, seed=0)
        x = np.ones((8,), dtype=np.float32)
        assert layer.forward(x).shape == (4,)

    def test_forward_batched(self):
        layer = LinearLayer(8, 4, seed=0)
        x = np.ones((16, 8), dtype=np.float32)
        assert layer.forward(x).shape == (16, 4)

    def test_backward_gradient_shapes(self):
        layer = LinearLayer(4, 3, seed=1)
        # backward requires 2D (batched) input
        x = _rng.random((1, 4)).astype(np.float32)
        layer.forward(x)
        dx = layer.backward(np.ones((1, 3), dtype=np.float32))
        assert dx.shape == x.shape
        assert layer.dW.shape == layer.W.shape
        assert layer.db.shape == layer.b.shape

    def test_step_zeroes_gradients(self):
        layer = LinearLayer(4, 3, seed=2)
        # backward requires 2D (batched) input
        x = _rng.random((1, 4)).astype(np.float32)
        layer.forward(x)
        layer.backward(np.ones((1, 3), dtype=np.float32))
        layer.step(lr=0.01)
        assert np.allclose(layer.dW, 0)
        assert np.allclose(layer.db, 0)

    def test_xavier_init_reasonable_scale(self):
        layer = LinearLayer(128, 64, seed=42)
        assert np.abs(layer.W).mean() < 0.2

    def test_deterministic_seed(self):
        l1 = LinearLayer(8, 4, seed=99)
        l2 = LinearLayer(8, 4, seed=99)
        assert np.allclose(l1.W, l2.W)


# ── PolicyNetwork ─────────────────────────────────────────────────────────

class TestPolicyNetwork:
    def test_output_is_valid_probability_distribution(self):
        net = PolicyNetwork(hidden_size=64, seed=0)
        obs = _rng.random(OBS_DIM).astype(np.float32)
        probs = net(obs)
        assert probs.shape == (len(ACTIONS),)
        assert probs.min() >= 0
        assert abs(probs.sum() - 1.0) < 1e-5

    def test_batched_probabilities_sum_to_one(self):
        net = PolicyNetwork(hidden_size=64, seed=0)
        batch = _rng.random((8, OBS_DIM)).astype(np.float32)
        probs = net(batch)
        assert probs.shape == (8, len(ACTIONS))
        assert np.allclose(probs.sum(axis=-1), 1.0, atol=1e-5)

    def test_sample_action_returns_valid_index(self):
        net = PolicyNetwork(hidden_size=64, seed=0)
        obs = _rng.random(OBS_DIM).astype(np.float32)
        action, log_prob = net.sample_action(obs)
        assert 0 <= action < len(ACTIONS)
        assert np.isfinite(log_prob)

    def test_different_seeds_give_different_outputs(self):
        net_a = PolicyNetwork(seed=0)
        net_b = PolicyNetwork(seed=1)
        obs = _rng.random(OBS_DIM).astype(np.float32)
        assert not np.allclose(net_a(obs), net_b(obs))


# ── ValueNetwork ──────────────────────────────────────────────────────────

class TestValueNetwork:
    def test_output_is_scalar_like(self):
        net = ValueNetwork(hidden_size=64, seed=0)
        obs = _rng.random(OBS_DIM).astype(np.float32)
        val = net(obs)
        assert np.asarray(val).size == 1

    def test_batched_output_length(self):
        net = ValueNetwork(hidden_size=64, seed=0)
        batch = _rng.random((8, OBS_DIM)).astype(np.float32)
        vals = net(batch)
        assert np.asarray(vals).shape[0] == 8

    def test_value_is_finite(self):
        net = ValueNetwork(hidden_size=64, seed=0)
        obs = np.zeros(OBS_DIM, dtype=np.float32)
        assert np.isfinite(float(net(obs)))


# ── PPO ───────────────────────────────────────────────────────────────────

class TestPPO:
    def test_instantiates_with_defaults(self):
        agent = PPO()
        assert agent.policy is not None
        assert agent.value is not None

    def test_hyperparams_stored(self):
        agent = PPO(gamma=0.95, clip_eps=0.1)
        assert math.isclose(agent.gamma, 0.95)
        assert math.isclose(agent.clip_eps, 0.1)

    def test_compute_gae_shapes(self):
        agent = PPO()
        n_steps = 16
        rewards = np.ones(n_steps, dtype=np.float32)
        values = np.ones(n_steps, dtype=np.float32) * 0.5
        dones = np.zeros(n_steps, dtype=np.float32)
        adv, ret = agent.compute_gae(
            rewards, values, dones, last_value=0.5
        )
        assert adv.shape == (n_steps,)
        assert ret.shape == (n_steps,)
        assert np.all(np.isfinite(adv))

    def test_update_runs_on_synthetic_batch(self):
        # tiny hidden size so finite-diff update completes quickly
        agent = PPO(hidden_size=4, n_epochs=1)
        n_steps = 8
        obs = _rng.random((n_steps, OBS_DIM)).astype(np.float32)
        actions = _rng.integers(
            0, len(ACTIONS), n_steps
        ).astype(np.int32)
        rewards = _rng.random(n_steps).astype(np.float32)
        values = _rng.random(n_steps).astype(np.float32)
        dones = np.zeros(n_steps, dtype=np.float32)
        logprobs = np.array(
            [agent.policy.sample_action(obs[i])[1] for i in range(n_steps)],
            dtype=np.float32,
        )
        batch = {
            "obs": obs,
            "actions": actions,
            "logprobs": logprobs,
            "rewards": rewards,
            "values": values,
            "dones": dones,
            "last_value": 0.0,
        }
        metrics = agent.update(batch)
        assert isinstance(metrics, dict)


# ── PPOAgent ──────────────────────────────────────────────────────────────

class TestPPOAgent:
    def test_instantiates_with_correct_dims(self):
        ag = PPOAgent()
        assert ag.obs_dim == OBS_DIM
        assert ag.action_dim == len(ACTIONS)

    def test_select_action_returns_valid_index(self):
        ag = PPOAgent()
        obs = _rng.random(OBS_DIM).astype(np.float32)
        action, log_prob = ag.select_action(obs)
        assert 0 <= action < len(ACTIONS)
        assert np.isfinite(log_prob)

    def test_get_value_returns_finite_float(self):
        ag = PPOAgent()
        obs = _rng.random(OBS_DIM).astype(np.float32)
        val = ag.get_value(obs)
        assert isinstance(val, float)
        assert np.isfinite(val)

    def test_status_returns_dict(self):
        ag = PPOAgent()
        assert isinstance(ag.status(), dict)
