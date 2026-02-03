import pytest
from config import Config
def test_config_from_file():
    config = Config.from_file('test_config.json')
    assert config.api_key == 'test_api_key'
    assert config.debug_mode is True