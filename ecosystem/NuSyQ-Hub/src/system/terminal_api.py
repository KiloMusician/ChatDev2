"""Terminal API for NuSyQ-Hub CLI integrations.

Provides REST endpoints for routing messages into the enhanced terminal
ecosystem so remote clients (ChatGPT CLI, automation scripts, etc.) can emit
events without needing direct repository access.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

try:
    from src.system.enhanced_terminal_ecosystem import TerminalManager
except ImportError:
    from system.enhanced_terminal_ecosystem import TerminalManager


class TerminalSendRequest(BaseModel):
    channel: str = Field(..., description="Terminal channel name (case insensitive)")
    level: str = Field(..., description="Log level, e.g., info, warning, error")
    message: str = Field(..., description="Human-readable message body")
    meta: dict[str, Any] | None = Field(
        default=None, description="Optional structured metadata to accompany the message"
    )


class ApiResponse(BaseModel):
    status: str
    detail: str | None = None
    payload: Any | None = None


def _get_terminal_manager() -> TerminalManager:
    return TerminalManager.get_instance()


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def create_app() -> FastAPI:
    app = FastAPI(
        title="NuSyQ Terminal API",
        version="1.0.0",
        description="API for routing structured messages into the NuSyQ terminal ecosystem.",
    )

    @app.get("/health", response_model=ApiResponse)
    def health() -> ApiResponse:
        return ApiResponse(
            status="ok", detail="terminal API healthy", payload={"timestamp": _now_iso()}
        )

    @app.post(
        "/api/terminals/send", response_model=ApiResponse, status_code=status.HTTP_201_CREATED
    )
    def send_message(
        payload: TerminalSendRequest,
        tm: TerminalManager = Depends(_get_terminal_manager),
    ) -> ApiResponse:
        entry = tm.send(payload.channel, payload.level, payload.message, meta=payload.meta or {})
        return ApiResponse(status="ok", payload=entry)

    @app.get("/api/terminals", response_model=ApiResponse)
    def list_terminals(
        tm: TerminalManager = Depends(_get_terminal_manager),
    ) -> ApiResponse:
        from src.system.enhanced_terminal_ecosystem import TerminalType
        from src.system.terminal_manager import EnhancedTerminalManager

        etm = EnhancedTerminalManager()
        # List all available shell and agent terminals
        terminals = [t.name for t in TerminalType]
        sessions = etm.get_session_summary()
        return ApiResponse(
            status="ok",
            detail="list of terminals",
            payload={
                "channels": tm.list_channels(),
                "terminals": terminals,
                "sessions": sessions,
                "timestamp": _now_iso(),
            },
        )

    @app.post("/api/terminals/start", response_model=ApiResponse)
    def start_terminal(
        terminal_type: str,
    ) -> ApiResponse:
        from pathlib import Path

        from src.system.enhanced_terminal_ecosystem import (
            EnhancedTerminalEcosystem, TerminalType)

        ecosystem = EnhancedTerminalEcosystem(Path(__file__).resolve().parents[2])
        try:
            ttype = TerminalType[terminal_type.upper()]
            started = ecosystem.start_terminal(ttype)
            return ApiResponse(
                status="ok", detail=f"Started {terminal_type}", payload={"started": started}
            )
        except Exception as e:
            return ApiResponse(status="error", detail=str(e), payload={})

    @app.post("/api/terminals/stop", response_model=ApiResponse)
    def stop_terminal(
        terminal_type: str,
    ) -> ApiResponse:
        from pathlib import Path

        from src.system.enhanced_terminal_ecosystem import (
            EnhancedTerminalEcosystem, TerminalType)

        ecosystem = EnhancedTerminalEcosystem(Path(__file__).resolve().parents[2])
        try:
            ttype = TerminalType[terminal_type.upper()]
            stopped = ecosystem.stop_terminal(ttype)
            return ApiResponse(
                status="ok", detail=f"Stopped {terminal_type}", payload={"stopped": stopped}
            )
        except Exception as e:
            return ApiResponse(status="error", detail=str(e), payload={})

    @app.post("/api/terminals/send_command", response_model=ApiResponse)
    def send_command(
        terminal_type: str,
        command: str,
    ) -> ApiResponse:
        from src.system.terminal_manager import EnhancedTerminalManager

        etm = EnhancedTerminalManager()
        session_id = etm.create_session()
        result = etm.execute_command(command, session_id=session_id)
        return ApiResponse(
            status="ok",
            detail="command executed",
            payload={"result": result, "session_id": session_id},
        )

    @app.get("/api/terminals/output/{session_id}", response_model=ApiResponse)
    def get_terminal_output(
        session_id: str,
        command_index: int = -1,
    ) -> ApiResponse:
        from src.system.terminal_manager import EnhancedTerminalManager

        etm = EnhancedTerminalManager()
        output = etm.get_session_output(session_id, command_index=command_index)
        return ApiResponse(status="ok", detail="output fetched", payload={"output": output})

    @app.get("/api/terminals/{channel}/recent", response_model=ApiResponse)
    def recent_entries(
        channel: str,
        n: int = Query(20, ge=1, le=500),
        tm: TerminalManager = Depends(_get_terminal_manager),
    ) -> ApiResponse:
        entries = tm.recent(channel, n=n)
        if not entries:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No entries found for channel {channel}",
            )
        return ApiResponse(status="ok", payload={"count": len(entries), "entries": entries})

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.system.terminal_api:app", host="0.0.0.0", port=8000, log_level="info")
