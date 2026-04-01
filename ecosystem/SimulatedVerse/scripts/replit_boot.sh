#!/bin/bash

# Replit Boot Script - Autonomous Development Ecosystem
echo "[🚀] COGNITOWEAVE Boot Sequence Starting..."

# Start the main development server
echo "[dev] Starting development server on port 5000..."
npm run dev &
DEV_PID=$!

# Wait for server to come online
echo "[boot] Waiting for server to initialize..."
sleep 5

# Check if server is responding
if curl -sf http://127.0.0.1:5000/health > /dev/null 2>&1; then
    echo "[✅] Server online and healthy"
else
    echo "[⚠️] Server health check failed, but continuing..."
fi

# Start autonomous ops loop in background
echo "[ops] Starting autonomous operations loop..."
mkdir -p ops/logs
( sleep 2; node ops/autonomous-loop.js ) > ops/logs/autonomous.log 2>&1 &
OPS_PID=$!

# Start Yap Monitor for ML/LLM tagging in background
echo "[yap] Starting Yap Monitor for ML/LLM analysis..."
( sleep 3; node ops/yap-monitor.js ) > ops/logs/yap.log 2>&1 &
YAP_PID=$!

echo "[🎮] Autonomous development ecosystem active!"
echo "[📊] Development server PID: $DEV_PID"
echo "[🤖] Autonomous ops PID: $OPS_PID" 
echo "[🧠] Yap Monitor PID: $YAP_PID"
echo "[🌐] Access at: http://localhost:5000"
echo "[📱] Council HUD: http://localhost:5000/council"
echo "[🎯] Game Interface: http://localhost:5000/game"
echo "[📂] Archives: archive/ (Archivist), yap_archive/ (Yap Monitor)"
echo "[🎵] Conductor: Auto-mapping musical harmonics on square generation"

# Wait for the main dev server
wait $DEV_PID