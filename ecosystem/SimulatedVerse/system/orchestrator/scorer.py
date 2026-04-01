from __future__ import annotations
from typing import List, Dict, Tuple
from .task_types import Task
from .module_index import count_todos, detect_duplicates, fuzzy_exists, git_dirty_files

def score_task(task: Task, weights: Dict, roots: Dict) -> Tuple[float, List[str], str]:
    reasons: List[str] = []
    s = 0.0
    action = task.kind

    # Prefer improving what exists
    targets_exist = any(fuzzy_exists(t, roots.get("module_roots", [])) for t in task.targets)
    if targets_exist:
        s += weights.get("improve_existing_module", 0); reasons.append("improve_existing_module")
    else:
        s += weights.get("new_module", 0); reasons.append("new_module")

    # Error & placeholder pressure
    todo_count = count_todos(roots.get("module_roots", []))
    if task.kind in ("fix","complete") and todo_count>0:
        s += weights.get("fix_errors" if task.kind=="fix" else "complete_placeholders", 0)
        reasons.append(f"{task.kind}_pressure({todo_count})")

    # Dedup pressure
    dup = detect_duplicates(roots.get("module_roots", []))
    if task.kind in ("refactor","fix") and dup:
        s += weights.get("reduce_duplication", 0); reasons.append("reduce_duplication")

    # Test encouragement if dirty
    if task.kind in ("test","fix","refactor"):
        if git_dirty_files():
            s += weights.get("add_tests_for_changed_code", 0); reasons.append("tests_for_changed_code")

    # Docs are welcome but not blocking
    if task.kind == "docs":
        s += weights.get("docs_and_examples", 0); reasons.append("docs_and_examples")

    # Performance tasks get micro boost
    if task.kind == "perf":
        s += weights.get("performance_micro", 0); reasons.append("performance_micro")

    # ΞNuSyQ-specific boosts
    if any("consciousness" in t.lower() or "temple" in t.lower() for t in task.targets):
        s += 1.0; reasons.append("core_consciousness_system")
    
    if any("guardian" in t.lower() or "containment" in t.lower() for t in task.targets):
        s += 0.8; reasons.append("guardian_ethics_system")
    
    # 123 Mechanics tier prioritization
    if "m00" in " ".join(task.targets):  # Tier I foundations
        s += 1.5; reasons.append("tier_I_foundation_mechanics")
    elif "m02" in " ".join(task.targets):  # Tier II expansion 
        s += 1.0; reasons.append("tier_II_expansion_mechanics")
    elif "m04" in " ".join(task.targets):  # Tier III defense
        s += 0.8; reasons.append("tier_III_defense_mechanics")
    
    # ASCII/UI systems get mobile-responsive bonus
    if any("ascii" in t.lower() or "ui" in t.lower() for t in task.targets):
        s += 0.5; reasons.append("mobile_responsive_ui_priority")

    # Adjust action when needed
    if task.kind=="refactor" and not targets_exist:
        action = "survey_then_refactor"  # guardrail

    return s, reasons, action