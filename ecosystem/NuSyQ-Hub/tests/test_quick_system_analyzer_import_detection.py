from src.diagnostics.quick_system_analyzer import QuickSystemAnalyzer


def test_quick_import_test_accepts_canonical_logging_path() -> None:
    analyzer = QuickSystemAnalyzer()
    issues = analyzer._quick_import_test(
        "from src.LOGGING.modular_logging_system import get_logger\nlogger = get_logger(__name__)\n"
    )
    assert issues == []


def test_quick_import_test_flags_legacy_logging_paths() -> None:
    analyzer = QuickSystemAnalyzer()
    issues = analyzer._quick_import_test(
        "\n".join(
            [
                "from LOGGING.modular_logging_system import get_logger",
                "from src.LOGGING.infrastructure.modular_logging_system import get_logger",
            ]
        )
    )
    assert "Line 1: Old logging path" in issues
    assert "Line 2: Legacy compatibility logging path" in issues
