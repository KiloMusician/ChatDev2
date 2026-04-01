# Diagnostic script: collect Docker and Kubernetes status for local troubleshooting
# Writes a timestamped report to ./Reports/docker_k8s_status_<timestamp>.log

param(
    [string]$OutDir = "Reports"
)

$ts = (Get-Date).ToString('yyyyMMdd_HHmmss')
$reportFile = Join-Path -Path $PSScriptRoot -ChildPath (Join-Path $OutDir "docker_k8s_status_$ts.log")

if (-not (Test-Path (Join-Path $PSScriptRoot $OutDir))) {
    New-Item -ItemType Directory -Path (Join-Path $PSScriptRoot $OutDir) -Force | Out-Null
}

function Run-Cmd {
    param($Name, $Cmd)
    Add-Content -Path $reportFile -Value "=== $Name ==="
    try {
        $out = & $Cmd 2>&1
        if ($null -eq $out) { $out = "(no output)" }
        Add-Content -Path $reportFile -Value $out
    } catch {
        Add-Content -Path $reportFile -Value "ERROR: $_"
    }
    Add-Content -Path $reportFile -Value "`n"
}

Add-Content -Path $reportFile -Value "Docker & Kubernetes diagnostic report: $ts`n"

# Docker checks
Run-Cmd -Name 'Docker --version' -Cmd { docker --version }
Run-Cmd -Name 'Docker info' -Cmd { docker info }
Run-Cmd -Name 'Docker ps -a' -Cmd { docker ps -a }
Run-Cmd -Name 'Docker images' -Cmd { docker images }

# kubectl checks
Run-Cmd -Name 'kubectl version --client' -Cmd { kubectl version --client }
Run-Cmd -Name 'kubectl config current-context' -Cmd { kubectl config current-context }
Run-Cmd -Name 'kubectl cluster-info' -Cmd { kubectl cluster-info }
Run-Cmd -Name 'kubectl get nodes --no-headers' -Cmd { kubectl get nodes --no-headers }
Run-Cmd -Name 'kubectl get pods -A --no-headers' -Cmd { kubectl get pods -A --no-headers }

Write-Host "Wrote diagnostic report to: $reportFile"
