import scripts.comprehensive_modernization_audit as audit


def test_parse_args_applies_mode_and_filters():
    args = audit.parse_args(
        [
            "--mode",
            "warehouse",
            "--exclude-paths",
            "tmp",
            ".venv",
            "--include-paths",
            "src",
            "--warehouse-projects",
            "proj1",
            "proj2",
            "--repos",
            "NuSyQ-Hub",
        ]
    )

    assert args.mode == "warehouse"
    # user-provided include first, then mode-provided include_paths
    assert args.include_paths == ["src", "ChatDev/WareHouse"]
    assert args.exclude_paths == ["tmp", ".venv"]
    assert args.warehouse_projects == ["proj1", "proj2"]
    assert args.repos == ["NuSyQ-Hub"]
    assert args.skip_culture_ship is False


def test_parse_args_can_skip_culture_ship():
    args = audit.parse_args(["--skip-culture-ship"])

    assert args.skip_culture_ship is True


def test_matches_filters_honors_excludes_and_includes():
    auditor = audit.ComprehensiveModernizationAuditor(
        include_paths=["src"],
        exclude_paths=["node_modules", ".venv"],
        warehouse_projects=None,
        target_repos=None,
        skip_culture_ship=True,
    )

    # excluded anywhere in path -> False
    assert auditor._matches_filters("project/node_modules/pkg/file.py") is False
    # include_paths acts as allowlist
    assert auditor._matches_filters("src/app/main.py") is True
    # not in include_paths -> False
    assert auditor._matches_filters("docs/readme.md") is False
