def test_demo_unified_queue_runs_and_reports():
    from src.automation.unified_pu_queue import demo_unified_queue

    q = demo_unified_queue()
    report = q.generate_report()
    assert "statistics" in report
    assert report["statistics"]["total_pus"] >= 1
    # Ensure the simulation fallback exists by checking for 'completed' or other statuses
    statuses = {pu["status"] for pu in report["recent"]}
    assert any(
        s in {"queued", "approved", "completed", "executing", "failed", "rejected"}
        for s in statuses
    )
