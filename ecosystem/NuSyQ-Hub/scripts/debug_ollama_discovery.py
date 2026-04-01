"""Debug script to test Ollama model discovery."""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from integration.Ollama_Integration_Hub import KILOOllamaHub, list_ollama_models
except ImportError:
    print("FAILED: Could not import KILOOllamaHub")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

print("\n" + "=" * 60)
print("OLLAMA MODEL DISCOVERY DEBUG")
print("=" * 60)

# Test 1: Direct API call
print("\n1. Testing direct API call via list_ollama_models():")
print("-" * 60)
models_from_api = list_ollama_models()
print(f"   Models found: {len(models_from_api)}")
if models_from_api:
    print(f"   First model: {models_from_api[0].get('name', 'unknown')}")
    print(f"   Model structure: {list(models_from_api[0].keys())}")
else:
    print("   ⚠️  WARNING: No models returned from direct API call!")

# Test 2: Ollama client
print("\n2. Testing ollama client import:")
print("-" * 60)
try:
    import ollama

    print(f"   ✅ ollama module imported: {ollama.__name__}")
    print(f"   Has Client: {hasattr(ollama, 'Client')}")

    # Try to create client
    try:
        client = ollama.Client()
        print(f"   ✅ Client created: {type(client)}")
        print(f"   Has list method: {hasattr(client, 'list')}")

        if hasattr(client, "list"):
            try:
                client_response = client.list()
                print(f"   Client list() response type: {type(client_response)}")
                print(f"   Client list() response: {client_response}")

                # Check if it's a dict
                if isinstance(client_response, dict):
                    print(f"   Response keys: {client_response.keys()}")
                    if "models" in client_response:
                        print(f"   Models in response: {len(client_response['models'])}")
                    elif "data" in client_response:
                        print(f"   Data in response: {len(client_response['data'])}")

                # Check if it has attributes
                if hasattr(client_response, "models"):
                    models_attr = client_response.models
                    print(
                        f"   Has models attribute: {type(models_attr)}, length: {len(models_attr) if isinstance(models_attr, list) else 'N/A'}"
                    )

                if hasattr(client_response, "model_dump"):
                    dumped = client_response.model_dump()
                    print(f"   model_dump() result: {type(dumped)}")
                    if isinstance(dumped, dict):
                        print(f"   model_dump() keys: {dumped.keys()}")

            except Exception as e:
                print(f"   ⚠️  ERROR calling client.list(): {e}")
    except Exception as e:
        print(f"   ⚠️  ERROR creating client: {e}")

except ImportError as e:
    print(f"   ⚠️  ollama module not installed: {e}")

# Test 3: KILOOllamaHub initialization
print("\n3. Testing KILOOllamaHub initialization:")
print("-" * 60)
try:
    hub = KILOOllamaHub()
    print("   ✅ Hub created")
    print(f"   Connected: {hub.is_connected}")
    print(f"   Client type: {type(hub.client)}")
    print(f"   Available models count: {len(hub.available_models)}")

    if hub.available_models:
        print(f"   Model names: {list(hub.available_models.keys())}")
    else:
        print("   ⚠️  WARNING: No models discovered by hub!")

        # Try manual discovery
        print("\n   Attempting manual discovery:")
        discovered = hub.discover_models()
        print(f"   Manual discovery result: {len(discovered)} models")
        if discovered:
            print(f"   Model names: {list(discovered.keys())}")

except Exception as e:
    print(f"   ❌ ERROR: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60 + "\n")
