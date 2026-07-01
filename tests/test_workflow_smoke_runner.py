import tempfile
import unittest
from pathlib import Path

from tools.workflow_smoke_runner import (
    _list_workspace_artifacts,
    _resolve_yaml_path,
    _summarize_token_progress,
)


class WorkflowSmokeRunnerTests(unittest.TestCase):
    def test_resolve_yaml_path_prefers_repo_and_then_yaml_instance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()

            direct = repo_root / "custom.yaml"
            direct.write_text("graph: {}", encoding="utf-8")

            yaml_instance = repo_root / "yaml_instance"
            yaml_instance.mkdir()
            nested = yaml_instance / "ChatDev_v1.yaml"
            nested.write_text("graph: {}", encoding="utf-8")

            self.assertEqual(_resolve_yaml_path(repo_root, "custom.yaml"), direct)
            self.assertEqual(_resolve_yaml_path(repo_root, "ChatDev_v1.yaml"), nested)

    def test_list_workspace_artifacts_ignores_bootstrap_noise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "WareHouse" / "smoke_run"
            workspace = output_dir / "code_workspace"
            workspace.mkdir(parents=True)

            (workspace / "hello.py").write_text("print('hello')", encoding="utf-8")
            (workspace / "pyproject.toml").write_text("[project]", encoding="utf-8")
            (workspace / "uv.lock").write_text("lock", encoding="utf-8")

            attachment_dir = workspace / "attachments"
            attachment_dir.mkdir()
            (attachment_dir / "notes.txt").write_text("ignore me", encoding="utf-8")

            hidden_dir = workspace / ".venv" / "Lib"
            hidden_dir.mkdir(parents=True)
            (hidden_dir / "site.py").write_text("ignore me", encoding="utf-8")

            nested = workspace / "src"
            nested.mkdir()
            (nested / "main.py").write_text("print('main')", encoding="utf-8")

            artifacts = _list_workspace_artifacts(output_dir)

            self.assertEqual(
                [item["relative_path"] for item in artifacts],
                [
                    "code_workspace/hello.py",
                    "code_workspace/src/main.py",
                ],
            )

    def test_summarize_token_progress_reports_completed_and_active_nodes(self) -> None:
        token_usage = {
            "call_history": [
                {"node_id": "Game Designer"},
                {"node_id": "Planner"},
            ]
        }

        progress = _summarize_token_progress(token_usage, "Core_Developer")

        self.assertEqual(
            progress,
            {
                "last_completed_node": "Planner",
                "last_active_node": "Core_Developer",
            },
        )


if __name__ == "__main__":
    unittest.main()
