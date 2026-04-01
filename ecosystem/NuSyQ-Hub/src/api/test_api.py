"""Test Orchestration API endpoints."""

import subprocess
from typing import Any

from fastapi import APIRouter, Query

router = APIRouter()


@router.post("/test/run")
def run_tests(pattern: str = Query("tests/")) -> dict[str, Any]:
    """Run tests matching the pattern and return results."""
    try:
        result = subprocess.run(
            ["pytest", pattern, "-q"], capture_output=True, text=True, timeout=300
        )
        return {
            "exit_code": result.returncode,
            "output": result.stdout + result.stderr,
        }
    except Exception as e:
        return {"error": str(e)}
