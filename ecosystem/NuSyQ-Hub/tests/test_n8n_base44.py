from unittest.mock import MagicMock

from src.integration.n8n_integration import N8NClient
from src.utils import base44


def test_base44_roundtrip():
    data = b"hello world"
    encoded = base44.encode(data)
    assert base44.decode(encoded) == data


def test_n8n_trigger_workflow():
    session = MagicMock()
    response = MagicMock()
    response.headers = {"content-type": "application/json"}
    response.json.return_value = {"ok": True}
    response.raise_for_status.return_value = None
    session.post.return_value = response

    client = N8NClient(base_url="http://example.com", session=session)
    result = client.trigger_workflow("test", {"a": 1})

    session.post.assert_called_once_with("http://example.com/webhook/test", json={"a": 1})
    assert result["ok"] is True
    assert result["success"] is True
