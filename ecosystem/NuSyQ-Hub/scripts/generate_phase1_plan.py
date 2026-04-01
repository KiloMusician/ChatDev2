from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

spec = spec_from_file_location("quest_prioritization", Path(__file__).resolve().parents[0] / "quest_prioritization.py")
qp_mod = module_from_spec(spec)
spec.loader.exec_module(qp_mod)
QuestPrioritizer = qp_mod.QuestPrioritizer


def run_plan(project_root: Path | None = None) -> dict:
    pr = QuestPrioritizer(project_root=project_root)
    plan = pr.create_phase1_focus_plan()
    out_path = Path("config") / "PHASE1_FOCUS_PLAN.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(str(plan), encoding="utf-8")
    return plan


if __name__ == "__main__":
    plan = run_plan()
    print("Phase1 plan generated")
