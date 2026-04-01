#!/bin/bash
set -e

echo "[post-merge] Installing Python dependencies..."
pip install -q -r requirements.txt --disable-pip-version-check 2>/dev/null || true

echo "[post-merge] Checking game engine imports..."
python3 -c "
from app.game_engine.agents import AGENTS, AGENT_MAP
from app.game_engine.factions import FactionSystem
from app.game_engine.trust_matrix import TrustMatrix
from app.game_engine.agent_dialogue import AgentDialogueEngine
from app.game_engine.gamestate import GameState
from app.game_engine.session import GameSession
print(f'  agents={len(AGENTS)}  factions=6  OK')
"

echo "[post-merge] Done."
