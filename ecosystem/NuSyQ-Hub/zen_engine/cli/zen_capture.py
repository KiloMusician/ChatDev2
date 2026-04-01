#!/usr/bin/env python3
"""zen-capture - Error Event Capture and Analysis

Capture error events from logs or live execution and analyze them
against the ZenCodex.

Usage:
    zen-capture --log error.log
    zen-capture --text "ModuleNotFoundError: No module named 'requests'"
    zen-capture --watch logs/
    zen-capture --analyze events/

OmniTag: [zen-engine, cli, error-capture, analysis]
MegaTag: ZEN_ENGINE⨳CLI⦾ERROR_CAPTURE→∞
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Add zen-engine to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from zen_engine.agents import ErrorObserver, Matcher


def capture_from_log(log_path: Path, output_dir: Path | None = None):
    """Capture errors from a log file."""
    observer = ErrorObserver()

    print(f"🔍 Analyzing log file: {log_path}")

    events = observer.observe_log_file(log_path)

    print(f"\n✅ Captured {len(events)} error events\n")

    for event in events:
        print(f"Event: {event.id}")
        print(f"  Symptom: {event.symptom}")
        print(f"  Patterns: {', '.join(event.patterns_detected)}")

        if output_dir:
            observer.save_event(event, output_dir)

    if output_dir:
        print(f"\n📁 Events saved to: {output_dir}")


def capture_from_text(error_text: str, command: str = "", shell: str = "unknown"):
    """Capture and analyze error text."""
    observer = ErrorObserver()
    matcher = Matcher()

    print("🔍 Analyzing error text...")

    event = observer.observe_error(
        error_text=error_text,
        command=command,
        shell=shell,
    )

    if event:
        print(f"\n✅ Error event created: {event.id}")
        print(f"   Symptom: {event.symptom}")
        print(f"   Auto-fixable: {event.auto_fixable}")

        # Match against rules
        matches = matcher.match_event_to_rules(event)

        if matches:
            print(f"\n📚 Found {len(matches)} matching rules")
            advice = matcher.compose_multi_rule_advice(event, matches)
            print(f"\n{advice}")
        else:
            print("\n❓ No matching rules found")
    else:
        print("\n❓ No error pattern detected")


def watch_directory(watch_dir: Path, output_dir: Path | None = None):
    """Watch directory for new log files."""
    observer = ErrorObserver()

    print(f"👀 Watching directory: {watch_dir}")
    print("Press Ctrl+C to stop\n")

    processed_files = set()

    try:
        while True:
            # Check for new log files
            log_files = list(watch_dir.glob("*.log"))

            for log_file in log_files:
                if log_file not in processed_files:
                    print(f"\n📄 New log file detected: {log_file.name}")
                    events = observer.observe_log_file(log_file)

                    if events:
                        print(f"   Captured {len(events)} events")
                        for event in events:
                            if output_dir:
                                observer.save_event(event, output_dir)

                    processed_files.add(log_file)

            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\n👋 Stopped watching")


def analyze_events(events_dir: Path):
    """Analyze captured event files."""
    matcher = Matcher()

    event_files = list(events_dir.glob("*.json"))

    if not event_files:
        print(f"❌ No event files found in {events_dir}")
        return

    print(f"📊 Analyzing {len(event_files)} event files\n")

    total_matches = 0
    auto_fixable = 0

    for event_file in event_files:
        with open(event_file, encoding="utf-8") as f:
            event_data = json.load(f)

        # Reconstruct ErrorEvent (simplified)
        from zen_engine.agents.error_observer import ErrorEvent

        event = ErrorEvent(**event_data)

        matches = matcher.match_event_to_rules(event)

        if matches:
            total_matches += len(matches)
            if event.auto_fixable:
                auto_fixable += 1

            print(f"{event.id}: {len(matches)} rules matched")

    print("\n📈 Analysis Summary:")
    print(f"   Total events: {len(event_files)}")
    print(f"   Total rule matches: {total_matches}")
    print(f"   Auto-fixable: {auto_fixable}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Zen-Capture: Capture and analyze error events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  zen-capture --log error.log
  zen-capture --text "ImportError: No module named 'numpy'"
  zen-capture --watch logs/ --output events/
  zen-capture --analyze events/
        """,
    )

    parser.add_argument("--log", "-l", type=Path, help="Log file to analyze")
    parser.add_argument("--text", "-t", help="Error text to analyze")
    parser.add_argument("--command", "-c", help="Command that caused error")
    parser.add_argument("--shell", default="unknown", help="Shell environment")
    parser.add_argument("--watch", "-w", type=Path, help="Watch directory for new logs")
    parser.add_argument("--analyze", "-a", type=Path, help="Analyze captured events")
    parser.add_argument("--output", "-o", type=Path, help="Output directory for events")

    args = parser.parse_args()

    if args.log:
        capture_from_log(args.log, args.output)
    elif args.text:
        capture_from_text(args.text, args.command or "", args.shell)
    elif args.watch:
        watch_directory(args.watch, args.output)
    elif args.analyze:
        analyze_events(args.analyze)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
