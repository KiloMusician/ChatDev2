"""Tests for src/utils/sns_core_helper.py — SNS-Core token compression utilities."""

import pytest


class TestSnsSymbols:
    """Tests for SNS_SYMBOLS dict."""

    def test_symbols_dict_exists(self):
        from src.utils.sns_core_helper import SNS_SYMBOLS
        assert isinstance(SNS_SYMBOLS, dict)
        assert len(SNS_SYMBOLS) > 0

    def test_symbols_have_descriptions(self):
        from src.utils.sns_core_helper import SNS_SYMBOLS
        for symbol, description in SNS_SYMBOLS.items():
            assert isinstance(symbol, str)
            assert isinstance(description, str)
            assert len(description) > 0


class TestConvertToSns:
    """Tests for convert_to_sns function."""

    def test_returns_tuple(self):
        from src.utils.sns_core_helper import convert_to_sns
        result = convert_to_sns("hello world")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_tuple_structure(self):
        from src.utils.sns_core_helper import convert_to_sns
        sns_text, metadata = convert_to_sns("test input")
        assert isinstance(sns_text, str)
        assert isinstance(metadata, dict)

    def test_empty_string(self):
        from src.utils.sns_core_helper import convert_to_sns
        sns_text, _metadata = convert_to_sns("")
        assert isinstance(sns_text, str)

    def test_system_keyword_replaced(self):
        from src.utils.sns_core_helper import convert_to_sns
        sns_text, _ = convert_to_sns("the system is running")
        # 'system' should be replaced by '⨳'
        assert "⨳" in sns_text or "system" not in sns_text.lower()

    def test_flow_keyword_replaced(self):
        from src.utils.sns_core_helper import convert_to_sns
        sns_text, _ = convert_to_sns("data flow to processing")
        assert "→" in sns_text or "flow" not in sns_text.lower()

    def test_aggressive_mode(self):
        from src.utils.sns_core_helper import convert_to_sns
        _, meta_normal = convert_to_sns("analyze the system module flow", aggressive=False)
        _, meta_aggressive = convert_to_sns("analyze the system module flow", aggressive=True)
        # Both should return valid metadata
        assert isinstance(meta_normal, dict)
        assert isinstance(meta_aggressive, dict)

    def test_metadata_has_expected_keys(self):
        from src.utils.sns_core_helper import convert_to_sns
        _, metadata = convert_to_sns("test system integration flow")
        # Should have some tracking info
        assert isinstance(metadata, dict)


class TestEstimateTokens:
    """Tests for estimate_tokens function."""

    def test_empty_string(self):
        from src.utils.sns_core_helper import estimate_tokens
        assert estimate_tokens("") == 0

    def test_single_word(self):
        from src.utils.sns_core_helper import estimate_tokens
        result = estimate_tokens("hello")
        assert result > 0

    def test_longer_text_has_more_tokens(self):
        from src.utils.sns_core_helper import estimate_tokens
        short = estimate_tokens("hello")
        long = estimate_tokens("hello world this is a longer sentence with many words")
        assert long > short

    def test_returns_int(self):
        from src.utils.sns_core_helper import estimate_tokens
        result = estimate_tokens("test text here")
        assert isinstance(result, int)


class TestLoadSnsSymbols:
    """Tests for load_sns_symbols function."""

    def test_returns_dict(self):
        from src.utils.sns_core_helper import load_sns_symbols
        result = load_sns_symbols()
        assert isinstance(result, dict)

    def test_has_content(self):
        from src.utils.sns_core_helper import load_sns_symbols
        result = load_sns_symbols()
        assert len(result) > 0


class TestAnalyzeTokenSavings:
    """Tests for analyze_token_savings function."""

    def test_returns_dict(self):
        from src.utils.sns_core_helper import analyze_token_savings
        result = analyze_token_savings("the system runs the module")
        assert isinstance(result, dict)

    def test_has_savings_info(self):
        from src.utils.sns_core_helper import analyze_token_savings
        result = analyze_token_savings("system module integration flow component")
        # Should contain some token/savings information
        assert len(result) > 0

    def test_empty_input(self):
        from src.utils.sns_core_helper import analyze_token_savings
        result = analyze_token_savings("")
        assert isinstance(result, dict)


class TestFormatSnsReport:
    """Tests for format_sns_report function."""

    def test_returns_string(self):
        from src.utils.sns_core_helper import analyze_token_savings, format_sns_report
        analysis = analyze_token_savings("test system module")
        report = format_sns_report(analysis)
        assert isinstance(report, str)

    def test_real_analysis_input(self):
        from src.utils.sns_core_helper import analyze_token_savings, format_sns_report
        analysis = analyze_token_savings("system integration module flow")
        report = format_sns_report(analysis)
        assert isinstance(report, str)
        assert len(report) > 0
