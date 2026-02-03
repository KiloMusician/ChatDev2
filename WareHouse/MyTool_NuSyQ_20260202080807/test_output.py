import pytest
from output import RichOutput
from config import Config
def test_display_config(capsys):
    config = Config(api_key='test_api_key', debug_mode=True)
    output = RichOutput()
    output.display_config(config)
    captured = capsys.readouterr()
    assert "API Key: test_api_key" in captured.out
    assert "Debug Mode: Enabled" in captured.out