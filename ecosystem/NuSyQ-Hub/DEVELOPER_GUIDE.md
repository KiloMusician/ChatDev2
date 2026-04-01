# NuSyQ-Hub Developer Guide

Complete guide for developers working on NuSyQ-Hub.

## 📋 Table of Contents

- [Development Setup](#development-setup)
- [Architecture Overview](#architecture-overview)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [AI System Integration](#ai-system-integration)
- [Common Workflows](#common-workflows)
- [Troubleshooting](#troubleshooting)

## 🛠️ Development Setup

### Prerequisites
- Python 3.12+
- Git
- Ollama (optional, for local LLM)
- Docker (optional, for containerized development)

### Initial Setup
```bash
# Clone and setup
git clone https://github.com/yourusername/NuSyQ-Hub.git
cd NuSyQ-Hub

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run tests to verify setup
pytest tests/ -v
```

## 🏗️ Architecture Overview

### Core Components

```
NuSyQ-Hub/
├── src/
│   ├── integration/          # AI system integrations
│   │   ├── mcp_server.py                    # MCP protocol server
│   │   ├── unified_ai_context_manager.py    # Context management
│   │   ├── copilot_chatdev_bridge.py        # Multi-AI bridge
│   │   └── ollama_integration.py            # Ollama integration
│   ├── orchestration/        # Task orchestration
│   │   ├── multi_ai_orchestrator.py         # Main orchestrator
│   │   └── comprehensive_workflow_orchestrator.py
│   ├── diagnostics/          # System health & testing
│   │   ├── testing_dashboard.py             # Web dashboard
│   │   ├── system_health_assessor.py
│   │   └── ecosystem_integrator.py
│   └── ai/                   # AI subsystems
│       ├── ai_coordinator.py
│       ├── ollama_hub.py
│       └── chatdev_integration.py
├── tests/                    # Test suites
│   ├── integration/          # Integration tests
│   └── unit/                 # Unit tests
└── scripts/                  # Utility scripts
    ├── comprehensive_modernization.py
    └── todo_to_issue.py
```

### Data Flow

```
User Request
    ↓
Multi-AI Orchestrator
    ↓
┌─────────────┬──────────────┬──────────────┬─────────────┐
│   Copilot   │    Ollama    │   ChatDev    │   Claude    │
└──────┬──────┴──────┬───────┴──────┬───────┴──────┬──────┘
       │             │              │              │
       └─────────────┴──────────────┴──────────────┘
                          ↓
            Unified Context Manager
                          ↓
               Synthesized Response
```

## 📝 Coding Standards

### Python Style
- **Formatter:** Ruff (black-compatible)
- **Linter:** Ruff
- **Type Checker:** MyPy
- **Line Length:** 100 characters
- **Import Order:** isort via ruff

### Code Quality Checklist
- [ ] Type hints on all function signatures
- [ ] Docstrings (Google style) for public functions
- [ ] Tests for new functionality
- [ ] Pre-commit hooks passing
- [ ] No TODO comments without issue numbers

### Example Function
```python
def process_context(
    context_id: str,
    source_system: str,
    metadata: Dict[str, Any] | None = None
) -> ContextEntry:
    """Process and validate context entry.

    Args:
        context_id: Unique context identifier
        source_system: AI system that generated context
        metadata: Optional metadata dictionary

    Returns:
        Processed ContextEntry object

    Raises:
        ValueError: If context_id is invalid
        ContextNotFoundError: If context doesn't exist
    """
    # Implementation
    pass
```

## 🧪 Testing Guidelines

### Test Structure
```
tests/
├── integration/              # Integration tests
│   ├── test_mcp_server.py
│   └── test_unified_ai_context_manager.py
├── unit/                     # Unit tests
│   └── test_utils.py
└── conftest.py              # Shared fixtures
```

### Writing Tests
```python
import pytest
from src.integration.mcp_server import MCPServer

@pytest.fixture
def mcp_server():
    """Fixture for MCP server."""
    return MCPServer(port=8081)  # Use different port for tests

def test_health_check(mcp_server):
    """Test MCP server health endpoint."""
    client = mcp_server.app.test_client()
    response = client.get("/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
```

### Running Tests
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/integration/test_mcp_server.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Only integration tests
pytest tests/integration/ -v

# Fast tests only (exclude slow)
pytest tests/ -v -m "not slow"

# Failed tests only
pytest --lf
```

### Test Markers
```python
@pytest.mark.slow
def test_long_running_operation():
    pass

@pytest.mark.integration
def test_mcp_server_integration():
    pass

@pytest.mark.unit
def test_utility_function():
    pass
```

## 🤖 AI System Integration

### Adding a New AI System

1. **Register in Context Manager**
```python
# In unified_ai_context_manager.py
def _init_system_contexts(self):
    systems = [
        # ... existing systems ...
        AISystemContext(
            system_name="new_ai",
            status="idle",
            capabilities=["capability1", "capability2"],
            last_updated=datetime.now().isoformat()
        )
    ]
```

2. **Add to Orchestrator**
```python
# In multi_ai_orchestrator.py
class AISystemType(Enum):
    # ... existing types ...
    NEW_AI = "new_ai_system"
```

3. **Create Integration Module**
```python
# src/integration/new_ai_integration.py
class NewAIIntegration:
    def __init__(self):
        self.client = NewAIClient()

    def execute_task(self, task: str) -> str:
        # Implementation
        pass
```

### Using Context Manager
```python
from src.integration.unified_ai_context_manager import get_unified_context_manager

context_mgr = get_unified_context_manager()

# Record AI system activity
context_mgr.update_system_status(
    system_name="your_system",
    status="active",
    current_task="Processing request"
)

# Store context
context_id = context_mgr.add_context(
    content="Your content here",
    context_type="code",
    source_system="your_system",
    metadata={"key": "value"},
    tags=["tag1", "tag2"]
)

# Create relationships
context_mgr.create_context_link(
    source_id=problem_id,
    target_id=solution_id,
    relationship_type="solution_for"
)
```

## 🔄 Common Workflows

### Adding a New Feature

1. **Create Feature Branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Implement Feature**
```python
# src/your_module.py
# Add implementation with type hints and docstrings
```

3. **Add Tests**
```python
# tests/test_your_module.py
# Add comprehensive tests
```

4. **Run Quality Checks**
```bash
# Format code
ruff format src/

# Check linting
ruff check src/ --fix

# Run tests
pytest tests/ -v

# Check types
mypy src/your_module.py
```

5. **Commit and Push**
```bash
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name
```

### Debugging

#### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Use Testing Dashboard
```bash
# Start dashboard
python src/diagnostics/testing_dashboard.py

# Access at http://localhost:5001
# Run tests interactively with real-time feedback
```

#### Context Manager Inspection
```python
from src.integration.unified_ai_context_manager import get_unified_context_manager

context_mgr = get_unified_context_manager()

# Get all system statuses
statuses = context_mgr.get_all_system_statuses()
for name, status in statuses.items():
    print(f"{name}: {status.status} - {status.current_task}")

# Get recent contexts
recent = context_mgr.get_contexts_by_type("error", limit=10)
for ctx in recent:
    print(f"{ctx.id}: {ctx.content[:50]}")
```

## 🛠️ Utility Scripts

### Comprehensive Modernization
```bash
# Run all modernization checks
python scripts/comprehensive_modernization.py

# Output:
# - Ruff auto-fixes
# - Import sorting
# - Syntax validation
# - Test execution
# - Detailed report
```

### TODO to GitHub Issues
```bash
# Preview TODOs
python scripts/todo_to_issue.py --dry-run

# Create issues (limited)
python scripts/todo_to_issue.py --limit 10

# Create all issues
python scripts/todo_to_issue.py
```

## 🔍 Troubleshooting

### Import Errors
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=.  # Linux/Mac
set PYTHONPATH=.     # Windows

# Or use absolute imports
from src.integration.mcp_server import MCPServer
```

### Database Locked
```bash
# Reset context database
rm data/unified_ai_context.db

# Or in Python
from pathlib import Path
Path("data/unified_ai_context.db").unlink(missing_ok=True)
```

### Port Already in Use
```python
# Use different port
from src.integration.mcp_server import MCPServer
server = MCPServer(port=9090)  # Instead of default 8080
```

### Test Failures
```bash
# Clear cache
pytest --cache-clear

# Verbose output
pytest -vv --tb=long

# Debug specific test
pytest tests/test_file.py::test_function -vv --pdb
```

### Terminal Output Routing
```bash
# Validate routing artifacts
python scripts/activate_live_terminal_routing.py --validate
```
If output still seems missing, inspect `data/terminal_logs/*.log` and restart
the VS Code watcher tasks.

## 📊 Performance Optimization

### Profiling
```bash
# Profile test execution
pytest tests/ --profile

# Profile specific function
python -m cProfile -o profile.stats your_script.py
python -m pstats profile.stats
```

### Benchmarking
```bash
# Run benchmarks
pytest tests/benchmarks/ --benchmark-only

# Save benchmark results
pytest tests/benchmarks/ --benchmark-save=baseline

# Compare benchmarks
pytest tests/benchmarks/ --benchmark-compare=baseline
```

## 🔐 Security Best Practices

1. **Never commit secrets**
   - Use `.env` for sensitive data
   - Add secrets to `.gitignore`
   - Use environment variables

2. **Input validation**
   - Validate all user inputs
   - Use type hints and Pydantic models
   - Sanitize file paths

3. **Dependency scanning**
   - Run `pip-audit` regularly
   - Keep dependencies updated
   - Review security advisories

## 📚 Additional Resources

- **MCP Protocol:** [docs/Integration/ENHANCED_CAPABILITIES.md](docs/Integration/ENHANCED_CAPABILITIES.md)
- **Context Manager:** `src/integration/unified_ai_context_manager.py`
- **Test Examples:** `tests/integration/`
- **CI/CD:** `.github/workflows/`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Ensure pre-commit hooks pass
5. Submit pull request

## 📞 Getting Help

- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Documentation:** `docs/` directory

---

**Last Updated:** November 26, 2025
**Maintainers:** NuSyQ-Hub Development Team
