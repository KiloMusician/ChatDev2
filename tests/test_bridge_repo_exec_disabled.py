"""POST /api/bridge/repo/exec is retired: 410 before any body parsing, and no process is ever spawned.

Mirror of Dev-Mentor PRs #117 / #118 (2026-09-11). The old handler took a raw dict
body and ran the client's `command` string through `subprocess.run(..., shell=True)`
inside the named repo's root. There was no blacklist at all.

The discriminator here is a spy over the *global* `subprocess` / `os` process
entry points, not over `bridge.subprocess` -- so a local `import subprocess`
inside a future handler would still be caught.
"""
from __future__ import annotations

import importlib
import inspect
import json
import os
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


def _import_bridge():
    """Import server.routes.bridge without executing server/routes/__init__.py.

    The aggregator imports every router, and unrelated ones (artifacts -> state ->
    websocket -> workflow_run_service -> check -> fastmcp client) fail to import on
    a machine without the fastmcp client extra. The exec route lives in bridge.py
    alone, so this containment test must not depend on the rest of the package.
    """
    if "server.routes.bridge" in sys.modules:
        return sys.modules["server.routes.bridge"]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    importlib.import_module("server")
    if "server.routes" not in sys.modules:
        pkg = types.ModuleType("server.routes")
        pkg.__path__ = [str(ROOT / "server" / "routes")]
        pkg.__package__ = "server.routes"
        sys.modules["server.routes"] = pkg
    return importlib.import_module("server.routes.bridge")


bridge = _import_bridge()

EXEC_PATH = "/api/bridge/repo/exec"

SHELL_PAYLOADS = [
    "git status",
    "echo ok; echo changed",
    "$(echo changed)",
    "echo changed > marker",
]

PROCESS_ENTRY_POINTS = [
    (subprocess, "run"),
    (subprocess, "Popen"),
    (subprocess, "call"),
    (subprocess, "check_call"),
    (subprocess, "check_output"),
    (os, "system"),
    (os, "popen"),
]


@pytest.fixture
def spies(monkeypatch):
    """Replace every process-spawning entry point with a Mock; return them by name."""
    out = {}
    for module, attr in PROCESS_ENTRY_POINTS:
        spy = Mock(name=f"{module.__name__}.{attr}",
                   return_value=Mock(returncode=0, stdout="", stderr=""))
        monkeypatch.setattr(module, attr, spy)
        out[f"{module.__name__}.{attr}"] = spy
    return out


@pytest.fixture
def repo_root(tmp_path):
    root = tmp_path / "fixture-repo"
    root.mkdir()
    return root


@pytest.fixture
def client(monkeypatch, repo_root):
    # Make the registry lookup succeed with an on-disk root so that a handler
    # which still had the shell path would reach subprocess.run (negative control).
    registry_entry = {"id": "fixture", "name": "fixture", "root": str(repo_root),
                      "status": "online", "api": "", "capabilities": []}
    monkeypatch.setattr(bridge, "get_repo", lambda name: registry_entry if name == "fixture" else None)
    monkeypatch.setattr(bridge, "list_repos", lambda: [registry_entry])
    monkeypatch.setattr(bridge, "get_registry", lambda: {"repos": [registry_entry]})
    monkeypatch.setattr(bridge, "log_action", Mock(name="log_action"))
    app = FastAPI()
    app.include_router(bridge.router)
    return TestClient(app)


def _assert_no_process(spies):
    for name, spy in spies.items():
        assert not spy.called, f"{name} was invoked {spy.call_count}x with {spy.call_args_list}"


# -- (a) four shell payloads -> 410, subprocess never invoked -----------------

@pytest.mark.parametrize("command", SHELL_PAYLOADS)
def test_shell_payload_gets_410_and_never_spawns(client, spies, repo_root, command):
    response = client.post(EXEC_PATH, json={"repo": "fixture", "command": command})

    assert response.status_code == 410, response.text
    detail = response.json()["detail"]
    assert "disabled" in detail.lower()
    assert "/api/bridge/repo/list" in detail
    _assert_no_process(spies)
    assert not (repo_root / "marker").exists()
    assert not bridge.log_action.called, "retired route must not write to the execution log"


@pytest.mark.parametrize("payload", [
    {},                                   # no fields at all
    None,                                 # no JSON body
    {"repo": "fixture"},                  # missing command
    {"command": "git status"},            # missing repo
    {"repo": "unknown", "command": "x"},  # registry miss
    {"repo": "fixture", "command": ""},   # empty command
])
def test_410_precedes_body_validation_and_registry_lookup(client, spies, payload):
    response = client.post(EXEC_PATH, json=payload)

    assert response.status_code == 410, response.text
    _assert_no_process(spies)


def test_route_is_still_mounted_so_410_is_a_verdict_not_a_404(client, spies):
    """A 404 would mean 'nothing here' and a later re-add would go unnoticed."""
    routes = [r for r in bridge.router.routes if getattr(r, "path", "") == EXEC_PATH]
    assert len(routes) == 1
    assert routes[0].methods == {"POST"}
    assert client.get(EXEC_PATH).status_code == 405
    assert client.post(EXEC_PATH).status_code == 410
    _assert_no_process(spies)


# -- (b) nothing re-enables it: no flag, env, header, query, or body key ------

RE_ENABLE_ENV = {
    "BRIDGE_ALLOW_EXEC": "1", "CHATDEV_ALLOW_EXEC": "1", "ALLOW_REPO_EXEC": "true",
    "REPO_EXEC_ENABLED": "yes", "BRIDGE_UNSAFE": "1", "CHATDEV_UNSAFE": "1",
    "DEBUG": "1", "DEV": "1", "ENV": "dev", "ENVIRONMENT": "development",
}
RE_ENABLE_HEADERS = {
    "X-Allow-Exec": "1", "X-Bridge-Unsafe": "1", "X-Admin": "1", "X-Force": "1",
    "Authorization": "Bearer let-me-in", "X-Api-Key": "let-me-in", "X-Confirm": "yes",
}
RE_ENABLE_QUERY = {"force": "1", "allow": "true", "unsafe": "1", "confirm": "yes", "admin": "1"}
RE_ENABLE_BODY = {"repo": "fixture", "command": "git status", "force": True, "allow": True,
                  "unsafe": True, "confirm": True, "admin": True, "sudo": True, "timeout": 1}


def test_env_vars_do_not_reenable(client, spies, monkeypatch):
    for key, value in RE_ENABLE_ENV.items():
        monkeypatch.setenv(key, value)
    response = client.post(EXEC_PATH, json={"repo": "fixture", "command": "git status"})
    assert response.status_code == 410, response.text
    _assert_no_process(spies)


def test_headers_query_and_body_flags_do_not_reenable(client, spies):
    response = client.post(EXEC_PATH, params=RE_ENABLE_QUERY, headers=RE_ENABLE_HEADERS,
                           json=RE_ENABLE_BODY)
    assert response.status_code == 410, response.text
    _assert_no_process(spies)


def test_handler_has_no_inputs_so_no_channel_can_influence_it():
    """Structural proof: a zero-parameter endpoint cannot read body, query, headers,
    or the Request object. The only remaining channel is the environment, which the
    handler source must not touch either."""
    sig = inspect.signature(bridge.repo_exec)
    assert sig.parameters == {}, f"handler takes inputs: {list(sig.parameters)}"

    source = inspect.getsource(bridge.repo_exec)
    for forbidden in ("subprocess", "os.system", "os.popen", "shell", "environ", "getenv",
                      "Request", "body", "get_repo"):
        assert forbidden not in source, f"handler source still references {forbidden!r}"
    assert "410" in source


def test_shell_path_is_deleted_not_guarded():
    """The old request model and the module-level subprocess import are gone."""
    assert not hasattr(bridge, "RepoExecRequest")
    assert not hasattr(bridge, "subprocess"), "module-level `import subprocess` should be gone"
    module_source = inspect.getsource(bridge)
    assert "shell=True" not in module_source


# -- manifest / advertisement -------------------------------------------------

def test_manifest_no_longer_advertises_exec(client, spies):
    manifest = client.get("/api/bridge/manifest")
    assert manifest.status_code == 200, manifest.text
    flat = json.dumps(manifest.json()).lower()
    assert "repo/exec" not in flat
    assert "repo_exec" not in flat
    assert "repo_bridge" in manifest.json()["capabilities"]
    _assert_no_process(spies)


def test_module_docstring_marks_route_retired():
    doc = bridge.__doc__ or ""
    exec_lines = [ln for ln in doc.splitlines() if "repo/exec" in ln]
    assert exec_lines, "docstring should still list the route (mounted, 410)"
    assert all("410" in ln or "retired" in ln.lower() for ln in exec_lines), exec_lines


# -- read-only repo routes remain ---------------------------------------------

def test_readonly_repo_routes_remain_available(client, spies):
    listing = client.get("/api/bridge/repo/list")
    assert listing.status_code == 200
    assert listing.json()["repos"][0]["id"] == "fixture"
    _assert_no_process(spies)
