"""Tests for src/ai/sns_core_integration.py — SNSCoreHelper and SNSCoreConverter."""


class TestSNSCoreHelperPatterns:
    """Tests for SNSCoreHelper class attributes."""

    def test_patterns_is_dict(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        assert isinstance(SNSCoreHelper.PATTERNS, dict)

    def test_patterns_has_flow(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        assert "flow" in SNSCoreHelper.PATTERNS
        assert SNSCoreHelper.PATTERNS["flow"] == "→"

    def test_abbreviations_is_dict(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        assert isinstance(SNSCoreHelper.ABBREVIATIONS, dict)
        assert len(SNSCoreHelper.ABBREVIATIONS) > 0

    def test_abbreviations_has_query(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        assert "query" in SNSCoreHelper.ABBREVIATIONS


class TestConvertToSNS:
    """Tests for SNSCoreHelper.convert_to_sns (rule-based, no Ollama)."""

    def test_returns_string(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        result = SNSCoreHelper.convert_to_sns("Extract keywords from query")
        assert isinstance(result, str)

    def test_non_empty_result(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        result = SNSCoreHelper.convert_to_sns("Analyze code and generate report")
        assert len(result) > 0

    def test_shorter_than_input(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        original = "Extract keywords from the query and classify the intent of the document"
        result = SNSCoreHelper.convert_to_sns(original)
        assert len(result) < len(original)

    def test_contains_arrow_operator(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        result = SNSCoreHelper.convert_to_sns("Extract data and process it then generate output")
        assert "→" in result

    def test_empty_input_returns_empty(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        result = SNSCoreHelper.convert_to_sns("")
        assert result == ""

    def test_short_input_two_segment_sns(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        # <= 3 words → first → last format
        result = SNSCoreHelper.convert_to_sns("analyze errors")
        assert "→" in result

    def test_flow_pattern_explicit(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        result = SNSCoreHelper.convert_to_sns("fetch data then process", pattern="flow")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_auto_pattern_detection_works(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        result = SNSCoreHelper.convert_to_sns("fetch data and process errors", pattern="auto")
        assert isinstance(result, str)

    def test_articles_removed(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        # Articles like "the", "a", "an" should be stripped
        result = SNSCoreHelper.convert_to_sns("the query extracts the keywords")
        # Result should be much shorter
        assert "the" not in result.lower().split()

    def test_use_ollama_false_does_not_invoke_subprocess(self):
        from unittest.mock import patch
        from src.ai.sns_core_integration import SNSCoreHelper
        with patch("subprocess.run") as mock_run:
            SNSCoreHelper.convert_to_sns("analyze code", use_ollama=False)
            mock_run.assert_not_called()


class TestDetectPattern:
    """Tests for SNSCoreHelper._detect_pattern."""

    def test_then_keyword_gives_flow(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        assert SNSCoreHelper._detect_pattern("do this then do that") == "flow"

    def test_pipeline_keyword(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        assert SNSCoreHelper._detect_pattern("data pipeline process") == "pipeline"

    def test_if_keyword_gives_conditional(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        assert SNSCoreHelper._detect_pattern("if error exists handle it") == "conditional"

    def test_combine_keyword_gives_compose(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        assert SNSCoreHelper._detect_pattern("combine results together") == "compose"

    def test_default_is_flow(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        assert SNSCoreHelper._detect_pattern("something unrecognized xyz") == "flow"


class TestValidateSNS:
    """Tests for SNSCoreHelper.validate_sns."""

    def test_valid_flow_notation(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        is_valid, issues = SNSCoreHelper.validate_sns("q → kw → result")
        assert is_valid is True
        assert issues == []

    def test_valid_pipe_notation(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        is_valid, _issues = SNSCoreHelper.validate_sns("a | b | c")
        assert is_valid is True

    def test_unbalanced_parentheses_invalid(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        is_valid, issues = SNSCoreHelper.validate_sns("q → (kw → result")
        assert is_valid is False
        assert any("parenthes" in i.lower() for i in issues)

    def test_unbalanced_brackets_invalid(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        is_valid, _issues = SNSCoreHelper.validate_sns("q → [kw")
        assert is_valid is False

    def test_double_arrow_detected(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        is_valid, issues = SNSCoreHelper.validate_sns("q → → result")
        assert is_valid is False
        assert any("double arrow" in i.lower() for i in issues)

    def test_invalid_punctuation_detected(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        is_valid, _issues = SNSCoreHelper.validate_sns("q!→result")
        assert is_valid is False

    def test_plain_text_flagged(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        is_valid, issues = SNSCoreHelper.validate_sns("this is just plain English text here")
        assert is_valid is False
        assert len(issues) > 0

    def test_returns_tuple(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        result = SNSCoreHelper.validate_sns("q → kw")
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestGetSNSTemplate:
    """Tests for SNSCoreHelper.get_sns_template."""

    def test_orchestrator_template(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        template = SNSCoreHelper.get_sns_template("orchestrator")
        assert isinstance(template, str)
        assert len(template) > 0

    def test_chatdev_agent_template(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        template = SNSCoreHelper.get_sns_template("chatdev_agent")
        assert isinstance(template, str)

    def test_quantum_resolver_template(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        template = SNSCoreHelper.get_sns_template("quantum_resolver")
        assert isinstance(template, str)

    def test_unknown_use_case_returns_default(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        template = SNSCoreHelper.get_sns_template("nonexistent_case")
        # Falls back to orchestrator
        assert isinstance(template, str)
        assert len(template) > 0

    def test_all_known_templates_non_empty(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        for use_case in ("orchestrator", "chatdev_agent", "quantum_resolver",
                         "consciousness_bridge", "ollama_routing", "rag_orchestrator"):
            t = SNSCoreHelper.get_sns_template(use_case)
            assert len(t) > 0, f"{use_case} template is empty"


class TestCompareTokenCounts:
    """Tests for SNSCoreHelper.compare_token_counts."""

    def test_returns_dict(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        result = SNSCoreHelper.compare_token_counts(
            "Extract keywords from the query document",
            "q → kw_extr → kw"
        )
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        result = SNSCoreHelper.compare_token_counts("long prompt here", "q → r")
        for key in ("traditional_tokens", "sns_tokens", "tokens_saved", "savings_percent",
                    "compression_ratio"):
            assert key in result

    def test_savings_percent_non_negative(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        result = SNSCoreHelper.compare_token_counts(
            "analyze the system errors and generate a report",
            "anlz sys err → rpt"
        )
        assert result["savings_percent"] >= 0

    def test_savings_percent_capped_at_55(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        # Very long traditional vs very short SNS
        result = SNSCoreHelper.compare_token_counts(
            "please analyze all of the system errors and generate a comprehensive report " * 5,
            "anlz → rpt"
        )
        assert result["savings_percent"] <= 55.0

    def test_compression_ratio_at_least_one_when_sns_shorter(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        result = SNSCoreHelper.compare_token_counts(
            "Extract keywords from query and classify intent of the document",
            "q → kw → int"
        )
        assert result["compression_ratio"] >= 1.0

    def test_custom_tokenizer(self):
        from src.ai.sns_core_integration import SNSCoreHelper
        tokenizer = str.split  # returns list of words
        result = SNSCoreHelper.compare_token_counts("hello world test", "hw", tokenizer=tokenizer)
        assert isinstance(result, dict)
        assert result["traditional_tokens"] == 3


class TestSNSCoreConverter:
    """Tests for SNSCoreConverter."""

    def test_instantiation_no_llm(self):
        from src.ai.sns_core_integration import SNSCoreConverter
        converter = SNSCoreConverter()
        assert converter is not None
        assert converter.llm_client is None

    def test_instantiation_with_llm(self):
        from unittest.mock import MagicMock
        from src.ai.sns_core_integration import SNSCoreConverter
        mock_client = MagicMock()
        converter = SNSCoreConverter(llm_client=mock_client)
        assert converter.llm_client is mock_client

    def test_model_sns_loaded(self):
        from src.ai.sns_core_integration import SNSCoreConverter
        converter = SNSCoreConverter()
        assert isinstance(converter.model_sns, str)
        assert len(converter.model_sns) > 0
