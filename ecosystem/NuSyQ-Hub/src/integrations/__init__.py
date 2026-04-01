"""NuSyQ-Hub Integration Modules Package.

This package provides comprehensive integration between NuSyQ-Hub and
external systems including Nogic Visualizer, OpenClaw messaging gateway,
MCP extension bridges, and other AI services.

Modules:
    nogic_bridge: Low-level Nogic API wrapper (commands + SQLite access)
    nogic_quest_integration: Quest system integration + architecture analysis
    nogic_vscode_bridge: VS Code extension communication and task runners
    openclaw_gateway_bridge: Multi-channel messaging integration (Slack, Discord, Telegram, etc.)
    devtool_bridge: Chrome DevTools MCP bridge (browser automation, 25+ tools)
    dbclient_bridge: Database Client MCP bridge (SQL/SQLite operations)
    gitkraken_bridge: GitKraken MCP bridge (git, issues, PRs across 10+ platforms)
    huggingface_bridge: HuggingFace Hub MCP bridge (model/dataset discovery)
    mcp_extension_catalog: Catalog of all MCP extension tools and integration status
    skyclaw_gateway_client: SkyClaw binary+HTTP gateway client
"""

# ── MCP Extension bridges (v0.3.0) ───────────────────────────────────────────
from src.integrations.dbclient_bridge import DBClientBridge
from src.integrations.dbclient_bridge import get_bridge as get_dbclient_bridge
from src.integrations.devtool_bridge import DevToolBridge
from src.integrations.devtool_bridge import get_bridge as get_devtool_bridge
from src.integrations.gitkraken_bridge import GitKrakenBridge
from src.integrations.gitkraken_bridge import \
    get_bridge as get_gitkraken_bridge
from src.integrations.huggingface_bridge import HuggingFaceBridge
from src.integrations.huggingface_bridge import \
    get_bridge as get_huggingface_bridge
from src.integrations.mcp_extension_catalog import (ExtensionCategory,
                                                    IntegrationStatus,
                                                    MCPExtension)
from src.integrations.mcp_extension_catalog import \
    get_all_extensions as get_extension_catalog
from src.integrations.mcp_extension_catalog import (
    get_extension, get_extensions_by_category, get_integration_recommendations,
    get_integration_summary)
# ── Nogic + OpenClaw (original) ───────────────────────────────────────────────
from src.integrations.nogic_bridge import (CodeFile, NogicBridge, RelationType,
                                           Symbol, SymbolKind, SymbolRelation)
from src.integrations.nogic_quest_integration import (
    ArchitectureAnalysis, NogicQuestIntegration, run_architecture_analysis)
from src.integrations.nogic_vscode_bridge import (NogicTaskRunner,
                                                  NogicVSCodeBridge,
                                                  NogicWebviewMessenger)
from src.integrations.openclaw_gateway_bridge import (
    OpenClawGatewayBridge, get_openclaw_gateway_bridge)

__version__ = "0.3.0"
__all__ = [
    "ArchitectureAnalysis",
    "CodeFile",
    "DBClientBridge",
    "DevToolBridge",
    "ExtensionCategory",
    "GitKrakenBridge",
    "HuggingFaceBridge",
    "IntegrationStatus",
    "MCPExtension",
    "NogicBridge",
    "NogicQuestIntegration",
    "NogicTaskRunner",
    "NogicVSCodeBridge",
    "NogicWebviewMessenger",
    "OpenClawGatewayBridge",
    "RelationType",
    "Symbol",
    "SymbolKind",
    "SymbolRelation",
    "get_dbclient_bridge",
    "get_devtool_bridge",
    "get_extension",
    "get_extension_catalog",
    "get_extensions_by_category",
    "get_gitkraken_bridge",
    "get_huggingface_bridge",
    "get_integration_recommendations",
    "get_integration_summary",
    "get_openclaw_gateway_bridge",
    "run_architecture_analysis",
]

__doc__ = """
NuSyQ-Hub Integrations Package (v0.3.0)

MCP Extension Bridges (new in v0.3.0):
    ```python
    from src.integrations import get_devtool_bridge, get_gitkraken_bridge
    from src.integrations import get_huggingface_bridge, get_dbclient_bridge
    from src.integrations import get_integration_catalog

    # Check integration status
    summary = get_integration_summary()

    # Access individual bridges
    dt = get_devtool_bridge()
    status = dt.probe()  # DevToolBridgeStatus

    hf = get_huggingface_bridge()
    hf_status = hf.probe()  # HFBridgeStatus
    ```

Nogic + OpenClaw (original):
    ```python
    from src.integrations import NogicBridge, NogicQuestIntegration

    with NogicBridge() as ng:
        symbols = ng.query_symbols(kind="Function")

    with NogicQuestIntegration() as nqi:
        analysis = nqi.analyze_architecture()
    ```

MJOLNIR Dispatch (zero-token routing):
    python scripts/nusyq_dispatch.py ask devtool "Navigate to localhost:8080"
    python scripts/nusyq_dispatch.py ask gitkraken "Show recent commits"
    python scripts/nusyq_dispatch.py ask huggingface "Search code generation models"
    python scripts/nusyq_dispatch.py ask dbclient "List tables in nusyq_state.db"
"""
