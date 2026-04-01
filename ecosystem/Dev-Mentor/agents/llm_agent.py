"""
LLM Agent — autonomous content generator for Terminal Depths.

Watches the tasks/ queue for LLM-flavored tasks and fulfills them:
  - generate_challenge  → adds to challenges DB
  - generate_lore       → writes to virtual FS lore file
  - generate_npc        → creates NPC dialogue entry
  - generate_command    → scaffolds a new command handler
  - generate_tests      → writes pytest tests for a command
  - analyze_devlog      → produces next-action priorities
  - debug_error         → suggests a fix for a traceback

Usage:
    python agents/llm_agent.py               # process one task
    python agents/llm_agent.py --loop        # run indefinitely
    python agents/llm_agent.py --status      # show backend + task queue
    python agents/llm_agent.py --demo        # run demo prompts
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_client import LLMClient, Prompts

TASKS_DIR = Path("tasks")
FILE_TASKS_DIR = TASKS_DIR / "legacy_runtime"
DONE_TASKS_DIR = FILE_TASKS_DIR / "done"
OUTPUTS_DIR = Path("agents/outputs")
KNOWLEDGE_DIR = Path("knowledge")
CHALLENGES_FILE = Path("app/game_engine/challenge_db.json")

TASKS_DIR.mkdir(exist_ok=True)
FILE_TASKS_DIR.mkdir(parents=True, exist_ok=True)
DONE_TASKS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)
KNOWLEDGE_DIR.mkdir(exist_ok=True)


def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def log(msg: str):
    print(f"[{ts()}] [llm_agent] {msg}")


class LLMAgent:
    """Autonomous LLM-powered content generation agent."""

    def __init__(self):
        self.llm = LLMClient()
        log(f"LLM backend: {self.llm.backend_name}")

    # ── Task processing ──────────────────────────────────────────────────

    def process_task(self, task_file: Path) -> dict:
        """Load and process a task file. Returns result dict."""
        try:
            task = json.loads(task_file.read_text())
        except Exception as e:
            return {"ok": False, "error": f"Bad task file: {e}"}

        task_type = task.get("type", "unknown")
        log(f"Processing task: {task_type} ({task_file.name})")

        handlers = {
            "generate_challenge": self._task_generate_challenge,
            "generate_lore": self._task_generate_lore,
            "generate_command": self._task_generate_command,
            "generate_tests": self._task_generate_tests,
            "analyze_devlog": self._task_analyze_devlog,
            "debug_error": self._task_debug_error,
            "generate_npc": self._task_generate_npc,
            "freeform": self._task_freeform,
        }

        handler = handlers.get(task_type)
        if not handler:
            return {"ok": False, "error": f"Unknown task type: {task_type}"}

        result = handler(task)
        result["task_type"] = task_type
        result["task_file"] = task_file.name
        result["timestamp"] = datetime.now().isoformat()

        if result.get("ok"):
            self._save_output(task_file.stem, result)
            task_file.rename(DONE_TASKS_DIR / task_file.name)
            log(f"  ✓ Task completed: {task_file.stem}")
        else:
            log(f"  ✗ Task failed: {result.get('error')}")

        return result

    def _save_output(self, name: str, result: dict):
        out_file = OUTPUTS_DIR / f"{name}_output.json"
        out_file.write_text(json.dumps(result, indent=2))

    # ── Task handlers ────────────────────────────────────────────────────

    def _task_generate_challenge(self, task: dict) -> dict:
        category = task.get("category", "networking")
        difficulty = task.get("difficulty", "medium")
        prompt = Prompts.generate_challenge(category, difficulty)
        raw = self.llm.generate(
            prompt,
            system="You are a CTF challenge designer. Return ONLY valid JSON.",
            max_tokens=300,
        )
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            challenge = json.loads(raw[start:end])
            challenge["category"] = category
            challenge["difficulty"] = difficulty
            challenge["source"] = "llm_agent"
            challenge["generated_at"] = datetime.now().isoformat()
            self._append_challenge(challenge)
            return {"ok": True, "challenge": challenge}
        except Exception as e:
            return {"ok": False, "error": f"JSON parse failed: {e}", "raw": raw}

    def _task_generate_lore(self, task: dict) -> dict:
        node = task.get("node", "node-7")
        context = task.get("context", "")
        lore = self.llm.generate(Prompts.generate_lore(node, context), max_tokens=200)
        lore_file = KNOWLEDGE_DIR / f"lore_{node}_{int(time.time())}.md"
        lore_file.write_text(f"# Lore: {node}\n\n{lore}\n")
        return {"ok": True, "lore": lore, "file": str(lore_file)}

    def _task_generate_command(self, task: dict) -> dict:
        cmd = task.get("command", "example")
        flags = task.get("flags", "-h, --help")
        desc = task.get("description", "A useful command")
        prompt = Prompts.generate_command_handler(cmd, flags, desc)
        code = self.llm.generate(prompt, system=Prompts.SYSTEM_DEV, max_tokens=500)
        out_file = OUTPUTS_DIR / f"cmd_{cmd}.py"
        out_file.write_text(code)
        return {"ok": True, "code": code, "file": str(out_file), "command": cmd}

    def _task_generate_tests(self, task: dict) -> dict:
        cmd = task.get("command", "example")
        prompt = (
            f"Write pytest test cases for a virtual terminal command `{cmd}` in a hacking game.\n"
            f"The command handler returns List[dict] with keys 't' (type) and 's' (text).\n"
            f"Test: basic call, help flag, error conditions, expected output content.\n"
            f"Keep tests simple and self-contained."
        )
        code = self.llm.generate(prompt, system=Prompts.SYSTEM_DEV, max_tokens=500)
        out_file = OUTPUTS_DIR / f"test_cmd_{cmd}.py"
        out_file.write_text(code)
        return {"ok": True, "code": code, "file": str(out_file), "command": cmd}

    def _task_analyze_devlog(self, task: dict) -> dict:
        devlog = Path("devlog.md")
        if not devlog.exists():
            return {"ok": False, "error": "devlog.md not found"}
        text = devlog.read_text()
        priorities = self.llm.generate(Prompts.devlog_priorities(text), max_tokens=400)
        todo = Path("todo.md")
        current = todo.read_text() if todo.exists() else "# TODO\n\n"
        section = f"\n## AI Priorities — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{priorities}\n"
        todo.write_text(current + section)
        log(f"  Appended AI priorities to todo.md")
        return {"ok": True, "priorities": priorities}

    def _task_debug_error(self, task: dict) -> dict:
        tb = task.get("traceback", "")
        code = task.get("code", "")
        prompt = Prompts.debug_error(tb, code)
        suggestion = self.llm.generate(prompt, max_tokens=300)
        return {"ok": True, "suggestion": suggestion}

    def _task_generate_npc(self, task: dict) -> dict:
        name = task.get("name", "unknown")
        personality = task.get("personality", "mysterious")
        question = task.get("question", "What should I do?")
        prompt = Prompts.npc_response(name, personality, question)
        response = self.llm.generate(prompt, system=Prompts.SYSTEM_GAME, max_tokens=150)
        npc_file = KNOWLEDGE_DIR / f"npc_{name}.jsonl"
        entry = json.dumps({"q": question, "a": response, "ts": datetime.now().isoformat()})
        with open(npc_file, "a") as f:
            f.write(entry + "\n")
        return {"ok": True, "response": response, "npc": name}

    def _task_freeform(self, task: dict) -> dict:
        prompt = task.get("prompt", "Say hello.")
        system = task.get("system", Prompts.SYSTEM_GAME)
        max_tokens = task.get("max_tokens", 500)
        result = self.llm.generate(prompt, system=system, max_tokens=max_tokens)
        return {"ok": True, "result": result}

    # ── Challenge DB helper ──────────────────────────────────────────────

    def _append_challenge(self, challenge: dict):
        if CHALLENGES_FILE.exists():
            db = json.loads(CHALLENGES_FILE.read_text())
        else:
            db = []
        db.append(challenge)
        CHALLENGES_FILE.write_text(json.dumps(db, indent=2))

    # ── Demo mode ────────────────────────────────────────────────────────

    def demo(self):
        print("\n" + "="*60)
        print("  LLM AGENT DEMO — Terminal Depths")
        print("="*60)

        print(f"\n[1] Backend Status:")
        st = self.llm.status()
        for k, v in st.items():
            print(f"    {k}: {v}")

        print(f"\n[2] Game Master response:")
        gm = self.llm.generate(
            "Ghost has just achieved root access for the first time. Describe the moment.",
            system=Prompts.SYSTEM_GAME,
            max_tokens=100,
        )
        print(f"    {gm}")

        print(f"\n[3] Challenge generation (networking):")
        raw = self.llm.generate(
            Prompts.generate_challenge("networking", "medium"),
            system="Return ONLY valid JSON.",
            max_tokens=200,
        )
        print(f"    {raw[:300]}")

        print(f"\n[4] NPC dialogue (Ada, player asks about CHIMERA):")
        ada = self.llm.generate(
            Prompts.npc_response("Ada", "former NexusCorp engineer, cryptic, protective",
                                 "What exactly is Project CHIMERA?"),
            system=Prompts.SYSTEM_GAME,
            max_tokens=100,
        )
        print(f"    Ada: {ada}")

        print(f"\n[5] Lore generation (chimera-control server):")
        lore = self.llm.generate(
            Prompts.generate_lore("chimera-control", "NexusCorp's main surveillance control node"),
            max_tokens=100,
        )
        print(f"    {lore}")

        print("\n" + "="*60)
        print("  Demo complete.")
        print("="*60 + "\n")

    # ── Main loop ────────────────────────────────────────────────────────

    def run_once(self) -> int:
        """Process all pending tasks once. Returns count processed."""
        tasks = sorted(FILE_TASKS_DIR.glob("task_*.json"))
        if not tasks:
            log("No pending tasks.")
            return 0
        count = 0
        for task_file in tasks:
            self.process_task(task_file)
            count += 1
        return count

    def run_loop(self, interval: int = 10):
        """Process tasks continuously, sleeping between passes."""
        log(f"Starting loop (poll interval: {interval}s)")
        while True:
            processed = self.run_once()
            if not processed:
                log(f"Idle — next poll in {interval}s")
            time.sleep(interval)

    def status(self):
        pending = list(FILE_TASKS_DIR.glob("task_*.json"))
        done = list(DONE_TASKS_DIR.glob("*.json"))
        outputs = list(OUTPUTS_DIR.glob("*.json"))
        st = self.llm.status()
        print(f"\n{'='*50}")
        print(f"  LLM Agent Status")
        print(f"{'='*50}")
        print(f"  Backend:        {st['active_backend']}")
        print(f"  Replit AI:      {st['replit_ai']}")
        print(f"  Ollama:         {st['ollama']}")
        if st.get("ollama_models"):
            print(f"  Ollama models:  {', '.join(st['ollama_models'])}")
        print(f"  Pending tasks:  {len(pending)}")
        print(f"  Done tasks:     {len(done)}")
        print(f"  Outputs:        {len(outputs)}")
        if pending:
            print(f"\n  Pending:")
            for t in pending:
                print(f"    - {t.name}")
        print(f"{'='*50}\n")


def _create_sample_tasks():
    """Create sample task files for demonstration."""
    samples = [
        {"type": "generate_challenge", "category": "privilege_escalation", "difficulty": "hard"},
        {"type": "generate_lore", "node": "chimera-control", "context": "CHIMERA central server"},
        {"type": "generate_npc", "name": "nova", "personality": "NexusCorp CISO, hostile and intelligent",
         "question": "Why is CHIMERA justified?"},
        {"type": "analyze_devlog"},
    ]
    for i, task in enumerate(samples):
        f = FILE_TASKS_DIR / f"task_sample_{i:03d}.json"
        f.write_text(json.dumps(task, indent=2))
    print(f"Created {len(samples)} sample tasks in {FILE_TASKS_DIR}/")


def main():
    parser = argparse.ArgumentParser(description="LLM Agent for Terminal Depths")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--demo", action="store_true", help="Run demo prompts")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--create-tasks", action="store_true", help="Create sample tasks")
    parser.add_argument("--interval", type=int, default=10, help="Poll interval in seconds")
    args = parser.parse_args()

    agent = LLMAgent()

    if args.status:
        agent.status()
    elif args.demo:
        agent.demo()
    elif args.create_tasks:
        _create_sample_tasks()
    elif args.loop:
        agent.run_loop(interval=args.interval)
    else:
        agent.run_once()


if __name__ == "__main__":
    main()
