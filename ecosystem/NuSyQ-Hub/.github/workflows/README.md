# GitHub Actions Workflows for NuSyQ-Hub

This directory contains automated CI/CD workflows for the NuSyQ-Hub project.

## Workflows Overview

### 🔨 docker-build-test.yml
**Trigger:** Push to main branches, PRs
**Purpose:** Build, test, and scan Docker images

**Jobs:**
- `docker-lint`: Lint all Dockerfiles with Hadolint
- `build-and-test`: Build and test all Docker variants (base, dev, prod)
- `integration-test`: Run Docker Compose integration tests
- `multi-arch-build`: Build multi-architecture images (amd64, arm64) on master

**Features:**
- Multi-stage builds with caching
- Security scanning with Trivy
- Vulnerability reporting to GitHub Security
- Container registry publishing (GHCR)
- Health check validation

### 🧪 ci-enhanced.yml
**Trigger:** Push, PR, Daily schedule
**Purpose:** Comprehensive code quality and validation

**Jobs:**
- `code-quality`: Linting, formatting, type checking, tests (matrix: OS × Python version)
- `security-scan`: Safety, Bandit, pip-audit security checks
- `dependency-check`: Analyze dependency tree and versions
- `system-validation`: Run NuSyQ-specific validation scripts
- `performance-benchmark`: Run performance benchmarks (master only)

**Features:**
- Cross-platform testing (Ubuntu, Windows)
- Multiple Python versions (3.11, 3.12)
- Code coverage reporting
- Security artifact uploads
- Performance tracking

### 🚀 deploy.yml
**Trigger:** Release published, Manual dispatch
**Purpose:** Production deployment pipeline

**Jobs:**
- `build-production-image`: Build optimized multi-arch production image
- `deploy`: Deploy to staging/production environments
- `rollback`: Automatic rollback on deployment failure

**Features:**
- Semantic versioning support
- Environment-specific deployments
- Health checks
- Rollback capabilities
- Deployment notifications

## Docker Integration Best Practices

### 1. Multi-Stage Builds
All Dockerfiles use multi-stage builds to:
- Separate build dependencies from runtime
- Minimize final image size
- Improve build caching

### 2. Security Hardening
- Non-root user execution
- Minimal base images (Alpine for prod)
- Security scanning (Trivy)
- Vulnerability reporting

### 3. Caching Strategy
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```
Uses GitHub Actions cache for faster builds.

### 4. Image Variants
- **Base (Dockerfile)**: Balanced production image
- **Dev (Dockerfile.dev)**: Development with hot-reload, debugging
- **Prod (Dockerfile.prod)**: Optimized Alpine-based production

### 5. Testing Layers
1. Dockerfile linting (Hadolint)
2. Image build validation
3. Container runtime tests
4. Integration tests (Docker Compose)
5. Security scans (Trivy)

## Environment Variables

Required secrets and variables:

### Secrets
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions
- Add deployment-specific secrets in repository settings

### Variables
- `REGISTRY`: ghcr.io (default)
- `IMAGE_NAME`: Derived from repository name

## Local Testing

### Test Docker builds locally:
```bash
# Test base image
docker build -f Dockerfile -t nusyq-hub:test .

# Test dev image
docker build -f Dockerfile.dev -t nusyq-hub:dev .

# Test prod image
docker build -f Dockerfile.prod -t nusyq-hub:prod .

# Run tests
docker run --rm nusyq-hub:test python -m pytest

# Test with compose
docker compose -f deploy/docker-compose.dev.yml up --build
```

### Test workflows locally with act:
```bash
# Install act: https://github.com/nektos/act
brew install act  # or equivalent

# Run CI workflow
act push -W .github/workflows/ci-enhanced.yml

# Run Docker workflow
act push -W .github/workflows/docker-build-test.yml
```

## Workflow Customization

### Add deployment targets:
Edit `deploy.yml` to add your deployment logic:
- Kubernetes (kubectl apply)
- Docker Compose (docker-compose up)
- Cloud providers (AWS, Azure, GCP)
- Configuration management (Terraform, Ansible)

### Add custom tests:
Add test scripts in the `integration-test` job:
```yaml
- name: Custom integration test
  run: |
    python scripts/your_test_script.py
```

### Modify build matrix:
Change Python versions or OS in `ci-enhanced.yml`:
```yaml
matrix:
  os: [ubuntu-latest, windows-latest, macos-latest]
  python-version: ['3.11', '3.12']
```

## Troubleshooting

### Build cache issues
Clear GitHub Actions cache in repository settings or add:
```yaml
cache-to: type=gha,mode=max,ignore-error=true
```

### Permission denied errors
Ensure proper file ownership in Dockerfile:
```dockerfile
COPY --chown=nusyq:nusyq . .
```

### Test failures
Check logs in GitHub Actions UI or run locally:
```bash
docker compose logs
docker exec <container> pytest -v
```

## Performance Optimization

### Build speed tips:
1. Use `.dockerignore` to exclude unnecessary files
2. Order Dockerfile instructions from least to most frequently changing
3. Leverage build cache with `--cache-from`
4. Use BuildKit features (secrets, SSH, cache mounts)

### Resource limits:
Add resource constraints to workflows:
```yaml
container:
  image: ubuntu:latest
  options: --cpus 2 --memory 4g
```

## Monitoring and Alerts

### Set up notifications:
Add notification steps to workflows:
```yaml
- name: Notify on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Track metrics:
- Build times in Actions insights
- Security vulnerabilities in Security tab
- Code coverage in Codecov
- Performance benchmarks in benchmark dashboard

## Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [BuildKit Documentation](https://docs.docker.com/build/buildkit/)
- [Trivy Security Scanner](https://aquasecurity.github.io/trivy/)
