"""Suggest repository scripts to run via internal LLM.

This utility queries the configured Ollama model through the `OllamaHub`
wrapper and logs the conversation using ``conversation_manager``. It can be
extended to integrate with VS Code or other front-ends so Copilot or other
agents can discover useful entry points in the repository.

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["LLM", "Python", "AI", "Ollama"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import argparse
from pathlib import Path

from ai.conversation_manager import conversation_manager
from ai.ollama_hub import ollama_hub


def gather_scripts() -> list[str]:
    """Return a list of available Python scripts in the ``scripts`` folder."""
    scripts_dir = Path(__file__).parent
    return [p.name for p in scripts_dir.glob("*.py") if p.name != Path(__file__).name]


def suggest_script(preset: str | None = None) -> str | None:
    """Ask the internal LLM which script should run next.

    Parameters
    ----------
    preset:
        Optional hint describing the current goal (e.g. ``"test"`` or
        ``"setup"``).
    """
    available = gather_scripts()
    prompt = [
        "The repository contains the following runnable scripts:",
        *[f"- {name}" for name in available],
        "Which script should run next?",
    ]
    if preset:
        prompt.append(f"The current preset is: {preset}.")
    prompt_text = "\n".join(prompt)

    models = ollama_hub.list_models()
    if not models:
        print("No Ollama models available.")
        return None

    model = models[0] if isinstance(models, list) else models
    result = ollama_hub.ollama.generate(model=model, prompt=prompt_text)
    if not result:
        print("Ollama generation failed.")
        return None

    response = result.get("response") or result.get("data") or str(result)
    conversation_manager.add_message("llm_task_suggester", "user", prompt_text)
    conversation_manager.add_message("llm_task_suggester", "assistant", response)
    return response


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", help="Optional task preset", default=None)
    args = parser.parse_args()

    suggestion = suggest_script(args.preset)
    if suggestion:
        print(suggestion)


if __name__ == "__main__":
    main()
