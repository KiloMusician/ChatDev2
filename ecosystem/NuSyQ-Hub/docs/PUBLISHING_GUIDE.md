# 📦 Publishing Guide - Phase 2

Complete guide for publishing projects to PyPI, NPM, VSCode Marketplace, and Docker registries using NuSyQ's Publishing Infrastructure.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Quick Start](#quick-start)
3. [Registry-Specific Setup](#registry-specific-setup)
4. [REST API Reference](#rest-api-reference)
5. [CLI Reference](#cli-reference)
6. [Configuration Examples](#configuration-examples)
7. [Troubleshooting](#troubleshooting)

## Architecture Overview

The Publishing Infrastructure consists of four main components:

### 1. **PublishingOrchestrator** (`src/publishing/orchestrator.py`)
Central orchestration engine that:
- Validates publishing configuration
- Routes projects to appropriate registries
- Coordinates multi-step publishing workflows
- Tracks publishing history and status

**Key Classes:**
- `PublishingOrchestrator` - Main orchestration engine
- `PublishConfig` - Publishing configuration dataclass
- `PublishResult` - Publishing outcome tracking
- `RegistryType` enum - Supported registries (PyPI, NPM, VSCode, Docker, GitHub)
- `PublishTarget` enum - Targeting strategies (PyPI-only, multi, hybrid, etc.)

### 2. **Registry Publishers** (`src/publishing/registry_publishers.py`)
Registry-specific publishers with metadata generation:

#### PyPIPublisher
- Generates `setup.py` and `pyproject.toml`
- Builds Python packages
- Uploads to PyPI via `twine`

#### NPMPublisher
- Generates `package.json` and `.npmrc`
- Builds JavaScript/Node packages
- Publishes to NPM registry

#### VSCodePublisher
- Generates extension manifest
- Compiles TypeScript (if needed)
- Packages and publishes to VSCode Marketplace

### 3. **DockerBuilder** (`src/publishing/docker_builder.py`)
Docker image management:
- Generates Dockerfiles for Python and Node.js
- Creates `.dockerignore` files
- Builds and pushes images to registries

**Key Classes:**
- `DockerBuilder` - Image building and pushing
- `DockerConfig` - Docker configuration
- `DockerfileGenerator` - Dockerfile generation

### 4. **REST API & CLI**
User-facing interfaces:
- `src/api/publishing_api.py` - REST endpoints
- `scripts/publish_project.py` - Command-line tool

## Quick Start

### 1. Publish to PyPI (Python Package)

**Via CLI:**
```bash
python scripts/publish_project.py publish my-package 0.1.0 \
  --author "Your Name" \
  --author-email "you@example.com" \
  --registries pypi
```

**Via REST API:**
```bash
curl -X POST http://localhost:8000/api/publishing/publish \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "my-package",
    "project_name": "My Package",
    "version": "0.1.0",
    "author": "Your Name",
    "author_email": "you@example.com",
    "registries": ["pypi"]
  }'
```

### 2. Publish to NPM (JavaScript/Node Package)

**Via CLI:**
```bash
python scripts/publish_project.py publish my-lib 1.0.0 \
  --author "Your Name" \
  --registries npm
```

### 3. Publish Docker Image

**Via CLI:**
```bash
python scripts/publish_project.py publish my-app 1.0.0 \
  --registries docker
```

### 4. Multi-Registry Publishing

**Via CLI:**
```bash
python scripts/publish_project.py publish my-project 0.1.0 \
  --registries pypi,npm,docker \
  --author "Your Name"
```

## Registry-Specific Setup

### PyPI (Python Packages)

#### Prerequisites
1. Create PyPI account: https://pypi.org/account/register/
2. Generate API token:
   - Go to Account Settings → API tokens
   - Create new token with "Entire account" scope
3. Add to environment or config:
   ```bash
   export PYPI_TOKEN="pypi-AgEIcHlwaS5vcmc..."
   ```

#### Configuration
```python
PublishConfig(
    project_id="my-package",
    project_name="My Package",
    version="0.1.0",
    author="Your Name",
    author_email="you@example.com",
    license_type="MIT",
    pypi_token=os.getenv("PYPI_TOKEN"),
    targets=[RegistryType.PYPI],
)
```

#### Project Requirements
- ✅ `setup.py` or `pyproject.toml` (auto-generated if missing)
- ✅ `README.md` or `README.rst`
- ✅ `LICENSE` file
- ✅ Package version matching semantic versioning

#### Generated Files
```
setup.py                    # Installation and metadata
pyproject.toml             # Modern Python packaging
build/                     # Build artifacts
dist/                      # Distribution packages
my_package.egg-info/       # Package metadata
```

### NPM (JavaScript/Node Packages)

#### Prerequisites
1. Create NPM account: https://www.npmjs.com/signup
2. Generate access token:
   - Go to Profile → Access Tokens
   - Create Automation or Granular access token
3. Add to environment or `.npmrc`:
   ```bash
   npm config set //registry.npmjs.org/:_authToken="npm_..."
   ```

#### Configuration
```python
PublishConfig(
    project_id="my-lib",
    project_name="My Library",
    version="1.0.0",
    author="Your Name",
    npm_token=os.getenv("NPM_TOKEN"),
    targets=[RegistryType.NPM],
)
```

#### Project Requirements
- ✅ `package.json` (auto-generated if missing)
- ✅ Build scripts in `package.json` (e.g., `npm run build`)
- ✅ `README.md`
- ✅ Semantic versioning in `package.json`

#### Generated Files
```
.npmrc                     # NPM registry configuration
dist/                      # Build output
package.json              # Updated metadata
```

### VS Code Marketplace (Extensions)

#### Prerequisites
1. Create Microsoft account: https://account.microsoft.com
2. Create Publisher profile: https://marketplace.visualstudio.com/manage
3. Generate Personal Access Token (PAT):
   - Azure DevOps → Organization settings → Personal access tokens
   - Scopes: `vso.marketplace_publish`
4. Add to environment:
   ```bash
   export VSCODE_TOKEN="your-pat-token"
   ```

#### Configuration
```python
PublishConfig(
    project_id="my-extension",
    project_name="My VS Code Extension",
    version="0.1.0",
    author="Your Name",
    vscode_token=os.getenv("VSCODE_TOKEN"),
    targets=[RegistryType.VSCODE],
)
```

#### Project Requirements
- ✅ `package.json` with extension metadata
- ✅ `vsce` package installed: `npm install -g vsce`
- ✅ Extension code in `src/` directory
- ✅ `README.md` with extension description
- ✅ `CHANGELOG.md` (recommended)

#### Generated Files
```
package.json              # Extension manifest
extension.vsix           # Packaged extension
```

### Docker Hub (Container Images)

#### Prerequisites
1. Create Docker Hub account: https://hub.docker.com/signup
2. Generate access token:
   - Account Settings → Security → Access Tokens
3. Add to environment:
   ```bash
   export DOCKER_USERNAME="your-username"
   export DOCKER_TOKEN="your-access-token"
   ```

#### Configuration
```python
PublishConfig(
    project_id="my-app",
    project_name="My Application",
    version="1.0.0",
    docker_username=os.getenv("DOCKER_USERNAME"),
    docker_password=os.getenv("DOCKER_TOKEN"),
    targets=[RegistryType.DOCKER],
)
```

#### Project Requirements
- ✅ `Dockerfile` (auto-generated if missing)
- ✅ Application code
- ✅ `.dockerignore` file
- ✅ Docker installed and running
- ✅ Dockerfile references valid base image

#### Generated Files
```
Dockerfile                # Container definition
.dockerignore            # Files to exclude from build
```

## REST API Reference

### Endpoints

#### POST /api/publishing/publish
Publish a project to specified registries.

**Request:**
```json
{
  "project_id": "my-project",
  "project_name": "My Project",
  "version": "0.1.0",
  "description": "Project description",
  "author": "Author Name",
  "author_email": "author@example.com",
  "license_type": "MIT",
  "registries": ["pypi", "npm"],
  "pypi_token": "pypi-...",
  "npm_token": "npm-...",
  "repository_url": "https://github.com/user/project"
}
```

**Response:**
```json
{
  "status": "success",
  "project_id": "my-project",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "results": {
    "pypi": {
      "status": "success",
      "url": "https://pypi.org/project/my-project"
    },
    "npm": {
      "status": "success",
      "url": "https://www.npmjs.com/package/my-project"
    }
  }
}
```

#### GET /api/publishing/history/{project_id}
Get publishing history for a project.

**Query Parameters:**
- `limit` (int, 1-100, default: 10) - Max results

**Response:**
```json
[
  {
    "timestamp": "2024-01-01T12:00:00.000Z",
    "status": "success",
    "version": "0.1.0",
    "registries": ["pypi"],
    "error": null
  }
]
```

#### GET /api/publishing/status/{project_id}
Get latest publish status for a project.

**Response:**
```json
{
  "project_id": "my-project",
  "project_name": "My Project",
  "latest_version": "0.1.0",
  "latest_status": "success",
  "last_publish_time": "2024-01-01T12:00:00.000Z",
  "registry_status": {
    "pypi": "success",
    "npm": "pending"
  }
}
```

#### GET /api/publishing/registries
List all available registries.

**Response:**
```json
[
  {
    "name": "PyPI",
    "registry_type": "pypi",
    "description": "Python Package Index",
    "website": "https://pypi.org",
    "authentication_required": true
  }
]
```

#### GET /api/publishing/health
Health check for publishing service.

**Response:**
```json
{
  "status": "healthy",
  "service": "publishing",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

## CLI Reference

### Command Structure
```bash
python scripts/publish_project.py <command> [arguments] [options]
```

### Commands

#### publish
Publish a project to registries.

**Usage:**
```bash
python scripts/publish_project.py publish <project_id> <version> [options]
```

**Arguments:**
- `project_id` - Project identifier (required)
- `version` - Semantic version (required)

**Options:**
- `--project-name NAME` - Human-readable name
- `--registries REGS` - Comma-separated registry list (default: pypi)
- `--author NAME` - Author name
- `--author-email EMAIL` - Author email
- `--description TEXT` - Project description
- `--license TYPE` - License type (MIT, Apache-2.0, GPL-3.0)
- `--repository-url URL` - Git repository URL
- `--documentation-url URL` - Documentation website
- `--project-path PATH` - Project directory (default: .)

**Example:**
```bash
python scripts/publish_project.py publish my-package 0.1.0 \
  --author "John Doe" \
  --author-email "john@example.com" \
  --description "My awesome package" \
  --registries pypi,npm \
  --license MIT
```

#### status
Check publish status for a project.

**Usage:**
```bash
python scripts/publish_project.py status <project_id>
```

**Example:**
```bash
python scripts/publish_project.py status my-package
```

#### history
View publish history for a project.

**Usage:**
```bash
python scripts/publish_project.py history <project_id> [--limit N]
```

**Options:**
- `--limit N` - Max history entries (default: 10)

**Example:**
```bash
python scripts/publish_project.py history my-package --limit 20
```

## Configuration Examples

### Example 1: Python Package (PyPI Only)

```python
from src.publishing.orchestrator import PublishingOrchestrator, PublishConfig, RegistryType, PublishTarget

config = PublishConfig(
    project_id="awesome-lib",
    project_name="Awesome Library",
    version="1.0.0",
    description="A Python library for awesome things",
    author="Your Name",
    author_email="you@example.com",
    license_type="MIT",
    targets=[RegistryType.PYPI],
    publish_target=PublishTarget.PYPI_ONLY,
    pypi_token="pypi-AgEIcHlwaS5vcmc...",
)

orchestrator = PublishingOrchestrator()
result = orchestrator.publish(config, project_path="/path/to/project")
```

### Example 2: NPM Package with Docker Image

```python
config = PublishConfig(
    project_id="web-app",
    project_name="Web Application",
    version="2.0.0",
    description="Modern web application",
    author="Your Name",
    license_type="MIT",
    targets=[RegistryType.NPM, RegistryType.DOCKER],
    publish_target=PublishTarget.HYBRID_NODE,
    npm_token="npm_...",
    docker_username="myusername",
    docker_password="my-token",
)

orchestrator = PublishingOrchestrator()
result = orchestrator.publish(config, project_path="/path/to/project")
```

### Example 3: VS Code Extension

```python
config = PublishConfig(
    project_id="my-extension",
    project_name="My VS Code Extension",
    version="0.5.0",
    description="Adds awesome features to VS Code",
    author="Extension Author",
    license_type="MIT",
    targets=[RegistryType.VSCODE],
    publish_target=PublishTarget.VSCODE_ONLY,
    vscode_token="your-pat-token",
)

orchestrator = PublishingOrchestrator()
result = orchestrator.publish(config, project_path="/path/to/extension")
```

## Troubleshooting

### PyPI Issues

**Problem:** "Invalid API token"
- **Solution:** Verify PYPI_TOKEN is correct and has not expired. Regenerate in PyPI settings.

**Problem:** "Package already exists"
- **Solution:** Increment version number in setup.py or pyproject.toml.

**Problem:** "Missing required fields"
- **Solution:** Ensure README.md, LICENSE, and valid setup.py exist.

### NPM Issues

**Problem:** "401 Unauthorized"
- **Solution:** Check NPM token is valid. Run `npm login` and verify `~/.npmrc`.

**Problem:** "Package name already taken"
- **Solution:** Choose a unique package name or publish to a scope: `@yourscope/package`.

### Docker Issues

**Problem:** "Docker daemon not running"
- **Solution:** Start Docker Desktop or Docker daemon on your system.

**Problem:** "Authentication failed"
- **Solution:** Verify Docker credentials via `docker login`.

### VS Code Issues

**Problem:** "PAT token expired"
- **Solution:** Generate new Personal Access Token in Azure DevOps.

**Problem:** "Publisher not found"
- **Solution:** Create publisher profile in VS Code Marketplace first.

## Integration with NuSyQ Systems

### Quest System Integration
Publishing operations are logged to the quest system:
```
src/Rosetta_Quest_System/quest_log.jsonl
```

Each publish creates an entry:
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "quest_type": "publish",
  "status": "completed",
  "details": {
    "project_id": "my-package",
    "registries": ["pypi"],
    "version": "0.1.0"
  }
}
```

### Multi-AI Orchestration
Publishing can be triggered via the multi-AI orchestrator:
```bash
python -m src.orchestration.multi_ai_orchestrator publish my-package 0.1.0
```

## Performance Metrics

- **Single Registry Publish:** ~30-60 seconds (depends on build time)
- **Multi-Registry Publish:** ~2-5 minutes
- **Docker Image Build:** ~1-3 minutes (depends on size)
- **Metadata Generation:** <1 second

## Security Considerations

1. **Credentials**: Store API tokens in:
   - Environment variables (recommended for CI/CD)
   - `config/secrets.json` (local development only)
   - Never commit to version control

2. **Token Rotation**: Rotate API tokens regularly (every 90 days recommended)

3. **Scope Limiting**: Use granular tokens with minimal required scopes

4. **Signed Packages** (Python): Consider signing packages after publishing

## Next Steps

After Phase 2 publishing infrastructure:
- **Phase 3.1:** GraphQL generator for generated projects
- **Phase 3.2:** Database schema helpers
- **Phase 3.3:** Component scaffolding
- **Phase 3.4:** OpenAPI documentation

---

**Phase 2 Status:** ✅ Complete (Phase 2.7 Documentation)
**Phase 2 Deliverables:** ~2,500 LOC + 20+ tests + full documentation
**Coverage:** 35%+ of publishing infrastructure
