"""Test Runner Plugin — runs pytest and optionally generates missing tests."""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def plugin(input_data: str, config: dict) -> str:
    target = config.get("target") or input_data.strip() or "tests/"
    generate = str(config.get("generate", "false")).lower() == "true"

    result = subprocess.run(
        [sys.executable, "-m", "pytest", target, "--tb=short", "-q", "--no-header"],
        capture_output=True, text=True, timeout=60
    )
    output = (result.stdout + result.stderr)[-2000:]
    passed = result.returncode == 0

    report = {
        "ok": passed,
        "returncode": result.returncode,
        "output": output,
        "target": target,
    }

    if generate and not passed:
        # Find source files to generate tests for
        src_files = list(Path(".").glob("*.py"))[:3]
        for src in src_files:
            if src.name.startswith("test_") or src.name in ("conftest.py",):
                continue
            code = src.read_text()[:2000]
            from llm_client import LLMClient
            llm = LLMClient()
            test_code = llm.generate(
                f"Write pytest unit tests for this Python module:\n\n```python\n{code}\n```\n"
                f"Output only valid Python test code, no explanation.",
                max_tokens=400,
                temperature=0.2,
            )
            test_path = Path(f"tests/test_{src.stem}_generated.py")
            test_path.parent.mkdir(exist_ok=True)
            test_path.write_text(test_code)
            report.setdefault("generated_tests", []).append(str(test_path))

    return json.dumps(report, indent=2)
