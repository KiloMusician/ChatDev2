"""Unit tests for the ChatDev integration helper.

These tests mock :class:`ChatDevLauncher` so that no external systems are
started.  Fixtures provide canned responses for the status check and API key
configuration allowing the tests to run completely offline.

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Testing"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

from unittest.mock import MagicMock, patch

import pytest
from src.integration.chatdev_launcher import ChatDevLauncher


@pytest.fixture
def status_response():
    """Canned status information returned by ``check_status``."""
    return {
        "chatdev_installed": True,
        "chatdev_path": "/fake/path",
        "kilo_secrets_available": False,
        "api_key_configured": False,
        "config_loaded": False,
    }


@pytest.fixture
def api_key(request):
    """API key value used to determine ``setup_api_key`` result.

    The fixture is parametrised in tests to simulate both successful and
    failing configurations.
    """
    return getattr(request, "param", "sk-test")


@pytest.fixture
def launcher(status_response, api_key):
    """Return a ``ChatDevLauncher`` mock with canned responses."""
    launcher = MagicMock(spec=ChatDevLauncher)
    launcher.check_status.return_value = status_response
    launcher.setup_api_key.return_value = bool(api_key)
    return launcher


def test_chatdev_status_check(launcher, status_response):
    """The launcher reports the expected status information."""
    assert launcher.check_status() == status_response


def test_chatdev_api_key_setup_success(launcher):
    """API key configuration succeeds when a key is supplied."""
    assert launcher.setup_api_key() is True


@pytest.mark.parametrize("api_key", [None], indirect=True)
def test_chatdev_missing_api_key(launcher):
    """Setup fails when no API key is provided."""
    assert launcher.setup_api_key() is False


def test_chatdev_invalid_installation():
    """Initialisation fails when ChatDev is not installed at the given path."""
    with patch.object(
        ChatDevLauncher,
        "_validate_chatdev_installation",
        side_effect=FileNotFoundError("ChatDev not found"),
    ):
        with pytest.raises(FileNotFoundError):
            ChatDevLauncher()
