# ChatDev 2.0 — DevAll

## Overview

ChatDev 2.0 (DevAll) is a zero-code multi-agent orchestration platform for building complex AI workflows. It supports visual graph-based workflow design, multiple LLM backends (OpenAI, Gemini, Ollama), and produces artifacts via multi-agent collaboration.

## Architecture

- **Frontend**: Vue 3 + Vite, runs on port 5000 (`frontend/`)
- **Backend**: FastAPI + uvicorn, runs on port 6400 (`server/`, `server_main.py`)
- **Proxy**: Vite dev server proxies `/api` and `/ws` requests to the backend on port 6400
- **Agent Runtime**: `runtime/` — node executors, edge logic, memory, tools
- **Workflows**: Defined as YAML in `yaml_instance/`, outputs stored in `WareHouse/`

## Running the App

The single workflow `Start application` runs `bash start.sh` which:
1. Starts the FastAPI backend on `localhost:6400`
2. Starts the Vite frontend on `0.0.0.0:5000`

## Port Design

- Port 5000: Frontend (Vite) — webview-accessible
- Port 6400: Backend (FastAPI) — internal only, proxied through Vite
- Port 8008: Dev-Mentor (Terminal Depths) — ecosystem service
- Port 3001: CONCEPT_SAMURAI static docs — ecosystem service

## Key Files

- `start.sh` — Startup script for both services
- `server_main.py` — Backend entry point
- `frontend/vite.config.js` — Vite config with proxy and port settings
- `pyproject.toml` — Python project config (`tool.uv.package = false`)
- `yaml_instance/` — Pre-built workflow YAML definitions

## Dependencies

- **Python**: 3.12 (installed via Replit module system)
- **Python packages**: fastapi, uvicorn, fastmcp, pandas, pyyaml, openai, anthropic, etc. (installed via pip)
- **Node packages**: Vue 3, vue-router, @vue-flow/core, vite (installed via npm in `frontend/`)

## NuSyQ Ecosystem Integration

Six repos cloned to `ecosystem/` and launched via `ecosystem/start_services.sh`:

| Repo | Type | Port | Status |
|------|------|------|--------|
| Dev-Mentor | FastAPI (game engine, CHUG, ML) | 8008 | Auto-started |
| CONCEPT_SAMURAI | Static docs server | 3001 | Auto-started |
| SimulatedVerse | Node/RimWorld sim | 3000 | Heavy — not auto-started |
| NuSyQ-Hub | CLI / health analysis | — | Snapshot on startup |
| NuSyQ_Ultimate | Python library | — | CLI/library mode |
| awesome-vibe-coding | Docs/resources | — | Static reference |

The **Ecosystem** page (`/ecosystem`) in the frontend shows live health of all 6 repos with git metadata, status indicators, architecture diagram, and a CHUG cycle trigger button.

Backend API: `GET /api/ecosystem/status`, `GET /api/ecosystem/repos`, `POST /api/ecosystem/chug`

## LLM Setup

The app requires API keys to run workflows (OpenAI, Anthropic, Gemini). Set these as environment variables/secrets before use.
