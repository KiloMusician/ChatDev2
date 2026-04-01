# Build all tripartite images from local workspace (PowerShell)
Set-StrictMode -Version Latest
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Building NuSyQ root..."
cd "$root/.."
docker build -t nusyq-root:local ./NuSyQ

Write-Host "Building SimulatedVerse..."
cd "$root/..\Desktop\SimulatedVerse\SimulatedVerse"
docker build -t simverse:local .

Write-Host "Building ChatDev..."
cd "$root/..\NuSyQ\ChatDev"
docker build -t chatdev:local .

Write-Host "All builds finished."
