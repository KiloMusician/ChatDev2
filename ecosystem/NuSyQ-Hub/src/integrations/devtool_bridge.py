"""DevTool+ Bridge for NuSyQ Ecosystem.

Integrates Chrome DevTools MCP tools (from DevTool+ VS Code extension) into the
NuSyQ agent ecosystem, enabling browser automation, debugging, and testing.

MCP Tool Categories:
- Page Management: list_pages, new_page, close_page, navigate_page, select_page
- DOM Interaction: click, fill, fill_form, hover, drag, press_key, type_text
- Content Capture: take_screenshot, take_snapshot, take_memory_snapshot
- JavaScript: evaluate_script
- Network: list_network_requests, get_network_request
- Console: list_console_messages, get_console_message
- Performance: lighthouse_audit, performance_start_trace, performance_stop_trace,
               performance_analyze_insight
- Emulation: emulate, resize_page
- Dialogs: handle_dialog, upload_file
- Synchronization: wait_for

Preferred browser: Chrome. On Windows/WSL, Edge can be exposed as a degraded
fallback so extension-backed flows remain visible to the ecosystem.
"""

from __future__ import annotations

import logging
import os
import shutil
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Browser Detection ─────────────────────────────────────────────────────────


class BrowserStatus(Enum):
    """Browser availability status."""

    AVAILABLE = "available"
    NOT_INSTALLED = "not_installed"
    NOT_STARTED = "not_started"
    UNKNOWN = "unknown"


@dataclass
class BrowserProbeResult:
    """Result of browser availability probe."""

    status: BrowserStatus
    browser: str | None = None
    path: str | None = None
    detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _is_wsl() -> bool:
    """Return True when running inside WSL."""
    uname = getattr(os, "uname", None)
    release = uname().release.lower() if callable(uname) else ""
    return "WSL_DISTRO_NAME" in os.environ or "microsoft" in release


def _windows_mount_candidates(*relative_paths: str) -> list[Path]:
    """Build candidate Windows install paths visible from WSL."""
    return [Path("/mnt/c") / relative_path for relative_path in relative_paths]


def _find_chrome_windows() -> Path | None:
    """Locate a Chromium-compatible browser on Windows."""
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Chromium/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "Chromium/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Chromium/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", ""))
        / "BraveSoftware/Brave-Browser/Application/brave.exe",
        Path(os.environ.get("PROGRAMFILES", ""))
        / "BraveSoftware/Brave-Browser/Application/brave.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", ""))
        / "BraveSoftware/Brave-Browser/Application/brave.exe",
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files/Chromium/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Chromium/Application/chrome.exe"),
        Path("C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"),
        Path("C:/Program Files (x86)/BraveSoftware/Brave-Browser/Application/brave.exe"),
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _find_chrome_macos() -> Path | None:
    """Locate a Chromium-compatible browser on macOS."""
    candidates = [
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
        Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
    ]
    return next((path for path in candidates if path.exists()), None)


def _find_chrome_linux() -> Path | None:
    """Locate a Chromium-compatible browser on Linux."""
    # Check common paths and PATH
    candidates = [
        Path("/usr/bin/google-chrome"),
        Path("/usr/bin/google-chrome-stable"),
        Path("/usr/bin/chromium"),
        Path("/usr/bin/chromium-browser"),
        Path("/usr/bin/brave-browser"),
        Path("/opt/google/chrome/chrome"),
        Path("/opt/chromium/chrome"),
        Path("/opt/brave.com/brave/brave-browser"),
    ]
    if _is_wsl():
        candidates.extend(
            _windows_mount_candidates(
                "Program Files/Google/Chrome/Application/chrome.exe",
                "Program Files (x86)/Google/Chrome/Application/chrome.exe",
                "Program Files/Chromium/Application/chrome.exe",
                "Program Files (x86)/Chromium/Application/chrome.exe",
                "Program Files/BraveSoftware/Brave-Browser/Application/brave.exe",
                "Program Files (x86)/BraveSoftware/Brave-Browser/Application/brave.exe",
            )
        )
    for path in candidates:
        if path.exists():
            return path
    # Fallback to shutil.which
    which_result = (
        shutil.which("google-chrome")
        or shutil.which("google-chrome-stable")
        or shutil.which("chromium")
        or shutil.which("chromium-browser")
        or shutil.which("brave-browser")
    )
    return Path(which_result) if which_result else None


def _browser_family(path: Path) -> str:
    """Infer the Chromium-family browser name from the binary path."""
    lowered = str(path).lower()
    if "brave" in lowered:
        return "brave"
    if "chromium" in lowered:
        return "chromium"
    return "chrome"


def detect_chrome() -> BrowserProbeResult:
    """Detect Chrome browser installation.

    Returns:
        BrowserProbeResult with status and path if found.
    """
    platform = sys.platform

    if platform == "win32":
        chrome_path = _find_chrome_windows()
    elif platform == "darwin":
        chrome_path = _find_chrome_macos()
    else:
        chrome_path = _find_chrome_linux()

    if chrome_path:
        browser_name = _browser_family(chrome_path)
        return BrowserProbeResult(
            status=BrowserStatus.AVAILABLE,
            browser=browser_name,
            path=str(chrome_path),
            detail=f"{browser_name.title()} found at {chrome_path}",
            metadata={"platform": platform, "browser_family": browser_name},
        )

    return BrowserProbeResult(
        status=BrowserStatus.NOT_INSTALLED,
        detail="No Chromium-compatible browser found. DevTool+ requires Chrome/Chromium-family support.",
        metadata={"platform": platform, "searched": "standard_paths"},
    )


def detect_edge_fallback() -> BrowserProbeResult:
    """Detect Edge as a degraded but usable fallback."""
    candidates: list[Path] = []

    if sys.platform == "win32":
        candidates.extend(
            [
                Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
                Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
                Path(os.environ.get("PROGRAMFILES(X86)", ""))
                / "Microsoft/Edge/Application/msedge.exe",
                Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft/Edge/Application/msedge.exe",
            ]
        )
    elif _is_wsl():
        candidates.extend(
            _windows_mount_candidates(
                "Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
                "Program Files/Microsoft/Edge/Application/msedge.exe",
            )
        )
    else:
        which_result = shutil.which("microsoft-edge") or shutil.which("microsoft-edge-stable")
        if which_result:
            candidates.append(Path(which_result))

    for path in candidates:
        if path.exists():
            return BrowserProbeResult(
                status=BrowserStatus.AVAILABLE,
                browser="edge",
                path=str(path),
                detail=f"Edge found at {path} (degraded fallback mode)",
                metadata={
                    "warning": "Chrome is preferred; Edge fallback may not support every workflow",
                    "platform": sys.platform,
                    "wsl": _is_wsl(),
                },
            )

    return BrowserProbeResult(
        status=BrowserStatus.NOT_INSTALLED,
        detail="Edge not found",
        metadata={"platform": sys.platform, "wsl": _is_wsl()},
    )


# ── DevTool+ MCP Tool Catalog ─────────────────────────────────────────────────


@dataclass
class MCPToolInfo:
    """Metadata for an MCP tool."""

    name: str
    category: str
    description: str
    requires_page: bool = True
    returns_image: bool = False


# Catalog of DevTool+ MCP tools
DEVTOOL_MCP_TOOLS: dict[str, MCPToolInfo] = {
    # Page Management
    "list_pages": MCPToolInfo(
        name="mcp_chromedevtool_list_pages",
        category="page",
        description="List all open browser pages/tabs",
        requires_page=False,
    ),
    "new_page": MCPToolInfo(
        name="mcp_chromedevtool_new_page",
        category="page",
        description="Open a new browser page",
        requires_page=False,
    ),
    "close_page": MCPToolInfo(
        name="mcp_chromedevtool_close_page",
        category="page",
        description="Close the current page",
    ),
    "navigate_page": MCPToolInfo(
        name="mcp_chromedevtool_navigate_page",
        category="page",
        description="Navigate to a URL",
    ),
    "select_page": MCPToolInfo(
        name="mcp_chromedevtool_select_page",
        category="page",
        description="Select/focus a specific page by ID",
    ),
    # DOM Interaction
    "click": MCPToolInfo(
        name="mcp_chromedevtool_click",
        category="dom",
        description="Click an element by selector",
    ),
    "fill": MCPToolInfo(
        name="mcp_chromedevtool_fill",
        category="dom",
        description="Fill an input field",
    ),
    "fill_form": MCPToolInfo(
        name="mcp_chromedevtool_fill_form",
        category="dom",
        description="Fill multiple form fields",
    ),
    "hover": MCPToolInfo(
        name="mcp_chromedevtool_hover",
        category="dom",
        description="Hover over an element",
    ),
    "drag": MCPToolInfo(
        name="mcp_chromedevtool_drag",
        category="dom",
        description="Drag an element",
    ),
    "press_key": MCPToolInfo(
        name="mcp_chromedevtool_press_key",
        category="dom",
        description="Press a keyboard key",
    ),
    "type_text": MCPToolInfo(
        name="mcp_chromedevtool_type_text",
        category="dom",
        description="Type text into the focused element",
    ),
    # Content Capture
    "take_screenshot": MCPToolInfo(
        name="mcp_chromedevtool_take_screenshot",
        category="capture",
        description="Capture a screenshot of the page",
        returns_image=True,
    ),
    "take_snapshot": MCPToolInfo(
        name="mcp_chromedevtool_take_snapshot",
        category="capture",
        description="Capture DOM snapshot",
    ),
    "take_memory_snapshot": MCPToolInfo(
        name="mcp_chromedevtool_take_memory_snapshot",
        category="capture",
        description="Capture memory heap snapshot",
    ),
    # JavaScript
    "evaluate_script": MCPToolInfo(
        name="mcp_chromedevtool_evaluate_script",
        category="javascript",
        description="Execute JavaScript in page context",
    ),
    # Network
    "list_network_requests": MCPToolInfo(
        name="mcp_chromedevtool_list_network_requests",
        category="network",
        description="List captured network requests",
    ),
    "get_network_request": MCPToolInfo(
        name="mcp_chromedevtool_get_network_request",
        category="network",
        description="Get details of a specific network request",
    ),
    # Console
    "list_console_messages": MCPToolInfo(
        name="mcp_chromedevtool_list_console_messages",
        category="console",
        description="List browser console messages",
    ),
    "get_console_message": MCPToolInfo(
        name="mcp_chromedevtool_get_console_message",
        category="console",
        description="Get a specific console message",
    ),
    # Performance
    "lighthouse_audit": MCPToolInfo(
        name="mcp_chromedevtool_lighthouse_audit",
        category="performance",
        description="Run Lighthouse performance audit",
    ),
    "start_trace": MCPToolInfo(
        name="mcp_chromedevtool_performance_start_trace",
        category="performance",
        description="Start performance tracing",
    ),
    "stop_trace": MCPToolInfo(
        name="mcp_chromedevtool_performance_stop_trace",
        category="performance",
        description="Stop performance tracing",
    ),
    "analyze_insight": MCPToolInfo(
        name="mcp_chromedevtool_performance_analyze_insight",
        category="performance",
        description="Analyze performance insights",
    ),
    # Emulation
    "emulate": MCPToolInfo(
        name="mcp_chromedevtool_emulate",
        category="emulation",
        description="Emulate device (mobile, tablet, etc.)",
    ),
    "resize_page": MCPToolInfo(
        name="mcp_chromedevtool_resize_page",
        category="emulation",
        description="Resize page viewport",
    ),
    # Dialogs & Files
    "handle_dialog": MCPToolInfo(
        name="mcp_chromedevtool_handle_dialog",
        category="dialog",
        description="Handle browser dialogs (alert, confirm, prompt)",
    ),
    "upload_file": MCPToolInfo(
        name="mcp_chromedevtool_upload_file",
        category="dialog",
        description="Upload file to file input",
    ),
    # Synchronization
    "wait_for": MCPToolInfo(
        name="mcp_chromedevtool_wait_for",
        category="sync",
        description="Wait for element, network idle, or navigation",
    ),
}


def get_tool_by_category(category: str) -> list[MCPToolInfo]:
    """Get all DevTool+ MCP tools in a category.

    Args:
        category: Category name (page, dom, capture, javascript, network,
                  console, performance, emulation, dialog, sync)

    Returns:
        List of MCPToolInfo for tools in the category.
    """
    return [tool for tool in DEVTOOL_MCP_TOOLS.values() if tool.category == category]


def get_all_categories() -> list[str]:
    """Get all available DevTool+ categories."""
    return list({tool.category for tool in DEVTOOL_MCP_TOOLS.values()})


# ── DevTool+ Bridge Client ────────────────────────────────────────────────────


@dataclass
class DevToolBridgeStatus:
    """Status of the DevTool+ bridge."""

    chrome_available: bool
    edge_fallback_available: bool
    mcp_tools_count: int
    categories: list[str]
    detail: str
    metadata: dict[str, Any] = field(default_factory=dict)


class DevToolBridge:
    """Bridge for coordinating DevTool+ MCP operations.

    This bridge provides:
    - Browser availability detection (Chrome preferred, Edge as degraded fallback)
    - MCP tool catalog for routing
    - Integration points for MJOLNIR dispatch

    Note: The actual MCP tool invocation is handled by Copilot's MCP system.
    This bridge provides metadata and coordination capabilities.
    """

    def __init__(self) -> None:
        """Initialize DevTool+ bridge."""
        self._chrome_result: BrowserProbeResult | None = None
        self._edge_result: BrowserProbeResult | None = None

    def probe_browser(self, force: bool = False) -> BrowserProbeResult:
        """Probe for Chrome availability.

        Args:
            force: Force re-probe even if cached.

        Returns:
            BrowserProbeResult with Chrome status.
        """
        if self._chrome_result is None or force:
            self._chrome_result = detect_chrome()
        return self._chrome_result

    def probe_edge_fallback(self, force: bool = False) -> BrowserProbeResult:
        """Probe for Edge as informational fallback.

        Args:
            force: Force re-probe even if cached.

        Returns:
            BrowserProbeResult with Edge status.
        """
        if self._edge_result is None or force:
            self._edge_result = detect_edge_fallback()
        return self._edge_result

    def get_status(self) -> DevToolBridgeStatus:
        """Get comprehensive bridge status.

        Returns:
            DevToolBridgeStatus with all availability info.
        """
        chrome = self.probe_browser()
        edge = self.probe_edge_fallback()

        detail_parts = []
        if chrome.status == BrowserStatus.AVAILABLE:
            browser_label = str(chrome.browser or "chrome").title()
            detail_parts.append(f"{browser_label}: {chrome.path}")
        else:
            detail_parts.append("Chrome-family browser: NOT INSTALLED (preferred)")

        if edge.status == BrowserStatus.AVAILABLE:
            detail_parts.append(f"Edge: {edge.path} (degraded fallback)")

        status = DevToolBridgeStatus(
            chrome_available=chrome.status == BrowserStatus.AVAILABLE,
            edge_fallback_available=edge.status == BrowserStatus.AVAILABLE,
            mcp_tools_count=len(DEVTOOL_MCP_TOOLS),
            categories=get_all_categories(),
            detail="; ".join(detail_parts),
            metadata={
                "chrome": chrome.metadata,
                "edge": edge.metadata if edge.metadata else {},
                "platform": sys.platform,
            },
        )

        try:
            from src.system.agent_awareness import emit as _emit

            _avail = (
                "chrome"
                if status.chrome_available
                else ("edge" if status.edge_fallback_available else "none")
            )
            _emit(
                "agents",
                f"DevTool probe: browser={_avail} tools={status.mcp_tools_count}",
                level="INFO",
                source="devtool_bridge",
            )
        except Exception:
            pass

        return status

    def is_operational(self) -> bool:
        """Check if DevTool+ has any usable browser path."""
        return self.probe_browser().status == BrowserStatus.AVAILABLE or (
            self.probe_edge_fallback().status == BrowserStatus.AVAILABLE
        )

    def get_mcp_tool_name(self, short_name: str) -> str | None:
        """Get full MCP tool name for a short name.

        Args:
            short_name: Short name like "click", "navigate_page", etc.

        Returns:
            Full MCP tool name or None if not found.
        """
        tool_info = DEVTOOL_MCP_TOOLS.get(short_name)
        return tool_info.name if tool_info else None

    def list_tools(self, category: str | None = None) -> list[dict[str, Any]]:
        """List available DevTool+ MCP tools.

        Args:
            category: Filter by category (optional).

        Returns:
            List of tool info dicts.
        """
        _tools = get_tool_by_category(category) if category else list(DEVTOOL_MCP_TOOLS.values())
        return [
            {
                "short_name": key,
                "mcp_name": tool.name,
                "category": tool.category,
                "description": tool.description,
                "requires_page": tool.requires_page,
                "returns_image": tool.returns_image,
            }
            for key, tool in DEVTOOL_MCP_TOOLS.items()
            if category is None or tool.category == category
        ]


# ── Agent Registry Integration ────────────────────────────────────────────────


def probe_devtool() -> tuple[str, str, dict[str, Any]]:
    """Probe function for agent_registry.py integration.

    Returns:
        Tuple of (status, detail, metadata) compatible with AGENT_PROBES.
    """
    bridge = DevToolBridge()
    chrome = bridge.probe_browser()

    if chrome.status == BrowserStatus.AVAILABLE:
        browser_name = str(chrome.browser or "chrome")
        return (
            "ONLINE",
            f"DevTool+ ready ({len(DEVTOOL_MCP_TOOLS)} MCP tools, {browser_name}: {chrome.path})",
            {
                "browser": browser_name,
                "path": chrome.path,
                "tool_count": len(DEVTOOL_MCP_TOOLS),
                "categories": get_all_categories(),
                "browser_family": browser_name,
            },
        )

    edge = bridge.probe_edge_fallback()
    if edge.status == BrowserStatus.AVAILABLE:
        return (
            "DEGRADED",
            f"DevTool+ limited (Chrome not found, Edge available: {edge.path})",
            {
                "browser": "edge",
                "path": edge.path,
                "warning": "Chrome is preferred; Edge fallback may not support every workflow",
                "wsl": _is_wsl(),
            },
        )

    return (
        "OFFLINE",
        "DevTool+ unavailable (no Chromium-compatible browser installed)",
        {"searched": "standard_paths", "recommendation": "Install Chrome, Chromium, or Brave"},
    )


# ── Convenience Functions ─────────────────────────────────────────────────────


def get_bridge() -> DevToolBridge:
    """Get a DevTool+ bridge instance.

    Returns:
        Initialized DevToolBridge.
    """
    return DevToolBridge()


def quick_status() -> str:
    """Quick one-liner status for DevTool+.

    Returns:
        Human-readable status string.
    """
    status, detail, _ = probe_devtool()
    return f"DevTool+: {status} - {detail}"


if __name__ == "__main__":
    # Quick smoke test
    print("DevTool+ Bridge Status Check")
    print("=" * 50)

    bridge = get_bridge()
    status = bridge.get_status()

    print(f"Chrome Available: {status.chrome_available}")
    print(f"Edge Fallback: {status.edge_fallback_available}")
    print(f"MCP Tools: {status.mcp_tools_count}")
    print(f"Categories: {', '.join(status.categories)}")
    print(f"Detail: {status.detail}")
    print()

    print("Tool Categories:")
    for category in sorted(status.categories):
        tools = bridge.list_tools(category)
        print(f"  {category}: {len(tools)} tools")

    print()
    print("Agent Registry Probe:")
    result = probe_devtool()
    print(f"  Status: {result[0]}")
    print(f"  Detail: {result[1]}")
