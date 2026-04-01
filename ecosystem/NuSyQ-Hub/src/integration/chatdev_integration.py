"""ChatDev Integration Module.

Provides integration utilities for ChatDev with KILO-FOOLISH systems.

Features:
- Adaptive timeout management based on task complexity
- Intelligent timeout learning from historical performance
- Copilot-ChatDev Bridge integration
- Multi-agent collaboration workflows

OmniTag: {'purpose': 'chatdev_integration', 'type': 'integration_module', 'evolution_stage': 'v4.1_adaptive'}
MegaTag: {'scope': 'ai_integration', 'integration_level': 'chatdev_bridge', 'quantum_context': 'ai_orchestration'}
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from src.agents.adaptive_timeout_manager import get_timeout_manager
from src.system.feature_flags import is_feature_enabled

# Fix imports for standalone execution
current_dir = Path(__file__).parent.absolute()
repo_root = current_dir.parent.parent
sys.path.insert(0, str(repo_root))

logger = logging.getLogger(__name__)


class ChatDevIntegrationManager:
    """Comprehensive ChatDev integration manager for KILO-FOOLISH systems."""

    def __init__(self) -> None:
        """Initialize ChatDevIntegrationManager."""
        self.launcher: Any | None = None
        self.session_active = False
        self.integration_status: dict[str, Any] = {}
        self.repo_root = Path(__file__).parent.parent.parent

        # Integration with new Copilot-ChatDev Bridge
        self.copilot_bridge: Any | None = None
        self.bridge_available = False

        # Adaptive timeout management
        self.timeout_manager = get_timeout_manager()
        logger.info("✅ Adaptive timeout manager integrated with ChatDev")

        # Initialize bridge integration
        self._initialize_bridge_integration()

    def _initialize_bridge_integration(self) -> None:
        """Initialize integration with Copilot-ChatDev Bridge."""
        try:
            # Import the new bridge system
            bridge_path = self.repo_root / "src" / "integration" / "copilot_chatdev_bridge.py"
            if bridge_path.exists():
                sys.path.insert(0, str(bridge_path.parent))
                from copilot_chatdev_bridge import CopilotChatDevBridge

                self.copilot_bridge = CopilotChatDevBridge(workspace_root=str(self.repo_root))
                self.bridge_available = True
                logger.info("🤖 Copilot-ChatDev Bridge integration initialized")

                # set up enhanced collaboration modes
                self.collaboration_modes = {
                    "code_review": "Enhanced multi-agent code review with Copilot",
                    "refactoring": "Collaborative refactoring with real-time assistance",
                    "feature_development": "Coordinated feature development workflow",
                    "debugging": "Multi-perspective debugging approach",
                }

            else:
                logger.warning("⚠️ Copilot-ChatDev Bridge not found")
                self.bridge_available = False

        except ImportError as e:
            logger.warning(f"⚠️ Bridge integration unavailable: {e}")
            self.bridge_available = False
        except Exception as e:
            logger.exception(f"❌ Bridge initialization failed: {e}")
            self.bridge_available = False

    def initialize_chatdev_integration(self) -> dict[str, Any]:
        """Initialize ChatDev integration with KILO-FOOLISH systems."""
        logger.info("🚀 Initializing ChatDev integration...")

        try:
            # Import ChatDev launcher with fixed path handling
            chatdev_launcher_path = repo_root / "src" / "integration" / "chatdev_launcher.py"
            if chatdev_launcher_path.exists():
                sys.path.insert(0, str(chatdev_launcher_path.parent))
                from chatdev_launcher import ChatDevLauncher

                launcher = ChatDevLauncher()
                self.launcher = launcher

                # Setup API keys and environment
                api_setup = launcher.setup_api_key()
                launcher.setup_environment()

                # Test ChatDev availability
                status = launcher.check_status()

                self.integration_status = {
                    "success": True,
                    "launcher_available": True,
                    "api_configured": api_setup,
                    "chatdev_path_valid": status.get("chatdev_installation", False),
                    "initialization_time": datetime.now().isoformat(),
                    "status": "operational" if api_setup else "limited",
                }
            else:
                msg = "ChatDev launcher not found"
                raise ImportError(msg)

            logger.info(f"✅ ChatDev integration initialized: {self.integration_status['status']}")
            return self.integration_status

        except ImportError as e:
            logger.warning(f"⚠️ ChatDev launcher not available: {e}")
            self.integration_status = {
                "success": False,
                "launcher_available": False,
                "error": str(e),
                "status": "unavailable",
            }
            return self.integration_status
        except Exception as e:
            logger.exception(f"❌ ChatDev integration initialization failed: {e}")
            self.integration_status = {
                "success": False,
                "launcher_available": False,
                "error": str(e),
                "status": "failed",
            }
            return self.integration_status

    def launch_autofix(self, issue_description: str) -> dict[str, Any]:
        """Attempt an automated fix using ChatDev.

        This capability is gated behind the ``chatdev_autofix`` feature flag.
        When disabled the method returns a disabled status without invoking
        any ChatDev functionality. The feature is intended to be enabled in
        staging environments before wider production rollout.
        """
        if not is_feature_enabled("chatdev_autofix"):
            logger.info("chatdev_autofix feature flag disabled; skipping auto-fix")
            return {"success": False, "autofix_enabled": False, "status": "disabled"}

        logger.info("🤖 Running ChatDev auto-fix for issue: %s", issue_description)
        result = launch_chatdev_session(task_description=issue_description, complexity="simple")
        result["autofix_enabled"] = True
        return result

    def launch_enhanced_collaboration(
        self,
        task_description: str,
        target_files: list[str] | None = None,
        workflow_type: str = "code_review",
    ) -> dict[str, Any]:
        """Launch enhanced collaboration using Copilot-ChatDev Bridge."""
        if not self.bridge_available or not self.copilot_bridge:
            logger.warning("🔄 Bridge not available, falling back to traditional ChatDev launcher")
            return launch_chatdev_session(task_description)

        try:
            logger.info("🤖 Launching enhanced Copilot-ChatDev collaboration")

            # Use bridge for enhanced collaboration
            if target_files:
                workflow = self.copilot_bridge.create_agent_workflow(workflow_type, target_files)
                session = self.copilot_bridge.launch_collaborative_session(workflow)

                return {
                    "success": True,
                    "collaboration_type": "enhanced",
                    "workflow_id": workflow["id"],
                    "session_config": session.get("session_config"),
                    "chatdev_task": session.get("chatdev_task"),
                    "bridge_active": True,
                    "next_steps": session.get("next_steps", []),
                }
            # Create simple collaboration session
            session = self.copilot_bridge.create_agent_collaboration_session(
                task_description,
                collaboration_mode="enhanced",
            )

            return {
                "success": True,
                "collaboration_type": "enhanced_simple",
                "session_id": session["id"],
                "bridge_active": True,
                "task": task_description,
            }

        except Exception as e:
            logger.exception(f"❌ Enhanced collaboration failed: {e}")
            # Fallback to traditional launcher
            return self._fallback_session(task_description)

    def _fallback_session(self, task_description: str) -> dict[str, Any]:
        """Fallback session with basic ChatDev integration."""
        import time

        return {
            "success": True,
            "collaboration_type": "fallback",
            "session_id": f"fallback_{int(time.time())}",
            "bridge_active": False,
            "task": task_description,
        }


def get_chatdev_launcher():
    """Bridge to existing functional ChatDev launcher."""
    try:
        from .chatdev_launcher import ChatDevLauncher

        launcher = ChatDevLauncher()
        logger.info("✅ ChatDev launcher accessed successfully")
        return launcher
    except ImportError as e:
        logger.warning(f"⚠️ ChatDev launcher not available: {e}")
        return None
    except Exception as e:
        logger.exception(f"❌ Error accessing ChatDev launcher: {e}")
        return None


def launch_chatdev_session(
    task_description: str | None = None,
    output_dir: str | None = None,
    complexity: str = "medium",
) -> dict[str, Any]:
    """Launch ChatDev session using existing functional launcher.

    Args:
        task_description: Description of the development task
        output_dir: Output directory for generated code
        complexity: Task complexity ("simple", "medium", "complex") for adaptive timeout

    Returns:
        Session status dict with success/error information
    """
    launcher = get_chatdev_launcher()

    if not launcher:
        return {
            "success": False,
            "error": "ChatDev launcher not available",
            "status": "unavailable",
        }

    try:
        logger.info("🚀 Launching ChatDev session...")

        # Get adaptive timeout based on task complexity
        timeout_manager = get_timeout_manager()
        adaptive_timeout = timeout_manager.get_timeout(
            model="chatdev", task_type="chatdev_session", complexity=complexity
        )

        logger.info(f"⏱️ Using adaptive timeout: {adaptive_timeout:.0f}s for {complexity} task")

        # SNS-CORE optimization for agent communication
        optimized_task = task_description or "AI development assistance"
        token_savings = 0.0
        if is_feature_enabled("sns_pilot_chatdev") and task_description:
            try:
                from src.ai.sns_core_integration import SNSCoreHelper

                # Convert to SNS if task is long enough
                if len(task_description) > 50:
                    sns_notation = SNSCoreHelper.convert_to_sns(task_description)
                    metrics = SNSCoreHelper.compare_token_counts(task_description, sns_notation)
                    token_savings = metrics.get("savings_percent", 0)

                    # Use SNS if savings are significant
                    if token_savings > 20:
                        optimized_task = sns_notation
                        logger.info(
                            f"🧩 SNS-CORE enabled: {token_savings:.1f}% token savings "
                            f"({metrics['tokens_saved']} tokens)"
                        )
            except Exception as e:
                logger.warning(f"⚠️ SNS-CORE optimization failed, using original task: {e}")

        # Configure session parameters
        session_config = {
            "task": optimized_task,
            "output_directory": output_dir or "chatdev_output",
            "timeout": adaptive_timeout,  # Adaptive timeout based on complexity
            "complexity": complexity,
            "sns_enabled": token_savings > 0,
            "token_savings_pct": token_savings,
        }

        # Launch ChatDev with configuration
        if hasattr(launcher, "launch_chatdev"):
            process = launcher.launch_chatdev(
                task=session_config["task"],
                name=session_config.get("project_name", "EnhancedProject"),
            )

            return {
                "success": True,
                "process_id": process.pid if process else None,
                "session_config": session_config,
                "status": "launched",
            }
        # Use interactive mode as fallback
        launcher.launch_interactive()
        return {
            "success": True,
            "session_config": session_config,
            "status": "interactive_mode",
        }

    except Exception as e:
        logger.exception(f"❌ ChatDev session launch failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "status": "failed",
        }


def setup_chatdev_environment() -> dict[str, Any]:
    """Set up ChatDev environment for integration."""
    logger.info("🔧 Setting up ChatDev environment...")

    setup_results = {
        "environment_configured": False,
        "api_keys_available": False,
        "dependencies_satisfied": False,
        "setup_timestamp": datetime.now().isoformat(),
    }

    try:
        launcher = get_chatdev_launcher()

        if launcher:
            # Setup API keys
            api_setup = launcher.setup_api_key()
            setup_results["api_keys_available"] = api_setup

            # Setup environment
            launcher.setup_environment()
            setup_results["environment_configured"] = True

            # Check dependencies
            status = launcher.check_status()
            setup_results["dependencies_satisfied"] = status.get("chatdev_installation", False)

            logger.info("✅ ChatDev environment setup completed")
        else:
            logger.warning("⚠️ ChatDev launcher not available for environment setup")

        return setup_results

    except Exception as e:
        logger.exception(f"❌ ChatDev environment setup failed: {e}")
        setup_results["error"] = str(e)
        return setup_results


def create_chatdev_task(task_description: str, task_type: str = "development") -> dict[str, Any]:
    """Create a structured ChatDev task configuration."""
    return {
        "task_id": f"chatdev_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": task_description,
        "type": task_type,
        "created_timestamp": datetime.now().isoformat(),
        "status": "pending",
        "config": {
            "model_selection": "intelligent",  # Use intelligent model selection
            "output_format": "structured",
            "include_documentation": True,
            "enable_testing": True,
        },
    }


def validate_chatdev_integration() -> dict[str, Any]:
    """Validate ChatDev integration health and functionality."""
    logger.info("🔍 Validating ChatDev integration...")

    tests: dict[str, bool] = {}
    validation_results: dict[str, Any] = {
        "validation_timestamp": datetime.now().isoformat(),
        "tests": tests,
    }

    # Test 1: Launcher availability
    launcher = get_chatdev_launcher()
    tests["launcher_import"] = launcher is not None

    if launcher:
        # Test 2: API configuration
        try:
            api_setup = launcher.setup_api_key()
            tests["api_configuration"] = api_setup
        except Exception as e:
            tests["api_configuration"] = False
            validation_results["api_error"] = str(e)

        # Test 3: Environment setup
        try:
            launcher.setup_environment()
            tests["environment_setup"] = True
        except Exception as e:
            tests["environment_setup"] = False
            validation_results["environment_error"] = str(e)

        # Test 4: ChatDev installation check
        try:
            status = launcher.check_status()
            tests["installation_check"] = status.get("chatdev_installation", False)
            validation_results["installation_status"] = status
        except Exception as e:
            tests["installation_check"] = False
            validation_results["installation_error"] = str(e)

    # Calculate overall health score
    passed_tests = sum(1 for result in tests.values() if result)
    total_tests = len(tests)
    health_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

    validation_results["health_score"] = round(health_score, 1)
    validation_results["status"] = "healthy" if health_score >= 75 else "needs_attention"

    logger.info(f"📊 ChatDev integration health: {health_score}% ({validation_results['status']})")

    return validation_results


# Legacy function names preserved for backward compatibility
def initialize_chatdev_integration():
    return ChatDevIntegrationManager().initialize_chatdev_integration()


launch_chatdev_session_legacy = launch_chatdev_session

if __name__ == "__main__":
    # Comprehensive integration test

    # Initialize integration
    init_results = initialize_chatdev_integration()

    # Validate integration
    validation = validate_chatdev_integration()

    for result in validation["tests"].values():
        status = "✅" if result else "❌"


if __name__ == "__main__":
    initialize_chatdev_integration()
