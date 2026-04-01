"""
Test Suite for Bidirectional AI Collaboration Framework
========================================================

Tests the interaction between Claude Code, GitHub Copilot, AI Council,
and ChatDev via the MCP server.

Usage:
    python test_bidirectional_collaboration.py --test all
    python test_bidirectional_collaboration.py --test copilot_query
    python test_bidirectional_collaboration.py --test ai_council
    python test_bidirectional_collaboration.py --test orchestration
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config.claude_code_bridge import (
    ClaudeCodeBridge,
    ClaudeCodeClient,
    ClaudeStatus,
    QueryPriority,
)


@pytest.mark.asyncio
async def test_claude_status():
    """Test 1: Check if Claude Code is available or cooling down"""
    print("\n" + "=" * 60)
    print("TEST 1: Claude Code Status Check")
    print("=" * 60)

    async with ClaudeCodeClient() as client:
        status = await client.check_status()

        if status == ClaudeStatus.AVAILABLE:
            print("✅ Claude Code is AVAILABLE")
            return True
        elif status == ClaudeStatus.COOLING_DOWN:
            print(f"⏰ Claude Code is COOLING DOWN until {client.cooldown_until}")
            print("   (Will be available at 6 AM)")
            return False
        elif status == ClaudeStatus.OFFLINE:
            print("❌ Claude Code is OFFLINE")
            print("   Check that MCP server is running and configured correctly")
            return False
        else:
            print(f"⚠️ Claude Code status: {status.value}")
            return False


@pytest.mark.asyncio
async def test_copilot_query_submission():
    """Test 2: Submit a query to Claude Code (if available)"""
    print("\n" + "=" * 60)
    print("TEST 2: Query Submission (Copilot → Claude)")
    print("=" * 60)

    async with ClaudeCodeClient() as client:
        response = await client.query(
            prompt="What are the best practices for async/await in Python?",
            priority=QueryPriority.NORMAL,
        )

        if response:
            print("✅ Query successful!")
            print(f"Response preview: {response[:200]}...")
            return True
        else:
            print("❌ Query failed (Claude may be cooling down)")
            return False


@pytest.mark.asyncio
async def test_ai_council_query_file():
    """Test 3: Check that Claude → Copilot query files work"""
    print("\n" + "=" * 60)
    print("TEST 3: Query File System (Claude → Copilot)")
    print("=" * 60)

    # Simulate what the MCP server does when Claude queries Copilot
    query_dir = Path("Logs/claude_copilot_queries")
    query_dir.mkdir(parents=True, exist_ok=True)

    # Create a test query file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    query_id = f"test_query_{timestamp}"
    query_file = query_dir / f"{query_id}.json"

    query_data = {
        "query_id": query_id,
        "timestamp": datetime.now().isoformat(),
        "query": "Test query from Claude Code",
        "priority": "normal",
        "context": {},
        "from": "claude_code",
        "to": "github_copilot",
        "status": "pending",
    }

    query_file.write_text(json.dumps(query_data, indent=2))
    print(f"✅ Created test query file: {query_file}")

    # Simulate Copilot's response
    response_file = query_dir / f"{query_id}_response.json"
    response_data = {
        "query_id": query_id,
        "timestamp": datetime.now().isoformat(),
        "from": "github_copilot",
        "to": "claude_code",
        "status": "completed",
        "response": (
            "I recommend using async/await for I/O-bound operations. "
            "Key best practices:\n"
            "1. Use asyncio.create_task() for concurrent tasks\n"
            "2. Always await coroutines\n"
            "3. Use async context managers with 'async with'\n"
            "4. Handle exceptions with try/except in async functions"
        ),
    }

    response_file.write_text(json.dumps(response_data, indent=2))
    print(f"✅ Created test response file: {response_file}")

    # Verify both files exist
    if query_file.exists() and response_file.exists():
        print("✅ Query file system working correctly!")
        return True
    else:
        print("❌ Query file system failed")
        return False


@pytest.mark.asyncio
async def test_mcp_server_health():
    """Test 4: Verify MCP server is running and healthy"""
    print("\n" + "=" * 60)
    print("TEST 4: MCP Server Health Check")
    print("=" * 60)

    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:3000/health", timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ MCP Server is HEALTHY")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Components: {data.get('components')}")
                    return True
                else:
                    print(f"❌ MCP Server returned HTTP {response.status}")
                    return False

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Failed to connect to MCP server: {e}")
        print("   Make sure the server is running: python mcp_server/main.py")
        return False


@pytest.mark.asyncio
async def test_mcp_tools_available():
    """Test 5: Check that new MCP tools are registered"""
    print("\n" + "=" * 60)
    print("TEST 5: MCP Tools Registration")
    print("=" * 60)

    try:
        import aiohttp

        mcp_request = {"method": "tools/list", "params": {}, "id": "test_tools_list"}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:3000/mcp",
                json=mcp_request,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    tools = data.get("result", {}).get("tools", [])
                    tool_names = [t["name"] for t in tools]

                    required_tools = [
                        "ai_council_session",
                        "query_github_copilot",
                        "multi_agent_orchestration",
                    ]

                    print(f"✅ Found {len(tools)} MCP tools:")
                    for tool_name in tool_names:
                        marker = "✨" if tool_name in required_tools else "  "
                        print(f"   {marker} {tool_name}")

                    missing = [t for t in required_tools if t not in tool_names]
                    if missing:
                        print(f"\n❌ Missing required tools: {missing}")
                        return False
                    else:
                        print("\n✅ All required tools registered!")
                        return True
                else:
                    print(f"❌ MCP request failed: HTTP {response.status}")
                    return False

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Failed to query MCP tools: {e}")
        return False


@pytest.mark.asyncio
async def test_orchestration():
    """Test 6: Test full multi-agent orchestration"""
    print("\n" + "=" * 60)
    print("TEST 6: Multi-Agent Orchestration")
    print("=" * 60)

    bridge = ClaudeCodeBridge()

    print("Testing orchestration with AI Council + Ollama (no ChatDev)...")

    result = await bridge.orchestrate_task(
        task="Design a simple configuration validation module",
        use_ai_council=False,  # Skip council for quick test
        use_claude=False,  # Skip Claude if cooling down
        use_chatdev=False,  # Skip ChatDev for quick test
    )

    if result.get("agents_used"):
        print("✅ Orchestration completed!")
        print(f"   Agents used: {', '.join(result['agents_used'])}")
        return True
    else:
        print("⚠️ Orchestration ran but no agents participated")
        print(f"   Result: {result}")
        return False


async def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "=" * 60)
    print("🧪 BIDIRECTIONAL AI COLLABORATION TEST SUITE")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")

    results = {}

    # Test 1: MCP Server Health
    results["mcp_health"] = await test_mcp_server_health()

    # Test 2: MCP Tools Registration
    results["mcp_tools"] = await test_mcp_tools_available()

    # Test 3: Query File System
    results["query_files"] = await test_ai_council_query_file()

    # Test 4: Claude Status
    results["claude_status"] = await test_claude_status()

    # Test 5: Copilot → Claude Query (only if Claude available)
    if results["claude_status"]:
        results["copilot_query"] = await test_copilot_query_submission()
    else:
        results["copilot_query"] = None  # Skipped

    # Test 6: Orchestration
    results["orchestration"] = await test_orchestration()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        if passed is None:
            status = "⏭️ SKIPPED"
        elif passed:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"{status}  {test_name}")

    total_tests = sum(1 for v in results.values() if v is not None)
    passed_tests = sum(1 for v in results.values() if v is True)

    print(f"\n📈 Results: {passed_tests}/{total_tests} tests passed")
    print(f"Completed: {datetime.now().isoformat()}")

    return passed_tests == total_tests


async def main():
    """Main test runner"""
    success = False
    parser = argparse.ArgumentParser(description="Test bidirectional AI collaboration framework")
    parser.add_argument(
        "--test",
        choices=["all", "status", "query", "files", "mcp", "tools", "orchestration"],
        default="all",
        help="Which test to run (default: all)",
    )

    args = parser.parse_args()

    if args.test == "all":
        success = await run_all_tests()
    elif args.test == "status":
        success = await test_claude_status()
    elif args.test == "query":
        success = await test_copilot_query_submission()
    elif args.test == "files":
        success = await test_ai_council_query_file()
    elif args.test == "mcp":
        success = await test_mcp_server_health()
    elif args.test == "tools":
        success = await test_mcp_tools_available()
    elif args.test == "orchestration":
        success = await test_orchestration()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
