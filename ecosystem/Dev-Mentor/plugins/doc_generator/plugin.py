"""Doc Generator Plugin — generates Markdown docs from Python source."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def plugin(input_data: str, config: dict) -> str:
    file_path = config.get("file") or input_data.strip()
    style = config.get("style", "brief")

    if not file_path:
        return json.dumps({"error": "Provide a file path as input or config.file"})

    p = Path(file_path)
    if not p.exists():
        return json.dumps({"error": f"File not found: {file_path}"})

    source = p.read_text()[:4000]  # cap context

    from llm_client import LLMClient
    llm = LLMClient()

    prompt = (
        f"Generate {'comprehensive' if style == 'full' else 'concise'} Markdown documentation "
        f"for this Python module. Include: overview, public API (functions/classes), "
        f"usage examples, and any important notes.\n\n```python\n{source}\n```"
    )

    doc = llm.generate(prompt, max_tokens=600, temperature=0.3,
                       system="You are a technical writer. Output clean Markdown only.")

    out_path = p.with_suffix(".docs.md")
    out_path.write_text(f"# {p.name}\n\n{doc}\n")

    return json.dumps({
        "ok": True,
        "source": file_path,
        "output": str(out_path),
        "chars": len(doc),
    })
