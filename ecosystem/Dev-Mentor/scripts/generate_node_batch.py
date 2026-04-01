"""scripts/generate_node_batch.py — Procedural world node (server) generator.

Creates new network nodes for Terminal Depths with unique:
  • Themes (corporate, underground, resistance, academic, gov, darknet)
  • Virtual filesystem contents (files, configs, logs)
  • Resident NPCs and challenges
  • Connection graph integration

Usage:
    python scripts/generate_node_batch.py               # generate 3 nodes
    python scripts/generate_node_batch.py --count 5     # generate N nodes
    python scripts/generate_node_batch.py --theme corp  # specific theme
    python scripts/generate_node_batch.py --dry-run
"""

from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUTPUT_FILE = ROOT / ".devmentor" / "node_pool.json"

THEMES = {
    "corp": {
        "name": "Corporate Server",
        "hostname_templates": [
            "srv-{n}.corp.internal",
            "dc{n}.megacorp.net",
            "prod-{n}.omnicorp.io",
        ],
        "os": ["Windows Server 2029", "CentOS 8.x (EOL)", "RHEL 9.1"],
        "mood": "sterile, hostile, heavily monitored",
        "files": [
            "quarterly_report_FINAL.xlsx",
            "employee_data.csv",
            "firewall_rules.conf",
            "audit_log.txt",
        ],
        "npc_type": "corporate_drone",
    },
    "underground": {
        "name": "Underground Node",
        "hostname_templates": [
            "node{n}.onion",
            "dark{n}.underground",
            "ghost-{n}.null",
        ],
        "os": ["Kali Linux 2029", "QubesOS", "Tails 6.x"],
        "mood": "chaotic, paranoid, collaborative",
        "files": [
            "exploits.tar.gz",
            "zero_days.txt",
            "contact_list.enc",
            "manifesto.md",
        ],
        "npc_type": "hacker",
    },
    "resistance": {
        "name": "Resistance Cell",
        "hostname_templates": [
            "cell{n}.free.net",
            "r{n}.liberation.org",
            "node{n}.resistance",
        ],
        "os": ["Ubuntu 28 LTS", "Debian 14", "Arch Linux"],
        "mood": "urgent, hopeful, secretive",
        "files": [
            "intel_dump.txt",
            "safe_houses.enc",
            "broadcast_key.pem",
            "mission_brief.md",
        ],
        "npc_type": "rebel",
    },
    "academic": {
        "name": "Research Institute",
        "hostname_templates": [
            "lab{n}.university.edu",
            "research{n}.institute.ac",
            "hpc{n}.academia.net",
        ],
        "os": ["Ubuntu 26 LTS", "Scientific Linux 8", "NixOS"],
        "mood": "curious, open, slightly naive",
        "files": [
            "research_data.csv",
            "paper_draft.pdf",
            "experiment_log.txt",
            "thesis.tex",
        ],
        "npc_type": "researcher",
    },
    "gov": {
        "name": "Government System",
        "hostname_templates": [
            "sys{n}.gov.classified",
            "dc{n}.agency.mil",
            "srv{n}.federal.gov",
        ],
        "os": ["Windows Server 2029 Hardened", "RHEL 9 STIG", "Fedora Server"],
        "mood": "formal, paranoid, bureaucratic",
        "files": [
            "classified_report.pdf",
            "personnel_file.dat",
            "access_log.txt",
            "security_policy.pdf",
        ],
        "npc_type": "agent",
    },
    "darknet": {
        "name": "Darknet Market Node",
        "hostname_templates": ["{n}market.onion", "shop{n}.dark", "bazaar{n}.void"],
        "os": ["Debian 13", "Alpine Linux", "Unknown"],
        "mood": "transactional, dangerous, anonymous",
        "files": ["inventory.enc", "transactions.db", "pgp_key.asc", "rules.txt"],
        "npc_type": "broker",
    },
}

CHALLENGE_TEMPLATES = [
    {
        "title": "Crack the config",
        "description": "Decrypt the config file using the key hidden in the logs.",
        "xp": 200,
    },
    {
        "title": "Pivot access",
        "description": "Use credentials found here to access the adjacent node.",
        "xp": 300,
    },
    {
        "title": "Exfiltrate the data",
        "description": "Copy the target file without triggering the IDS.",
        "xp": 250,
    },
    {
        "title": "Find the backdoor",
        "description": "Locate the hidden admin account in the user database.",
        "xp": 150,
    },
    {
        "title": "Patch the vuln",
        "description": "Identify and document the CVE in the running service.",
        "xp": 200,
    },
]


def _llm_enhance_node(node: dict, theme: str) -> dict:
    """Use LLM to enrich node description and add unique lore."""
    try:
        sys.path.insert(0, str(ROOT))
        from llm_client import get_client

        llm = get_client()
        t = THEMES[theme]
        prompt = f"""For a cyberpunk terminal RPG, write a 2-sentence description for a {t['name']} called '{node['hostname']}'.
Mood: {t['mood']}. Make it evocative and specific. Return only the description text."""
        node["description"] = llm.generate(
            prompt, max_tokens=100, temperature=0.8
        ).strip()
    except Exception:
        node["description"] = f"A {THEMES[theme]['name']} with restricted access."
    return node


def _build_node(theme_key: str, index: int) -> dict:
    t = THEMES[theme_key]
    n = str(index).zfill(2)
    hostname = random.choice(t["hostname_templates"]).format(n=n)

    # Build virtual filesystem
    files = {}
    for fname in t["files"]:
        files[fname] = (
            f"[BINARY: {fname}]"
            if any(
                fname.endswith(x)
                for x in [".xlsx", ".pdf", ".db", ".enc", ".dat", ".tar.gz"]
            )
            else f"# {fname}\n# Content redacted — use `cat` to view\n"
        )

    # Pick a challenge
    challenge = {**random.choice(CHALLENGE_TEMPLATES)}
    challenge["id"] = f"ch_{hostname.replace('.', '_')}_{int(time.time())}"

    node = {
        "id": f"node_{hostname.replace('.', '_')}",
        "hostname": hostname,
        "ip": f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
        "theme": theme_key,
        "theme_name": t["name"],
        "os": random.choice(t["os"]),
        "mood": t["mood"],
        "security_level": random.randint(1, 5),
        "files": files,
        "challenge": challenge,
        "npc_type": t["npc_type"],
        "connections": [],  # filled by graph builder
        "discovered": False,
        "created_at": datetime.now().isoformat(),
    }
    return node


def generate(
    count: int = 3, theme: str | None = None, dry_run: bool = False
) -> list[dict]:
    # Load existing pool
    existing = []
    if OUTPUT_FILE.exists():
        data = json.loads(OUTPUT_FILE.read_text())
        existing = data.get("nodes", [])
    existing_ids = {n["id"] for n in existing}

    new_nodes = []
    theme_keys = list(THEMES.keys())

    for i in range(count):
        t = theme or random.choice(theme_keys)
        if t not in THEMES:
            t = random.choice(theme_keys)
        node = _build_node(t, len(existing) + len(new_nodes) + 1)

        if node["id"] in existing_ids:
            continue

        # LLM enrich description
        node = _llm_enhance_node(node, t)

        # Wire connections (connect to last 2 nodes in existing pool)
        recent = [n["hostname"] for n in (existing + new_nodes)[-2:]]
        node["connections"] = recent

        new_nodes.append(node)
        existing_ids.add(node["id"])
        print(
            f"  Node: {node['hostname']} ({node['theme_name']}) — {node['description'][:60]}..."
        )

    if dry_run:
        print(f"[DRY-RUN] Would add {len(new_nodes)} nodes")
        return new_nodes

    all_nodes = existing + new_nodes
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(),
                "count": len(all_nodes),
                "nodes": all_nodes,
            },
            indent=2,
        )
    )
    print(
        f"  Saved {len(new_nodes)} new nodes ({len(all_nodes)} total) → {OUTPUT_FILE.relative_to(ROOT)}"
    )

    # Chronicle
    try:
        sys.path.insert(0, str(ROOT))
        from nusyq_bridge import chronicle

        chronicle(
            "nodes_generated",
            f"Added {len(new_nodes)} world nodes",
            tags=["game", "world", "generation"],
            metadata={
                "count": len(new_nodes),
                "themes": [n["theme"] for n in new_nodes],
            },
        )
    except Exception:
        pass

    return new_nodes


def main():
    dry_run = "--dry-run" in sys.argv
    count = 3
    theme = None
    for i, arg in enumerate(sys.argv):
        if arg == "--count" and i + 1 < len(sys.argv):
            count = int(sys.argv[i + 1])
        if arg == "--theme" and i + 1 < len(sys.argv):
            theme = sys.argv[i + 1]
    generate(count=count, theme=theme, dry_run=dry_run)


if __name__ == "__main__":
    main()
