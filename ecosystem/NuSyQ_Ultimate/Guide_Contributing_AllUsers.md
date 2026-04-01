<!--
╔══════════════════════════════════════════════════════════════════════════╗
║ ΞNuSyQ OmniTag Metadata                                                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║ FILE-ID: nusyq.docs.root.contributing                                  ║
║ TYPE: Markdown Document                                                 ║
║ STATUS: Active                                                          ║
║ VERSION: 1.0.0                                                          ║
║ TAGS: [contributing, development, guidelines, github-standard]         ║
║ CONTEXT: Σ∆ (Meta Layer)                                               ║
║ AGENTS: [AllAgents]                                                     ║
║ DEPS: [NuSyQ_Root_README.md, knowledge-base.yaml]                                 ║
║ INTEGRATIONS: [Git, GitHub]                                            ║
║ CREATED: 2025-10-05                                                     ║
║ UPDATED: 2025-10-06                                                     ║
║ AUTHOR: Claude Code                                                     ║
║ STABILITY: High (Active Standard)                                       ║
╚══════════════════════════════════════════════════════════════════════════╝
-->

# Contributing to NuSyQ

Welcome to the NuSyQ AI-powered developer workspace! This guide will help you get started with contributing to the project.

---

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/KiloMusician/NuSyQ.git
   cd NuSyQ
   ```

2. **Run the orchestrator** (automated setup)
   ```powershell
   .\NuSyQ.Orchestrator.ps1
   ```

3. **Verify installation**
   ```powershell
   python -c "from config.config_manager import ConfigManager; print('OK')"
   ```

For detailed setup instructions, see [docs/QUICK_START.md](docs/QUICK_START.md).

---

## Prerequisites

### Required Tools
- **Python 3.8+** - Core runtime
- **Git** - Version control
- **VS Code** - Primary development environment
- **Ollama** - Local LLM inference (install from https://ollama.ai)
- **PowerShell** - For orchestrator scripts (Windows) or PowerShell Core (cross-platform)

### Recommended Tools
- **Node.js** - For JavaScript tooling
- **Docker** - Container support (optional)
- **GitHub CLI (`gh`)** - Simplified GitHub workflows

---

## Authentication Setup

### GitHub Authentication (Required for Extensions)

NuSyQ uses GitHub CLI for authentication. Choose one of these methods:

#### Method 1: GitHub CLI (Recommended)
```bash
# Install GitHub CLI
winget install GitHub.CLI  # Windows
brew install gh            # macOS
sudo apt install gh        # Linux

# Authenticate
gh auth login
```

Follow the prompts:
1. Select "GitHub.com"
2. Choose "HTTPS" or "SSH" (HTTPS is easier)
3. Choose "Login with a web browser" (easiest)
4. Copy the one-time code and paste in browser
5. Authorize GitHub CLI

#### Method 2: Personal Access Token (PAT)
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `workflow`, `read:org`
4. Generate and copy the token
5. Set environment variable:
   ```powershell
   # Windows
   $env:GITHUB_TOKEN = "ghp_YOUR_TOKEN_HERE"

   # Linux/macOS
   export GITHUB_TOKEN="ghp_YOUR_TOKEN_HERE"
   ```

#### Method 3: SSH Keys
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# Add to SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key and add to GitHub
cat ~/.ssh/id_ed25519.pub
# Paste at: https://github.com/settings/ssh/new
```

### VS Code Extensions Authentication

VS Code extensions (GitHub Copilot, Continue.dev) authenticate separately:

1. **GitHub Copilot**
   - Open VS Code
   - Press `Ctrl+Shift+P` → "GitHub Copilot: Sign In"
   - Follow browser authentication

2. **Continue.dev** (for Ollama)
   - No authentication needed
   - Configure in `.vscode/settings.json`:
     ```json
     {
       "continue.telemetryEnabled": false,
       "continue.enableTabAutocomplete": true
     }
     ```

---

## Development Setup

### 1. Create Virtual Environment
```bash
python -m venv .venv

# Activate
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # Linux/macOS
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r mcp_server/requirements.txt
```

### 3. Configure Environment
```bash
# Copy example environment
cp .env.example .env

# Edit with your settings
code .env
```

### 4. Start MCP Server
```bash
python mcp_server/main.py
```

Server will be available at: http://localhost:3000

### 5. Verify Ollama Models
```bash
# List installed models
ollama list

# Pull recommended coding model
ollama pull qwen2.5-coder:14b
```

---

## Project Structure

```
NuSyQ/
├── AI_Hub/                  # AI integration guides and documentation
├── ChatDev/                 # Multi-agent software development framework
├── config/                  # Configuration management
│   ├── config_manager.py
│   └── flexibility_manager.py
├── mcp_server/              # Model Context Protocol server
│   ├── main.py             # FastAPI server
│   ├── src/                # Service modules
│   └── tests/              # Test suite
├── scripts/                 # Utility scripts
├── docs/                    # Additional documentation
├── .vscode/                 # VS Code configuration
├── nusyq.manifest.yaml      # System manifest
├── NuSyQ.Orchestrator.ps1   # Automated setup
└── knowledge-base.yaml      # Learning log

Key files to know:
- nusyq.manifest.yaml - Defines all packages, models, extensions
- NuSyQ.Orchestrator.ps1 - Runs automated setup
- nusyq_chatdev.py - ChatDev + Ollama integration
- knowledge-base.yaml - Persistent learning system
```

---

## Development Workflow

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow code style guidelines (see below)
   - Add tests for new features
   - Update documentation

3. **Test your changes**
   ```bash
   # Run tests
   pytest mcp_server/tests/

   # Validate manifest
   python scripts/validate_manifest.py

   # Check code quality
   python deep_analysis.py
   ```

4. **Commit with clear messages**
   ```bash
   git add .
   git commit -m "feat: add new feature X"
   ```

   Use conventional commits:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation
   - `style:` - Code style (formatting)
   - `refactor:` - Code refactoring
   - `test:` - Adding tests
   - `chore:` - Maintenance

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name

   # Create PR using GitHub CLI
   gh pr create --title "Add feature X" --body "Description of changes"
   ```

### Code Style Guidelines

#### Python
- **Style:** PEP 8 compliant
- **Line length:** Max 120 characters
- **Imports:** Alphabetically ordered
- **Type hints:** Required for all public functions
- **Docstrings:** Google style
- **Encoding:** Always specify `encoding='utf-8'` for file operations

Example:
```python
from pathlib import Path
from typing import Dict, List, Optional

def process_data(input_path: Path, options: Optional[Dict] = None) -> List[str]:
    """
    Process data from input file.

    Args:
        input_path: Path to input file
        options: Optional processing options

    Returns:
        List of processed results
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = f.read()

    return data.split('\n')
```

#### Logging
- Use lazy % formatting: `logger.info("Message: %s", value)`
- Not f-strings: `logger.info(f"Message: {value}")` ❌

#### Error Handling
- Catch specific exceptions, not broad `Exception`
- Always log exceptions: `logger.error("Failed: %s", e)`
- Use `subprocess.run()` with explicit `check=True` or `check=False`

#### Type Hints
- Use `Optional[T]` for nullable types
- Use `Dict`, `List`, `Set` from `typing` (Python 3.8)
- Use `dict`, `list`, `set` for Python 3.9+
- Add return types to all functions: `-> None`, `-> str`, etc.

---

## Running Tests

### Unit Tests
```bash
pytest mcp_server/tests/ -v
```

### Integration Tests
```bash
# Start MCP server in one terminal
python mcp_server/main.py

# Run integration tests in another
pytest tests/integration/ -v
```

### Code Quality Checks
```bash
# Type checking
mypy config/ mcp_server/

# Linting
flake8 config/ mcp_server/ --max-line-length=120

# Code analysis
python deep_analysis.py
```

---

## Common Tasks

### Adding a New Ollama Model
1. Edit `nusyq.manifest.yaml`:
   ```yaml
   ollama_models:
     - your-model-name:7b
   ```

2. Pull the model:
   ```bash
   ollama pull your-model-name:7b
   ```

3. Verify in ChatDev:
   ```bash
   python nusyq_chatdev.py --setup-only
   ```

### Adding a VS Code Extension
1. Edit `nusyq.manifest.yaml`:
   ```yaml
   vscode_extensions:
     - publisher.extension-name
   ```

2. Install manually or re-run orchestrator:
   ```bash
   code --install-extension publisher.extension-name
   # OR
   .\NuSyQ.Orchestrator.ps1
   ```

### Updating Configuration
1. Edit `config/environment.json` or relevant YAML
2. Reload configuration:
   ```python
   from config.config_manager import ConfigManager
   config = ConfigManager()
   config.reload_all()
   ```

---

## Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
# Windows: Restart from system tray
# Linux: systemctl restart ollama
# macOS: Restart Ollama app
```

### GitHub Authentication Failed
```bash
# Check authentication status
gh auth status

# Re-authenticate
gh auth logout
gh auth login
```

### MCP Server Won't Start
```bash
# Check port 3000 is available
netstat -ano | findstr :3000  # Windows
lsof -i :3000                 # Linux/macOS

# Check logs
tail -f Logs/mcp_server.log
```

### ChatDev API Key Error
```bash
# Verify environment variable
echo $OPENAI_API_KEY  # Should be 'ollama-local-model' or actual key

# Re-run setup
python nusyq_chatdev.py --setup-only
```

---

## Reporting Issues

### Before Creating an Issue
1. Check [existing issues](https://github.com/KiloMusician/NuSyQ/issues)
2. Run `python deep_analysis.py` to check for known problems
3. Review `knowledge-base.yaml` for similar issues

### Creating a Good Issue
Include:
- **Environment:** OS, Python version, Ollama version
- **Steps to reproduce:** Exact commands run
- **Expected behavior:** What should happen
- **Actual behavior:** What actually happened
- **Logs:** Relevant error messages
- **Configuration:** Relevant sections from manifest/config

Example issue template:
```markdown
## Environment
- OS: Windows 11
- Python: 3.12
- Ollama: 0.1.17

## Problem
ChatDev fails with API key error

## Steps to Reproduce
1. Run `python nusyq_chatdev.py --task "test"`
2. Error appears immediately

## Error Message
```
KeyError: 'OPENAI_API_KEY'
```

## Expected
Should use Ollama without requiring API key

## Attempted Fixes
- Checked `.env.ollama` exists
- Verified Ollama is running
```

---

## Finding TODOs

Known TODO items are tracked in:
- `TODO_REPORT.md` - Generated list of all TODOs
- GitHub Issues with `todo` label
- `knowledge-base.yaml` under `improvements` section

To find TODOs in code:
```bash
# Search all Python files
grep -r "TODO" --include="*.py" .

# Search with context
grep -rn "TODO\|FIXME" --include="*.py" . | head -20
```

---

## Documentation

### Adding Documentation
- **Guides:** Place in `AI_Hub/` or `docs/`
- **Code docs:** Use docstrings in modules
- **API docs:** Update `mcp_server/NuSyQ_Root_README.md`
- **Changes:** Update `knowledge-base.yaml`

### Documentation Style
- Use Markdown with GitHub flavor
- Include code examples
- Add links to related docs
- Keep NuSyQ_Root_README.md concise, detailed docs elsewhere

---

## Release Process

1. **Update version** in `nusyq.manifest.yaml`
2. **Update CHANGELOG.md** with changes
3. **Run full test suite**
4. **Tag release**:
   ```bash
   git tag -a v1.2.0 -m "Release v1.2.0"
   git push origin v1.2.0
   ```
5. **Create GitHub release** with notes

---

## Getting Help

- **Documentation:** Check `AI_Hub/` and `docs/`
- **Discussions:** GitHub Discussions (if enabled)
- **Issues:** GitHub Issues for bugs/features
- **Knowledge Base:** `knowledge-base.yaml` for common problems

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please:
- Be respectful and considerate
- Welcome newcomers
- Focus on constructive feedback
- Respect differing viewpoints
- Report unacceptable behavior to maintainers

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

Built with:
- **Ollama** - Local LLM inference
- **FastAPI** - MCP server framework
- **ChatDev** - Multi-agent framework
- **VS Code** - Development environment
- **Python** - Core language

Special thanks to all contributors!

---

**Questions?** Open an issue or check the [Quick Start Guide](docs/QUICK_START.md).
