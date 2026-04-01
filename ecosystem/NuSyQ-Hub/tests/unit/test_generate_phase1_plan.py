from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

spec = spec_from_file_location(
    "generate_phase1_plan",
    Path(__file__).resolve().parents[2] / "scripts" / "generate_phase1_plan.py",
)
plan_mod = module_from_spec(spec)
spec.loader.exec_module(plan_mod)
run_plan = plan_mod.run_plan


def test_run_phase1_plan():
    plan = run_plan(Path("."))
    assert isinstance(plan, dict)
    assert "objective" in plan
