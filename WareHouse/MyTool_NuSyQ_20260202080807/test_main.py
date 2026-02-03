import pytest
from click.testing import CliRunner
from main import cli
runner = CliRunner()
def test_run_command():
    result = runner.invoke(cli, ['run', '--config', 'test_config.json'])
    assert result.exit_code == 0
    assert "API Key" in result.output
    assert "Debug Mode" in result.output