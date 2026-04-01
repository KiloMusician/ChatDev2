from src.nusyq_spine import cli


def test_cli_status_snapshot():
    # smoke: call snapshot and status functions directly
    assert cli.main(["snapshot"]) == 0
    assert cli.main(["status"]) == 0
