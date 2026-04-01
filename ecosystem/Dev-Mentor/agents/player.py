#!/usr/bin/env python3
"""
agents/player.py — Autonomous Game Player Agent

Plays Terminal Depths via the REST API. Can run specific scenarios,
explore the world, complete challenges, and report observations.

Usage:
    python3 agents/player.py               # play full demo session
    python3 agents/player.py --scenario priv_esc
    python3 agents/player.py --scenario scripting
    python3 agents/player.py --scenario explore
    python3 agents/player.py --scenario challenges
    python3 agents/player.py --report      # generate play report
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_URL = "http://localhost:7337"

# PPO policy — optional, falls back to scripted play if unavailable
try:
    from agents.rl.ppo import PPOAgent as _PPOAgent
    _PPO_AVAILABLE = True
except ImportError:
    _PPOAgent = None  # type: ignore[assignment,misc]
    _PPO_AVAILABLE = False
KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"
KNOWLEDGE_DIR.mkdir(exist_ok=True)


def _post(path: str, data: dict) -> dict:
    req = urllib.request.Request(
        BASE_URL + path,
        json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def _get(path: str) -> dict:
    with urllib.request.urlopen(BASE_URL + path, timeout=8) as r:
        return json.loads(r.read())


class Player:
    """Autonomous game player with observation logging."""

    CYAN = "\033[36m"; GREEN = "\033[32m"; DIM = "\033[2m"; RESET = "\033[0m"

    def __init__(self, name: str = "Agent"):
        self.name = name
        self.sid: Optional[str] = None
        self.observations: List[dict] = []
        self.commands_run = 0

    def connect(self):
        r = _post("/api/game/session", {})
        self.sid = r["session_id"]
        state = r["state"]
        self._log(f"Connected: {self.sid[:8]}... level={state['level']} xp={state['xp']}")
        return self

    def cmd(self, command: str, silent: bool = False) -> List[dict]:
        r = _post("/api/game/command", {"command": command, "session_id": self.sid})
        out = r.get("output", [])
        self.commands_run += 1
        if not silent:
            self._print_cmd(command, out)
        self._observe(command, out)
        return out

    def script_run(self, code: str, name: str = "agent") -> List[dict]:
        r = _post("/api/script/run", {
            "code": code, "session_id": self.sid,
            "agent_token": "GHOST-DEV-2026-ALPHA", "name": name
        })
        out = r.get("output", [])
        self._log(f"[script:{name}] {len(out)} lines output")
        return out

    def get_state(self) -> dict:
        return _post("/api/game/command", {"command": "skills", "session_id": self.sid}).get("state", {})

    def _print_cmd(self, command: str, out: List[dict]):
        print(f"{self.DIM}$ {command}{self.RESET}")
        for item in out[:4]:
            if isinstance(item, dict):
                t = item.get("t", "")
                s = item.get("s", "")
                if t == "error":
                    print(f"  \033[31m{s[:100]}\033[0m")
                elif t in ("success", "xp"):
                    print(f"  {self.GREEN}{s[:100]}{self.RESET}")
                elif t != "clear":
                    print(f"  {s[:100]}")

    def _observe(self, cmd: str, out: List[dict]):
        errors = [i.get("s", "") for i in out if isinstance(i, dict) and i.get("t") == "error"]
        self.observations.append({
            "cmd": cmd,
            "lines": len(out),
            "errors": errors,
            "has_error": bool(errors),
        })

    def _log(self, msg: str):
        print(f"{self.CYAN}[{self.name}]{self.RESET} {msg}")

    # ── Scenarios ─────────────────────────────────────────────────────

    def scenario_onboarding(self):
        """New player onboarding experience."""
        self._log("Scenario: Onboarding")
        self.cmd("help")
        self.cmd("tutorial")
        self.cmd("whoami")
        self.cmd("ls")
        self.cmd("cat README.md")
        self.cmd("skills")
        self.cmd("talk ada")

    def scenario_priv_esc(self):
        """Full privilege escalation path."""
        self._log("Scenario: Privilege Escalation")
        self.cmd("cat notes.txt")
        self.cmd("cat /etc/passwd")
        self.cmd("cat /etc/shadow")  # Should fail
        self.cmd("sudo -l")
        self.cmd("ps aux")
        self.cmd("cat /proc/1337/environ")
        self.cmd("cat /var/log/nexus.log")
        self.cmd("cat /var/log/chimera.log")  # Might fail
        self.cmd("sudo find . -exec /bin/sh ;")
        self.cmd("whoami")  # Should be root
        self.cmd("cat /etc/shadow")  # Should work now
        self.cmd("cat /opt/chimera/keys/master.key")
        self.cmd("cat /opt/chimera/config/master.conf")

    def scenario_scripting(self):
        """Play through scripting API features."""
        self._log("Scenario: Scripting API")
        self.cmd("script list")
        self.cmd("script run hello.py")
        self.cmd("script run recon.py")
        self.cmd("script run exploit.py")
        self.cmd("script run loot_collector.py")
        self.cmd("script run generate_challenge.py networking hard")
        self.cmd("script run test_suite.py")

        # Write a custom script
        self.cmd("script new my_agent.py")
        code = (
            "ns.tprint('[Agent] Starting recon...')\n"
            "player = ns.getPlayer()\n"
            "ns.tprint(f'Level: {player[\"level\"]} XP: {player[\"xp\"]}')\n"
            "hosts = ns.scan()\n"
            "for h in hosts:\n"
            "    srv = ns.getServer(h)\n"
            "    ns.tprint(f'  {h}: {srv[\"ip\"]} ram={srv[\"ram\"]}GB')\n"
            "results = [ns.hack(h) for h in hosts]\n"
            "wins = sum(1 for r in results if r['success'])\n"
            "ns.tprint(f'Hacked {wins}/{len(hosts)} nodes')\n"
            "ns.addXP(20, 'security')\n"
        )
        self.script_run(code, "agent_recon")

    def scenario_explore(self):
        """Explore the full virtual filesystem."""
        self._log("Scenario: Exploration")
        dirs = [
            "/home/ghost", "/home/ghost/ctf", "/home/ghost/scripts",
            "/home/ghost/tools", "/etc", "/var/log", "/var/msg",
            "/opt", "/proc", "/tmp",
        ]
        for d in dirs:
            self.cmd(f"ls {d}", silent=True)
            print(f"  {self.DIM}ls {d}{self.RESET} → {len(self.observations[-1].get('errors', []))==0}")

        # Interesting files
        files = [
            "/var/msg/ada",
            "/etc/ssh/sshd_config",
            "/etc/cron.d/sync",
            "/proc/1337/environ",
            "/home/ghost/.hidden",
            "/home/ghost/mission.enc",
        ]
        self._log("Reading interesting files:")
        for f in files:
            out = self.cmd(f"cat {f}", silent=True)
            has_content = any(i.get("t") != "error" for i in out if isinstance(i, dict))
            print(f"  {'✓' if has_content else '✗'} {f}")

    def scenario_challenges(self):
        """Attempt the CTF challenges."""
        self._log("Scenario: CTF Challenges")
        self.cmd("ls /home/ghost/ctf")
        for i in range(1, 5):
            self.cmd(f"cat /home/ghost/ctf/challenge0{i}.txt")

        # Challenge solutions
        self.cmd("find /home/ghost -name '.*' 2>/dev/null")
        self.cmd("echo 'Q0hJTUVSQV9DT05ORUNUX0tFWT1uZXh1czEzMzc=' | base64 -d")
        self.cmd("nc chimera-control 8443")
        self.cmd("sudo find . -exec /bin/sh ;")  # priv esc for challenge 4

    def scenario_devmode(self):
        """Play through developer mode features."""
        self._log("Scenario: Developer Mode")
        self.cmd("devmode on GHOST-DEV-2026-ALPHA")
        self.cmd("inspect state")
        self.cmd("inspect fs")
        self.cmd("inspect story")
        self.cmd("inspect processes")
        self.cmd("profile")
        self.cmd("spawn /tmp/agent_created.txt 'created by player agent'")
        self.cmd("cat /tmp/agent_created.txt")
        self.cmd("generate challenge networking hard")
        self.cmd("generate lore")
        self.cmd("test all")

    def scenario_ppo(self, n_steps: int = 50):
        """Play using the PPO policy network when available; falls back to scripted explore."""
        self._log("Scenario: PPO Policy")
        if not _PPO_AVAILABLE or _PPOAgent is None:
            self._log("PPO unavailable — falling back to explore scenario")
            return self.scenario_explore()

        try:
            from agents.rl.environment import TerminalDepthsEnv, ACTIONS
            import numpy as np

            env = TerminalDepthsEnv(server_url=BASE_URL, session_id=self.sid)
            agent = _PPOAgent()

            # Load latest checkpoint if available
            import glob as _glob, os
            ckpts = sorted(_glob.glob("state/rl/policy_ep*.npz"))
            if ckpts:
                agent._ppo.policy.load(ckpts[-1].replace(".npz", ""))
                self._log(f"Loaded checkpoint: {os.path.basename(ckpts[-1])}")
            else:
                self._log("No checkpoint found — using untrained policy (random-ish)")

            obs, _ = env.reset()
            total_reward = 0.0
            for step in range(n_steps):
                obs_arr = np.array(obs, dtype=np.float32)
                action, _ = agent._ppo.policy.sample_action(obs_arr)
                command = ACTIONS[action % len(ACTIONS)]
                out = self.cmd(command, silent=True)
                obs, reward, done, truncated, _ = env.step(action)
                total_reward += reward
                if step % 10 == 0:
                    self._log(f"  step {step:3d}: {command!r:35s} reward={reward:+.1f}  total={total_reward:+.1f}")
                if done or truncated:
                    obs, _ = env.reset()
            self._log(f"PPO scenario complete: {n_steps} steps, total_reward={total_reward:+.1f}")
        except Exception as exc:
            self._log(f"PPO scenario error: {exc} — falling back to explore")
            self.scenario_explore()

    def report(self) -> dict:
        """Generate a report of the play session."""
        errors = [o for o in self.observations if o["has_error"]]
        report = {
            "session_id": self.sid[:8] if self.sid else "?",
            "commands_run": self.commands_run,
            "error_commands": len(errors),
            "error_rate": f"{len(errors)/max(1,self.commands_run)*100:.1f}%",
            "failed_commands": [o["cmd"] for o in errors[:10]],
        }
        return report

    def save_report(self, scenario: str):
        r = self.report()
        path = KNOWLEDGE_DIR / f"player_report_{scenario}.json"
        with open(path, "w") as f:
            json.dump({**r, "scenario": scenario, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ")}, f, indent=2)
        print(f"\n[Report saved: {path}]")
        return r


def main():
    parser = argparse.ArgumentParser(description="Terminal Depths Player Agent")
    parser.add_argument("--scenario", "-s", default="all",
                        choices=["onboarding", "priv_esc", "scripting", "explore",
                                 "challenges", "devmode", "ppo", "all"],
                        help="Scenario to play")
    parser.add_argument("--report", "-r", action="store_true", help="Print play report")
    parser.add_argument("--task", help="Task ID (for orchestrator delegation)")
    args = parser.parse_args()

    try:
        p = Player(name="PlayerAgent").connect()
    except Exception as e:
        print(f"[ERROR] Cannot connect to game server: {e}")
        sys.exit(1)

    scenarios = {
        "onboarding": p.scenario_onboarding,
        "priv_esc":   p.scenario_priv_esc,
        "scripting":  p.scenario_scripting,
        "explore":    p.scenario_explore,
        "challenges": p.scenario_challenges,
        "devmode":    p.scenario_devmode,
        "ppo":        p.scenario_ppo,
    }

    if args.scenario == "all":
        for name, fn in scenarios.items():
            print(f"\n{'='*50}")
            fn()
    else:
        scenarios[args.scenario]()

    r = p.save_report(args.scenario)
    if args.report:
        print(f"\n{'='*50}")
        print(f"Commands run:   {r['commands_run']}")
        print(f"Error rate:     {r['error_rate']}")
        if r["failed_commands"]:
            print(f"Failed commands: {r['failed_commands']}")


if __name__ == "__main__":
    main()
