"""
Integration test for MCP server retry logic and error handling
"""
import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))
# pylint: disable=wrong-import-position
from mcp_server.main import NuSyQMCPServer  # noqa: E402


async def test_ollama_retry_logic():
    """Test Ollama query retry with simulated failures"""
    print("\n" + "=" * 60)
    print("TESTING RETRY LOGIC")
    print("=" * 60 + "\n")

    server = NuSyQMCPServer()

    # Test 1: Normal query (should work)
    print("Test 1: Normal Ollama query...")
    result = await server._ollama_query(  # pylint: disable=protected-access
        {
            "model": "qwen2.5-coder:7b",
            "prompt": "Say 'test' in one word.",
            "max_tokens": 10,
        }
    )

    if result["success"]:
        print(f"✅ Success on attempt {result.get('retries', 0) + 1}")
        print(f"   Response: {result['response'][:50]}...")
    else:
        print(f"❌ Failed: {result.get('error')}")

    # Test 2: Invalid model (should retry 3 times then fail)
    print("\nTest 2: Invalid model (expect retries)...")
    result = await server._ollama_query(  # pylint: disable=protected-access
        {
            "model": "nonexistent-model:latest",
            "prompt": "This will fail",
            "max_tokens": 10,
        },
        max_retries=2,
        base_delay=0.5,
    )

    if not result["success"]:
        print(f"✅ Failed as expected after "
              f"{result.get('retries', 0)} retries")
        print(f"   Error: {result.get('error')}")
    else:
        print("❌ Should have failed but didn't")

    print("\n" + "=" * 60)
    print("RETRY LOGIC TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_ollama_retry_logic())
