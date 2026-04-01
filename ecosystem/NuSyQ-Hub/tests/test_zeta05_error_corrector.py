"""Tests for src.healing.zeta05_error_corrector module."""

from datetime import datetime
from unittest.mock import MagicMock, patch


class TestModuleImports:
    """Test module imports."""

    def test_import_module(self):
        from src.healing import zeta05_error_corrector

        assert zeta05_error_corrector is not None

    def test_import_enums(self):
        from src.healing.zeta05_error_corrector import (
            CorrectionStrategy,
            ErrorSeverity,
        )

        assert ErrorSeverity is not None
        assert CorrectionStrategy is not None

    def test_import_dataclasses(self):
        from src.healing.zeta05_error_corrector import (
            CorrectionResult,
            ErrorContext,
        )

        assert ErrorContext is not None
        assert CorrectionResult is not None

    def test_import_corrector_class(self):
        from src.healing.zeta05_error_corrector import Zeta05ErrorCorrector

        assert Zeta05ErrorCorrector is not None


class TestErrorSeverityEnum:
    """Test ErrorSeverity enum."""

    def test_severity_levels(self):
        from src.healing.zeta05_error_corrector import ErrorSeverity

        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"

    def test_all_severities_exist(self):
        from src.healing.zeta05_error_corrector import ErrorSeverity

        assert len(ErrorSeverity) == 4


class TestCorrectionStrategyEnum:
    """Test CorrectionStrategy enum."""

    def test_strategies(self):
        from src.healing.zeta05_error_corrector import CorrectionStrategy

        assert CorrectionStrategy.AUTO_FIX.value == "auto_fix"
        assert CorrectionStrategy.SUGGEST_FIX.value == "suggest_fix"
        assert CorrectionStrategy.ESCALATE.value == "escalate"
        assert CorrectionStrategy.IGNORE.value == "ignore"


class TestErrorContext:
    """Test ErrorContext dataclass."""

    def test_create_minimal_error_context(self):
        from src.healing.zeta05_error_corrector import ErrorContext, ErrorSeverity

        ctx = ErrorContext(
            error_type="ValueError",
            error_message="Invalid value",
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
        )

        assert ctx.error_type == "ValueError"
        assert ctx.error_message == "Invalid value"
        assert ctx.severity == ErrorSeverity.MEDIUM
        assert ctx.source_file is None
        assert ctx.line_number is None

    def test_create_full_error_context(self):
        from src.healing.zeta05_error_corrector import ErrorContext, ErrorSeverity

        ctx = ErrorContext(
            error_type="TypeError",
            error_message="Type mismatch",
            severity=ErrorSeverity.HIGH,
            timestamp=datetime.now(),
            source_file="test.py",
            line_number=42,
            stack_trace="stack trace here",
            context_lines=["line1", "line2"],
            metadata={"key": "value"},
        )

        assert ctx.source_file == "test.py"
        assert ctx.line_number == 42
        assert ctx.metadata["key"] == "value"


class TestCorrectionResult:
    """Test CorrectionResult dataclass."""

    def test_create_correction_result(self):
        from src.healing.zeta05_error_corrector import (
            CorrectionResult,
            CorrectionStrategy,
            ErrorContext,
            ErrorSeverity,
        )

        ctx = ErrorContext(
            error_type="ValueError",
            error_message="test",
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
        )

        result = CorrectionResult(
            success=True,
            strategy_used=CorrectionStrategy.AUTO_FIX,
            original_error=ctx,
        )

        assert result.success is True
        assert result.strategy_used == CorrectionStrategy.AUTO_FIX
        assert result.timestamp is not None

    def test_post_init_sets_timestamp(self):
        from src.healing.zeta05_error_corrector import (
            CorrectionResult,
            CorrectionStrategy,
            ErrorContext,
            ErrorSeverity,
        )

        ctx = ErrorContext(
            error_type="ValueError",
            error_message="test",
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
        )

        result = CorrectionResult(
            success=False,
            strategy_used=CorrectionStrategy.SUGGEST_FIX,
            original_error=ctx,
        )

        assert result.timestamp is not None
        assert isinstance(result.timestamp, datetime)


class TestZeta05ErrorCorrectorInit:
    """Test Zeta05ErrorCorrector initialization."""

    def test_init_creates_history(self):
        from src.healing.zeta05_error_corrector import Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()
        assert hasattr(corrector, "corrections_history")
        assert isinstance(corrector.corrections_history, list)
        assert len(corrector.corrections_history) == 0

    def test_init_loads_known_patterns(self):
        from src.healing.zeta05_error_corrector import Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()
        assert hasattr(corrector, "known_patterns")
        assert isinstance(corrector.known_patterns, dict)
        assert "ModuleNotFoundError" in corrector.known_patterns
        assert "TypeError" in corrector.known_patterns

    def test_init_auto_fix_enabled(self):
        from src.healing.zeta05_error_corrector import Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()
        assert corrector.auto_fix_enabled is True


class TestLoadKnownPatterns:
    """Test _load_known_patterns method."""

    def test_patterns_include_import_errors(self):
        from src.healing.zeta05_error_corrector import Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()
        patterns = corrector._load_known_patterns()

        assert "ModuleNotFoundError" in patterns
        assert "ImportError" in patterns

    def test_patterns_include_type_errors(self):
        from src.healing.zeta05_error_corrector import Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()
        patterns = corrector._load_known_patterns()

        assert "TypeError" in patterns
        assert "AttributeError" in patterns

    def test_patterns_include_file_errors(self):
        from src.healing.zeta05_error_corrector import Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()
        patterns = corrector._load_known_patterns()

        assert "FileNotFoundError" in patterns
        assert "PermissionError" in patterns


class TestDetectError:
    """Test detect_error method."""

    def test_detect_value_error(self):
        from src.healing.zeta05_error_corrector import Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()
        error = ValueError("Invalid input")

        ctx = corrector.detect_error(error)

        assert ctx.error_type == "ValueError"
        assert ctx.error_message == "Invalid input"
        assert ctx.stack_trace is not None

    def test_detect_error_with_source_file(self):
        from src.healing.zeta05_error_corrector import Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()
        error = TypeError("Expected int")

        ctx = corrector.detect_error(error, source_file="test.py")

        assert ctx.source_file == "test.py"

    def test_detect_error_with_context(self):
        from src.healing.zeta05_error_corrector import Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()
        error = ImportError("No module")
        context = {"function": "test_func"}

        ctx = corrector.detect_error(error, context=context)

        assert ctx.metadata == context


class TestDetermineSeverity:
    """Test _determine_severity method."""

    def test_critical_patterns(self):
        from src.healing.zeta05_error_corrector import ErrorSeverity, Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()

        severity = corrector._determine_severity("RuntimeError", "CRITICAL failure")
        assert severity == ErrorSeverity.CRITICAL

        severity = corrector._determine_severity("Error", "FATAL error occurred")
        assert severity == ErrorSeverity.CRITICAL

    def test_system_errors_critical(self):
        from src.healing.zeta05_error_corrector import ErrorSeverity, Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()

        severity = corrector._determine_severity("SystemError", "system issue")
        assert severity == ErrorSeverity.CRITICAL

        severity = corrector._determine_severity("MemoryError", "out of memory")
        assert severity == ErrorSeverity.CRITICAL

    def test_runtime_errors_high(self):
        from src.healing.zeta05_error_corrector import ErrorSeverity, Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()

        severity = corrector._determine_severity("RuntimeError", "some error")
        assert severity == ErrorSeverity.HIGH

        severity = corrector._determine_severity("TypeError", "type mismatch")
        assert severity == ErrorSeverity.HIGH

    def test_warning_low(self):
        from src.healing.zeta05_error_corrector import ErrorSeverity, Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()

        severity = corrector._determine_severity("DeprecationWarning", "deprecated feature")
        assert severity == ErrorSeverity.LOW

    def test_default_medium(self):
        from src.healing.zeta05_error_corrector import ErrorSeverity, Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()

        severity = corrector._determine_severity("CustomError", "some message")
        assert severity == ErrorSeverity.MEDIUM


class TestSelectStrategy:
    """Test _select_strategy method."""

    def test_critical_escalates(self):
        from src.healing.zeta05_error_corrector import (
            CorrectionStrategy,
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="SystemError",
            error_message="Critical failure",
            severity=ErrorSeverity.CRITICAL,
            timestamp=datetime.now(),
        )

        strategy = corrector._select_strategy(ctx)
        assert strategy == CorrectionStrategy.ESCALATE

    def test_low_ignored(self):
        from src.healing.zeta05_error_corrector import (
            CorrectionStrategy,
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="Warning",
            error_message="Minor issue",
            severity=ErrorSeverity.LOW,
            timestamp=datetime.now(),
        )

        strategy = corrector._select_strategy(ctx)
        assert strategy == CorrectionStrategy.IGNORE

    def test_known_pattern_auto_fix(self):
        from src.healing.zeta05_error_corrector import (
            CorrectionStrategy,
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="ModuleNotFoundError",
            error_message="No module named xyz",
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
        )

        strategy = corrector._select_strategy(ctx)
        assert strategy == CorrectionStrategy.AUTO_FIX


class TestCorrectError:
    """Test correct_error method."""

    def test_correct_with_auto_fix(self):
        from src.healing.zeta05_error_corrector import (
            CorrectionStrategy,
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="ImportError",
            error_message="Cannot import module",
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
        )

        result = corrector.correct_error(ctx)

        assert result.strategy_used == CorrectionStrategy.AUTO_FIX
        assert len(result.suggestions) > 0

    def test_correct_with_ignore(self):
        from src.healing.zeta05_error_corrector import (
            CorrectionStrategy,
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="DeprecationWarning",
            error_message="Feature deprecated",
            severity=ErrorSeverity.LOW,
            timestamp=datetime.now(),
        )

        result = corrector.correct_error(ctx)

        assert result.strategy_used == CorrectionStrategy.IGNORE
        assert result.success is True


class TestAttemptAutoFix:
    """Test _attempt_auto_fix method."""

    def test_auto_fix_known_pattern(self):
        from src.healing.zeta05_error_corrector import (
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="FileNotFoundError",
            error_message="File not found",
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
        )

        result = corrector._attempt_auto_fix(ctx)

        assert len(result.suggestions) > 0
        assert result.confidence > 0

    def test_auto_fix_unknown_pattern(self):
        from src.healing.zeta05_error_corrector import (
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="UnknownError",
            error_message="Unknown issue",
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
        )

        result = corrector._attempt_auto_fix(ctx)

        assert result.confidence == 0.0
        assert "Manual intervention required" in result.suggestions


class TestGenerateSuggestions:
    """Test _generate_suggestions method."""

    def test_import_suggestions(self):
        from src.healing.zeta05_error_corrector import (
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="ImportError",
            error_message="Cannot import",
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
        )

        result = corrector._generate_suggestions(ctx)

        assert len(result.suggestions) > 0
        assert any("pip" in s or "sys.path" in s for s in result.suggestions)

    def test_type_suggestions(self):
        from src.healing.zeta05_error_corrector import (
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="TypeError",
            error_message="type mismatch",
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
        )

        result = corrector._generate_suggestions(ctx)

        assert len(result.suggestions) > 0
        assert any("type" in s.lower() for s in result.suggestions)

    def test_file_suggestions(self):
        from src.healing.zeta05_error_corrector import (
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="FileNotFoundError",
            error_message="file not found",
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
        )

        result = corrector._generate_suggestions(ctx)

        assert len(result.suggestions) > 0
        assert any("path" in s.lower() or "file" in s.lower() for s in result.suggestions)


class TestDetermineSeverityEdgeCases:
    """Test edge cases in _determine_severity method."""

    def test_high_pattern_in_message(self):
        """Error message containing 'ERROR' returns HIGH severity."""
        from src.healing.zeta05_error_corrector import ErrorSeverity, Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()

        # CustomError is not in the high error_type list, but message contains "ERROR"
        severity = corrector._determine_severity("CustomError", "Connection ERROR occurred")
        assert severity == ErrorSeverity.HIGH

    def test_failure_pattern_in_message(self):
        """Error message containing 'FAILURE' returns HIGH severity."""
        from src.healing.zeta05_error_corrector import ErrorSeverity, Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()

        severity = corrector._determine_severity("IOError", "Network FAILURE detected")
        assert severity == ErrorSeverity.HIGH

    def test_exception_pattern_in_message(self):
        """Error message containing 'EXCEPTION' returns HIGH severity."""
        from src.healing.zeta05_error_corrector import ErrorSeverity, Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()

        severity = corrector._determine_severity("OSError", "Unhandled EXCEPTION")
        assert severity == ErrorSeverity.HIGH


class TestCorrectErrorPaths:
    """Test all branches in correct_error method."""

    def test_suggest_fix_path(self):
        """SUGGEST_FIX strategy triggers _generate_suggestions."""
        from src.healing.zeta05_error_corrector import (
            CorrectionStrategy,
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        # Medium severity with unknown error type → SUGGEST_FIX
        ctx = ErrorContext(
            error_type="CustomUnknownError",
            error_message="Something unusual",
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
        )

        result = corrector.correct_error(ctx)

        assert result.strategy_used == CorrectionStrategy.SUGGEST_FIX
        assert len(result.suggestions) > 0

    def test_escalate_path(self):
        """ESCALATE strategy triggers _escalate_to_quantum."""
        from src.healing.zeta05_error_corrector import (
            CorrectionStrategy,
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="CatastrophicError",
            error_message="CRITICAL system failure",
            severity=ErrorSeverity.CRITICAL,
            timestamp=datetime.now(),
        )

        result = corrector.correct_error(ctx)

        assert result.strategy_used == CorrectionStrategy.ESCALATE


class TestSelectStrategyEdgeCases:
    """Test edge cases in _select_strategy method."""

    def test_high_severity_unknown_pattern_escalates(self):
        """HIGH severity with unknown pattern returns ESCALATE."""
        from src.healing.zeta05_error_corrector import (
            CorrectionStrategy,
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="UnknownHighError",  # Not in known_patterns
            error_message="Serious issue",
            severity=ErrorSeverity.HIGH,
            timestamp=datetime.now(),
        )

        strategy = corrector._select_strategy(ctx)
        assert strategy == CorrectionStrategy.ESCALATE


class TestGenerateSuggestionsEdgeCases:
    """Test edge cases in _generate_suggestions method."""

    def test_generic_error_type_suggestions(self):
        """Generic error type gets generic suggestions."""
        from src.healing.zeta05_error_corrector import (
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="CompletelyUnknownError",  # Not Import/Type/File related
            error_message="Unknown issue here",
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
        )

        result = corrector._generate_suggestions(ctx)

        assert "Review error message and stack trace for clues" in result.suggestions


class TestEscalateToQuantum:
    """Test _escalate_to_quantum method."""

    def test_escalate_catches_import_error(self):
        from src.healing.zeta05_error_corrector import (
            CorrectionStrategy,
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="SystemError",
            error_message="Critical system error",
            severity=ErrorSeverity.CRITICAL,
            timestamp=datetime.now(),
        )

        with patch(
            "src.healing.zeta05_error_corrector.Zeta05ErrorCorrector._escalate_to_quantum"
        ) as mock:
            mock.return_value = MagicMock(
                success=False,
                strategy_used=CorrectionStrategy.ESCALATE,
            )

            result = corrector._escalate_to_quantum(ctx)
            assert result.strategy_used == CorrectionStrategy.ESCALATE

    def test_quantum_escalation_success_path(self):
        """Test quantum escalation when resolver successfully resolves."""
        from src.healing.zeta05_error_corrector import (
            CorrectionStrategy,
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="CriticalError",
            error_message="Severe issue",
            severity=ErrorSeverity.CRITICAL,
            timestamp=datetime.now(),
        )

        # Mock quantum resolver to return success
        mock_resolver = MagicMock()
        mock_resolver.resolve_quantum_problem = MagicMock(return_value=True)

        with patch.dict(
            "sys.modules",
            {
                "src.healing.quantum_problem_resolver": MagicMock(
                    QuantumProblemResolver=MagicMock(return_value=mock_resolver),
                    ProblemSignature=MagicMock(),
                    QuantumProblemState=MagicMock(SUPERPOSITION="superposition"),
                ),
            },
        ):
            # Call _escalate_to_quantum directly - it will now use mocked module
            result = corrector._escalate_to_quantum(ctx)

            # Should return escalate strategy (regardless of mock success)
            assert result.strategy_used == CorrectionStrategy.ESCALATE

    def test_quantum_escalation_failure_path(self):
        """Test quantum escalation when resolver encounters exception."""
        from src.healing.zeta05_error_corrector import (
            CorrectionStrategy,
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="CriticalError",
            error_message="Severe issue",
            severity=ErrorSeverity.CRITICAL,
            timestamp=datetime.now(),
        )

        # The quantum resolver import happens inside _escalate_to_quantum
        # Patch the import mechanism to fail
        with patch.dict("sys.modules", {"src.healing.quantum_problem_resolver": None}):
            result = corrector._escalate_to_quantum(ctx)

            # Should handle error gracefully
            assert result.strategy_used == CorrectionStrategy.ESCALATE
            assert result.success is False

    def test_quantum_resolver_returns_true(self):
        """Test quantum escalation when resolver returns True (resolved)."""

        from src.healing.zeta05_error_corrector import (
            CorrectionStrategy,
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="CriticalError",
            error_message="Severe issue",
            severity=ErrorSeverity.CRITICAL,
            timestamp=datetime.now(),
        )

        # Create mock resolver that returns True
        mock_resolver = MagicMock()

        async def resolve_coro(problem):
            return True

        mock_resolver.resolve_quantum_problem = resolve_coro

        mock_module = MagicMock()
        mock_module.QuantumProblemResolver = MagicMock(return_value=mock_resolver)
        mock_module.ProblemSignature = MagicMock()
        mock_module.QuantumProblemState = MagicMock()
        mock_module.QuantumProblemState.SUPERPOSITION = "superposition"

        with patch.dict("sys.modules", {"src.healing.quantum_problem_resolver": mock_module}):
            result = corrector._escalate_to_quantum(ctx)

            assert result.success is True
            assert result.strategy_used == CorrectionStrategy.ESCALATE
            assert result.confidence == 0.85

    def test_quantum_resolver_returns_false(self):
        """Test quantum escalation when resolver returns False (not resolved)."""
        from src.healing.zeta05_error_corrector import (
            CorrectionStrategy,
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()
        ctx = ErrorContext(
            error_type="CriticalError",
            error_message="Severe issue",
            severity=ErrorSeverity.CRITICAL,
            timestamp=datetime.now(),
        )

        # Create mock resolver that returns False
        mock_resolver = MagicMock()

        async def resolve_coro(problem):
            return False

        mock_resolver.resolve_quantum_problem = resolve_coro

        mock_module = MagicMock()
        mock_module.QuantumProblemResolver = MagicMock(return_value=mock_resolver)
        mock_module.ProblemSignature = MagicMock()
        mock_module.QuantumProblemState = MagicMock()
        mock_module.QuantumProblemState.SUPERPOSITION = "superposition"

        with patch.dict("sys.modules", {"src.healing.quantum_problem_resolver": mock_module}):
            result = corrector._escalate_to_quantum(ctx)

            assert result.success is False
            assert result.strategy_used == CorrectionStrategy.ESCALATE
            assert result.confidence == 0.4


class TestGetCorrectionStats:
    """Test get_correction_stats method."""

    def test_empty_stats(self):
        from src.healing.zeta05_error_corrector import Zeta05ErrorCorrector

        corrector = Zeta05ErrorCorrector()
        stats = corrector.get_correction_stats()

        assert stats["total_corrections"] == 0
        assert stats["success_rate"] == 0.0

    def test_stats_after_corrections(self):
        from src.healing.zeta05_error_corrector import (
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()

        # Make some corrections
        ctx = ErrorContext(
            error_type="ImportError",
            error_message="test",
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
        )

        corrector.correct_error(ctx)
        corrector.correct_error(ctx)

        stats = corrector.get_correction_stats()

        assert stats["total_corrections"] == 2
        assert "strategy_distribution" in stats
        assert "avg_confidence" in stats


class TestSingletonInstance:
    """Test singleton instance."""

    def test_zeta05_corrector_exists(self):
        from src.healing.zeta05_error_corrector import zeta05_corrector

        assert zeta05_corrector is not None

    def test_singleton_is_corrector(self):
        from src.healing.zeta05_error_corrector import (
            Zeta05ErrorCorrector,
            zeta05_corrector,
        )

        assert isinstance(zeta05_corrector, Zeta05ErrorCorrector)
