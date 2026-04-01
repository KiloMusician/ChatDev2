#!/usr/bin/env python3
"""Quick ChatDev MCP test - uses existing running server"""

import os
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).parent.parent
CHATDEV_PATH_CANDIDATES = [
    Path("C:/Users/keath/NuSyQ/ChatDev"),
    Path(os.getenv("CHATDEV_PATH", "")),
]
CHATDEV_PATH = next((p for p in CHATDEV_PATH_CANDIDATES if p.exists()), CHATDEV_PATH_CANDIDATES[0])
MCP_SERVER_URL = "http://localhost:8081"


def test_health():
    """Test /health endpoint"""
    print("\n🏥 Testing /health endpoint...")
    try:
        response = requests.get(f"{MCP_SERVER_URL}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Tools available: {len(data.get('tools', []))}")
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_manifest():
    """Test /manifest endpoint"""
    print("\n📋 Testing /manifest endpoint...")
    try:
        response = requests.get(f"{MCP_SERVER_URL}/manifest", timeout=5)
        data = response.json()
        tools = [t["name"] for t in data.get("tools", [])]
        print(f"   Server: {data.get('name')}")
        print(f"   Tools: {len(tools)}")

        if "chatdev_run" in tools and "chatdev_status" in tools:
            print("✅ ChatDev tools registered")
            return True
        else:
            print("❌ ChatDev tools missing")
            return False
    except Exception as e:
        print(f"❌ Manifest check failed: {e}")
        return False


def test_chatdev_task():
    """Test chatdev_run with simple task"""
    print("\n🏗️  Testing chatdev_run endpoint...")
    print("   Task: Create a Python fibonacci calculator")

    payload = {
        "tool": "chatdev_run",
        "parameters": {
            "task": "Create a Python function that calculates fibonacci numbers up to n.",
            "name": "e2e_quick_fibonacci",
            "model": "qwen2.5-coder:7b",
            "use_ollama": True,
        },
    }

    try:
        print("📤 Sending ChatDev request (timeout=900s)...")
        response = requests.post(
            f"{MCP_SERVER_URL}/execute",
            json=payload,
            timeout=900,
        )

        if response.status_code == 200:
            data = response.json()
            success = bool(data.get("success"))
            if not success:
                print(f"❌ MCP returned failure: {data.get('error')}")
                return False

            result = data.get("result", {}) if isinstance(data, dict) else {}
            print(f"✅ Task submitted: {result.get('name')}")
            print(f"   PID: {result.get('pid')}")

            # Quick check for project
            project_path = CHATDEV_PATH / "WareHouse" / "e2e_quick_fibonacci"
            if project_path.exists():
                print("✅ Project directory created")
                py_files = list(project_path.rglob("*.py"))
                if py_files:
                    print(f"✅ Generated {len(py_files)} Python files")
                    return True
                else:
                    print("⚠️  Project exists but no Python files yet")
                    return False
            return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print("⚠️  Request timed out (checking if project was created anyway)")
        project_path = CHATDEV_PATH / "WareHouse" / "e2e_quick_fibonacci"
        if project_path.exists():
            print(f"✅ Project found despite timeout: {project_path}")
            return True
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("=" * 60)
    print("🧪 ChatDev MCP Quick Test (No Server Startup)")
    print("=" * 60)

    results = {
        "health": test_health(),
        "manifest": test_manifest(),
        "chatdev_run": test_chatdev_task(),
    }

    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
