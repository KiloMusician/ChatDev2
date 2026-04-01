import json

import requests

# Check manifest
print("🔍 Checking MCP Server manifest...")
r = requests.get("http://localhost:8081/manifest")
data = r.json()

print(f"\n✅ Server: {data['name']}")
print(f"✅ Version: {data['version']}")
print(f"✅ Total tools: {len(data['tools'])}")

print("\n📋 Registered tools:")
for tool in data["tools"]:
    print(f"  • {tool['name']}")

# Check for ChatDev tools
chatdev_tools = [t for t in data["tools"] if "chatdev" in t["name"].lower()]
if chatdev_tools:
    print(f"\n✅ {len(chatdev_tools)} ChatDev tools found:")
    for t in chatdev_tools:
        print(f"  • {t['name']}")
else:
    print("\n❌ No ChatDev tools found!")

print("\n" + "=" * 60)
print("🧪 Now testing chatdev_run via /execute endpoint...")
print("=" * 60)

# Test ChatDev run endpoint using /execute with tool name
payload = {
    "tool": "chatdev_run",
    "parameters": {
        "task": "Create a simple Python function that adds two numbers. Include docstring and return the sum.",
        "name": "mcp_test_adder",
        "model": "GPT_4O_MINI",  # ChatDev expects uppercase with underscores
    },
}

print("\n📤 Sending request to /execute...")
print("   Tool: chatdev_run")
print(f"   Task: {payload['parameters']['task'][:60]}...")
print(f"   Project name: {payload['parameters']['name']}")

try:
    # Send request with 5 minute timeout (ChatDev may need time)
    r = requests.post("http://localhost:8081/execute", json=payload, timeout=300)

    if r.status_code == 200:
        result = r.json()
        print("\n✅ ChatDev request successful!")
        print("\n📋 Full response:")
        print(json.dumps(result, indent=2))

        # Check expected fields
        if result.get("success"):
            print("\n✅ Execution succeeded!")
            if "result" in result:
                print(f"   Result: {result['result']}")
        else:
            print("\n⚠️ Execution had issues:")
            print(f"   Error: {result.get('error', 'Unknown')}")
    else:
        print(f"\n❌ Request failed: HTTP {r.status_code}")
        print(f"   Response: {r.text}")

except requests.exceptions.Timeout:
    print("\n⚠️ Request timed out (ChatDev may still be running)")
except Exception as e:
    print(f"\n❌ Error: {e}")
