"""
agents/rl/environment.py — RL Environment Wrapper for Terminal Depths
======================================================================
Wraps the Terminal Depths game as an OpenAI Gym-compatible environment.
Allows RL agents to learn optimal command sequences.

Observation space: player state vector (normalized)
Action space:  discrete — maps integer → game command string
Reward:  +XP gained, +level ups, -trace penalties, -death

Use:
    from agents.rl.environment import TerminalDepthsEnv
    env = TerminalDepthsEnv()
    obs, info = env.reset()
    for _ in range(1000):
        action = env.action_space.sample()
        obs, reward, done, truncated, info = env.step(action)
        if done: obs, info = env.reset()

Compatible with stable-baselines3 / RLlib if gym is installed.
Falls back to a minimal Gym-compatible interface if gym not present.
"""
from __future__ import annotations

import json
import math
import random
import time
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Minimal Gym-compatible shim (no dependency on gym/gymnasium)
# ---------------------------------------------------------------------------

class _Space:
    def sample(self): raise NotImplementedError
    def contains(self, x): raise NotImplementedError

class DiscreteSpace(_Space):
    def __init__(self, n: int):
        self.n = n
        self.shape = ()
        self.dtype = int

    def sample(self) -> int:
        return random.randint(0, self.n - 1)

    def contains(self, x) -> bool:
        return isinstance(x, int) and 0 <= x < self.n

class BoxSpace(_Space):
    def __init__(self, low: float, high: float, shape: tuple, dtype=float):
        self.low = low
        self.high = high
        self.shape = shape
        self.dtype = dtype

    def sample(self):
        return [random.uniform(self.low, self.high) for _ in range(self.shape[0])]

    def contains(self, x) -> bool:
        return len(x) == self.shape[0]

# Try to use real gym if available
try:
    import gymnasium as gym
    _GymEnv = gym.Env
    _USE_GYM = True
except ImportError:
    try:
        import gym
        _GymEnv = gym.Env
        _USE_GYM = True
    except ImportError:
        _GymEnv = object
        _USE_GYM = False


# ---------------------------------------------------------------------------
# Action set — game commands available to the RL agent
# ---------------------------------------------------------------------------

ACTIONS: List[str] = [
    # Navigation
    "ls", "pwd", "cd /opt", "cd /var", "cd /home/ghost",
    # Investigation
    "cat /var/log/nexus.log", "cat /etc/motd", "map",
    # Hacking
    "scan", "exploit", "hack chimera-proxy",
    # Social
    "talk ada hello", "talk raven intel", "talk serena",
    # Skills
    "skills", "status", "quests",
    # Puzzles
    "number-theory list", "number-theory load 1",
    # Economy
    "bank balance", "faction",
    # Combat/exploration
    "basement start", "sleep",
    # Tutorial
    "whoami", "help",
    # Lore
    "lore", "lore chimera", "lore zero",
]

OBS_DIM = 20  # observation vector length

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

class TerminalDepthsEnv(_GymEnv if _USE_GYM else object):
    """
    Terminal Depths as an RL environment.

    Observation: 20-dimensional float vector:
      [level, xp_pct, skills×9, is_root, commands_run_norm, timer_pct,
       faction_reps×4, mole_clues]
    Reward: XP gained + level bonus − trace penalty − death penalty
    Done: player death OR 72-hour timer expired OR max_steps
    """

    metadata = {"render_modes": ["ansi"]}

    def __init__(
        self,
        server_url: str = None,
        session_id: str = "rl-agent",
        max_steps: int = 500,
        render_mode: Optional[str] = None,
    ):
        import os
        if server_url is None:
            server_url = os.environ.get(
                "TD_SERVER_URL",
                "http://localhost:5000" if os.environ.get("REPL_ID") else "http://localhost:7337",
            )
        self.server_url = server_url
        self.session_id = session_id
        self.max_steps = max_steps
        self.render_mode = render_mode

        self.action_space = DiscreteSpace(len(ACTIONS))
        self.observation_space = BoxSpace(0.0, 1.0, (OBS_DIM,))

        self._step_count = 0
        self._prev_xp = 0
        self._prev_level = 0
        self._last_obs = [0.0] * OBS_DIM
        self._last_state: Dict[str, Any] = {}
        self._episode_reward = 0.0

    def _post_command(self, command: str) -> dict:
        """Send a game command; return parsed response."""
        try:
            payload = json.dumps({"session_id": self.session_id, "command": command}).encode()
            req = urllib.request.Request(
                f"{self.server_url}/api/game/command",
                payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read())
        except Exception:
            return {"state": {}, "output": []}

    def _state_to_obs(self, state: dict) -> List[float]:
        """Convert game state dict to normalized observation vector."""
        if not state:
            return [0.0] * OBS_DIM

        max_xp = max(state.get("xp_to_next", 100), 1)
        xp_pct = state.get("xp", 0) / max_xp

        skills = state.get("skills", {})
        skill_names = ["terminal", "networking", "security", "programming",
                       "git", "cryptography", "social_engineering", "forensics", "scripting"]
        skill_vec = [min(skills.get(sk, 0) / 100.0, 1.0) for sk in skill_names]

        timer_pct = 0.5  # default
        if "timer" in state:
            timer_pct = state["timer"].get("pct_elapsed", 0.5)

        faction_reps = state.get("faction_reps", {})
        faction_vec = [
            faction_reps.get("resistance", 0) / 100.0,
            faction_reps.get("corporation", 0) / 100.0,
            faction_reps.get("shadow_council", 0) / 100.0,
            faction_reps.get("specialist_guild", 0) / 100.0,
        ]

        obs = [
            min(state.get("level", 1) / 125.0, 1.0),      # 0: level
            xp_pct,                                         # 1: xp progress
            *skill_vec,                                     # 2-10: skills
            1.0 if state.get("is_root") else 0.0,          # 11: root
            min(state.get("commands_run", 0) / 1000.0, 1.0),  # 12: commands
            timer_pct,                                      # 13: timer
            *faction_vec,                                   # 14-17: factions
            min(state.get("mole_clues_found", 0) / 10.0, 1.0),  # 18: clues
            1.0 if state.get("mole_exposed") else 0.0,     # 19: mole
        ]
        return obs[:OBS_DIM]

    def _compute_reward(self, old_state: dict, new_state: dict, output: list) -> float:
        reward = 0.0

        # XP gain
        old_xp = old_state.get("xp", 0) + (old_state.get("level", 1) - 1) * 100
        new_xp = new_state.get("xp", 0) + (new_state.get("level", 1) - 1) * 100
        xp_delta = max(0, new_xp - old_xp)
        reward += xp_delta * 0.1

        # Level up bonus
        if new_state.get("level", 1) > old_state.get("level", 1):
            reward += 50.0

        # Root access bonus
        if new_state.get("is_root") and not old_state.get("is_root"):
            reward += 100.0

        # Mole exposure bonus
        if new_state.get("mole_exposed") and not old_state.get("mole_exposed"):
            reward += 200.0

        # Death penalty
        output_texts = " ".join(x.get("s", "") for x in output if isinstance(x, dict))
        if "TERMINATED" in output_texts or "terminated" in output_texts.lower():
            reward -= 50.0

        # Error penalty (command not found wastes a step)
        if any(x.get("t") == "error" for x in output if isinstance(x, dict)):
            reward -= 0.5

        return reward

    def reset(self, seed=None, options=None) -> Tuple[List[float], dict]:
        self._step_count = 0
        self._episode_reward = 0.0

        # Fresh session
        self.session_id = f"rl-agent-{int(time.time())}"
        resp = self._post_command("status")
        state = resp.get("state", {})
        self._last_state = state
        obs = self._state_to_obs(state)
        self._last_obs = obs
        return obs, {"session_id": self.session_id}

    def step(self, action: int) -> Tuple[List[float], float, bool, bool, dict]:
        command = ACTIONS[action % len(ACTIONS)]
        resp = self._post_command(command)

        new_state = resp.get("state", {})
        output = resp.get("output", [])

        reward = self._compute_reward(self._last_state, new_state, output)
        self._episode_reward += reward

        obs = self._state_to_obs(new_state)
        self._last_obs = obs
        self._last_state = new_state
        self._step_count += 1

        # Termination conditions
        output_texts = " ".join(x.get("s", "") for x in output if isinstance(x, dict))
        dead = "TERMINATED" in output_texts
        timer_done = new_state.get("timer", {}).get("pct_elapsed", 0.0) >= 1.0
        truncated = self._step_count >= self.max_steps
        done = dead or timer_done

        info = {
            "command": command,
            "level": new_state.get("level", 1),
            "xp": new_state.get("xp", 0),
            "episode_reward": self._episode_reward,
            "step": self._step_count,
        }
        return obs, reward, done, truncated, info

    def render(self) -> Optional[str]:
        if self.render_mode == "ansi":
            s = self._last_state
            return (
                f"[RL] Level {s.get('level',1)} | XP {s.get('xp',0)} | "
                f"Step {self._step_count} | EpReward {self._episode_reward:.1f}"
            )
        return None

    def close(self):
        pass

    # ── Convenience: random rollout for testing ──────────────────────────────

    @staticmethod
    def random_rollout(
        n_steps: int = 100,
        server_url: str = None,
        verbose: bool = True,
    ) -> dict:
        """Run a random policy for n_steps; return episode stats."""
        env = TerminalDepthsEnv(server_url=server_url)
        obs, info = env.reset()
        total_reward = 0.0
        steps = 0
        for i in range(n_steps):
            action = env.action_space.sample()
            obs, reward, done, truncated, info = env.step(action)
            total_reward += reward
            steps += 1
            if verbose and reward != 0:
                print(f"  step {i}: cmd={ACTIONS[action]!r} reward={reward:.1f}")
            if done or truncated:
                break
        env.close()
        return {
            "steps": steps,
            "total_reward": total_reward,
            "final_level": info.get("level", 1),
            "final_xp": info.get("xp", 0),
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Running 20-step random rollout...")
    result = TerminalDepthsEnv.random_rollout(n_steps=20, verbose=True)
    print(f"\nResult: {result}")
