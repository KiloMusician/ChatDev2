"""Interactive Testing Dashboard for AI Systems.

Provides real-time visualization and control of test execution across
all AI systems with comprehensive metrics and insights.

OmniTag: {
    "purpose": "Interactive testing dashboard with real-time metrics",
    "dependencies": ["flask", "pytest", "unified_ai_context_manager"],
    "context": "Unified testing interface for all AI systems",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

import logging
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Represents a test execution result."""

    test_name: str
    status: str  # passed, failed, skipped, error
    duration: float
    error_message: str | None = None
    timestamp: str = ""


@dataclass
class TestSuite:
    """Represents a test suite."""

    name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration: float
    timestamp: str


class TestingDashboard:
    """Interactive dashboard for test execution and monitoring."""

    def __init__(self, host: str = "localhost", port: int = 5001) -> None:
        """Initialize testing dashboard.

        Args:
            host: Dashboard host address
            port: Dashboard port number

        """
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)

        # Dashboard state
        self.test_results: list[TestResult] = []
        self.test_suites: list[TestSuite] = []
        self.current_execution: dict[str, Any] | None = None
        self.execution_history: list[dict[str, Any]] = []

        # Register routes
        self._register_routes()

        logger.info("Testing Dashboard initialized on %s:%s", host, port)

    def _register_routes(self) -> None:
        """Register Flask routes for dashboard."""

        @self.app.route("/")
        def index():
            """Dashboard home page."""
            return render_template_string(DASHBOARD_HTML)  # static internal template # nosemgrep

        @self.app.route("/api/status")
        def get_status():
            """Get dashboard status."""
            return jsonify(
                {
                    "status": "running",
                    "current_execution": self.current_execution,
                    "total_suites": len(self.test_suites),
                    "total_tests": sum(s.total_tests for s in self.test_suites),
                    "timestamp": datetime.now().isoformat(),
                },
            )

        @self.app.route("/api/suites")
        def get_suites():
            """Get all test suites."""
            return jsonify(
                {
                    "suites": [asdict(s) for s in self.test_suites],
                    "count": len(self.test_suites),
                },
            )

        @self.app.route("/api/results")
        def get_results():
            """Get test results."""
            limit = request.args.get("limit", 100, type=int)
            return jsonify(
                {
                    "results": [asdict(r) for r in self.test_results[-limit:]],
                    "count": len(self.test_results),
                },
            )

        @self.app.route("/api/execute", methods=["POST"])
        def execute_tests():
            """Execute tests."""
            data = request.get_json()
            test_path = data.get("test_path", "tests/")
            markers = data.get("markers", [])

            execution_id = f"exec_{int(time.time())}"
            self.current_execution = {
                "id": execution_id,
                "test_path": test_path,
                "markers": markers,
                "status": "running",
                "start_time": datetime.now().isoformat(),
            }

            # Execute tests asynchronously
            result = self._execute_pytest(test_path, markers)

            self.current_execution["status"] = "completed"
            self.current_execution["end_time"] = datetime.now().isoformat()
            self.execution_history.append(self.current_execution.copy())
            self.current_execution = None

            return jsonify({"execution_id": execution_id, "result": result})

        @self.app.route("/api/history")
        def get_history():
            """Get execution history."""
            return jsonify(
                {
                    "executions": self.execution_history,
                    "count": len(self.execution_history),
                },
            )

        @self.app.route("/api/metrics")
        def get_metrics():
            """Get test metrics."""
            total_passed = sum(s.passed for s in self.test_suites)
            total_failed = sum(s.failed for s in self.test_suites)
            total_tests = sum(s.total_tests for s in self.test_suites)

            pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

            return jsonify(
                {
                    "total_suites": len(self.test_suites),
                    "total_tests": total_tests,
                    "total_passed": total_passed,
                    "total_failed": total_failed,
                    "pass_rate": round(pass_rate, 2),
                    "average_duration": (
                        sum(s.duration for s in self.test_suites) / len(self.test_suites)
                        if self.test_suites
                        else 0
                    ),
                },
            )

    def _execute_pytest(self, test_path: str, markers: list[str]) -> dict[str, Any]:
        """Execute pytest and parse results.

        Args:
            test_path: Path to tests
            markers: Pytest markers to filter

        Returns:
            Execution results

        """
        start_time = time.time()

        # Build pytest command
        cmd = ["pytest", test_path, "-v", "--tb=short"]
        for marker in markers:
            cmd.extend(["-m", marker])

        try:
            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            duration = time.time() - start_time

            # Parse output (simplified)
            output = result.stdout + result.stderr
            passed = output.count(" PASSED")
            failed = output.count(" FAILED")
            skipped = output.count(" SKIPPED")

            # Create test suite
            suite = TestSuite(
                name=f"Suite {len(self.test_suites) + 1}",
                total_tests=passed + failed + skipped,
                passed=passed,
                failed=failed,
                skipped=skipped,
                duration=duration,
                timestamp=datetime.now().isoformat(),
            )

            self.test_suites.append(suite)

            return {
                "success": result.returncode == 0,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "duration": duration,
                "output": output[:1000],  # Truncate output
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test execution timed out",
                "duration": time.time() - start_time,
            }
        except Exception as e:
            logger.exception("Error executing tests")
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time,
            }

    def run(self, debug: bool = False) -> None:
        """Run the dashboard server.

        Args:
            debug: Enable Flask debug mode

        """
        logger.info("Starting Testing Dashboard on %s:%s", self.host, self.port)
        self.app.run(host=self.host, port=self.port, debug=debug)


# Dashboard HTML template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NuSyQ-Hub Testing Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s;
        }
        .metric-card:hover {
            transform: translateY(-5px);
        }
        .metric-label {
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        .metric-value {
            font-size: 36px;
            font-weight: bold;
            color: #333;
        }
        .metric-card.success .metric-value { color: #10b981; }
        .metric-card.danger .metric-value { color: #ef4444; }
        .metric-card.info .metric-value { color: #3b82f6; }
        .control-panel {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        .btn:hover {
            background: #5568d3;
        }
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .results-section {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .test-result {
            padding: 15px;
            border-left: 4px solid #ccc;
            margin-bottom: 10px;
            background: #f9fafb;
        }
        .test-result.passed { border-color: #10b981; }
        .test-result.failed { border-color: #ef4444; }
        .test-result.skipped { border-color: #f59e0b; }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-indicator.running {
            background: #3b82f6;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 NuSyQ-Hub Testing Dashboard</h1>

        <div class="metrics-grid" id="metrics">
            <div class="metric-card info">
                <div class="metric-label">Total Tests</div>
                <div class="metric-value" id="total-tests">0</div>
            </div>
            <div class="metric-card success">
                <div class="metric-label">Passed</div>
                <div class="metric-value" id="passed-tests">0</div>
            </div>
            <div class="metric-card danger">
                <div class="metric-label">Failed</div>
                <div class="metric-value" id="failed-tests">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Pass Rate</div>
                <div class="metric-value" id="pass-rate">0%</div>
            </div>
        </div>

        <div class="control-panel">
            <h2>Test Execution</h2>
            <button class="btn" onclick="runTests()" id="run-btn">
                Run All Tests
            </button>
            <button class="btn" onclick="runTests('integration')">
                Run Integration Tests
            </button>
            <button class="btn" onclick="runTests('unit')">
                Run Unit Tests
            </button>
            <div id="status" style="margin-top: 15px;"></div>
        </div>

        <div class="results-section">
            <h2>Recent Test Suites</h2>
            <div id="suites"></div>
        </div>
    </div>

    <script>
        function updateMetrics() {
            fetch('/api/metrics')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('total-tests').textContent = data.total_tests;
                    document.getElementById('passed-tests').textContent = data.total_passed;
                    document.getElementById('failed-tests').textContent = data.total_failed;
                    document.getElementById('pass-rate').textContent = data.pass_rate + '%';
                });
        }

        function updateSuites() {
            fetch('/api/suites')
                .then(r => r.json())
                .then(data => {
                    const suitesDiv = document.getElementById('suites');
                    suitesDiv.innerHTML = data.suites.map(suite => `
                        <div class="test-result">
                            <strong>${suite.name}</strong> -
                            ${suite.passed} passed, ${suite.failed} failed, ${suite.skipped} skipped
                            (${suite.duration.toFixed(2)}s)
                        </div>
                    `).join('');
                });
        }

        function runTests(marker = '') {
            const btn = document.getElementById('run-btn');
            const status = document.getElementById('status');

            btn.disabled = true;
            status.innerHTML = '<span class="status-indicator running"></span>Running tests...';

            fetch('/api/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    test_path: 'tests/',
                    markers: marker ? [marker] : []
                })
            })
            .then(r => r.json())
            .then(data => {
                btn.disabled = false;
                status.innerHTML = data.result.success ?
                    '✅ Tests completed successfully!' :
                    '❌ Tests failed';
                updateMetrics();
                updateSuites();
            })
            .catch(err => {
                btn.disabled = false;
                status.innerHTML = '❌ Error: ' + err.message;
            });
        }

        // Update dashboard every 5 seconds
        setInterval(() => {
            updateMetrics();
            updateSuites();
        }, 5000);

        // Initial load
        updateMetrics();
        updateSuites();
    </script>
</body>
</html>
"""


def main() -> None:
    """Main entry point for testing dashboard."""
    dashboard = TestingDashboard(host="localhost", port=5001)
    dashboard.run(debug=False)


if __name__ == "__main__":
    main()
