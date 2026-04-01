#!/usr/bin/env bash
set -e

echo "🚀 Setting up NuSyQ Tripartite Ecosystem..."
echo ""

# Function to print section headers
print_section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Verify workspace structure
print_section "📁 Verifying Workspace Structure"
for repo in "NuSyQ-Hub" "NuSyQ" "SimulatedVerse"; do
    if [ -d "/workspaces/$repo" ]; then
        echo "✅ /workspaces/$repo exists"
    else
        echo "⚠️  /workspaces/$repo not found (may not be mounted)"
    fi
done

# Install Python dependencies (NuSyQ-Hub)
print_section "🐍 Installing Python Dependencies (NuSyQ-Hub)"

# Standard requirements
if [ -f /workspaces/NuSyQ-Hub/requirements.txt ]; then
    echo "Installing from requirements.txt..."
    pip install -r /workspaces/NuSyQ-Hub/requirements.txt || echo "⚠️  Some packages failed"
fi

# Dev requirements
if [ -f /workspaces/NuSyQ-Hub/dev-requirements.txt ]; then
    echo "Installing from dev-requirements.txt..."
    pip install -r /workspaces/NuSyQ-Hub/dev-requirements.txt || echo "⚠️  Some dev packages failed"
fi

# Tracing requirements
if [ -f /workspaces/NuSyQ-Hub/requirements-tracing.txt ]; then
    echo "Installing from requirements-tracing.txt..."
    pip install -r /workspaces/NuSyQ-Hub/requirements-tracing.txt || echo "⚠️  Some tracing packages failed"
fi

echo "✅ NuSyQ-Hub Python dependencies installed"

# Install Python dependencies (NuSyQ repo if available)
print_section "🐍 Installing Python Dependencies (NuSyQ)"
if [ -f /workspaces/NuSyQ/requirements.txt ]; then
    echo "Installing from requirements.txt..."
    pip install -r /workspaces/NuSyQ/requirements.txt || echo "⚠️  Some packages failed"
    echo "✅ NuSyQ Python dependencies installed"
else
    echo "ℹ️  NuSyQ repository not mounted or no requirements.txt"
fi

# Install npm dependencies (SimulatedVerse if available)
print_section "📦 Installing npm Dependencies (SimulatedVerse)"
if [ -f /workspaces/SimulatedVerse/package.json ]; then
    echo "Installing from package.json..."
    cd /workspaces/SimulatedVerse
    npm install || echo "⚠️  npm install failed"
    cd /workspaces/NuSyQ-Hub
    echo "✅ SimulatedVerse npm dependencies installed"
else
    echo "ℹ️  SimulatedVerse repository not mounted or no package.json"
fi

# VS Code extension setup (if present)
print_section "🔧 VS Code Extension Setup"
if [ -d "/workspaces/NuSyQ-Hub/vscode-extension" ]; then
    cd /workspaces/NuSyQ-Hub/vscode-extension
    if [ -f package.json ]; then
        echo "Installing extension dependencies..."
        npm ci || npm install || true
        echo "✅ VS Code extension dependencies installed"
        echo "ℹ️  Press F5 in VS Code to start extension host"
    fi
    cd /workspaces/NuSyQ-Hub
else
    echo "ℹ️  No vscode-extension directory found"
fi

# Environment file setup
if [ -f ".devcontainer/.env.example" ] && [ ! -f ".devcontainer/.env" ]; then
    echo "Creating .devcontainer/.env from example..."
    cp .devcontainer/.env.example .devcontainer/.env
    echo "ℹ️  Update .devcontainer/.env with secrets if needed"
fi

# Validate ecosystem health
print_section "🏥 Running Ecosystem Health Check"
if [ -f /workspaces/NuSyQ-Hub/scripts/ecosystem_entrypoint.py ]; then
    python /workspaces/NuSyQ-Hub/scripts/ecosystem_entrypoint.py doctor || echo "⚠️  Health check completed with warnings"
else
    echo "⚠️  ecosystem_entrypoint.py not found"
fi

# Display completion message
print_section "✅ Setup Complete"
echo ""
echo "🎉 NuSyQ Tripartite Ecosystem is ready!"
echo ""
echo "📋 Quick Commands:"
echo "   python scripts/ecosystem_entrypoint.py doctor    - Health check"
echo "   python scripts/ecosystem_entrypoint.py activate  - Start all services"
echo "   python scripts/ecosystem_entrypoint.py status    - Service status"
echo ""
echo "📁 Workspace Structure:"
echo "   /workspaces/NuSyQ-Hub       - Main hub (current directory)"
echo "   /workspaces/NuSyQ           - MCP server & orchestrator"
echo "   /workspaces/SimulatedVerse  - Frontend visualization"
echo ""
echo "🌍 Environment Variables:"
echo "   NUSYQ_HUB_ROOT=$NUSYQ_HUB_ROOT"
echo "   NUSYQ_ROOT=$NUSYQ_ROOT"
echo "   SIMULATEDVERSE_ROOT=$SIMULATEDVERSE_ROOT"
echo ""
echo "💡 Note: Ollama should be installed on host (port 11434)"
echo "   Install: https://ollama.com/docs/installation"
echo ""

exit 0
