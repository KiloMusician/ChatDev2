from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from scripts import stack_smoke


def test_load_targets_uses_selected_services(tmp_path):
    port_map = {
        "ports": {
            "7337": {"service": "devmentor", "name": "TD", "external": 7337, "health": "/api/health"},
            "8000": {"service": "nusyq_hub", "name": "Hub", "external": 8000, "health": "/healthz"},
            "9876": {"service": "nusyq_bridge", "name": "Bridge", "external": 9876, "health": "/readyz"},
        }
    }
    cfg = tmp_path / "port_map.json"
    cfg.write_text(json.dumps(port_map))

    # Patch out Replit port overrides so the test is environment-independent
    with patch.object(stack_smoke, "_REPLIT_PORT_OVERRIDES", {}):
        targets = stack_smoke.load_targets(("devmentor", "nusyq_bridge"), path=cfg)

    assert [target["service"] for target in targets] == ["devmentor", "nusyq_bridge"]
    assert targets[0]["url"] == "http://127.0.0.1:7337/api/health"
    assert targets[1]["url"] == "http://127.0.0.1:9876/readyz"


def test_probe_target_reports_http_error():
    target = {"service": "devmentor", "name": "TD", "url": "http://example.invalid/health", "critical": True}

    with patch("urllib.request.urlopen", side_effect=RuntimeError("boom")):
        result = stack_smoke.probe_target(target, timeout=1.0)

    assert result["ok"] is False
    assert result["error"] == "boom"


def test_probe_target_marks_degraded_json_body_unhealthy():
    target = {"service": "nusyq_bridge", "name": "Bridge", "url": "http://example.invalid/readyz", "critical": False}

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self):
            return b'{"status":"degraded","ready":true}'

    with patch("urllib.request.urlopen", return_value=Response()):
        result = stack_smoke.probe_target(target, timeout=1.0)

    assert result["ok"] is False
    assert result["status"] == 200
