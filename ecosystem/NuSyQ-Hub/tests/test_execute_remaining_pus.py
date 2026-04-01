import scripts.execute_remaining_pus as pu_runner


def test_summarize_results_reports_error_and_failure():
    lines, success = pu_runner._summarize_results(
        {"PU-TODO-001": {"error": "Bridge not available"}}
    )

    assert success is False
    assert any("PU-TODO-001: ❌ Bridge not available" in line for line in lines)


def test_summarize_results_treats_missing_agent_response_as_failure():
    lines, success = pu_runner._summarize_results(
        {
            "PU-IMPL-001": {
                "alchemist": {"ok": True},
                "zod": None,
            }
        }
    )

    assert success is False
    assert any("PU-IMPL-001: 1/2 agents returned responses" in line for line in lines)
    assert any("⏱️ zod" in line for line in lines)


def test_parse_args_defaults():
    args = pu_runner._parse_args([])

    assert args.output_json is False
    assert args.timeout == pu_runner.DEFAULT_TIMEOUT


def test_parse_args_custom_values():
    args = pu_runner._parse_args(["--json", "--timeout", "15"])

    assert args.output_json is True
    assert args.timeout == 15
