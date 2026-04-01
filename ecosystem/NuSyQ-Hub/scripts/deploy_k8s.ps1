# NuSyQ-Hub Kubernetes Deployment Script
# Deploys the full stack to a Kubernetes cluster

param(
    [Parameter(Mandatory=$false)]
    [string]$Namespace = "nusyq",

    [Parameter(Mandatory=$false)]
    [string]$ImageTag = "latest",

    [Parameter(Mandatory=$false)]
    [string]$Registry = "ghcr.io/kilomusician",

    [Parameter(Mandatory=$false)]
    [switch]$SkipSecrets,

    [Parameter(Mandatory=$false)]
    [switch]$SkipOllama,

    [Parameter(Mandatory=$false)]
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "☸️  NuSyQ-Hub Kubernetes Deployment" -ForegroundColor Cyan
Write-Host "=" * 60

# Check kubectl
Write-Host "`n🔍 Checking kubectl..." -ForegroundColor Yellow
try {
    $kubectlVersion = kubectl version --client --short
    Write-Host "✅ kubectl: $kubectlVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ kubectl not found. Please install kubectl." -ForegroundColor Red
    exit 1
}

# Check cluster connection
Write-Host "`n🔍 Checking cluster connection..." -ForegroundColor Yellow
try {
    $clusterInfo = kubectl cluster-info
    Write-Host "✅ Connected to cluster" -ForegroundColor Green
} catch {
    Write-Host "❌ Not connected to a Kubernetes cluster!" -ForegroundColor Red
    exit 1
}

$DeployDir = Join-Path $PSScriptRoot "..\deploy\k8s"

# Deploy namespace
Write-Host "`n📦 Creating namespace: $Namespace" -ForegroundColor Yellow
if ($DryRun) {
    kubectl apply -f "$DeployDir\namespace.yaml" --dry-run=client
} else {
    kubectl apply -f "$DeployDir\namespace.yaml"
}

# Deploy ConfigMap
Write-Host "`n⚙️  Deploying ConfigMap..." -ForegroundColor Yellow
if ($DryRun) {
    kubectl apply -f "$DeployDir\configmap.yaml" --dry-run=client
} else {
    kubectl apply -f "$DeployDir\configmap.yaml"
}

# Handle secrets
if (-not $SkipSecrets) {
    Write-Host "`n🔐 Checking secrets..." -ForegroundColor Yellow

    $secretExists = kubectl get secret nusyq-hub-secrets -n $Namespace 2>&1 | Select-String "nusyq-hub-secrets"

    if ($secretExists) {
        Write-Host "⚠️  Secret 'nusyq-hub-secrets' already exists. Skipping." -ForegroundColor Yellow
        Write-Host "   To update secrets, delete and recreate manually." -ForegroundColor Gray
    } else {
        Write-Host "Creating secrets..." -ForegroundColor Cyan

        # Generate secure random passwords
        $postgresPassword = -join ((48..57 + 65..90 + 97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
        $secretKey = -join ((48..57 + 65..90 + 97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})

        if ($DryRun) {
            Write-Host "Would create secret with generated credentials" -ForegroundColor Gray
        } else {
            kubectl create secret generic nusyq-hub-secrets `
                --from-literal=POSTGRES_USER=nusyq `
                --from-literal=POSTGRES_PASSWORD=$postgresPassword `
                --from-literal=SECRET_KEY=$secretKey `
                --from-literal=JWT_SECRET=$secretKey `
                --from-literal=DATABASE_URL="postgresql://nusyq:${postgresPassword}@postgres-service:5432/nusyq" `
                --namespace=$Namespace

            Write-Host "✅ Secrets created" -ForegroundColor Green
        }
    }
} else {
    Write-Host "⚠️  Skipping secrets (--SkipSecrets flag)" -ForegroundColor Yellow
}

# Deploy infrastructure
Write-Host "`n🏗️  Deploying infrastructure..." -ForegroundColor Yellow

Write-Host "  📊 PostgreSQL..." -ForegroundColor Cyan
if ($DryRun) {
    kubectl apply -f "$DeployDir\postgres.yaml" --dry-run=client
} else {
    kubectl apply -f "$DeployDir\postgres.yaml"
}

Write-Host "  ⚡ Redis..." -ForegroundColor Cyan
if ($DryRun) {
    kubectl apply -f "$DeployDir\redis.yaml" --dry-run=client
} else {
    kubectl apply -f "$DeployDir\redis.yaml"
}

if (-not $SkipOllama) {
    Write-Host "  🤖 Ollama..." -ForegroundColor Cyan
    if ($DryRun) {
        kubectl apply -f "$DeployDir\ollama.yaml" --dry-run=client
    } else {
        kubectl apply -f "$DeployDir\ollama.yaml"
    }
}

# Wait for infrastructure
if (-not $DryRun) {
    Write-Host "`n⏳ Waiting for infrastructure to be ready..." -ForegroundColor Yellow

    Write-Host "  Waiting for PostgreSQL..." -ForegroundColor Gray
    kubectl wait --for=condition=ready pod -l app=postgres -n $Namespace --timeout=120s

    Write-Host "  Waiting for Redis..." -ForegroundColor Gray
    kubectl wait --for=condition=ready pod -l app=redis -n $Namespace --timeout=120s

    Write-Host "✅ Infrastructure ready" -ForegroundColor Green
}

# Update image in deployment manifest
$deploymentFile = "$DeployDir\deployment.yaml"
$FullImageName = "${Registry}/nusyq-hub:${ImageTag}"

Write-Host "`n🖼️  Using image: $FullImageName" -ForegroundColor Cyan

# Deploy application
Write-Host "`n🚀 Deploying application..." -ForegroundColor Yellow

if ($DryRun) {
    kubectl apply -f "$DeployDir\deployment.yaml" --dry-run=client
    kubectl apply -f "$DeployDir\service.yaml" --dry-run=client
    kubectl apply -f "$DeployDir\hpa.yaml" --dry-run=client
} else {
    kubectl apply -f "$DeployDir\deployment.yaml"
    kubectl apply -f "$DeployDir\service.yaml"
    kubectl apply -f "$DeployDir\hpa.yaml"

    Write-Host "`n⏳ Waiting for deployment..." -ForegroundColor Yellow
    kubectl rollout status deployment/nusyq-hub -n $Namespace --timeout=300s
}

# Display status
Write-Host "`n📊 Deployment Status:" -ForegroundColor Cyan
kubectl get all -n $Namespace

Write-Host "`n✅ Deployment complete!" -ForegroundColor Green

Write-Host "`n📝 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Check pod logs:" -ForegroundColor White
Write-Host "     kubectl logs -f deployment/nusyq-hub -n $Namespace" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Port forward for local access:" -ForegroundColor White
Write-Host "     kubectl port-forward service/nusyq-hub-service 5000:5000 -n $Namespace" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Access at: http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "  4. Deploy ingress (optional):" -ForegroundColor White
Write-Host "     kubectl apply -f $DeployDir\ingress.yaml" -ForegroundColor Gray
