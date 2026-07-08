import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import local_devall_app


class LocalDevallAppTests(unittest.TestCase):
    def test_local_status_reports_unmanaged_when_state_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "local_devall_app.json"
            with mock.patch.object(local_devall_app, "STATE_PATH", state_path):
                with mock.patch.object(local_devall_app, "_probe_health", return_value={"ok": False, "error": "refused"}):
                    payload = local_devall_app.local_status()

        self.assertFalse(payload["managed"])
        self.assertIsNone(payload["pid"])
        self.assertFalse(payload["health"]["ok"])

    def test_start_local_app_returns_already_running_when_health_is_live(self) -> None:
        with mock.patch.object(local_devall_app, "local_status", return_value={"health": {"ok": True}, "managed": False}):
            payload = local_devall_app.start_local_app(timeout=1.0)

        self.assertEqual(payload["status"], "already_running")

    def test_build_stop_local_app_returns_not_managed_without_state(self) -> None:
        with mock.patch.object(local_devall_app, "local_status", return_value={"managed": False, "pid": None, "health": {"ok": False}}):
            payload = local_devall_app.stop_local_app(timeout=1.0)

        self.assertEqual(payload["status"], "not_managed")


if __name__ == "__main__":
    unittest.main()
