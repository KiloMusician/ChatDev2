# Ollama Models Configuration

The `config/ollama_models.json` file defines which Ollama models are available to the hub and where the Ollama server is running.

## Schema

```json
{
  "ollama": {
    "base_url": "http://localhost:11435",
    "models": {
      "mistral": {"full_name": "mistral:latest"}
    }
  }
}
```

- **base_url**: URL where the Ollama API is accessible.
- **models**: Mapping of short names to their `full_name` as recognized by Ollama.

To add a custom model, add a new entry under `models`:

```json
"codellama": {"full_name": "codellama:latest"}
```

The short name (`codellama`) is used within the project, while `full_name` is sent to the Ollama API.
