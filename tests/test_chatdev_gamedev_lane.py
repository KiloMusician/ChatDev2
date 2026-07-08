import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.chatdev_gamedev_test_helpers import build_smoke_receipt_payload


class ChatdevGamedevLaneWrapperTests(unittest.TestCase):
    @staticmethod
    def _run_lane(*args: str) -> dict:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                "tools/chatdev_gamedev_lane.ps1",
                *args,
            ],
            cwd="C:\\dev\\active\\ChatDev2",
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        return json.loads(completed.stdout)

    @staticmethod
    def _write_latest_receipt(receipt_dir: Path, payload: dict) -> None:
        (receipt_dir / "latest.json").write_text(json.dumps(payload), encoding="utf-8")

    def test_doctor_json_returns_loaded_local_route_payload(self) -> None:
        payload = self._run_lane("doctor", "-Json")
        self.assertIn("summary", payload)
        self.assertIn("local_routes", payload)
        self.assertIn("gamedev_env", payload)
        self.assertTrue(payload["local_routes"]["loaded"])
        self.assertIn("local_app_loaded", payload["summary"])
        self.assertIn("local_app_bootable", payload["summary"])

    def test_status_compact_honors_custom_receipt_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_dir = Path(tmp)
            self._write_latest_receipt(
                receipt_dir,
                {
                    "session_name": "compact-status",
                    "status": "artifact_emitted",
                    "bounded_stop_reason": "artifact_threshold_reached",
                },
            )

            payload = self._run_lane("status-compact", "-ReceiptDir", str(receipt_dir))
            self.assertEqual(payload["contract_version"], 1)
            self.assertIn("callable", payload)
            self.assertIn("backend_requirements", payload)
            self.assertIn("operator_commands", payload)
            self.assertIn("smoke_status_compact", payload["operator_commands"])
            self.assertFalse(payload["backend_requirements"]["ollama_required_for_current_lane"])
            self.assertNotIn("latest_smoke", payload)

    def test_latest_and_status_compact_stay_aligned_on_core_receipt_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_dir = Path(tmp)
            self._write_latest_receipt(
                receipt_dir,
                build_smoke_receipt_payload(session_name="alignment-proof"),
            )

            latest_payload = self._run_lane("latest", "-ReceiptDir", str(receipt_dir))
            status_payload = self._run_lane("status-compact", "-ReceiptDir", str(receipt_dir))

            self.assertEqual(status_payload["workflow_used"], latest_payload["workflow_used"])
            self.assertEqual(status_payload["provider"], latest_payload["provider"])
            self.assertEqual(status_payload["model"], latest_payload["model"])
            self.assertEqual(status_payload["proven_smoke_model"], latest_payload["proven_smoke_model"])
            self.assertEqual(status_payload["attempted_model"], latest_payload["attempted_model"])
            self.assertEqual(status_payload["env_defaults"], latest_payload["env_defaults"])
            self.assertEqual(status_payload["output_path"], latest_payload["output_path"])
            self.assertEqual(status_payload["artifact_runtime_outcome"], latest_payload["artifact_runtime_outcome"])
            self.assertEqual(status_payload["runtime_proof_depth"], latest_payload["runtime_proof_depth"])
            self.assertEqual(status_payload["runtime_launch_proven"], latest_payload["runtime_launch_proven"])
            self.assertEqual(status_payload["runtime_completion_proven"], latest_payload["runtime_completion_proven"])

    def test_status_compact_and_status_full_stay_aligned_on_automation_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_dir = Path(tmp)
            self._write_latest_receipt(
                receipt_dir,
                build_smoke_receipt_payload(session_name="full-compact-alignment-proof"),
            )

            compact_payload = self._run_lane("status-compact", "-ReceiptDir", str(receipt_dir))
            full_payload = self._run_lane("status-full", "-ReceiptDir", str(receipt_dir))
            summary_payload = full_payload["automation_summary"]

            self.assertEqual(summary_payload["workflow_used"], compact_payload["workflow_used"])
            self.assertEqual(summary_payload["provider"], compact_payload["provider"])
            self.assertEqual(summary_payload["model"], compact_payload["model"])
            self.assertEqual(summary_payload["proven_smoke_model"], compact_payload["proven_smoke_model"])
            self.assertEqual(summary_payload["attempted_model"], compact_payload["attempted_model"])
            self.assertEqual(summary_payload["env_defaults"], compact_payload["env_defaults"])
            self.assertEqual(summary_payload["output_path"], compact_payload["output_path"])
            self.assertEqual(summary_payload["artifact_runtime_outcome"], compact_payload["artifact_runtime_outcome"])
            self.assertEqual(summary_payload["runtime_proof_depth"], compact_payload["runtime_proof_depth"])
            self.assertEqual(summary_payload["runtime_launch_proven"], compact_payload["runtime_launch_proven"])
            self.assertEqual(summary_payload["runtime_completion_proven"], compact_payload["runtime_completion_proven"])
            self.assertEqual(summary_payload["backend_requirements"], compact_payload["backend_requirements"])
            self.assertEqual(summary_payload["advisories"], compact_payload["advisories"])

    def test_status_full_honors_custom_receipt_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_dir = Path(tmp)
            self._write_latest_receipt(
                receipt_dir,
                {
                    "session_name": "status-full-proof",
                    "status": "artifact_emitted",
                    "bounded_stop_reason": "artifact_threshold_reached",
                },
            )

            payload = self._run_lane("status-full", "-ReceiptDir", str(receipt_dir))
            self.assertEqual(payload["latest_smoke"]["session_name"], "status-full-proof")
            self.assertEqual(payload["latest_smoke"]["status"], "artifact_emitted")
            self.assertIn("doctor_summary", payload)
            self.assertIn("assessment", payload)
            self.assertIn("automation_summary", payload)
            self.assertIn("backend_requirements", payload["automation_summary"])
            self.assertFalse(payload["automation_summary"]["backend_requirements"]["ollama_required_for_current_lane"])

    def test_local_status_json_returns_managed_payload_shape(self) -> None:
        payload = self._run_lane("local-status")
        self.assertIn("managed", payload)
        self.assertIn("health", payload)
        self.assertIn("base_url", payload)

    def test_local_proof_json_returns_bounded_local_payload(self) -> None:
        payload = self._run_lane("local-proof", "-Json")
        self.assertIn("summary", payload)
        self.assertIn("local_startup_probe", payload)
        self.assertIn("local_app_bootable", payload["summary"])
        self.assertIn("local_app_core_routes_ready", payload["summary"])
        self.assertIn("local_app_extended_routes_ready", payload["summary"])
        self.assertIn("next_action", payload)

    def test_latest_json_honors_custom_receipt_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_dir = Path(tmp)
            self._write_latest_receipt(
                receipt_dir,
                {
                    "session_name": "custom-latest",
                    "status": "artifact_emitted",
                    "bounded_stop_reason": "artifact_threshold_reached",
                },
            )

            payload = self._run_lane("latest", "-Json", "-ReceiptDir", str(receipt_dir))
            self.assertEqual(payload["session_name"], "custom-latest")
            self.assertTrue(payload["receipt_path"].endswith("latest.json"))

    def test_latest_full_honors_custom_receipt_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_dir = Path(tmp)
            self._write_latest_receipt(
                receipt_dir,
                {
                    "session_name": "custom-latest-full",
                    "status": "artifact_emitted",
                    "bounded_stop_reason": "artifact_threshold_reached",
                },
            )

            payload = self._run_lane("latest-full", "-ReceiptDir", str(receipt_dir))
            self.assertEqual(payload["session_name"], "custom-latest-full")
            self.assertTrue(payload["receipt_path"].endswith("latest.json"))


if __name__ == "__main__":
    unittest.main()
