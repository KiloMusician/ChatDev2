"""NuSyQ-Hub Autonomous Development Dashboard API.

REST API backend for real-time monitoring of:
- Extended autonomous healing cycles
- Issue detection and routing
- ChatDev multi-agent task execution
- System health metrics
- Resolution tracking

Architecture:
- Flask-based REST API (port 5001)
- WebSocket support for real-time updates
- JSON reporting endpoints
- Historical data persistence
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")


class DashboardAPI:
    """Wrapper class for Dashboard API to support import as 'from src.web.dashboard_api import DashboardAPI'."""

    def __init__(self) -> None:
        """Initialize Dashboard API."""
        self.app = app
        self.socketio = socketio
        self.collector = DashboardMetricsCollector()
        self.metrics_file = REPORTS_DIR / "latest_metrics.json"
        logger.info("✅ Dashboard API initialized")

    def run(self, host="0.0.0.0", port=5001, debug=False) -> None:
        """Run the dashboard server."""
        logger.info(f"🚀 Starting NuSyQ-Hub Dashboard API on http://{host}:{port}")
        socketio.run(self.app, host=host, port=port, debug=debug)

    def record_cycle(self, cycle_data: dict) -> None:
        """Record a healing cycle's data."""
        if self.collector:
            # Convert dict to CycleMetrics if needed
            if not isinstance(cycle_data, CycleMetrics):
                cycle_data = CycleMetrics(**cycle_data)
            self.collector.cycles.append(cycle_data)

        # Also save to metrics file
        self.metrics_file.write_text(
            json.dumps(
                cycle_data if isinstance(cycle_data, dict) else asdict(cycle_data),
                indent=2,
            ),
            encoding="utf-8",
        )

    def get_metrics(self) -> dict:
        """Get current dashboard metrics."""
        if self.collector:
            return {
                "cycles": [asdict(c) for c in self.collector.cycles],
                "status_history": [asdict(s) for s in self.collector.status_history],
            }
        return {"cycles": [], "status_history": []}


# Data storage paths
REPORTS_DIR = Path("Reports/dashboard")
METRICS_DIR = Path("Reports/metrics")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class CycleMetrics:
    """Single healing cycle metrics."""

    cycle_num: int = 0
    timestamp: str = ""
    issues_detected: int = 0
    tasks_created: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    healing_applied: int = 0
    health_status: str = ""
    duration_seconds: float = 0.0
    issues_by_type: dict[str, int] = field(default_factory=dict)


@dataclass
class SystemStatus:
    """Overall system health status."""

    timestamp: str
    status: str  # healthy, degraded, critical
    cycles_completed: int
    total_issues_detected: int
    total_issues_fixed: int
    uptime_minutes: int
    last_cycle_timestamp: str | None
    ai_systems_online: int
    ai_systems_total: int


class DashboardMetricsCollector:
    """Collects and manages dashboard metrics."""

    def __init__(self) -> None:
        """Initialize DashboardMetricsCollector."""
        self.cycles: list[CycleMetrics] = []
        self.status_history: list[SystemStatus] = []
        self.startup_time = datetime.now()
        self.load_historical_data()

    def load_historical_data(self) -> None:
        """Load metrics from recent reports."""
        try:
            # Load unified healing pipeline reports
            for report_file in sorted(REPORTS_DIR.glob("unified_healing_report_*.json"))[-10:]:
                try:
                    with open(report_file, encoding="utf-8") as f:
                        data = json.load(f)
                        self._parse_unified_report(data)
                except Exception as e:
                    logger.warning(f"Failed to load report {report_file}: {e}")
        except Exception as e:
            logger.warning(f"Failed to load historical data: {e}")

    def _parse_unified_report(self, data: dict) -> None:
        """Parse unified healing pipeline report."""
        try:
            for i, cycle_data in enumerate(data.get("cycles", []), 1):
                cycle_metric = CycleMetrics(
                    cycle_num=i,
                    timestamp=cycle_data.get("timestamp", datetime.now().isoformat()),
                    issues_detected=cycle_data.get("issues_detected", 0),
                    issues_by_type=cycle_data.get("issues_summary", {}),
                    tasks_created=cycle_data.get("tasks_created", 0),
                    tasks_completed=cycle_data.get("tasks_completed", 0),
                    tasks_failed=cycle_data.get("tasks_failed", 0),
                    healing_applied=cycle_data.get("healing_applied", 0),
                    health_status=cycle_data.get("health_status", "unknown"),
                    duration_seconds=cycle_data.get("duration", 0),
                )
                if cycle_metric not in self.cycles:
                    self.cycles.append(cycle_metric)
        except Exception as e:
            logger.debug(f"Error parsing report: {e}")

    def add_cycle(self, cycle_metrics: CycleMetrics) -> None:
        """Add new cycle metrics."""
        self.cycles.append(cycle_metrics)

    def get_system_status(self) -> SystemStatus:
        """Calculate current system status."""
        if not self.cycles:
            return SystemStatus(
                timestamp=datetime.now().isoformat(),
                status="initializing",
                cycles_completed=0,
                total_issues_detected=0,
                total_issues_fixed=0,
                uptime_minutes=0,
                last_cycle_timestamp=None,
                ai_systems_online=5,
                ai_systems_total=5,
            )

        # Calculate metrics
        total_issues = sum(c.issues_detected for c in self.cycles)
        total_fixed = sum(c.healing_applied for c in self.cycles)
        last_cycle = self.cycles[-1]
        uptime = int((datetime.now() - self.startup_time).total_seconds() / 60)

        # Determine status
        failed_tasks = sum(c.tasks_failed for c in self.cycles[-5:] if c)
        if failed_tasks > 2:
            status = "degraded"
        elif last_cycle.health_status == "healthy":
            status = "healthy"
        else:
            status = "unknown"

        return SystemStatus(
            timestamp=datetime.now().isoformat(),
            status=status,
            cycles_completed=len(self.cycles),
            total_issues_detected=total_issues,
            total_issues_fixed=total_fixed,
            uptime_minutes=uptime,
            last_cycle_timestamp=last_cycle.timestamp,
            ai_systems_online=5,
            ai_systems_total=5,
        )

    def get_recent_cycles(self, limit: int = 10) -> list[CycleMetrics]:
        """Get recent cycle metrics."""
        return self.cycles[-limit:] if self.cycles else []

    def get_trends(self, hours: int = 24) -> dict[str, Any]:
        """Calculate trends over time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_cycles = [
            c for c in self.cycles if datetime.fromisoformat(c.timestamp) > cutoff_time
        ]

        if not recent_cycles:
            return {}

        return {
            "cycles": len(recent_cycles),
            "avg_issues_per_cycle": sum(c.issues_detected for c in recent_cycles)
            / len(recent_cycles),
            "total_issues": sum(c.issues_detected for c in recent_cycles),
            "total_fixed": sum(c.healing_applied for c in recent_cycles),
            "avg_tasks_created": sum(c.tasks_created for c in recent_cycles) / len(recent_cycles),
            "success_rate": (
                sum(c.tasks_completed for c in recent_cycles)
                / max(sum(c.tasks_created for c in recent_cycles), 1)
                * 100
            ),
        }


# Global metrics collector
metrics = DashboardMetricsCollector()


# ============================================================================
# API ENDPOINTS
# ============================================================================


@app.route("/api/health", methods=["GET"])
def health_check():
    """System health check endpoint."""
    status = metrics.get_system_status()
    return jsonify(asdict(status))


@app.route("/api/cycles", methods=["GET"])
def get_cycles():
    """Get recent healing cycles."""
    limit = request.args.get("limit", 10, type=int)
    cycles = metrics.get_recent_cycles(limit)
    return jsonify([asdict(c) for c in cycles])


@app.route("/api/cycles/<int:cycle_num>", methods=["GET"])
def get_cycle(cycle_num):
    """Get specific cycle details."""
    cycle = next((c for c in metrics.cycles if c.cycle_num == cycle_num), None)
    if not cycle:
        return jsonify({"error": f"Cycle {cycle_num} not found"}), 404
    return jsonify(asdict(cycle))


@app.route("/api/issues", methods=["GET"])
def get_issues():
    """Get issue detection summary."""
    cycles = metrics.get_recent_cycles(5)

    # Aggregate issues by type
    issues_by_type = {}
    for cycle in cycles:
        for issue_type, count in cycle.issues_by_type.items():
            issues_by_type[issue_type] = issues_by_type.get(issue_type, 0) + count

    return jsonify(
        {
            "total_detected": sum(c.issues_detected for c in cycles),
            "by_type": issues_by_type,
            "last_updated": cycles[-1].timestamp if cycles else None,
        }
    )


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    """Get ChatDev task execution status."""
    cycles = metrics.get_recent_cycles(10)

    total_created = sum(c.tasks_created for c in cycles)
    total_completed = sum(c.tasks_completed for c in cycles)
    total_failed = sum(c.tasks_failed for c in cycles)

    success_rate = (total_completed / total_created * 100) if total_created > 0 else 0

    return jsonify(
        {
            "tasks_created": total_created,
            "tasks_completed": total_completed,
            "tasks_failed": total_failed,
            "success_rate": round(success_rate, 2),
            "pending": total_created - total_completed - total_failed,
        }
    )


@app.route("/api/trends", methods=["GET"])
def get_trends():
    """Get performance trends."""
    hours = request.args.get("hours", 24, type=int)
    trends = metrics.get_trends(hours)
    return jsonify(trends) if trends else jsonify({"error": "No data available"}), 204


@app.route("/api/reports", methods=["GET"])
def list_reports():
    """List available reports."""
    reports = []
    for report_file in sorted(REPORTS_DIR.glob("*.json"), reverse=True)[:20]:
        reports.append(
            {
                "filename": report_file.name,
                "created": datetime.fromtimestamp(report_file.stat().st_mtime).isoformat(),
                "size_bytes": report_file.stat().st_size,
            }
        )
    return jsonify(reports)


@app.route("/api/reports/<report_name>", methods=["GET"])
def get_report(report_name):
    """Get specific report contents."""
    report_file = REPORTS_DIR / report_name

    if not report_file.exists() or ".." in report_name:
        return jsonify({"error": "Report not found"}), 404

    try:
        with open(report_file, encoding="utf-8") as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"error": f"Failed to read report: {e}"}), 500


@app.route("/api/metrics/performance", methods=["GET"])
def performance_metrics():
    """Get performance metrics."""
    cycles = metrics.get_recent_cycles(20)

    if not cycles:
        return jsonify({"error": "No cycle data"}), 204

    return jsonify(
        {
            "avg_cycle_duration": sum(c.duration_seconds for c in cycles) / len(cycles),
            "avg_issues_detected": sum(c.issues_detected for c in cycles) / len(cycles),
            "avg_healing_applied": sum(c.healing_applied for c in cycles) / len(cycles),
            "cycles_analyzed": len(cycles),
        }
    )


# ============================================================================
# WebSocket Support for Real-time Updates
# ============================================================================


@socketio.on("connect")
def handle_connect():
    """Client connected."""
    logger.info("Dashboard client connected")
    emit("response", {"data": "Connected to NuSyQ-Hub Dashboard"})


@socketio.on("request_status")
def handle_status_request():
    """Send current system status."""
    status = metrics.get_system_status()
    emit("status_update", asdict(status))


@socketio.on("request_metrics")
def handle_metrics_request():
    """Send recent metrics."""
    cycles = metrics.get_recent_cycles(10)
    emit(
        "metrics_update",
        {
            "cycles": [asdict(c) for c in cycles],
            "timestamp": datetime.now().isoformat(),
        },
    )


@socketio.on("disconnect")
def handle_disconnect():
    """Client disconnected."""
    logger.info("Dashboard client disconnected")


# ============================================================================
# Metric Injection Endpoints (for cycle runners)
# ============================================================================


@app.route("/api/cycles/record", methods=["POST"])
def record_cycle():
    """Record new healing cycle metrics (called by cycle runners)."""
    try:
        data = request.get_json()
        cycle_metric = CycleMetrics(
            cycle_num=data["cycle_num"],
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            issues_detected=data.get("issues_detected", 0),
            issues_by_type=data.get("issues_by_type", {}),
            tasks_created=data.get("tasks_created", 0),
            tasks_completed=data.get("tasks_completed", 0),
            tasks_failed=data.get("tasks_failed", 0),
            healing_applied=data.get("healing_applied", 0),
            health_status=data.get("health_status", "unknown"),
            duration_seconds=data.get("duration_seconds", 0),
        )
        metrics.add_cycle(cycle_metric)

        # Emit real-time update to connected clients
        socketio.emit("cycle_recorded", asdict(cycle_metric), broadcast=True)

        return jsonify({"status": "recorded", "cycle_num": cycle_metric.cycle_num}), 201
    except Exception as e:
        logger.error(f"Failed to record cycle: {e}")
        return jsonify({"error": str(e)}), 400


# ============================================================================
# Static HTML Dashboard (simple fallback)
# ============================================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>NuSyQ-Hub Autonomous Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #333; color: white; padding: 20px; border-radius: 5px; }
            .metrics {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-value { font-size: 32px; font-weight: bold; color: #333; }
        .metric-label { color: #666; margin-top: 5px; }
        .status-healthy { color: #4CAF50; }
        .status-degraded { color: #FF9800; }
        .status-critical { color: #F44336; }
        .chart { background: white; padding: 20px; border-radius: 5px; margin-top: 20px; }
    </style>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 NuSyQ-Hub Autonomous Development Dashboard</h1>
            <p>Real-time monitoring of autonomous healing cycles and AI agent coordination</p>
        </div>

        <div class="metrics">
            <div class="metric-card">
                <div class="metric-label">System Status</div>
                <div class="metric-value" id="status">—</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Cycles Completed</div>
                <div class="metric-value" id="cycles">—</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Issues Detected</div>
                <div class="metric-value" id="issues">—</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Issues Fixed</div>
                <div class="metric-value" id="fixed">—</div>
            </div>
        </div>

        <div class="chart">
            <h3>Recent Cycles</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #eee;">
                        <th style="padding: 10px; text-align: left;">Cycle</th>
                        <th style="padding: 10px; text-align: left;">Issues</th>
                        <th style="padding: 10px; text-align: left;">Tasks</th>
                        <th style="padding: 10px; text-align: left;">Fixed</th>
                        <th style="padding: 10px; text-align: left;">Status</th>
                    </tr>
                </thead>
                <tbody id="cycles-table">
                    <tr>
                        <td colspan="5" style="text-align: center; padding: 20px;">
                            Loading...
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const socket = io();

        // Connect and request initial data
        socket.on('connect', function() {
            socket.emit('request_status');
            socket.emit('request_metrics');
        });

        // Update status
        socket.on('status_update', function(data) {
            document.getElementById('status').textContent = data.status;
            document.getElementById('status').className = 'metric-value status-' + data.status;
            document.getElementById('cycles').textContent = data.cycles_completed;
            document.getElementById('issues').textContent = data.total_issues_detected;
            document.getElementById('fixed').textContent = data.total_issues_fixed;
        });

        // Update metrics
        socket.on('metrics_update', function(data) {
            const tbody = document.getElementById('cycles-table');
            tbody.innerHTML = '';
            data.cycles.forEach(cycle => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td style="padding: 10px;">#${cycle.cycle_num}</td>
                    <td style="padding: 10px;">${cycle.issues_detected}</td>
                    <td style="padding: 10px;">${cycle.tasks_created}</td>
                    <td style="padding: 10px;">${cycle.healing_applied}</td>
                    <td style="padding: 10px;">${cycle.health_status}</td>
                `;
            });
        });

        // Real-time cycle recording
        socket.on('cycle_recorded', function(data) {
            socket.emit('request_metrics');  // Refresh metrics
        });
    </script>
</body>
</html>
"""


@app.route("/")
def dashboard():
    """Serve dashboard HTML."""
    return DASHBOARD_HTML


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("🚀 Starting NuSyQ-Hub Dashboard API on http://localhost:5001")
    socketio.run(app, host="0.0.0.0", port=5001, debug=False)
