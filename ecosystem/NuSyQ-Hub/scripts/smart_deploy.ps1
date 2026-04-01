#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Intelligent, automated NuSyQ-Hub Kubernetes deployment with Docker build workaround
.DESCRIPTION
    Sophisticated deployment script that:
    - Creates clean build context avoiding problematic files
    - Builds Docker image with multi-stage optimization
    - Generates secure secrets automatically
    - Deploys complete stack to Kubernetes
    - Validates health and provides diagnostics
#>

param(
    [string]$Namespace = "nusyq",
    [string]$ImageTag = "latest",
    [switch]$SkipBuild,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Color output functions
function Write-Step { param($msg) Write-Host "🔷 $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }

# Configuration
$repoRoot = Split-Path $PSScriptRoot -Parent
$buildContext = Join-Path $repoRoot ".docker_build_context"
$imageName = "nusyq-hub"
$imageFullName = "${imageName}:${ImageTag}"

Write-Host "`n🚀 NuSyQ-Hub Intelligent Deployment System`n" -ForegroundColor Magenta

# Step 1: Pre-flight checks
Write-Step "Running pre-flight checks..."

# Check Docker
try {
    $dockerVersion = docker version --format '{{.Server.Version}}' 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Docker not running" }
    Write-Success "Docker running (v$dockerVersion)"
} catch {
    Write-Error "Docker Desktop is not running. Please start it and retry."
    exit 1
}

# Check Kubernetes
try {
    # Ensure kubectl is in PATH (Docker Desktop location)
    $kubectlPath = Get-Command kubectl -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
    if (-not $kubectlPath) {
        $dockerKubectl = "C:\Program Files\Docker\Docker\resources\bin\kubectl.exe"
        if (Test-Path $dockerKubectl) {
            $env:PATH = "$env:PATH;C:\Program Files\Docker\Docker\resources\bin"
        } else {
            throw "kubectl not found"
        }
    }

    $k8sVersion = kubectl version --client 2>&1 | Select-String "Client Version" | Select-Object -First 1
    Write-Success "kubectl available"
} catch {
    Write-Error "kubectl not found. Please install Kubernetes CLI."
    exit 1
}

# Check cluster connectivity
try {
    kubectl cluster-info --request-timeout=5s | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Cluster not accessible" }
    Write-Success "Kubernetes cluster accessible"
} catch {
    Write-Error "Cannot connect to Kubernetes cluster."
    exit 1
}

# Step 2: Build Docker image with clean context
if (-not $SkipBuild) {
    Write-Step "Creating clean build context..."

    # Remove old build context
    if (Test-Path $buildContext) {
        Remove-Item $buildContext -Recurse -Force
    }
    New-Item -ItemType Directory -Path $buildContext -Force | Out-Null

    # Copy only necessary files (avoiding config/.secure and other problematic paths)
    $filesToCopy = @(
        @{Source="src"; Dest="src"; Type="Directory"},
        @{Source="requirements.txt"; Dest="requirements.txt"; Type="File"},
        @{Source="Dockerfile"; Dest="Dockerfile"; Type="File"},
        @{Source=".dockerignore"; Dest=".dockerignore"; Type="File"}
    )

    foreach ($item in $filesToCopy) {
        $sourcePath = Join-Path $repoRoot $item.Source
        $destPath = Join-Path $buildContext $item.Dest

        if (Test-Path $sourcePath) {
            if ($item.Type -eq "Directory") {
                Copy-Item $sourcePath $destPath -Recurse -Force -ErrorAction SilentlyContinue
                Write-Host "  📁 Copied $($item.Source)/" -ForegroundColor Gray
            } else {
                Copy-Item $sourcePath $destPath -Force
                Write-Host "  📄 Copied $($item.Source)" -ForegroundColor Gray
            }
        } else {
            Write-Warning "Skipped missing: $($item.Source)"
        }
    }

    Write-Success "Clean build context created"

    Write-Step "Building Docker image: $imageFullName"

    try {
        Push-Location $buildContext

        $buildArgs = @(
            "build",
            "-t", $imageFullName,
            "-f", "Dockerfile",
            "--build-arg", "INSTALL_ALEMBIC=yes",
            "."
        )

        if ($Verbose) {
            $buildArgs += "--progress=plain"
        }

        & docker $buildArgs

        if ($LASTEXITCODE -ne 0) {
            throw "Docker build failed with exit code $LASTEXITCODE"
        }

        Pop-Location
        Write-Success "Docker image built successfully"

        # Cleanup build context
        Remove-Item $buildContext -Recurse -Force

    } catch {
        Pop-Location
        Write-Error "Docker build failed: $_"
        exit 1
    }
} else {
    Write-Warning "Skipping Docker build (--SkipBuild specified)"

    # Verify image exists
    $imageExists = docker images --format "{{.Repository}}:{{.Tag}}" | Select-String "^${imageFullName}$"
    if (-not $imageExists) {
        Write-Error "Image $imageFullName not found. Build it first or remove --SkipBuild flag."
        exit 1
    }
}

# Step 3: Create namespace
Write-Step "Creating Kubernetes namespace: $Namespace"

$namespaceExists = kubectl get namespace $Namespace 2>&1 | Select-String "^$Namespace"
if (-not $namespaceExists) {
    kubectl apply -f "$repoRoot/deploy/k8s/namespace.yaml"
    Write-Success "Namespace created"
} else {
    Write-Success "Namespace already exists"
}

# Step 4: Generate and apply secrets
Write-Step "Generating secure secrets..."

# Generate secure random passwords
function New-SecurePassword {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    return [Convert]::ToBase64String($bytes).Substring(0, 32)
}

$postgresPassword = New-SecurePassword
$redisPassword = New-SecurePassword

# Check if secrets already exist
$secretExists = kubectl get secret nusyq-hub-secrets -n $Namespace 2>&1 | Select-String "nusyq-hub-secrets"

if (-not $secretExists) {
    # Create secrets from literals
    kubectl create secret generic nusyq-hub-secrets `
        --from-literal=POSTGRES_PASSWORD=$postgresPassword `
        --from-literal=REDIS_PASSWORD=$redisPassword `
        --from-literal=OPENAI_API_KEY="" `
        --from-literal=ANTHROPIC_API_KEY="" `
        --from-literal=GOOGLE_API_KEY="" `
        --from-literal=GITHUB_TOKEN="" `
        --namespace=$Namespace

    Write-Success "Secrets created"
    Write-Host "  🔐 Postgres Password: $postgresPassword" -ForegroundColor DarkGray
    Write-Host "  🔐 Redis Password: $redisPassword" -ForegroundColor DarkGray
} else {
    Write-Success "Secrets already exist"
}

# Step 5: Apply ConfigMap
Write-Step "Applying ConfigMap..."
kubectl apply -f "$repoRoot/deploy/k8s/configmap.yaml" -n $Namespace
Write-Success "ConfigMap applied"

# Step 6: Deploy infrastructure (Postgres, Redis, Ollama)
Write-Step "Deploying infrastructure services..."

kubectl apply -f "$repoRoot/deploy/k8s/postgres.yaml" -n $Namespace
Write-Host "  🐘 PostgreSQL StatefulSet deployed" -ForegroundColor Gray

kubectl apply -f "$repoRoot/deploy/k8s/redis.yaml" -n $Namespace
Write-Host "  ⚡ Redis Deployment deployed" -ForegroundColor Gray

kubectl apply -f "$repoRoot/deploy/k8s/ollama.yaml" -n $Namespace
Write-Host "  🤖 Ollama Service deployed" -ForegroundColor Gray

Write-Success "Infrastructure services deployed"

# Wait for databases to be ready
Write-Step "Waiting for databases to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n $Namespace --timeout=120s 2>&1 | Out-Null
kubectl wait --for=condition=ready pod -l app=redis -n $Namespace --timeout=60s 2>&1 | Out-Null
Write-Success "Databases are ready"

# Step 7: Deploy main application
Write-Step "Deploying NuSyQ-Hub application..."

# Update deployment image if needed
$deploymentPath = "$repoRoot/deploy/k8s/deployment.yaml"
$deploymentContent = Get-Content $deploymentPath -Raw
if ($deploymentContent -notmatch "image:\s+$imageFullName") {
    $deploymentContent = $deploymentContent -replace 'image:\s+nusyq-hub:[^\s]+', "image: $imageFullName"
    Set-Content $deploymentPath $deploymentContent
    Write-Host "  🔧 Updated deployment image to $imageFullName" -ForegroundColor Gray
}

kubectl apply -f $deploymentPath -n $Namespace
Write-Success "Application deployed"

# Step 8: Apply Service and HPA
Write-Step "Configuring services and autoscaling..."

kubectl apply -f "$repoRoot/deploy/k8s/service.yaml" -n $Namespace
Write-Host "  🌐 Service exposed" -ForegroundColor Gray

kubectl apply -f "$repoRoot/deploy/k8s/hpa.yaml" -n $Namespace
Write-Host "  📊 Horizontal Pod Autoscaler configured" -ForegroundColor Gray

Write-Success "Services configured"

# Step 9: Wait for deployment rollout
Write-Step "Waiting for deployment rollout..."
kubectl rollout status deployment/nusyq-hub -n $Namespace --timeout=300s

Write-Success "Deployment rolled out successfully"

# Step 10: Validation and diagnostics
Write-Step "Running post-deployment validation..."

Write-Host "`n📋 Deployment Status:" -ForegroundColor Yellow
kubectl get all -n $Namespace

Write-Host "`n📊 Pod Details:" -ForegroundColor Yellow
kubectl get pods -n $Namespace -o wide

Write-Host "`n🔍 Recent Events:" -ForegroundColor Yellow
kubectl get events -n $Namespace --sort-by='.lastTimestamp' | Select-Object -Last 10

# Check pod health
$unhealthyPods = kubectl get pods -n $Namespace -o json | ConvertFrom-Json |
    Select-Object -ExpandProperty items |
    Where-Object { $_.status.phase -ne "Running" }

if ($unhealthyPods) {
    Write-Warning "Some pods are not healthy. Check logs with: kubectl logs -n $Namespace <pod-name>"
} else {
    Write-Success "All pods are healthy!"
}

# Get service endpoint
$servicePort = kubectl get svc nusyq-hub -n $Namespace -o jsonpath='{.spec.ports[0].nodePort}' 2>&1
if ($servicePort -and $servicePort -match '^\d+$') {
    Write-Host "`n🌐 Access NuSyQ-Hub at: http://localhost:$servicePort" -ForegroundColor Green
} else {
    $clusterIP = kubectl get svc nusyq-hub -n $Namespace -o jsonpath='{.spec.clusterIP}' 2>&1
    Write-Host "`n🌐 Access NuSyQ-Hub at: http://${clusterIP}:5000 (cluster internal)" -ForegroundColor Green
    Write-Host "   Use port-forward: kubectl port-forward -n $Namespace svc/nusyq-hub 5000:5000" -ForegroundColor Gray
}

Write-Host "`n✨ Deployment Complete! ✨`n" -ForegroundColor Magenta

# Helpful commands
Write-Host "📚 Useful Commands:" -ForegroundColor Yellow
Write-Host "  View logs:        kubectl logs -f -n $Namespace deployment/nusyq-hub" -ForegroundColor Gray
Write-Host "  Scale replicas:   kubectl scale deployment/nusyq-hub -n $Namespace --replicas=3" -ForegroundColor Gray
Write-Host "  Port forward:     kubectl port-forward -n $Namespace svc/nusyq-hub 5000:5000" -ForegroundColor Gray
Write-Host "  Delete all:       kubectl delete namespace $Namespace" -ForegroundColor Gray
Write-Host ""
