import subprocess
import unittest
from unittest import mock

from tools.chatdev_colony_doctor import (
    STARTUP_ROUTE_TIMEOUTS,
    _gamedev_env_probe,
    _python_capability_probe,
    build_local_proof,
    build_report,
)


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

    @mock.patch("tools.chatdev_colony_doctor._gamedev_env_probe")
    @mock.patch("tools.chatdev_colony_doctor._local_app_startup_probe")
    @mock.patch("tools.chatdev_colony_doctor._local_routes")
    @mock.patch("tools.chatdev_colony_doctor._probe")
    @mock.patch("tools.chatdev_colony_doctor._tcp_reachable")
    def test_build_report_surfaces_local_app_bootable_when_not_live(
        self,
        tcp_mock: mock.Mock,
        probe_mock: mock.Mock,
        local_routes_mock: mock.Mock,
        startup_mock: mock.Mock,
        gamedev_mock: mock.Mock,
    ) -> None:
        tcp_mock.return_value = {"ok": False, "host": "localhost", "port": 6400}
        probe_mock.return_value = {"ok": False, "skipped": True, "reason": "tcp_unreachable"}
        local_routes_mock.return_value = {"loaded": True, "important": {}, "routes": []}
        startup_mock.return_value = {
            "ok": True,
            "port": 6410,
            "health_url": "http://127.0.0.1:6410/health",
            "paths": {
                "/health": {"ok": True},
                "/api/health": {"ok": True},
                "/api/bridge/status": {"ok": False, "error": "timed out"},
                "/api/ecosystem/status": {"ok": False, "error": "timed out"},
            },
        }
        gamedev_mock.return_value = []

        report = build_report(timeout=1.0)

        self.assertFalse(report["summary"]["chatdev_local_health"])
        self.assertTrue(report["summary"]["local_app_loaded"])
        self.assertTrue(report["summary"]["local_app_bootable"])
        self.assertTrue(report["summary"]["local_app_core_routes_ready"])
        self.assertFalse(report["summary"]["local_app_extended_routes_ready"])
        self.assertTrue(report["local_startup_probe"]["ok"])

    @mock.patch("tools.chatdev_colony_doctor._gamedev_env_probe")
    @mock.patch("tools.chatdev_colony_doctor._local_routes")
    @mock.patch("tools.chatdev_colony_doctor._probe")
    @mock.patch("tools.chatdev_colony_doctor._startup_probe_port")
    @mock.patch("tools.chatdev_colony_doctor._tcp_reachable")
    def test_build_report_uses_longer_timeout_budget_for_extended_startup_routes(
        self,
        tcp_mock: mock.Mock,
        startup_port_mock: mock.Mock,
        probe_mock: mock.Mock,
        local_routes_mock: mock.Mock,
        gamedev_mock: mock.Mock,
    ) -> None:
        tcp_mock.return_value = {"ok": False, "host": "localhost", "port": 6400}
        startup_port_mock.return_value = 6410
        local_routes_mock.return_value = {"loaded": True, "important": {}, "routes": []}
        gamedev_mock.return_value = []

        captured_timeouts: list[tuple[str, float]] = []

        def probe_side_effect(url: str, timeout: float) -> dict:
            captured_timeouts.append((url, timeout))
            if url.endswith("/health"):
                return {"ok": True}
            return {"ok": True, "status": 200}

        probe_mock.side_effect = probe_side_effect

        with mock.patch("tools.chatdev_colony_doctor.subprocess.Popen") as popen_mock:
            process_mock = mock.Mock()
            process_mock.poll.return_value = None
            process_mock.stdout = mock.Mock()
            process_mock.stdout.read.return_value = ""
            popen_mock.return_value = process_mock

            report = build_report(timeout=1.0)

        self.assertTrue(report["summary"]["local_app_extended_routes_ready"])
        timeout_by_suffix = {url.split("127.0.0.1:6410", 1)[-1]: timeout for url, timeout in captured_timeouts if "127.0.0.1:6410" in url}
        self.assertEqual(timeout_by_suffix["/health"], 1.0)
        self.assertEqual(timeout_by_suffix["/api/health"], STARTUP_ROUTE_TIMEOUTS["/api/health"])
        self.assertEqual(timeout_by_suffix["/api/bridge/status"], STARTUP_ROUTE_TIMEOUTS["/api/bridge/status"])
        self.assertEqual(timeout_by_suffix["/api/ecosystem/status"], STARTUP_ROUTE_TIMEOUTS["/api/ecosystem/status"])

    @mock.patch("tools.chatdev_colony_doctor.build_report")
    def test_build_local_proof_returns_bounded_local_summary(self, build_report_mock: mock.Mock) -> None:
        build_report_mock.return_value = {
            "generated_at": "2026-07-02T03:11:29Z",
            "root": "C:\\dev\\active\\ChatDev2",
            "summary": {
                "chatdev_local_health": False,
                "local_app_loaded": True,
                "local_app_bootable": True,
                "local_app_core_routes_ready": True,
                "local_app_extended_routes_ready": True,
            },
            "local_startup_probe": {"ok": True, "port": 6410},
        }

        proof = build_local_proof(timeout=1.0)

        self.assertEqual(proof["root"], "C:\\dev\\active\\ChatDev2")
        self.assertFalse(proof["summary"]["chatdev_local_health"])
        self.assertTrue(proof["summary"]["local_app_bootable"])
        self.assertTrue(proof["summary"]["local_app_extended_routes_ready"])
        self.assertEqual(proof["next_action"], "start_local_devall_app")
        self.assertTrue(proof["local_startup_probe"]["ok"])


if __name__ == "__main__":
    unittest.main()
