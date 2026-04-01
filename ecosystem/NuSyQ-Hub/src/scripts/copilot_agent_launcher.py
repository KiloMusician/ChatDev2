import logging

logger = logging.getLogger(__name__)

#!/usr/bin/env python3
# pyright: reportMissingImports=false, reportUndefinedVariable=false, reportUnknownMemberType=false
"""🚀 Copilot-ChatDev Agent Launcher

Streamlined launcher for agent-assisted development.

Quick Examples:
  python copilot_agent_launcher.py review src/integration/chatdev_integration.py
  python copilot_agent_launcher.py refactor --all-changed
  python copilot_agent_launcher.py enhance src/core/main.py
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure 'src' directory is in Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
# Determine if the Copilot-ChatDev bridge is available
try:
    from integration.copilot_chatdev_bridge import BRIDGE_AVAILABLE
except ImportError:
    BRIDGE_AVAILABLE = False

# Import the ChatDev integration manager for enhanced collaboration
try:
    from integration.chatdev_integration import ChatDevIntegrationManager
except ImportError:
    ChatDevIntegrationManager = None


def get_target_files(args) -> list[str]:
    """Determine target files based on args: either all changed files or specified list."""
    project_root = Path.cwd()
    src_root = project_root / "src"

    # Start with changed files if requested
    files: list[str] = []
    if getattr(args, "all_changed", False):
        files.extend(get_changed_files(project_root))

    for raw_path in getattr(args, "files", []):
        path = Path(raw_path)

        # Determine if the user supplied a directory component
        has_explicit_dir = path.is_absolute() or "/" in raw_path or "\\" in raw_path

        # Unqualified paths default to the src/ directory
        if not has_explicit_dir:
            src_candidate = src_root / path
            root_candidate = project_root / path

            if root_candidate.exists() and not src_candidate.exists():
                resolved = root_candidate
            else:
                if not src_candidate.exists():
                    pass
                resolved = src_candidate
        else:
            resolved = project_root / path
            if not resolved.exists():
                pass

        try:
            files.append(str(resolved.relative_to(project_root)))
        except ValueError:
            files.append(str(resolved))

    return files


def get_changed_files(project_root: Path) -> list[str]:
    """Get list of changed files from git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        if result.returncode == 0:
            return [f for f in result.stdout.strip().split("\n") if f.strip()]
    except (subprocess.CalledProcessError, UnicodeDecodeError, OSError):
        logger.debug("Suppressed OSError/UnicodeDecodeError/subprocess", exc_info=True)
    return []


def analyze_file(file_path: Path) -> dict[str, Any]:
    """Analyze a file for agent collaboration context."""
    if not file_path.exists():
        return {"error": "File not found"}

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.splitlines()

        # Basic analysis
        return {
            "path": str(file_path),
            "language": get_language(file_path),
            "lines": len(lines),
            "size": len(content),
            "functions": extract_functions(content),
            "classes": extract_classes(content),
            "imports": extract_imports(content),
        }

    except Exception as e:
        return {"error": str(e)}


def get_language(file_path: Path) -> str:
    """Detect programming language from file extension."""
    ext = file_path.suffix.lower()
    languages = {
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
    }
    return languages.get(ext, "unknown")


def extract_functions(content: str) -> list[str]:
    """Extract function names from code."""
    functions: list[Any] = []
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("def ") or "function " in line:
            if "def " in line:
                name = line.split("def ")[1].split("(")[0].strip()
            else:
                name = line.split("function ")[1].split("(")[0].strip()
            functions.append(name)
    return functions[:10]  # Limit results


def extract_classes(content: str) -> list[str]:
    """Extract class names from code."""
    classes: list[Any] = []
    for line in content.splitlines():
        if line.strip().startswith("class "):
            name = line.split("class ")[1].split("(")[0].split(":")[0].strip()
            classes.append(name)
    return classes[:5]  # Limit results


def extract_imports(content: str) -> list[str]:
    """Extract import statements."""
    imports: list[Any] = []
    for line in content.splitlines():
        line = line.strip()
        if line.startswith(("import ", "from ", "#include ", "using ")):
            imports.append(line)
    return imports[:8]  # Limit results


def generate_agent_task(action: str, files_analysis: list[dict[str, Any]]) -> str:
    """Generate ChatDev task description."""
    total_lines = sum(f.get("lines", 0) for f in files_analysis)
    total_functions = sum(len(f.get("functions", [])) for f in files_analysis)
    languages = {f.get("language", "unknown") for f in files_analysis}

    context = f"""
Project Analysis:
- Files: {len(files_analysis)}
- Total lines: {total_lines}
- Languages: {", ".join(languages)}
- Functions: {total_functions}

Files to analyze:
"""
    for analysis in files_analysis:
        context += f"- {analysis['path']} ({analysis['language']}, {analysis['lines']} lines)\n"

    task_templates = {
        "review": f"""Code Review and Quality Analysis Task

{context}

Please perform comprehensive code review:
1. Code quality and best practices assessment
2. Security vulnerability analysis
3. Performance optimization opportunities
4. Maintainability improvements
5. Documentation enhancement suggestions

Focus on actionable recommendations that complement GitHub Copilot.
""",
        "refactor": f"""Code Refactoring Enhancement Task

{context}

Please provide refactoring strategy:
1. Code structure improvements
2. Design pattern opportunities
3. Performance optimizations
4. Readability enhancements
5. Test coverage improvements

Coordinate with GitHub Copilot for implementation.
""",
        "enhance": f"""Feature Enhancement and Development Task

{context}

Please analyze enhancement opportunities:
1. Feature extension possibilities
2. Architecture improvements
3. Integration enhancements
4. User experience optimizations
5. Scalability considerations

Work with GitHub Copilot for incremental development.
""",
        "debug": f"""Debugging and Problem Resolution Task

{context}

Please analyze for issues:
1. Error detection and root cause analysis
2. Bug fixing strategies
3. Error handling improvements
4. Testing enhancements
5. Monitoring recommendations

Collaborate with GitHub Copilot for targeted fixes.
""",
    }

    return task_templates.get(action, task_templates["review"])


def main():
    if not BRIDGE_AVAILABLE:
        # Simple fallback mode
        args = parse_args()
        if isinstance(args, int):
            return args
        target_files = get_target_files(args)
        if not target_files:
            return 1
        action = getattr(args, "action", "")
        return 0
    # Enhanced collaboration mode when bridge is available
    args = parse_args()
    if isinstance(args, int):
        return args
    # Determine target files
    target_files = get_target_files(args)
    if not target_files:
        return 1
    # Analyze files for context
    files_analysis = [analyze_file(Path(f)) for f in target_files]
    # Generate task description
    action = getattr(args, "action", "")
    task_description = generate_agent_task(action, files_analysis)
    # Initialize integration manager
    manager = ChatDevIntegrationManager() if ChatDevIntegrationManager else None
    if manager and getattr(manager, "bridge_available", False):
        # Launch enhanced Copilot-ChatDev collaboration
        manager.launch_enhanced_collaboration(
            task_description,
            target_files,
            workflow_type=action,
        )
    else:
        pass
    return 0


def parse_args() -> int:
    parser = argparse.ArgumentParser(
        description="🤖 Copilot-ChatDev Agent Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "action",
        choices=["review", "refactor", "enhance", "debug"],
        help="Agent collaboration action",
    )

    parser.add_argument(
        "files",
        nargs="*",
        help=(
            "Target files for agent collaboration. "
            "Paths without directories are resolved relative to src/. "
            "Use './' to target repository root files."
        ),
    )

    parser.add_argument(
        "--all-changed",
        action="store_true",
        help="Target all changed files in git",
    )

    parser.add_argument(
        "--output-dir",
        default="agent_output",
        help="Output directory for agent results",
    )

    args = parser.parse_args()

    project_root = Path.cwd()
    target_files: list[Any] = []
    # Get target files
    if args.all_changed:
        changed_files = get_changed_files(project_root)
        if changed_files:
            target_files.extend(changed_files)
        else:
            pass

    if args.files:
        target_files.extend(args.files)

    if not target_files:
        return 1

    # Analyze files

    analyses: list[Any] = []
    valid_files = 0

    for file_path_str in target_files:
        file_path = project_root / file_path_str
        analysis = analyze_file(file_path)

        if "error" not in analysis:
            analyses.append(analysis)
            valid_files += 1
        else:
            pass

    if not analyses:
        return 1

    # Generate agent task
    agent_task = generate_agent_task(args.action, analyses)

    # Create output directory and save task
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_file = output_dir / f"chatdev_task_{args.action}_{timestamp}.txt"

    with open(task_file, "w", encoding="utf-8") as f:
        f.write(agent_task)

    # Save analysis context
    context_file = output_dir / f"analysis_context_{args.action}_{timestamp}.json"
    with open(context_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "action": args.action,
                "timestamp": timestamp,
                "target_files": target_files,
                "analyses": analyses,
                "summary": {
                    "total_files": len(analyses),
                    "total_lines": sum(a.get("lines", 0) for a in analyses),
                    "languages": list({a.get("language") for a in analyses}),
                    "total_functions": sum(len(a.get("functions", [])) for a in analyses),
                },
            },
            f,
            indent=2,
        )

    # Show summary
    {
        "files": len(analyses),
        "lines": sum(a.get("lines", 0) for a in analyses),
        "functions": sum(len(a.get("functions", [])) for a in analyses),
    }

    return 0


if __name__ == "__main__":
    sys.exit(main())

if __name__ == "__main__":
    sys.exit(main())
