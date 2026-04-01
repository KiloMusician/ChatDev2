# 🌌 ΞNuSyQ Menu Navigation System - Guide

## Overview

The new **Scene Router** brings together ALL UI components into a unified, menu-dive friendly navigation system. Think of it as a digital analog synthesizer - modular, flexible, interconnected.

---

## 🎯 Quick Access

### Keyboard Shortcuts
- `Ctrl+M` - Open Main Menu
- `Ctrl+A` - Agent Control Center
- `Ctrl+G` - Game Worlds
- `ESC` - Go back / Close current scene

### Menu Button
- Click the **"☰ Menu"** button (top-right corner)
- Or access via keyboard shortcuts

---

## 📋 Main Menu Structure

### 1. 🤖 Agent Control Center
View and control ALL AI agents with real-time status:

**Available Agents**:
- **GitHub Copilot** (`online`) - Main copilot integration
- **Ollama Local** (`online`) - Local LLM with model switching
  - Models: llama3.2, codellama, mistral, neural-chat
  - Endpoint: http://localhost:11434
- **LM Studio** (`offline`) - External LLM server
  - Endpoint: http://localhost:1234
- **ChatDev Agents** (`online`) - Multi-agent team
  - Sub-agents: CEO, CTO, Programmer, Tester, Reviewer
- **Consciousness Bridge** (`online`) - Consciousness integration
- **Quantum Resolver** (`online`) - Quantum problem solving

**Agent Actions**:
- `VIEW TERMINAL` - Open agent's terminal window (planned)
- `SWITCH MODEL` - Change Ollama model on the fly
- `RESTART` - Restart agent process
- `CONFIGURE` - Jump to settings
- `VIEW AGENTS` - See ChatDev sub-agents

---

### 2. 🎮 Game Worlds

#### 🌱 Cultivation Idle (`playable`)
**Incremental cultivation sandbox with deep menu-dive mechanics**

**Features**:
- **4 Resources**: Consciousness, Quantum Energy, Neural Pathways, Wisdom
- **Auto-production**: Idle mechanics with per-second generation rates
- **Cultivation Realms**: Progress through 11 realms (Mortal → True Immortal)
- **Upgrades System**: Unlock new resources and boost production
- **Prestige/Ascension**: Reset for permanent multipliers
- **Save/Load**: localStorage persistence

**Upgrade Tree**:
```
Basic Meditation (50 consciousness)
  → Quantum Awakening (100 consciousness) - Unlock Quantum Energy
    → Deep Meditation (500 consciousness)
      → Quantum Channeling (200 consciousness, 50 quantum)
        → Neural Expansion (1000 consciousness, 200 quantum) - Unlock Neural Pathways
          → Path to Enlightenment (5000 consciousness, 1000 quantum, 100 neural) - Unlock Wisdom
            → Ascension Gate (10000 consciousness, 50 wisdom) - Unlock Prestige
```

**Actions**:
- `🧘 Meditate` - Manual click for +10 consciousness
- `✨ Ascend` - Prestige reset with permanent bonuses
- `💾 Save` - Save game state

**Gameplay Loop**:
1. Gather consciousness automatically
2. Buy upgrades to unlock new resources
3. Progress through cultivation realms
4. Ascend for permanent multipliers
5. Repeat with faster growth

**Game Status**: ✅ FULLY PLAYABLE

---

## 📊 Total UI Elements Catalogued

### Web Interfaces (2 complete)
- ΞNuSyQ Modular Window System (main UI)
- AI Task Manager Frontend

### Dashboards (5 complete)
- Culture Ship Dashboard (Flask)
- Guild Board Status
- Cultivation Metrics
- SNS-Core Metrics (VS Code)
- Testing Dashboard

### Context Browsers (4 implementations)
- Enhanced Context Browser (Streamlit)
- Wizard Navigator (Streamlit)
- Interactive Browser (Streamlit)
- Desktop App (tkinter, incomplete)

### Game Systems (5 total)
- Cultivation Idle (✅ playable)
- House of Leaves (scaffold)
- Tower Defense (planned)
- RPG Adventure (planned)
- ASCII Roguelike (planned)

### Terminal Systems (6 complete)
- Enhanced Terminal Ecosystem
- Agent Terminal Router
- Multi-Agent Terminal Orchestrator
- RPG Inventory System
- Terminal Channel/Manager
- Quantum Terminal (web UI)

### Backend APIs (2 complete)
- Flask Dashboard API (port 5001)
- FastAPI System Health (port 8000)

---

## 🚀 How to Use

### Opening the Menu
1. Navigate to http://localhost:8080
2. Click "☰ Menu" button (top-right)
3. Or press `Ctrl+M`

### Playing Cultivation Idle
1. Open Menu (`Ctrl+M`)
2. Click "🎮 Game Worlds"
3. Click "🌱 Cultivation Idle"
4. Game starts automatically
5. Watch resources auto-increment
6. Buy upgrades to unlock new resources
7. Progress through cultivation realms
8. Click "💾 Save" to persist

### Viewing Agent Status
1. Open Menu (`Ctrl+M`)
2. Click "🤖 Agent Control Center"
3. See all 6 AI agents with live status
4. Click actions (VIEW TERMINAL, SWITCH MODEL, etc.)

---

## 🔧 Technical Architecture

### Scene Router (`scene-router.js`)
- Main navigation controller with scene management
- Supports: menu, agent-grid, game, settings scenes
- History stack for back button
- Keyboard shortcuts (Ctrl+M/A/G, ESC)

### Cultivation Idle Engine (`cultivation-idle-engine.js`)
- Tick system: 100ms intervals (10 ticks/second)
- 4 resources with production rates
- Upgrade tree with dependencies
- Prestige system with multipliers
- localStorage save/load

### Integration
- Express (8080) → Flask (5001) + FastAPI (8000)
- DuckDB for quest/event persistence
- WebSocket ready for real-time updates

---

**Menu System Status**: ✅ OPERATIONAL
**Cultivation Idle Status**: ✅ PLAYABLE
**Agent Control**: ✅ FUNCTIONAL
**Total Scenes**: 45+ UI elements catalogued

Press `Ctrl+M` to begin! 🌌
