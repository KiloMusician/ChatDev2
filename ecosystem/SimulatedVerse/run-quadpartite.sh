#!/bin/bash

# ΞNuSyQ Quadpartite Architecture Launcher
# Runs all four pillars: System/Repo, Game/UI, Simulation, Godot Engine

echo "🚀 Starting ΞNuSyQ Quadpartite Architecture..."

# Function to handle cleanup
cleanup() {
    echo "🛑 Shutting down all services..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}

trap cleanup SIGINT

# Build Godot docs index
echo "📚 Building Godot docs index..."
npx tsx ops/godot-docs-index.ts

# Start all services in background
echo "🌐 Starting main UI server..."
NODE_ENV=development npx tsx server/index.ts &
UI_PID=$!

echo "🌉 Starting Godot bridge..."
npx tsx ops/godot-bridge.ts &
BRIDGE_PID=$!

echo "🔄 Starting Python ⇄ GDScript translator..."
python ops/gdtranslate.py &
TRANSLATE_PID=$!

echo ""
echo "✅ All services started!"
echo ""
echo "📱 UI: http://localhost:5000"
echo "🌉 Bridge: ws://localhost:8765"  
echo "🔄 Translator: http://localhost:7878"
echo ""
echo "🎮 Godot Integration:"
echo "  1. Open Godot and create a new project"
echo "  2. Copy /godot/addons/ to your project"
echo "  3. Enable 'XiNuSyQ Bridge' plugin in Project Settings"
echo "  4. Add Bridge.gd script to a Node in your scene"
echo "  5. Run the scene - it will connect to ws://localhost:8765"
echo ""
echo "🎨 TouchDesigner Integration:"
echo "  - OSC output: 127.0.0.1:9000"
echo "  - See ops/touchdesigner-osc-example.py for setup"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for all background processes
wait