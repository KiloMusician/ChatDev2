import json
from pathlib import Path

from src.diagnostics.system_health_assessor import SystemHealthAssessment


def test_collect_and_render(tmp_path: Path):
    # Create a fake quick_system_analysis file
    data = {
        "working_files": [{"path": "src/a.py"}],
        "broken_files": [{"path": "src/b.py"}],
        "launch_pad_files": [],
        "enhancement_candidates": [],
    }
    analysis_path = tmp_path / "quick_system_analysis_123.json"
    analysis_path.write_text(json.dumps(data))

    assessor = SystemHealthAssessment()
    assessor.repo_root = tmp_path

    (tmp_path / "src" / "ai").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "orchestration" / "bridges").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "observability").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "tools").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "search").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "graphs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "state" / "reports").mkdir(parents=True, exist_ok=True)

    (tmp_path / "src" / "ai" / "ai_intermediary.py").write_text("# anchor\n", encoding="utf-8")
    (tmp_path / "src" / "consciousness" / "temple_of_knowledge").mkdir(
        parents=True, exist_ok=True
    )
    (tmp_path / "src" / "orchestration" / "advanced_consensus_voter.py").write_text(
        "# anchor\n", encoding="utf-8"
    )
    (tmp_path / "src" / "orchestration" / "specialization_learner.py").write_text(
        "# anchor\n", encoding="utf-8"
    )
    (tmp_path / "src" / "orchestration" / "bridges" / "consensus_voting_bridge.py").write_text(
        "# anchor\n", encoding="utf-8"
    )
    (tmp_path / "src" / "observability" / "tracing.py").write_text("# anchor\n", encoding="utf-8")
    (tmp_path / "src" / "observability" / "autonomy_dashboard.py").write_text(
        "# anchor\n", encoding="utf-8"
    )
    (tmp_path / "src" / "consciousness" / "temple_of_knowledge" / "floor_3_systems.py").write_text(
        "# anchor\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "tools" / "embeddings_exporter.py").write_text(
        "# anchor\n", encoding="utf-8"
    )
    (tmp_path / "src" / "tools" / "dependency_analyzer.py").write_text(
        "# anchor\n", encoding="utf-8"
    )
    (tmp_path / "src" / "tools" / "agent_task_router.py").write_text("# anchor\n", encoding="utf-8")
    (tmp_path / "src" / "search" / "smart_search.py").write_text("# anchor\n", encoding="utf-8")
    (tmp_path / "docs" / "graphs" / "README.md").write_text("# graph\n", encoding="utf-8")
    (tmp_path / "state" / "reports" / "graph_learning_latest.json").write_text(
        json.dumps({"status": "ok"}),
        encoding="utf-8",
    )

    collected = assessor.collect()
    assert collected
    assert collected["analysis_path"] == str(analysis_path)
    report = assessor.render_report(collected["health_metrics"], collected["roadmap"])
    assert "Overall Health Score" in report
    assert "Health Grade" in report
    assert "Advanced AI Readiness" in report
    readiness = collected["roadmap"]["advanced_ai_readiness"]
    assert readiness["ensemble_consensus"]["status"] == "ready"
    assert readiness["meta_learning"]["status"] == "partial"
    assert readiness["few_shot_adaptation"]["status"] == "partial"
    assert readiness["continual_learning"]["status"] == "partial"
    assert readiness["causal_inference"]["status"] == "partial"
    assert readiness["federated_learning"]["status"] == "partial"
    assert readiness["graph_learning"]["status"] == "partial"
