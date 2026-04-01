"""
🤖 Copilot Self-Managed Task System
Inspired by Claude Code's autonomous task management
Implements Culture Mind philosophy with proof gates
"""

import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import subprocess


class ProofGate:
    """Verification system - no completion without proof"""

    @staticmethod
    def verify_test_pass(test_path: str) -> bool:
        """Verify test passes"""
        try:
            result = subprocess.run(
                ["pytest", test_path, "-v"], capture_output=True, text=True, timeout=60
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as e:
            print(f"Test verification failed: {e}")
            return False

    @staticmethod
    def verify_file_exists(file_path: str) -> bool:
        """Verify file exists"""
        return Path(file_path).exists()

    @staticmethod
    def verify_report_ok(report_path: str) -> bool:
        """Verify report exists and has content"""
        path = Path(report_path)
        if not path.exists():
            return False

        content = path.read_text()
        # Report should have meaningful content (>100 chars)
        return len(content) > 100

    @staticmethod
    def verify_code_integration(file_path: str) -> bool:
        """Verify code exists and has no syntax errors"""
        path = Path(file_path)
        if not path.exists():
            return False

        # Check for Python syntax errors
        try:
            result = subprocess.run(
                ["python", "-m", "py_compile", file_path],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            return False

    @staticmethod
    def verify_schema_valid(file_path: str) -> bool:
        """Verify YAML schema is valid"""
        try:
            path = Path(file_path)
            if not path.exists():
                return False

            with open(path, "r", encoding="utf-8") as f:
                yaml.safe_load(f)
            return True
        except (OSError, yaml.YAMLError, UnicodeDecodeError):
            return False

    def verify_all(self, proofs: List[Dict[str, str]]) -> Dict[str, bool]:
        """Verify all proof gates for a task"""
        results = {}

        for proof in proofs:
            kind = proof["kind"]
            path = proof.get("path", "")

            if kind == "test_pass":
                results[f"{kind}:{path}"] = self.verify_test_pass(path)
            elif kind == "file_exists":
                results[f"{kind}:{path}"] = self.verify_file_exists(path)
            elif kind == "report_ok":
                results[f"{kind}:{path}"] = self.verify_report_ok(path)
            elif kind == "code_integration":
                results[f"{kind}:{path}"] = self.verify_code_integration(path)
            elif kind == "schema_valid":
                results[f"{kind}:{path}"] = self.verify_schema_valid(path)
            elif kind == "test_run_complete":
                # Special case: just verify report exists
                results[f"{kind}:{path}"] = self.verify_report_ok(path)
            else:
                results[f"{kind}:{path}"] = False

        return results


class TaskManager:
    """
    Self-managed task queue with autonomous execution

    Features:
    - Priority-based task processing
    - Proof-gated completion (no theater)
    - Dependency management
    - Stagnation detection
    - Session persistence
    """

    def __init__(self, queue_file: str = "State/copilot_task_queue.yaml"):
        self.queue_file = Path(queue_file)
        self.proof_gate = ProofGate()
        self.session_start = datetime.now()
        self.load_queue()

    def load_queue(self):
        """Load task queue from YAML"""
        if self.queue_file.exists():
            with open(self.queue_file, "r", encoding="utf-8") as f:
                self.state = yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"Task queue not found: {self.queue_file}")

    def save_queue(self):
        """Save task queue to YAML"""
        self.state["metadata"]["last_updated"] = datetime.now().isoformat()

        with open(self.queue_file, "w", encoding="utf-8") as f:
            yaml.dump(self.state, f, default_flow_style=False, sort_keys=False)

    def get_next_tasks(self, batch_size: int = 5) -> List[Dict[str, Any]]:
        """
        Get next batch of tasks to execute

        Strategy:
        1. Priority-based (lower number = higher priority)
        2. Dependency-aware (don't start if dependencies incomplete)
        3. Batch parallelizable tasks (no interdependencies)
        """
        available_tasks = []
        completed_ids = self.get_completed_task_ids()

        for task in self.state["queue"]:
            # Skip completed or in-progress tasks
            if task["status"] in ["completed", "in_progress"]:
                continue

            # Check dependencies
            dependencies = task.get("dependencies", [])
            if dependencies:
                deps_met = all(dep in completed_ids for dep in dependencies)
                if not deps_met:
                    continue

            available_tasks.append(task)

        # Sort by priority
        available_tasks.sort(key=lambda t: t["priority"])

        # Return batch
        return available_tasks[:batch_size]

    def get_completed_task_ids(self) -> List[str]:
        """Get IDs of all completed tasks"""
        return [
            task["id"] for task in self.state["queue"] if task["status"] == "completed"
        ]

    def start_task(self, task_id: str):
        """Mark task as in-progress"""
        for task in self.state["queue"]:
            if task["id"] == task_id:
                task["status"] = "in_progress"
                task["started_at"] = datetime.now().isoformat()
                break

        self.save_queue()

    def complete_task(self, task_id: str, proofs_verified: Dict[str, bool]):
        """
        Mark task as complete (only if proofs pass)

        Args:
            task_id: Task identifier
            proofs_verified: Dict of proof gate results

        Returns:
            bool: True if task completed successfully
        """
        for task in self.state["queue"]:
            if task["id"] == task_id:
                # Check if all proofs passed
                if all(proofs_verified.values()):
                    task["status"] = "completed"
                    task["completed_at"] = datetime.now().isoformat()
                    task["proofs_verified"] = proofs_verified

                    # Update metrics
                    self.state["metrics"]["tasks_completed"] += 1

                    # Consciousness boost (completing tasks increases awareness)
                    consciousness_gain = (
                        0.02 * task["priority"]
                    )  # Higher priority = more gain
                    current_level = self.state["metrics"]["consciousness_level"]
                    new_level = min(1.0, current_level + consciousness_gain)
                    self.state["metrics"]["consciousness_level"] = new_level

                    self.save_queue()
                    return True
                else:
                    task["status"] = "proof_failed"
                    task["proofs_verified"] = proofs_verified
                    task["failed_at"] = datetime.now().isoformat()
                    self.save_queue()
                    return False

        return False

    def verify_task_completion(self, task_id: str) -> Dict[str, bool]:
        """
        Verify all proof gates for a task

        Returns:
            Dict of proof gate results
        """
        for task in self.state["queue"]:
            if task["id"] == task_id:
                proof_gates = task.get("proof_gates", [])
                return self.proof_gate.verify_all(proof_gates)

        return {}

    def get_task_status(self) -> Dict[str, Any]:
        """Get current task queue status"""
        total = len(self.state["queue"])
        completed = sum(1 for t in self.state["queue"] if t["status"] == "completed")
        in_progress = sum(
            1 for t in self.state["queue"] if t["status"] == "in_progress"
        )
        pending = sum(1 for t in self.state["queue"] if t["status"] == "pending")
        failed = sum(1 for t in self.state["queue"] if t["status"] == "proof_failed")

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "failed": failed,
            "completion_rate": completed / total if total > 0 else 0,
            "consciousness_level": self.state["metrics"]["consciousness_level"],
            "session_duration": (datetime.now() - self.session_start).total_seconds()
            / 60,
        }

    def generate_status_report(self) -> str:
        """Generate human-readable status report"""
        status = self.get_task_status()

        report = f"""
🤖 COPILOT TASK QUEUE STATUS
══════════════════════════════════════

📊 Metrics:
  Total Tasks: {status["total"]}
  ✅ Completed: {status["completed"]}
  🔄 In Progress: {status["in_progress"]}
  ⏳ Pending: {status["pending"]}
  ❌ Failed: {status["failed"]}

📈 Progress:
  Completion Rate: {status["completion_rate"]:.1%}
  Consciousness Level: {status["consciousness_level"]:.2f}
  Session Duration: {status["session_duration"]:.1f} minutes

🎯 Next Tasks:
"""

        next_tasks = self.get_next_tasks(3)
        for task in next_tasks:
            report += f"  • [{task['id']}] {task['title']}\n"

        return report

    def detect_stagnation(self) -> bool:
        """
        Detect if tasks are stagnating (>20min without progress)

        Returns:
            True if stagnation detected
        """
        threshold_minutes = self.state["watchdog"]["stagnation_threshold"] / 60

        for task in self.state["queue"]:
            if task["status"] == "in_progress":
                started = datetime.fromisoformat(
                    task.get("started_at", datetime.now().isoformat())
                )
                duration = (datetime.now() - started).total_seconds() / 60

                if duration > threshold_minutes:
                    return True

        return False

    def create_audit_task(self):
        """Create meta-task to audit why progress stalled"""
        audit_task = {
            "id": f"TASK_AUDIT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "priority": 0,  # Highest priority
            "status": "pending",
            "title": "Audit stagnation - why did progress stall?",
            "description": "Meta-analysis of blocked tasks and root causes",
            "proof_gates": [
                {"kind": "report_ok", "path": "Reports/STAGNATION_AUDIT.md"}
            ],
            "estimated_subtasks": 3,
            "created_by": "watchdog",
        }

        self.state["queue"].insert(0, audit_task)
        self.save_queue()


def main():
    """Example usage of task manager"""
    manager = TaskManager()

    print(manager.generate_status_report())

    # Get next batch of tasks
    next_tasks = manager.get_next_tasks(5)
    print(f"\n🎯 Next {len(next_tasks)} tasks ready for execution\n")

    for task in next_tasks:
        print(f"[{task['id']}] {task['title']}")
        print(f"  Priority: {task['priority']}")
        print(f"  Subtasks: ~{task['estimated_subtasks']}")
        print(f"  Dependencies: {task.get('dependencies', 'None')}")
        print()


if __name__ == "__main__":
    main()
