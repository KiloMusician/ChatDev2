# cspell: ignore omnitag
"""Unified cross-repo metrics logger."""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.telemetry.omnitag import log_event


class LogUnifiedMetric:
    """Cross-repo metric logger with local JSONL persistence."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        root = Path(__file__).resolve().parents[2]
        self.output_dir = output_dir or (root / "Reports" / "metrics")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._output_file = self.output_dir / "unified_metrics.jsonl"

    def log(
        self,
        *,
        agent_id: str,
        source_repo: str,
        task: Dict[str, Any],
        result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a unified metric to OmniTag and local report storage."""
        outcome = "success" if result.get("success", True) else "failure"
        timestamp = datetime.now().isoformat()
        payload = {
            "timestamp": timestamp,
            "agent_id": agent_id,
            "source_repo": source_repo,
            "task": task,
            "result": result,
        }
        log_event(
            component="unified_metrics",
            action="log_metric",
            payload=payload,
            outcome=outcome,
            context=context,
        )
        line = json.dumps(payload, ensure_ascii=False, default=str)
        with self._lock:
            with open(self._output_file, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
