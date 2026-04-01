"""Example adapter demonstrating how an agent should be wrapped with task_context.

This file shows how to: create a task, run commands under the task, and register artifacts.
"""

from src.task_runtime.agent_wrapper import task_context
from src.task_runtime.db import Database


def smart_search_called() -> bool:
    # Placeholder precondition - in real usage this would query smart_search/index metadata
    return True


def main():
    with task_context("Example: build and package", precondition_callable=smart_search_called) as ctx:
        # build step
        ctx.run("echo Building... && python -V")
        # package step (example)
        ctx.run("echo Packaging... && dir")

        # optionally register artifacts (direct DB access shown for example)
        db = Database()
        db.execute(
            "INSERT INTO artifacts (project_id, path, type) VALUES (?, ?, ?)",
            (1, "dist_electron/MyAppSetup.exe", "installer"),
        )
        print("Registered artifact in DB")


if __name__ == "__main__":
    main()
