import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.latest_smoke_receipt import _build_latest_summary_payload


class LatestSmokeReceiptTests(unittest.TestCase):
    def test_build_latest_summary_payload_exposes_shared_contract_fields(self) -> None:
        payload = _build_latest_summary_payload(
            {
                "session_name": "shared-summary",
                "status": "artifact_emitted",
                "bounded_stop_reason": "artifact_threshold_reached",
                "repo_root": r"C:\dev\_sandboxes\chatdev-factory-prototype-smoke",
                "first_artifact_path": r"WareHouse\proof\code_workspace\game.py",
                "yaml_file": r"C:\dev\active\ChatDev2\yaml_instance\GameDev_mechanic_smoke.yaml",
                "runtime_python": r"C:\dev\active\ChatDev2\.venv-gamedev313\Scripts\python.exe",
                "override_model": "ecosystem-devstral",
                "env_defaults": {
                    "BASE_URL": "http://127.0.0.1:4000/v1",
                    "API_KEY": "ollama-local-model",
                },
                "token_usage": {
                    "model_usages": {"ecosystem-coder-fast": {"total_tokens": 123}},
                    "call_history": [
                        {
                            "provider": "openai",
                            "model_name": "ecosystem-coder-fast",
                        }
                    ],
                },
                "artifact_runtime_validation": [
                    {
                        "relative_path": "code_workspace/game.py",
                        "valid": True,
                        "outcome": "completed",
                    }
                ],
            },
            receipt_path=Path(r"C:\dev\_sandboxes\chatdev-factory-prototype-smoke\WareHouse\_smoke_receipts\latest.json"),
        )

        self.assertEqual(payload["workflow_used"], r"C:\dev\active\ChatDev2\yaml_instance\GameDev_mechanic_smoke.yaml")
        self.assertEqual(payload["provider"], "openai")
        self.assertEqual(payload["model"], "ecosystem-coder-fast")
        self.assertEqual(payload["proven_smoke_model"], "ecosystem-coder-fast")
        self.assertEqual(payload["attempted_model"], "ecosystem-devstral")
        self.assertEqual(payload["env_defaults"]["BASE_URL"], "http://127.0.0.1:4000/v1")
        self.assertEqual(
            payload["output_path"],
            r"C:\dev\_sandboxes\chatdev-factory-prototype-smoke\WareHouse\proof\code_workspace\game.py",
        )
        self.assertEqual(payload["artifact_runtime_outcome"], "completed")
        self.assertEqual(payload["runtime_proof_depth"], "completed")
        self.assertTrue(payload["runtime_launch_proven"])
        self.assertTrue(payload["runtime_completion_proven"])

    def test_summary_returns_latest_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_dir = Path(tmp)
            older = receipt_dir / "older.json"
            newer = receipt_dir / "newer.json"

            older.write_text(json.dumps({"session_name": "older", "status": "artifact_emitted"}), encoding="utf-8")
            newer.write_text(
                json.dumps(
                    {
                        "session_name": "newer",
                        "status": "artifact_emitted",
                        "bounded_stop_reason": "artifact_threshold_reached",
                        "repo_root": r"C:\dev\_sandboxes\chatdev-factory-prototype-smoke",
                        "first_artifact_path": r"WareHouse\proof\code_workspace\game.py",
                        "yaml_file": r"C:\dev\active\ChatDev2\yaml_instance\GameDev_mechanic_smoke.yaml",
                        "runtime_python": r"C:\dev\active\ChatDev2\.venv-gamedev313\Scripts\python.exe",
                        "override_model": "ecosystem-devstral",
                        "env_defaults": {
                            "BASE_URL": "http://127.0.0.1:4000/v1",
                            "API_KEY": "ollama-local-model",
                        },
                        "token_usage": {
                            "model_usages": {"ecosystem-coder-fast": {"total_tokens": 123}},
                            "call_history": [
                                {
                                    "provider": "openai",
                                    "model_name": "ecosystem-coder-fast",
                                }
                            ],
                        },
                        "artifact_runtime_validation": [
                            {
                                "relative_path": "code_workspace/game.py",
                                "valid": True,
                                "outcome": "timed_out_after_launch",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            older.touch()
            newer.touch()

            completed = subprocess.run(
                [
                    "python",
                    "tools/latest_smoke_receipt.py",
                    "--receipt-dir",
                    str(receipt_dir),
                    "--summary",
                ],
                cwd="C:\\dev\\active\\ChatDev2",
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["session_name"], "newer")
            self.assertEqual(payload["bounded_stop_reason"], "artifact_threshold_reached")
            self.assertTrue(payload["receipt_path"].endswith("newer.json"))
            self.assertTrue(payload["result_json"].endswith("newer.json"))
            self.assertEqual(payload["workflow_used"], r"C:\dev\active\ChatDev2\yaml_instance\GameDev_mechanic_smoke.yaml")
            self.assertEqual(payload["provider"], "openai")
            self.assertEqual(payload["model"], "ecosystem-coder-fast")
            self.assertEqual(payload["proven_smoke_model"], "ecosystem-coder-fast")
            self.assertEqual(payload["attempted_model"], "ecosystem-devstral")
            self.assertEqual(payload["env_defaults"]["API_KEY"], "ollama-local-model")
            self.assertEqual(
                payload["output_path"],
                r"C:\dev\_sandboxes\chatdev-factory-prototype-smoke\WareHouse\proof\code_workspace\game.py",
            )
            self.assertEqual(payload["artifact_runtime_outcome"], "timed_out_after_launch")
            self.assertEqual(payload["runtime_proof_depth"], "launch_only")
            self.assertTrue(payload["runtime_launch_proven"])
            self.assertFalse(payload["runtime_completion_proven"])

    def test_prefers_stable_latest_pointer_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_dir = Path(tmp)
            (receipt_dir / "older.json").write_text(
                json.dumps({"session_name": "older", "status": "artifact_emitted"}),
                encoding="utf-8",
            )
            latest_pointer = receipt_dir / "latest.json"
            latest_pointer.write_text(
                json.dumps(
                    {
                        "session_name": "stable-latest",
                        "status": "artifact_emitted",
                        "bounded_stop_reason": "artifact_threshold_reached",
                        "artifact_runtime_validation": [
                            {
                                "relative_path": "code_workspace/game.py",
                                "valid": True,
                                "outcome": "completed",
                            }
                        ],
                        "override_model": "ecosystem-devstral",
                        "env_defaults": {
                            "BASE_URL": "http://127.0.0.1:4000/v1",
                            "API_KEY": "ollama-local-model",
                        },
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "python",
                    "tools/latest_smoke_receipt.py",
                    "--receipt-dir",
                    str(receipt_dir),
                    "--summary",
                ],
                cwd="C:\\dev\\active\\ChatDev2",
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["session_name"], "stable-latest")
            self.assertTrue(payload["receipt_path"].endswith("latest.json"))
            self.assertIsNone(payload["proven_smoke_model"])
            self.assertEqual(payload["attempted_model"], "ecosystem-devstral")
            self.assertEqual(payload["env_defaults"]["BASE_URL"], "http://127.0.0.1:4000/v1")
            self.assertEqual(payload["runtime_proof_depth"], "completed")
            self.assertTrue(payload["runtime_launch_proven"])
            self.assertTrue(payload["runtime_completion_proven"])

    def test_missing_directory_returns_nonzero_missing_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"

            completed = subprocess.run(
                [
                    "python",
                    "tools/latest_smoke_receipt.py",
                    "--receipt-dir",
                    str(missing),
                ],
                cwd="C:\\dev\\active\\ChatDev2",
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertEqual(completed.returncode, 1)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "missing")
            self.assertEqual(payload["receipt_dir"], str(missing.resolve()))


if __name__ == "__main__":
    unittest.main()
