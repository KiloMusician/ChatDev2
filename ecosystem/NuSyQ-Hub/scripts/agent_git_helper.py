#!/usr/bin/env python3
"""🤖 Agent Git Helper - Intelligent commit message generator and session tracker.

This script helps agents create comprehensive, searchable commit messages with:
- Progress tracking on the 50-item to-do list
- Breadcrumbs for future agent sessions
- Technical context and impact assessment
"""

import subprocess
from datetime import datetime
from pathlib import Path


class AgentGitHelper:
    """Enhanced git operations with agent-aware commit messages."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.session_date = datetime.now().strftime("%Y-%m-%d")
        self.session_time = datetime.now().strftime("%H:%M:%S")

    def create_agent_commit(
        self,
        changes: list[str],
        todo_items_completed: list[str] | None = None,
        next_priorities: list[str] | None = None,
        technical_notes: str = "",
        agent_instructions: str = "",
    ) -> str:
        """Create a comprehensive agent-aware commit message."""
        todo_completed = todo_items_completed or []
        next_items = next_priorities or []

        commit_msg = f"""🤖 Agent Session Progress - {self.session_date}

CHANGES MADE:
{chr(10).join(f"• {change}" for change in changes)}

TO-DO LIST PROGRESS:
✅ Completed ({len(todo_completed)} items):
{chr(10).join(f"  • {item}" for item in todo_completed)}

🎯 Next Priority ({len(next_items)} items):
{chr(10).join(f"  • {item}" for item in next_items)}

TECHNICAL CONTEXT:
{technical_notes if technical_notes else "Standard repository maintenance and enhancement"}

BREADCRUMBS FOR NEXT AGENT:
{agent_instructions if agent_instructions else "Continue with next to-do list items in order of complexity"}

Agent Session: {self.session_date} {self.session_time}
Repository State: Clean and ready for next development cycle
"""
        return commit_msg

    def commit_with_agent_context(
        self,
        changes: list[str],
        todo_completed: list[str] | None = None,
        next_priorities: list[str] | None = None,
        technical_notes: str = "",
        agent_instructions: str = "",
    ) -> bool:
        """Execute git commit with agent-aware message."""
        commit_msg = self.create_agent_commit(
            changes,
            todo_completed,
            next_priorities,
            technical_notes,
            agent_instructions,
        )

        try:
            # Stage all changes
            subprocess.run(["git", "add", "-A"], cwd=self.repo_path, check=True)

            # Commit with message
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=self.repo_path, check=True)

            # Push to remote
            subprocess.run(["git", "push", "origin", "main"], cwd=self.repo_path, check=True)

            return True
        except subprocess.CalledProcessError as e:
            print(f"Git operation failed: {e}")
            return False


# Quick helper function for agents
def agent_commit(changes: list[str], **kwargs):
    """Quick commit function for agent use."""
    helper = AgentGitHelper()
    return helper.commit_with_agent_context(changes, **kwargs)


if __name__ == "__main__":
    # Example usage for agents
    agent_commit(
        changes=[
            "Added agent git helper system",
            "Created session logging infrastructure",
            "Enhanced commit message templates",
        ],
        todo_completed=[
            "Create breadcrumb system for agents",
            "Add intelligent commit message generation",
        ],
        next_priorities=[
            "Implement graceful shutdown logic",
            "Continue print → logging conversion",
            "Add enum constants for model names",
        ],
        technical_notes="Enhanced agent workflow with self-documenting git operations",
        agent_instructions="Use agent_git_helper.py for all future commits to maintain breadcrumb trail",
    )
