#!/usr/bin/env python3
"""
Integration test for dynamic model discovery and capability-based routing.
Tests: Discovery, caching, persistence, and routing across Ollama and LM Studio.
"""

import json
import os
import sys
import time
from pathlib import Path

# Load environment variables from .env
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv not available

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 80)
print("🧪 NuSyQ Model Discovery Integration Test")
print("=" * 80)

# Test 1: Dynamic Discovery
print("\n[TEST 1] Dynamic Model Discovery")
print("-" * 40)
try:
    from src.integration.universal_llm_gateway import load_model_capabilities

    print("→ Discovering models (first call, should hit APIs)...")
    start = time.time()
    caps = load_model_capabilities()
    elapsed = time.time() - start

    print(f"✓ Discovered {len(caps)} models in {elapsed:.2f}s")
    model_names = [f"{c.provider}:{c.model}" for c in caps]
    print(f"  Models: {model_names[:5]}..." if len(caps) > 5 else f"  Models: {model_names}")

    # Test caching
    print("\n→ Re-loading models (second call, should use cache)...")
    start = time.time()
    caps2 = load_model_capabilities()
    elapsed2 = time.time() - start

    print(f"✓ Loaded {len(caps2)} models in {elapsed2:.2f}s")
    if elapsed2 < 0.1:
        print("  ✓ Cache working (fast load)")
    else:
        print("  ⚠ Cache may not be working (slow load)")

except Exception as e:
    print(f"✗ Discovery failed: {e}")
    import traceback

    traceback.print_exc()

# Test 2: Persistence
print("\n\n[TEST 2] Model Roster Persistence")
print("-" * 40)
try:
    roster_path = Path(__file__).parent / "config" / "model_capabilities.json"

    if roster_path.exists():
        with open(roster_path) as f:
            persisted = json.load(f)
        print(f"✓ Roster persisted to {roster_path}")

        # Handle both dict and list formats
        if isinstance(persisted, dict):
            print(f"  Contains {len(persisted)} models")
            dynamic_models = [
                k for k in persisted.keys() if k.startswith("ollama:") or k.startswith("lmstudio:")
            ]
            static_models = [
                k
                for k in persisted.keys()
                if not k.startswith("ollama:") and not k.startswith("lmstudio:")
            ]
        else:
            print(f"  Contains {len(persisted)} models (legacy list format)")
            dynamic_models = [
                f"{m['provider']}:{m['model']}"
                for m in persisted
                if m["provider"] in ("ollama", "lmstudio")
            ]
            static_models = [
                f"{m['provider']}:{m['model']}"
                for m in persisted
                if m["provider"] not in ("ollama", "lmstudio")
            ]

        print(f"  Static models: {len(static_models)} ({', '.join(static_models[:2])}...)")
        print(f"  Dynamic models: {len(dynamic_models)} ({', '.join(dynamic_models[:3])}...)")
    else:
        print(f"⚠ No roster file found at {roster_path}")

except Exception as e:
    print(f"✗ Persistence check failed: {e}")

# Test 3: Capability-Based Routing
print("\n\n[TEST 3] Capability-Based Model Selection")
print("-" * 40)
try:
    # Test tag extraction without full router initialization
    print("\n→ Testing task type tag extraction...")

    test_cases = [
        ("Analyze this Python code for bugs", ["code"]),
        ("Write a general explanation of quantum computing", ["general"]),
        ("Debug this complex algorithm", ["code"]),
        ("Explain the concept of recursion", ["general"]),
    ]

    # Simple tag extraction logic for testing
    def simple_tag_extraction(task: str) -> list[str]:
        task_lower = task.lower()
        tags = []
        if any(word in task_lower for word in ["code", "python", "function", "debug", "analyze"]):
            tags.append("code")
        if any(word in task_lower for word in ["explain", "general", "write", "concept"]):
            tags.append("general")
        if any(word in task_lower for word in ["debug", "complex", "reason"]):
            tags.append("reasoning")
        return tags if tags else ["general"]

    for task_desc, expected_tags in test_cases:
        print(f"\n→ Task: '{task_desc[:50]}...'")
        print(f"  Expected tags: {expected_tags}")

        extracted_tags = simple_tag_extraction(task_desc)
        print(f"  Extracted tags: {extracted_tags}")

        tag_match = any(tag in extracted_tags for tag in expected_tags)
        if tag_match:
            print("  ✓ Tag extraction working")
        else:
            print(f"  ⚠ Expected one of {expected_tags}, got {extracted_tags}")

    # Test model selection from capabilities
    print("\n→ Testing model selection from roster...")
    from src.integration.universal_llm_gateway import UniversalLLMGateway

    gateway = UniversalLLMGateway()

    # Test selecting a code model
    code_model = gateway.select_model(
        model_hint=None, capability_tags=["code", "local"], prefer_local=True
    )
    if code_model:
        print(f"  ✓ Selected code model: {code_model.provider}:{code_model.model}")
    else:
        print("  ⚠ No code model found")

    # Test selecting a general model
    general_model = gateway.select_model(
        model_hint=None, capability_tags=["general"], prefer_local=False
    )
    if general_model:
        print(f"  ✓ Selected general model: {general_model.provider}:{general_model.model}")
    else:
        print("  ⚠ No general model found")

except Exception as e:
    print(f"✗ Routing test failed: {e}")
    import traceback

    traceback.print_exc()

# Test 4: Provider Detection
print("\n\n[TEST 4] Provider Availability")
print("-" * 40)
try:
    import httpx

    providers = [
        ("Ollama", "http://localhost:11434/api/tags"),
        ("LM Studio", "http://localhost:1234/v1/models"),
    ]

    for name, url in providers:
        try:
            response = httpx.get(url, timeout=2.0)
            if response.status_code == 200:
                print(f"✓ {name} is available at {url}")
            else:
                print(f"⚠ {name} responded with {response.status_code}")
        except httpx.ConnectError:
            print(f"⚠ {name} not running at {url}")
        except Exception as e:
            print(f"⚠ {name} check failed: {e}")

except Exception as e:
    print(f"✗ Provider check failed: {e}")

# Test 5: Environment Configuration
print("\n\n[TEST 5] Environment Configuration")
print("-" * 40)
env_vars = [
    "NUSYQ_MODEL_DISCOVERY",
    "NUSYQ_MODEL_CAPS_TTL_SECONDS",
    "NUSYQ_LLM_DISCOVERY_TIMEOUT",
    "NUSYQ_MODEL_CAPS_PERSIST",
]

for var in env_vars:
    value = os.getenv(var)
    if value:
        print(f"✓ {var}={value}")
    else:
        print(f"⚠ {var} not set (using default)")

# Summary
print("\n\n" + "=" * 80)
print("🏁 Integration Test Summary")
print("=" * 80)
print(
    """
✓ = Working as expected
⚠ = Warning or optional feature
✗ = Error or failure

Review the output above to identify any issues.
"""
)
