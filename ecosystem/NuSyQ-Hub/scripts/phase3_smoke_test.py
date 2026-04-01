#!/usr/bin/env python3
"""Phase 3 Comprehensive Smoke Test Suite

Tests:
1. MCP Server initialization
2. MCP Registry loading
3. ChatDevLauncher with git-mode
4. Docker smoke script validation
"""

import os
import sys
from pathlib import Path

# Add repo to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))


def test_mcp_server():
    """Test MCP server initialization."""
    print("\n" + "=" * 70)
    print("TEST 1: MCP Server Initialization")
    print("=" * 70)

    try:
        os.environ["CHATDEV_PATH"] = "C:\\Users\\keath\\NuSyQ\\ChatDev"
        os.environ["ACL_ENABLED"] = "1"

        from src.integration.mcp_server import MCPServer

        srv = MCPServer()
        print(f"✅ MCP Server: {srv.host}:{srv.port}")
        print(f"✅ Registered tools: {len(srv.registered_tools)}")

        tools = list(srv.registered_tools.keys())
        for tool in tools[:5]:
            print(f"   • {tool}")
        if len(tools) > 5:
            print(f"   ... +{len(tools) - 5} more")

        return True
    except Exception as e:
        print(f"❌ MCP Server test failed: {e}")
        return False


def test_mcp_registry():
    """Test MCP registry loading."""
    print("\n" + "=" * 70)
    print("TEST 2: MCP Registry Loading")
    print("=" * 70)

    try:
        from src.integration.mcp_registry_loader import get_mcp_registry_loader

        loader = get_mcp_registry_loader()

        print(f"✅ Registry loaded: {len(loader.servers)} servers")

        for server_id in loader.servers:
            _ = loader.get_server_info(server_id)
            can_start = loader.validate_server(loader.servers[server_id])
            status = "✓" if can_start else "✗"
            print(f"   {status} {server_id}")

        return True
    except Exception as e:
        print(f"❌ MCP Registry test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_chatdev_launcher():
    """Test ChatDevLauncher git-mode support."""
    print("\n" + "=" * 70)
    print("TEST 3: ChatDevLauncher Git-Mode Support")
    print("=" * 70)

    try:
        import inspect

        from src.integration.chatdev_launcher import ChatDevLauncher

        launcher = ChatDevLauncher()
        print(f"✅ ChatDevLauncher initialized: {launcher!r}")

        # Check git_mode parameter
        sig = inspect.signature(launcher.launch_chatdev)
        params = list(sig.parameters.keys())

        if "git_mode" in params:
            print("✅ git_mode parameter: SUPPORTED")
        else:
            print("❌ git_mode parameter: NOT FOUND")
            return False

        if "git_branch" in params:
            print("✅ git_branch parameter: SUPPORTED")

        print(f"✅ launch_chatdev parameters: {len(params)}")
        for param in params:
            print(f"   • {param}")

        return True
    except Exception as e:
        print(f"❌ ChatDevLauncher test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_docker_smoke_script():
    """Test Docker smoke script exists."""
    print("\n" + "=" * 70)
    print("TEST 4: Docker Smoke Script")
    print("=" * 70)

    try:
        script_path = repo_root / "scripts" / "chatdev_ci_smoke.sh"

        if script_path.exists():
            print(f"✅ Script found: {script_path}")

            with open(script_path) as f:
                content = f.read()

            lines = len(content.split("\n"))
            print(f"✅ Script size: {len(content)} bytes, {lines} lines")

            # Check for key elements
            if "docker" in content.lower():
                print("✅ Contains docker commands")
            if "sheepgreen/chatdev" in content:
                print("✅ Uses official ChatDev image")

            return True
        else:
            print(f"❌ Script not found: {script_path}")
            return False

    except Exception as e:
        print(f"❌ Docker smoke script test failed: {e}")
        return False


def main():
    """Run all Phase 3 smoke tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "PHASE 3: COMPREHENSIVE SMOKE TEST SUITE" + " " * 13 + "║")
    print("╚" + "=" * 68 + "╝")

    results = {
        "MCP Server": test_mcp_server(),
        "MCP Registry": test_mcp_registry(),
        "ChatDev Launcher": test_chatdev_launcher(),
        "Docker Script": test_docker_smoke_script(),
    }

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\n{'✅ ALL TESTS PASSED' if passed == total else '⚠️  SOME TESTS FAILED'}")
    print(f"Result: {passed}/{total} tests passed")
    print("=" * 70)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
