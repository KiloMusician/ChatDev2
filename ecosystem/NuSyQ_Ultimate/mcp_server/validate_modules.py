"""Quick validation script for modular MCP server components.

This script is intentionally **Copilot-friendly**:
- Uses importlib guards instead of direct imports (avoids missing-module noise)
- Emits human-readable status lines for each capability
- Keeps state in memory only (no external deps)
"""

import asyncio
import importlib
import importlib.util
import sys
from pathlib import Path

# Set UTF-8 encoding for console output on Windows
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def _module_available(module_name: str) -> bool:
    """Return True if a module can be imported."""

    return importlib.util.find_spec(module_name) is not None


def _import_optional(module_name: str, members: list[str] | None = None):
    """Import a module (and optionally members) if available.

    Returns the imported module or list of members, or ``None`` if unavailable.
    """

    if not _module_available(module_name):
        print(f"⚠ {module_name} not found (optional)")
        return None

    module = importlib.import_module(module_name)
    if not members:
        return module

    resolved = [getattr(module, name) for name in members]
    if len(resolved) == 1:
        return resolved[0]
    return resolved


def test_imports():
    """Test that all our modules can be imported"""
    print("Testing imports...")

    checks = [
        ("models", ["MCPRequest", "OllamaQueryRequest", "FileReadRequest"]),
        ("config", ["ConfigManager", "ServiceConfig", "OllamaConfig"]),
        ("security", ["SecurityValidator"]),
        ("file_ops", ["FileOperationsService"]),
        ("ollama", ["OllamaService"]),
    ]

    all_ok = True
    for module_name, members in checks:
        imported = _import_optional(module_name, members)
        if imported:
            print(f"✓ {module_name} imported successfully")
        else:
            all_ok = False

    return all_ok


def test_model_validation():
    """Test model validation"""
    print("\nTesting model validation...")

    models = _import_optional("models", ["MCPRequest", "OllamaQueryRequest"])
    if not models:
        print("⚠ Models module not available - skipping validation tests")
        return True

    mcp_request, ollama_request = models

    # Test valid MCP request
    request = mcp_request(method="tools/list", params={})
    print(f"✓ Valid MCP request: {request.method}")

    # Test valid Ollama request
    ollama_req = ollama_request(
        model="qwen2.5-coder:7b",
        prompt="Hello world",
        max_tokens=50,
    )
    print(f"✓ Valid Ollama request: {ollama_req.model}")

    # Test invalid request (should raise exception)
    try:
        _ = mcp_request(method="invalid/method", params={})
        print("✗ Should have failed validation")
        return False
    except ValueError:
        print("✓ Invalid request properly rejected")

    return True


def test_security_validation():
    """Test security validation"""
    print("\nTesting security validation...")

    validator_cls = _import_optional("security", ["SecurityValidator"])
    if not validator_cls:
        print("⚠ Security module not available - skipping tests")
        return True

    validator = validator_cls()

    # Test model name validation
    assert validator.validate_model_name("qwen2.5-coder:7b")
    print("✓ Valid model name accepted")

    assert not validator.validate_model_name("invalid model name")
    print("✓ Invalid model name rejected")

    # Test input sanitization
    clean = validator.sanitize_input("Hello, world!")
    assert clean == "Hello, world!"
    print("✓ Clean input preserved")

    dirty = validator.sanitize_input("Hello <script>alert()</script>")
    assert "<script>" not in dirty
    print("✓ Dangerous input sanitized")

    # Test code safety
    assert validator.is_safe_code("print('hello')")
    print("✓ Safe code accepted")

    assert not validator.is_safe_code("import os; os.system('rm -rf /')")
    print("✓ Dangerous code rejected")

    return True


def test_config_manager():
    """Test configuration manager"""
    print("\nTesting configuration manager...")

    config_manager_cls = _import_optional("config", ["ConfigManager"])
    if not config_manager_cls:
        print("⚠ Config module not available - skipping tests")
        return True

    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as handle:
        config_manager = config_manager_cls(handle.name)

        # Test default config creation
        service_config = config_manager.get_service_config()
        assert service_config.host == "localhost"
        print("✓ Service config loaded with defaults")

        ollama_config = config_manager.get_ollama_config()
        assert ollama_config.port == 11434
        print("✓ Ollama config loaded with defaults")

        # Test get/set operations
        config_manager.set("test.value", "hello")
        assert config_manager.get("test.value") == "hello"
        print("✓ Config get/set operations work")

    return True


async def test_async_services():
    """Test async service components"""
    print("\nTesting async services...")

    ollama_service_cls = _import_optional("ollama", ["OllamaService"])
    if not ollama_service_cls:
        print("⚠️  Ollama module not available (optional dependency)")
        return True

    config_cls = _import_optional("config", ["OllamaConfig"])
    request_cls = _import_optional("models", ["OllamaQueryRequest"])
    if not (config_cls and request_cls):
        print("⚠️  Config or models module missing - skipping async service tests")
        return True

    config = config_cls(host="localhost", port=11434)
    service = ollama_service_cls(config)
    assert service.base_url == "http://localhost:11434"
    print("✓ Ollama service initialized")

    # Test request creation (don't actually call Ollama)
    _ = request_cls(
        model="qwen2.5-coder:7b",
        prompt="Test prompt",
        max_tokens=50,
    )
    print("✓ Ollama request created")

    # Clean up
    await service.close()
    print("✓ Service cleanup completed")

    return True


async def main():
    """Run all validation tests"""
    print("🚀 NuSyQ MCP Server - Modular Component Validation")
    print("=" * 60)

    tests = [
        ("Module Imports", test_imports),
        ("Model Validation", test_model_validation),
        ("Security Validation", test_security_validation),
        ("Configuration Manager", test_config_manager),
        ("Async Services", test_async_services),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)

        if asyncio.iscoroutinefunction(test_func):
            success = await test_func()
        else:
            success = test_func()

        results.append((test_name, success))

        if success:
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")

    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All modular components validated successfully!")
        print("🚀 Ready for integration into main MCP server")
    else:
        print("⚠️  Some components need attention before integration")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
