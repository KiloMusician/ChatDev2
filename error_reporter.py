"""
Enhanced ChatDev Error Reporter
Captures errors with full context, suggestions, and integration hooks

Author: NuSyQ Development Team
Version: 1.0.0
"""

import json
import traceback
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class ErrorContext:
    """Comprehensive error context"""

    timestamp: str
    error_type: str
    error_message: str
    file_location: str
    line_number: int
    function_name: str
    full_traceback: str
    expected_behavior: str
    actual_behavior: str
    possible_causes: List[str]
    suggested_fixes: List[str]
    related_logs: List[str]
    system_state: Dict[str, Any]
    severity: str  # "CRITICAL", "ERROR", "WARNING", "INFO"


class ChatDevErrorReporter:
    """Advanced error reporting with context and suggestions"""

    def __init__(self, log_dir: Path = None):
        self.log_dir = log_dir or Path("error_reports")
        self.log_dir.mkdir(exist_ok=True)

    def capture_error(
        self,
        exception: Exception,
        context: Dict[str, Any] = None,
        expected: str = "",
        actual: str = "",
    ) -> ErrorContext:
        """Capture error with full context"""

        tb = traceback.extract_tb(exception.__traceback__)
        last_frame = tb[-1] if tb else None

        # Analyze error type and provide suggestions
        error_type = type(exception).__name__
        suggestions = self._get_suggestions(exception, context)
        possible_causes = self._analyze_causes(exception, context)

        error_ctx = ErrorContext(
            timestamp=datetime.now().isoformat(),
            error_type=error_type,
            error_message=str(exception),
            file_location=last_frame.filename if last_frame else "unknown",
            line_number=last_frame.lineno if last_frame else 0,
            function_name=last_frame.name if last_frame else "unknown",
            full_traceback=traceback.format_exc(),
            expected_behavior=expected or self._infer_expected(exception),
            actual_behavior=actual or str(exception),
            possible_causes=possible_causes,
            suggested_fixes=suggestions,
            related_logs=self._find_related_logs(context),
            system_state=self._capture_system_state(context),
            severity=self._determine_severity(exception),
        )

        return error_ctx

    def _get_suggestions(
        self, exception: Exception, context: Dict[str, Any] = None
    ) -> List[str]:
        """Generate context-aware suggestions"""
        suggestions = []
        error_type = type(exception).__name__
        error_msg = str(exception).lower()

        # Ollama-specific errors
        if "llama runner process has terminated" in error_msg:
            suggestions.extend(
                [
                    "🔄 Model crashed - check available system memory",
                    "💾 Try a smaller model (e.g., qwen2.5-coder:7b instead of gemma2:9b)",
                    "🛠️ Run: ollama ps to check model status",
                    "🔧 Restart Ollama service: Restart-Service Ollama",
                    "📊 Check model size vs available RAM (gemma2:9b = ~5.4GB)",
                    "⚙️ Update model config: RoleConfig_Modular.json to use stable models",
                    "🔍 Enable verbose logging: OLLAMA_DEBUG=1",
                ]
            )

        elif "connection refused" in error_msg or "connection error" in error_msg:
            suggestions.extend(
                [
                    "🚀 Start Ollama service: ollama serve",
                    "🔌 Check if Ollama is running: ollama list",
                    "🌐 Verify Ollama API endpoint: http://localhost:11434",
                    "🔒 Check firewall settings for port 11434",
                ]
            )

        elif "model not found" in error_msg:
            suggestions.extend(
                [
                    "📥 Pull the model: ollama pull <model-name>",
                    "📋 List available models: ollama list",
                    "🔧 Update ChatDev config to use available model",
                ]
            )

        elif error_type == "ImportError":
            missing_module = self._extract_missing_module(error_msg)
            if missing_module:
                suggestions.extend(
                    [
                        f"📦 Install missing package: pip install {missing_module}",
                        f"🔍 Check requirements.txt for {missing_module}",
                        "🐍 Verify virtual environment is activated",
                    ]
                )

        elif error_type == "FileNotFoundError":
            suggestions.extend(
                [
                    "📁 Verify file path exists",
                    "🔍 Check working directory: os.getcwd()",
                    "🛤️ Use absolute paths or Path() objects",
                    "📂 Check if file was moved or deleted",
                ]
            )

        elif "openai" in error_msg and "api" in error_msg:
            suggestions.extend(
                [
                    "🔑 Check API configuration in secrets.json",
                    "🌐 Verify API endpoint URL",
                    "🔄 Ensure Ollama is configured as OpenAI-compatible endpoint",
                    "⚙️ Check base_url: http://localhost:11434/v1",
                ]
            )

        # ChatDev-specific suggestions
        if context and context.get("phase"):
            phase = context["phase"]
            suggestions.append(
                f"📍 Error in phase: {phase} - check phase configuration"
            )

        if context and context.get("agent"):
            agent = context["agent"]
            suggestions.append(
                f"🤖 Agent involved: {agent} - check agent model assignment"
            )

        # Generic suggestions
        suggestions.extend(
            [
                "📝 Check full log file for more details",
                "🔍 Search GitHub issues for similar errors",
                "💬 Enable debug mode for verbose output",
            ]
        )

        return suggestions

    def _analyze_causes(
        self, exception: Exception, context: Dict[str, Any] = None
    ) -> List[str]:
        """Analyze possible root causes"""
        causes = []
        error_msg = str(exception).lower()

        if "llama runner process has terminated" in error_msg:
            causes.extend(
                [
                    "❌ Ollama model ran out of memory (OOM)",
                    "⚠️ Model incompatibility with system architecture",
                    "🔥 Model crashed due to malformed input/prompt",
                    "💥 Concurrent model loading conflicts",
                    "🐛 Ollama service instability",
                ]
            )

        elif "connection" in error_msg:
            causes.extend(
                [
                    "🔌 Ollama service not running",
                    "🌐 Network/firewall blocking localhost:11434",
                    "⏱️ Service startup timeout",
                ]
            )

        elif "import" in error_msg.lower():
            causes.extend(
                [
                    "📦 Missing Python package in virtual environment",
                    "🐍 Wrong Python version or environment",
                    "📁 PYTHONPATH configuration issue",
                ]
            )

        return causes

    def _infer_expected(self, exception: Exception) -> str:
        """Infer what was expected to happen"""
        error_type = type(exception).__name__

        expectations = {
            "FileNotFoundError": "File should exist at specified path",
            "ImportError": "Python module should be installed and importable",
            "ConnectionError": "Service should be running and accessible",
            "InternalServerError": "Model should respond successfully to chat completion request",
            "TimeoutError": "Operation should complete within timeout period",
        }

        return expectations.get(error_type, "Operation should complete successfully")

    def _extract_missing_module(self, error_msg: str) -> Optional[str]:
        """Extract missing module name from ImportError"""
        if "no module named" in error_msg:
            parts = error_msg.split("'")
            if len(parts) >= 2:
                return parts[1]
        return None

    def _find_related_logs(self, context: Dict[str, Any] = None) -> List[str]:
        """Find related log files"""
        logs = []

        if context and context.get("log_file"):
            logs.append(context["log_file"])

        # Look for recent ChatDev logs
        warehouse_dir = Path("WareHouse")
        if warehouse_dir.exists():
            log_files = sorted(
                warehouse_dir.glob("**/*.log"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            logs.extend([str(f) for f in log_files[:3]])

        return logs

    def _capture_system_state(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Capture relevant system state"""
        state = {
            "python_version": sys.version,
            "platform": sys.platform,
            "cwd": str(Path.cwd()),
        }

        if context:
            state.update(context)

        # Try to get Ollama status
        try:
            import subprocess

            result = subprocess.run(
                ["ollama", "ps"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            state["ollama_status"] = result.stdout
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError):
            state["ollama_status"] = "Unable to check Ollama status"

        return state

    def _determine_severity(self, exception: Exception) -> str:
        """Determine error severity"""
        error_type = type(exception).__name__

        critical_errors = ["SystemExit", "KeyboardInterrupt", "MemoryError"]
        high_errors = ["InternalServerError", "ConnectionError", "TimeoutError"]

        if error_type in critical_errors:
            return "CRITICAL"
        elif error_type in high_errors:
            return "ERROR"
        else:
            return "WARNING"

    def save_report(self, error_ctx: ErrorContext) -> Path:
        """Save error report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"error_report_{timestamp}.json"
        filepath = self.log_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(error_ctx), f, indent=2)

        return filepath

    def format_report(self, error_ctx: ErrorContext) -> str:
        """Format error report for console output"""
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         ChatDev Error Report                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

⏰ Timestamp: {error_ctx.timestamp}
🔥 Severity: {error_ctx.severity}
❌ Error Type: {error_ctx.error_type}
💬 Message: {error_ctx.error_message}

📍 Location:
   File: {error_ctx.file_location}
   Line: {error_ctx.line_number}
   Function: {error_ctx.function_name}

📋 Expected Behavior:
   {error_ctx.expected_behavior}

⚠️ Actual Behavior:
   {error_ctx.actual_behavior}

🔍 Possible Causes:
"""
        for cause in error_ctx.possible_causes:
            report += f"   {cause}\n"

        report += "\n💡 Suggested Fixes:\n"
        for fix in error_ctx.suggested_fixes:
            report += f"   {fix}\n"

        if error_ctx.related_logs:
            report += "\n📂 Related Logs:\n"
            for log in error_ctx.related_logs:
                report += f"   {log}\n"

        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 Full Traceback:
{error_ctx.full_traceback}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return report


def wrap_chatdev_execution(func):
    """Decorator to wrap ChatDev execution with error reporting"""

    def wrapper(*args, **kwargs):
        reporter = ChatDevErrorReporter()

        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Extract context from kwargs or args
            context = {
                "function": func.__name__,
                "args": str(args)[:500],  # Truncate for readability
            }

            # Capture and report error
            error_ctx = reporter.capture_error(
                e,
                context=context,
                expected="ChatDev should complete task successfully",
                actual=f"ChatDev failed with {type(e).__name__}",
            )

            # Save report
            report_path = reporter.save_report(error_ctx)

            # Print formatted report
            print(reporter.format_report(error_ctx))
            print(f"\n📝 Full report saved to: {report_path}")

            # Re-raise exception
            raise

    return wrapper


if __name__ == "__main__":
    # Test error reporter
    reporter = ChatDevErrorReporter()

    try:
        # Simulate Ollama crash error
        raise Exception("llama runner process has terminated: exit status 2")
    except Exception as e:
        error_ctx = reporter.capture_error(
            e,
            context={"phase": "DemandAnalysis", "agent": "Chief Product Officer"},
            expected="CPO agent should respond to CEO prompt",
            actual="gemma2:9b model crashed during response generation",
        )

        print(reporter.format_report(error_ctx))
        report_path = reporter.save_report(error_ctx)
        print(f"\nReport saved to: {report_path}")
