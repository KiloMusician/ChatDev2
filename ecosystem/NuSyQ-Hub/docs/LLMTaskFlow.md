# LLM Task Flow Helper

The `llm_task_suggester.py` script queries the internal Ollama models to
propose which repository script should run next.  It lists available scripts in
the `scripts/` directory, builds a prompt that optionally includes a preset
(e.g. `test` or `setup`), and sends it to the model via `OllamaHub`.

Results are stored using the `conversation_manager` so other tools or editors
can review previous suggestions.  This module can be wired into a VS Code
extension so Copilot can request task suggestions and present them in the
interface.

## Usage

```bash
python scripts/llm_task_suggester.py --preset test
```

If models are available the script prints the model's recommendation and logs
the interaction.
