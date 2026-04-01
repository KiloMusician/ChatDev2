# NuSyQ Kubernetes Setup Script
# Run this script after Docker Desktop is started and Kubernetes is enabled

Write-Host "🚀 NuSyQ Kubernetes Setup" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

# Check if Docker Desktop is running
Write-Host "1. Checking Docker Desktop..." -ForegroundColor Yellow
if (Get-Command docker -ErrorAction SilentlyContinue) {
    try {
        docker version | Out-Null
        Write-Host "   ✅ Docker is available" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️ Docker CLI is available but Docker Desktop may not be running or the daemon is unreachable." -ForegroundColor Yellow
        Write-Host "   Please start Docker Desktop and ensure the daemon is running." -ForegroundColor Yellow
        Write-Host "   Then run this script again." -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "   ❌ Docker CLI not found on PATH" -ForegroundColor Red
    Write-Host "   Install Docker Desktop and ensure 'docker' is on PATH." -ForegroundColor Yellow
    exit 1
}

# Check if Kubernetes is enabled in Docker Desktop
Write-Host "2. Checking Kubernetes..." -ForegroundColor Yellow
if (Get-Command kubectl -ErrorAction SilentlyContinue) {
    try {
        kubectl cluster-info | Out-Null
        Write-Host "   ✅ Kubernetes is available" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Kubernetes appears to be unavailable or not responding." -ForegroundColor Red
        Write-Host "   If you are using Docker Desktop, enable Kubernetes in Settings > Kubernetes and wait for it to start." -ForegroundColor Yellow
        Write-Host "   Then run this script again." -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "   ❌ kubectl CLI not found on PATH" -ForegroundColor Red
    Write-Host "   Install kubectl or enable the Kubernetes client and try again." -ForegroundColor Yellow
    exit 1
}

# Set the current context to docker-desktop
Write-Host "3. Setting up kubectl context..." -ForegroundColor Yellow
kubectl config use-context docker-desktop
Write-Host "   ✅ Context set to docker-desktop" -ForegroundColor Green

# Verify the setup
Write-Host "4. Verifying setup..." -ForegroundColor Yellow
Write-Host "   Current context: $(kubectl config current-context)" -ForegroundColor Cyan
Write-Host "   Cluster info:" -ForegroundColor Cyan
kubectl cluster-info

# Create a test namespace for NuSyQ
Write-Host "5. Creating NuSyQ namespace..." -ForegroundColor Yellow
kubectl create namespace nusyq --dry-run=client -o yaml | kubectl apply -f -
Write-Host "   ✅ NuSyQ namespace ready" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 Kubernetes setup complete!" -ForegroundColor Green
Write-Host "You can now use kubectl and the VS Code Kubernetes extension." -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  kubectl get pods -A          # List all pods"
Write-Host "  kubectl get namespaces       # List namespaces"
Write-Host "  kubectl config get-contexts  # List available contexts"
