"""Code Formatter Plugin — formats Python code, optionally LLM-reviews it."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def plugin(input_data: str, config: dict) -> str:
    file_path = config.get("file")
    review = str(config.get("review", "false")).lower() == "true"

    if file_path:
        p = Path(file_path)
        if not p.exists():
            return json.dumps({"error": f"File not found: {file_path}"})
        code = p.read_text()
        target = p
    elif input_data.strip():
        code = input_data
        target = None
    else:
        return json.dumps({"error": "Provide code via input or config.file"})

    # Try ruff first, then autopep8, then nothing
    formatted = code
    formatter_used = "none"
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    for fmt, cmd in [
        ("ruff", ["ruff", "format", "--quiet", tmp_path]),
        ("autopep8", ["autopep8", "--in-place", tmp_path]),
    ]:
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=10)
            if r.returncode == 0:
                formatted = Path(tmp_path).read_text()
                formatter_used = fmt
                break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    Path(tmp_path).unlink(missing_ok=True)

    if target:
        target.write_text(formatted)

    result: dict = {"ok": True, "formatter": formatter_used, "lines": len(formatted.splitlines())}

    if review:
        from llm_client import LLMClient
        llm = LLMClient()
        review_text = llm.generate(
            f"Review this Python code briefly (2-3 bullet points on style/bugs):\n\n```python\n{formatted[:2000]}\n```",
            max_tokens=150,
            temperature=0.2,
        )
        result["review"] = review_text

    if not target:
        result["formatted_code"] = formatted

    return json.dumps(result, indent=2)
