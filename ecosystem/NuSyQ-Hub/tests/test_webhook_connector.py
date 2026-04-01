"""Tests for src/connectors/webhook.py — WebhookConnector via mocked requests."""

import sys
import types
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(**kwargs):
    from src.connectors.base import ConnectorConfig

    defaults = {
        "name": "test_webhook",
        "endpoint": "https://example.com/hook",
        "timeout": 10,
        "retry_count": 3,
    }
    defaults.update(kwargs)
    return ConnectorConfig(**defaults)


def _make_connector(**kwargs):
    from src.connectors.webhook import WebhookConnector

    cfg = _make_config(**kwargs)
    return WebhookConnector(cfg)


def _mock_response(status_code=200, json_data=None, text="ok", ok=None):
    """Build a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.ok = (status_code < 400) if ok is None else ok
    resp.text = text
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = ValueError("No JSON")
    return resp


# ---------------------------------------------------------------------------
# ConnectorConfig (base) — sanity tests
# ---------------------------------------------------------------------------


class TestConnectorConfig:
    """Tests for ConnectorConfig dataclass."""

    def test_name_stored(self):
        cfg = _make_config(name="my_hook")
        assert cfg.name == "my_hook"

    def test_endpoint_stored(self):
        cfg = _make_config(endpoint="https://api.example.com")
        assert cfg.endpoint == "https://api.example.com"

    def test_default_timeout(self):
        cfg = _make_config(timeout=30)
        assert cfg.timeout == 30

    def test_default_retry_count(self):
        cfg = _make_config(retry_count=3)
        assert cfg.retry_count == 3

    def test_api_key_none_by_default(self):
        cfg = _make_config()
        assert cfg.api_key is None

    def test_to_dict_has_api_key_flag(self):
        cfg = _make_config(api_key="secret")
        d = cfg.to_dict()
        assert d["has_api_key"] is True

    def test_to_dict_no_api_key_false(self):
        cfg = _make_config()
        d = cfg.to_dict()
        assert d["has_api_key"] is False

    def test_to_dict_does_not_expose_key(self):
        cfg = _make_config(api_key="supersecret")
        d = cfg.to_dict()
        assert "supersecret" not in str(d)


# ---------------------------------------------------------------------------
# WebhookConnector — init / base properties
# ---------------------------------------------------------------------------


class TestWebhookConnectorInit:
    """Tests for WebhookConnector.__init__ and base properties."""

    def test_name_from_config(self):
        wh = _make_connector(name="slack_hook")
        assert wh.name == "slack_hook"

    def test_initial_status_disconnected(self):
        from src.connectors.base import ConnectorStatus

        wh = _make_connector()
        assert wh.status == ConnectorStatus.DISCONNECTED

    def test_is_connected_false_initially(self):
        wh = _make_connector()
        assert wh.is_connected is False

    def test_session_none_initially(self):
        wh = _make_connector()
        assert wh._session is None

    def test_repr_contains_name(self):
        wh = _make_connector(name="hook_x")
        assert "hook_x" in repr(wh)

    def test_to_dict_has_status(self):
        wh = _make_connector()
        d = wh.to_dict()
        assert "status" in d

    def test_to_dict_status_is_disconnected(self):
        wh = _make_connector()
        assert wh.to_dict()["status"] == "disconnected"


# ---------------------------------------------------------------------------
# WebhookConnector — connect
# ---------------------------------------------------------------------------


class TestWebhookConnectorConnect:
    """Tests for WebhookConnector.connect."""

    def test_connect_no_endpoint_fails(self):
        wh = _make_connector(endpoint=None)
        result = wh.connect()
        assert not result.success

    def test_connect_no_endpoint_error_code(self):
        wh = _make_connector(endpoint=None)
        result = wh.connect()
        assert result.code == "NO_ENDPOINT"

    def test_connect_sets_connected_status(self):
        from src.connectors.base import ConnectorStatus

        wh = _make_connector()
        result = wh.connect()
        assert result.success
        assert wh.status == ConnectorStatus.CONNECTED

    def test_connect_is_connected_true(self):
        wh = _make_connector()
        wh.connect()
        assert wh.is_connected is True

    def test_connect_creates_session(self):
        wh = _make_connector()
        wh.connect()
        assert wh._session is not None

    def test_connect_adds_content_type_header(self):
        wh = _make_connector()
        wh.connect()
        assert "application/json" in wh._session.headers.get("Content-Type", "")

    def test_connect_adds_user_agent_header(self):
        wh = _make_connector()
        wh.connect()
        assert "NuSyQ-Hub" in wh._session.headers.get("User-Agent", "")

    def test_connect_with_api_key_sets_auth_header(self):
        wh = _make_connector(api_key="tok_abc")
        wh.connect()
        assert "Bearer tok_abc" in wh._session.headers.get("Authorization", "")

    def test_connect_returns_ok_true(self):
        wh = _make_connector()
        result = wh.connect()
        assert result.data is True


# ---------------------------------------------------------------------------
# WebhookConnector — disconnect
# ---------------------------------------------------------------------------


class TestWebhookConnectorDisconnect:
    """Tests for WebhookConnector.disconnect."""

    def test_disconnect_returns_ok(self):
        wh = _make_connector()
        wh.connect()
        result = wh.disconnect()
        assert result.success

    def test_disconnect_clears_session(self):
        wh = _make_connector()
        wh.connect()
        wh.disconnect()
        assert wh._session is None

    def test_disconnect_sets_disconnected_status(self):
        from src.connectors.base import ConnectorStatus

        wh = _make_connector()
        wh.connect()
        wh.disconnect()
        assert wh.status == ConnectorStatus.DISCONNECTED

    def test_disconnect_without_connect_ok(self):
        wh = _make_connector()
        result = wh.disconnect()
        assert result.success


# ---------------------------------------------------------------------------
# WebhookConnector — health_check
# ---------------------------------------------------------------------------


class TestWebhookConnectorHealthCheck:
    """Tests for WebhookConnector.health_check."""

    def test_health_check_no_endpoint_fails(self):
        wh = _make_connector(endpoint=None)
        result = wh.health_check()
        assert not result.success
        assert result.code == "NO_ENDPOINT"

    def test_health_check_200_is_healthy(self):
        wh = _make_connector()
        resp = _mock_response(status_code=200)
        with patch("requests.head", return_value=resp):
            result = wh.health_check()
        assert result.success
        assert result.data["status"] == "healthy"

    def test_health_check_404_is_healthy(self):
        # status_code < 500 → healthy
        wh = _make_connector()
        resp = _mock_response(status_code=404)
        with patch("requests.head", return_value=resp):
            result = wh.health_check()
        assert result.success
        assert result.data["status"] == "healthy"

    def test_health_check_500_is_degraded(self):
        wh = _make_connector()
        resp = _mock_response(status_code=500)
        with patch("requests.head", return_value=resp):
            result = wh.health_check()
        assert result.success
        assert result.data["status"] == "degraded"

    def test_health_check_timeout_fails(self):
        import requests

        wh = _make_connector()
        with patch("requests.head", side_effect=requests.Timeout):
            result = wh.health_check()
        assert not result.success
        assert result.code == "TIMEOUT"

    def test_health_check_connection_error_fails(self):
        import requests

        wh = _make_connector()
        with patch("requests.head", side_effect=requests.ConnectionError("refused")):
            result = wh.health_check()
        assert not result.success
        assert result.code == "CONNECTION_ERROR"

    def test_health_check_returns_endpoint(self):
        wh = _make_connector(endpoint="https://hooks.example.com")
        resp = _mock_response(status_code=200)
        with patch("requests.head", return_value=resp):
            result = wh.health_check()
        assert result.data["endpoint"] == "https://hooks.example.com"


# ---------------------------------------------------------------------------
# WebhookConnector — execute dispatch
# ---------------------------------------------------------------------------


class TestWebhookConnectorExecute:
    """Tests for WebhookConnector.execute action dispatch."""

    def test_unknown_action_fails(self):
        wh = _make_connector()
        wh.connect()
        result = wh.execute("nonexistent", {})
        assert not result.success
        assert result.code == "UNKNOWN_ACTION"

    def test_unknown_action_lists_supported(self):
        wh = _make_connector()
        wh.connect()
        result = wh.execute("nonexistent", {})
        assert "send" in result.error

    def test_send_action_routed(self):
        wh = _make_connector()
        wh.connect()
        resp = _mock_response(status_code=200, json_data={"ok": True})
        wh._session.post = MagicMock(return_value=resp)
        result = wh.execute("send", {"payload": {"text": "hi"}})
        assert result.success

    def test_post_action_same_as_send(self):
        wh = _make_connector()
        wh.connect()
        resp = _mock_response(status_code=200, json_data={"ok": True})
        wh._session.post = MagicMock(return_value=resp)
        result = wh.execute("post", {"payload": {}})
        assert result.success

    def test_get_action_routed(self):
        wh = _make_connector()
        wh.connect()
        resp = _mock_response(status_code=200, json_data={"items": []})
        wh._session.get = MagicMock(return_value=resp)
        result = wh.execute("get", {})
        assert result.success

    def test_put_action_routed(self):
        wh = _make_connector()
        wh.connect()
        resp = _mock_response(status_code=200, json_data={"updated": True})
        wh._session.put = MagicMock(return_value=resp)
        result = wh.execute("put", {"payload": {"key": "val"}})
        assert result.success

    def test_delete_action_routed(self):
        wh = _make_connector()
        wh.connect()
        resp = _mock_response(status_code=200)
        resp.json.return_value = {}
        wh._session.delete = MagicMock(return_value=resp)
        result = wh.execute("delete", {})
        assert result.success

    def test_case_insensitive_action(self):
        wh = _make_connector()
        wh.connect()
        resp = _mock_response(status_code=200, json_data={})
        wh._session.get = MagicMock(return_value=resp)
        result = wh.execute("GET", {})
        assert result.success


# ---------------------------------------------------------------------------
# WebhookConnector — _send_webhook internals
# ---------------------------------------------------------------------------


class TestWebhookConnectorSendWebhook:
    """Tests for _send_webhook behaviour."""

    def test_not_connected_fails(self):
        wh = _make_connector()
        # Do not call connect()
        result = wh._send_webhook({})
        assert not result.success
        assert result.code == "NOT_CONNECTED"

    def test_success_returns_status_code(self):
        wh = _make_connector()
        wh.connect()
        resp = _mock_response(status_code=201, json_data={"id": 42})
        wh._session.post = MagicMock(return_value=resp)
        result = wh._send_webhook({"payload": {"x": 1}})
        assert result.data["status_code"] == 201

    def test_url_suffix_appended(self):
        wh = _make_connector(endpoint="https://api.example.com")
        wh.connect()
        resp = _mock_response(status_code=200, json_data={})
        mock_post = MagicMock(return_value=resp)
        wh._session.post = mock_post
        wh._send_webhook({"payload": {}, "url_suffix": "/v2/events"})
        called_url = mock_post.call_args[0][0]
        assert called_url == "https://api.example.com/v2/events"

    def test_4xx_returns_fail(self):
        wh = _make_connector(retry_count=1)
        wh.connect()
        resp = _mock_response(status_code=400, ok=False)
        resp.json.side_effect = ValueError("no json")
        resp.text = "bad request"
        wh._session.post = MagicMock(return_value=resp)
        result = wh._send_webhook({"payload": {}})
        assert not result.success
        assert result.code == "WEBHOOK_FAILED"

    def test_timeout_returns_fail(self):
        import requests

        wh = _make_connector(retry_count=1)
        wh.connect()
        wh._session.post = MagicMock(side_effect=requests.Timeout)
        result = wh._send_webhook({"payload": {}})
        assert not result.success
        assert result.code == "TIMEOUT"

    def test_non_json_response_uses_text(self):
        wh = _make_connector()
        wh.connect()
        resp = _mock_response(status_code=200, text="plain text response")
        # json() raises → falls back to text
        wh._session.post = MagicMock(return_value=resp)
        result = wh._send_webhook({"payload": {}})
        assert result.success
        assert result.data["response"] == "plain text response"


# ---------------------------------------------------------------------------
# WebhookConnector — _get_request
# ---------------------------------------------------------------------------


class TestWebhookConnectorGetRequest:
    """Tests for _get_request."""

    def test_not_connected_fails(self):
        wh = _make_connector()
        result = wh._get_request({})
        assert not result.success
        assert result.code == "NOT_CONNECTED"

    def test_get_passes_query_params(self):
        wh = _make_connector()
        wh.connect()
        resp = _mock_response(status_code=200, json_data={})
        mock_get = MagicMock(return_value=resp)
        wh._session.get = mock_get
        wh._get_request({"query_params": {"page": 1}})
        _, kwargs = mock_get.call_args
        assert kwargs.get("params") == {"page": 1}


# ---------------------------------------------------------------------------
# WebhookConnector — _safe_json
# ---------------------------------------------------------------------------


class TestWebhookConnectorSafeJson:
    """Tests for _safe_json helper."""

    def test_valid_json_returned(self):
        wh = _make_connector()
        resp = MagicMock()
        resp.json.return_value = {"key": "value"}
        assert wh._safe_json(resp) == {"key": "value"}

    def test_invalid_json_returns_text(self):
        wh = _make_connector()
        resp = MagicMock()
        resp.json.side_effect = ValueError("no json")
        resp.text = "plain text"
        assert wh._safe_json(resp) == "plain text"

    def test_empty_text_returns_none(self):
        wh = _make_connector()
        resp = MagicMock()
        resp.json.side_effect = ValueError("no json")
        resp.text = ""
        assert wh._safe_json(resp) is None

    def test_long_text_truncated_at_1000(self):
        wh = _make_connector()
        resp = MagicMock()
        resp.json.side_effect = ValueError("no json")
        resp.text = "x" * 2000
        result = wh._safe_json(resp)
        assert len(result) == 1000


# ---------------------------------------------------------------------------
# validate_config (inherited from BaseConnector)
# ---------------------------------------------------------------------------


class TestBaseConnectorValidateConfig:
    """Tests for BaseConnector.validate_config via WebhookConnector."""

    def test_valid_config_ok(self):
        wh = _make_connector(name="ok_hook")
        result = wh.validate_config()
        assert result.success

    def test_empty_name_fails(self):
        from src.connectors.base import ConnectorConfig
        from src.connectors.webhook import WebhookConnector

        cfg = ConnectorConfig(name="")
        wh = WebhookConnector(cfg)
        result = wh.validate_config()
        assert not result.success
        assert result.code == "INVALID_CONFIG"
