import importlib

import pytest


def test_health_cli_tracing_no_throw():
    # Load the health_cli module and call main with --tracing.
    hc = importlib.import_module("src.diagnostics.health_cli")
    # Call main with the --tracing flag; it will sys.exit with 0 or 1 depending on tracing availability.
    with pytest.raises(SystemExit) as exc:
        hc.main(["--tracing"])
    assert isinstance(exc.value.code, int)


def test_health_cli_otel_compose_prints(capsys):
    hc = importlib.import_module("src.diagnostics.health_cli")
    # Call main with --otel-compose and capture stdout
    with pytest.raises(SystemExit) as exc:
        hc.main(["--otel-compose"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert (
        "otlp-collector" in captured.out
        or "OTLP" in captured.out
        or "opentelemetry-collector" in captured.out
    )


def test_health_cli_stats_exit_code():
    hc = importlib.import_module("src.diagnostics.health_cli")
    # Running stats will use ruff; ensure it exits with an integer code
    # Use pytest fixture imported at top-level
    with pytest.raises(SystemExit) as exc:
        hc.main(["--stats"])
    assert isinstance(exc.value.code, int)
