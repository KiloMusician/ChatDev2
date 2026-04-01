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

## LLM Setup

The app requires API keys to run workflows (OpenAI, Anthropic, Gemini). Set these as environment variables/secrets before use.
