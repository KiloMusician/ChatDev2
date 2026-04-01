"""
generate_lore_batch.py — Procedural lore fragment generator.

Generates log files, emails, notes, and memos for Terminal Depths nodes.
Injects them into the game's virtual filesystem and logs to memory.

Usage:
    python generate_lore_batch.py                        # 20 fragments
    python generate_lore_batch.py --count 50
    python generate_lore_batch.py --node chimera-control # specific node
    python generate_lore_batch.py --type email           # email fragments only
    python generate_lore_batch.py --inject               # also write to game VFS
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path
from typing import Optional

from memory import Memory, get_memory
from llm_client import LLMClient


LORE_PATH = Path(".devmentor/lore_library.json")
LORE_PATH.parent.mkdir(parents=True, exist_ok=True)

NODES = [
    "nexuscorp-hq", "chimera-control", "node-7", "watcher-relay",
    "ghost-home", "darknet-hub", "nova-office", "ada-lab",
    "exfil-server", "backup-vault", "ghost-relay", "recon-node",
]
LORE_TYPES = ["log", "email", "note", "memo", "chat", "report", "config"]

PROMPTS = {
    "log": (
        "Write a realistic server log fragment (10-15 lines) from a NexusCorp node called '{node}'. "
        "Include timestamps, IP addresses, suspicious activity, and references to Project CHIMERA or Ghost. "
        "Cyberpunk dystopia setting, 2045."
    ),
    "email": (
        "Write a corporate email from NexusCorp's '{node}' node. "
        "It should hint at corruption, surveillance, or Project CHIMERA. "
        "Include To, From, Subject, Date headers and 3-4 sentences of body. Cyberpunk 2045."
    ),
    "note": (
        "Write a short handwritten note (50-80 words) found on the '{node}' server. "
        "It's from a corporate insider who is scared about what CHIMERA is doing. "
        "Cryptic, paranoid tone. Cyberpunk 2045."
    ),
    "memo": (
        "Write an internal corporate memo from '{node}' node in NexusCorp. "
        "Topic: a security breach, the Ghost hacker, or CHIMERA escalation protocol. "
        "Formal tone, 60-80 words."
    ),
    "chat": (
        "Write a leaked chat log (4-6 messages) between two NexusCorp employees on the '{node}' node. "
        "They're worried about Ghost, a hacker. One is complicit, one is scared. "
        "Use handles like [sys_admin], [nova], [r3d], [watcher]. Cyberpunk 2045."
    ),
    "report": (
        "Write an intelligence report from NexusCorp security about hacker activity on '{node}'. "
        "Should mention Ghost, detected intrusion attempts, and CHIMERA exposure risk. "
        "100-120 words, formal security language."
    ),
    "config": (
        "Write a realistic-looking configuration file excerpt from NexusCorp's '{node}' node. "
        "Include suspicious parameters, hardcoded credentials, or CHIMERA-related settings. "
        "30-40 lines. Cyberpunk 2045."
    ),
}

VFS_NODE_DIRS = {
    "chimera-control": "/opt/chimera/logs",
    "node-7": "/var/log",
    "nexuscorp-hq": "/var/log/nexus",
    "watcher-relay": "/dev/.watcher_logs",
    "ghost-home": "/home/ghost/notes",
    "nova-office": "/var/msg",
    "ada-lab": "/home/ada",
}


def _load_library() -> list[dict]:
    if LORE_PATH.exists():
        try:
            return json.loads(LORE_PATH.read_text())
        except Exception:
            return []
    return []


def _save_library(lib: list[dict]) -> None:
    LORE_PATH.write_text(json.dumps(lib, indent=2))


def _generate_fragment(
    llm: LLMClient,
    node: str,
    lore_type: str,
) -> Optional[str]:
    prompt_tmpl = PROMPTS.get(lore_type, PROMPTS["log"])
    prompt = prompt_tmpl.format(node=node)
    text = llm.generate(prompt, max_tokens=250, temperature=0.9)
    return text.strip() if text and len(text) > 20 else None


def run_batch(
    count: int = 20,
    node: Optional[str] = None,
    lore_type: Optional[str] = None,
    inject: bool = False,
    quiet: bool = False,
) -> dict:
    mem = get_memory()
    llm = LLMClient()
    library = _load_library()
    existing = {f["content"][:50] for f in library}

    generated = 0
    t0 = time.time()

    nodes = [node] if node else NODES
    types = [lore_type] if lore_type else LORE_TYPES

    if not quiet:
        print(f"[lore_batch] Generating {count} fragments…  library={len(library)}")

    for _ in range(count * 2):
        if generated >= count:
            break
        n = random.choice(nodes)
        t = random.choice(types)
        text = _generate_fragment(llm, n, t)
        if not text or text[:50] in existing:
            continue

        entry = {"node": n, "type": t, "content": text}
        library.append(entry)
        existing.add(text[:50])
        mem.store_generated("lore", text, metadata={"node": n, "type": t})
        generated += 1

        if not quiet:
            print(f"  [{generated}/{count}] {t}@{n}  ({len(text)} chars)")

        # optionally inject into VFS directory listing (flat text file)
        if inject:
            vfs_dir = VFS_NODE_DIRS.get(n, "/var/log")
            ext = {"log": ".log", "email": ".eml", "note": ".txt",
                   "memo": ".txt", "chat": ".log", "report": ".rpt", "config": ".conf"}.get(t, ".txt")
            fname = f"{n}_{t}_{generated}{ext}"
            inject_path = Path(f".devmentor/vfs_inject/{vfs_dir.lstrip('/')}")
            inject_path.mkdir(parents=True, exist_ok=True)
            (inject_path / fname).write_text(text)

    _save_library(library)
    elapsed = round(time.time() - t0, 1)

    result = {
        "generated": generated,
        "library_total": len(library),
        "elapsed_s": elapsed,
        "library_path": str(LORE_PATH),
    }
    if not quiet:
        print(f"\n[lore_batch] Done — generated={generated} library={len(library)} ({elapsed}s)")
    return result


if __name__ == "__main__":
    count = 20
    node = None
    lore_type = None
    inject = "--inject" in sys.argv
    quiet = "--quiet" in sys.argv

    for i, arg in enumerate(sys.argv):
        if arg == "--count" and i + 1 < len(sys.argv):
            count = int(sys.argv[i + 1])
        if arg == "--node" and i + 1 < len(sys.argv):
            node = sys.argv[i + 1]
        if arg == "--type" and i + 1 < len(sys.argv):
            lore_type = sys.argv[i + 1]

    run_batch(count=count, node=node, lore_type=lore_type, inject=inject, quiet=quiet)
