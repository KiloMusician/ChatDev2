import subprocess
import unittest
from unittest import mock

from tools.chatdev_colony_doctor import _gamedev_env_probe, _python_capability_probe


class ChatDevColonyDoctorTests(unittest.TestCase):
    @mock.patch("tools.chatdev_colony_doctor.subprocess.run")
    def test_python_capability_probe_reports_pygame_truth(self, run_mock: mock.Mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess(
            args=["python", "-c", "..."],
            returncode=0,
            stdout="C:\\Python313\\python.exe\nTrue\n3.13.14\n",
            stderr="",
        )

        result = _python_capability_probe(["python"], timeout=1.0)

        self.assertTrue(result["ok"])
        self.assertEqual(result["executable"], "C:\\Python313\\python.exe")
        self.assertTrue(result["pygame"])
        self.assertEqual(result["python_version"], "3.13.14")

    @mock.patch("tools.chatdev_colony_doctor._gamedev_python_candidates")
    @mock.patch("tools.chatdev_colony_doctor._python_capability_probe")
    def test_gamedev_env_probe_labels_results(self, probe_mock: mock.Mock, candidates_mock: mock.Mock) -> None:
        candidates_mock.return_value = [
            {"label": "system_python", "command": ["python"]},
            {"label": "sandbox_venv", "command": ["C:\\sandbox\\python.exe"]},
        ]
        probe_mock.side_effect = [
            {"ok": True, "pygame": True, "python_version": "3.13.14"},
            {"ok": True, "pygame": False, "python_version": "3.14.0"},
        ]

        result = _gamedev_env_probe(timeout=1.5)

        self.assertEqual(
            result,
            [
                {
                    "label": "system_python",
                    "ok": True,
                    "pygame": True,
                    "python_version": "3.13.14",
                },
                {
                    "label": "sandbox_venv",
                    "ok": True,
                    "pygame": False,
                    "python_version": "3.14.0",
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
