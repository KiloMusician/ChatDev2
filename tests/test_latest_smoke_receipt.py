import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class LatestSmokeReceiptTests(unittest.TestCase):
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
