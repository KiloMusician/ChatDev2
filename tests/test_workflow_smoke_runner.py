import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools.workflow_smoke_runner import (
    _list_workspace_artifacts,
    _node_progress_reached,
    _override_openai_node_models,
    _resolve_final_status,
    _resolve_yaml_path,
    _runtime_validate_python_artifacts,
    _summarize_token_progress,
    _validate_python_artifacts,
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

    def test_validate_python_artifacts_reports_valid_and_invalid_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "WareHouse" / "smoke_run"
            workspace = output_dir / "code_workspace"
            workspace.mkdir(parents=True)

            valid_file = workspace / "game.py"
            valid_file.write_text("print('ok')\n", encoding="utf-8")

            invalid_file = workspace / "broken.py"
            invalid_file.write_text("def nope(:\n    pass\n", encoding="utf-8")

            validations = _validate_python_artifacts(
                output_dir,
                [
                    {"relative_path": "code_workspace/game.py"},
                    {"relative_path": "code_workspace/broken.py"},
                    {"relative_path": "code_workspace/readme.md"},
                ],
            )

            self.assertEqual(
                validations,
                [
                    {"relative_path": "code_workspace/game.py", "valid": True},
                    {
                        "relative_path": "code_workspace/broken.py",
                        "valid": False,
                        "error": "invalid syntax",
                        "line": 1,
                        "offset": 10,
                    },
                ],
            )

    @mock.patch("tools.workflow_smoke_runner.subprocess.run")
    def test_runtime_validate_python_artifacts_accepts_timeout_as_launch_success(self, run_mock: mock.Mock) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "WareHouse" / "smoke_run"
            workspace = output_dir / "code_workspace"
            workspace.mkdir(parents=True)
            script = workspace / "game.py"
            script.write_text("while True:\n    pass\n", encoding="utf-8")

            timeout_exc = subprocess.TimeoutExpired(
                cmd=["python", str(script)],
                timeout=3.0,
                output="boot ok",
                stderr="",
            )
            run_mock.side_effect = timeout_exc

            validations = _runtime_validate_python_artifacts(
                output_dir,
                [{"relative_path": "code_workspace/game.py"}],
                runtime_python="python",
                timeout_seconds=3.0,
            )

            self.assertEqual(
                validations,
                [
                    {
                        "relative_path": "code_workspace/game.py",
                        "valid": True,
                        "outcome": "timed_out_after_launch",
                        "timeout_seconds": 3.0,
                        "stdout_tail": "boot ok",
                        "stderr_tail": "",
                    }
                ],
            )

    @mock.patch("tools.workflow_smoke_runner.subprocess.run")
    def test_runtime_validate_python_artifacts_reports_nonzero_exit(self, run_mock: mock.Mock) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "WareHouse" / "smoke_run"
            workspace = output_dir / "code_workspace"
            workspace.mkdir(parents=True)
            script = workspace / "broken.py"
            script.write_text("raise SystemExit(1)\n", encoding="utf-8")

            run_mock.return_value = subprocess.CompletedProcess(
                args=["python", str(script)],
                returncode=1,
                stdout="",
                stderr="Traceback...",
            )

            validations = _runtime_validate_python_artifacts(
                output_dir,
                [{"relative_path": "code_workspace/broken.py"}],
                runtime_python="python",
                timeout_seconds=2.0,
            )

            self.assertEqual(
                validations,
                [
                    {
                        "relative_path": "code_workspace/broken.py",
                        "valid": False,
                        "outcome": "exited_nonzero",
                        "returncode": 1,
                        "stdout_tail": "",
                        "stderr_tail": "Traceback...",
                    }
                ],
            )
            run_mock.assert_called_once()
            invoked_cmd = run_mock.call_args.args[0]
            invoked_kwargs = run_mock.call_args.kwargs
            self.assertEqual(invoked_cmd[0], "python")
            self.assertEqual(invoked_cmd[1], "broken.py")
            self.assertEqual(invoked_kwargs["cwd"], str(script.parent))

    def test_node_progress_reached_matches_requested_thresholds(self) -> None:
        token_progress = {
            "last_completed_node": "Game Designer",
            "last_active_node": "Planner",
        }

        self.assertTrue(
            _node_progress_reached(
                token_progress,
                stop_on_active_node="Planner",
                stop_on_completed_node=None,
            )
        )
        self.assertTrue(
            _node_progress_reached(
                token_progress,
                stop_on_active_node=None,
                stop_on_completed_node="Game Designer",
            )
        )
        self.assertFalse(
            _node_progress_reached(
                token_progress,
                stop_on_active_node="Core_Developer",
                stop_on_completed_node="Polish_Developer",
            )
        )

    def test_resolve_final_status_treats_cancelled_artifact_threshold_as_success(self) -> None:
        status = _resolve_final_status(
            state_status="error",
            artifacts=[{"relative_path": "code_workspace/game.py"}],
            artifact_stop_requested=True,
            node_progress_stop_requested=False,
            cancel_requested=True,
            exception_type="WorkflowCancelledError",
        )

        self.assertEqual(status, "artifact_emitted")

    def test_override_openai_node_models_updates_only_openai_nodes(self) -> None:
        graph_definition = {
            "nodes": [
                {"id": "A", "config": {"provider": "openai", "name": "old-a"}},
                {"id": "B", "config": {"provider": "gemini", "name": "old-b"}},
                {"id": "C", "config": {"provider": "openai", "name": "old-c"}},
                {"id": "D", "config": "invalid"},
            ]
        }

        updated = _override_openai_node_models(graph_definition, "ecosystem-qwen")

        self.assertEqual(updated, 2)
        self.assertEqual(graph_definition["nodes"][0]["config"]["name"], "ecosystem-qwen")
        self.assertEqual(graph_definition["nodes"][1]["config"]["name"], "old-b")
        self.assertEqual(graph_definition["nodes"][2]["config"]["name"], "ecosystem-qwen")

    def test_override_openai_node_models_updates_object_graph_definitions(self) -> None:
        graph_definition = SimpleNamespace(
            nodes=[
                SimpleNamespace(config=SimpleNamespace(provider="openai", name="old-a")),
                SimpleNamespace(config=SimpleNamespace(provider="anthropic", name="old-b")),
            ]
        )

        updated = _override_openai_node_models(graph_definition, "ecosystem-auto")

        self.assertEqual(updated, 1)
        self.assertEqual(graph_definition.nodes[0].config.name, "ecosystem-auto")
        self.assertEqual(graph_definition.nodes[1].config.name, "old-b")


if __name__ == "__main__":
    unittest.main()
