#!/bin/bash
set -e

echo "=== ChatDev Smoke Test ==="

# Test 1: Health check
echo "1. Health check..."
curl -sf http://127.0.0.1:4466/chatdev/agents || {
  echo "❌ ChatDev not responding on :4466"
  exit 1
}
echo "✅ ChatDev responding"

# Test 2: List agents
echo "2. Agent roster..."
AGENTS=$(curl -s http://127.0.0.1:4466/chatdev/agents | jq -r '.agents[]' 2>/dev/null || echo "none")
echo "Available agents: $AGENTS"

# Test 3: Simple turn with Raven
echo "3. Raven test turn..."
RESPONSE=$(curl -s -X POST http://127.0.0.1:4466/chatdev/turn \
  -H 'content-type: application/json' \
  -d '{"agent":"raven","input":"Reply with just the word SUCCESS if you can hear me."}' \
  | jq -r '.output' 2>/dev/null || echo "FAILED")

echo "Raven response: $RESPONSE"

# Test 4: Check if backend cascade works
echo "4. Backend cascade test..."
BACKEND=$(curl -s -X POST http://127.0.0.1:4466/chatdev/turn \
  -H 'content-type: application/json' \
  -d '{"agent":"librarian","input":"What backend are you using?"}' \
  | jq -r '.backend' 2>/dev/null || echo "unknown")

echo "Backend used: $BACKEND"

echo "=== All tests completed ==="