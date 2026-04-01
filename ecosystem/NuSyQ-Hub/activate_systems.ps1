# 🔌 NuSyQ Ecosystem Activation Script
# Generated: 2025-11-05T23:15:59.594930

Write-Host '🔌 Activating NuSyQ Ecosystem Systems...' -ForegroundColor Cyan

# MCP Server
Write-Host '🔗 Starting MCP Server...' -ForegroundColor Yellow
$NusyqRoot = $env:NUSYQ_ROOT_PATH
if (-not $NusyqRoot) {
    $NusyqRoot = Join-Path $env:USERPROFILE "NuSyQ"
}
$MCPServerPath = Join-Path $NusyqRoot "mcp_server\main.py"
if (Test-Path $MCPServerPath) {
    Start-Process 'python' -ArgumentList $MCPServerPath -WindowStyle Hidden
} else {
    Write-Host "⚠️ MCP Server not found at $MCPServerPath" -ForegroundColor Yellow
    Write-Host "   → Set NUSYQ_ROOT_PATH or install NuSyQ root repo" -ForegroundColor DarkGray
}

Write-Host '✅ Activation Complete!' -ForegroundColor Green
Write-Host 'Run: python health.py --resume' -ForegroundColor Cyan
