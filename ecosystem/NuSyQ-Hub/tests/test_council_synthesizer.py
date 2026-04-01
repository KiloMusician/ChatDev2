"""Tests for CouncilSynthesizer - multi-agent consensus synthesis.

Tests cover:
- synthesize() main entry point with various response scenarios
- Quality scoring based on status, timing, output length
- Jaccard similarity computation for agreement
- Consensus classification thresholds
- Recommendation selection and dissent detection
- Confidence computation
"""

from src.dispatch.council_synthesizer import CouncilSynthesizer


class TestCouncilSynthesizerThresholds:
    """Verify consensus threshold constants."""

    def test_threshold_values(self):
        synth = CouncilSynthesizer()
        assert synth.STRONG_THRESHOLD == 0.6
        assert synth.MODERATE_THRESHOLD == 0.4
        assert synth.WEAK_THRESHOLD == 0.2

    def test_timing_penalty_threshold(self):
        synth = CouncilSynthesizer()
        assert synth.TIMING_PENALTY_MS == 30_000

    def test_min_output_length(self):
        synth = CouncilSynthesizer()
        assert synth.MIN_OUTPUT_LENGTH == 20


class TestJaccardSimilarity:
    """Test _jaccard_similarity static method."""

    def test_identical_texts(self):
        sim = CouncilSynthesizer._jaccard_similarity("hello world", "hello world")
        assert sim == 1.0

    def test_completely_different_texts(self):
        sim = CouncilSynthesizer._jaccard_similarity("hello world", "foo bar baz")
        assert sim == 0.0

    def test_partial_overlap(self):
        # "hello world" -> {hello, world}
        # "hello there" -> {hello, there}
        # intersection: {hello}, union: {hello, world, there}
        # similarity: 1/3 = 0.333...
        sim = CouncilSynthesizer._jaccard_similarity("hello world", "hello there")
        assert abs(sim - (1 / 3)) < 0.001

    def test_both_empty(self):
        sim = CouncilSynthesizer._jaccard_similarity("", "")
        assert sim == 1.0

    def test_one_empty(self):
        sim = CouncilSynthesizer._jaccard_similarity("hello", "")
        assert sim == 0.0
        sim = CouncilSynthesizer._jaccard_similarity("", "hello")
        assert sim == 0.0

    def test_case_insensitive(self):
        sim = CouncilSynthesizer._jaccard_similarity("Hello World", "HELLO WORLD")
        assert sim == 1.0

    def test_punctuation_ignored(self):
        sim = CouncilSynthesizer._jaccard_similarity("hello, world!", "hello world")
        assert sim == 1.0


class TestToText:
    """Test _to_text static method."""

    def test_none_returns_empty(self):
        assert CouncilSynthesizer._to_text(None) == ""

    def test_string_passthrough(self):
        assert CouncilSynthesizer._to_text("hello") == "hello"

    def test_dict_with_output_key(self):
        assert CouncilSynthesizer._to_text({"output": "result text"}) == "result text"

    def test_dict_with_result_key(self):
        assert CouncilSynthesizer._to_text({"result": "result text"}) == "result text"

    def test_dict_with_text_key(self):
        assert CouncilSynthesizer._to_text({"text": "result text"}) == "result text"

    def test_dict_with_content_key(self):
        assert CouncilSynthesizer._to_text({"content": "result text"}) == "result text"

    def test_dict_with_response_key(self):
        assert CouncilSynthesizer._to_text({"response": "result text"}) == "result text"

    def test_dict_without_known_keys(self):
        result = CouncilSynthesizer._to_text({"foo": "bar"})
        assert "foo" in result and "bar" in result

    def test_other_types_converted(self):
        assert CouncilSynthesizer._to_text(123) == "123"
        assert CouncilSynthesizer._to_text([1, 2, 3]) == "[1, 2, 3]"


class TestScoreResponses:
    """Test _score_responses method."""

    def test_error_status_scores_zero(self):
        synth = CouncilSynthesizer()
        responses = {"agent1": {"status": "error", "output": "failed"}}
        scores = synth._score_responses(responses)
        assert scores["agent1"] == 0.0

    def test_ok_status_with_good_output(self):
        synth = CouncilSynthesizer()
        responses = {
            "agent1": {"status": "ok", "output": "This is a valid response with enough length."}
        }
        scores = synth._score_responses(responses)
        assert scores["agent1"] == 1.0

    def test_timing_penalty_applied(self):
        synth = CouncilSynthesizer()
        responses = {
            "agent1": {
                "status": "ok",
                "output": "This is a valid response with enough length.",
                "timing_ms": 35000,  # > 30000 threshold
            }
        }
        scores = synth._score_responses(responses)
        assert scores["agent1"] == 0.7  # 1.0 * 0.7

    def test_short_output_penalty(self):
        synth = CouncilSynthesizer()
        responses = {"agent1": {"status": "ok", "output": "too short"}}  # < 20 chars
        scores = synth._score_responses(responses)
        assert scores["agent1"] == 0.5  # 1.0 * 0.5

    def test_combined_penalties(self):
        synth = CouncilSynthesizer()
        responses = {
            "agent1": {
                "status": "ok",
                "output": "too short",  # < 20 chars
                "timing_ms": 35000,  # > 30000
            }
        }
        scores = synth._score_responses(responses)
        assert scores["agent1"] == 0.35  # 1.0 * 0.7 * 0.5


class TestExtractTexts:
    """Test _extract_texts method."""

    def test_extracts_successful_only(self):
        synth = CouncilSynthesizer()
        responses = {
            "agent1": {"status": "ok", "output": "success response"},
            "agent2": {"status": "error", "output": "error message"},
        }
        texts = synth._extract_texts(responses)
        assert "agent1" in texts
        assert "agent2" not in texts
        assert texts["agent1"] == "success response"

    def test_empty_on_all_failures(self):
        synth = CouncilSynthesizer()
        responses = {
            "agent1": {"status": "error", "output": "fail"},
            "agent2": {"status": "timeout"},
        }
        texts = synth._extract_texts(responses)
        assert texts == {}


class TestComputeAgreement:
    """Test _compute_agreement method."""

    def test_single_agent_perfect_agreement(self):
        synth = CouncilSynthesizer()
        texts = {"agent1": "hello world"}
        matrix, avg = synth._compute_agreement(texts)
        assert matrix == {}
        assert avg == 1.0

    def test_no_agents_zero_agreement(self):
        synth = CouncilSynthesizer()
        texts = {}
        matrix, avg = synth._compute_agreement(texts)
        assert matrix == {}
        assert avg == 0.0

    def test_two_identical_agents(self):
        synth = CouncilSynthesizer()
        texts = {"agent1": "hello world", "agent2": "hello world"}
        matrix, avg = synth._compute_agreement(texts)
        assert "agent1↔agent2" in matrix
        assert matrix["agent1↔agent2"] == 1.0
        assert avg == 1.0

    def test_two_different_agents(self):
        synth = CouncilSynthesizer()
        texts = {"agent1": "hello world", "agent2": "foo bar baz"}
        matrix, avg = synth._compute_agreement(texts)
        assert "agent1↔agent2" in matrix
        assert matrix["agent1↔agent2"] == 0.0
        assert avg == 0.0

    def test_three_agents_averaged(self):
        synth = CouncilSynthesizer()
        texts = {
            "agent1": "hello world",
            "agent2": "hello world",
            "agent3": "foo bar baz",
        }
        matrix, avg = synth._compute_agreement(texts)
        # 3 pairs: agent1↔agent2 (1.0), agent1↔agent3 (0.0), agent2↔agent3 (0.0)
        assert len(matrix) == 3
        assert abs(avg - (1.0 / 3)) < 0.001


class TestClassifyConsensus:
    """Test _classify_consensus method."""

    def test_strong_consensus(self):
        synth = CouncilSynthesizer()
        assert synth._classify_consensus(0.8) == "strong"
        assert synth._classify_consensus(0.6) == "strong"

    def test_moderate_consensus(self):
        synth = CouncilSynthesizer()
        assert synth._classify_consensus(0.5) == "moderate"
        assert synth._classify_consensus(0.4) == "moderate"

    def test_weak_consensus(self):
        synth = CouncilSynthesizer()
        assert synth._classify_consensus(0.3) == "weak"
        assert synth._classify_consensus(0.2) == "weak"

    def test_divergent(self):
        synth = CouncilSynthesizer()
        assert synth._classify_consensus(0.1) == "divergent"
        assert synth._classify_consensus(0.0) == "divergent"


class TestSelectRecommendation:
    """Test _select_recommendation method."""

    def test_selects_highest_quality(self):
        synth = CouncilSynthesizer()
        responses = {
            "agent1": {"status": "ok", "output": "response 1"},
            "agent2": {"status": "ok", "output": "response 2 is better"},
        }
        quality_scores = {"agent1": 0.5, "agent2": 1.0}
        texts = {"agent1": "response 1", "agent2": "response 2 is better"}
        recommendation = synth._select_recommendation(responses, quality_scores, texts)
        assert recommendation == "response 2 is better"

    def test_all_failed_returns_error_summary(self):
        synth = CouncilSynthesizer()
        responses = {
            "agent1": {"status": "error", "output": "error1"},
            "agent2": {"status": "error", "output": "error2"},
        }
        quality_scores = {"agent1": 0.0, "agent2": 0.0}
        texts = {}  # No successful extractions
        recommendation = synth._select_recommendation(responses, quality_scores, texts)
        assert "All agents failed" in recommendation


class TestFindDissenting:
    """Test _find_dissenting method."""

    def test_no_dissent_for_similar(self):
        synth = CouncilSynthesizer()
        texts = {"agent1": "hello world", "agent2": "hello world"}
        dissenting = synth._find_dissenting(texts, "hello world")
        assert dissenting == []

    def test_detects_dissent(self):
        synth = CouncilSynthesizer()
        texts = {"agent1": "hello world", "agent2": "totally different answer"}
        dissenting = synth._find_dissenting(texts, "hello world")
        assert "agent2" in dissenting
        assert "agent1" not in dissenting


class TestComputeConfidence:
    """Test _compute_confidence static method."""

    def test_perfect_agreement_all_succeeded(self):
        conf = CouncilSynthesizer._compute_confidence(1.0, 3, 3)
        # 1.0 * 0.6 + 1.0 * 0.4 = 1.0
        assert conf == 1.0

    def test_no_agents(self):
        conf = CouncilSynthesizer._compute_confidence(0.5, 0, 0)
        assert conf == 0.0

    def test_half_agreement_half_success(self):
        conf = CouncilSynthesizer._compute_confidence(0.5, 2, 4)
        # 0.5 * 0.6 + 0.5 * 0.4 = 0.3 + 0.2 = 0.5
        assert conf == 0.5


class TestEmptyResult:
    """Test _empty_result static method."""

    def test_empty_result_structure(self):
        result = CouncilSynthesizer._empty_result()
        assert result["consensus_level"] == "divergent"
        assert result["confidence"] == 0.0
        assert result["recommendation"] == "No agents responded"
        assert result["agents_consulted"] == 0
        assert result["agents_succeeded"] == 0


class TestSynthesizeIntegration:
    """Integration tests for the synthesize() method."""

    def test_empty_responses(self):
        synth = CouncilSynthesizer()
        result = synth.synthesize({})
        assert result["agents_consulted"] == 0
        assert result["consensus_level"] == "divergent"

    def test_single_successful_agent(self):
        synth = CouncilSynthesizer()
        responses = {"ollama": {"status": "ok", "output": "This is a complete analysis result."}}
        result = synth.synthesize(responses)
        assert result["agents_consulted"] == 1
        assert result["agents_succeeded"] == 1
        assert result["consensus_level"] in ["strong", "moderate", "weak", "divergent"]
        assert "analysis" in result["recommendation"].lower()

    def test_two_agreeing_agents(self):
        synth = CouncilSynthesizer()
        responses = {
            "ollama": {"status": "ok", "output": "The answer is definitely yes, proceed."},
            "lmstudio": {"status": "ok", "output": "The answer is definitely yes, proceed."},
        }
        result = synth.synthesize(responses)
        assert result["agents_consulted"] == 2
        assert result["agents_succeeded"] == 2
        assert result["consensus_level"] == "strong"
        assert result["confidence"] >= 0.6

    def test_two_disagreeing_agents(self):
        synth = CouncilSynthesizer()
        responses = {
            "ollama": {"status": "ok", "output": "The answer is definitely yes."},
            "lmstudio": {"status": "ok", "output": "No way, that is completely wrong."},
        }
        result = synth.synthesize(responses)
        assert result["agents_consulted"] == 2
        assert result["consensus_level"] in ["weak", "divergent"]
        assert len(result["dissenting_views"]) >= 1

    def test_mixed_success_and_failure(self):
        synth = CouncilSynthesizer()
        responses = {
            "ollama": {"status": "ok", "output": "Valid response from ollama agent here."},
            "lmstudio": {"status": "error", "error": "Connection timeout"},
        }
        result = synth.synthesize(responses)
        assert result["agents_consulted"] == 2
        assert result["agents_succeeded"] == 1
        assert result["response_quality"]["lmstudio"] == 0.0
        assert result["response_quality"]["ollama"] == 1.0

    def test_all_agents_fail(self):
        synth = CouncilSynthesizer()
        responses = {
            "ollama": {"status": "error", "output": "timeout"},
            "lmstudio": {"status": "error", "output": "connection refused"},
        }
        result = synth.synthesize(responses)
        assert result["agents_consulted"] == 2
        assert result["agents_succeeded"] == 0
        assert "All agents failed" in result["recommendation"]
        assert result["consensus_level"] == "divergent"
