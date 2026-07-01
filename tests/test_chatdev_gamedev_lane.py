import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class ChatdevGamedevLaneWrapperTests(unittest.TestCase):
    def test_latest_json_honors_custom_receipt_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_dir = Path(tmp)
            (receipt_dir / "latest.json").write_text(
                json.dumps(
                    {
                        "session_name": "custom-latest",
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
                    "latest",
                    "-Json",
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
            self.assertEqual(payload["session_name"], "custom-latest")
            self.assertTrue(payload["receipt_path"].endswith("latest.json"))


if __name__ == "__main__":
    unittest.main()
