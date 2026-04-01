# Ollama VS Code Integration

The VS Code extension in this repository exposes a simple workflow for working with local
Ollama models.

## Workflow

1. The extension uses the `src/ai/ollama_hub.py` module to query and load models.
2. When the `ollama.selectModel` command is executed, the extension runs a short
   Python snippet to call `ollama_hub.list_models()` and displays the results in a
   VS Code **Quick Pick**.
3. After a model is chosen, the extension triggers `ollama_hub.load_model()`.
   On success the selected model name is shown in the status bar.  Any errors
   during loading are surfaced via VS Code notifications.

This lightweight approach avoids maintaining a long‑running server and instead
invokes Python on demand using a minimal CLI wrapper.
