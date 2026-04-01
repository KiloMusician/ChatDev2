"""Tests for src/integration/quantum_resolver_adapter.py and src/integration/n8n_integration.py."""

from unittest.mock import MagicMock

import pytest


class TestQuantumResolverAdapter:
    """Tests for QuantumResolverAdapter — fully pure, no external deps."""

    def _make(self):
        from src.integration.quantum_resolver_adapter import QuantumResolverAdapter
        return QuantumResolverAdapter()

    def test_instantiation(self):
        assert self._make() is not None

    def test_omni_tags_starts_empty(self):
        assert self._make().omni_tags == []

    def test_mega_tags_starts_empty(self):
        assert self._make().mega_tags == []

    def test_add_omni_tag(self):
        adapter = self._make()
        adapter.add_omni_tag("python")
        assert "python" in adapter.omni_tags

    def test_add_multiple_omni_tags(self):
        adapter = self._make()
        adapter.add_omni_tag("python")
        adapter.add_omni_tag("error")
        assert len(adapter.omni_tags) == 2

    def test_add_mega_tag(self):
        adapter = self._make()
        adapter.add_mega_tag("performance")
        assert "performance" in adapter.mega_tags

    def test_resolve_context_returns_dict(self):
        result = self._make().resolve_context("test query")
        assert isinstance(result, dict)

    def test_resolve_context_has_query_key(self):
        adapter = self._make()
        result = adapter.resolve_context("my query")
        assert result["query"] == "my query"

    def test_resolve_context_has_tags(self):
        adapter = self._make()
        adapter.add_omni_tag("tag1")
        result = adapter.resolve_context("q")
        assert "omni_tags" in result
        assert "mega_tags" in result

    def test_resolve_context_has_insights(self):
        result = self._make().resolve_context("q")
        assert "contextual_insights" in result
        assert isinstance(result["contextual_insights"], list)

    def test_omni_tag_in_query_yields_insight(self):
        adapter = self._make()
        adapter.add_omni_tag("python")
        result = adapter.resolve_context("python is great")
        assert any("OmniTag" in insight for insight in result["contextual_insights"])

    def test_mega_tag_in_query_yields_insight(self):
        adapter = self._make()
        adapter.add_mega_tag("performance")
        result = adapter.resolve_context("performance benchmark")
        assert any("MegaTag" in insight for insight in result["contextual_insights"])

    def test_no_matching_tag_no_insight(self):
        adapter = self._make()
        adapter.add_omni_tag("unrelated")
        result = adapter.resolve_context("something completely different xyz")
        assert result["contextual_insights"] == []

    def test_clear_tags(self):
        adapter = self._make()
        adapter.add_omni_tag("a")
        adapter.add_mega_tag("b")
        adapter.clear_tags()
        assert adapter.omni_tags == []
        assert adapter.mega_tags == []

    def test_resolve_context_after_clear(self):
        adapter = self._make()
        adapter.add_omni_tag("python")
        adapter.clear_tags()
        result = adapter.resolve_context("python")
        # After clear, tags list is empty — no insights from omni_tags
        assert result["omni_tags"] == []


class TestN8NClient:
    """Tests for N8NClient with mocked HTTP session."""

    def _make_client(self, base_url="http://test-n8n:5678", session=None):
        from src.integration.n8n_integration import N8NClient
        mock_session = session or MagicMock()
        return N8NClient(base_url=base_url, session=mock_session), mock_session

    def test_instantiation(self):
        client, _ = self._make_client()
        assert client is not None

    def test_base_url_stored(self):
        client, _ = self._make_client("http://myhost:5678")
        assert client.base_url == "http://myhost:5678"

    def test_session_stored(self):
        mock_session = MagicMock()
        client, _ = self._make_client(session=mock_session)
        assert client.session is mock_session

    def test_default_base_url_from_env(self, monkeypatch):
        from src.integration.n8n_integration import N8NClient
        monkeypatch.setenv("N8N_URL", "http://envhost:9999")
        monkeypatch.setattr("src.integration.n8n_integration._ServiceConfig", None)
        client = N8NClient(session=MagicMock())
        assert "envhost" in client.base_url or "9999" in client.base_url

    def test_trigger_workflow_calls_post(self):
        client, mock_session = self._make_client()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.json.return_value = {"status": "ok"}
        mock_session.post.return_value = mock_resp
        client.trigger_workflow("wf-001", data={"key": "val"})
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert "wf-001" in call_args[0][0]

    def test_trigger_workflow_url_format(self):
        client, mock_session = self._make_client("http://n8n:5678")
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.headers = {"content-type": "text/plain"}
        mock_resp.status_code = 200
        mock_session.post.return_value = mock_resp
        client.trigger_workflow("my-workflow")
        url_called = mock_session.post.call_args[0][0]
        assert url_called == "http://n8n:5678/webhook/my-workflow"

    def test_json_response_returned(self):
        client, mock_session = self._make_client()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.json.return_value = {"result": "done", "success": True}
        mock_session.post.return_value = mock_resp
        result = client.trigger_workflow("wf")
        assert result["result"] == "done"

    def test_json_response_adds_success_key_when_missing(self):
        client, mock_session = self._make_client()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.json.return_value = {"data": "payload"}  # no "success" key
        mock_session.post.return_value = mock_resp
        result = client.trigger_workflow("wf")
        assert "success" in result
        assert result["success"] is True

    def test_json_status_ok_sets_success_true(self):
        client, mock_session = self._make_client()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.json.return_value = {"status": "ok"}
        mock_session.post.return_value = mock_resp
        result = client.trigger_workflow("wf")
        assert result["success"] is True

    def test_non_json_response_returns_success(self):
        client, mock_session = self._make_client()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.headers = {"content-type": "text/html"}
        mock_resp.status_code = 200
        mock_session.post.return_value = mock_resp
        result = client.trigger_workflow("wf")
        assert result["success"] is True
        assert result["status"] == 200

    def test_http_error_raises(self):
        import requests
        client, mock_session = self._make_client()
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = requests.HTTPError("Server error")
        mock_resp.headers = {}
        mock_session.post.return_value = mock_resp
        with pytest.raises(requests.HTTPError):
            client.trigger_workflow("fail-wf")

    def test_empty_data_defaults_to_empty_dict(self):
        client, mock_session = self._make_client()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.headers = {"content-type": "text/plain"}
        mock_resp.status_code = 200
        mock_session.post.return_value = mock_resp
        client.trigger_workflow("wf")
        _, kwargs = mock_session.post.call_args
        assert kwargs.get("json") == {}
