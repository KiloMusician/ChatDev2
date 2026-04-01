"""Tests for src/autonomy/patch_builder.py and src/autonomy/risk_scorer.py."""

import pytest


class TestPatchActionEnum:
    """Tests for PatchAction enum."""

    def test_has_five_values(self):
        from src.autonomy.patch_builder import PatchAction
        assert len(list(PatchAction)) == 5

    def test_values_are_strings(self):
        from src.autonomy.patch_builder import PatchAction
        for action in PatchAction:
            assert isinstance(action.value, str)

    def test_all_members(self):
        from src.autonomy.patch_builder import PatchAction
        names = {a.name for a in PatchAction}
        assert names == {"CREATE", "MODIFY", "DELETE", "REPLACE", "APPEND"}


class TestPatchStatusEnum:
    """Tests for PatchStatus enum."""

    def test_has_eight_values(self):
        from src.autonomy.patch_builder import PatchStatus
        assert len(list(PatchStatus)) == 8

    def test_proposed_is_first(self):
        from src.autonomy.patch_builder import PatchStatus
        assert PatchStatus.PROPOSED.value == "proposed"

    def test_ready_for_pr_exists(self):
        from src.autonomy.patch_builder import PatchStatus
        assert PatchStatus.READY_FOR_PR is not None


class TestCodeBlock:
    """Tests for CodeBlock dataclass."""

    def test_instantiation(self):
        from src.autonomy.patch_builder import CodeBlock
        cb = CodeBlock(language="python", content="x = 1")
        assert cb.language == "python"
        assert cb.content == "x = 1"

    def test_default_confidence(self):
        from src.autonomy.patch_builder import CodeBlock
        cb = CodeBlock(language="python", content="x = 1")
        assert cb.confidence == 0.95

    def test_custom_confidence(self):
        from src.autonomy.patch_builder import CodeBlock
        cb = CodeBlock(language="python", content="x = 1", confidence=0.75)
        assert cb.confidence == 0.75

    def test_line_range_defaults_none(self):
        from src.autonomy.patch_builder import CodeBlock
        cb = CodeBlock(language="python", content="x = 1")
        assert cb.line_start is None
        assert cb.line_end is None


class TestFilePatch:
    """Tests for FilePatch dataclass and validate()."""

    def test_create_valid(self):
        from src.autonomy.patch_builder import FilePatch, PatchAction
        patch = FilePatch(
            file_path="src/new_file.py",
            action=PatchAction.CREATE,
            new_content="x = 1\n",
        )
        valid, _msg = patch.validate()
        assert valid is True

    def test_create_missing_new_content_invalid(self):
        from src.autonomy.patch_builder import FilePatch, PatchAction
        patch = FilePatch(
            file_path="src/new_file.py",
            action=PatchAction.CREATE,
        )
        valid, _msg = patch.validate()
        assert valid is False

    def test_create_with_old_content_invalid(self):
        from src.autonomy.patch_builder import FilePatch, PatchAction
        patch = FilePatch(
            file_path="src/f.py",
            action=PatchAction.CREATE,
            new_content="x = 1",
            old_content="y = 2",
        )
        valid, _msg = patch.validate()
        assert valid is False

    def test_delete_valid(self):
        from src.autonomy.patch_builder import FilePatch, PatchAction
        patch = FilePatch(
            file_path="src/old.py",
            action=PatchAction.DELETE,
            old_content="old code\n",
        )
        valid, _msg = patch.validate()
        assert valid is True

    def test_delete_missing_old_content_invalid(self):
        from src.autonomy.patch_builder import FilePatch, PatchAction
        patch = FilePatch(file_path="src/old.py", action=PatchAction.DELETE)
        valid, _msg = patch.validate()
        assert valid is False

    def test_modify_valid(self):
        from src.autonomy.patch_builder import FilePatch, PatchAction
        patch = FilePatch(
            file_path="src/foo.py",
            action=PatchAction.MODIFY,
            old_content="x = 1",
            new_content="x = 2",
        )
        valid, _msg = patch.validate()
        assert valid is True

    def test_append_valid(self):
        from src.autonomy.patch_builder import FilePatch, PatchAction
        patch = FilePatch(
            file_path="src/foo.py",
            action=PatchAction.APPEND,
            new_content="# appended\n",
        )
        valid, _msg = patch.validate()
        assert valid is True


class TestPatchSet:
    """Tests for PatchSet dataclass."""

    def _make_patchset(self):
        from src.autonomy.patch_builder import PatchSet, PatchStatus
        return PatchSet(patch_id="ps-001")

    def _make_valid_patch(self):
        from src.autonomy.patch_builder import FilePatch, PatchAction
        return FilePatch(
            file_path="src/new.py",
            action=PatchAction.CREATE,
            new_content="x = 1\n",
        )

    def _make_invalid_patch(self):
        from src.autonomy.patch_builder import FilePatch, PatchAction
        return FilePatch(
            file_path="src/new.py",
            action=PatchAction.CREATE,
            # missing new_content
        )

    def test_instantiation(self):
        ps = self._make_patchset()
        assert ps.patch_id == "ps-001"
        assert ps.patches == []

    def test_default_status_proposed(self):
        from src.autonomy.patch_builder import PatchStatus
        ps = self._make_patchset()
        assert ps.status == PatchStatus.PROPOSED

    def test_add_valid_patch(self):
        ps = self._make_patchset()
        result = ps.add_patch(self._make_valid_patch())
        assert result is True
        assert len(ps.patches) == 1

    def test_add_invalid_patch_returns_false(self):
        ps = self._make_patchset()
        result = ps.add_patch(self._make_invalid_patch())
        assert result is False
        assert len(ps.patches) == 0

    def test_add_invalid_patch_appends_error(self):
        ps = self._make_patchset()
        ps.add_patch(self._make_invalid_patch())
        assert len(ps.errors) == 1

    def test_validate_all_empty_is_valid(self):
        ps = self._make_patchset()
        assert ps.validate_all() is True

    def test_validate_all_with_valid_patches(self):
        ps = self._make_patchset()
        # Directly add a valid patch to bypass validate_on_add
        ps.patches.append(self._make_valid_patch())
        assert ps.validate_all() is True


class TestRiskLevelAndApprovalPolicy:
    """Tests for risk_scorer enums."""

    def test_risk_level_has_four_values(self):
        from src.autonomy.risk_scorer import RiskLevel
        assert len(list(RiskLevel)) == 4

    def test_risk_level_values(self):
        from src.autonomy.risk_scorer import RiskLevel
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_approval_policy_has_four_values(self):
        from src.autonomy.risk_scorer import ApprovalPolicy
        assert len(list(ApprovalPolicy)) == 4

    def test_approval_policy_values(self):
        from src.autonomy.risk_scorer import ApprovalPolicy
        assert ApprovalPolicy.AUTO.value == "auto"
        assert ApprovalPolicy.BLOCKED.value == "blocked"


class TestRiskAssessment:
    """Tests for RiskAssessment dataclass."""

    def test_instantiation(self):
        from src.autonomy.risk_scorer import ApprovalPolicy, RiskAssessment, RiskLevel
        ra = RiskAssessment(
            risk_level=RiskLevel.LOW,
            risk_score=0.1,
            approval_policy=ApprovalPolicy.AUTO,
        )
        assert ra.risk_score == 0.1
        assert ra.risk_level == RiskLevel.LOW

    def test_default_lists_empty(self):
        from src.autonomy.risk_scorer import ApprovalPolicy, RiskAssessment, RiskLevel
        ra = RiskAssessment(
            risk_level=RiskLevel.LOW,
            risk_score=0.2,
            approval_policy=ApprovalPolicy.AUTO,
        )
        assert ra.reasoning == []
        assert ra.warnings == []


class TestRiskScorer:
    """Tests for RiskScorer.score() with mock PatchSets."""

    def _make_patchset_with_patches(self, file_paths: list):
        from src.autonomy.patch_builder import FilePatch, PatchAction, PatchSet
        ps = PatchSet(patch_id="test-ps")
        for fp in file_paths:
            patch = FilePatch(
                file_path=fp,
                action=PatchAction.CREATE,
                new_content="x = 1\n",
            )
            ps.patches.append(patch)
        return ps

    def test_score_returns_assessment(self):
        from src.autonomy.risk_scorer import RiskScorer
        scorer = RiskScorer()
        ps = self._make_patchset_with_patches(["src/utils/helper.py"])
        result = scorer.score(ps)
        assert result is not None

    def test_score_low_risk_single_file(self):
        from src.autonomy.risk_scorer import ApprovalPolicy, RiskScorer
        scorer = RiskScorer()
        ps = self._make_patchset_with_patches(["src/tools/helper.py"])
        result = scorer.score(ps)
        assert result.risk_score >= 0.0
        assert result.risk_score <= 1.0

    def test_score_critical_path_raises_risk(self):
        from src.autonomy.risk_scorer import RiskScorer
        scorer = RiskScorer()
        ps = self._make_patchset_with_patches(["src/core/main.py"])  # "core" is critical path
        result = scorer.score(ps)
        # Critical path should raise risk above plain file
        ps2 = self._make_patchset_with_patches(["src/utils/helper.py"])
        result2 = scorer.score(ps2)
        assert result.risk_score >= result2.risk_score

    def test_score_many_files_higher_risk(self):
        from src.autonomy.risk_scorer import RiskScorer
        scorer = RiskScorer()
        many_files = [f"src/module_{i}.py" for i in range(10)]
        one_file = ["src/module_x.py"]
        result_many = scorer.score(self._make_patchset_with_patches(many_files))
        result_one = scorer.score(self._make_patchset_with_patches(one_file))
        assert result_many.risk_score >= result_one.risk_score

    def test_score_has_reasoning(self):
        from src.autonomy.risk_scorer import RiskScorer
        scorer = RiskScorer()
        ps = self._make_patchset_with_patches(["src/core/engine.py"])
        result = scorer.score(ps)
        assert isinstance(result.reasoning, list)

    def test_thresholds_defined(self):
        from src.autonomy.risk_scorer import RiskScorer
        assert "low" in RiskScorer.THRESHOLDS
        assert "medium" in RiskScorer.THRESHOLDS

    def test_critical_paths_defined(self):
        from src.autonomy.risk_scorer import RiskScorer
        assert len(RiskScorer.CRITICAL_PATHS) > 0
        assert "core" in RiskScorer.CRITICAL_PATHS
