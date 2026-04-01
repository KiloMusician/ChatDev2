"""MCP Extension Catalog and Integration Status.

This module provides a comprehensive catalog of all available MCP (Model Context
Protocol) tools from installed VS Code extensions, their categories, and integration
status within the NuSyQ ecosystem.

MCP Extension Categories:
1. DevTool+ (chromedevtool) - Browser automation and testing
2. Database Client (dbclient) - SQL database operations
3. Mermaid Diagram (mermaid) - Architecture visualization
4. Hugging Face (evalstate_hf) - ML model/dataset discovery
5. GitHub MCP - Full GitHub API access
6. GitKraken MCP - Multi-platform git operations
7. Azure MCP - Cloud infrastructure management
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class IntegrationStatus(Enum):
    """Status of MCP extension integration with NuSyQ."""

    FULLY_INTEGRATED = "fully_integrated"  # Bridge exists, agent registered
    PARTIALLY_INTEGRATED = "partially_integrated"  # Some integration exists
    NOT_INTEGRATED = "not_integrated"  # No integration yet
    NOT_APPLICABLE = "not_applicable"  # Direct MCP use is sufficient


class ExtensionCategory(Enum):
    """Categories of MCP extensions."""

    BROWSER = "browser"
    DATABASE = "database"
    VISUALIZATION = "visualization"
    ML_AI = "ml_ai"
    VERSION_CONTROL = "version_control"
    CLOUD = "cloud"


@dataclass
class MCPTool:
    """Individual MCP tool metadata."""

    name: str
    category: str
    description: str
    parameters: list[str] = field(default_factory=list)


@dataclass
class MCPExtension:
    """MCP Extension metadata and tool catalog."""

    name: str
    prefix: str
    category: ExtensionCategory
    description: str
    tool_count: int
    integration_status: IntegrationStatus
    tools: list[MCPTool] = field(default_factory=list)
    notes: str = ""
    bridge_module: str | None = None


# ── Extension Catalog ─────────────────────────────────────────────────────────

MCP_EXTENSIONS: dict[str, MCPExtension] = {
    "devtool": MCPExtension(
        name="DevTool+",
        prefix="mcp_chromedevtool_",
        category=ExtensionCategory.BROWSER,
        description="Chrome DevTools automation for browser testing, debugging, and performance analysis",
        tool_count=25,
        integration_status=IntegrationStatus.FULLY_INTEGRATED,
        bridge_module="src.integrations.devtool_bridge",
        notes="Requires Chrome browser (Edge fallback available but limited)",
        tools=[
            MCPTool("list_pages", "page", "List all open browser pages/tabs"),
            MCPTool("new_page", "page", "Open a new browser page"),
            MCPTool("close_page", "page", "Close the current page"),
            MCPTool("navigate_page", "page", "Navigate to a URL"),
            MCPTool("select_page", "page", "Select/focus a specific page by ID"),
            MCPTool("click", "dom", "Click an element by selector"),
            MCPTool("fill", "dom", "Fill an input field"),
            MCPTool("fill_form", "dom", "Fill multiple form fields"),
            MCPTool("hover", "dom", "Hover over an element"),
            MCPTool("drag", "dom", "Drag an element"),
            MCPTool("press_key", "dom", "Press a keyboard key"),
            MCPTool("type_text", "dom", "Type text into focused element"),
            MCPTool("take_screenshot", "capture", "Capture page screenshot"),
            MCPTool("take_snapshot", "capture", "Capture DOM snapshot"),
            MCPTool("take_memory_snapshot", "capture", "Capture memory heap"),
            MCPTool("evaluate_script", "javascript", "Execute JavaScript"),
            MCPTool("list_network_requests", "network", "List network requests"),
            MCPTool("get_network_request", "network", "Get request details"),
            MCPTool("list_console_messages", "console", "List console messages"),
            MCPTool("get_console_message", "console", "Get specific message"),
            MCPTool("lighthouse_audit", "performance", "Run Lighthouse audit"),
            MCPTool("start_trace", "performance", "Start performance trace"),
            MCPTool("stop_trace", "performance", "Stop performance trace"),
            MCPTool("emulate", "emulation", "Emulate device"),
            MCPTool("resize_page", "emulation", "Resize viewport"),
        ],
    ),
    "dbclient": MCPExtension(
        name="Database Client",
        prefix="dbclient-",
        category=ExtensionCategory.DATABASE,
        description="SQL database operations: queries, schema inspection, and database management",
        tool_count=3,
        integration_status=IntegrationStatus.FULLY_INTEGRATED,
        bridge_module="src.integrations.dbclient_bridge",
        notes="Integrated with agent_task_router, provides nusyq_state.db inspection and SQL queries",
        tools=[
            MCPTool("execute-query", "query", "Execute SQL queries with results"),
            MCPTool("get-databases", "schema", "List available databases"),
            MCPTool("get-tables", "schema", "List tables with schema info"),
        ],
    ),
    "mermaid": MCPExtension(
        name="Mermaid Diagram",
        prefix="",
        category=ExtensionCategory.VISUALIZATION,
        description="Architecture visualization and diagram syntax documentation",
        tool_count=3,
        integration_status=IntegrationStatus.NOT_APPLICABLE,
        notes="Available via deferred tools; used internally by dependency_analyzer.py for exports",
        tools=[
            MCPTool("get-syntax-docs-mermaid", "docs", "Get syntax docs for 20+ diagram types"),
            MCPTool("mermaid-diagram-preview", "render", "Preview diagram in editor"),
            MCPTool("mermaid-diagram-validator", "validate", "Validate diagram syntax"),
        ],
    ),
    "huggingface": MCPExtension(
        name="Hugging Face Hub",
        prefix="mcp_evalstate_hf-_",
        category=ExtensionCategory.ML_AI,
        description="ML model/dataset discovery, documentation, and dynamic space invocation",
        tool_count=10,
        integration_status=IntegrationStatus.FULLY_INTEGRATED,
        bridge_module="src.integrations.huggingface_bridge",
        notes="Authenticated as 'KiloEthereal', integrated with agent_task_router for ML discovery",
        tools=[
            MCPTool("dataset_search", "search", "Search HF datasets"),
            MCPTool("model_search", "search", "Search HF models"),
            MCPTool("paper_search", "search", "Search ML papers"),
            MCPTool("space_search", "search", "Search Gradio spaces"),
            MCPTool("hub_repo_details", "info", "Get repo details"),
            MCPTool("hf_doc_search", "docs", "Search HF documentation"),
            MCPTool("hf_doc_fetch", "docs", "Fetch specific doc"),
            MCPTool("hf_whoami", "auth", "Get current user info"),
            MCPTool("dynamic_space", "execute", "Invoke Gradio space"),
            MCPTool("gr1_z_image_turbo_generate", "generate", "Generate images"),
        ],
    ),
    "github": MCPExtension(
        name="GitHub MCP",
        prefix="mcp_github_",
        category=ExtensionCategory.VERSION_CONTROL,
        description="Full GitHub API: issues, PRs, repos, branches, commits, releases",
        tool_count=50,
        integration_status=IntegrationStatus.NOT_APPLICABLE,
        notes="Available via deferred tools (mcp_github_*) + github-pull-request extension; no bridge needed",
        tools=[
            # Issues
            MCPTool("list_issues", "issues", "List repository issues"),
            MCPTool("search_issues", "issues", "Search issues with filters"),
            MCPTool("issue_read", "issues", "Read issue details"),
            MCPTool("issue_write", "issues", "Create/update issues"),
            MCPTool("add_issue_comment", "issues", "Add issue comment"),
            MCPTool("list_issue_types", "issues", "List issue types"),
            MCPTool("sub_issue_write", "issues", "Create sub-issues"),
            MCPTool("assign_copilot_to_issue", "issues", "Assign Copilot"),
            # Pull Requests
            MCPTool("list_pull_requests", "pr", "List PRs"),
            MCPTool("search_pull_requests", "pr", "Search PRs"),
            MCPTool("pull_request_read", "pr", "Read PR details"),
            MCPTool("create_pull_request", "pr", "Create new PR"),
            MCPTool("update_pull_request", "pr", "Update PR"),
            MCPTool("merge_pull_request", "pr", "Merge PR"),
            MCPTool("update_pull_request_branch", "pr", "Update PR branch"),
            MCPTool("pull_request_review_write", "pr", "Write PR review"),
            MCPTool("add_comment_to_pending_review", "pr", "Add review comment"),
            MCPTool("request_copilot_review", "pr", "Request Copilot review"),
            # Repository
            MCPTool("create_repository", "repo", "Create repository"),
            MCPTool("fork_repository", "repo", "Fork repository"),
            MCPTool("search_repositories", "repo", "Search repositories"),
            MCPTool("get_file_contents", "repo", "Get file contents"),
            MCPTool("create_or_update_file", "repo", "Create/update file"),
            MCPTool("delete_file", "repo", "Delete file"),
            MCPTool("push_files", "repo", "Push multiple files"),
            # Branches & Commits
            MCPTool("create_branch", "branch", "Create branch"),
            MCPTool("list_branches", "branch", "List branches"),
            MCPTool("list_commits", "commit", "List commits"),
            MCPTool("get_commit", "commit", "Get commit details"),
            MCPTool("search_code", "search", "Search code"),
            # Users & Teams
            MCPTool("get_me", "user", "Get authenticated user"),
            MCPTool("search_users", "user", "Search users"),
            MCPTool("get_teams", "team", "Get teams"),
            MCPTool("get_team_members", "team", "Get team members"),
            # Releases & Tags
            MCPTool("list_releases", "release", "List releases"),
            MCPTool("get_latest_release", "release", "Get latest release"),
            MCPTool("get_release_by_tag", "release", "Get release by tag"),
            MCPTool("list_tags", "tag", "List tags"),
            MCPTool("get_tag", "tag", "Get tag details"),
            MCPTool("get_label", "label", "Get label"),
        ],
    ),
    "gitkraken": MCPExtension(
        name="GitKraken MCP",
        prefix="mcp_gitkraken_",
        category=ExtensionCategory.VERSION_CONTROL,
        description="Multi-platform git operations, cross-provider issues/PRs, GitLens features",
        tool_count=24,
        integration_status=IntegrationStatus.FULLY_INTEGRATED,
        bridge_module="src.integrations.gitkraken_bridge",
        notes="Integrated with agent_task_router for multi-platform git/issue operations",
        tools=[
            # Git operations
            MCPTool("git_add_or_commit", "git", "Stage and commit changes"),
            MCPTool("git_blame", "git", "Show file blame"),
            MCPTool("git_branch", "git", "Branch operations"),
            MCPTool("git_checkout", "git", "Checkout branch/commit"),
            MCPTool("git_log_or_diff", "git", "View log or diff"),
            MCPTool("git_push", "git", "Push changes"),
            MCPTool("git_stash", "git", "Stash management"),
            MCPTool("git_status", "git", "Repository status"),
            MCPTool("git_worktree", "git", "Worktree management"),
            # GitLens features
            MCPTool("gitlens_commit_composer", "gitlens", "Compose commits with AI"),
            MCPTool("gitlens_launchpad", "gitlens", "PR/issue launchpad"),
            MCPTool("gitlens_start_review", "gitlens", "Start code review"),
            MCPTool("gitlens_start_work", "gitlens", "Start work on issue"),
            # Cross-provider issues
            MCPTool("issues_assigned_to_me", "issues", "Issues assigned to me"),
            MCPTool("issues_get_detail", "issues", "Get issue details"),
            MCPTool("issues_add_comment", "issues", "Add issue comment"),
            # Cross-provider PRs
            MCPTool("pull_request_assigned_to_me", "pr", "PRs assigned to me"),
            MCPTool("pull_request_get_detail", "pr", "Get PR details"),
            MCPTool("pull_request_get_comments", "pr", "Get PR comments"),
            MCPTool("pull_request_create", "pr", "Create PR"),
            MCPTool("pull_request_create_review", "pr", "Create PR review"),
            # Repository
            MCPTool("repository_get_file_content", "repo", "Get file content"),
            MCPTool("gitkraken_workspace_list", "workspace", "List workspaces"),
        ],
    ),
    "azure": MCPExtension(
        name="Azure MCP",
        prefix="mcp_azure_mcp_",
        category=ExtensionCategory.CLOUD,
        description="Azure cloud infrastructure: compute, storage, databases, AI services",
        tool_count=40,
        integration_status=IntegrationStatus.NOT_APPLICABLE,
        notes="Available via deferred tools (mcp_azure_mcp_*); no bridge needed - invoked directly by Copilot",
        tools=[
            # Compute & Hosting
            MCPTool("appservice", "compute", "App Service management"),
            MCPTool("functionapp", "compute", "Function App management"),
            MCPTool("aks", "compute", "Kubernetes clusters"),
            MCPTool("acr", "compute", "Container Registry"),
            # Storage & Data
            MCPTool("storage", "data", "Storage accounts"),
            MCPTool("cosmos", "data", "Cosmos DB"),
            MCPTool("postgres", "data", "PostgreSQL"),
            MCPTool("mysql", "data", "MySQL"),
            MCPTool("sql", "data", "SQL Database"),
            MCPTool("redis", "data", "Redis Cache"),
            MCPTool("kusto", "data", "Data Explorer"),
            # AI & ML
            MCPTool("foundry", "ai", "AI Foundry"),
            MCPTool("speech", "ai", "Speech services"),
            MCPTool("search", "ai", "Cognitive Search"),
            # Messaging
            MCPTool("eventhubs", "messaging", "Event Hubs"),
            MCPTool("eventgrid", "messaging", "Event Grid"),
            MCPTool("servicebus", "messaging", "Service Bus"),
            # Security & Config
            MCPTool("keyvault", "security", "Key Vault"),
            MCPTool("appconfig", "config", "App Configuration"),
            MCPTool("role", "security", "RBAC management"),
            # Monitoring & Management
            MCPTool("monitor", "monitoring", "Azure Monitor"),
            MCPTool("applicationinsights", "monitoring", "App Insights"),
            MCPTool("grafana", "monitoring", "Managed Grafana"),
            MCPTool("workbooks", "monitoring", "Azure Workbooks"),
            MCPTool("applens", "monitoring", "App Lens diagnostics"),
            MCPTool("resourcehealth", "monitoring", "Resource health"),
            MCPTool("loadtesting", "testing", "Load Testing"),
            # IaC & Deployment
            MCPTool("deploy", "iac", "Deployments"),
            MCPTool("azd", "iac", "Azure Developer CLI"),
            MCPTool("bicepschema", "iac", "Bicep schema"),
            MCPTool("azureterraformbestpractices", "iac", "Terraform best practices"),
            MCPTool("cloudarchitect", "iac", "Architecture guidance"),
            # Management
            MCPTool("subscription_list", "management", "List subscriptions"),
            MCPTool("group_list", "management", "List resource groups"),
            MCPTool("quota", "management", "Quota management"),
            MCPTool("documentation", "docs", "Azure documentation"),
            MCPTool("get_bestpractices", "docs", "Best practices"),
        ],
    ),
}


# ── Extension Discovery ───────────────────────────────────────────────────────


def get_extension(name: str) -> MCPExtension | None:
    """Get MCP extension metadata by name.

    Args:
        name: Extension name (e.g., 'devtool', 'github', 'azure')

    Returns:
        MCPExtension metadata or None if not found.
    """
    return MCP_EXTENSIONS.get(name)


def get_all_extensions() -> list[MCPExtension]:
    """Get all registered MCP extensions.

    Returns:
        List of all MCPExtension objects.
    """
    return list(MCP_EXTENSIONS.values())


def get_extensions_by_category(category: ExtensionCategory) -> list[MCPExtension]:
    """Get extensions by category.

    Args:
        category: ExtensionCategory to filter by.

    Returns:
        List of extensions in the category.
    """
    return [ext for ext in MCP_EXTENSIONS.values() if ext.category == category]


def get_extensions_by_status(status: IntegrationStatus) -> list[MCPExtension]:
    """Get extensions by integration status.

    Args:
        status: IntegrationStatus to filter by.

    Returns:
        List of extensions with the given status.
    """
    return [ext for ext in MCP_EXTENSIONS.values() if ext.integration_status == status]


def get_integration_summary() -> dict[str, Any]:
    """Get summary of MCP extension integration status.

    Returns:
        Dict with counts and lists by integration status.
    """
    extensions = get_all_extensions()
    total_tools = sum(ext.tool_count for ext in extensions)

    return {
        "total_extensions": len(extensions),
        "total_tools": total_tools,
        "fully_integrated": [
            ext.name
            for ext in extensions
            if ext.integration_status == IntegrationStatus.FULLY_INTEGRATED
        ],
        "partially_integrated": [
            ext.name
            for ext in extensions
            if ext.integration_status == IntegrationStatus.PARTIALLY_INTEGRATED
        ],
        "not_integrated": [
            ext.name
            for ext in extensions
            if ext.integration_status == IntegrationStatus.NOT_INTEGRATED
        ],
        "by_category": {
            cat.value: [ext.name for ext in extensions if ext.category == cat]
            for cat in ExtensionCategory
        },
    }


# ── Integration Recommendations ───────────────────────────────────────────────


def get_integration_recommendations() -> list[dict[str, Any]]:
    """Get recommendations for improving MCP integration.

    Returns:
        List of recommendations with priority and effort.
    """
    recommendations = []

    for ext in MCP_EXTENSIONS.values():
        if ext.integration_status == IntegrationStatus.NOT_INTEGRATED:
            priority = "high" if ext.tool_count > 10 else "medium"
            effort = "high" if ext.tool_count > 20 else "medium" if ext.tool_count > 5 else "low"

            recommendations.append(
                {
                    "extension": ext.name,
                    "priority": priority,
                    "effort": effort,
                    "tool_count": ext.tool_count,
                    "category": ext.category.value,
                    "reason": f"Add {ext.name} bridge for {ext.tool_count} tools ({ext.category.value})",
                    "notes": ext.notes,
                }
            )

    # Sort by priority (high first) then by tool count (higher first)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda x: (priority_order[x["priority"]], -x["tool_count"]))

    return recommendations


# ── Main ──────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    print("MCP Extension Catalog - NuSyQ Integration Status")
    print("=" * 60)

    summary = get_integration_summary()
    print(f"\nTotal Extensions: {summary['total_extensions']}")
    print(f"Total MCP Tools: {summary['total_tools']}")

    print("\nIntegration Status:")
    print(f"  🔄 Partially Integrated: {', '.join(summary['partially_integrated']) or 'None'}")
    print(f"  ❌ Not Integrated: {', '.join(summary['not_integrated']) or 'None'}")

    print("\nExtensions by Category:")
    for cat, exts in summary["by_category"].items():
        if exts:
            print(f"  {cat}: {', '.join(exts)}")

    print("\nIntegration Recommendations:")
    for rec in get_integration_recommendations():
        print(f"  [{rec['priority'].upper()}] {rec['extension']}: {rec['tool_count']} tools")
        print(f"         {rec['reason']}")
        if rec["notes"]:
            print(f"         Note: {rec['notes']}")
