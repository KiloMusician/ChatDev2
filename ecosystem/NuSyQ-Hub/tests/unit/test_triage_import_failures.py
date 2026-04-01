from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

spec = spec_from_file_location(
    "triage_import_failures",
    Path(__file__).resolve().parents[2] / "scripts" / "triage_import_failures.py",
)
triage_mod = module_from_spec(spec)
spec.loader.exec_module(triage_mod)
simple_triage = triage_mod.simple_triage


def test_triage_creates_queue(tmp_path):
    rpt = tmp_path / "import_failures_programmatic.json"
    rpt.write_text(
        '{"foo_module": "ImportError: something", "skipped_mod": "skipped_heavy_imports"}',
        encoding="utf-8",
    )
    out = tmp_path / "data" / "unified_pu_queue.json"
    created = simple_triage(rpt, out)
    assert created == 1
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "foo_module" in content
