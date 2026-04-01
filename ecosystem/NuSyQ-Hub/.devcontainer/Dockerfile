## NuSyQ Tripartite Ecosystem Dev Container
## Supports NuSyQ-Hub, NuSyQ, and SimulatedVerse repositories
FROM mcr.microsoft.com/devcontainers/python:3.13

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies, Node.js, and development tools
RUN apt-get update && apt-get -y install --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    git \
    gnupg \
    lsb-release \
    unzip \
    wget \
    vim \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get update && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip setuptools wheel \
    && npm install -g @vscode/devcontainer-cli vsce npm@latest || true

# Create workspace structure for all three repositories
RUN mkdir -p /workspaces/NuSyQ-Hub \
             /workspaces/NuSyQ \
             /workspaces/SimulatedVerse

# Set working directory to Hub (main repository)
WORKDIR /workspaces/NuSyQ-Hub

# Set ecosystem environment variables (also set in devcontainer.json for VS Code)
ENV NUSYQ_HUB_ROOT=/workspaces/NuSyQ-Hub \
    NUSYQ_ROOT=/workspaces/NuSyQ \
    SIMULATEDVERSE_ROOT=/workspaces/SimulatedVerse \
    ECOSYSTEM_ROOT=/workspaces/NuSyQ-Hub \
    IN_DEVCONTAINER=true

CMD ["/bin/bash"]
