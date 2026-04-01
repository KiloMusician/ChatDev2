# Docker Build and Push Script for NuSyQ-Hub
# Supports multi-architecture builds and registry push

param(
    [Parameter(Mandatory=$false)]
    [string]$Registry = "ghcr.io/kilomusician",

    [Parameter(Mandatory=$false)]
    [string]$ImageName = "nusyq-hub",

    [Parameter(Mandatory=$false)]
    [string]$Tag = "latest",

    [Parameter(Mandatory=$false)]
    [ValidateSet("Dockerfile", "Dockerfile.dev", "Dockerfile.prod")]
    [string]$DockerfilePath = "Dockerfile.prod",

    [Parameter(Mandatory=$false)]
    [switch]$Push,

    [Parameter(Mandatory=$false)]
    [switch]$MultiArch,

    [Parameter(Mandatory=$false)]
    [string]$Platform = "linux/amd64"
)

$ErrorActionPreference = "Stop"

Write-Host "🐳 NuSyQ-Hub Docker Build Script" -ForegroundColor Cyan
Write-Host "=" * 60

# Full image name
$FullImageName = "${Registry}/${ImageName}:${Tag}"

Write-Host "📦 Image: $FullImageName" -ForegroundColor Green
Write-Host "🐋 Dockerfile: $DockerfilePath" -ForegroundColor Green
Write-Host "🏗️  Platform: $Platform" -ForegroundColor Green

# Change to repository root
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "`n🔍 Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker version --format '{{.Server.Version}}'
    Write-Host "✅ Docker version: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Build the image
Write-Host "`n🏗️  Building Docker image..." -ForegroundColor Yellow

if ($MultiArch) {
    Write-Host "🌍 Building multi-architecture image (linux/amd64, linux/arm64)..." -ForegroundColor Cyan

    # Create buildx builder if it doesn't exist
    $builderName = "nusyq-builder"
    $existingBuilder = docker buildx ls | Select-String $builderName

    if (-not $existingBuilder) {
        Write-Host "Creating buildx builder: $builderName" -ForegroundColor Yellow
        docker buildx create --name $builderName --use
        docker buildx inspect --bootstrap
    } else {
        docker buildx use $builderName
    }

    # Build for multiple platforms
    $buildCmd = "docker buildx build --platform linux/amd64,linux/arm64 -f $DockerfilePath -t $FullImageName"

    if ($Push) {
        $buildCmd += " --push"
    } else {
        $buildCmd += " --load"
    }

    $buildCmd += " ."

    Write-Host "Running: $buildCmd" -ForegroundColor Gray
    Invoke-Expression $buildCmd

} else {
    # Single architecture build
    Write-Host "Building for platform: $Platform" -ForegroundColor Cyan

    docker build `
        --platform $Platform `
        -f $DockerfilePath `
        -t $FullImageName `
        --progress=plain `
        .

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker build failed!" -ForegroundColor Red
        exit 1
    }

    Write-Host "✅ Build successful!" -ForegroundColor Green
}

# Get image details
Write-Host "`n📊 Image Details:" -ForegroundColor Yellow
docker images $FullImageName

# Security scan (if trivy is installed)
Write-Host "`n🔍 Security scan..." -ForegroundColor Yellow
if (Get-Command trivy -ErrorAction SilentlyContinue) {
    Write-Host "Running Trivy security scan..." -ForegroundColor Cyan
    trivy image --severity HIGH,CRITICAL $FullImageName
} else {
    Write-Host "⚠️  Trivy not installed. Skipping security scan." -ForegroundColor Yellow
    Write-Host "   Install: choco install trivy or https://github.com/aquasecurity/trivy" -ForegroundColor Gray
}

# Test the image
Write-Host "`n🧪 Testing image..." -ForegroundColor Yellow
Write-Host "Running quick test container..." -ForegroundColor Cyan

$testContainer = "nusyq-hub-test-$(Get-Random)"
docker run --rm --name $testContainer -d -p 5001:5000 $FullImageName

Start-Sleep -Seconds 5

try {
    $healthCheck = docker inspect --format='{{.State.Health.Status}}' $testContainer
    Write-Host "Container health: $healthCheck" -ForegroundColor Green

    # Try to hit the health endpoint
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5001/health" -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✅ Health check passed: $($response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Health endpoint not responding (this may be expected)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Container test had issues: $_" -ForegroundColor Yellow
} finally {
    docker stop $testContainer 2>&1 | Out-Null
    Write-Host "Test container stopped" -ForegroundColor Gray
}

# Push to registry
if ($Push) {
    Write-Host "`n🚀 Pushing to registry..." -ForegroundColor Yellow

    # Check if logged in
    Write-Host "Checking registry authentication..." -ForegroundColor Cyan
    docker login $Registry.Split('/')[0]

    if (-not $MultiArch) {
        docker push $FullImageName
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully pushed: $FullImageName" -ForegroundColor Green
    } else {
        Write-Host "❌ Push failed!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n✅ Build complete!" -ForegroundColor Green
Write-Host "`nUsage:" -ForegroundColor Cyan
Write-Host "  docker run -p 5000:5000 $FullImageName" -ForegroundColor White
Write-Host "`nKubernetes:" -ForegroundColor Cyan
Write-Host "  kubectl set image deployment/nusyq-hub nusyq-hub=$FullImageName -n nusyq" -ForegroundColor White
