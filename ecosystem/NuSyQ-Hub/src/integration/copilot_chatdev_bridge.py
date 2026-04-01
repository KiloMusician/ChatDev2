#!/usr/bin/env python3
"""🤖 Copilot-ChatDev Agent Bridge.

Advanced AI collaboration system for agent-assisted development.

This module provides a bridge between GitHub Copilot and ChatDev to enable:
- Multi-agent code review and enhancement
- Collaborative problem solving between AI systems
- Agent-assisted refactoring and optimization
- Intelligent code generation workflows

OmniTag: {
    "purpose": "copilot_chatdev_agent_bridge",
    "type": "ai_collaboration_system",
    "evolution_stage": "v1.0_functional"
}
MegaTag: {
    "scope": "multi_ai_orchestration",
    "integration_level": "copilot_chatdev_bridge",
    "quantum_context": "agent_collaboration"
}
"""

import contextlib
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Initialize imports with None defaults
MazeRepoScanner = None
run_and_capture = None

# Robust import for MazeRepoScanner: support package-relative and workspace imports
with contextlib.suppress(ImportError, ModuleNotFoundError):
    from src.tools.maze_solver import MazeRepoScanner  # type: ignore

# Attempt to import the streaming runner
with contextlib.suppress(ImportError, ModuleNotFoundError):
    from src.tools.run_and_capture import run_and_capture  # type: ignore

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Repository root for relative paths
REPO_ROOT = Path(__file__).resolve().parents[2]


def _draft_patch(issue: dict[str, Any]) -> Path:
    """Create a patch file for the given issue report."""
    patches_dir = REPO_ROOT / "incoming" / "patches"
    patches_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    patch_name = f"{issue.get('id', 'patch')}_{timestamp}.diff"
    patch_path = patches_dir / patch_name
    patch_content = issue.get("patch", "")
    patch_path.write_text(patch_content, encoding="utf-8")
    return patch_path


def review_and_apply_patch(patch_path: Path, auto_confirm: bool = False) -> bool:
    """Display a patch and apply it if confirmed."""
    with open(patch_path, encoding="utf-8") as f:
        f.read()
    if auto_confirm or input("Apply patch? [y/N]: ").strip().lower().startswith("y"):
        subprocess.run(["git", "apply", str(patch_path)], check=True)
        return True
    return False


TASK_ROUTER = {
    "fix": _draft_patch,
}


class CopilotChatDevBridge:
    """Bridge for Copilot-ChatDev agent collaboration."""

    def __init__(self, workspace_root: str = ".") -> None:
        """Initialize CopilotChatDevBridge with workspace_root."""
        self.workspace_root = Path(workspace_root)
        self.active_sessions: dict[str, Any] = {}
        self.collaboration_history: list[dict[str, Any]] = []

        # Initialize agent capabilities
        self.copilot_capabilities = {
            "code_completion": True,
            "context_awareness": True,
            "real_time_suggestions": True,
            "workspace_integration": True,
        }

        self.chatdev_capabilities = {
            "multi_agent_development": True,
            "role_based_collaboration": True,
            "project_generation": True,
            "systematic_development": True,
        }

        logger.info("🤖 Copilot-ChatDev Agent Bridge initialized")

    def create_agent_collaboration_session(
        self, task_description: str, collaboration_mode: str = "enhanced"
    ) -> dict[str, Any]:
        """Create a new agent collaboration session."""
        session_id = f"collab_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        session = {
            "id": session_id,
            "task": task_description,
            "mode": collaboration_mode,
            "created": datetime.now().isoformat(),
            "status": "initialized",
            "agents": {
                "copilot": {"active": True, "role": "real_time_assistant"},
                "chatdev": {"active": False, "role": "multi_agent_orchestrator"},
            },
            "collaboration_log": [],
        }

        self.active_sessions[session_id] = session
        logger.info(f"🆕 Created collaboration session: {session_id}")

        return session

    def request_chatdev_assistance(
        self, session_id: str, code_context: str, assistance_type: str = "review"
    ) -> dict[str, Any]:
        """Request ChatDev assistance for current Copilot context."""
        if session_id not in self.active_sessions:
            return {"error": "Session not found", "success": False}

        session = self.active_sessions[session_id]

        # Prepare ChatDev task based on assistance type
        chatdev_tasks = {
            "review": f"Code Review: Analyze and provide feedback on this code:\n{code_context}",
            "refactor": f"Code Refactoring: Suggest improvements for this code:\n{code_context}",
            "enhance": f"Code Enhancement: Add features or optimize this code:\n{code_context}",
            "debug": f"Code Debugging: Find and fix issues in this code:\n{code_context}",
            "document": f"Code Documentation: Generate documentation for this code:\n{code_context}",
            "test": f"Test Generation: Create comprehensive tests for this code:\n{code_context}",
        }

        task = chatdev_tasks.get(assistance_type, chatdev_tasks["review"])

        # Log the collaboration request
        collaboration_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "chatdev_request",
            "assistance_type": assistance_type,
            "context_length": len(code_context),
            "task": task[:100] + "..." if len(task) > 100 else task,
        }

        session["collaboration_log"].append(collaboration_entry)
        session["agents"]["chatdev"]["active"] = True

        logger.info(f"🔄 Requested ChatDev {assistance_type} assistance for session {session_id}")

        return {
            "success": True,
            "session_id": session_id,
            "task": task,
            "assistance_type": assistance_type,
            "next_action": "launch_chatdev_with_task",
        }

    def handle_chatdev_issue(
        self, issue_report: dict[str, Any], auto_apply: bool = False
    ) -> dict[str, Any]:
        """Route ChatDev issue reports to the fix handler."""
        handler = TASK_ROUTER.get("fix")
        if handler is None:
            return {"success": False, "error": "No fix handler available"}

        patch_path = handler(issue_report)
        applied = False
        if auto_apply:
            applied = review_and_apply_patch(patch_path, auto_confirm=True)

        return {"success": True, "patch_path": str(patch_path), "applied": applied}

    def generate_copilot_context_for_chatdev(self, file_paths: list[str]) -> dict[str, Any]:
        """Generate rich context from Copilot workspace for ChatDev."""
        context = {
            "workspace_root": str(self.workspace_root),
            "timestamp": datetime.now().isoformat(),
            "files_analyzed": [],
            "project_structure": {},
            "code_patterns": {},
            "dependencies": [],
            "architecture_insights": [],
        }

        # Analyze provided files
        for file_path in file_paths:
            full_path = self.workspace_root / file_path

            if full_path.exists():
                try:
                    with open(full_path, encoding="utf-8") as f:
                        content = f.read()

                    file_info = {
                        "path": file_path,
                        "size": len(content),
                        "lines": len(content.splitlines()),
                        "language": self._detect_language(file_path),
                        "imports": self._extract_imports(content),
                        "functions": self._extract_functions(content),
                        "classes": self._extract_classes(content),
                    }

                    context["files_analyzed"].append(file_info)

                except Exception as e:
                    logger.warning(f"⚠️ Could not analyze {file_path}: {e}")

        # Generate project insights
        context["architecture_insights"] = self._generate_architecture_insights(
            context["files_analyzed"]
        )

        logger.info(f"📊 Generated context for {len(context['files_analyzed'])} files")

        return context

    def create_agent_workflow(self, workflow_type: str, target_files: list[str]) -> dict[str, Any]:
        """Create a collaborative workflow between Copilot and ChatDev."""
        workflows = {
            "code_review": {
                "steps": [
                    "copilot_initial_analysis",
                    "chatdev_team_review",
                    "copilot_integration_suggestions",
                    "chatdev_implementation_plan",
                ],
                "description": "Comprehensive code review with multiple AI perspectives",
            },
            "feature_development": {
                "steps": [
                    "copilot_context_analysis",
                    "chatdev_team_planning",
                    "copilot_incremental_development",
                    "chatdev_integration_testing",
                ],
                "description": "Collaborative feature development",
            },
            "refactoring": {
                "steps": [
                    "copilot_pattern_analysis",
                    "chatdev_refactoring_strategy",
                    "copilot_incremental_changes",
                    "chatdev_quality_assurance",
                ],
                "description": "Systematic code refactoring",
            },
            "debugging": {
                "steps": [
                    "copilot_error_identification",
                    "chatdev_root_cause_analysis",
                    "copilot_targeted_fixes",
                    "chatdev_comprehensive_testing",
                ],
                "description": "Multi-agent debugging approach",
            },
        }

        if workflow_type not in workflows:
            workflow_type = "code_review"

        workflow = workflows[workflow_type].copy()
        workflow.update(
            {
                "id": f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "type": workflow_type,
                "target_files": target_files,
                "created": datetime.now().isoformat(),
                "status": "ready",
                "current_step": 0,
                "context": self.generate_copilot_context_for_chatdev(target_files),
            }
        )

        logger.info(f"🔄 Created {workflow_type} workflow for {len(target_files)} files")

        return workflow

    def scan_repository_for_treasures(
        self, root: str | None = None, max_depth: int = 20
    ) -> dict[str, list[tuple[int, str]]]:
        """Run the repository "maze" scanner to discover technical-debt "treasures".

        such as TODO/TODO/BUG markers. Returns the findings mapping file->list.
        """
        if MazeRepoScanner is None:
            logger.warning(
                "⚠️ MazeRepoScanner not available — install or fix imports to enable repository scanning"
            )
            return {}

        root_path = Path(root) if root is not None else self.workspace_root
        scanner = MazeRepoScanner(root_path)
        findings = scanner.scan(max_depth=max_depth)
        logger.info(
            f"🧭 Repository scan complete: {sum(len(v) for v in findings.values())} findings in {len(findings)} files"
        )
        return findings

        def run_scanner_and_capture(
            self,
            root: str | None = None,
            max_depth: int = 20,
            log_dir: Path | None = None,
        ) -> dict[str, Any]:
            """Run the maze scanner as a subprocess and capture full stdout/stderr into a.

            timestamped log file. Also attempt to parse findings by importing the
            MazeRepoScanner directly (fast path). Returns a dict with keys:
              - log_path: path to the captured output file
              - findings: parsed findings mapping (may be empty if parsing failed).

            This is useful when command outputs are large — the full trace is kept
            in `log_path` for inspection and for Copilot/ChatDev to consume.
            """
            root_path = str(root) if root is not None else str(self.workspace_root)
            if log_dir is None:
                log_dir = REPO_ROOT / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = log_dir / f"maze_scan_{timestamp}.log"

            # Build command using current Python executable for reliable environment
            cmd = [
                sys.executable,
                "-m",
                "src.tools.maze_solver",
                root_path,
                "--max-depth",
                str(max_depth),
            ]

            logger.info(f"🔎 Running scanner command: {' '.join(cmd)} -> {log_path}")
            # Run and capture output robustly
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=str(self.workspace_root),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                out = proc.stdout or ""
                err = proc.stderr or ""
                with open(log_path, "w", encoding="utf-8") as fh:
                    fh.write(f"# Command: {' '.join(cmd)}\n# Return code: {proc.returncode}\n\n")
                    fh.write(out)
                    if err:
                        fh.write("\n\n# STDERR:\n")
                        fh.write(err)
            except Exception as e:
                logger.exception("Failed to run scanner subprocess")
                with open(log_path, "w", encoding="utf-8") as fh:
                    fh.write(f"# Subprocess failure: {e}\n")

            # Try fast-path parsing by using the MazeRepoScanner directly when available
            parsed: dict[str, Any] = {}
            try:
                if MazeRepoScanner is not None:
                    scanner = MazeRepoScanner(Path(root_path))
                    parsed = scanner.scan(max_depth=max_depth)
            except (OSError, AttributeError, RuntimeError):
                # fall back to parsing the log if needed (not implemented here)
                parsed: dict[str, Any] = {}
            # If no parsed findings and we have a streaming runner, attempt to run and capture for full visibility
            if not parsed and run_and_capture is not None:
                try:
                    cmd = [
                        sys.executable,
                        "-m",
                        "src.tools.maze_solver",
                        root_path,
                        "--max-depth",
                        str(max_depth),
                    ]
                    log_path = run_and_capture(
                        cmd, cwd=self.workspace_root, log_dir=REPO_ROOT / "logs"
                    )
                    logger.info(f"Captured scanner output to {log_path}")
                except (OSError, subprocess.SubprocessError):
                    logger.debug("run_and_capture failed or not available")

            # Attempt to locate a machine-readable summary written by the scanner
            summary_path = None
            try:
                from src.tools.log_indexer import latest_maze_summaries

                latest = latest_maze_summaries(REPO_ROOT / "logs", limit=1)
                if latest:
                    summary_path = str(latest[0])
            except (ImportError, ModuleNotFoundError, OSError, IndexError):
                summary_path = None

            return {
                "log_path": str(log_path),
                "findings": parsed,
                "summary_path": summary_path,
            }

        return None

    def create_workflow_from_treasures(
        self, findings: dict[Path, list[tuple[int, str]]]
    ) -> dict[str, Any]:
        """Create a 'tech_debt_cleanup' workflow from findings. The workflow's.

        target_files are the files that contain treasures.
        """
        target_files = [
            (
                str(p.relative_to(self.workspace_root))
                if p.is_relative_to(self.workspace_root)
                else str(p)
            )
            for p in findings
        ]
        workflow = self.create_agent_workflow("refactoring", target_files)
        # Attach findings summary to workflow context for agent use
        workflow.setdefault("context", {})
        workflow["context"]["treasures"] = {str(p): hits for p, hits in findings.items()}
        logger.info(f"🛠 Created tech-debt workflow for {len(target_files)} files")
        return workflow

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()

        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby",
            ".cs": "csharp",
            ".ps1": "powershell",
            ".sh": "bash",
            ".md": "markdown",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
        }

        return language_map.get(ext, "unknown")

    def _extract_imports(self, content: str) -> list[str]:
        """Extract import statements from code."""
        imports: list[Any] = []
        lines = content.splitlines()

        for line in lines:
            line = line.strip()
            if line.startswith(("import ", "from ", "#include ", "using ", "require(")):
                imports.append(line)

        return imports[:10]  # Limit to first 10 imports

    def _extract_functions(self, content: str) -> list[str]:
        """Extract function definitions from code."""
        functions: list[Any] = []
        lines = content.splitlines()

        for line in lines:
            line = line.strip()
            if any(pattern in line for pattern in ["def ", "function ", "async def ", "function*"]):
                # Extract function name
                if "def " in line:
                    func_name = line.split("def ")[1].split("(")[0].strip()
                elif "function " in line:
                    func_name = line.split("function ")[1].split("(")[0].strip()
                else:
                    func_name = line

                functions.append(func_name)

        return functions[:20]  # Limit to first 20 functions

    def _extract_classes(self, content: str) -> list[str]:
        """Extract class definitions from code."""
        classes: list[Any] = []
        lines = content.splitlines()

        for line in lines:
            line = line.strip()
            if line.startswith("class "):
                class_name = line.split("class ")[1].split("(")[0].split(":")[0].strip()
                classes.append(class_name)

        return classes[:10]  # Limit to first 10 classes

    def _generate_architecture_insights(self, files_analyzed: list[dict]) -> list[str]:
        """Generate architecture insights from analyzed files."""
        insights: list[Any] = []
        total_files = len(files_analyzed)
        total_lines = sum(f.get("lines", 0) for f in files_analyzed)
        languages = {f.get("language", "unknown") for f in files_analyzed}

        insights.append(f"Project contains {total_files} files with {total_lines} total lines")
        insights.append(f"Primary languages: {', '.join(languages)}")

        # Function analysis
        total_functions = sum(len(f.get("functions", [])) for f in files_analyzed)
        if total_functions > 0:
            insights.append(f"Contains {total_functions} functions across all files")

        # Class analysis
        total_classes = sum(len(f.get("classes", [])) for f in files_analyzed)
        if total_classes > 0:
            insights.append(f"Contains {total_classes} classes indicating object-oriented design")

        # Import analysis
        all_imports: list[Any] = []
        for f in files_analyzed:
            all_imports.extend(f.get("imports", []))

        if all_imports:
            insights.append(f"Uses {len(set(all_imports))} unique imports/dependencies")

        return insights

    def launch_collaborative_session(self, workflow: dict[str, Any]) -> dict[str, Any]:
        """Launch a collaborative session between Copilot and ChatDev."""
        logger.info(f"🚀 Launching collaborative session: {workflow['type']}")

        # Generate ChatDev task description
        task_description = self._generate_chatdev_task_from_workflow(workflow)

        # Create session configuration
        session_config = {
            "workflow_id": workflow["id"],
            "task_description": task_description,
            "target_files": workflow["target_files"],
            "context": workflow["context"],
            "collaboration_mode": "active",
            "expected_outputs": self._get_expected_outputs_for_workflow(workflow["type"]),
        }

        logger.info(f"📋 Collaborative session configured for {workflow['type']}")

        return {
            "success": True,
            "session_config": session_config,
            "next_steps": [
                "Launch ChatDev with generated task",
                "Monitor Copilot integration",
                "Coordinate agent outputs",
                "Merge collaborative results",
            ],
            "chatdev_task": task_description,
        }

    def _generate_chatdev_task_from_workflow(self, workflow: dict[str, Any]) -> str:
        """Generate ChatDev task description from workflow."""
        context = workflow["context"]
        files_info = "\n".join(
            [
                f"- {f['path']} ({f['language']}, {f['lines']} lines)"
                for f in context["files_analyzed"]
            ]
        )

        architecture_info = "\n".join(
            [f"- {insight}" for insight in context["architecture_insights"]]
        )

        task_templates = {
            "code_review": f"""
Code Review and Analysis Task

Project Context:
{architecture_info}

Files to Review:
{files_info}

Please perform a comprehensive code review including:
1. Code quality assessment
2. Best practice recommendations
3. Security vulnerability analysis
4. Performance optimization suggestions
5. Documentation improvement recommendations

Focus on collaborative enhancement that complements GitHub Copilot's real-time assistance.
""",
            "feature_development": f"""
Feature Development Task

Project Context:
{architecture_info}

Target Files:
{files_info}

Please develop new features with:
1. Architectural planning
2. Implementation strategy
3. Testing approach
4. Integration considerations
5. Documentation requirements

Coordinate with GitHub Copilot for incremental development.
""",
            "refactoring": f"""
Code Refactoring Task

Project Context:
{architecture_info}

Files to Refactor:
{files_info}

Please provide refactoring recommendations:
1. Code structure improvements
2. Design pattern implementations
3. Performance optimizations
4. Maintainability enhancements
5. Test coverage improvements

Work collaboratively with GitHub Copilot for implementation.
""",
            "debugging": f"""
Debugging and Problem Resolution Task

Project Context:
{architecture_info}

Files with Issues:
{files_info}

Please analyze and resolve:
1. Error identification and root cause analysis
2. Bug fixing strategies
3. Prevention mechanisms
4. Testing improvements
5. Monitoring recommendations

Collaborate with GitHub Copilot for targeted fixes.
""",
        }

        return task_templates.get(workflow["type"], task_templates["code_review"])

    def _get_expected_outputs_for_workflow(self, workflow_type: str) -> list[str]:
        """Get expected outputs for workflow type."""
        outputs = {
            "code_review": [
                "Code quality assessment report",
                "Security analysis findings",
                "Performance recommendations",
                "Refactoring suggestions",
                "Documentation improvements",
            ],
            "feature_development": [
                "Feature implementation plan",
                "Code architecture design",
                "Test strategy and cases",
                "Integration documentation",
                "Deployment guidelines",
            ],
            "refactoring": [
                "Refactoring strategy document",
                "Code structure improvements",
                "Design pattern recommendations",
                "Performance optimization plan",
                "Migration guide",
            ],
            "debugging": [
                "Error analysis report",
                "Bug fix implementations",
                "Prevention strategy",
                "Improved error handling",
                "Monitoring enhancements",
            ],
        }

        return outputs.get(workflow_type, outputs["code_review"])


# CLI Interface for Copilot-ChatDev Bridge
def main() -> None:
    """Main CLI interface for Copilot-ChatDev Agent Bridge."""
    bridge = CopilotChatDevBridge()

    # Example: Create a code review workflow
    target_files = [
        "src/integration/chatdev_integration.py",
        "src/core/main.py",
    ]

    workflow = bridge.create_agent_workflow("code_review", target_files)

    # Launch collaborative session
    session = bridge.launch_collaborative_session(workflow)

    if session["success"]:
        for _i, _step in enumerate(session["next_steps"], 1):
            pass


if __name__ == "__main__":
    main()
