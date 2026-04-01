#!/usr/bin/env python3
"""Live instantiation test for OpenClaw Gateway Bridge."""

print("\n" + "=" * 70)
print("🔌 OpenClaw Gateway Bridge - Live Instantiation Test")
print("=" * 70 + "\n")

# Test 1: Import
print("1️⃣  Testing imports...")
try:
    from src.integrations.openclaw_gateway_bridge import (
        OpenClawGatewayBridge,
        get_openclaw_gateway_bridge,
    )

    print("   ✅ Gateway bridge imported")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    exit(1)

# Test 2: Instantiate with defaults
print("\n2️⃣  Testing default instantiation...")
try:
    bridge = OpenClawGatewayBridge()
    print("   ✅ Bridge instantiated")
    print(f"      - Gateway URL: {bridge.gateway_url}")
    print(f"      - Timeout: {bridge.timeout_seconds}s")
    print(f"      - Running: {bridge.running}")
except Exception as e:
    print(f"   ❌ Instantiation failed: {e}")
    exit(1)

# Test 3: Instantiate with custom config
print("\n3️⃣  Testing custom configuration...")
try:
    custom_bridge = OpenClawGatewayBridge(
        gateway_url="ws://custom.example.com:9999", timeout_seconds=60
    )
    print("   ✅ Custom bridge instantiated")
    print(f"      - Gateway URL: {custom_bridge.gateway_url}")
    print(f"      - Timeout: {custom_bridge.timeout_seconds}s")
except Exception as e:
    print(f"   ❌ Custom config failed: {e}")
    exit(1)

# Test 4: Singleton pattern
print("\n4️⃣  Testing singleton pattern...")
try:
    bridge1 = get_openclaw_gateway_bridge()
    bridge2 = get_openclaw_gateway_bridge()
    assert bridge1 is bridge2
    print("   ✅ Singleton pattern working")
    print(f"      - Same instance: {bridge1 is bridge2}")
except Exception as e:
    print(f"   ❌ Singleton test failed: {e}")
    exit(1)

# Test 5: Configuration loading
print("\n5️⃣  Testing configuration loading...")
try:
    import json
    from pathlib import Path

    config_path = Path("config/secrets.json")
    with open(config_path) as f:
        config = json.load(f)

    openclaw_config = config.get("openclaw", {})
    print("   ✅ Configuration loaded")
    print(f"      - Gateway: {openclaw_config.get('gateway_url')}")
    print(f"      - Timeout: {openclaw_config.get('timeout_seconds')}s")
    print(f"      - Enabled: {openclaw_config.get('enabled')}")
    print(f"      - Channels configured: {len(openclaw_config.get('channels', {}))}")
except Exception as e:
    print(f"   ❌ Configuration load failed: {e}")
    exit(1)

# Test 6: Method availability
print("\n6️⃣  Testing available methods...")
try:
    methods = [
        "connect",
        "listen_for_messages",
        "handle_inbound_message",
        "send_result",
        "disconnect",
        "run",
    ]

    bridge = get_openclaw_gateway_bridge()
    for method in methods:
        if hasattr(bridge, method):
            print(f"   ✅ {method}() available")
        else:
            raise AttributeError(f"Missing method: {method}")
except Exception as e:
    print(f"   ❌ Method check failed: {e}")
    exit(1)

print("\n" + "=" * 70)
print("✅ All instantiation tests PASSED")
print("=" * 70)
print("\nGateway bridge is ready for deployment!")
print("\nNext steps:")
print("  1. Start OpenClaw Gateway: openclaw gateway")
print("  2. Start NuSyQ-Hub with bridge: python src/main.py --openclaw-enabled")
print("  3. Send message from Slack/Discord/Telegram/etc.")
print("  4. Agent processes and responds in same channel")
print()
