#!/usr/bin/env python3
"""🔍 VSCode Tools vs System Capabilities Cross-Reference Analyzer.

Compares available VSCode Copilot tools (228 from user interface) with system capabilities (403 discovered).

OmniTag: {
    "purpose": "tool_capability_analysis",
    "type": "diagnostic_cross_reference",
    "evolution_stage": "v1.0"
}
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_jsonc(path: Path) -> dict:
    """Load JSON file that may contain comment lines."""
    raw = path.read_text(encoding="utf-8")
    cleaned = "\n".join(line for line in raw.splitlines() if not line.strip().startswith("//"))
    return json.loads(cleaned)


def analyze_capability_inventory():
    """Analyze the system capability inventory."""
    inventory_path = Path("data/system_capability_inventory.json")

    if not inventory_path.exists():
        return None

    with open(inventory_path) as f:
        data = json.load(f)

    data.get("total_capabilities", 0)
    data.get("system_stats", {})
    capabilities = data.get("capabilities", {})

    # Analyze action categories
    actions = capabilities.get("actions", {})
    for _category, _items in actions.items():
        pass

    return data


def enumerate_vscode_tools():
    """Enumerate VSCode Copilot tools based on known categories.

    User reports 228 tools available.
    """
    # Known tool categories from workspace context
    tool_categories = {
        "File Operations": [
            "create_file",
            "read_file",
            "replace_string_in_file",
            "create_directory",
            "list_dir",
            "file_search",
        ],
        "Search & Navigation": ["semantic_search", "grep_search", "list_code_usages"],
        "Terminal": [
            "run_in_terminal",
            "get_terminal_output",
            "terminal_last_command",
            "terminal_selection",
        ],
        "Git Operations": [
            "get_changed_files",
            # Git tools require activation
        ],
        "Testing": ["runTests", "get_errors", "test_failure"],
        "Tasks": ["run_task", "get_task_output", "create_and_run_task"],
        "Notebook Operations": [
            "create_new_jupyter_notebook",
            "edit_notebook_file",
            "copilot_getNotebookSummary",
            "run_notebook_cell",
            "read_notebook_cell_output",
        ],
        "Workspace": [
            "create_new_workspace",
            "get_project_setup_info",
            "get_search_view_results",
        ],
        "VSCode API": ["get_vscode_api", "install_extension", "run_vscode_command"],
        "Documentation": ["fetch_webpage", "github_repo"],
        "Project Management": ["manage_todo_list"],
        "GitHub (Basic)": [
            "mcp_github_github_get_me",
            "mcp_github_github_get_tag",
            "mcp_github_github_list_commits",
            "mcp_github_github_list_issue_types",
            "mcp_github_github_star_repository",
            "mcp_github_github_unstar_repository",
        ],
        "Azure Resources": ["azureResources_getAzureActivityLog"],
    }

    # Activation-gated tools (not currently active)
    activation_tools = {
        "AI Model & Tracing": "activate_ai_model_and_tracing_tools",
        "Notebook Management": "activate_notebook_management_tools",
        "Python Environment": "activate_python_environment_tools",
        "Mermaid Diagrams": "activate_mermaid_diagram_tools",
        "GitHub PR": "activate_github_pull_request_tools",
        "Browser Navigation": "activate_browser_navigation_tools",
        "Element Interaction": "activate_element_interaction_tools",
        "Performance Analysis": "activate_performance_analysis_tools",
        "Screenshot & Snapshot": "activate_screenshot_and_snapshot_tools",
        "Network Tools": "activate_network_tools",
        "Script & Console": "activate_script_and_console_tools",
        "Page Management": "activate_page_management_tools",
        "Hugging Face": "activate_hugging_face_tools",
        "GitHub Issues": "activate_github_tools_issue_management",
        "GitHub PRs": "activate_github_tools_pull_request_management",
        "GitHub Repos": "activate_github_tools_repository_management",
        "GitHub Projects": "activate_github_tools_project_management",
        "GitHub Workflows": "activate_github_tools_workflow_management",
        "GitHub Notifications": "activate_github_tools_notification_management",
        "GitHub Search": "activate_github_tools_search_and_discovery",
        "GitHub Security": "activate_github_tools_security_management",
        "GitHub Gists": "activate_github_tools_gist_management",
        "GitHub Copilot": "activate_github_tools_copilot_management",
        "GitHub Discussions": "activate_github_tools_discussion_management",
        "GitHub Releases": "activate_github_tools_release_management",
        "GitHub Teams": "activate_github_tools_team_management",
        "Git Version Control": "activate_git_tools_version_control",
        "Git Issues": "activate_git_tools_issue_management",
        "Git Workspace": "activate_git_tools_workspace_management",
        "Git Repository": "activate_git_tools_repository_management",
        "Pylance": "activate_pylance_tools",
        "SonarQube": "activate_sonarqube_tools",
    }

    # Count currently active tools
    active_count = sum(len(tools) for tools in tool_categories.values())

    for _category, _tools in tool_categories.items():
        pass

    for _category, _activator in list(activation_tools.items())[:10]:
        pass

    return active_count, len(activation_tools)


def check_extension_recommendations():
    """Check workspace extension recommendations."""
    extensions_file = Path(".vscode/extensions.json")
    if not extensions_file.exists():
        return {
            "recommendations": [],
            "optionalRecommendations": [],
            "unwantedRecommendations": [],
            "localRecommendations": [],
        }
    data = _load_jsonc(extensions_file)
    return {
        "recommendations": data.get("recommendations", []),
        "optionalRecommendations": data.get(
            "optionalRecommendations",
            data.get("recommendedOptional", []),
        ),
        "unwantedRecommendations": data.get("unwantedRecommendations", []),
        "localRecommendations": data.get("localRecommendations", []),
    }


def _get_extension_integrator():
    """Import existing extension integrator lazily."""
    try:
        from scripts.integrate_extensions import ExtensionIntegrator

        return ExtensionIntegrator()
    except Exception:
        return None


def get_live_extension_stats() -> dict:
    """Collect live extension state from existing integration tooling."""
    integrator = _get_extension_integrator()
    if integrator is None:
        return {
            "status": "unavailable",
            "installed_total": 0,
            "recommended_total": 0,
            "recommended_installed": 0,
            "recommended_missing": 0,
            "optional_total": 0,
            "optional_installed": 0,
            "optional_missing": 0,
        }

    status = integrator.check_recommended_extensions()
    installed_total = len(integrator.get_installed_extensions())
    return {
        "status": "ok",
        "installed_total": installed_total,
        "recommended_total": len(status.get("recommended", [])),
        "recommended_installed": len(status.get("installed", [])),
        "recommended_missing": len(status.get("missing", [])),
        "optional_total": len(status.get("optional_missing", [])) + len(status.get("optional_installed", [])),
        "optional_installed": len(status.get("optional_installed", [])),
        "optional_missing": len(status.get("optional_missing", [])),
    }


def analyze_claude_surface() -> dict:
    """Map Claude local tooling surface from .claude/settings.local.json."""
    settings_file = Path(".claude/settings.local.json")
    if not settings_file.exists():
        return {"status": "missing"}

    try:
        data = json.loads(settings_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "invalid_json"}

    allow = data.get("permissions", {}).get("allow", [])
    allow = [entry for entry in allow if isinstance(entry, str)]
    code_cli_allow = [entry for entry in allow if "Bash(code" in entry]
    codex_cli_allow = [entry for entry in allow if "Bash(codex" in entry]
    mcp_allow = [entry for entry in allow if entry.startswith("mcp__")]
    start_nusyq_allow = [entry for entry in allow if "start_nusyq.py" in entry]
    return {
        "status": "ok",
        "allow_entries": len(allow),
        "code_cli_rules": len(code_cli_allow),
        "codex_cli_rules": len(codex_cli_allow),
        "mcp_rules": len(mcp_allow),
        "start_nusyq_rules": len(start_nusyq_allow),
    }


def generate_cross_reference_report():
    """Generate comprehensive cross-reference report."""
    cap_data = analyze_capability_inventory()
    active_tools, gated_tools = enumerate_vscode_tools()
    extensions = check_extension_recommendations()
    live_extensions = get_live_extension_stats()
    claude_surface = analyze_claude_surface()

    system_caps = cap_data["total_capabilities"] if cap_data else 0
    vscode_estimate = active_tools + gated_tools
    installed_extensions = live_extensions.get("installed_total", 0)
    user_reported = installed_extensions or 228
    recommended_total = len(extensions.get("recommendations", []))
    recommended_hit_rate = 0.0
    if recommended_total:
        recommended_hit_rate = live_extensions.get("recommended_installed", 0) / recommended_total

    # Generate detailed report
    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "system_capabilities": system_caps,
        "vscode_active_tools": active_tools,
        "vscode_gated_tools": gated_tools,
        "user_reported_tools": user_reported,
        "installed_extensions": installed_extensions,
        "discrepancy": {
            "system_vs_vscode": system_caps - user_reported,
            "vscode_vs_reported": vscode_estimate - user_reported,
        },
        "extension_recommendations": extensions,
        "live_extension_stats": live_extensions,
        "claude_surface": claude_surface,
        "utilization_signals": {
            "recommended_hit_rate": round(recommended_hit_rate, 3),
            "unwanted_recommendations": len(extensions.get("unwantedRecommendations", [])),
            "local_extension_recommendations": len(extensions.get("localRecommendations", [])),
        },
    }

    report_path = Path("state/reports/vscode_tools_analysis.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    generate_cross_reference_report()
