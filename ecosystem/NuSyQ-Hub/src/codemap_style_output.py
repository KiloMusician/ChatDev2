#!/usr/bin/env python3
"""Tripartite rendering utility for human, agent, and programmatic consumers.

Features:
  * Structured `Record` model shared by library, CLI, and pipelines.
  * Renderer that can output pretty tables, terse agent-friendly KV lines,
    or pure JSONL for downstream ingestion.
  * Example `analyze_trace()` generator to demonstrate how records flow through
    the system without touching the rendering logic.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import asdict, dataclass
from enum import Enum
from typing import TextIO

# --
# Record model (shared core logic)
# --


class RecordType(str, Enum):
    """Common record categories shared across renderers."""

    META = "meta"
    SCOPE = "scope"
    SYMBOL = "symbol"
    CALLER = "caller"
    FINDING = "finding"
    END = "end"


@dataclass(frozen=True)
class Record:
    """Immutable schema for any codemap observation."""

    record: RecordType
    name: str | None = None
    file: str | None = None
    line: int | None = None
    kind: str | None = None
    count: int | None = None
    path: str | None = None
    severity: str | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, str | int]:
        payload = asdict(self)
        payload["record"] = self.record.value
        return {key: value for key, value in payload.items() if value is not None}


# --
# Renderer implementations
# --


class OutputFormat(str, Enum):
    """Available output styles for the tripartite ecosystem."""

    PRETTY = "pretty"  # friendly output for humans
    AGENT = "agent"  # key-value lines for LLMs
    JSONL = "jsonl"  # pipeline-friendly streaming records


def render(records: Iterable[Record], fmt: OutputFormat, out: TextIO) -> None:
    """Dispatch renderer based on the requested format."""
    if fmt == OutputFormat.JSONL:
        _render_jsonl(records, out)
    elif fmt == OutputFormat.AGENT:
        _render_agent(records, out)
    else:
        _render_pretty(records, out)


def _render_jsonl(records: Iterable[Record], out: TextIO) -> None:
    for record in records:
        out.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


def _render_agent(records: Iterable[Record], out: TextIO) -> None:
    for record in records:
        data = record.to_dict()
        keys = ["record"] + [k for k in data if k != "record"]
        tokens = [f"{key}={data[key]}" for key in keys]
        out.write("\t".join(tokens) + "\n")


def _render_pretty(records: Iterable[Record], out: TextIO) -> None:
    current_file: str | None = None
    for record in records:
        if record.record == RecordType.META:
            if record.count is not None and record.kind:
                out.write(f"[{record.kind}] count: {record.count}\n")
            elif record.message:
                out.write(f"{record.message}\n")
        elif record.record == RecordType.SCOPE and record.path:
            current_file = record.path
            out.write("\n" + ("=" * 44) + "\n")
            out.write(f"FILE: {current_file}\n")
            out.write(("=" * 44) + "\n")
        elif record.record == RecordType.SYMBOL:
            out.write("\n" + ("-" * 44) + "\n")
            out.write(f"SYMBOL: {record.name}\n")
            if record.file and record.line is not None:
                out.write(f"  defined at: {record.file}:{record.line}\n")
            out.write(("-" * 44) + "\n")
        elif record.record == RecordType.CALLER:
            location = ""
            if record.file and record.line is not None:
                location = f"  ({record.file}:{record.line})"
            elif current_file and record.line is not None:
                location = f"  ({current_file}:{record.line})"
            out.write(f"  -> {record.name}{location}\n")
        elif record.record == RecordType.FINDING:
            location = ""
            if record.file and record.line is not None:
                location = f" [{record.file}:{record.line}]"
            prefix = f"{record.severity.upper()}: " if record.severity else ""
            out.write(f"{prefix}{record.kind}{location} {record.message or ''}\n")
        elif record.record == RecordType.END:
            out.write("\n[done]\n")


# --
# Example generator (replace with real codemap logic)
# --


def analyze_trace(symbol: str) -> Iterator[Record]:
    """Sample generator that yields records for a traced symbol."""
    yield Record(RecordType.META, kind="command", message="trace")
    yield Record(RecordType.SYMBOL, name=symbol, file="api.rs", line=45)
    yield Record(RecordType.SCOPE, path="HomePresenter.swift")
    yield Record(RecordType.META, kind="callers", count=3)
    yield Record(RecordType.CALLER, name="loadData", line=142)
    yield Record(RecordType.CALLER, name="refreshData", line=188)
    yield Record(RecordType.CALLER, name="bootstrap", line=219)
    yield Record(RecordType.END)


# --
# CLI wiring
# --


def _format_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--format",
        choices=[fmt.value for fmt in OutputFormat],
        default=OutputFormat.PRETTY.value,
        help="Output format for the records",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codemap_style_output.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    trace_parser = subparsers.add_parser("trace", help="Trace callers for a symbol")
    _format_argument(trace_parser)
    trace_parser.add_argument("symbol", type=str, help="Symbol to trace")

    return parser


def main(argv: Sequence[str]) -> int:
    args = build_parser().parse_args(argv)
    fmt = OutputFormat(args.format)
    if args.command == "trace":
        records = analyze_trace(args.symbol)
    else:
        raise SystemError("unknown command")
    render(records, fmt, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
