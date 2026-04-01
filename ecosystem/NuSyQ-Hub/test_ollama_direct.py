"""Direct Ollama API test to diagnose generation issues."""

import json
import time

import requests


def test_ollama():
    """Test direct Ollama API call."""
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": "phi3.5:latest",
        "prompt": "Write a simple Python function that adds two numbers. Just return the code, no explanation.",
        "stream": False,
        "temperature": 0.2,
    }

    print("🧪 Testing Ollama API...")
    print(f"Model: {payload['model']}")
    print(f"Prompt: {payload['prompt'][:50]}...")

    try:
        start_time = time.time()
        print("\n⏳ Sending request...")

        response = requests.post(url, json=payload, timeout=30)
        duration = time.time() - start_time

        print(f"✅ Response received in {duration:.1f}s")
        print(f"Status Code: {response.status_code}")

        data = response.json()
        print(f"\nResponse keys: {list(data.keys())}")

        if "response" in data:
            content = data["response"]
            print(f"\n📝 Generated content ({len(content)} chars):")
            print("-" * 60)
            print(content[:500])
            print("-" * 60)

            if not content or content.strip() == "":
                print("⚠️ WARNING: Response field is empty!")
            else:
                print("✅ Content generated successfully")
        else:
            print("❌ ERROR: No 'response' field in response")
            print(f"Full response: {json.dumps(data, indent=2)}")

    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out")
    except Exception as e:
        print(f"❌ ERROR: {e}")


if __name__ == "__main__":
    test_ollama()
