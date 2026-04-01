#!/usr/bin/env python3
"""Phase C: Docker Sandbox Testing & Resource Validation.

Tests Docker container isolation, resource limits, and production pattern collection.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.resilience.sandbox_chatdev_validator import (
    ChatDevSandboxValidator,
    SandboxConfig,
    SandboxMode,
)

PRIMARY_MODEL_ENV = "NUSYQ_SANDBOX_MODEL_PRIMARY"
SECONDARY_MODEL_ENV = "NUSYQ_SANDBOX_MODEL_SECONDARY"
DEFAULT_MODEL_ENV = "OLLAMA_DEFAULT_MODEL"


def _get_model_from_env(primary: bool) -> str:
    if primary:
        value = os.getenv(PRIMARY_MODEL_ENV, "").strip()
        if value:
            return value
        value = os.getenv(DEFAULT_MODEL_ENV, "").strip()
        if value:
            return value
        return "qwen2.5-coder:7b"

    value = os.getenv(SECONDARY_MODEL_ENV, "").strip()
    if value:
        return value
    return "phi:latest"


def check_docker_available() -> dict:
    """Check if Docker daemon is accessible."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            # Extract version
            version_result = subprocess.run(
                ["docker", "version", "--format", "{{.Server.Version}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            version = version_result.stdout.strip() if version_result.returncode == 0 else "unknown"

            return {
                "available": True,
                "version": version,
                "info": result.stdout[:200],  # First 200 chars
            }
        else:
            return {
                "available": False,
                "error": result.stderr,
            }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
        }


async def test_process_isolated_mode() -> dict:
    """Test PROCESS_ISOLATED sandbox mode."""
    print("\n1️⃣  Testing PROCESS_ISOLATED Mode...")

    config = SandboxConfig(
        mode=SandboxMode.PROCESS_ISOLATED,
        memory_limit=1024,  # 1GB
        cpu_limit=0.5,  # 50% CPU
        timeout=60.0,  # 1 minute
    )

    validator = ChatDevSandboxValidator(config)

    start = time.time()
    model = _get_model_from_env(primary=True)
    result = await validator.validate_chatdev_run(
        task="Build a simple calculator",
        model=model,
        project_name="test_calculator",
    )
    elapsed = time.time() - start

    return {
        "mode": "PROCESS_ISOLATED",
        "model": model,
        "success": result.success,
        "execution_time": elapsed,
        "validation_score": result.validation_score,
        "audit_entries": len(result.audit_entries),
        "output_files": result.output.get("file_count", 0) if result.output else 0,
        "resource_usage": result.resource_usage,
    }


async def test_local_only_mode() -> dict:
    """Test LOCAL_ONLY sandbox mode."""
    print("\n2️⃣  Testing LOCAL_ONLY Mode...")

    config = SandboxConfig(
        mode=SandboxMode.LOCAL_ONLY,
        memory_limit=512,  # 512MB
        timeout=30.0,  # 30 seconds
    )

    validator = ChatDevSandboxValidator(config)

    start = time.time()
    model = _get_model_from_env(primary=False)
    result = await validator.validate_chatdev_run(
        task="Create a hello world app",
        model=model,
        project_name="test_hello",
    )
    elapsed = time.time() - start

    return {
        "mode": "LOCAL_ONLY",
        "model": model,
        "success": result.success,
        "execution_time": elapsed,
        "validation_score": result.validation_score,
        "audit_entries": len(result.audit_entries),
        "output_files": result.output.get("file_count", 0) if result.output else 0,
        "resource_usage": result.resource_usage,
    }


async def test_container_mode() -> dict:
    """Test CONTAINER mode (Docker-based)."""
    print("\n3️⃣  Testing CONTAINER Mode (Docker)...")

    # Check Docker first
    docker_status = check_docker_available()
    if not docker_status["available"]:
        return {
            "mode": "CONTAINER",
            "skipped": True,
            "reason": f"Docker not available: {docker_status.get('error', 'unknown')}",
        }

    print(f"    ✅ Docker available: {docker_status['version']}")

    config = SandboxConfig(
        mode=SandboxMode.CONTAINER,
        memory_limit=2048,  # 2GB
        cpu_limit=1.0,  # 1 CPU
        timeout=300.0,  # 5 minutes
        network_allowed=False,  # Network isolation
        disk_limit=1000,  # 1GB disk
    )

    validator = ChatDevSandboxValidator(config)

    start = time.time()
    model = _get_model_from_env(primary=True)
    result = await validator.validate_chatdev_run(
        task="Build a Docker-safe app",
        model=model,
        project_name="test_docker_app",
    )
    elapsed = time.time() - start

    return {
        "mode": "CONTAINER",
        "model": model,
        "success": result.success,
        "execution_time": elapsed,
        "validation_score": result.validation_score,
        "audit_entries": len(result.audit_entries),
        "output_files": result.output.get("file_count", 0) if result.output else 0,
        "resource_usage": result.resource_usage,
        "docker_version": docker_status["version"],
    }


async def test_resource_enforcement() -> dict:
    """Test resource limit enforcement."""
    print("\n4️⃣  Testing Resource Enforcement...")

    # Test with very low limits to trigger enforcement
    config = SandboxConfig(
        mode=SandboxMode.PROCESS_ISOLATED,
        memory_limit=128,  # Very low - 128MB
        cpu_limit=0.25,  # Very low - 25% CPU
        timeout=10.0,  # Short timeout
    )

    validator = ChatDevSandboxValidator(config)

    start = time.time()
    model = _get_model_from_env(primary=True)
    result = await validator.validate_chatdev_run(
        task="Build a resource-intensive app",
        model=model,
        project_name="test_resource_enforcement",
    )
    elapsed = time.time() - start

    return {
        "test": "resource_enforcement",
        "model": model,
        "success": result.success,
        "execution_time": elapsed,
        "timeout_triggered": elapsed >= config.timeout,
        "config_limits": {
            "memory_mb": config.memory_limit,
            "cpu_cores": config.cpu_limit,
            "timeout_sec": config.timeout,
        },
        "actual_usage": result.resource_usage,
    }


async def collect_production_patterns() -> dict:
    """Collect production usage patterns from audit log."""
    print("\n5️⃣  Collecting Production Patterns...")

    audit_log_path = Path("state/audit.jsonl")

    if not audit_log_path.exists():
        return {
            "collected": False,
            "reason": "Audit log not found",
        }

    # Parse audit log
    patterns = {
        "total_entries": 0,
        "by_action": {},
        "by_result": {},
        "execution_modes": {},
        "avg_execution_time": 0.0,
    }

    execution_times = []

    with open(audit_log_path) as f:
        for line in f:
            try:
                entry = json.loads(line)
                patterns["total_entries"] += 1

                action = entry.get("action", "unknown")
                result = entry.get("result", "unknown")

                patterns["by_action"][action] = patterns["by_action"].get(action, 0) + 1
                patterns["by_result"][result] = patterns["by_result"].get(result, 0) + 1

                # Track execution modes
                if "execution_mode" in entry.get("context", {}):
                    mode = entry["context"]["execution_mode"]
                    patterns["execution_modes"][mode] = patterns["execution_modes"].get(mode, 0) + 1

                # Track execution times
                if "execution_time" in entry.get("context", {}):
                    execution_times.append(entry["context"]["execution_time"])

            except json.JSONDecodeError:
                continue

    if execution_times:
        patterns["avg_execution_time"] = sum(execution_times) / len(execution_times)
        patterns["max_execution_time"] = max(execution_times)
        patterns["min_execution_time"] = min(execution_times)

    return {
        "collected": True,
        "patterns": patterns,
        "audit_log_path": str(audit_log_path),
    }


async def main() -> None:
    """Run Phase C testing suite."""
    print("\n" + "=" * 80)
    print("Phase C: Docker Sandbox Integration & Resource Validation")
    print("=" * 80)

    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tests": {},
    }

    # Check Docker availability first
    print("\n🐳 Docker Status Check...")
    docker_status = check_docker_available()
    if docker_status["available"]:
        print(f"    ✅ Docker available: {docker_status['version']}")
    else:
        print(f"    ⚠️  Docker not available: {docker_status.get('error', 'unknown')}")

    results["docker_status"] = docker_status

    # Run tests
    try:
        results["tests"]["process_isolated"] = await test_process_isolated_mode()
        print(f"    ✅ Result: {results['tests']['process_isolated']['success']}")
    except Exception as e:
        results["tests"]["process_isolated"] = {"error": str(e)}
        print(f"    ❌ Error: {e}")

    try:
        results["tests"]["local_only"] = await test_local_only_mode()
        print(f"    ✅ Result: {results['tests']['local_only']['success']}")
    except Exception as e:
        results["tests"]["local_only"] = {"error": str(e)}
        print(f"    ❌ Error: {e}")

    try:
        results["tests"]["container"] = await test_container_mode()
        if "skipped" in results["tests"]["container"]:
            print(f"    ⏭️  Skipped: {results['tests']['container']['reason']}")
        else:
            print(f"    ✅ Result: {results['tests']['container']['success']}")
    except Exception as e:
        results["tests"]["container"] = {"error": str(e)}
        print(f"    ❌ Error: {e}")

    try:
        results["tests"]["resource_enforcement"] = await test_resource_enforcement()
        print(f"    ✅ Result: {results['tests']['resource_enforcement']['success']}")
    except Exception as e:
        results["tests"]["resource_enforcement"] = {"error": str(e)}
        print(f"    ❌ Error: {e}")

    try:
        results["patterns"] = await collect_production_patterns()
        if results["patterns"]["collected"]:
            print(f"    ✅ Collected {results['patterns']['patterns']['total_entries']} audit entries")
        else:
            print(f"    ⏭️  Skipped: {results['patterns']['reason']}")
    except Exception as e:
        results["patterns"] = {"error": str(e)}
        print(f"    ❌ Error: {e}")

    # Save results
    report_path = Path("state/reports/phase_c_sandbox_test_results.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(results, indent=2, default=str))

    # Summary
    print("\n" + "=" * 80)
    print("Phase C Test Summary")
    print("=" * 80)

    total_tests = len([t for t in results["tests"].values() if "error" not in t and not t.get("skipped")])
    passed_tests = len([t for t in results["tests"].values() if t.get("success")])

    print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
    print(f"📊 Report saved: {report_path}")

    if docker_status["available"]:
        print(f"🐳 Docker: Available (v{docker_status['version']})")
    else:
        print("⚠️  Docker: Not available (container mode skipped)")

    if results["patterns"].get("collected"):
        patterns = results["patterns"]["patterns"]
        print("\n📈 Production Patterns:")
        print(f"   Total audit entries: {patterns['total_entries']}")
        if patterns.get("execution_modes"):
            print(f"   Execution modes: {patterns['execution_modes']}")
        if patterns.get("avg_execution_time"):
            print(f"   Avg execution time: {patterns['avg_execution_time']:.2f}s")

    print("\n" + "=" * 80)
    print(f"Phase C testing complete. Results: {report_path}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
