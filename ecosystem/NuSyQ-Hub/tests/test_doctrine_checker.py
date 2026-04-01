"""Tests for src/doctrine/doctrine_checker.py — pure unit tests, no network or real git calls."""


# ---------------------------------------------------------------------------
# All imports are inside test functions per project convention
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# DoctrineViolation dataclass tests
# ---------------------------------------------------------------------------


def test_doctrine_violation_construction_minimal():
    from src.doctrine.doctrine_checker import DoctrineViolation

    v = DoctrineViolation(
        mandate="Do not delete files",
        violation_type="forbidden_pattern",
        evidence=["file.py missing"],
        severity="high",
        recommendation="Restore file.py",
    )
    assert v.mandate == "Do not delete files"
    assert v.violation_type == "forbidden_pattern"
    assert v.evidence == ["file.py missing"]
    assert v.severity == "high"
    assert v.recommendation == "Restore file.py"
    assert v.source_file is None  # default


def test_doctrine_violation_source_file_set():
    from src.doctrine.doctrine_checker import DoctrineViolation

    v = DoctrineViolation(
        mandate="Keep imports clean",
        violation_type="drift",
        evidence=[],
        severity="medium",
        recommendation="Refactor",
        source_file="/some/path/mandate.md",
    )
    assert v.source_file == "/some/path/mandate.md"


def test_doctrine_violation_evidence_is_list():
    from src.doctrine.doctrine_checker import DoctrineViolation

    v = DoctrineViolation(
        mandate="m",
        violation_type="abandoned",
        evidence=["a", "b", "c"],
        severity="low",
        recommendation="fix",
    )
    assert isinstance(v.evidence, list)
    assert len(v.evidence) == 3


# ---------------------------------------------------------------------------
# ComplianceReport dataclass tests
# ---------------------------------------------------------------------------


def test_compliance_report_defaults(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport

    r = ComplianceReport(timestamp="2026-01-01T00:00:00", hub_path=tmp_path)
    assert r.total_mandates == 0
    assert r.violations == []
    assert r.compliance_score == 0.0
    assert r.instruction_files_parsed == []
    assert r.doctrine_files_parsed == []
    assert r.git_commits_analyzed == 0
    assert r.insights == []


def test_compliance_report_violations_list_is_independent(tmp_path):
    """Each ComplianceReport gets its own violations list (not shared default)."""
    from src.doctrine.doctrine_checker import ComplianceReport

    r1 = ComplianceReport(timestamp="t1", hub_path=tmp_path)
    r2 = ComplianceReport(timestamp="t2", hub_path=tmp_path)
    r1.violations.append(object())  # type: ignore[arg-type]
    assert r2.violations == []


# ---------------------------------------------------------------------------
# ComplianceReport.to_markdown tests
# ---------------------------------------------------------------------------


def test_to_markdown_basic_structure(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport

    r = ComplianceReport(
        timestamp="2026-03-15T12:00:00",
        hub_path=tmp_path,
        total_mandates=3,
        compliance_score=0.85,
        git_commits_analyzed=10,
    )
    md = r.to_markdown()
    assert "# Doctrine Compliance Report" in md
    assert "85.0%" in md
    assert "2026-03-15T12:00:00" in md
    assert "3" in md  # total mandates
    assert "10" in md  # commits analyzed


def test_to_markdown_no_violations(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport

    r = ComplianceReport(timestamp="ts", hub_path=tmp_path)
    md = r.to_markdown()
    assert "## Violations by Severity" not in md


def test_to_markdown_with_violations(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport, DoctrineViolation

    v = DoctrineViolation(
        mandate="Keep files",
        violation_type="drift",
        evidence=["evidence_one", "evidence_two"],
        severity="critical",
        recommendation="Restore them",
        source_file=str(tmp_path / "mandate.md"),
    )
    r = ComplianceReport(timestamp="ts", hub_path=tmp_path, violations=[v])
    md = r.to_markdown()
    assert "## Violations by Severity" in md
    assert "CRITICAL" in md
    assert "Keep files" in md
    assert "evidence_one" in md
    assert "Restore them" in md


def test_to_markdown_evidence_truncated_at_three(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport, DoctrineViolation

    evidence = [f"item_{i}" for i in range(7)]
    v = DoctrineViolation(
        mandate="m",
        violation_type="drift",
        evidence=evidence,
        severity="high",
        recommendation="fix",
    )
    r = ComplianceReport(timestamp="ts", hub_path=tmp_path, violations=[v])
    md = r.to_markdown()
    assert "...and 4 more" in md


def test_to_markdown_instruction_files_truncated_at_five(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport

    files = [f"/path/file_{i}.md" for i in range(8)]
    r = ComplianceReport(
        timestamp="ts",
        hub_path=tmp_path,
        instruction_files_parsed=files,
    )
    md = r.to_markdown()
    assert "...and 3 more" in md


def test_to_markdown_insights_included(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport

    r = ComplianceReport(
        timestamp="ts",
        hub_path=tmp_path,
        insights=["Great job!", "One warning"],
    )
    md = r.to_markdown()
    assert "## Insights" in md
    assert "Great job!" in md
    assert "One warning" in md


def test_to_markdown_all_severity_levels(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport, DoctrineViolation

    severities = ["critical", "high", "medium", "low"]
    violations = [
        DoctrineViolation(
            mandate=f"mandate_{s}",
            violation_type="drift",
            evidence=["e"],
            severity=s,
            recommendation="r",
        )
        for s in severities
    ]
    r = ComplianceReport(timestamp="ts", hub_path=tmp_path, violations=violations)
    md = r.to_markdown()
    for s in severities:
        assert s.upper() in md


# ---------------------------------------------------------------------------
# DoctrineChecker instantiation tests
# ---------------------------------------------------------------------------


def test_doctrine_checker_init(tmp_path):
    from src.doctrine.doctrine_checker import DoctrineChecker

    checker = DoctrineChecker(hub_path=tmp_path)
    assert checker.hub_path == tmp_path
    assert checker.instructions_dir == tmp_path / ".github" / "instructions"
    assert checker.doctrine_dir == tmp_path / "docs" / "doctrine"


# ---------------------------------------------------------------------------
# _get_recent_commits tests (subprocess stubbed)
# ---------------------------------------------------------------------------


def test_get_recent_commits_success(tmp_path):
    from unittest.mock import MagicMock, patch

    from src.doctrine.doctrine_checker import DoctrineChecker

    checker = DoctrineChecker(hub_path=tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = (
        "abc1234|feat: add thing|2026-01-01 12:00:00 +0000\n"
        "def5678|fix: repair bug|2026-01-02 09:00:00 +0000\n"
    )
    with patch("subprocess.run", return_value=mock_result):
        commits = checker._get_recent_commits(5)

    assert len(commits) == 2
    assert commits[0]["sha"] == "abc1234"
    assert commits[0]["message"] == "feat: add thing"
    assert commits[1]["sha"] == "def5678"


def test_get_recent_commits_nonzero_returncode(tmp_path):
    from unittest.mock import MagicMock, patch

    from src.doctrine.doctrine_checker import DoctrineChecker

    checker = DoctrineChecker(hub_path=tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    with patch("subprocess.run", return_value=mock_result):
        commits = checker._get_recent_commits(5)

    assert commits == []


def test_get_recent_commits_exception_returns_empty(tmp_path):
    from unittest.mock import patch

    from src.doctrine.doctrine_checker import DoctrineChecker

    checker = DoctrineChecker(hub_path=tmp_path)
    with patch("subprocess.run", side_effect=OSError("git not found")):
        commits = checker._get_recent_commits(5)

    assert commits == []


def test_get_recent_commits_empty_stdout(tmp_path):
    from unittest.mock import MagicMock, patch

    from src.doctrine.doctrine_checker import DoctrineChecker

    checker = DoctrineChecker(hub_path=tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    with patch("subprocess.run", return_value=mock_result):
        commits = checker._get_recent_commits(10)

    assert commits == []


# ---------------------------------------------------------------------------
# _check_receipt_discipline tests (pure logic, no subprocess)
# ---------------------------------------------------------------------------


def _make_commits(messages):
    """Helper: build commit dicts with fake SHAs."""
    return [
        {"sha": f"{'a' * 7}{i:02d}", "message": msg, "date": "2026-01-01"}
        for i, msg in enumerate(messages)
    ]


def test_receipt_discipline_all_conventional(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport, DoctrineChecker

    checker = DoctrineChecker(hub_path=tmp_path)
    commits = _make_commits(
        [
            "feat: add new feature",
            "fix: resolve bug",
            "docs: update README",
            "chore: bump deps",
            "refactor: improve structure",
        ]
    )
    report = ComplianceReport(timestamp="ts", hub_path=tmp_path)
    checker._check_receipt_discipline(report, commits)
    assert len(report.violations) == 0


def test_receipt_discipline_many_non_conventional(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport, DoctrineChecker

    checker = DoctrineChecker(hub_path=tmp_path)
    # 6 non-conventional commits => exceeds threshold of 5 => violation added
    commits = _make_commits(
        [
            "WIP stuff",
            "another thing",
            "more work",
            "updates",
            "random commit",
            "yet another",
        ]
    )
    report = ComplianceReport(timestamp="ts", hub_path=tmp_path)
    checker._check_receipt_discipline(report, commits)
    assert len(report.violations) == 1
    v = report.violations[0]
    assert "conventional commits" in v.mandate
    assert v.severity == "low"
    assert v.violation_type == "drift"


def test_receipt_discipline_exactly_five_non_conventional_no_violation(tmp_path):
    """Threshold is >5 so exactly 5 should NOT trigger a violation."""
    from src.doctrine.doctrine_checker import ComplianceReport, DoctrineChecker

    checker = DoctrineChecker(hub_path=tmp_path)
    commits = _make_commits(["bad one", "bad two", "bad three", "bad four", "bad five"])
    report = ComplianceReport(timestamp="ts", hub_path=tmp_path)
    checker._check_receipt_discipline(report, commits)
    assert len(report.violations) == 0


def test_receipt_discipline_with_scope_format(tmp_path):
    """feat(scope): msg format should be accepted."""
    from src.doctrine.doctrine_checker import ComplianceReport, DoctrineChecker

    checker = DoctrineChecker(hub_path=tmp_path)
    commits = _make_commits(["feat(api): add endpoint", "fix(core): handle edge case"])
    report = ComplianceReport(timestamp="ts", hub_path=tmp_path)
    checker._check_receipt_discipline(report, commits)
    assert len(report.violations) == 0


# ---------------------------------------------------------------------------
# _check_mandatory_files tests (real filesystem via tmp_path)
# ---------------------------------------------------------------------------


def test_check_mandatory_files_all_missing(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport, DoctrineChecker

    checker = DoctrineChecker(hub_path=tmp_path)
    report = ComplianceReport(timestamp="ts", hub_path=tmp_path)
    checker._check_mandatory_files(report)
    assert len(report.violations) == 1
    v = report.violations[0]
    assert v.severity == "critical"
    assert v.violation_type == "missing_implementation"


def test_check_mandatory_files_all_present(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport, DoctrineChecker

    # Create all mandatory paths
    mandatory_files = [
        "src/main.py",
        "src/orchestration/",
        "src/healing/",
        "src/diagnostics/",
        "config/action_catalog.json",
        "scripts/start_nusyq.py",
        "AGENTS.md",
        "docs/doctrine/SYSTEM_OVERVIEW.md",
    ]
    for path in mandatory_files:
        full = tmp_path / path
        if path.endswith("/"):
            full.mkdir(parents=True, exist_ok=True)
        else:
            full.parent.mkdir(parents=True, exist_ok=True)
            full.touch()

    checker = DoctrineChecker(hub_path=tmp_path)
    report = ComplianceReport(timestamp="ts", hub_path=tmp_path)
    checker._check_mandatory_files(report)
    assert len(report.violations) == 0


def test_check_mandatory_files_partial_missing(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport, DoctrineChecker

    # Create only some mandatory paths
    (tmp_path / "src" / "orchestration").mkdir(parents=True)
    (tmp_path / "src" / "healing").mkdir(parents=True)

    checker = DoctrineChecker(hub_path=tmp_path)
    report = ComplianceReport(timestamp="ts", hub_path=tmp_path)
    checker._check_mandatory_files(report)
    assert len(report.violations) == 1
    evidence_str = report.violations[0].evidence[0]
    assert "Missing" in evidence_str


# ---------------------------------------------------------------------------
# _generate_insights tests
# ---------------------------------------------------------------------------


def test_generate_insights_excellent(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport, DoctrineChecker

    checker = DoctrineChecker(hub_path=tmp_path)
    report = ComplianceReport(timestamp="ts", hub_path=tmp_path, compliance_score=0.95)
    checker._generate_insights(report)
    assert any("Excellent" in i for i in report.insights)


def test_generate_insights_good(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport, DoctrineChecker

    checker = DoctrineChecker(hub_path=tmp_path)
    report = ComplianceReport(timestamp="ts", hub_path=tmp_path, compliance_score=0.80)
    checker._generate_insights(report)
    assert any("Good" in i for i in report.insights)


def test_generate_insights_low(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport, DoctrineChecker

    checker = DoctrineChecker(hub_path=tmp_path)
    report = ComplianceReport(timestamp="ts", hub_path=tmp_path, compliance_score=0.50)
    checker._generate_insights(report)
    assert any("Low" in i for i in report.insights)


def test_generate_insights_severity_counts(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport, DoctrineChecker, DoctrineViolation

    checker = DoctrineChecker(hub_path=tmp_path)
    violations = [
        DoctrineViolation("m", "drift", ["e"], "critical", "r"),
        DoctrineViolation("m", "drift", ["e"], "high", "r"),
        DoctrineViolation("m", "drift", ["e"], "medium", "r"),
        DoctrineViolation("m", "drift", ["e"], "low", "r"),
    ]
    report = ComplianceReport(
        timestamp="ts", hub_path=tmp_path, compliance_score=0.4, violations=violations
    )
    checker._generate_insights(report)
    insight_text = " ".join(report.insights)
    assert "CRITICAL" in insight_text
    assert "HIGH" in insight_text
    assert "MEDIUM" in insight_text
    assert "LOW" in insight_text


def test_generate_insights_most_common_violation_type(tmp_path):
    from src.doctrine.doctrine_checker import ComplianceReport, DoctrineChecker, DoctrineViolation

    checker = DoctrineChecker(hub_path=tmp_path)
    violations = [
        DoctrineViolation("m", "abandoned", ["e"], "low", "r"),
        DoctrineViolation("m", "abandoned", ["e"], "low", "r"),
        DoctrineViolation("m", "drift", ["e"], "low", "r"),
    ]
    report = ComplianceReport(
        timestamp="ts", hub_path=tmp_path, compliance_score=0.9, violations=violations
    )
    checker._generate_insights(report)
    insight_text = " ".join(report.insights)
    assert "abandoned" in insight_text


# ---------------------------------------------------------------------------
# check_compliance integration test (all subprocess calls stubbed)
# ---------------------------------------------------------------------------


def test_check_compliance_returns_report(tmp_path):
    """check_compliance returns a ComplianceReport even with no real git/grep."""
    from unittest.mock import MagicMock, patch

    from src.doctrine.doctrine_checker import ComplianceReport, DoctrineChecker

    checker = DoctrineChecker(hub_path=tmp_path)

    # Stub subprocess.run to always indicate command not found / no output
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""

    with patch("subprocess.run", return_value=mock_result):
        report = checker.check_compliance(commits_to_analyze=5)

    assert isinstance(report, ComplianceReport)
    assert report.hub_path == tmp_path
    assert report.total_mandates == 6
    assert isinstance(report.compliance_score, float)
    assert 0.0 <= report.compliance_score <= 1.0


def test_check_compliance_score_decreases_with_violations(tmp_path):
    """More violations should lower the compliance score."""
    from unittest.mock import MagicMock, patch

    from src.doctrine.doctrine_checker import DoctrineChecker

    checker = DoctrineChecker(hub_path=tmp_path)

    mock_fail = MagicMock()
    mock_fail.returncode = 1
    mock_fail.stdout = ""

    with patch("subprocess.run", return_value=mock_fail):
        report = checker.check_compliance(commits_to_analyze=5)

    # At minimum mandatory files are missing → at least 1 violation → score < 1.0
    assert report.compliance_score < 1.0


def test_check_compliance_parses_instruction_files(tmp_path):
    """Instruction .instructions.md files in .github/instructions/ are found."""
    from unittest.mock import MagicMock, patch

    from src.doctrine.doctrine_checker import DoctrineChecker

    inst_dir = tmp_path / ".github" / "instructions"
    inst_dir.mkdir(parents=True)
    (inst_dir / "FOO.instructions.md").touch()
    (inst_dir / "BAR.instructions.md").touch()

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""

    with patch("subprocess.run", return_value=mock_result):
        report = checker = DoctrineChecker(hub_path=tmp_path)
        report = checker.check_compliance(commits_to_analyze=0)

    assert len(report.instruction_files_parsed) == 2


def test_check_compliance_parses_doctrine_files(tmp_path):
    """Doctrine .md files in docs/doctrine/ are found."""
    from unittest.mock import MagicMock, patch

    from src.doctrine.doctrine_checker import DoctrineChecker

    doctrine_dir = tmp_path / "docs" / "doctrine"
    doctrine_dir.mkdir(parents=True)
    (doctrine_dir / "SYSTEM_OVERVIEW.md").touch()

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""

    with patch("subprocess.run", return_value=mock_result):
        checker = DoctrineChecker(hub_path=tmp_path)
        report = checker.check_compliance(commits_to_analyze=0)

    assert len(report.doctrine_files_parsed) == 1
