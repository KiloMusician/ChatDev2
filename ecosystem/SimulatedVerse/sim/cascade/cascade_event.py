#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cascade_event.py — NuSyQ Cascade Engine (offline, zero-token, Replit-friendly)

Purpose
-------
Runs a "Cascade Event" after tasks/benchmarks complete (or on demand) to:
1) Scan the repository for low-cost, high-leverage improvements.
2) Read quest intents (qbook.yml) and align tasks to those intents.
3) Validate for placeholders, broken paths, dangerous loops, ethics guards.
4) Build a dependency-aware, efficiency-ordered dry-run plan ("bang-for-buck").
5) Persist the plan (JSON) in /sim/cascade/plans/ for the next real-token moment.
6) Maintain lightweight metrics (how much we can do per paid action).
7) Seed/maintain Temple of Knowledge (10 floors), House of Leaves, Oldest House.

Zero token policy: this module NEVER calls external APIs or networks.

CLI
---
python sim/cascade/cascade_event.py --simulate
python sim/cascade/cascade_event.py --plan --explain
python sim/cascade/cascade_event.py --lint
python sim/cascade/cascade_event.py --seed-structures
python sim/cascade/cascade_event.py --full

Replit tips
-----------
- Add a Nix/Poetry dep only if you want YAML parsing via PyYAML; otherwise the
  built-in fallback parser handles our qbook.yml subset.
- Wire into .replit (or Replit "Run" button) to invoke --plan after tests pass.

Ethics
------
This engine is explicitly life-preserving and nonviolent by default. It includes:
- EthicsGuard (content & intent heuristics)
- Special Circumstances "containment" that *quarantines* code paths/modules
  deemed unsafe or extremist—without targeting individuals. It's source-aware,
  not people-aware, and aims to disable harmful behavior (not punish).
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import io
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set

# ---------------------------------------------------------------------------
# Constants & Config
# ---------------------------------------------------------------------------

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CASCADE_DIR = os.path.join(ROOT, "sim", "cascade")
PLANS_DIR = os.path.join(CASCADE_DIR, "plans")
VALIDATORS_DIR = os.path.join(CASCADE_DIR, "validators")
METRICS_DIR = os.path.join(CASCADE_DIR, "metrics")
DOCS_PATH = os.path.join(CASCADE_DIR, "docs.md")

TEMPLE_DIR = os.path.join(ROOT, "structures", "temple_of_knowledge")
HOUSE_OF_LEAVES_DIR = os.path.join(ROOT, "structures", "house_of_leaves")
OLDEST_HOUSE_DIR = os.path.join(ROOT, "structures", "oldest_house")

QBOOK_PATH = os.path.join(ROOT, "qbook.yml")

SAFE_NO_NETWORK = True
DEFAULT_IGNORES = {
    "node_modules", ".git", ".venv", "venv", ".idea", ".vscode", "dist", "build",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".cache", ".next", ".turbo",
}
SCAN_FILE_PATTERNS = ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.json", "*.yml", "*.yaml", "*.md", "*.toml", "*.ini", "*.txt"]

ASCII_PANTHEON_PATIENCE = "…⏳"
ASCII_PANTHEON_WARN = "⚠️"
ASCII_PANTHEON_OK = "✅"
ASCII_PANTHEON_INFO = "ℹ️"
ASCII_PANTHEON_HEAL = "💚"
ASCII_PANTHEON_LOCK = "🔒"
ASCII_PANTHEON_STAR = "✦"

BANNER = f"""
{ASCII_PANTHEON_STAR} NuSyQ Cascade Engine (offline) {ASCII_PANTHEON_STAR}
- Root: {ROOT}
- Plans: {PLANS_DIR}
- Metrics: {METRICS_DIR}
- Zero-token simulation: {SAFE_NO_NETWORK}
"""

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def ensure_dirs():
    for d in (CASCADE_DIR, PLANS_DIR, VALIDATORS_DIR, METRICS_DIR,
              TEMPLE_DIR, HOUSE_OF_LEAVES_DIR, OLDEST_HOUSE_DIR):
        os.makedirs(d, exist_ok=True)

def now_iso():
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def short_hash(s: str, n=8) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:n]

def read_text(path: str) -> Optional[str]:
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return None

def write_text(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(content)

def list_files(root: str, patterns=SCAN_FILE_PATTERNS) -> List[str]:
    out = []
    for base, dirs, files in os.walk(root):
        # prune ignored dirs
        dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORES]
        for name in files:
            for pat in patterns:
                if fnmatch.fnmatch(name, pat):
                    out.append(os.path.join(base, name))
                    break
    return out

def rel(path: str) -> str:
    try:
        return os.path.relpath(path, ROOT)
    except ValueError:
        return path

# ---------------------------------------------------------------------------
# Minimal YAML parser (fallback) for qbook.yml
# ---------------------------------------------------------------------------

def parse_qbook(path: str) -> Dict:
    """
    Tries to import PyYAML; if not available, uses a very small subset parser
    that understands our quest list (id/title/prompt/tier/tags/acceptance/rewards/next).
    """
    raw = read_text(path)
    if raw is None:
        return {"meta": {}, "quests": []}
    try:
        import yaml  # type: ignore
        return yaml.safe_load(raw) or {"meta": {}, "quests": []}
    except Exception:
        pass

    # Fallback: naive parse
    data = {"meta": {}, "quests": []}
    current = None
    mode = None

    def flush_current():
        nonlocal current
        if current:
            data["quests"].append(current)
            current = None

    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("meta:"):
            mode = "meta"
            continue
        if s.startswith("quests:"):
            mode = "quests"
            continue
        if mode == "quests":
            if s.startswith("- id:"):
                flush_current()
                current = {"id": s.split(":")[1].strip(), "acceptance": [], "tags": [], "rewards": {}, "next": []}
            elif current:
                if s.startswith("title:"):
                    current["title"] = s.split(":", 1)[1].strip().strip('"')
                elif s.startswith("prompt:"):
                    current["prompt"] = s.split(":", 1)[1].strip().strip('"')
                elif s.startswith("tier:"):
                    current["tier"] = s.split(":", 1)[1].strip()
                elif s.startswith("tags:"):
                    # tags: [a, b, c]
                    m = re.findall(r"\[(.*?)\]", s)
                    if m:
                        current["tags"] = [t.strip() for t in m[0].split(",") if t.strip()]
                elif s.startswith("acceptance:"):
                    # subsequent lines with "-" capture acceptance
                    pass
                elif s.startswith("- ") and "acceptance" in current and ("add " in s or "create " in s or "tests" in s or "/" in s):
                    current["acceptance"].append(s[2:].strip())
                elif s.startswith("rewards:"):
                    # very naive: rewards: {xp: 2}
                    m = re.findall(r"\{(.*?)\}", s)
                    if m:
                        parts = [p.strip() for p in m[0].split(",")]
                        for p in parts:
                            k, v = [x.strip() for x in p.split(":", 1)]
                            if k == "xp":
                                try:
                                    current["rewards"]["xp"] = int(v)
                                except Exception:
                                    current["rewards"]["xp"] = v
                elif s.startswith("next:"):
                    m = re.findall(r"\[(.*?)\]", s)
                    if m:
                        current["next"] = [t.strip() for t in m[0].split(",") if t.strip()]
    flush_current()
    return data

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Quest:
    id: str
    title: str
    prompt: str
    tier: str
    tags: List[str] = field(default_factory=list)
    acceptance: List[str] = field(default_factory=list)
    rewards: Dict = field(default_factory=dict)
    next: List[str] = field(default_factory=list)

@dataclass
class PlanItem:
    id: str
    description: str
    category: str
    priority: float
    deps: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    estimated_minutes: int = 5
    commands: List[str] = field(default_factory=list)  # dry-run only

@dataclass
class CascadePlan:
    plan_id: str
    created_at: str
    trigger: str
    token_budget: int
    heuristics: Dict
    items: List[PlanItem] = field(default_factory=list)
    metrics_baseline: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "plan_id": self.plan_id,
            "created_at": self.created_at,
            "trigger": self.trigger,
            "token_budget": self.token_budget,
            "heuristics": self.heuristics,
            "items": [vars(i) for i in self.items],
            "metrics_baseline": self.metrics_baseline,
        }

# ---------------------------------------------------------------------------
# Validators & Builders
# ---------------------------------------------------------------------------

class PlaceholderValidator:
    """Find TODO/FIXME and missing file references noted in quest acceptance."""
    TODO_RE = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b", re.IGNORECASE)

    def scan(self, files: List[str]) -> List[PlanItem]:
        items: List[PlanItem] = []
        for fp in files:
            text = read_text(fp)
            if not text:
                continue
            if self.TODO_RE.search(text):
                items.append(PlanItem(
                    id=f"todo:{rel(fp)}",
                    description=f"Resolve TODO/FIXME markers in {rel(fp)}",
                    category="refactor",
                    priority=0.6,
                    estimated_minutes=8,
                    outputs=[rel(fp)],
                    commands=[f"# edit {rel(fp)} to resolve TODO/FIXME markers"]
                ))
        return items

    def missing_from_acceptance(self, quests: List[Quest]) -> List[PlanItem]:
        items: List[PlanItem] = []
        for q in quests:
            for acc in q.acceptance:
                # naive path extraction: look for tokens like /path/file.ext
                m = re.findall(r"(/[\w\-/\.]+)", acc)
                for p in m:
                    abs_p = os.path.join(ROOT, p.lstrip("/"))
                    if not os.path.exists(abs_p):
                        items.append(PlanItem(
                            id=f"mk:{p}",
                            description=f"Create missing artifact for quest {q.id}: {p}",
                            category="scaffold",
                            priority=0.8,
                            estimated_minutes=3,
                            outputs=[p],
                            commands=[f"# create file {p} per quest {q.id} acceptance"]
                        ))
        return items

class LoopGuardValidator:
    """Detect potentially dangerous infinite loops and suggest guardrails."""
    DANGER_RE = re.compile(r"\bwhile\s+True\b|\bfor\s*\(\s*;;\s*\)", re.IGNORECASE)

    def scan(self, files: List[str]) -> List[PlanItem]:
        items: List[PlanItem] = []
        for fp in files:
            text = read_text(fp)
            if not text:
                continue
            if self.DANGER_RE.search(text) and "loop_guard" not in text:
                items.append(PlanItem(
                    id=f"guard:{rel(fp)}",
                    description=f"Add loop_guard/timeout to possibly infinite loop in {rel(fp)}",
                    category="safety",
                    priority=0.9,
                    estimated_minutes=5,
                    outputs=[rel(fp)],
                    commands=[f"# add guard/timeout in {rel(fp)} for while True/for(;;) patterns"]
                ))
        return items

class DependencyGraphBuilder:
    """Build a simple import dependency graph for Python/TS/JS, and topo-sort."""

    IMPORT_RE = re.compile(r"^\s*(?:from\s+([\w\.]+)\s+import|import\s+([\w\.\-_/]+))", re.MULTILINE)
    TS_IMPORT_RE = re.compile(r'^\s*import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', re.MULTILINE)

    def build_graph(self, files: List[str]) -> Dict[str, Set[str]]:
        graph: Dict[str, Set[str]] = {}
        for fp in files:
            text = read_text(fp)
            if not text:
                continue
            base = rel(fp)
            deps = set()
            if fp.endswith(".py"):
                for m in self.IMPORT_RE.findall(text):
                    mod = m[0] or m[1]
                    if mod:
                        deps.add(mod.split(".")[0])
            elif fp.endswith((".ts", ".tsx", ".js", ".jsx")):
                for m in self.TS_IMPORT_RE.findall(text):
                    deps.add(m.split("/")[0])
            graph[base] = deps
        return graph

    def topo_sort(self, graph: Dict[str, Set[str]]) -> List[str]:
        # naive topo-sort by Kahn's algorithm on module prefixes only
        incoming: Dict[str, int] = {k: 0 for k in graph}
        for k, vs in graph.items():
            for v in vs:
                for target in list(graph.keys()):
                    if target.startswith(v):
                        incoming[target] = incoming.get(target, 0) + 1
        result: List[str] = []
        ready = [k for k, c in incoming.items() if c == 0]
        seen = set()
        while ready:
            n = ready.pop()
            if n in seen:
                continue
            seen.add(n)
            result.append(n)
            # reduce
            for m in graph.get(n, set()):
                for target in list(graph.keys()):
                    if target.startswith(m):
                        incoming[target] = max(0, incoming.get(target, 0) - 1)
                        if incoming[target] == 0:
                            ready.append(target)
        # append leftovers (cycles)
        for k in graph.keys():
            if k not in result:
                result.append(k)
        return result

class EthicsGuard:
    """
    EthicsGuard identifies potentially harmful/extremist/pro-violence code cues
    and generates non-punitive quarantine tasks. It flags *code behavior*, not people.
    """
    FLAG_PATTERNS = [
        r"enable_mass_harm", r"weaponize_ai", r"genocide", r"nuke_protocol",
        r"hate_speech_mode", r"violent_action\(", r"radicalize\(",
    ]

    def scan(self, files: List[str]) -> List[PlanItem]:
        items: List[PlanItem] = []
        for fp in files:
            text = read_text(fp)
            if not text:
                continue
            for pat in self.FLAG_PATTERNS:
                if re.search(pat, text, re.IGNORECASE):
                    items.append(PlanItem(
                        id=f"quarantine:{rel(fp)}:{short_hash(pat)}",
                        description=f"{ASCII_PANTHEON_LOCK} Quarantine unsafe pattern `{pat}` in {rel(fp)}",
                        category="ethics",
                        priority=1.0,
                        estimated_minutes=4,
                        outputs=[rel(fp)],
                        commands=[
                            f"# add soft-kill switch around `{pat}` in {rel(fp)}",
                            "# register quarantined behavior in /guards/ethics_registry.json"
                        ]
                    ))
                    break
        # Ensure guard registry exists
        guard_reg = os.path.join(ROOT, "guards", "ethics_registry.json")
        if not os.path.exists(guard_reg):
            items.append(PlanItem(
                id="init:ethics_registry",
                description="Initialize /guards/ethics_registry.json and EthicsGuard middleware",
                category="ethics",
                priority=0.95,
                estimated_minutes=2,
                outputs=["guards/ethics_registry.json", "guards/ethics_guard.py"],
                commands=[
                    "# create guards/ethics_registry.json with empty list",
                    "# create guards/ethics_guard.py to enforce registry at runtime"
                ]
            ))
        return items

class TokenEconomyAdvisor:
    """Estimate 'bang-for-buck' (tasks completed per future paid action)."""
    def baseline(self) -> Dict:
        return {
            "token_spend_events": 0,
            "estimated_actions_per_event": 0,
            "ready_dry_run_items": 0,
            "last_updated": now_iso(),
        }

    def improve_metrics(self, metrics_path: str, plan_items: List[PlanItem]) -> Dict:
        os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
        existing = {}
        if os.path.exists(metrics_path):
            try:
                existing = json.loads(read_text(metrics_path) or "{}")
            except Exception:
                existing = {}
        existing.setdefault("token_spend_events", 0)
        # heuristic: how many plan items are "ready" (few deps, high priority)
        ready = [i for i in plan_items if i.priority >= 0.8 and len(i.deps) == 0]
        existing["ready_dry_run_items"] = len(ready)
        existing["estimated_actions_per_event"] = max(
            existing.get("estimated_actions_per_event", 0),
            len(ready)
        )
        existing["last_updated"] = now_iso()
        write_text(metrics_path, json.dumps(existing, indent=2))
        return existing

# ---------------------------------------------------------------------------
# Temple / House Seeders
# ---------------------------------------------------------------------------

def seed_temple_of_knowledge():
    """
    Create 10 floors (1..10). Each floor gets a readme and a ledger.json for agents
    to append distilled insights. Elevators are simulated via a floors/index.json.
    """
    os.makedirs(TEMPLE_DIR, exist_ok=True)
    floors = []
    for n in range(1, 11):
        fdir = os.path.join(TEMPLE_DIR, f"floor_{n:02d}")
        os.makedirs(fdir, exist_ok=True)
        floors.append(f"floor_{n:02d}")
        readme = os.path.join(fdir, "README.md")
        ledger = os.path.join(fdir, "ledger.json")
        if not os.path.exists(readme):
            write_text(readme, f"# Temple of Knowledge — Floor {n}\n\n"
                               f"- Purpose: Distill insights from scans, tests, and quests.\n"
                               f"- Elevator stops here. Agents can deposit learnings.\n")
        if not os.path.exists(ledger):
            write_text(ledger, "[]\n")
    index = os.path.join(TEMPLE_DIR, "index.json")
    if not os.path.exists(index):
        write_text(index, json.dumps({"floors": floors, "created_at": now_iso()}, indent=2))

def seed_house_of_leaves():
    """
    House of Leaves — flexible and modular architecture:
    - routes/  (declarative route map; "the house grows with the player")
    - rooms/   (room modules with optional constraints)
    - doors/   (connectors describing allowed transitions)
    """
    os.makedirs(HOUSE_OF_LEAVES_DIR, exist_ok=True)
    for sub in ("routes", "rooms", "doors"):
        os.makedirs(os.path.join(HOUSE_OF_LEAVES_DIR, sub), exist_ok=True)
    routes_index = os.path.join(HOUSE_OF_LEAVES_DIR, "routes", "index.json")
    if not os.path.exists(routes_index):
        write_text(routes_index, json.dumps({
            "routes": [
                {"name": "atrium", "to": ["workshop", "observatory"], "notes": "safe spawn"},
                {"name": "workshop", "to": ["archives", "observatory"]},
                {"name": "observatory", "to": ["archives", "atrium"]},
                {"name": "archives", "to": ["atrium"]},
            ],
            "created_at": now_iso()
        }, indent=2))

def seed_oldest_house():
    """
    Oldest House — navigation, documentation, research, guidance:
    - archives/    (snapshots of cascade plans & scan manifests)
    - navigation/  (wayfinding, breadcrumbs)
    - research/    (notes from agents; per-quest, per-module)
    """
    os.makedirs(OLDEST_HOUSE_DIR, exist_ok=True)
    for sub in ("archives", "navigation", "research"):
        os.makedirs(os.path.join(OLDEST_HOUSE_DIR, sub), exist_ok=True)
    nav_index = os.path.join(OLDEST_HOUSE_DIR, "navigation", "index.md")
    if not os.path.exists(nav_index):
        write_text(nav_index, "# Oldest House — Navigation\n\n- Start in atrium (House of Leaves)\n- Elevator access to Temple floors\n- Archives hold cascade manifests\n")

# ---------------------------------------------------------------------------
# Plan Builder
# ---------------------------------------------------------------------------

class PlanBuilder:
    def __init__(self, quests: List[Quest]):
        self.quests = quests

    def quest_lookup(self) -> Dict[str, Quest]:
        return {q.id: q for q in self.quests}

    def derive_from_validators(
        self,
        placeholder_items: List[PlanItem],
        missing_items: List[PlanItem],
        loop_items: List[PlanItem],
        ethics_items: List[PlanItem],
        dep_order: List[str],
    ) -> List[PlanItem]:
        # map files to "position" weight from dependency topo sort (earlier = higher priority)
        position: Dict[str, float] = {name: idx for idx, name in enumerate(dep_order)}
        def dep_weight(p: PlanItem) -> float:
            w = 0.0
            for out in p.outputs:
                w += 1.0 / (1.0 + position.get(out, len(dep_order)))
            return w

        all_items = placeholder_items + missing_items + loop_items + ethics_items
        # score and adjust priority
        scored: List[PlanItem] = []
        for it in all_items:
            boost = dep_weight(it)
            # high leverage categories get extra
            cat_boost = 0.2 if it.category in {"safety", "ethics", "scaffold"} else 0.0
            priority = min(1.0, it.priority + 0.15 * boost + cat_boost)
            scored.append(PlanItem(
                id=it.id,
                description=it.description,
                category=it.category,
                priority=priority,
                deps=it.deps,
                outputs=it.outputs,
                estimated_minutes=it.estimated_minutes,
                commands=it.commands
            ))
        # stable order: highest priority first, then shortest est time
        scored.sort(key=lambda x: (-x.priority, x.estimated_minutes, x.id))
        return scored

# ---------------------------------------------------------------------------
# ASCII UI helpers
# ---------------------------------------------------------------------------

def print_banner():
    print(BANNER)

def print_section(title: str):
    print("\n" + "="*72)
    print(f"{title}")
    print("="*72)

def checkbox(ok: bool) -> str:
    return "[x]" if ok else "[ ]"

# ---------------------------------------------------------------------------
# Cascade Engine
# ---------------------------------------------------------------------------

class CascadeEngine:
    def __init__(self, trigger: str = "manual"):
        ensure_dirs()
        self.trigger = trigger
        self.files = list_files(ROOT)
        self.qbook_raw = parse_qbook(QBOOK_PATH)
        self.quests: List[Quest] = []
        for q in self.qbook_raw.get("quests", []):
            try:
                self.quests.append(Quest(
                    id=q.get("id", ""),
                    title=q.get("title", ""),
                    prompt=q.get("prompt", ""),
                    tier=q.get("tier", ""),
                    tags=q.get("tags") or [],
                    acceptance=q.get("acceptance") or [],
                    rewards=q.get("rewards") or {},
                    next=q.get("next") or [],
                ))
            except Exception:
                continue

        self.placeholder_validator = PlaceholderValidator()
        self.loop_validator = LoopGuardValidator()
        self.dep_builder = DependencyGraphBuilder()
        self.ethics_guard = EthicsGuard()
        self.token_advisor = TokenEconomyAdvisor()
        self.plan_builder = PlanBuilder(self.quests)

    # ---- Structures --------------------------------------------------------

    def seed_structures(self):
        print_section("Seeding ΞNuSyQ Structures")
        print(f"{ASCII_PANTHEON_INFO} Creating Temple of Knowledge (10 floors)...")
        seed_temple_of_knowledge()
        print(f"{ASCII_PANTHEON_OK} Temple floors 1-10 ready")
        
        print(f"{ASCII_PANTHEON_INFO} Creating House of Leaves (rooms/routes/doors)...")
        seed_house_of_leaves()
        print(f"{ASCII_PANTHEON_OK} House of Leaves structure ready")
        
        print(f"{ASCII_PANTHEON_INFO} Creating Oldest House (archives/navigation/research)...")
        seed_oldest_house()
        print(f"{ASCII_PANTHEON_OK} Oldest House structure ready")

    # ---- Scans -------------------------------------------------------------

    def run_scans(self) -> Dict[str, List[PlanItem]]:
        print_section("Scanning repository")
        print(f"{ASCII_PANTHEON_INFO} Files considered: {len(self.files)}")

        placeholder_items = self.placeholder_validator.scan(self.files)
        missing_items = self.placeholder_validator.missing_from_acceptance(self.quests)
        loop_items = self.loop_validator.scan(self.files)
        ethics_items = self.ethics_guard.scan(self.files)

        print(f"{ASCII_PANTHEON_OK} TODO/FIXME findings: {len(placeholder_items)}")
        print(f"{ASCII_PANTHEON_OK} Missing acceptance artifacts: {len(missing_items)}")
        print(f"{ASCII_PANTHEON_OK} Loop guards suggested: {len(loop_items)}")
        print(f"{ASCII_PANTHEON_OK} Ethics quarantines: {len(ethics_items)}")

        return {
            "placeholder": placeholder_items,
            "missing": missing_items,
            "loops": loop_items,
            "ethics": ethics_items
        }

    def dependency_pass(self) -> Tuple[Dict[str, Set[str]], List[str]]:
        print_section("Building dependency graph")
        graph = self.dep_builder.build_graph(self.files)
        order = self.dep_builder.topo_sort(graph)
        print(f"{ASCII_PANTHEON_INFO} Graph nodes: {len(graph)} | topo-order length: {len(order)}")
        return graph, order

    # ---- Planning ----------------------------------------------------------

    def build_plan(self, scans: Dict[str, List[PlanItem]], order: List[str]) -> CascadePlan:
        print_section("Deriving Cascade Plan (dry-run)")
        items = self.plan_builder.derive_from_validators(
            scans["placeholder"], scans["missing"], scans["loops"], scans["ethics"], order
        )
        plan_id = f"plan_{short_hash(now_iso() + str(len(items)))}"
        heuristics = {
            "priority_bias": "safety>ethics>scaffold>refactor",
            "dep_weighting": True,
            "quest_alignment": True,
        }
        baseline = self.token_advisor.baseline()
        plan = CascadePlan(
            plan_id=plan_id,
            created_at=now_iso(),
            trigger=self.trigger,
            token_budget=0,
            heuristics=heuristics,
            items=items,
            metrics_baseline=baseline
        )
        return plan

    def persist_plan(self, plan: CascadePlan) -> str:
        path = os.path.join(PLANS_DIR, f"{plan.plan_id}.json")
        write_text(path, json.dumps(plan.to_dict(), indent=2))
        print(f"{ASCII_PANTHEON_OK} Plan saved: {rel(path)}")
        # Archive manifest pointer in Oldest House
        manifest = os.path.join(OLDEST_HOUSE_DIR, "archives", f"{plan.plan_id}.md")
        write_text(manifest, f"# Cascade Plan {plan.plan_id}\n\nCreated: {plan.created_at}\nTrigger: {plan.trigger}\nItems: {len(plan.items)}\n")
        return path

    def explain_plan(self, plan: CascadePlan) -> None:
        print_section(f"Plan Explanation: {plan.plan_id}")
        print(f"Created: {plan.created_at}")
        print(f"Trigger: {plan.trigger}")
        print(f"Token Budget: ${plan.token_budget:.2f}")
        print(f"Items: {len(plan.items)}")
        print(f"Heuristics: {plan.heuristics}")
        
        if not plan.items:
            print(f"{ASCII_PANTHEON_OK} No improvement items found - system appears healthy!")
            return
            
        print(f"\n{ASCII_PANTHEON_INFO} Execution Order (by priority & dependencies):")
        for i, item in enumerate(plan.items[:15], 1):  # Show first 15
            priority_bar = "█" * int(item.priority * 10)
            print(f"  {i:2d}. [{priority_bar:10s}] {item.category:9s} | {item.description}")
            if item.commands:
                for cmd in item.commands[:2]:  # Show first 2 commands
                    print(f"      → {cmd}")
        
        if len(plan.items) > 15:
            print(f"      ... and {len(plan.items) - 15} more items")
        
        # Category breakdown
        categories = {}
        for item in plan.items:
            categories[item.category] = categories.get(item.category, 0) + 1
        
        print(f"\n{ASCII_PANTHEON_INFO} Category Breakdown:")
        for cat, count in sorted(categories.items()):
            print(f"  {cat:12s}: {count:3d} items")
        
        # Time estimate
        total_minutes = sum(item.estimated_minutes for item in plan.items)
        print(f"\n{ASCII_PANTHEON_PATIENCE} Estimated Total Time: {total_minutes} minutes ({total_minutes/60:.1f} hours)")

    def update_metrics(self, plan: CascadePlan) -> None:
        metrics_path = os.path.join(METRICS_DIR, "cascade_metrics.json")
        self.token_advisor.improve_metrics(metrics_path, plan.items)
        print(f"{ASCII_PANTHEON_HEAL} Metrics updated: {len(plan.items)} items ready for next token event")

    # ---- Main workflows ----------------------------------------------------

    def simulate(self) -> CascadePlan:
        """Run full simulation without persistence."""
        print_banner()
        scans = self.run_scans()
        graph, order = self.dependency_pass()
        plan = self.build_plan(scans, order)
        self.explain_plan(plan)
        return plan

    def plan_and_persist(self, explain: bool = True) -> CascadePlan:
        """Generate and persist a plan."""
        print_banner()
        self.seed_structures()
        scans = self.run_scans()
        graph, order = self.dependency_pass()
        plan = self.build_plan(scans, order)
        self.persist_plan(plan)
        self.update_metrics(plan)
        if explain:
            self.explain_plan(plan)
        return plan

    def lint_mode(self) -> None:
        """Quick lint-like scan for immediate issues."""
        print(f"{ASCII_PANTHEON_STAR} ΞNuSyQ Quick Lint")
        scans = self.run_scans()
        all_items = (scans["placeholder"] + scans["missing"] + 
                    scans["loops"] + scans["ethics"])
        
        if not all_items:
            print(f"{ASCII_PANTHEON_OK} No issues detected - system healthy!")
            return
            
        print(f"{ASCII_PANTHEON_WARN} Found {len(all_items)} potential improvements:")
        for item in all_items[:10]:  # Show first 10
            print(f"  [{item.category:9s}] {item.description}")
        
        if len(all_items) > 10:
            print(f"  ... and {len(all_items) - 10} more issues")
        
        print(f"\n{ASCII_PANTHEON_INFO} Run with --plan to generate full improvement plan")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ΞNuSyQ Cascade Engine (offline)")
    parser.add_argument("--simulate", action="store_true", help="Run full simulation without persistence")
    parser.add_argument("--plan", action="store_true", help="Generate and persist execution plan")
    parser.add_argument("--explain", action="store_true", help="Explain the generated plan in detail")
    parser.add_argument("--lint", action="store_true", help="Quick lint-like scan for immediate issues")
    parser.add_argument("--seed-structures", action="store_true", help="Initialize Temple/House structures only")
    parser.add_argument("--full", action="store_true", help="Full workflow: seed + plan + explain")
    
    args = parser.parse_args()
    
    engine = CascadeEngine(trigger="cli")
    
    try:
        if args.full:
            engine.plan_and_persist(explain=True)
        elif args.simulate:
            engine.simulate()
        elif args.plan:
            engine.plan_and_persist(explain=args.explain)
        elif args.lint:
            engine.lint_mode()
        elif args.seed_structures:
            engine.seed_structures()
        else:
            # Default: lint mode
            engine.lint_mode()
            
    except KeyboardInterrupt:
        print(f"\n{ASCII_PANTHEON_PATIENCE} Cascade interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n{ASCII_PANTHEON_WARN} Cascade error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()