# Continue Extension Configuration

**Status**: ✅ Configured for NuSyQ-Hub with multi-provider support

---

## Available Models

### 1. Claude Sonnet 3.5 (Anthropic API) - **RECOMMENDED**
- **Provider**: Anthropic
- **Model**: `claude-3-5-sonnet-20241022`
- **Use for**: Complex refactoring, architecture decisions, code reviews
- **Requires**: `ANTHROPIC_API_KEY` environment variable

### 2. GPT-4 Turbo (OpenAI)
- **Provider**: OpenAI
- **Model**: `gpt-4-turbo-preview`
- **Use for**: General coding, alternative perspective
- **Requires**: `OPENAI_API_KEY` environment variable

### 3. Ollama Qwen 2.5 Coder (Local) - **DEFAULT**
- **Provider**: Ollama (localhost:11434)
- **Model**: `qwen2.5-coder:7b`
- **Use for**: Fast local inference, autocomplete, quick edits
- **Requires**: Ollama running locally (already configured)

### 4. Ollama DeepSeek Coder (Local)
- **Provider**: Ollama
- **Model**: `deepseek-coder-v2:16b`
- **Use for**: Alternative local model, specialized code tasks
- **Requires**: Ollama running locally

### 5. GitHub Copilot
- **Provider**: Free trial
- **Model**: `gpt-4o`
- **Use for**: If Copilot subscription active
- **Requires**: GitHub Copilot subscription

---

## Setup Instructions

### Option 1: Use Ollama (No API Keys Needed)

**Already configured!** Just make sure Ollama is running:

```powershell
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it:
ollama serve
```

**Models available**:
- ✅ `qwen2.5-coder:7b` (default chat)
- ✅ `qwen2.5-coder:14b` (larger, more capable)
- ✅ `deepseek-coder-v2:16b` (specialized)
- ✅ `nomic-embed-text:latest` (embeddings for codebase search)

### Option 2: Add Anthropic API (Recommended for Best Quality)

1. Get your API key from: https://console.anthropic.com/settings/keys

2. Set environment variable:

**PowerShell (session)**:
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-api03-..."
```

**PowerShell (permanent)**:
```powershell
[System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', 'sk-ant-api03-...', 'User')
```

**Bash/Linux/macOS**:
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
# Add to ~/.bashrc or ~/.zshrc for persistence
```

3. Restart VS Code to pick up new environment variable

4. In Continue chat, select "Claude Sonnet 3.5 (Anthropic API)" from model dropdown

### Option 3: Add OpenAI API

1. Get API key from: https://platform.openai.com/api-keys

2. Set environment variable:

```powershell
$env:OPENAI_API_KEY = "sk-..."
```

3. Restart VS Code

---

## Custom Commands for NuSyQ

The config includes 3 NuSyQ-specific slash commands:

### `/nusyq-analyze`
Analyzes code for:
- Integration with orchestration patterns
- FILE_PRESERVATION_MANDATE compliance
- Observability (tracing/logging)
- Test coverage needs

**Usage**:
```
Select code → Continue chat → /nusyq-analyze
```

### `/doctrine-check`
Validates code against NuSyQ doctrine:
- Edit-first principle (no unnecessary files)
- No circular imports
- No blocking operations without timeout
- Proper error handling
- Receipt discipline

**Usage**:
```
Select code → Continue chat → /doctrine-check
```

### `/wire-action`
Generates boilerplate for new start_nusyq.py action:
- Handler function
- Dispatch map entry
- Help text
- action_catalog.json entry
- Contract test

**Usage**:
```
Select/describe action → Continue chat → /wire-action
```

---

## Troubleshooting

### Error: "nomic-embed-text:latest does not support chat"

**Cause**: Embedding model was selected for chat instead of chat model.

**Fix**:
1. Open Continue chat panel
2. Click model dropdown (top of panel)
3. Select a **chat model**:
   - "Ollama Qwen 2.5 Coder (Local)" - local, fast
   - "Claude Sonnet 3.5" - best quality (if API key set)
   - "GPT-4 Turbo" - alternative cloud (if API key set)

**Note**: `nomic-embed-text` is for **codebase search only**, not chat.

### Error: "Failed to connect to Ollama"

**Fix**:
```powershell
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it:
ollama serve
```

### Error: "API key not found"

**For Anthropic**:
```powershell
# Verify key is set
echo $env:ANTHROPIC_API_KEY

# If empty, set it:
$env:ANTHROPIC_API_KEY = "sk-ant-api03-..."
```

**For OpenAI**:
```powershell
echo $env:OPENAI_API_KEY
$env:OPENAI_API_KEY = "sk-..."
```

**Then restart VS Code.**

### Autocomplete not working

**Check**:
1. Continue extension enabled in VS Code
2. `tabAutocompleteModel` is set to Ollama model (already configured)
3. Ollama is running: `curl http://localhost:11434/api/tags`

**If using Anthropic/OpenAI**, update `tabAutocompleteModel` in config.json:
```json
"tabAutocompleteModel": {
  "title": "Claude Sonnet 3.5",
  "provider": "anthropic",
  "model": "claude-3-5-sonnet-20241022"
}
```

---

## Configuration File Location

**Workspace config**: `.continue/config.json` (this file applies to NuSyQ-Hub only)

**User config**: `~/.continue/config.json` (global, all workspaces)

**Priority**: Workspace config overrides user config.

---

## Recommended Workflow

### Quick Edits (Local)
1. Select code
2. Continue chat → **"Ollama Qwen 2.5 Coder"**
3. Ask for change
4. Accept diff

### Complex Refactoring (Cloud)
1. Select code
2. Continue chat → **"Claude Sonnet 3.5"** (best) or **"GPT-4 Turbo"**
3. Use `/nusyq-analyze` for context-aware analysis
4. Accept suggested changes

### New Action Wiring
1. Describe action intent
2. Continue chat → **"Claude Sonnet 3.5"**
3. Use `/wire-action`
4. Review generated boilerplate

### Code Review
1. Select function/class
2. Continue chat → **"Claude Sonnet 3.5"**
3. Use `/doctrine-check` to validate against NuSyQ principles

---

## Model Selection Guide

| Task | Recommended Model | Why |
|------|------------------|-----|
| Autocomplete | Qwen 2.5 Coder 7B (Local) | Fast, low latency |
| Quick edits | Qwen 2.5 Coder 7B (Local) | Instant, no API cost |
| Code review | Claude Sonnet 3.5 (API) | Best understanding of architecture |
| Refactoring | Claude Sonnet 3.5 (API) | Handles complex context |
| Documentation | GPT-4 Turbo (API) | Alternative perspective |
| Codebase search | nomic-embed-text (Local) | Already configured for embeddings |

---

## Testing the Setup

### Test 1: Local Ollama
```
Continue chat → Select "Ollama Qwen 2.5 Coder"
Type: "Explain what this function does"
```

**Expected**: Fast response from local Ollama

### Test 2: Anthropic API (if configured)
```
Continue chat → Select "Claude Sonnet 3.5"
Type: "Analyze this code for potential issues"
```

**Expected**: High-quality analysis from Claude

### Test 3: Custom Command
```
Select a function → Continue chat → /nusyq-analyze
```

**Expected**: NuSyQ-specific analysis with doctrine checks

### Test 4: Autocomplete
```
Start typing a function in any .py file
Wait 1-2 seconds
```

**Expected**: Gray autocomplete suggestion appears

---

## Next Steps

1. **Set API keys** (optional but recommended):
   - Anthropic: https://console.anthropic.com/settings/keys
   - OpenAI: https://platform.openai.com/api-keys

2. **Try the custom commands**:
   - Select code and use `/nusyq-analyze`
   - Use `/wire-action` to generate new action boilerplate

3. **Experiment with models**:
   - Compare local (Qwen) vs cloud (Claude/GPT-4) responses
   - Find what works best for your workflow

4. **Explore Continue features**:
   - `@codebase` - search entire codebase
   - `@terminal` - include terminal output in context
   - `@docs` - include documentation

---

**Status**: ✅ Ready to use
**Default model**: Ollama Qwen 2.5 Coder (no API key needed)
**Upgrade path**: Add ANTHROPIC_API_KEY for best quality

**Questions?** Ask Continue: "How do I use /nusyq-analyze?"
