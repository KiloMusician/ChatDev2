#!/usr/bin/env python3
"""🚀 Enhanced Copilot-ChatDev Agent Launcher
Integration with existing NuSyQ-Hub infrastructure

This launcher integrates with:
- Existing ChatDev integration systems
- AI Coordinator with multi-provider routing
- Ollama local models
- Copilot-ChatDev Bridge
- Enhanced collaboration workflows

OmniTag: {
    "purpose": "enhanced_agent_launcher",
    "type": "integration_cli",
    "evolution_stage": "v2.0_infrastructure_integrated"
}
"""

import argparse
import asyncio
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Enhanced integration imports
TaskType = None
AIProvider = None
Priority = None
TaskRequest = None

try:
    # Import existing infrastructure
    sys.path.insert(0, str(project_root / "src" / "integration"))
    from chatdev_integration import ChatDevIntegrationManager

    CHATDEV_INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ ChatDev integration not available: {e}")
    CHATDEV_INTEGRATION_AVAILABLE = False

try:
    # Import AI Coordinator from KILO-FOOLISH
    kilo_path = project_root.parent / "Documents" / "GitHub" / "KILO-FOOLISH" / "src" / "ai"
    sys.path.insert(0, str(kilo_path))
    from ai_coordinator import AICoordinator, AIProvider, Priority, TaskRequest, TaskType

    AI_COORDINATOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ AI Coordinator not available: {e}")
    AI_COORDINATOR_AVAILABLE = False
    # Create dummy enums for type hints
    from enum import Enum

    class TaskType(Enum):
        CODE_REVIEW = "code_review"
        REFACTORING = "refactoring"
        CODE_GENERATION = "code_generation"
        DEBUGGING = "debugging"
        TESTING = "testing"
        DOCUMENTATION = "documentation"

    class AIProvider(Enum):
        AUTO = "auto"
        COPILOT = "copilot"
        OLLAMA = "ollama"
        OPENAI = "openai"

    class Priority(Enum):
        LOW = 1
        MEDIUM = 2
        HIGH = 3
        CRITICAL = 4


try:
    # Import Ollama configuration
    ollama_path = project_root.parent / "Documents" / "GitHub" / "KILO-FOOLISH" / "src"
    sys.path.insert(0, str(ollama_path))
    from LocalLLMConfigurationChatDevOllama import OllamaConfig

    OLLAMA_CONFIG_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Ollama configuration not available: {e}")
    OLLAMA_CONFIG_AVAILABLE = False

try:
    # Import Bridge directly
    from copilot_chatdev_bridge import CopilotChatDevBridge

    BRIDGE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Bridge not available: {e}")
    BRIDGE_AVAILABLE = False


class EnhancedAgentLauncher:
    """Enhanced launcher that integrates all existing infrastructure"""

    def __init__(self):
        self.workspace_root = project_root

        # Initialize infrastructure components
        self.chatdev_integration = None
        self.ai_coordinator = None
        self.ollama_config = None
        self.copilot_bridge = None

        self._initialize_components()

    def _initialize_components(self):
        """Initialize all available infrastructure components"""
        print("🔧 Initializing infrastructure components...")

        # Initialize ChatDev integration
        if CHATDEV_INTEGRATION_AVAILABLE:
            try:
                self.chatdev_integration = ChatDevIntegrationManager()
                status = self.chatdev_integration.initialize_chatdev_integration()
                print(f"✅ ChatDev integration: {status.get('status', 'unknown')}")
            except Exception as e:
                print(f"⚠️ ChatDev integration failed: {e}")

        # Initialize AI Coordinator
        if AI_COORDINATOR_AVAILABLE:
            try:
                self.ai_coordinator = AICoordinator()
                print("✅ AI Coordinator initialized")
            except Exception as e:
                print(f"⚠️ AI Coordinator failed: {e}")

        # Initialize Ollama configuration
        if OLLAMA_CONFIG_AVAILABLE:
            try:
                self.ollama_config = OllamaConfig()
                print("✅ Ollama configuration loaded")
            except Exception as e:
                print(f"⚠️ Ollama configuration failed: {e}")

        # Initialize Copilot Bridge
        if BRIDGE_AVAILABLE:
            try:
                self.copilot_bridge = CopilotChatDevBridge(workspace_root=str(self.workspace_root))
                print("✅ Copilot-ChatDev Bridge initialized")
            except Exception as e:
                print(f"⚠️ Bridge initialization failed: {e}")

    async def launch_collaboration(
        self, action: str, target_files: List[str], urgent: bool = False, workflow_type: str = None
    ) -> Dict[str, Any]:
        """Launch collaboration using the best available infrastructure"""
        print(f"🚀 Launching {action} collaboration...")

        # Determine workflow type
        if not workflow_type:
            workflow_type = self._map_action_to_workflow(action)

        # Try enhanced collaboration first (ChatDev + AI Coordinator + Bridge)
        if self.chatdev_integration and self.chatdev_integration.bridge_available:
            print("🤖 Using enhanced Copilot-ChatDev collaboration")
            return await self._launch_enhanced_collaboration(
                action, target_files, workflow_type, urgent
            )

        # Try AI Coordinator with ChatDev processing
        elif self.ai_coordinator:
            print("🎼 Using AI Coordinator for multi-provider collaboration")
            return await self._launch_ai_coordinator_collaboration(
                action, target_files, workflow_type, urgent
            )

        # Try direct ChatDev integration
        elif self.chatdev_integration:
            print("🔄 Using traditional ChatDev integration")
            return await self._launch_chatdev_collaboration(action, target_files, urgent)

        # Try direct bridge collaboration
        elif self.copilot_bridge:
            print("🌉 Using Copilot-ChatDev Bridge")
            return await self._launch_bridge_collaboration(action, target_files, workflow_type)

        # Fallback to simple analysis
        else:
            print("📋 Using fallback analysis mode")
            return self._launch_fallback_analysis(action, target_files)

    async def _launch_enhanced_collaboration(
        self, action: str, target_files: List[str], workflow_type: str, urgent: bool
    ) -> Dict[str, Any]:
        """Launch using enhanced ChatDev integration with bridge"""
        try:
            task_description = f"{action.title()} collaboration for {len(target_files)} files"
            if urgent:
                task_description += " (URGENT)"

            result = self.chatdev_integration.launch_enhanced_collaboration(
                task_description=task_description,
                target_files=target_files,
                workflow_type=workflow_type,
            )

            return {
                "success": True,
                "method": "enhanced_collaboration",
                "result": result,
                "infrastructure": "ChatDev + Bridge + AI Coordinator",
            }

        except Exception as e:
            print(f"❌ Enhanced collaboration failed: {e}")
            return {"success": False, "error": str(e)}

    async def _launch_ai_coordinator_collaboration(
        self, action: str, target_files: List[str], workflow_type: str, urgent: bool
    ) -> Dict[str, Any]:
        """Launch using AI Coordinator for multi-provider processing"""
        try:
            # Create task request
            task_type = self._map_action_to_task_type(action)
            priority = Priority.CRITICAL if urgent else Priority.HIGH

            task_request = TaskRequest(
                task_type=task_type,
                content=f"{action.title()} the following files: {', '.join(target_files)}",
                context={
                    "target_files": target_files,
                    "workflow_type": workflow_type,
                    "chatdev_task": True,  # Trigger ChatDev processing
                    "action": action,
                },
                priority=priority,
                preferred_provider=AIProvider.AUTO,
            )

            # Process using enhanced ChatDev processing
            response = await self.ai_coordinator.process_enhanced_chatdev_task(task_request)

            return {
                "success": True,
                "method": "ai_coordinator",
                "response": response,
                "infrastructure": "AI Coordinator + Multi-provider routing",
            }

        except Exception as e:
            print(f"❌ AI Coordinator collaboration failed: {e}")
            return {"success": False, "error": str(e)}

    async def _launch_chatdev_collaboration(
        self, action: str, target_files: List[str], urgent: bool
    ) -> Dict[str, Any]:
        """Launch using traditional ChatDev integration"""
        try:
            task_description = f"{action.title()} collaboration for: {', '.join(target_files)}"
            if urgent:
                task_description += " (HIGH PRIORITY)"

            # Use the traditional launcher
            from chatdev_integration import launch_chatdev_session

            result = launch_chatdev_session(task_description)

            return {
                "success": True,
                "method": "traditional_chatdev",
                "result": result,
                "infrastructure": "ChatDev traditional launcher",
            }

        except Exception as e:
            print(f"❌ ChatDev collaboration failed: {e}")
            return {"success": False, "error": str(e)}

    async def _launch_bridge_collaboration(
        self, action: str, target_files: List[str], workflow_type: str
    ) -> Dict[str, Any]:
        """Launch using direct Copilot-ChatDev Bridge"""
        try:
            # Create workflow
            workflow = self.copilot_bridge.create_agent_workflow(workflow_type, target_files)

            # Launch session
            session = self.copilot_bridge.launch_collaborative_session(workflow)

            return {
                "success": True,
                "method": "direct_bridge",
                "workflow": workflow,
                "session": session,
                "infrastructure": "Copilot-ChatDev Bridge",
            }

        except Exception as e:
            print(f"❌ Bridge collaboration failed: {e}")
            return {"success": False, "error": str(e)}

    def _launch_fallback_analysis(self, action: str, target_files: List[str]) -> Dict[str, Any]:
        """Fallback analysis when no infrastructure is available"""
        print("📋 Performing fallback analysis...")

        analysis = {
            "action": action,
            "target_files": target_files,
            "file_count": len(target_files),
            "timestamp": datetime.now().isoformat(),
            "recommendations": [
                "Install ChatDev integration for enhanced collaboration",
                "Set up Ollama for local AI processing",
                "Configure AI Coordinator for multi-provider routing",
                "Use GitHub Copilot for real-time assistance",
            ],
        }

        return {
            "success": True,
            "method": "fallback_analysis",
            "analysis": analysis,
            "infrastructure": "Basic analysis (no AI infrastructure)",
        }

    def _map_action_to_workflow(self, action: str) -> str:
        """Map action to workflow type"""
        mapping = {
            "review": "code_review",
            "refactor": "refactoring",
            "enhance": "feature_development",
            "debug": "debugging",
            "test": "code_review",
            "document": "code_review",
        }
        return mapping.get(action, "code_review")

    def _map_action_to_task_type(self, action: str) -> TaskType:
        """Map action to AI Coordinator task type"""
        mapping = {
            "review": TaskType.CODE_REVIEW,
            "refactor": TaskType.REFACTORING,
            "enhance": TaskType.CODE_GENERATION,
            "debug": TaskType.DEBUGGING,
            "test": TaskType.TESTING,
            "document": TaskType.DOCUMENTATION,
        }
        return mapping.get(action, TaskType.CODE_REVIEW)

    def get_changed_files(self) -> List[str]:
        """Get changed files from git"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.workspace_root,
            )
            if result.returncode == 0:
                return [f for f in result.stdout.strip().split("\n") if f.strip()]
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            pass
        return []

    def get_infrastructure_status(self) -> Dict[str, bool]:
        """Get status of all infrastructure components"""
        return {
            "chatdev_integration": self.chatdev_integration is not None,
            "chatdev_bridge_available": (
                self.chatdev_integration and self.chatdev_integration.bridge_available
                if self.chatdev_integration
                else False
            ),
            "ai_coordinator": self.ai_coordinator is not None,
            "ollama_config": self.ollama_config is not None,
            "copilot_bridge": self.copilot_bridge is not None,
        }


async def main():
    """Enhanced main function with infrastructure integration"""
    parser = argparse.ArgumentParser(
        description="🤖 Enhanced Copilot-ChatDev Agent Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Enhanced Integration Examples:
  %(prog)s review src/module.py                    # Review using best available infrastructure
  %(prog)s refactor --all-changed --urgent         # Urgent refactoring with priority routing
  %(prog)s enhance src/integration/*.py            # Feature enhancement with bridge
  %(prog)s debug src/problematic.py --ai-orchestration  # Debug with AI Coordinator
        """,
    )

    parser.add_argument(
        "action",
        choices=["review", "refactor", "enhance", "debug", "test", "document"],
        help="Agent collaboration action",
    )

    parser.add_argument("files", nargs="*", help="Target files for collaboration")

    parser.add_argument(
        "--all-changed", action="store_true", help="Target all changed files in git"
    )

    parser.add_argument("--urgent", action="store_true", help="High priority processing")

    parser.add_argument(
        "--workflow-type",
        choices=["code_review", "feature_development", "refactoring", "debugging"],
        help="Specific workflow type",
    )

    parser.add_argument(
        "--ai-orchestration", action="store_true", help="Force AI Coordinator routing"
    )

    parser.add_argument("--status", action="store_true", help="Show infrastructure status")

    args = parser.parse_args()

    # Initialize launcher
    print("🚀 Enhanced Copilot-ChatDev Agent Launcher")
    print("=" * 60)

    launcher = EnhancedAgentLauncher()

    # Show status if requested
    if args.status:
        status = launcher.get_infrastructure_status()
        print("📊 Infrastructure Status:")
        for component, available in status.items():
            status_icon = "✅" if available else "❌"
            print(f"   {status_icon} {component.replace('_', ' ').title()}")
        return 0

    # Determine target files
    target_files = []

    if args.all_changed:
        changed_files = launcher.get_changed_files()
        if changed_files:
            target_files.extend(changed_files)
            print(f"📁 Found {len(changed_files)} changed files")
        else:
            print("⚠️ No changed files found in git")

    if args.files:
        target_files.extend(args.files)

    if not target_files:
        print("❌ No target files specified")
        print("💡 Use --all-changed or specify files directly")
        return 1

    # Validate files exist
    valid_files = []
    for file_path in target_files:
        full_path = launcher.workspace_root / file_path
        if full_path.exists():
            valid_files.append(file_path)
        else:
            print(f"⚠️ File not found: {file_path}")

    if not valid_files:
        print("❌ No valid files found")
        return 1

    print(f"🎯 Targeting {len(valid_files)} files for {args.action}")
    if args.urgent:
        print("🔥 URGENT MODE: Priority processing enabled")

    # Launch collaboration
    try:
        result = await launcher.launch_collaboration(
            action=args.action,
            target_files=valid_files,
            urgent=args.urgent,
            workflow_type=args.workflow_type,
        )

        if result["success"]:
            print("\n✅ Collaboration launched successfully!")
            print(f"📋 Method: {result['method']}")
            print(f"🏗️ Infrastructure: {result.get('infrastructure', 'Unknown')}")

            # Show specific results based on method
            if "workflow" in result:
                workflow = result["workflow"]
                print(f"🔄 Workflow ID: {workflow.get('id')}")
                print(
                    f"📊 Files analyzed: {len(workflow.get('context', {}).get('files_analyzed', []))}"
                )

            if "response" in result:
                response = result["response"]
                print(
                    f"🤖 Provider: {response.provider.value if hasattr(response, 'provider') else 'unknown'}"
                )
                print(f"⚡ Execution time: {getattr(response, 'execution_time', 0):.2f}s")
                print(f"📈 Confidence: {getattr(response, 'confidence', 0):.2f}")

            print("\n🚀 Next steps:")
            print("1. Monitor collaboration progress")
            print("2. Use GitHub Copilot for real-time assistance")
            print("3. Review agent outputs when complete")
            print("4. Integrate improvements into codebase")

            return 0
        else:
            print(f"❌ Collaboration failed: {result.get('error')}")
            return 1

    except Exception as e:
        print(f"❌ Launcher error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
