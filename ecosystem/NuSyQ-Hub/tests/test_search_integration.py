"""Test SmartSearch CLI integration.

Coverage:
  - Search action CLI wiring
  - Keyword search functionality
  - Index health check
"""

import subprocess
import sys
from pathlib import Path

# Ensure NuSyQ-Hub is importable
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))


def test_search_keyword_cli():
    """Test search keyword via CLI."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/start_nusyq.py",
            "search",
            "keyword",
            "consciousness",
            "--limit",
            "3",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"Exit code {result.returncode}: {result.stderr}"
    assert "Keyword Search" in result.stdout, "Should show search results header"
    assert "matches" in result.stdout.lower(), "Should show match count"
    print("✅ test_search_keyword_cli PASSED")


def test_search_index_health_cli():
    """Test search index-health via CLI."""
    result = subprocess.run(
        [sys.executable, "scripts/start_nusyq.py", "search", "index-health"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"Exit code {result.returncode}: {result.stderr}"
    assert "Index Health" in result.stdout or "Health" in result.stdout, "Should show index health"
    print("✅ test_search_index_health_cli PASSED")


def test_search_dispatcher_help():
    """Test search dispatcher shows help."""
    result = subprocess.run(
        [sys.executable, "scripts/start_nusyq.py", "search"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    # Search with no args shows help
    assert "Subcommands" in result.stdout or "keyword" in result.stdout, "Should show help"
    print("✅ test_search_dispatcher_help PASSED")


if __name__ == "__main__":
    print("\n🧪 Testing SmartSearch CLI Integration\n")
    test_search_keyword_cli()
    test_search_index_health_cli()
    test_search_dispatcher_help()
    print("\n✅ All SmartSearch integration tests passed!\n")
