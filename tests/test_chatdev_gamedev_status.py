import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class ChatdevGamedevStatusTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
