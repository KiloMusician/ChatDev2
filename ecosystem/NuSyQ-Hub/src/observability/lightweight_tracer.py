"""Lightweight observability without Docker dependency.

This provides trace-like visibility into multi-AI orchestration
without requiring OpenTelemetry/Jaeger infrastructure. Logs are
written to JSON files and can be visualized later.

Features:
- Trace context propagation
- Span recording with timing
- Multi-AI decision paths
- JSON export for analysis
- Obsidian note generation
"""

import json
import logging
import time
import uuid
from collections import defaultdict
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Span:
    """A single operation span."""

    span_id: str
    trace_id: str
    name: str
    start_time: float
    end_time: float | None = None
    parent_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def duration_ms(self) -> float | None:
        """Duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None

    def add_event(self, name: str, attributes: dict | None = None) -> None:
        """Add event to span."""
        self.events.append({"timestamp": time.time(), "name": name, "attributes": attributes or {}})

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON serialization."""
        data = asdict(self)
        data["duration_ms"] = self.duration_ms
        return data


class LightweightTracer:
    """File-based tracer without Docker dependency."""

    def __init__(self, output_dir: Path | None = None) -> None:
        """Initialize tracer.

        Args:
            output_dir: Directory to write trace files (default: logs/traces/)
        """
        self.output_dir = output_dir if output_dir is not None else Path("logs/traces")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.spans: dict[str, Span] = {}  # span_id -> Span
        self.active_spans: dict[str, str] = {}  # trace_id -> current span_id

    def start_trace(self, operation_name: str) -> str:
        """Start new trace and return trace_id."""
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())

        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            name=operation_name,
            start_time=time.time(),
        )

        self.spans[span_id] = span
        self.active_spans[trace_id] = span_id
        return trace_id

    def start_span(self, trace_id: str, name: str, attributes: dict | None = None) -> str:
        """Start child span within trace."""
        span_id = str(uuid.uuid4())
        parent_id = self.active_spans.get(trace_id)

        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            name=name,
            start_time=time.time(),
            parent_id=parent_id,
            attributes=attributes or {},
        )

        self.spans[span_id] = span
        self.active_spans[trace_id] = span_id
        return span_id

    def end_span(self, span_id: str) -> None:
        """End span and record timing."""
        if span_id in self.spans:
            self.spans[span_id].end_time = time.time()

    def add_event(self, span_id: str, event_name: str, attributes: dict | None = None) -> None:
        """Add event to span."""
        if span_id in self.spans:
            self.spans[span_id].add_event(event_name, attributes)

    def set_attribute(self, span_id: str, key: str, value: Any) -> None:
        """Set attribute on span."""
        if span_id in self.spans:
            self.spans[span_id].attributes[key] = value

    def end_trace(self, trace_id: str) -> Path:
        """End trace and write to file."""
        # Get all spans for this trace
        trace_spans = [s for s in self.spans.values() if s.trace_id == trace_id]

        # Build trace structure
        trace_data = {
            "trace_id": trace_id,
            "timestamp": datetime.now().isoformat(),
            "spans": [s.to_dict() for s in trace_spans],
            "summary": self._build_summary(trace_spans),
        }

        # Write to file
        filename = f"trace_{trace_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(trace_data, f, indent=2)

        # Clean up
        for span in trace_spans:
            del self.spans[span.span_id]
        if trace_id in self.active_spans:
            del self.active_spans[trace_id]

        return filepath

    def _build_summary(self, spans: list[Span]) -> dict[str, Any]:
        """Build summary statistics for trace."""
        if not spans:
            return {}

        total_duration = sum(s.duration_ms or 0 for s in spans)

        # Group by operation name
        by_operation = defaultdict(list)
        for span in spans:
            by_operation[span.name].append(span.duration_ms or 0)

        return {
            "total_duration_ms": total_duration,
            "span_count": len(spans),
            "operations": {
                op: {
                    "count": len(durations),
                    "total_ms": sum(durations),
                    "avg_ms": sum(durations) / len(durations) if durations else 0,
                    "max_ms": max(durations) if durations else 0,
                }
                for op, durations in by_operation.items()
            },
        }

    @contextmanager
    def trace(self, operation_name: str) -> Generator[str, None, None]:
        """Context manager for full trace."""
        trace_id = self.start_trace(operation_name)
        try:
            yield trace_id
        finally:
            filepath = self.end_trace(trace_id)
            logger.debug(f"📊 Trace saved: {filepath}")
            print(f"📊 Trace saved: {filepath}")

    @contextmanager
    def span(self, trace_id: str, name: str, **attributes: Any) -> Generator[str, None, None]:
        """Context manager for span within trace."""
        span_id = self.start_span(trace_id, name, attributes)
        try:
            yield span_id
        finally:
            self.end_span(span_id)

    def generate_obsidian_note(self, trace_filepath: Path, vault_path: Path) -> Path:
        """Generate Obsidian note from trace file."""
        with open(trace_filepath, encoding="utf-8") as f:
            trace_data = json.load(f)

        trace_id = trace_data["trace_id"]
        summary = trace_data["summary"]

        # Create markdown
        note = f"""# Trace: {trace_id[:8]}
**Timestamp:** {trace_data["timestamp"]}
**Total Duration:** {summary.get("total_duration_ms", 0):.2f}ms
**Spans:** {summary.get("span_count", 0)}

## Operations

"""

        for op, stats in summary.get("operations", {}).items():
            note += f"### {op}\n"
            note += f"- Count: {stats['count']}\n"
            note += f"- Total: {stats['total_ms']:.2f}ms\n"
            note += f"- Average: {stats['avg_ms']:.2f}ms\n"
            note += f"- Max: {stats['max_ms']:.2f}ms\n\n"

        note += "## Span Timeline\n\n"
        note += "```json\n"
        note += json.dumps(trace_data["spans"], indent=2)
        note += "\n```\n"

        # Write to Obsidian
        vault_path = Path(vault_path)
        traces_dir = vault_path / "Traces"
        traces_dir.mkdir(exist_ok=True)

        note_path = traces_dir / f"Trace_{trace_id[:8]}.md"
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(note)

        return note_path


@lru_cache(maxsize=1)
def get_tracer() -> LightweightTracer:
    """Get a cached tracer instance without using global state."""
    return LightweightTracer()
