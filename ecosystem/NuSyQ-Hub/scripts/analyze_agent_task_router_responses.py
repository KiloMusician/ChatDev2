"""Analyze AgentTaskRouter response shapes, delegation paths, and health.

This script inspects ``src/tools/agent_task_router.py`` and produces:

- Per-route handler response key maps.
- Delegation edges between handlers.
- A joined delegation matrix with probe health and terminal awareness.
- A markdown summary for operator review.

Usage:
    python scripts/analyze_agent_task_router_responses.py

Outputs:
    state/reports/agent_task_router_analysis.json
    state/reports/agent_delegation_matrix.json
    state/reports/agent_delegation_matrix.md
"""

from __future__ import annotations

import ast
import json
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ROUTER_PATH = ROOT / "src" / "tools" / "agent_task_router.py"
REPORT_DIR = ROOT / "state" / "reports"
ANALYSIS_JSON_PATH = REPORT_DIR / "agent_task_router_analysis.json"
MATRIX_JSON_PATH = REPORT_DIR / "agent_delegation_matrix.json"
MATRIX_MD_PATH = REPORT_DIR / "agent_delegation_matrix.md"
PROBE_PATH = REPORT_DIR / "agent_probe_status.json"
REGISTRY_PATH = REPORT_DIR / "agent_registry_probe.json"
TERMINAL_PATH = REPORT_DIR / "terminal_awareness_latest.json"

CANONICAL_SCHEMA_KEYS = [
    "status",
    "system",
    "task_id",
    "execution_path",
    "delegated_from",
    "delegated_to",
    "output",
    "error",
    "suggestion",
    "handoff",
]

ROUTER_RUNTIME_GUARANTEED_KEYS = [
    "status",
    "system",
    "task_id",
]

PROBE_ALIASES: dict[str, list[str]] = {
    "ollama": ["ollama"],
    "ollama_adapter": ["ollama"],
    "lmstudio": ["lmstudio"],
    "chatdev": ["chatdev"],
    "openclaw": ["openclaw"],
    "mcp_server": ["mcp_server"],
}

TERMINAL_ALIASES: dict[str, str] = {
    "claude_cli": "claude",
    "ollama_adapter": "ollama",
    "quantum_resolver": "tasks",
    "consciousness": "culture_ship",
    "factory": "tasks",
    "intermediary": "agents",
    "devtool": "agents",
    "gitkraken": "agents",
    "huggingface": "agents",
    "dbclient": "agents",
    "neural_ml": "agents",
    "openclaw": "agents",
    "skyclaw": "agents",
}


def _get_constant_str(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


class RouterAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.handlers: dict[str, dict[str, Any]] = {}

    def _process_route_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if not node.name.startswith("_route_to_"):
            return
        keys: set[str] = set()
        calls: set[str] = set()

        for child in ast.walk(node):
            if isinstance(child, ast.Return) and isinstance(child.value, ast.Dict):
                for key_node in child.value.keys:
                    key_text = _get_constant_str(key_node)
                    if key_text:
                        keys.add(key_text)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                if isinstance(child.func.value, ast.Name) and child.func.value.id == "self":
                    attr = child.func.attr
                    if attr.startswith("_route_to_"):
                        calls.add(attr)

        self.handlers[node.name] = {
            "return_keys": sorted(keys),
            "delegates_to": sorted(calls),
        }

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._process_route_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._process_route_function(node)
        self.generic_visit(node)


def _system_from_handler(handler_name: str) -> str:
    return handler_name.removeprefix("_route_to_")


def _pick_probe(system_name: str, probes: dict[str, Any]) -> dict[str, Any] | None:
    for candidate in PROBE_ALIASES.get(system_name, [system_name]):
        probe = probes.get(candidate)
        if isinstance(probe, dict):
            return probe
    return None


def _probe_ok(probe: dict[str, Any] | None) -> bool | None:
    if not isinstance(probe, dict):
        return None
    explicit_ok = probe.get("ok")
    if isinstance(explicit_ok, bool):
        return explicit_ok
    status_text = str(probe.get("status", "")).strip().lower()
    registry_text = str(probe.get("registry_status", "")).strip().lower()
    if status_text in {"ok", "online", "healthy"}:
        return True
    if registry_text in {"online", "healthy"}:
        return True
    if status_text in {"error", "offline", "failed", "degraded"}:
        return False
    return None


def _pick_terminal(system_name: str, terminals: list[dict[str, Any]]) -> dict[str, Any] | None:
    terminal_key = TERMINAL_ALIASES.get(system_name, system_name)
    for terminal in terminals:
        if isinstance(terminal, dict) and terminal.get("key") == terminal_key:
            return terminal
    return None


def _find_registry_entries(system_name: str, registry_agents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    tokens = {
        system_name.lower(),
        system_name.replace("_cli", "").lower(),
        system_name.replace("_adapter", "").lower(),
    }
    for agent in registry_agents:
        if not isinstance(agent, dict):
            continue
        haystacks = [
            str(agent.get("id", "")).lower(),
            str(agent.get("name", "")).lower(),
            str(agent.get("runtime", "")).lower(),
        ]
        if any(token and token in hay for token in tokens for hay in haystacks):
            matches.append(agent)
    return matches


def _build_matrix(handlers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    probe_report = _read_json(PROBE_PATH)
    registry_report = _read_json(REGISTRY_PATH)
    terminal_report = _read_json(TERMINAL_PATH)

    probes = probe_report.get("probes", {}) if isinstance(probe_report.get("probes"), dict) else {}
    registry_agents = registry_report.get("agents", [])
    terminals = terminal_report.get("terminals", [])
    terminal_list = terminals if isinstance(terminals, list) else []

    entries: list[dict[str, Any]] = []
    router_runtime_guaranteed = "def _normalize_response_contract" in ROUTER_PATH.read_text(encoding="utf-8")
    for handler_name, details in sorted(handlers.items()):
        system_name = _system_from_handler(handler_name)
        return_keys = list(details.get("return_keys", []))
        effective_keys = sorted(
            set(return_keys) | (set(ROUTER_RUNTIME_GUARANTEED_KEYS) if router_runtime_guaranteed else set())
        )
        delegates_to = [_system_from_handler(name) for name in details.get("delegates_to", []) if isinstance(name, str)]
        probe = _pick_probe(system_name, probes)
        terminal = _pick_terminal(system_name, terminal_list)
        registry_matches = _find_registry_entries(
            system_name, registry_agents if isinstance(registry_agents, list) else []
        )
        missing_schema_keys = [key for key in CANONICAL_SCHEMA_KEYS if key not in return_keys]

        entry = {
            "handler": handler_name,
            "system": system_name,
            "return_keys": return_keys,
            "schema_coverage": {
                "present": [key for key in CANONICAL_SCHEMA_KEYS if key in return_keys],
                "missing": missing_schema_keys,
                "has_execution_path": "execution_path" in return_keys,
                "runtime_present": [key for key in CANONICAL_SCHEMA_KEYS if key in effective_keys],
                "runtime_missing": [key for key in CANONICAL_SCHEMA_KEYS if key not in effective_keys],
            },
            "delegates_to": delegates_to,
            "probe": {
                "available": probe is not None,
                "ok": _probe_ok(probe),
                "latency_ms": probe.get("latency_ms") if isinstance(probe, dict) else None,
                "details": probe,
            },
            "terminal": {
                "available": terminal is not None,
                "key": terminal.get("key") if isinstance(terminal, dict) else None,
                "observed_in_runtime": terminal.get("observed_in_runtime") if isinstance(terminal, dict) else None,
                "configured_in_session": terminal.get("configured_in_session") if isinstance(terminal, dict) else None,
                "configured_in_orchestrator": terminal.get("configured_in_orchestrator")
                if isinstance(terminal, dict)
                else None,
                "log_path": terminal.get("log_path") if isinstance(terminal, dict) else None,
            },
            "registry_matches": [
                {
                    "name": match.get("name"),
                    "runtime": match.get("runtime"),
                    "status": match.get("status"),
                    "capability_count": len(match.get("capabilities", []))
                    if isinstance(match.get("capabilities"), list)
                    else 0,
                }
                for match in registry_matches
            ],
        }
        entries.append(entry)

    execution_path_ready = [entry["system"] for entry in entries if entry["schema_coverage"]["has_execution_path"]]
    delegated_edges = [{"from": entry["system"], "to": target} for entry in entries for target in entry["delegates_to"]]
    matrix = {
        "generated_at": _iso_now(),
        "router_file": str(ROUTER_PATH),
        "canonical_schema_keys": CANONICAL_SCHEMA_KEYS,
        "router_runtime_guaranteed_keys": ROUTER_RUNTIME_GUARANTEED_KEYS if router_runtime_guaranteed else [],
        "summary": {
            "handler_count": len(entries),
            "delegation_edge_count": len(delegated_edges),
            "execution_path_ready_count": len(execution_path_ready),
            "execution_path_ready_systems": execution_path_ready,
            "probe_sources": sorted(probes.keys()),
            "router_runtime_contract_enabled": router_runtime_guaranteed,
        },
        "delegation_edges": delegated_edges,
        "entries": entries,
    }
    return matrix


def _build_markdown(matrix: dict[str, Any]) -> str:
    lines = [
        "# Agent Delegation Matrix",
        "",
        f"Generated: {matrix.get('generated_at')}",
        "",
        "## Summary",
        "",
        f"- Handlers analyzed: {matrix.get('summary', {}).get('handler_count')}",
        f"- Delegation edges: {matrix.get('summary', {}).get('delegation_edge_count')}",
        f"- Systems exposing `execution_path`: {matrix.get('summary', {}).get('execution_path_ready_count')}",
        "",
        "## Systems",
        "",
        "| System | Delegates To | Probe OK | Terminal Runtime | Missing Schema Keys |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in matrix.get("entries", []):
        delegates = ", ".join(entry.get("delegates_to") or ["-"])
        probe_ok = entry.get("probe", {}).get("ok")
        probe_text = "yes" if probe_ok is True else "no" if probe_ok is False else "n/a"
        runtime = entry.get("terminal", {}).get("observed_in_runtime")
        runtime_text = "yes" if runtime is True else "no" if runtime is False else "n/a"
        missing = ", ".join(entry.get("schema_coverage", {}).get("missing", [])[:6]) or "-"
        lines.append(f"| {entry.get('system')} | {delegates} | {probe_text} | {runtime_text} | {missing} |")

    lines.extend(
        [
            "",
            "## Delegation Edges",
            "",
        ]
    )
    for edge in matrix.get("delegation_edges", []):
        lines.append(f"- `{edge.get('from')}` -> `{edge.get('to')}`")
    if not matrix.get("delegation_edges"):
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    src = ROUTER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(src)
    analyzer = RouterAnalyzer()
    analyzer.visit(tree)

    analysis_report = {
        "router_file": str(ROUTER_PATH),
        "analyzed_at": _iso_now(),
        "handlers": analyzer.handlers,
    }
    matrix_report = _build_matrix(analyzer.handlers)
    markdown_report = _build_markdown(matrix_report)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_JSON_PATH.write_text(json.dumps(analysis_report, indent=2), encoding="utf-8")
    MATRIX_JSON_PATH.write_text(json.dumps(matrix_report, indent=2), encoding="utf-8")
    MATRIX_MD_PATH.write_text(markdown_report, encoding="utf-8")

    print(json.dumps(matrix_report, indent=2))


if __name__ == "__main__":
    main()
