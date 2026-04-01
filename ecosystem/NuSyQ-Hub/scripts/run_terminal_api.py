"""Helper to launch the NuSyQ terminal REST API."""

from __future__ import annotations

import uvicorn


def main() -> None:
    """Run the FastAPI-powered Terminal API."""
    uvicorn.run(
        "src.system.terminal_api:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
