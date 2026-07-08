import asyncio
import unittest
from unittest import mock

from server.routes import ecosystem


class EcosystemRouteTests(unittest.TestCase):
    @mock.patch("server.routes.ecosystem.subprocess.check_output")
    def test_repo_info_skips_size_probe_when_include_size_false(self, check_output_mock: mock.Mock) -> None:
        repo_name = "Dev-Mentor"
        repo_path = ecosystem.ECOSYSTEM_DIR / repo_name

        original_exists = ecosystem.Path.exists

        def exists_side_effect(path_self: ecosystem.Path) -> bool:
            if path_self == repo_path:
                return True
            return original_exists(path_self)

        check_output_mock.side_effect = [
            b"main\n",
            b"abc123 test commit\n",
        ]

        with mock.patch.object(ecosystem.Path, "exists", autospec=True, side_effect=exists_side_effect):
            result = ecosystem._repo_info(repo_name, include_size=False)

        self.assertTrue(result["cloned"])
        self.assertEqual(result["branch"], "main")
        self.assertEqual(result["latest_commit"], "abc123 test commit")
        self.assertNotIn("size_mb", result)
        commands = [call.args[0] for call in check_output_mock.call_args_list]
        self.assertEqual(commands, [["git", "branch", "--show-current"], ["git", "log", "-1", "--format=%h %s"]])

    @mock.patch("server.routes.ecosystem._repo_info")
    @mock.patch("server.routes.ecosystem._probe")
    def test_ecosystem_status_returns_summary_with_lightweight_repo_info(
        self,
        probe_mock: mock.Mock,
        repo_info_mock: mock.Mock,
    ) -> None:
        probe_mock.side_effect = [
            {"online": True, "status_code": 200},
            {"online": False, "error": "timed out"},
            {"online": True, "status_code": 200},
            {"online": False, "error": "timed out"},
        ]
        repo_info_mock.return_value = {"cloned": True, "branch": "main"}

        payload = asyncio.run(ecosystem.ecosystem_status())

        self.assertEqual(payload["summary"]["online"], 2)
        self.assertEqual(payload["summary"]["cli_mode"], 2)
        self.assertEqual(payload["summary"]["total"], len(ecosystem.SERVICES))
        self.assertEqual(len(payload["services"]), len(ecosystem.SERVICES))
        self.assertTrue(all(call.kwargs.get("include_size") is False for call in repo_info_mock.call_args_list))


if __name__ == "__main__":
    unittest.main()
