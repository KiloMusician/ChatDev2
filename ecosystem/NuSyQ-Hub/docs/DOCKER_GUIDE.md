# Docker Setup and Deployment Guide

This guide covers Docker-based development and deployment for NuSyQ-Hub.

## Quick Start

### Development
```bash
# Start development environment
docker compose --profile dev up -d

# View logs
docker compose logs -f nusyq-hub-dev

# Stop services
docker compose --profile dev down
```

### Production
```bash
# Build and start production services
docker compose up -d

# Scale services
docker compose up -d --scale nusyq-hub=3

# Stop services
docker compose down
```

## Docker Compose Profiles

### Default (Minimal)
- `nusyq-hub`: Main application
- `ollama`: LLM service

```bash
docker compose up -d
```

### Development (`dev`)
- All default services
- `nusyq-hub-dev`: Development container with hot-reload and debugging

```bash
docker compose --profile dev up -d
```

### Full (`full`)
- All default services
- `ollama-mock`: Mock Ollama for testing
- `redis`: Caching and task queue
- `postgres`: Persistent storage
- `nginx`: Reverse proxy

```bash
docker compose --profile full up -d
```

### Monitoring (`monitoring`)
- `prometheus`: Metrics collection
- `grafana`: Visualization dashboards

```bash
docker compose --profile monitoring up -d
```

### Testing (`test`)
- Lightweight services for CI/CD testing
- `ollama-mock`: Mock Ollama service

```bash
docker compose --profile test up -d
```

## Environment Configuration

Copy `.env.docker` to `.env` and customize:

```bash
cp .env.docker .env
# Edit .env with your configuration
```

Key variables:
- `APP_PORT`: Main application port (default: 5000)
- `OLLAMA_BASE_URL`: Ollama service URL
- `POSTGRES_PASSWORD`: Database password
- `GRAFANA_PASSWORD`: Grafana admin password

## Building Images

### Build specific services
```bash
docker compose build nusyq-hub
docker compose build nusyq-hub-dev
```

### Build all services
```bash
docker compose build
```

### Build with no cache
```bash
docker compose build --no-cache
```

## Service Management

### Start services
```bash
# All default services
docker compose up -d

# Specific service
docker compose up -d nusyq-hub

# Multiple profiles
docker compose --profile full --profile monitoring up -d
```

### Stop services
```bash
# All services
docker compose down

# Keep volumes
docker compose down --volumes
```

### Restart services
```bash
docker compose restart nusyq-hub
```

### View logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f nusyq-hub

# Last 100 lines
docker compose logs --tail=100 nusyq-hub
```

## Development Workflow

### 1. Start development environment
```bash
docker compose --profile dev up -d
```

### 2. Attach debugger
The development container exposes port 5678 for debugpy. Configure your IDE:

**VS Code (launch.json):**
```json
{
  "name": "Docker: Attach to Python",
  "type": "python",
  "request": "attach",
  "connect": {
    "host": "localhost",
    "port": 5678
  },
  "pathMappings": [
    {
      "localRoot": "${workspaceFolder}",
      "remoteRoot": "/app"
    }
  ]
}
```

### 3. Hot reload
The development container mounts your source code, so changes are reflected immediately.

### 4. Run tests inside container
```bash
docker compose exec nusyq-hub-dev pytest tests/
```

### 5. Shell access
```bash
docker compose exec nusyq-hub-dev bash
```

## Production Deployment

### 1. Build production images
```bash
docker compose -f docker-compose.yml build
```

### 2. Push to registry
```bash
docker tag nusyq-hub:latest ghcr.io/your-org/nusyq-hub:latest
docker push ghcr.io/your-org/nusyq-hub:latest
```

### 3. Deploy with full stack
```bash
docker compose --profile full up -d
```

### 4. Configure Nginx (optional)
Edit `deploy/nginx/nginx.conf` for your domain and SSL certificates.

### 5. Set up monitoring
```bash
docker compose --profile monitoring up -d
```

Access Grafana at http://localhost:3000 (default: admin/admin)

## Health Checks

All services include health checks. View status:

```bash
docker compose ps
```

Healthy services show `(healthy)` status.

## Troubleshooting

### Container won't start
```bash
# Check logs
docker compose logs nusyq-hub

# Check configuration
docker compose config

# Remove and recreate
docker compose down
docker compose up -d --force-recreate
```

### Database connection issues
```bash
# Check postgres is healthy
docker compose ps postgres

# Connect to postgres
docker compose exec postgres psql -U nusyq -d nusyq

# Reset database
docker compose down -v
docker compose up -d postgres
```

### Ollama not responding
```bash
# Check Ollama health
docker compose exec ollama curl localhost:11434/api/version

# Pull models
docker compose exec ollama ollama pull qwen2.5-coder

# List models
docker compose exec ollama ollama list
```

### Performance issues
```bash
# Check resource usage
docker stats

# Increase limits in docker-compose.yml:
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
```

## Backup and Restore

### Backup volumes
```bash
# Backup postgres data
docker compose exec postgres pg_dump -U nusyq nusyq > backup.sql

# Backup all volumes
docker run --rm \
  -v nusyq-hub_postgres-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz /data
```

### Restore volumes
```bash
# Restore postgres
docker compose exec -T postgres psql -U nusyq nusyq < backup.sql

# Restore volume
docker run --rm \
  -v nusyq-hub_postgres-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/postgres-backup.tar.gz -C /
```

## Security Best Practices

1. **Use secrets management:**
   ```bash
   # Use Docker secrets in production
   echo "secret_password" | docker secret create postgres_password -
   ```

2. **Run as non-root:**
   All containers run as non-root users by default.

3. **Network isolation:**
   Services communicate through the `nusyq-network` bridge.

4. **Update regularly:**
   ```bash
   docker compose pull
   docker compose up -d
   ```

5. **Scan for vulnerabilities:**
   ```bash
   docker scan nusyq-hub:latest
   ```

## Performance Optimization

### Build cache
```bash
# Use BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

### Layer caching
Order Dockerfile instructions from least to most frequently changing.

### Multi-stage builds
Already implemented in `Dockerfile.prod` for minimal image size.

### Resource limits
Configure in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
```

## CI/CD Integration

### GitHub Actions
The provided workflows automatically:
- Build and test images
- Scan for vulnerabilities
- Push to GHCR
- Deploy to environments

### Manual deployment
```bash
# Pull latest images
docker compose pull

# Update running services
docker compose up -d --no-deps --build nusyq-hub
```

## Monitoring and Observability

### Prometheus metrics
Access metrics at http://localhost:9090

### Grafana dashboards
Access dashboards at http://localhost:3000

### Application logs
```bash
# Stream logs
docker compose logs -f

# Export logs
docker compose logs > logs.txt
```

### Health endpoints
- App: http://localhost:5000/health
- Ollama: http://localhost:11434/api/version
- Prometheus: http://localhost:9090/-/healthy

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Ollama Documentation](https://github.com/jmorganca/ollama)
- [Nginx Configuration](https://nginx.org/en/docs/)
