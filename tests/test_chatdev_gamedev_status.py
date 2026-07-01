import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.chatdev_gamedev_status import _build_assessment


class ChatdevGamedevStatusTests(unittest.TestCase):
    def test_build_assessment_marks_ready_with_gaps_for_worker_only_surface(self) -> None:
        doctor = {
            "summary": {
                "chatdev_colony_health": True,
                "chatdev_local_health": False,
                "live_surface_id": "devmentor-chatdev-worker",
                "gamedev_python_with_pygame": ["repo_gamedev_venv"],
            },
            "probes": {
                "litellm": {
                    "paths": {
                        "/v1/models": {"ok": True},
                    }
                }
            },
        }
        latest = {"status": "artifact_emitted"}
        yaml_validation = {"ok": True}

        assessment = _build_assessment(doctor, latest, yaml_validation)

        self.assertEqual(assessment["overall_status"], "ready_with_gaps")
        self.assertTrue(assessment["bounded_smoke_ok"])
        self.assertTrue(assessment["yaml_validation_ok"])
        self.assertTrue(assessment["litellm_ok"])
        self.assertTrue(assessment["repo_gamedev_runtime_ok"])
        self.assertEqual(assessment["live_surface_mode"], "worker_only")
        self.assertEqual(assessment["next_action"], "start_local_devall_app")
        self.assertIn("chatdev_local_offline", assessment["gaps"])
        self.assertIn("live_surface_is_queue_worker_not_devall_app", assessment["gaps"])

    def test_build_assessment_marks_degraded_when_yaml_validation_is_not_proven(self) -> None:
        doctor = {
            "summary": {
                "chatdev_colony_health": True,
                "chatdev_local_health": True,
                "live_surface_id": "devmentor-chatdev-worker",
                "gamedev_python_with_pygame": ["repo_gamedev_venv"],
            },
            "probes": {
                "litellm": {
                    "paths": {
                        "/v1/models": {"ok": True},
                    }
                }
            },
        }
        latest = {"status": "artifact_emitted"}
        yaml_validation = {"ok": False}

        assessment = _build_assessment(doctor, latest, yaml_validation)

        self.assertEqual(assessment["overall_status"], "degraded")
        self.assertFalse(assessment["yaml_validation_ok"])
        self.assertEqual(assessment["next_action"], "run_validate_yamls")
        self.assertIn("yaml_validation_not_proven", assessment["gaps"])

    def test_status_json_honors_custom_receipt_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_dir = Path(tmp)
            (receipt_dir / "latest.json").write_text(
                json.dumps(
                    {
                        "session_name": "status-proof",
                        "status": "artifact_emitted",
                        "bounded_stop_reason": "artifact_threshold_reached",
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    "tools/chatdev_gamedev_lane.ps1",
                    "status",
                    "-ReceiptDir",
                    str(receipt_dir),
                ],
                cwd="C:\\dev\\active\\ChatDev2",
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["latest_smoke"]["session_name"], "status-proof")
            self.assertEqual(payload["latest_smoke"]["status"], "artifact_emitted")
            self.assertEqual(payload["latest_smoke"]["bounded_stop_reason"], "artifact_threshold_reached")
            self.assertIn("doctor_summary", payload)
            self.assertIn("yaml_validation", payload)
            self.assertIn("assessment", payload)


if __name__ == "__main__":
    unittest.main()
