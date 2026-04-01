#!/usr/bin/env python3
"""🎯 Next Steps Priority Assessment Tool.

Helps determine the best immediate next steps based on current system state.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from config.service_config import ServiceConfig
except ImportError:  # pragma: no cover - fallback when config not importable
    ServiceConfig = None


def _context_browser_url() -> str:
    env_base = os.environ.get("CONTEXT_BROWSER_BASE_URL") or os.environ.get("STREAMLIT_BASE_URL")
    if env_base:
        return env_base

    host = os.environ.get("CONTEXT_BROWSER_HOST") or os.environ.get(
        "STREAMLIT_HOST",
        "http://127.0.0.1",
    )
    port = os.environ.get("CONTEXT_BROWSER_PORT") or os.environ.get(
        "STREAMLIT_PORT",
        "8501",
    )
    return f"{host.rstrip('/')}:" + str(port)


def assess_current_state():
    """Assess the current state of our development environment."""
    assessments: dict[str, Any] = {}
    context_browser_url = (
        ServiceConfig.get_context_browser_url() if ServiceConfig else _context_browser_url()
    )

    # 1. Enhanced Context Browser Status
    try:
        health_snippet = (
            "import requests; "
            f'url="{context_browser_url}"; '
            "r=requests.get(url, timeout=3); "
            'print("✅ Running" if r.status_code==200 else "❌ Not responding")'
        )
        # Check if processes are running
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                health_snippet,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        browser_status = "✅ Running" if "✅" in result.stdout else "❌ Not Running"
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        browser_status = "❌ Not Running"

    assessments["context_browser"] = browser_status

    # 2. Repository Health
    repo_files = list(Path().rglob("*.py"))
    assessments["python_files"] = len(repo_files)

    # 3. AI Systems Integration
    ai_files = list(Path().rglob("*ai*.py")) + list(Path().rglob("*AI*.py"))
    assessments["ai_files"] = len(ai_files)

    # 4. Documentation Status
    md_files = list(Path().rglob("*.md"))
    assessments["documentation_files"] = len(md_files)

    return assessments


def recommend_priorities(assessments):
    """Generate priority recommendations based on assessment."""
    priorities: list[Any] = []
    # Context Browser Priority
    if "❌" in assessments["context_browser"]:
        priorities.append(
            {
                "priority": "HIGH",
                "task": "Fix Enhanced Context Browser",
                "reason": "Core tool not working properly",
                "action": "Debug and restart the browser application",
            }
        )
    else:
        priorities.append(
            {
                "priority": "MEDIUM",
                "task": "Enhance Context Browser Features",
                "reason": "Browser working, ready for improvements",
                "action": "Add advanced analytics and visualizations",
            }
        )

    # Repository Analysis Priority
    if assessments["python_files"] > 50:
        priorities.append(
            {
                "priority": "HIGH",
                "task": "Repository Organization & Analysis",
                "reason": f"Large codebase ({assessments['python_files']} Python files) needs structure",
                "action": "Create comprehensive dependency mapping and organization",
            }
        )

    # AI Integration Priority
    if assessments["ai_files"] > 5:
        priorities.append(
            {
                "priority": "MEDIUM",
                "task": "AI Systems Coordination",
                "reason": f"Multiple AI systems ({assessments['ai_files']} files) need coordination",
                "action": "Implement advanced AI orchestration patterns",
            }
        )

    # Documentation Priority
    if assessments["documentation_files"] < 10:
        priorities.append(
            {
                "priority": "LOW",
                "task": "Documentation Enhancement",
                "reason": "Insufficient documentation for complex system",
                "action": "Create comprehensive documentation and guides",
            }
        )

    return priorities


def display_recommendations(priorities) -> None:
    """Display prioritized recommendations."""
    priority_colors = {
        "HIGH": "🔴",
        "MEDIUM": "🟡",
        "LOW": "🟢",
    }

    for _i, item in enumerate(priorities, 1):
        priority_colors.get(item["priority"], "⚪")


def generate_session_plan() -> None:
    """Generate a focused session plan."""
    session_tasks = [
        "1. 🔍 Verify Enhanced Context Browser is accessible",
        "2. 📊 Run comprehensive repository analysis",
        "3. 🤖 Test AI coordination systems",
        "4. 🛡️ Validate anti-recursion protections",
        "5. 🎯 Choose next feature development focus",
    ]

    for _task in session_tasks:
        pass


def main() -> int:
    """Run the priority assessment."""
    try:
        # Assess current state
        assessments = assess_current_state()

        # Generate recommendations
        priorities = recommend_priorities(assessments)

        # Display results
        display_recommendations(priorities)

        # Generate session plan
        generate_session_plan()

        # Save assessment results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            "timestamp": timestamp,
            "assessments": assessments,
            "priorities": priorities,
        }

        with open(f"next_steps_assessment_{timestamp}.json", "w") as f:
            json.dump(results, f, indent=2)

    except (OSError, json.JSONDecodeError, ValueError):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
