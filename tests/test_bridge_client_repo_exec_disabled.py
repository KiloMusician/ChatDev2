"""BridgeClient.repo_exec fails closed locally, before any HTTP request (mirror of Dev-Mentor #118).

Two tracked copies of the client live in this repo:
  ecosystem/nusyq_surface/bridge_client.py
  ecosystem/NuSyQ-Hub/nusyq_surface/bridge_client.py   (vendored, hyphenated dir)
Both are loaded from their file paths as separate packages so the vendored copy
is exercised too, not just the importable one.
"""
from __future__ import annotations

import importlib
import importlib.util
import inspect
import sys
import urllib.request
from pathlib import Path
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLIENT_COPIES = {
    "ecosystem": ROOT / "ecosystem" / "nusyq_surface",
    "nusyq_hub_vendored": ROOT / "ecosystem" / "NuSyQ-Hub" / "nusyq_surface",
}


def _load_bridge_client(alias: str, pkg_dir: Path):
    pkg_name = f"_bridge_client_under_test_{alias}"
    if pkg_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            pkg_name, pkg_dir / "__init__.py", submodule_search_locations=[str(pkg_dir)],
        )
        pkg = importlib.util.module_from_spec(spec)
        sys.modules[pkg_name] = pkg
        spec.loader.exec_module(pkg)
    return importlib.import_module(f"{pkg_name}.bridge_client")


@pytest.fixture(params=sorted(CLIENT_COPIES), ids=sorted(CLIENT_COPIES))
def bridge_client_module(request):
    return _load_bridge_client(request.param, CLIENT_COPIES[request.param])


@pytest.fixture
def network_spy(monkeypatch):
    spy = Mock(name="urllib.request.urlopen", side_effect=AssertionError("network must not be touched"))
    monkeypatch.setattr(urllib.request, "urlopen", spy)
    return spy


def test_repo_exec_raises_before_posting(bridge_client_module, network_spy, monkeypatch):
    client = bridge_client_module.BridgeClient(base_url="http://127.0.0.1:1")
    posted: list = []

    def _unexpected_post(*args, **kwargs):
        posted.append((args, kwargs))
        raise AssertionError("repo_exec must not call _post")

    monkeypatch.setattr(client, "_post", _unexpected_post)

    with pytest.raises(RuntimeError, match="repo_exec is disabled"):
        client.repo_exec("nusyq_hub", "git status")

    assert posted == []
    network_spy.assert_not_called()


@pytest.mark.parametrize("command", ["git status", "echo ok; echo changed", "$(echo changed)",
                                     "echo changed > marker"])
def test_repo_exec_rejects_every_payload_shape(bridge_client_module, network_spy, command):
    client = bridge_client_module.BridgeClient(base_url="http://127.0.0.1:1")
    with pytest.raises(RuntimeError):
        client.repo_exec("nusyq_hub", command)
    network_spy.assert_not_called()


def test_repo_exec_source_has_no_request_path(bridge_client_module):
    source = inspect.getsource(bridge_client_module.BridgeClient.repo_exec)
    assert "_post" not in source
    assert "/repo/exec" not in source
    assert "raise RuntimeError" in source


def test_readonly_repo_methods_still_use_typed_get(bridge_client_module, network_spy, monkeypatch):
    client = bridge_client_module.BridgeClient(base_url="http://127.0.0.1:1")
    requested: list[str] = []
    monkeypatch.setattr(client, "_get", lambda path: requested.append(path) or {"ok": True})

    assert client.repo_list() == {"ok": True}
    assert client.repo_status() == {"ok": True}
    assert client.repo_status("nusyq_hub") == {"ok": True}
    assert requested == ["/repo/list", "/repo/status", "/repo/status/nusyq_hub"]
    network_spy.assert_not_called()


def test_both_tracked_copies_are_identical_modulo_line_endings():
    texts = {alias: (d / "bridge_client.py").read_text(encoding="utf-8").replace("\r\n", "\n")
             for alias, d in CLIENT_COPIES.items()}
    assert texts["ecosystem"] == texts["nusyq_hub_vendored"], "client copies drifted"
