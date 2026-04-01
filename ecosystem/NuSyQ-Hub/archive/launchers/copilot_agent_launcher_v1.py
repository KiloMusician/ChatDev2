#!/usr/bin/env python3
"""🚀 Copilot-ChatDev Agent Launcher
Streamlined launcher for agent-assisted development

Quick Examples:
  python copilot_agent_launcher.py review src/integration/chatdev_integration.py
  python copilot_agent_launcher.py refactor --all-changed
  python copilot_agent_launcher.py enhance src/core/main.py
"""

"""
OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Archive launcher fallback flags
BRIDGE_AVAILABLE = False


def get_target_files(args) -> list[str]:
    """Fallback target file resolver for archived launcher."""
    return list(args.files) if getattr(args, "files", None) else []


def get_changed_files(project_root: Path) -> List[str]:
    """Get list of changed files from git"""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True, cwd=project_root
        )
        if result.returncode == 0:
            return [f for f in result.stdout.strip().split("\n") if f.strip()]
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        pass
    return []


def analyze_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a file for agent collaboration context"""
    if not file_path.exists():
        return {"error": "File not found"}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.splitlines()

        # Basic analysis
        analysis = {
            "path": str(file_path),
            "language": get_language(file_path),
            "lines": len(lines),
            "size": len(content),
            "functions": extract_functions(content),
            "classes": extract_classes(content),
            "imports": extract_imports(content),
        }

        return analysis
    except Exception as e:
        return {"error": str(e)}


def get_language(file_path: Path) -> str:
    """Detect programming language from file extension"""
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


def extract_functions(content: str) -> List[str]:
    """Extract function names from code"""
    functions = []
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("def ") or "function " in line:
            if "def " in line:
                name = line.split("def ")[1].split("(")[0].strip()
            else:
                name = line.split("function ")[1].split("(")[0].strip()
            functions.append(name)
    return functions[:10]  # Limit results


def extract_classes(content: str) -> List[str]:
    """Extract class names from code"""
    classes = []
    for line in content.splitlines():
        if line.strip().startswith("class "):
            name = line.split("class ")[1].split("(")[0].split(":")[0].strip()
            classes.append(name)
    return classes[:5]  # Limit results


def extract_imports(content: str) -> List[str]:
    """Extract import statements"""
    imports = []
    for line in content.splitlines():
        line = line.strip()
        if line.startswith(("import ", "from ", "#include ", "using ")):
            imports.append(line)
    return imports[:8]  # Limit results


def generate_agent_task(action: str, files_analysis: List[Dict[str, Any]]) -> str:
    """Generate ChatDev task description"""
    total_lines = sum(f.get("lines", 0) for f in files_analysis)
    total_functions = sum(len(f.get("functions", [])) for f in files_analysis)
    languages = set(f.get("language", "unknown") for f in files_analysis)

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
        print("❌ Copilot-ChatDev Bridge not available")
        print("💡 Fallback: Creating agent collaboration plan...")

        # Simple fallback mode
        args = parse_args()
        print("🤖 Copilot-ChatDev Agent Launcher (Fallback Mode)")
        print("=" * 50)

        target_files = get_target_files(args)
        if not target_files:
            return 1

        print(f"🎯 Would target {len(target_files)} files for {args.action}")
        print("📋 Manual collaboration steps:")
        print("1. Use GitHub Copilot for real-time assistance")
        print("2. Launch ChatDev separately for team review")
        print("3. Coordinate outputs manually")
        print("4. Integrate improvements")

        return 0


def parse_args():
    parser = argparse.ArgumentParser(
        description="🤖 Copilot-ChatDev Agent Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "action",
        choices=["review", "refactor", "enhance", "debug"],
        help="Agent collaboration action",
    )

    parser.add_argument("files", nargs="*", help="Target files for agent collaboration")

    parser.add_argument(
        "--all-changed", action="store_true", help="Target all changed files in git"
    )

    parser.add_argument(
        "--output-dir", default="agent_output", help="Output directory for agent results"
    )

    args = parser.parse_args()

    print("🤖 Copilot-ChatDev Agent Launcher")
    print("=" * 50)

    project_root = Path.cwd()
    target_files = []

    # Get target files
    if args.all_changed:
        changed_files = get_changed_files(project_root)
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

    # Analyze files
    print(f"🔍 Analyzing {len(target_files)} files...")

    analyses = []
    valid_files = 0

    for file_path_str in target_files:
        file_path = project_root / file_path_str
        analysis = analyze_file(file_path)

        if "error" not in analysis:
            analyses.append(analysis)
            valid_files += 1
            print(f"✅ {file_path_str} ({analysis['language']}, {analysis['lines']} lines)")
        else:
            print(f"⚠️ {file_path_str}: {analysis['error']}")

    if not analyses:
        print("❌ No valid files to analyze")
        return 1

    # Generate agent task
    print(f"\n⚙️ Generating {args.action} task for ChatDev...")
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
                    "languages": list(set(a.get("language") for a in analyses)),
                    "total_functions": sum(len(a.get("functions", [])) for a in analyses),
                },
            },
            f,
            indent=2,
        )

    print("\n✅ Agent collaboration task ready!")
    print(f"📋 Task file: {task_file}")
    print(f"📊 Context file: {context_file}")

    # Show summary
    summary = {
        "files": len(analyses),
        "lines": sum(a.get("lines", 0) for a in analyses),
        "functions": sum(len(a.get("functions", [])) for a in analyses),
    }

    print("\n📊 Analysis Summary:")
    print(f"   📁 Files analyzed: {summary['files']}")
    print(f"   📝 Total lines: {summary['lines']}")
    print(f"   🔧 Functions found: {summary['functions']}")

    print("\n🚀 Next steps:")
    print("1. Use GitHub Copilot for real-time assistance")
    print(f"2. Launch ChatDev with task: {task_file}")
    print("3. Coordinate agent outputs for best results")

    print("\n💡 ChatDev launch command:")
    print(f"   python -m chatdev --task-file {task_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

if __name__ == "__main__":
    sys.exit(main())
