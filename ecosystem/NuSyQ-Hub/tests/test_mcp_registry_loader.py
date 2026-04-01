"""Tests for src/integration/mcp_registry_loader.py — MCPServerConfig and MCPRegistryLoader."""

import json
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# MCPServerConfig dataclass
# ---------------------------------------------------------------------------


class TestMCPServerConfig:
    """Tests for MCPServerConfig dataclass."""

    def _make(self, **kwargs):
        from src.integration.mcp_registry_loader import MCPServerConfig
        defaults = {
            "id": "test-server",
            "description": "A test MCP server",
            "command": ["python", "-m", "mcp_server"],
            "env": {},
            "tags": ["test"],
            "requires": [],
        }
        defaults.update(kwargs)
        return MCPServerConfig(**defaults)

    def test_instantiation(self):
        assert self._make() is not None

    def test_fields_stored(self):
        cfg = self._make(id="my-server", description="My desc")
        assert cfg.id == "my-server"
        assert cfg.description == "My desc"

    def test_default_process_none(self):
        assert self._make().process is None

    def test_from_dict_basic(self):
        from src.integration.mcp_registry_loader import MCPServerConfig
        data = {
            "id": "chatdev",
            "description": "ChatDev MCP",
            "command": ["python", "chatdev.py"],
            "env": {"PORT": "8081"},
            "tags": ["ai", "chatdev"],
            "requires": ["chatdev_mcp_enabled"],
        }
        cfg = MCPServerConfig.from_dict(data)
        assert cfg.id == "chatdev"
        assert cfg.command == ["python", "chatdev.py"]
        assert cfg.env == {"PORT": "8081"}
        assert cfg.requires == ["chatdev_mcp_enabled"]

    def test_from_dict_missing_fields_use_defaults(self):
        from src.integration.mcp_registry_loader import MCPServerConfig
        cfg = MCPServerConfig.from_dict({"id": "partial"})
        assert cfg.id == "partial"
        assert cfg.description == ""
        assert cfg.command == []
        assert cfg.env == {}
        assert cfg.tags == []
        assert cfg.requires == []

    def test_from_dict_empty_dict(self):
        from src.integration.mcp_registry_loader import MCPServerConfig
        cfg = MCPServerConfig.from_dict({})
        assert cfg.id == ""


# ---------------------------------------------------------------------------
# MCPRegistryLoader init and registry loading
# ---------------------------------------------------------------------------


class TestMCPRegistryLoaderInit:
    """Tests for MCPRegistryLoader initialization."""

    def _make_registry_file(self, tmp_path, data):
        f = tmp_path / "mcp_registry.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        return f

    def test_instantiation_with_missing_file(self, tmp_path):
        from src.integration.mcp_registry_loader import MCPRegistryLoader
        loader = MCPRegistryLoader(registry_path=tmp_path / "nonexistent.json")
        assert loader is not None
        assert loader.servers == {}

    def test_instantiation_with_empty_list(self, tmp_path):
        from src.integration.mcp_registry_loader import MCPRegistryLoader
        registry = self._make_registry_file(tmp_path, [])
        loader = MCPRegistryLoader(registry_path=registry)
        assert loader.servers == {}

    def test_instantiation_with_one_server(self, tmp_path):
        from src.integration.mcp_registry_loader import MCPRegistryLoader
        data = [{"id": "srv1", "description": "Server 1", "command": ["echo"], "env": {}, "tags": [], "requires": []}]
        registry = self._make_registry_file(tmp_path, data)
        loader = MCPRegistryLoader(registry_path=registry)
        assert "srv1" in loader.servers

    def test_instantiation_with_multiple_servers(self, tmp_path):
        from src.integration.mcp_registry_loader import MCPRegistryLoader
        data = [
            {"id": "s1", "description": "", "command": ["a"], "env": {}, "tags": [], "requires": []},
            {"id": "s2", "description": "", "command": ["b"], "env": {}, "tags": [], "requires": []},
        ]
        registry = self._make_registry_file(tmp_path, data)
        loader = MCPRegistryLoader(registry_path=registry)
        assert len(loader.servers) == 2

    def test_active_servers_empty_on_init(self, tmp_path):
        from src.integration.mcp_registry_loader import MCPRegistryLoader
        loader = MCPRegistryLoader(registry_path=tmp_path / "nope.json")
        assert loader.active_servers == {}

    def test_invalid_json_graceful(self, tmp_path):
        from src.integration.mcp_registry_loader import MCPRegistryLoader
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{not valid json", encoding="utf-8")
        loader = MCPRegistryLoader(registry_path=bad_file)
        assert loader.servers == {}


# ---------------------------------------------------------------------------
# MCPRegistryLoader.check_feature_flags
# ---------------------------------------------------------------------------


class TestCheckFeatureFlags:
    """Tests for check_feature_flags()."""

    def _make_loader(self, tmp_path):
        from src.integration.mcp_registry_loader import MCPRegistryLoader
        return MCPRegistryLoader(registry_path=tmp_path / "nope.json")

    def _make_server(self, requires=None):
        from src.integration.mcp_registry_loader import MCPServerConfig
        return MCPServerConfig(
            id="test", description="", command=["echo"], env={}, tags=[], requires=requires or []
        )

    def test_no_requires_returns_true_when_mgr_available(self, tmp_path):
        loader = self._make_loader(tmp_path)
        server = self._make_server(requires=[])
        mock_mgr = MagicMock()
        mock_mgr.is_feature_enabled.return_value = True
        # get_feature_flag_manager is a local import — patch at its source
        with patch("src.config.feature_flag_manager.get_feature_flag_manager", return_value=mock_mgr):
            result = loader.check_feature_flags(server)
        assert result is True

    def test_required_flag_disabled_returns_false(self, tmp_path):
        loader = self._make_loader(tmp_path)
        server = self._make_server(requires=["chatdev_mcp_enabled"])
        mock_mgr = MagicMock()
        mock_mgr.is_feature_enabled.return_value = False
        with patch("src.config.feature_flag_manager.get_feature_flag_manager", return_value=mock_mgr):
            result = loader.check_feature_flags(server)
        assert result is False

    def test_exception_in_flag_check_returns_false(self, tmp_path):
        loader = self._make_loader(tmp_path)
        server = self._make_server(requires=["some_flag"])
        # If the flag manager raises any exception, check_feature_flags returns False
        mock_mgr = MagicMock()
        mock_mgr.is_feature_enabled.side_effect = RuntimeError("mgr error")
        with patch("src.config.feature_flag_manager.get_feature_flag_manager", return_value=mock_mgr):
            result = loader.check_feature_flags(server)
        assert result is False


# ---------------------------------------------------------------------------
# MCPRegistryLoader.validate_server
# ---------------------------------------------------------------------------


class TestValidateServer:
    """Tests for validate_server()."""

    def _make_loader(self, tmp_path):
        from src.integration.mcp_registry_loader import MCPRegistryLoader
        return MCPRegistryLoader(registry_path=tmp_path / "nope.json")

    def _make_server(self, requires=None, command=None):
        from src.integration.mcp_registry_loader import MCPServerConfig
        # Use explicit sentinel check so an empty list [] is NOT replaced by ["echo"]
        cmd = ["echo"] if command is None else command
        reqs = [] if requires is None else requires
        return MCPServerConfig(id="test", description="", command=cmd, env={}, tags=[], requires=reqs)

    def test_empty_command_returns_false(self, tmp_path):
        loader = self._make_loader(tmp_path)
        server = self._make_server(command=[])
        with patch.object(loader, "check_feature_flags", return_value=True):
            result = loader.validate_server(server)
        assert result is False

    def test_valid_command_and_flags_returns_true(self, tmp_path):
        loader = self._make_loader(tmp_path)
        server = self._make_server(command=["echo", "hello"])
        with patch.object(loader, "check_feature_flags", return_value=True):
            result = loader.validate_server(server)
        assert result is True

    def test_flags_fail_returns_false(self, tmp_path):
        loader = self._make_loader(tmp_path)
        server = self._make_server(command=["echo"])
        with patch.object(loader, "check_feature_flags", return_value=False):
            result = loader.validate_server(server)
        assert result is False


# ---------------------------------------------------------------------------
# MCPRegistryLoader.get_server_info
# ---------------------------------------------------------------------------


class TestGetServerInfo:
    """Tests for get_server_info()."""

    def _make_loader_with_server(self, tmp_path):
        from src.integration.mcp_registry_loader import MCPRegistryLoader
        data = [{"id": "chatdev", "description": "ChatDev", "command": ["python"], "env": {}, "tags": ["ai"], "requires": []}]
        registry = tmp_path / "registry.json"
        registry.write_text(json.dumps(data), encoding="utf-8")
        return MCPRegistryLoader(registry_path=registry)

    def test_unknown_server_returns_none(self, tmp_path):
        from src.integration.mcp_registry_loader import MCPRegistryLoader
        loader = MCPRegistryLoader(registry_path=tmp_path / "nope.json")
        assert loader.get_server_info("nonexistent") is None

    def test_known_server_returns_dict(self, tmp_path):
        loader = self._make_loader_with_server(tmp_path)
        info = loader.get_server_info("chatdev")
        assert info is not None
        assert isinstance(info, dict)

    def test_server_info_has_required_keys(self, tmp_path):
        loader = self._make_loader_with_server(tmp_path)
        info = loader.get_server_info("chatdev")
        assert info is not None
        for key in ("id", "description", "command", "tags", "requires", "status"):
            assert key in info

    def test_inactive_server_status(self, tmp_path):
        loader = self._make_loader_with_server(tmp_path)
        info = loader.get_server_info("chatdev")
        assert info is not None
        assert info["status"] == "inactive"

    def test_no_process_pid_is_none(self, tmp_path):
        loader = self._make_loader_with_server(tmp_path)
        info = loader.get_server_info("chatdev")
        assert info is not None
        assert info["pid"] is None


# ---------------------------------------------------------------------------
# MCPRegistryLoader.list_servers and export_manifest
# ---------------------------------------------------------------------------


class TestListAndManifest:
    """Tests for list_servers() and export_manifest()."""

    def _make_loader(self, tmp_path, server_count=2):
        from src.integration.mcp_registry_loader import MCPRegistryLoader
        data = [
            {"id": f"srv{i}", "description": f"Server {i}", "command": ["echo"], "env": {}, "tags": [], "requires": []}
            for i in range(server_count)
        ]
        registry = tmp_path / "registry.json"
        registry.write_text(json.dumps(data), encoding="utf-8")
        return MCPRegistryLoader(registry_path=registry)

    def test_list_servers_returns_list(self, tmp_path):
        loader = self._make_loader(tmp_path)
        result = loader.list_servers()
        assert isinstance(result, list)

    def test_list_servers_count_matches_registry(self, tmp_path):
        loader = self._make_loader(tmp_path, server_count=3)
        result = loader.list_servers()
        assert len(result) == 3

    def test_export_manifest_returns_dict(self, tmp_path):
        loader = self._make_loader(tmp_path)
        manifest = loader.export_manifest()
        assert isinstance(manifest, dict)

    def test_export_manifest_keys(self, tmp_path):
        loader = self._make_loader(tmp_path)
        manifest = loader.export_manifest()
        for key in ("version", "total_servers", "active_servers", "servers"):
            assert key in manifest

    def test_export_manifest_total_servers(self, tmp_path):
        loader = self._make_loader(tmp_path, server_count=2)
        manifest = loader.export_manifest()
        assert manifest["total_servers"] == 2

    def test_export_manifest_active_servers_zero_initially(self, tmp_path):
        loader = self._make_loader(tmp_path)
        manifest = loader.export_manifest()
        assert manifest["active_servers"] == 0


# ---------------------------------------------------------------------------
# MCPRegistryLoader.start_server (mocked subprocess)
# ---------------------------------------------------------------------------


class TestStartServer:
    """Tests for start_server() with mocked subprocess."""

    def _make_loader_with_server(self, tmp_path):
        from src.integration.mcp_registry_loader import MCPRegistryLoader
        data = [{"id": "srv1", "description": "", "command": ["echo", "hello"], "env": {}, "tags": [], "requires": []}]
        registry = tmp_path / "registry.json"
        registry.write_text(json.dumps(data), encoding="utf-8")
        return MCPRegistryLoader(registry_path=registry)

    def test_unknown_server_returns_false(self, tmp_path):
        from src.integration.mcp_registry_loader import MCPRegistryLoader
        loader = MCPRegistryLoader(registry_path=tmp_path / "nope.json")
        assert loader.start_server("nonexistent") is False

    def test_start_server_validation_fails_returns_false(self, tmp_path):
        loader = self._make_loader_with_server(tmp_path)
        with patch.object(loader, "validate_server", return_value=False):
            result = loader.start_server("srv1")
        assert result is False

    def test_start_server_success(self, tmp_path):
        loader = self._make_loader_with_server(tmp_path)
        mock_process = MagicMock()
        mock_process.pid = 12345
        with (
            patch.object(loader, "validate_server", return_value=True),
            patch("subprocess.Popen", return_value=mock_process),
        ):
            result = loader.start_server("srv1")
        assert result is True
        assert "srv1" in loader.active_servers
