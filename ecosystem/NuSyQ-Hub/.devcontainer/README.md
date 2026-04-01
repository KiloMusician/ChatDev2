# NuSyQ Dev Container

This folder contains the development container configuration for the NuSyQ-Hub workspace.

What it installs:
- Python 3.13 base image via Microsoft devcontainers
- Node.js 18 LTS and `vsce` for extension management
- Installs `dev-requirements.txt` packages and optional `requirements-tracing.txt` in the post-create step

Key features & recommendations:
- Exposes ports for Ollama (11434) and common dev ports (3000, 5000)
- Installs recommended VS Code extensions defined in `.devcontainer/devcontainer.json` automatically
- Provides `post-create.sh` to install dependencies and prepare the local VS Code extension (for Ollama integration)

Using the devcontainer:
1. Open the `NuSyQ-Hub` workspace in VS Code and click 'Reopen in Container' when prompted.
2. After the container initializes, run: `bash .devcontainer/post-create.sh` (this is automatically executed via devcontainer postCreateCommand).
3. Ensure `CHATDEV_PATH` and `OLLAMA_BASE_URL` are set in your environment or .devcontainer/.env to enable ChatDev/Ollama integration in the workspace.

Notes
- This container does not install Ollama for you; Ollama requires host-level install and runs as a local service. The container forwards port 11434 so you can connect to a host-installed Ollama.
- If you want Ollama to run inside the container as well, you can add a custom script in `.devcontainer/` and modify the Dockerfile to download and install Ollama. It is recommended to keep Ollama on the host to use local GPU or resources.
