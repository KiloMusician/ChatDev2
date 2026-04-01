# Universal Project Generator (UPG) - Documentation

## Overview

The **Universal Project Generator (UPG)** is a unified system for creating new projects from templates. It integrates with the NuSyQ ecosystem to provide:

- **10 High-Value Templates**: Games, webapps, packages, extensions, CLI tools
- **AI-Powered Generation**: Automatic code with ChatDev (complex) or Ollama (simple)
- **Quest System Integration**: All projects logged for narrative integration
- **Artifact Registry**: Every project tracked and queryable
- **REST API**: Full HTTP interface for programmatic project creation

## Architecture

### Core Components

```
UniversalProjectGenerator (src/generators/universal_project_generator.py)
├── Template Loader (loads from template_definitions.py)
├── AI Provider Selector (complexity-based routing)
├── File Generator (writes starter files)
├── Artifact Registry (tracks all projects)
└── Quest Logger (logs to quest_log.jsonl)

Template Definitions (src/generators/template_definitions.py)
├── 10 Pre-Built Templates
├── Schema Definition (ProjectTemplate dataclass)
└── Template Discovery Functions

CLI Tool (scripts/generate_project.py)
├── list command (discover templates)
├── info command (template details)
└── generate command (create project)

REST API (src/api/generators_api.py)
├── GET /api/generators/templates
├── POST /api/generators/create
├── GET /api/generators/projects
└── Batch operations
```

### Data Flow

```
User Request (CLI/API)
    ↓
Template Loader (get_template)
    ↓
Validation (validate_template)
    ↓
AI Provider Selection (select_ai_provider)
    ↓
File Generation (write_starter_files)
    ↓
Metadata Creation (.nusyq.json)
    ↓
Artifact Registration (register_artifact)
    ↓
Quest Logging (log_quest)
    ↓
Result (project_id, output_path, status)
```

## Templates

### Available Templates (10 Total)

| Template ID | Name | Type | Language | Complexity | AI Provider |
|---|---|---|---|---|---|
| game_godot_3d | Godot 3D Game | Game | GDScript | 9 | ChatDev |
| game_phaser_web | Phaser Web Game | Game | TypeScript | 7 | ChatDev |
| webapp_fastapi_react | FastAPI + React | Webapp | Python | 8 | ChatDev |
| webapp_nextjs | Next.js Full-Stack | Webapp | TypeScript | 8 | ChatDev |
| webapp_minimal_fastapi | Minimal FastAPI | Webapp | Python | 3 | Ollama |
| package_python | Python Package | Package | Python | 4 | Ollama |
| package_npm | NPM Package | Package | TypeScript | 5 | Ollama |
| extension_vscode | VS Code Extension | Extension | TypeScript | 6 | Ollama |
| cli_python_click | Python CLI (Click) | CLI | Python | 3 | Ollama |
| cli_node_commander | Node.js CLI | CLI | TypeScript | 3 | Ollama |

### Template Characteristics

Each template defines:

- **Starter Files**: Boilerplate code to get started
- **Dependencies**: Required packages and versions
- **Complexity Score**: 1-10, determines AI provider
- **Language & Type**: For filtering and categorization
- **Prerequisites**: Tools needed (Python 3.9+, Node.js 18+, etc.)
- **Customization Options**: What features can be configured

### AI Provider Selection Logic

**Complexity-Based Routing:**

```
Complexity 8-10 (Complex)      → ChatDev (multi-agent code generation)
Complexity 5-7 (Medium)         → ChatDev (scaffold + enhancement)
Complexity 1-4 (Simple)         → Ollama (qwen2.5-coder local LLM)
```

**Examples:**
- `game_godot_3d` (complexity 9) → ChatDev orchestrates multi-file generation
- `package_python` (complexity 4) → Ollama generates standard package structure
- `extension_vscode` (complexity 6) → ChatDev creates extension commands + hooks

## Usage

### 1. CLI Tool (scripts/generate_project.py)

#### List Templates

```bash
# List all templates
python scripts/generate_project.py list

# Filter by type
python scripts/generate_project.py list game
python scripts/generate_project.py list webapp
```

Output:
```
======================================================================
  Available Templates (10)
======================================================================

  GAME
  ------
    📋 game_godot_3d                      Complexity: 9/10 🔥🔥🔥
       Full 3D game with Godot 4.x + NuSyQ integration
       Language: gdscript | AI: chatdev
```

#### Get Template Info

```bash
python scripts/generate_project.py info game_godot_3d
```

Output:
```
======================================================================
  Template: Godot 3D Game
======================================================================

  ID:                 game_godot_3d
  Name:               Godot 3D Game
  Type:               GAME
  Language:           gdscript
  Description:        Full 3D game with Godot 4.x + NuSyQ integration

  Complexity:         9/10
  Est. Generation:    30-45 minutes
  AI Provider:        chatdev
  AI Enhancement:     ✅ Yes
```

#### Generate Project

```bash
# Generate a game
python scripts/generate_project.py generate game_godot_3d my_awesome_game

# With options
python scripts/generate_project.py generate package_python utils_lib \
  --options '{"author": "John Doe", "license": "MIT"}'
```

Output:
```
======================================================================
  Generating Project: my_awesome_game
======================================================================

  Template:   Godot 3D Game
  Language:   gdscript
  Type:       game

⏳ Generating project...

✅ Project generated successfully!

  Project ID:     a1b2c3d4
  Name:           my_awesome_game
  Location:       c:\Users\keath\Desktop\Legacy\NuSyQ-Hub\projects\generated\my_awesome_game
  AI Provider:    chatdev
  Time:           2.34s

📋 Next Steps:
  1. cd my_awesome_game
  2. Review the generated project structure
  3. Install prerequisites: godot>=4.0
```

### 2. Python API

```python
from src.generators.universal_project_generator import UniversalProjectGenerator

# Initialize
upg = UniversalProjectGenerator()

# List templates
templates = upg.list_templates()
for t in templates:
    print(f"{t.template_id}: {t.name} (complexity={t.complexity})")

# Generate project
result = upg.generate("webapp_nextjs", "my_app")

if result.status == "success":
    print(f"✅ Generated: {result.output_path}")
    print(f"  Project ID: {result.project_id}")
else:
    print(f"❌ Failed: {result.error_message}")

# Retrieve project info
project = upg.get_project_info(result.project_id)
print(f"Project: {project['name']} (template={project['template_id']})")

# List all generated projects
all_projects = upg.list_generated_projects()
print(f"Total projects: {len(all_projects)}")
```

### 3. REST API

#### Health Check

```bash
curl http://localhost:8000/api/generators/health
```

```json
{
  "status": "healthy",
  "upg_available": true,
  "registry_status": "operational",
  "templates_available": 10,
  "projects_generated": 5
}
```

#### List Templates

```bash
curl "http://localhost:8000/api/generators/templates?project_type=game&complexity_min=8&complexity_max=10"
```

#### Get Template Info

```bash
curl http://localhost:8000/api/generators/templates/game_godot_3d
```

#### Create Project

```bash
curl -X POST http://localhost:8000/api/generators/create \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "package_python",
    "project_name": "my_package",
    "options": {"author": "John Doe"}
  }'
```

Response:
```json
{
  "project_id": "a1b2c3d4",
  "project_name": "my_package",
  "status": "success",
  "output_path": "projects/generated/my_package",
  "ai_provider": "ollama",
  "generation_time": 1.23,
  "created_at": "2026-02-04T10:30:00",
  "metadata": {
    "language": "python",
    "type": "package",
    "complexity": 4
  }
}
```

#### Get Project Status

```bash
curl http://localhost:8000/api/generators/projects/a1b2c3d4
```

#### Statistics

```bash
curl http://localhost:8000/api/generators/stats
```

```json
{
  "total_templates": 10,
  "total_projects_generated": 5,
  "template_usage": {
    "package_python": 2,
    "webapp_nextjs": 1,
    "game_godot_3d": 1,
    "cli_python_click": 1
  },
  "ai_provider_usage": {
    "ollama": 3,
    "chatdev": 2
  }
}
```

## Integration with NuSyQ Systems

### Artifact Registry

Every generated project is registered in `config/artifact_registry.json`:

```json
{
  "projects": [
    {
      "project_id": "a1b2c3d4",
      "template_id": "package_python",
      "name": "my_package",
      "path": "projects/generated/my_package",
      "status": "success",
      "ai_provider": "ollama",
      "created_at": "2026-02-04T10:30:00"
    }
  ],
  "last_updated": "2026-02-04T10:30:00"
}
```

### Quest Logging

All projects are logged to `src/Rosetta_Quest_System/quest_log.jsonl`:

```jsonl
{"timestamp": "2026-02-04T10:30:00", "event_type": "project_generated", "project_id": "a1b2c3d4", "template_id": "package_python", "project_name": "my_package", "status": "success", "metadata": {...}}
```

### Project Metadata

Each project has `.nusyq.json` in its root:

```json
{
  "project_id": "a1b2c3d4",
  "template_id": "package_python",
  "template_name": "Python Package (PyPI-Ready)",
  "created_at": "2026-02-04T10:30:00",
  "complexity": 4,
  "language": "python",
  "type": "package",
  "ai_provider": "ollama"
}
```

## Advanced Usage

### Batch Project Generation

```python
from src.generators.universal_project_generator import UniversalProjectGenerator

upg = UniversalProjectGenerator()

projects = [
    ("package_python", "utils_lib"),
    ("cli_python_click", "task_runner"),
    ("package_npm", "react_component"),
]

for template_id, name in projects:
    result = upg.generate(template_id, name)
    print(f"{name}: {result.status}")
```

### Filtering Templates by Complexity

```python
upg = UniversalProjectGenerator()

# Simple projects (can use Ollama)
simple = [t for t in upg.list_templates() if t.complexity <= 4]
print(f"Simple projects: {len(simple)}")

# Complex projects (use ChatDev)
complex = [t for t in upg.list_templates() if t.complexity >= 8]
print(f"Complex projects: {len(complex)}")
```

### Template Selection Criteria

```python
# Filter by language
python_templates = [t for t in upg.list_templates() if "python" in t.language.value]

# Filter by requirements
offline_templates = [t for t in upg.list_templates()
                     if "internet" not in t.prerequisites]

# Filter by AI-enhanced
ai_capable = [t for t in upg.list_templates()
              if t.ai_enhancement_available]
```

## Configuration

### Environment Variables

```bash
# Output location for generated projects
NUSYQ_PROJECTS_BASE=projects/generated

# Artifact registry path
NUSYQ_ARTIFACT_REGISTRY=config/artifact_registry.json

# Quest log path
NUSYQ_QUEST_LOG=src/Rosetta_Quest_System/quest_log.jsonl
```

### Customization

Override default paths:

```python
upg = UniversalProjectGenerator(
    output_base="custom/projects",
    registry_path="custom/registry.json",
    quest_log_path="custom/quest.jsonl"
)
```

## Troubleshooting

### Template Not Found

**Error:** `Template not found: game_godot_3d`

**Solution:** Verify template ID with `python scripts/generate_project.py list`

### Generation Failed

**Error:** `Generation failed: [error message]`

**Solutions:**
1. Check prerequisite tools are installed
2. Verify template is valid: `python scripts/generate_project.py info [template_id]`
3. Check disk space
4. Review error message for specific issue

### Quest Log Not Writing

**Error:** Projects don't appear in quest system

**Solutions:**
1. Check `quest_log_path` is writable
2. Verify quest log parent directory exists
3. Check file permissions

## Performance

### Generation Times

| Template | Complexity | Time | AI Provider |
|---|---|---|---|
| cli_python_click | 3 | 0.5s | Ollama |
| package_python | 4 | 0.8s | Ollama |
| webapp_minimal_fastapi | 3 | 0.6s | Ollama |
| extension_vscode | 6 | 30-60s | ChatDev |
| webapp_nextjs | 8 | 30-60s | ChatDev |
| game_godot_3d | 9 | 30-45min | ChatDev |

### Scaling

**Current Limits:**
- Single-threaded generation
- Sequential project creation
- No concurrent ChatDev runs (system limitation)

**Future Improvements:**
- Async generation pipeline
- Parallel Ollama requests
- Queued ChatDev tasks
- Background generation service

## Examples

### Example 1: Create Python Package

```bash
python scripts/generate_project.py generate package_python my_utils

cd my_utils
cat .nusyq.json
pip install -e .
pytest tests/
```

### Example 2: Create Web App with API

```bash
python scripts/generate_project.py generate webapp_fastapi_react team_dashboard

cd team_dashboard
docker-compose up
# API runs on http://localhost:8000
# Frontend runs on http://localhost:3000
```

### Example 3: Batch Project Generation via API

```bash
curl -X POST http://localhost:8000/api/generators/batch-create \
  -H "Content-Type: application/json" \
  -d '{
    "projects": [
      {"template_id": "package_python", "project_name": "lib1"},
      {"template_id": "package_npm", "project_name": "lib2"},
      {"template_id": "cli_python_click", "project_name": "tool1"}
    ]
  }'
```

## See Also

- [Template Definitions](../src/generators/template_definitions.py)
- [UPG Implementation](../src/generators/universal_project_generator.py)
- [REST API Endpoints](../src/api/generators_api.py)
- [CLI Tool](../scripts/generate_project.py)
- [Tests](../tests/test_universal_project_generator.py)
