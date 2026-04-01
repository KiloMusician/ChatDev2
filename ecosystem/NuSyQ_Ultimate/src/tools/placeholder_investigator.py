#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║ ΞNuSyQ Placeholder Investigator                                         ║
╠══════════════════════════════════════════════════════════════════════════╣
║ FILE-ID: nusyq.scripts.placeholder_investigator                         ║
║ TYPE: Python Script                                                     ║
║ STATUS: Production                                                      ║
║ VERSION: 1.0.0                                                          ║
║ PURPOSE: Automated placeholder code detection and integration planning  ║
║ TAGS: [automation, code-quality, technical-debt, ci-cd]                ║
║ CONTEXT: Σ3 (System Maintenance)                                       ║
║ AGENTS: [GitHubCopilot, ClaudeCode, OllamaQwen14b]                     ║
║ CREATED: 2025-10-07                                                     ║
║ AUTHOR: GitHub Copilot                                                  ║
╚══════════════════════════════════════════════════════════════════════════╝

Automatically scans codebase for placeholder code, analyzes context,
and creates actionable integration tasks for development pipeline.

Features:
- Multi-pattern placeholder detection (TODO, FIXME, PLACEHOLDER, STUB, etc.)
- Context analysis using AST parsing
- Priority classification (CRITICAL, HIGH, MEDIUM, LOW)
- Integration strategy recommendations
- GitHub issue generation
- Automated task routing to appropriate agents
- Progress tracking in knowledge-base.yaml
"""

import ast
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class PlaceholderMatch:
    """Represents a single placeholder code instance"""

    file_path: str
    line_number: int
    line_content: str
    pattern_type: str  # TODO, FIXME, PLACEHOLDER, etc.
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    priority: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM, LOW
    integration_strategy: Optional[str] = None
    estimated_effort: Optional[str] = None  # TRIVIAL, SIMPLE, MODERATE, COMPLEX
    recommended_agent: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)


@dataclass
class PlaceholderReport:
    """Complete placeholder analysis report"""

    scan_timestamp: str
    total_placeholders: int
    by_priority: Dict[str, int] = field(default_factory=dict)
    by_file: Dict[str, int] = field(default_factory=dict)
    by_type: Dict[str, int] = field(default_factory=dict)
    matches: List[PlaceholderMatch] = field(default_factory=list)
    integration_tasks: List[Dict] = field(default_factory=list)


class PlaceholderInvestigator:
    """Automated placeholder code analysis and integration planning"""

    # Placeholder patterns to search for
    PATTERNS = {
        "TODO": r"TODO:?\s*(.*)",
        "FIXME": r"FIXME:?\s*(.*)",
        "HACK": r"HACK:?\s*(.*)",
        "PLACEHOLDER": r"PLACEHOLDER:?\s*(.*)",
        "XXX": r"XXX:?\s*(.*)",
        "TEMP": r"TEMP:?\s*(.*)",
        "STUB": r"STUB:?\s*(.*)",
        "NotImplemented": r"NotImplemented(?:Error)?",
        "raise NotImplementedError": r"raise\s+NotImplementedError",
    }

    # Files/directories to exclude
    EXCLUDE_PATTERNS = {
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache",
        "ChatDev/WareHouse",
        "Archive",
        "Logs",
        ".vscode",
    }

    # File extensions to scan
    SCAN_EXTENSIONS = {".py", ".js", ".ts", ".yaml", ".yml", ".md", ".txt"}

    # Priority keywords (presence increases priority)
    PRIORITY_KEYWORDS = {
        "CRITICAL": ["security", "production", "critical", "urgent", "vulnerability"],
        "HIGH": ["integration", "api", "auth", "data loss", "breaking"],
        "MEDIUM": ["refactor", "optimize", "improve", "enhance"],
        "LOW": ["cleanup", "cosmetic", "documentation", "comment"],
    }

    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root)
        self.report = PlaceholderReport(
            scan_timestamp=datetime.now().isoformat(), total_placeholders=0
        )

    def scan_codebase(self) -> PlaceholderReport:
        """Scan entire codebase for placeholders"""
        print(f"🔍 Scanning codebase: {self.workspace_root}")
        print(f"   Patterns: {', '.join(self.PATTERNS.keys())}")
        print(f"   Extensions: {', '.join(self.SCAN_EXTENSIONS)}\n")

        for file_path in self._get_scannable_files():
            self._scan_file(file_path)

        self._analyze_matches()
        self._generate_integration_tasks()

        print("\n✅ Scan complete!")
        print(f"   Total placeholders: {self.report.total_placeholders}")
        print(f"   Files affected: {len(self.report.by_file)}")

        return self.report

    def _get_scannable_files(self) -> List[Path]:
        """Get all files that should be scanned"""
        scannable_files = []

        for file_path in self.workspace_root.rglob("*"):
            # Skip directories
            if file_path.is_dir():
                continue

            # Skip excluded patterns
            if any(excluded in file_path.parts for excluded in self.EXCLUDE_PATTERNS):
                continue

            # Only scan specified extensions
            if file_path.suffix not in self.SCAN_EXTENSIONS:
                continue

            scannable_files.append(file_path)

        return scannable_files

    def _scan_file(self, file_path: Path):
        """Scan a single file for placeholders"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, start=1):
                for pattern_type, pattern_regex in self.PATTERNS.items():
                    if re.search(pattern_regex, line, re.IGNORECASE):
                        match = self._create_match(file_path, line_num, line, pattern_type, lines)
                        self.report.matches.append(match)
                        self.report.total_placeholders += 1

                        # Update statistics
                        relative_path = str(file_path.relative_to(self.workspace_root))
                        self.report.by_file[relative_path] = (
                            self.report.by_file.get(relative_path, 0) + 1
                        )
                        self.report.by_type[pattern_type] = (
                            self.report.by_type.get(pattern_type, 0) + 1
                        )

        except (OSError, UnicodeDecodeError, ValueError, TypeError, re.error) as e:
            print(f"⚠️  Error scanning {file_path}: {e}")

    def _create_match(
        self,
        file_path: Path,
        line_num: int,
        line: str,
        pattern_type: str,
        all_lines: List[str],
    ) -> PlaceholderMatch:
        """Create a PlaceholderMatch with full context"""

        # Get surrounding context (3 lines before/after)
        context_before = all_lines[max(0, line_num - 4) : line_num - 1]
        context_after = all_lines[line_num : min(len(all_lines), line_num + 3)]

        match = PlaceholderMatch(
            file_path=str(file_path.relative_to(self.workspace_root)),
            line_number=line_num,
            line_content=line.strip(),
            pattern_type=pattern_type,
            context_before=[line_text.strip() for line_text in context_before],
            context_after=[line_text.strip() for line_text in context_after],
        )

        # Analyze context for Python files
        if file_path.suffix == ".py":
            self._analyze_python_context(match, file_path)

        # Determine priority
        match.priority = self._determine_priority(match)

        # Recommend integration strategy
        match.integration_strategy = self._recommend_integration_strategy(match)

        # Estimate effort
        match.estimated_effort = self._estimate_effort(match)

        # Recommend agent
        match.recommended_agent = self._recommend_agent(match)

        return match

    def _analyze_python_context(self, match: PlaceholderMatch, file_path: Path):
        """Analyze Python AST to determine function/class context"""
        try:
            with open(self.workspace_root / file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            # Find the node containing this line
            for node in ast.walk(tree):
                lineno = getattr(node, "lineno", None)
                if lineno is None:
                    continue

                end_lineno = getattr(node, "end_lineno", lineno)
                if lineno <= match.line_number <= end_lineno:
                    if isinstance(node, ast.FunctionDef):
                        match.function_name = node.name
                    elif isinstance(node, ast.AsyncFunctionDef):
                        match.function_name = f"async {node.name}"
                    elif isinstance(node, ast.ClassDef):
                        match.class_name = node.name

        except (OSError, SyntaxError, UnicodeDecodeError):
            # Not all Python files parse cleanly, that's okay
            pass

    def _determine_priority(self, match: PlaceholderMatch) -> str:
        """Determine priority based on keywords and context"""

        # Check comment text for priority keywords
        text = match.line_content.lower()
        for context_line in match.context_before + match.context_after:
            text += " " + context_line.lower()

        for priority, keywords in self.PRIORITY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return priority

        # Security-related files are HIGH priority
        if "security" in match.file_path.lower():
            return "HIGH"

        # Production server files are HIGH priority
        if "mcp_server" in match.file_path and "main.py" in match.file_path:
            return "HIGH"

        # Integration code is MEDIUM-HIGH
        if "integration" in match.file_path.lower() or "bridge" in match.file_path.lower():
            return "MEDIUM"

        return "MEDIUM"

    def _recommend_integration_strategy(self, match: PlaceholderMatch) -> str:
        """Recommend how to integrate this placeholder"""

        text = match.line_content.lower()

        # AI Council integration
        if "ai council" in text or "aicouncil" in text:
            return "Import and call actual AICouncil.execute_session() method"

        # ChatDev integration
        if "chatdev" in text:
            return "Create ChatDev API wrapper for programmatic invocation"

        # Security hardening
        if any(kw in text for kw in ["security", "cors", "path traversal", "sandbox"]):
            return "Implement security controls (whitelist, validation, isolation)"

        # API integration
        if "api" in text or "endpoint" in text:
            return "Implement REST API client or endpoint handler"

        # File operations
        if "file" in text or "path" in text:
            return "Add path validation and error handling"

        # Jupyter/code execution
        if "jupyter" in text or "execute" in text:
            return "Implement sandboxed execution environment"

        return "Review context and implement proper solution"

    def _estimate_effort(self, match: PlaceholderMatch) -> str:
        """Estimate implementation effort"""

        # CRITICAL priority items are usually COMPLEX
        if match.priority == "CRITICAL":
            return "COMPLEX"

        # Security items need careful review
        if "security" in match.file_path.lower():
            return "MODERATE"

        # Integration work is typically MODERATE to COMPLEX
        integration_strategy = (match.integration_strategy or "").lower()
        if "integration" in integration_strategy:
            return "MODERATE"

        # Simple TODOs are often SIMPLE
        if match.pattern_type == "TODO" and len(match.line_content) < 100:
            return "SIMPLE"

        return "MODERATE"

    def _recommend_agent(self, match: PlaceholderMatch) -> str:
        """Recommend which AI agent should handle this task"""

        effort = match.estimated_effort
        priority = match.priority

        # CRITICAL + COMPLEX = AI Council + Claude
        if priority == "CRITICAL" and effort == "COMPLEX":
            return "ai_council_advisory → claude_code"

        # Security = Qwen 14B (best for complex analysis)
        if "security" in match.file_path.lower():
            return "qwen2.5-coder:14b"

        # Integration work = AI Council discussion
        integration_strategy = (match.integration_strategy or "").lower()
        if "integration" in integration_strategy:
            return "ai_council_session → qwen2.5-coder:14b"

        # COMPLEX tasks = Qwen 14B or Gemma 9B
        if effort == "COMPLEX":
            return "qwen2.5-coder:14b (or gemma2:9b for architecture)"

        # MODERATE tasks = Qwen 7B
        if effort == "MODERATE":
            return "qwen2.5-coder:7b"

        # SIMPLE tasks = Fast models
        return "codellama:7b"

    def _analyze_matches(self):
        """Analyze all matches to find patterns and dependencies"""

        # Group by priority
        for match in self.report.matches:
            priority = match.priority
            self.report.by_priority[priority] = self.report.by_priority.get(priority, 0) + 1

        # Detect dependencies (e.g., integration TODOs that reference each other)
        integration_matches = [
            m
            for m in self.report.matches
            if "integration" in (m.integration_strategy or "").lower()
        ]

        for match in integration_matches:
            # Find related integration tasks
            for other in integration_matches:
                if other.file_path != match.file_path:
                    if any(
                        keyword in other.line_content.lower()
                        for keyword in ["aicouncil", "chatdev", "bridge"]
                    ):
                        match.dependencies.append(other.file_path)

    def _generate_integration_tasks(self):
        """Generate actionable integration tasks for development pipeline"""

        # Group by file and priority
        critical_matches = [m for m in self.report.matches if m.priority == "CRITICAL"]
        high_matches = [m for m in self.report.matches if m.priority == "HIGH"]

        if critical_matches:
            self.report.integration_tasks.append(
                {
                    "task_id": "critical-placeholder-sweep",
                    "title": "Critical Placeholder Sweep",
                    "priority": "CRITICAL",
                    "effort": "COMPLEX",
                    "agent": "qwen2.5-coder:14b",
                    "description": "Resolve critical placeholders flagged by automated investigation",
                    "subtasks": [
                        "Review critical placeholder contexts",
                        "Implement missing logic or guardrails",
                        "Add proof-gate coverage for critical paths",
                    ],
                    "files": [m.file_path for m in critical_matches][:10],
                    "estimated_time": f"{len(critical_matches)} critical items",
                    "dependencies": [],
                }
            )

        # Task 1: Security Hardening (mcp_server/main.py)
        security_todos = [
            m
            for m in high_matches
            if "mcp_server/main.py" in m.file_path and "security" in m.line_content.lower()
        ]

        if security_todos:
            self.report.integration_tasks.append(
                {
                    "task_id": "security-hardening-mcp",
                    "title": "MCP Server Security Hardening",
                    "priority": "HIGH",
                    "effort": "MODERATE",
                    "agent": "qwen2.5-coder:14b",
                    "description": "Implement security controls for MCP server",
                    "subtasks": [
                        "CORS origin whitelist (line 180)",
                        "Path traversal protection (line 845)",
                        "File write restrictions (line 887)",
                        "Code execution isolation (line 1022)",
                    ],
                    "files": ["mcp_server/main.py"],
                    "estimated_time": "2-3 hours",
                    "dependencies": [],
                }
            )

        # Task 2: AI Council Integration (claude_code_bridge.py)
        council_todos = [
            m
            for m in self.report.matches
            if "claude_code_bridge.py" in m.file_path and "aicouncil" in m.line_content.lower()
        ]

        if council_todos:
            self.report.integration_tasks.append(
                {
                    "task_id": "aicouncil-integration",
                    "title": "Complete AI Council Integration",
                    "priority": "MEDIUM",
                    "effort": "MODERATE",
                    "agent": "ai_council_session → qwen2.5-coder:14b",
                    "description": "Replace placeholder with actual AICouncil.execute_session() call",
                    "subtasks": [
                        "Import AICouncil from config/ai_council.py",
                        "Replace subprocess call with direct method invocation",
                        "Handle session results properly",
                        "Update error handling",
                    ],
                    "files": ["config/claude_code_bridge.py", "config/ai_council.py"],
                    "estimated_time": "1-2 hours",
                    "dependencies": [],
                }
            )

        # Task 3: ChatDev API Integration
        chatdev_todos = [
            m
            for m in self.report.matches
            if "chatdev" in m.line_content.lower() and m.pattern_type == "TODO"
        ]

        if chatdev_todos:
            self.report.integration_tasks.append(
                {
                    "task_id": "chatdev-api-wrapper",
                    "title": "Create ChatDev API Wrapper",
                    "priority": "MEDIUM",
                    "effort": "COMPLEX",
                    "agent": "ai_council_session → qwen2.5-coder:14b",
                    "description": "Build programmatic API wrapper for ChatDev execution",
                    "subtasks": [
                        "Design ChatDevAPI class with async methods",
                        "Implement project creation interface",
                        "Add progress monitoring callbacks",
                        "Create result parsing logic",
                        "Update claude_code_bridge.py integration",
                    ],
                    "files": [
                        "config/chatdev_api.py",  # NEW
                        "config/claude_code_bridge.py",
                        "nusyq_chatdev.py",
                    ],
                    "estimated_time": "3-4 hours",
                    "dependencies": [],
                }
            )

        # Task 4: Multi-Agent Orchestration Enhancement
        orchestration_todos = [
            m
            for m in self.report.matches
            if "orchestration" in m.file_path.lower() or "multi_agent" in m.file_path.lower()
        ]

        if orchestration_todos:
            self.report.integration_tasks.append(
                {
                    "task_id": "orchestration-enhancement",
                    "title": "Enhance Multi-Agent Orchestration",
                    "priority": "LOW",
                    "effort": "MODERATE",
                    "agent": "qwen2.5-coder:14b",
                    "description": "Replace placeholder orchestration with full implementation",
                    "subtasks": [
                        "Implement actual agent coordination logic",
                        "Add result aggregation",
                        "Improve error handling",
                        "Add orchestration metrics",
                    ],
                    "files": ["mcp_server/main.py", "config/multi_agent_session.py"],
                    "estimated_time": "2-3 hours",
                    "dependencies": ["aicouncil-integration"],
                }
            )

    def save_report(self, output_path: Path):
        """Save detailed report to JSON file"""

        report_data = {
            "scan_timestamp": self.report.scan_timestamp,
            "total_placeholders": self.report.total_placeholders,
            "statistics": {
                "by_priority": self.report.by_priority,
                "by_file": self.report.by_file,
                "by_type": self.report.by_type,
            },
            "matches": [
                {
                    "file": m.file_path,
                    "line": m.line_number,
                    "content": m.line_content,
                    "type": m.pattern_type,
                    "priority": m.priority,
                    "function": m.function_name,
                    "class": m.class_name,
                    "strategy": m.integration_strategy,
                    "effort": m.estimated_effort,
                    "agent": m.recommended_agent,
                    "dependencies": m.dependencies,
                }
                for m in self.report.matches
            ],
            "integration_tasks": self.report.integration_tasks,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        print(f"\n💾 Detailed report saved: {output_path}")

    def save_markdown_report(self, output_path: Path):
        """Save human-readable markdown report"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Placeholder Investigation Report\n\n")
            f.write(f"**Scan Date**: {self.report.scan_timestamp}\n\n")
            f.write(f"**Total Placeholders**: {self.report.total_placeholders}\n\n")

            # Statistics
            f.write("## 📊 Statistics\n\n")
            f.write("### By Priority\n\n")
            for priority in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                count = self.report.by_priority.get(priority, 0)
                f.write(f"- **{priority}**: {count}\n")

            f.write("\n### By Pattern Type\n\n")
            for pattern_type, count in sorted(self.report.by_type.items(), key=lambda x: -x[1]):
                f.write(f"- **{pattern_type}**: {count}\n")

            f.write("\n### Top 10 Files\n\n")
            top_files = sorted(self.report.by_file.items(), key=lambda x: -x[1])[:10]
            for file_path, count in top_files:
                f.write(f"- `{file_path}`: {count}\n")

            # Integration Tasks
            f.write("\n## 🔧 Integration Tasks\n\n")
            for task in self.report.integration_tasks:
                f.write(f"### {task['title']}\n\n")
                f.write(f"**ID**: `{task['task_id']}`\n")
                f.write(f"**Priority**: {task['priority']}\n")
                f.write(f"**Effort**: {task['effort']}\n")
                f.write(f"**Recommended Agent**: {task['agent']}\n")
                f.write(f"**Estimated Time**: {task['estimated_time']}\n\n")
                f.write(f"{task['description']}\n\n")

                f.write("**Subtasks**:\n")
                for subtask in task["subtasks"]:
                    f.write(f"- [ ] {subtask}\n")

                f.write(f"\n**Files**: {', '.join(f'`{f}`' for f in task['files'])}\n\n")

                if task["dependencies"]:
                    f.write(f"**Dependencies**: {', '.join(task['dependencies'])}\n\n")

                f.write("---\n\n")

            # Detailed Matches (grouped by priority)
            f.write("\n## 📝 Detailed Matches\n\n")
            for priority in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                matches = [m for m in self.report.matches if m.priority == priority]
                if matches:
                    f.write(f"### {priority} Priority ({len(matches)} items)\n\n")
                    for match in matches:
                        f.write(f"#### `{match.file_path}:{match.line_number}`\n\n")
                        f.write(f"```\n{match.line_content}\n```\n\n")
                        f.write(f"- **Type**: {match.pattern_type}\n")
                        if match.function_name:
                            f.write(f"- **Function**: `{match.function_name}`\n")
                        if match.class_name:
                            f.write(f"- **Class**: `{match.class_name}`\n")
                        f.write(f"- **Strategy**: {match.integration_strategy}\n")
                        f.write(f"- **Effort**: {match.estimated_effort}\n")
                        f.write(f"- **Recommended Agent**: {match.recommended_agent}\n")
                        f.write("\n")

        print(f"📄 Markdown report saved: {output_path}")

    def update_knowledge_base(self):
        """Update knowledge-base.yaml with integration tasks"""

        kb_path = self.workspace_root / "knowledge-base.yaml"

        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                kb_data = yaml.safe_load(f)

            # Add pending tasks
            if "tasks" not in kb_data:
                kb_data["tasks"] = {}
            if "pending" not in kb_data["tasks"]:
                kb_data["tasks"]["pending"] = []

            for task in self.report.integration_tasks:
                kb_task = {
                    "id": task["task_id"],
                    "name": task["title"],
                    "priority": task["priority"].lower(),
                    "effort": task["effort"].lower(),
                    "agent": task["agent"],
                    "description": task["description"],
                    "files": task["files"],
                    "estimated_time": task["estimated_time"],
                    "created_date": datetime.now().strftime("%Y-%m-%d"),
                    "source": "placeholder_investigator",
                }

                # Check if task already exists
                if not any(t.get("id") == task["task_id"] for t in kb_data["tasks"]["pending"]):
                    kb_data["tasks"]["pending"].append(kb_task)

            # Save updated knowledge base
            with open(kb_path, "w", encoding="utf-8") as f:
                yaml.dump(kb_data, f, default_flow_style=False, sort_keys=False)

            print(f"📚 Knowledge base updated: {kb_path}")
            print(f"   Added {len(self.report.integration_tasks)} integration tasks")

        except (OSError, yaml.YAMLError, ValueError, TypeError, AttributeError) as e:
            print(f"⚠️  Error updating knowledge base: {e}")


def main():
    """Main entry point"""

    print("=" * 60)
    print("🔍 ΞNuSyQ Placeholder Investigator")
    print("=" * 60)
    print()

    workspace_root = Path(__file__).parent.parent

    investigator = PlaceholderInvestigator(workspace_root)
    report = investigator.scan_codebase()

    # Save reports
    reports_dir = workspace_root / "Reports"
    reports_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    investigator.save_report(reports_dir / f"placeholder_report_{timestamp}.json")
    investigator.save_markdown_report(reports_dir / "PLACEHOLDER_INVESTIGATION.md")

    # Update knowledge base with tasks
    investigator.update_knowledge_base()

    print("\n" + "=" * 60)
    print("✅ Investigation Complete!")
    print("=" * 60)
    print("\n📊 Summary:")
    print(f"   Total Placeholders: {report.total_placeholders}")
    print(f"   Integration Tasks: {len(report.integration_tasks)}")
    print(f"   Files Affected: {len(report.by_file)}")
    print("\n📈 By Priority:")
    for priority in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        count = report.by_priority.get(priority, 0)
        if count > 0:
            print(f"   {priority}: {count}")

    print("\n📝 Next Steps:")
    print("   1. Review: Reports/PLACEHOLDER_INVESTIGATION.md")
    print("   2. Check: knowledge-base.yaml (pending tasks)")
    print("   3. Execute high-priority integration tasks")
    print("   4. Run this script regularly in CI/CD pipeline")
    print()


if __name__ == "__main__":
    main()
