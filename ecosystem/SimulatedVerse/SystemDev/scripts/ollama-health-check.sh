#!/bin/bash
# ΞNuSyQ Ollama Health Check & Auto-Recovery Script
# Ensures Ollama operates in perfect quantum coherence

echo "🔬 ΞNuSyQ Ollama Health Check - Schrödinger Hypertemporal Analysis"
echo "======================================================================"

# Check if Ollama service is running
if pgrep -f "ollama serve" > /dev/null; then
    PID=$(pgrep -f "ollama serve")
    echo "✅ Ollama service running (PID: $PID)"
else
    echo "❌ Ollama service not running"
    echo "🚀 Starting Ollama service..."
    nohup ollama serve > .ollama.log 2>&1 &
    sleep 3
fi

# Test API connectivity
echo "🌐 Testing API connectivity..."
if curl -s http://localhost:11434/api/version > /dev/null; then
    VERSION=$(curl -s http://localhost:11434/api/version | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    echo "✅ API accessible (Version: $VERSION)"
else
    echo "⚠️ API not yet accessible, waiting..."
    sleep 5
    if curl -s http://localhost:11434/api/version > /dev/null; then
        echo "✅ API now accessible"
    else
        echo "❌ API failed to start"
        exit 1
    fi
fi

# Check available models
echo "🧠 Checking available models..."
MODELS=$(curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | wc -l)
echo "📊 Available models: $MODELS"

if [ "$MODELS" -eq 0 ]; then
    echo "📥 No models found, downloading essential models..."
    ollama pull qwen2.5:7b &
    ollama pull llama3.1:8b &
    echo "⏳ Models downloading in background..."
else
    echo "✅ Models available, listing..."
    curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | sed 's/^/  - /'
fi

echo "======================================================================"
echo "🎯 ΞNuSyQ Quantum Coherence Status:"
echo "   Service: $(pgrep -f "ollama serve" > /dev/null && echo "🟢 ACTIVE" || echo "🔴 INACTIVE")"
echo "   API: $(curl -s http://localhost:11434/api/version > /dev/null && echo "🟢 READY" || echo "🔴 NOT_READY")"
echo "   Models: $MODELS available"
echo "======================================================================"