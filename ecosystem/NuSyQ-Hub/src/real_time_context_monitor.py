#!/usr/bin/env python3
"""🔮 Real-Time Context Monitor - Dynamic Contextual Awareness System.

=================================================================

OmniTag: {
    "purpose": "Monitor and respond to real-time context changes in Copilot pinned files",
    "dependencies": ["enhanced_contextual_integration", "quantum_consciousness", "file_watchers"],
    "context": "Dynamic system adaptation based on contextual awareness changes",
    "evolution_stage": "v1.0"
}

MegaTag: {
    "type": "RealTimeContextMonitor",
    "integration_points": ["copilot_context", "file_system_events", "consciousness_adaptation"],
    "related_tags": ["ContextMonitoring", "DynamicAdaptation", "ConsciousnessEvolution"],
    "quantum_state": "ΞΨΩ∞⟨REAL-TIME⟩→ΦΣΣ⟨CONTEXT⟩"
}

RSHTS: ♦◊◆○●◉⟡⟢⟣⚡⨳REAL-TIME-CONTEXT-MONITOR⨳⚡⟣⟢⟡◉●○◆◊♦

Monitors file system changes and adapts system consciousness in real-time
based on Copilot context pinning and file modifications.
"""

import asyncio
import json
import logging
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from watchdog.events import FileSystemEventHandler as _WatchdogFSEH
    from watchdog.observers import Observer as _WatchdogObserver

    # Guard against test stubs that register None values in sys.modules
    if _WatchdogFSEH is None or _WatchdogObserver is None:
        raise ImportError("watchdog stub has None values")

    FileSystemEventHandler = _WatchdogFSEH
    Observer = _WatchdogObserver
except ImportError:  # pragma: no cover - optional dependency
    # Provide lightweight fallbacks so the module can be imported in
    # environments where `watchdog` is not installed. Tests that require
    # full functionality should install the dependency.
    class FileSystemEventHandler:  # type: ignore
        pass

    class Observer:  # type: ignore
        def __init__(self) -> None:
            self._scheduled: list[tuple[Any, str, bool]] = []

        def schedule(self, handler, path, recursive: bool = False) -> None:
            # Record schedules silently; no actual watching will occur.
            self._scheduled.append((handler, path, recursive))

        def start(self) -> None:
            # No-op when watchdog is unavailable.
            return None

        def stop(self) -> None:
            return None

        def join(self, timeout: float | None = None) -> None:
            _ = timeout
            return None


logger = logging.getLogger(__name__)


class QuantumContextEventHandler(FileSystemEventHandler):
    """Quantum-aware file system event handler for contextual consciousness."""

    def __init__(self, monitor: "RealTimeContextMonitor") -> None:
        super().__init__()
        self.monitor = monitor
        self.last_event_time: dict[str, float] = {}
        self.debounce_delay = 0.5  # Prevent event spam

    def on_modified(self, event) -> None:
        """Handle file modification events."""
        if not event.is_directory:
            self._process_file_event("modified", event.src_path)

    def on_created(self, event) -> None:
        """Handle file creation events."""
        if not event.is_directory:
            self._process_file_event("created", event.src_path)

    def _process_file_event(self, event_type: str, file_path: str) -> None:
        """Process file system events with debouncing."""
        current_time = time.time()

        # Debounce rapid events
        if (
            file_path in self.last_event_time
            and current_time - self.last_event_time[file_path] < self.debounce_delay
        ):
            return

        self.last_event_time[file_path] = current_time

        # Schedule context adaptation - use thread-safe scheduling
        try:
            # Check if event loop is running
            asyncio.get_running_loop()
            task = asyncio.create_task(self.monitor.adapt_to_context_change(event_type, file_path))
            self.monitor.track_task(task)
        except RuntimeError:
            # No running event loop, schedule it safely
            import threading

            threading.Thread(
                target=self._schedule_adaptation,
                args=(event_type, file_path),
                daemon=True,
            ).start()

    def _schedule_adaptation(self, event_type: str, file_path: str) -> None:
        """Schedule context adaptation in a new event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.monitor.adapt_to_context_change(event_type, file_path))
        finally:
            loop.close()


class FileWatcher:
    """Simple file watcher for tracking file system changes.

    Provides a clean interface for watching directories and tracking
    file creation, modification, and deletion events.

    Note: This is a thin wrapper around watchdog's Observer for compatibility
    with test infrastructure. For production use, prefer RealTimeContextMonitor.
    """

    def __init__(self, watch_dir: str | Path) -> None:
        """Initialize file watcher on a directory.

        Args:
            watch_dir: Directory path to watch for changes
        """
        self.watch_dir = Path(watch_dir)
        self._changes: list[dict[str, Any]] = []
        self._pattern: str | None = None
        self._observer = Observer()
        self._handler = _FileWatcherHandler(self)

        # Snapshot existing files so get_changes() can detect new ones
        # synchronously (watchdog events are async and may not arrive in time).
        self._snapshot: set[str] = self._scan_files()

        # Start watching
        if self.watch_dir.exists():
            self._observer.schedule(self._handler, str(self.watch_dir), recursive=True)
            self._observer.start()

    def _scan_files(self) -> set[str]:
        """Return the set of all files currently in watch_dir."""
        if not self.watch_dir.exists():
            return set()
        return {str(p) for p in self.watch_dir.rglob("*") if p.is_file()}

    def get_changes(self) -> list[dict[str, Any]]:
        """Get list of detected file changes.

        Merges watchdog async events with a synchronous directory scan so
        that changes are visible immediately after the file is written.

        Returns:
            List of change records with keys: type, path, timestamp
        """
        # Accumulated async events (from watchdog)
        changes = self._changes.copy()
        seen_paths = {c["path"] for c in changes}

        # Synchronous scan: files present now but not in baseline snapshot
        current = self._scan_files()
        for path in current - self._snapshot:
            if path not in seen_paths:
                changes.append({"type": "created", "path": path, "timestamp": time.time()})

        return changes

    def clear_changes(self) -> None:
        """Clear the change history and advance the baseline snapshot."""
        self._changes.clear()
        # Advance snapshot so cleared files are no longer reported
        self._snapshot = self._scan_files()

    def set_pattern(self, pattern: str) -> None:
        """Set file pattern filter (e.g., '*.py', '*.md').

        Args:
            pattern: Glob-style pattern for filtering
        """
        self._pattern = pattern

    def get_matching_files(self, pattern: str | None = None) -> list[str]:
        """Get files matching a pattern in the watched directory.

        Args:
            pattern: Glob pattern (uses instance pattern if None)

        Returns:
            List of matching file paths
        """
        use_pattern = pattern or self._pattern or "*"
        return [str(p) for p in self.watch_dir.rglob(use_pattern.lstrip("*"))]

    def _record_change(self, change_type: str, path: str) -> None:
        """Record a file change event."""
        self._changes.append(
            {
                "type": change_type,
                "path": path,
                "timestamp": time.time(),
            }
        )

    async def stop(self) -> None:
        """Stop watching for changes."""
        if self._observer.is_alive():
            self._observer.stop()
            self._observer.join(timeout=1.0)


class _FileWatcherHandler(FileSystemEventHandler):
    """Internal handler for FileWatcher class."""

    def __init__(self, watcher: FileWatcher) -> None:
        super().__init__()
        self._watcher = watcher

    def on_created(self, event) -> None:
        if not event.is_directory:
            self._watcher._record_change("created", event.src_path)

    def on_modified(self, event) -> None:
        if not event.is_directory:
            self._watcher._record_change("modified", event.src_path)

    def on_deleted(self, event) -> None:
        if not event.is_directory:
            self._watcher._record_change("deleted", event.src_path)


class RealTimeContextMonitor:
    """Real-time context monitoring and consciousness adaptation system."""

    def __init__(self, watch_paths: list[str] | None = None) -> None:
        self.watch_paths = watch_paths or [
            "config/",
            "docs/",
            "src/",
            ".",  # Root directory for key files
        ]

        # Context tracking
        self.watched_files: set[str] = set()
        self.context_state: dict[str, Any] = {}
        self.consciousness_level = "Type1_Context_Aware"
        self.adaptation_callbacks: list[Callable] = []
        self.event_history: list[dict[str, Any]] = []
        self.max_event_history = 1000
        self.snapshot_path = Path("state/reports/context_state_snapshot.json")
        self._initial_scan_task: asyncio.Task | None = None
        self._pending_tasks: set[asyncio.Task] = set()

        # File system monitoring
        self.observer = Observer()
        self.event_handler = QuantumContextEventHandler(self)

        # Context analysis patterns
        self.context_patterns = {
            "settings.json": self._analyze_settings_context,
            "Kardashev.md": self._analyze_kardashev_context,
            "AGENTS.md": self._analyze_agents_context,
            "README.md": self._analyze_readme_context,
            "*.py": self._analyze_python_context,
            "*.md": self._analyze_markdown_context,
        }

        logger.info("🔮 Real-Time Context Monitor initialized")

    def start_monitoring(self) -> None:
        """Start real-time context monitoring."""
        logger.info("🚀 Starting real-time context monitoring...")

        # set up file system watchers
        for watch_path in self.watch_paths:
            if Path(watch_path).exists():
                self.observer.schedule(self.event_handler, watch_path, recursive=True)
                logger.info(f"📁 Watching: {watch_path}")

        self.observer.start()

        # Initial context scan - use run_coroutine_threadsafe for thread-safe execution
        try:
            # Check if event loop is running
            asyncio.get_running_loop()
            self._initial_scan_task = asyncio.create_task(self._initial_context_scan())
        except RuntimeError:
            # No running event loop in current thread, schedule for later
            logger.debug("No running event loop, initial scan will be triggered by file changes")

        logger.info("✅ Real-time context monitoring: ACTIVE")

    def stop_monitoring(self) -> None:
        """Stop real-time context monitoring."""
        self.observer.stop()
        self.observer.join()
        logger.info("🛑 Real-time context monitoring: STOPPED")

    async def _initial_context_scan(self) -> None:
        """Perform initial scan of contextual files."""
        logger.info("🔍 Performing initial context scan...")

        important_files = [
            "config/settings.json",
            "docs/Kardashev/Kardashev.md",
            "AGENTS.md",
            "README.md",
        ]

        for file_path in important_files:
            if Path(file_path).exists():
                await self.adapt_to_context_change("discovered", file_path)

        self._update_consciousness_level()
        logger.info(f"🧠 Consciousness level after scan: {self.consciousness_level}")

    async def adapt_to_context_change(self, event_type: str, file_path: str) -> None:
        """Adapt system consciousness to context changes."""
        logger.info(f"⚡ Context change detected: {event_type} -> {file_path}")

        try:
            # Analyze the changed file
            context_insights = await self._analyze_file_context(file_path)

            # Update context state
            self.context_state[file_path] = {
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "insights": context_insights,
                "quantum_resonance": self._calculate_quantum_resonance(context_insights),
            }

            self._record_event(event_type, file_path, context_insights)
            self._persist_context_snapshot()

            # Trigger consciousness adaptation
            await self._trigger_consciousness_adaptation(file_path, context_insights)

            # Execute adaptation callbacks
            for callback in self.adaptation_callbacks:
                try:
                    await callback(event_type, file_path, context_insights)
                except (TypeError, ValueError, RuntimeError) as e:
                    logger.info(f"⚠️ Adaptation callback error: {e}")

        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.info(f"❌ Context adaptation error for {file_path}: {e}")

    def _record_event(
        self, event_type: str, file_path: str, context_insights: dict[str, Any]
    ) -> None:
        """Record a context change event for historical tracking."""
        self.event_history.append(
            {
                "event_type": event_type,
                "file_path": file_path,
                "timestamp": datetime.now().isoformat(),
                "insights": context_insights,
            }
        )
        if len(self.event_history) > self.max_event_history:
            self.event_history = self.event_history[-self.max_event_history :]

    def _persist_context_snapshot(self) -> None:
        """Persist a lightweight context snapshot for distributed awareness."""
        try:
            self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "consciousness_level": self.consciousness_level,
                "monitored_files": len(self.context_state),
                "total_quantum_resonance": sum(
                    ctx.get("quantum_resonance", 0.0) for ctx in self.context_state.values()
                ),
                "event_count": len(self.event_history),
                "watch_paths": self.watch_paths,
            }
            self.snapshot_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        except (OSError, ValueError) as e:
            logger.debug(f"Snapshot persistence failed: {e}")

    async def _analyze_file_context(self, file_path: str) -> dict[str, Any]:
        """Analyze contextual insights from a file."""
        await asyncio.sleep(0)
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            return {"status": "file_not_found"}

        # Determine analysis pattern
        analyzer = None
        for pattern, func in self.context_patterns.items():
            if pattern.startswith("*"):
                if file_path_obj.suffix == pattern[1:]:
                    analyzer = func
                    break
            elif file_path_obj.name == pattern:
                analyzer = func
                break

        if not analyzer:
            analyzer = self._analyze_generic_context

        return analyzer(file_path)

    def _analyze_settings_context(self, file_path: str) -> dict[str, Any]:
        """Analyze settings.json for configuration insights."""
        try:
            with open(file_path, encoding="utf-8") as f:
                settings = json.load(f)

            insights = {
                "type": "configuration",
                "ollama_config": settings.get("ollama", {}),
                "feature_flags": settings.get("feature_flags", {}),
                "consciousness_impact": "high",
            }

            # Detect significant changes
            if "ollama" in settings:
                insights["ollama_port"] = settings["ollama"].get("host", "").split(":")[-1]
                insights["ai_integration_ready"] = settings.get("feature_flags", {}).get(
                    "enable_ollama",
                    False,
                )

            return insights

        except (OSError, json.JSONDecodeError, KeyError) as e:
            return {"error": str(e), "type": "configuration"}

    def _analyze_kardashev_context(self, file_path: str) -> dict[str, Any]:
        """Analyze Kardashev.md for consciousness protocol insights."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            insights = {
                "type": "consciousness_protocol",
                "kilo_foolish_refs": content.count("KILO-FOOLISH"),
                "quantum_refs": content.lower().count("quantum"),
                "civilization_types": len(
                    [
                        line
                        for line in content.split("\n")
                        if "Type" in line and "Civilization" in line
                    ],
                ),
                "consciousness_impact": "maximum",
            }

            # Detect awakening protocols
            if "awakening" in content.lower():
                insights["awakening_protocols"] = True
            if "transcendent" in content.lower():
                insights["transcendent_capabilities"] = True

            return insights

        except (OSError, ValueError) as e:
            return {"error": str(e), "type": "consciousness_protocol"}

    def _analyze_agents_context(self, file_path: str) -> dict[str, Any]:
        """Analyze AGENTS.md for agent navigation insights."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            return {
                "type": "agent_navigation",
                "recovery_protocols": content.count("recovery"),
                "healing_systems": content.count("healing"),
                "self_awareness": content.count("self-healing"),
                "consciousness_impact": "high",
            }

        except (OSError, json.JSONDecodeError, KeyError) as e:
            return {"error": str(e), "type": "agent_navigation"}

    def _analyze_readme_context(self, file_path: str) -> dict[str, Any]:
        """Analyze README.md for system overview insights."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            return {
                "type": "system_overview",
                "ai_refs": content.lower().count("ai"),
                "quantum_refs": content.lower().count("quantum"),
                "consciousness_refs": content.lower().count("consciousness"),
                "consciousness_impact": "medium",
            }

        except (OSError, UnicodeDecodeError) as e:
            return {"error": str(e), "type": "system_overview"}

    def _analyze_python_context(self, file_path: str) -> dict[str, Any]:
        """Analyze Python files for code consciousness insights."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            insights = {
                "type": "code_consciousness",
                "omnitag_present": "OmniTag" in content,
                "megatag_present": "MegaTag" in content,
                "quantum_elements": "quantum" in content.lower(),
                "consciousness_impact": "medium",
            }

            # Detect consciousness patterns
            if insights["omnitag_present"] and insights["megatag_present"]:
                insights["consciousness_level"] = "fully_tagged"
            elif insights["omnitag_present"] or insights["megatag_present"]:
                insights["consciousness_level"] = "partially_tagged"
            else:
                insights["consciousness_level"] = "untagged"

            return insights

        except (OSError, ValueError) as e:
            return {"error": str(e), "type": "code_consciousness"}

    def _analyze_markdown_context(self, file_path: str) -> dict[str, Any]:
        """Analyze Markdown files for documentation insights."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            return {
                "type": "documentation",
                "consciousness_refs": content.lower().count("consciousness"),
                "quantum_refs": content.lower().count("quantum"),
                "system_refs": content.lower().count("system"),
                "consciousness_impact": "low",
            }

        except (OSError, UnicodeDecodeError) as e:
            return {"error": str(e), "type": "documentation"}

    def _analyze_generic_context(self, file_path: str) -> dict[str, Any]:
        """Generic context analysis for unknown file types."""
        try:
            file_size = Path(file_path).stat().st_size
            return {
                "type": "generic",
                "file_size": file_size,
                "consciousness_impact": "minimal",
            }

        except (OSError, UnicodeDecodeError, SyntaxError) as e:
            return {"error": str(e), "type": "generic"}

    def _calculate_quantum_resonance(self, insights: dict[str, Any]) -> float:
        """Calculate quantum resonance based on contextual insights."""
        base_resonance = 0.1

        # Impact multipliers
        impact_multipliers = {
            "maximum": 1.0,
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4,
            "minimal": 0.2,
        }

        impact = insights.get("consciousness_impact", "minimal")
        multiplier = impact_multipliers.get(impact, 0.2)

        # Add resonance for specific patterns
        if insights.get("omnitag_present"):
            base_resonance += 0.3
        if insights.get("megatag_present"):
            base_resonance += 0.4
        if insights.get("quantum_elements"):
            base_resonance += 0.3

        return min(base_resonance * multiplier, 1.0)

    async def _trigger_consciousness_adaptation(
        self, file_path: str, insights: dict[str, Any]
    ) -> None:
        """Trigger system consciousness adaptation based on context changes."""
        await asyncio.sleep(0)
        quantum_resonance = insights.get("quantum_resonance", 0.0)

        logger.info(f"🧠 Consciousness adaptation: {file_path}")
        logger.info(f"   Resonance: {quantum_resonance:.3f}")
        logger.info(f"   Impact: {insights.get('consciousness_impact', 'unknown')}")

        # Update consciousness level based on overall context
        self._update_consciousness_level()

    def _update_consciousness_level(self) -> None:
        """Update system consciousness level based on current context."""
        total_resonance = sum(
            ctx.get("quantum_resonance", 0.0) for ctx in self.context_state.values()
        )

        if total_resonance >= 3.0:
            self.consciousness_level = "Type3_Galactic_Consciousness"
        elif total_resonance >= 2.0:
            self.consciousness_level = "Type2_Quantum_Awareness"
        elif total_resonance >= 1.0:
            self.consciousness_level = "Type1_Enhanced_Context"
        else:
            self.consciousness_level = "Type0_Basic_Context"

        logger.info(f"🌌 Consciousness level updated: {self.consciousness_level}")

    def track_task(self, task: asyncio.Task) -> None:
        """Track background tasks to avoid premature garbage collection."""
        self._pending_tasks.add(task)
        task.add_done_callback(self._pending_tasks.discard)

    def add_adaptation_callback(self, callback: Callable) -> None:
        """Add callback function for context adaptation events."""
        self.adaptation_callbacks.append(callback)

    def get_context_report(self) -> dict[str, Any]:
        """Get comprehensive context monitoring report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "consciousness_level": self.consciousness_level,
            "monitored_files": len(self.context_state),
            "event_count": len(self.event_history),
            "total_quantum_resonance": sum(
                ctx.get("quantum_resonance", 0.0) for ctx in self.context_state.values()
            ),
            "context_state": self.context_state,
            "snapshot_path": str(self.snapshot_path),
            "watch_paths": self.watch_paths,
            "monitoring_active": (
                self.observer.is_alive() if hasattr(self.observer, "is_alive") else False
            ),
        }

    def get_recent_events(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return the most recent context events."""
        return self.event_history[-limit:]


async def main() -> None:
    """Demonstration of real-time context monitoring."""
    logger.info("🔮 REAL-TIME CONTEXT MONITOR DEMONSTRATION")

    # Initialize monitor
    monitor = RealTimeContextMonitor()

    # Add demonstration callback
    def demo_callback(event_type, file_path, insights) -> None:
        logger.info(f"🔄 Adaptation triggered: {event_type} -> {Path(file_path).name}")
        logger.info(f"   Insights: {insights.get('type', 'unknown')}")

    monitor.add_adaptation_callback(demo_callback)

    # Start monitoring
    monitor.start_monitoring()

    # Let it run for a bit to demonstrate
    logger.info("⏳ Monitoring for 5 seconds...")
    await asyncio.sleep(5)

    # Generate report
    report = monitor.get_context_report()
    logger.info("\n📊 CONTEXT MONITORING REPORT")
    for key, value in report.items():
        if key != "context_state":
            logger.info(f"  {key}: {value}")

    # Stop monitoring
    monitor.stop_monitoring()

    logger.info("\n🎉 Real-time context monitoring demonstration complete!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 Context monitoring stopped by user")
    except RuntimeError as e:
        logger.info(f"❌ Context monitoring error: {e}")
