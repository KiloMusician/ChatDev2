# DevTool+ Invocation Patterns

## Agent Task Router

- Use `target_system="devtool"` in orchestration tasks to route directly to DevTool+.
- Supported actions: navigate, click, fill, screenshot, lighthouse, console, network, script.
- Example:
  ```python
  await router.route_task(
      task_type="analyze",
      description="Run Lighthouse audit on https://example.com",
      context={"action": "lighthouse", "url": "https://example.com"},
      target_system="devtool"
  )
  ```

## CLI Dispatch

- Use `nusyq_dispatch.py ask devtool "Navigate to URL"` for direct CLI invocation.
- DevTool+ tools are available as MCP tools (e.g., `mcp_chromedevtool_navigate_page`).

## Categories & Actions

- Page Management: navigate_page, list_pages, new_page, close_page, select_page
- DOM Interaction: click, fill, fill_form, hover, drag, press_key, type_text
- Content Capture: take_screenshot, take_snapshot, take_memory_snapshot
- JavaScript: evaluate_script
- Network: list_network_requests, get_network_request
- Console: list_console_messages, get_console_message
- Performance: lighthouse_audit, start_trace, stop_trace, analyze_insight
- Emulation: emulate, resize_page
- Dialogs: handle_dialog, upload_file
- Synchronization: wait_for

## Status & Diagnostics

- Use `DevToolBridge().get_status()` for operational status and tool catalog.
- Use `probe_devtool()` for agent registry probe.
- Chrome is the preferred browser path. In WSL-heavy setups, Windows Edge can
  appear as a degraded fallback so routing and diagnostics stay available even
  when Chrome is not installed.

## Integration Summary

- DevTool+ is fully integrated for agent routing, CLI dispatch, and MCP tool invocation.
- No missing entry points or gaps detected.

---

_Last updated: 2026-03-11_
