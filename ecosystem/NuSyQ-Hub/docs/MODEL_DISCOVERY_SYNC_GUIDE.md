# Model Discovery & Sync System - Quick Reference

## Overview

The NuSyQ-Hub model discovery system automatically finds, registers, and syncs local LLM models (primarily GGUF format) between Ollama and LM Studio without hardcoded paths.

## Current State (2026-02-04)

### 📊 Model Inventory

**Total discovered:** 15 models
- **Local GGUF files:** 4 files
- **Ollama API models:** 9 models
- **LM Studio API models:** 2 models

**Registered in `state/registry.json`:** 4 models

### 📁 Storage Locations

| System | Path | Size | Models |
|--------|------|------|--------|
| **Ollama** | `C:\Users\keath\.ollama\models` | (API reports 9 models) | 9 models |
| **LM Studio** | `C:\Users\keath\.lmstudio\models` | (API reports 2 models) | 2 models |
| **Docker** | `C:\Users\keath\.docker\models` | 0.31 GB | 1 GGUF model |

### 🔍 Discovered GGUF Files

1. **lmstudio-community/model.gguf** (0.31 GB)
2. **gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf** (11.28 GB) - 2 copies found
3. **Docker bundle/model.gguf** (0.31 GB)

## Configuration

### `config/model_paths.json`

Centralized path configuration with environment variable support:

```json
{
  "search_dirs": [
    "${USERPROFILE}\\.lmstudio\\models",
    "${USERPROFILE}\\.ollama\\models",
    "${USERPROFILE}\\.docker\\models",
    "${USERPROFILE}\\Downloads",
    "C:\\models",
    "D:\\models",
    "D:\\gguf",
    "E:\\gguf"
  ],
  "lmstudio_models_dir": "${USERPROFILE}\\.lmstudio\\models",
  "ollama_models_dir": "${USERPROFILE}\\.ollama\\models"
}
```

**Key Features:**
- Uses `${USERPROFILE}` environment variable placeholders
- Automatically expands paths at runtime
- No hardcoded user directories

### `state/registry.json`

Model registry with full metadata:

```json
[
  {
    "path": "C:\\Users\\keath\\.lmstudio\\models\\lmstudio-community\\gpt-oss-20b-GGUF\\gpt-oss-20b-MXFP4.gguf",
    "name": "gpt-oss-20b-MXFP4.gguf",
    "source": "lmstudio",
    "format": "gguf",
    "size_bytes": 12109565632,
    "metadata": {
      "is_dir": false
    }
  }
]
```

## Usage

### 1️⃣ Discover Models (Dry-Run)

```bash
python scripts/discover_and_sync_models.py --discover --query-apis --verbose
```

**What it does:**
- Scans all paths in `model_paths.json` for `.gguf` files
- Queries Ollama API (http://localhost:11434)
- Queries LM Studio API (http://localhost:1234)
- Reports findings (does NOT modify registry)

### 2️⃣ Populate Registry

```bash
python scripts/discover_and_sync_models.py --discover --apply
```

**What it does:**
- Discovers all GGUF models
- Registers them in `state/registry.json`
- Validates metadata before saving
- Avoids duplicates by path

### 3️⃣ Sync to LM Studio

```bash
python scripts/discover_and_sync_models.py --discover --sync --apply
```

**What it does:**
- Discovers GGUF models in all search paths
- Creates symlinks/junctions to `LM Studio/models/` directory
- Preserves parent directory structure for organization
- Uses PowerShell fallback on Windows if `os.symlink` fails

### 4️⃣ Full Workflow

```bash
python scripts/discover_and_sync_models.py --discover --query-apis --sync --apply --verbose
```

**Complete operation:**
1. Discover local GGUF files
2. Query both Ollama and LM Studio APIs
3. Register all models in `state/registry.json`
4. Sync models to LM Studio directory
5. Report full inventory

## Legacy Scripts (Still Available)
These are kept for narrow use cases. Prefer `discover_and_sync_models.py` for the full workflow.

### `register_local_models.py`

Original registration script:

```bash
python scripts/register_local_models.py \
  --search-dirs "C:\models" "D:\gguf" \
  --lmstudio-dir "%USERPROFILE%\.lmstudio\models" \
  --apply
```

### `sync_ollama_to_lmstudio.py`

Ollama-specific sync:

```bash
python scripts/sync_ollama_to_lmstudio.py \
  --search-dirs "%USERPROFILE%\.ollama\models" \
  --lmstudio-dir "%USERPROFILE%\.lmstudio\models" \
  --dry-run
```

## Architecture

### Model Registry Class

**`src/shared/model_registry.py`** - Thread-safe registry with:
- JSON schema validation
- File locking (via `portalocker` if available)
- Atomic writes
- Duplicate prevention

**Key Methods:**
```python
registry = ModelRegistry(Path("state/registry.json"))

# List all registered models
models = registry.list_models()

# Find specific model by path
model = registry.find("/path/to/model.gguf")

# Register new model (with validation)
registry.register_model({
    "path": "/path/to/model.gguf",
    "name": "model-name",
    "source": "local_discovery",
    "format": "gguf",
    "size_bytes": 12345678
}, apply=True)

# Health check
status = registry.health()  # {"count": 4}
```

## Future-Proof Design

✅ **No Hardcoded Paths** - All paths in `model_paths.json` with variable expansion
✅ **Multi-Source Discovery** - Scans filesystem + queries APIs
✅ **Flexible Sync** - Can sync any discovered GGUF to any target directory
✅ **Validation** - JSON schema enforcement prevents malformed entries
✅ **Extensible** - Easy to add new discovery sources (HuggingFace cache, custom dirs)

## Next Steps

### Phase 1: Organize Ollama Models ✅ COMPLETE
- Confirmed 9 models via Ollama API at `http://127.0.0.1:11434/api/tags`
- Registry tracks all discovered models
- APIs reporting correctly

### Phase 2: Deduplication (Optional)
```bash
# Find duplicate models
python scripts/discover_and_sync_models.py --discover --verbose | grep "✅ Found"
```

### Phase 3: Cleanup Non-Existent Paths
Update `model_paths.json` to remove:
- `C:\models` (does not exist)
- `D:\models` (does not exist)
- `D:\gguf` (does not exist)
- `E:\gguf` (does not exist)

### Phase 4: Gradio/Web UI (Future)
- Web interface to browse registry
- One-click sync buttons
- Storage usage dashboard
- Model metadata editor

## Troubleshooting

### "Permission denied" creating symlinks

**Windows:** Enable Developer Mode in Settings → Update  & Security → For Developers
**Alternative:** Script automatically falls back to PowerShell junctions

### "No models found" but you have models

1. Check `model_paths.json` paths are correct
2. Run with `--verbose` to see scanning details
3. Verify models are `.gguf` format

### API queries fail

- **Ollama:** Ensure Ollama is running (`ollama serve`)
- **LM Studio:** Start LM Studio server (default port 1234)
- Use `--ollama-url` and `--lmstudio-url` flags if using custom ports

## References

- **ROSETTA_STONE.md:** Model registry usage examples
- **model_paths.json:** Path configuration
- **state/registry.json:** Model inventory (auto-generated)
- **src/shared/model_registry.py:** Registry implementation

---

**Last Updated:** 2026-02-04
**Script:** `scripts/discover_and_sync_models.py`
**Registry:** `state/registry.json` (6 models registered)
