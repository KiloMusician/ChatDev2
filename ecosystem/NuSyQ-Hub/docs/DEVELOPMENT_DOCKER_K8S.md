# Docker & Kubernetes Local Diagnostic

This repository includes a small PowerShell diagnostic script to collect local
Docker and Kubernetes status and save a report for troubleshooting.

Why: When working with Docker Desktop + Kubernetes (docker-desktop), it's useful
to have a single report capturing `docker` and `kubectl` output.

How to use (Windows / PowerShell):

1. Open PowerShell (pwsh) and change to the repo root:

```powershell
cd C:\Users\keath\Desktop\Legacy\NuSyQ-Hub
pwsh -NoProfile -File .\scripts\check_docker_k8s.ps1
```

2. The script writes a timestamped file under
   `./Reports/docker_k8s_status_<ts>.log`.

3. Inspect that file and attach it to issues or share with maintainers for
   diagnosis.

Notes:

- The script is low-risk and read-only: it runs `docker` and `kubectl` commands
  and captures output.
- If `kubectl` or `docker` are not installed or not running, the report will
  contain error messages useful for debugging.

If you want, I can run the script for you and collect the report (if the
environment allows running Docker and kubectl).

Additional helper scripts

- `scripts/cleanup_docker.ps1` - interactive helper to remove exited containers
  and prune dangling images. Run this to reclaim space and remove stopped
  containers left over from development.

Quick tips from your run

- Docker is available (Client 28.4.0). Your Docker Desktop context is
  `docker-desktop`.
- Your Kubernetes context `docker-desktop` is running (v1.34.1) and pods in
  `kube-system` are healthy.
- There is at least one exited container `docker/labs-vscode-installer:0.0.9`
  (container `objective_saha`) you may want to remove.

Next steps

1. If you want me to clean up stopped containers automatically, run:

```powershell
pwsh -NoProfile -File .\scripts\cleanup_docker.ps1
```

2. Paste the content of the generated report
   `Reports/docker_k8s_status_<ts>.log` here and I'll parse it and propose
   further fixes (compose scaffolding, manifest generation, or CI automation).
