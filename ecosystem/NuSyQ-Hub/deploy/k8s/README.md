# Kubernetes Deployment for NuSyQ-Hub

Complete Kubernetes manifests for deploying NuSyQ-Hub to any K8s cluster.

## Prerequisites

- Kubernetes cluster (docker-desktop, minikube, kind, or cloud provider)
- kubectl configured to point to your cluster
- Docker images built and available

## Quick Start

### 1. Build Docker Image

```bash
# From repository root
docker build -t nusyq-hub:latest -f Dockerfile .
```

### 2. Deploy with kubectl

```bash
# Apply all manifests at once
kubectl apply -k deploy/k8s/

# Or apply individually
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s/configmap.yaml
kubectl apply -f deploy/k8s/secret.yaml
kubectl apply -f deploy/k8s/postgres.yaml
kubectl apply -f deploy/k8s/redis.yaml
kubectl apply -f deploy/k8s/deployment.yaml
kubectl apply -f deploy/k8s/service.yaml
kubectl apply -f deploy/k8s/ingress.yaml
```

### 3. Verify Deployment

```bash
# Check all resources
kubectl get all -n nusyq-hub

# Check pods
kubectl get pods -n nusyq-hub

# Check logs
kubectl logs -f -n nusyq-hub deployment/nusyq-hub

# Check health
kubectl port-forward -n nusyq-hub svc/nusyq-hub-service 5000:5000
curl http://localhost:5000/health
```

## Access the Application

### Port Forward (Local Development)

```bash
kubectl port-forward -n nusyq-hub svc/nusyq-hub-service 5000:5000
```

Then access at http://localhost:5000

### NodePort (docker-desktop)

Service is exposed on NodePort 30500:

```bash
curl http://localhost:30500/health
```

### Ingress (with nginx-ingress)

1. Install nginx-ingress controller:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
```

2. Add to `/etc/hosts` (or `C:\Windows\System32\drivers\etc\hosts`):

```
127.0.0.1 nusyq-hub.local
```

3. Access at http://nusyq-hub.local

## Configuration

### Update ConfigMap

Edit `deploy/k8s/configmap.yaml` and apply:

```bash
kubectl apply -f deploy/k8s/configmap.yaml
kubectl rollout restart -n nusyq-hub deployment/nusyq-hub
```

### Update Secrets

**Never commit secrets to git!** Use sealed-secrets or external secret managers in production.

```bash
# For local dev only:
kubectl create secret generic nusyq-hub-secrets \
  --from-literal=DATABASE_URL="postgres://..." \
  --from-literal=OPENAI_API_KEY="sk-..." \
  -n nusyq-hub \
  --dry-run=client -o yaml | kubectl apply -f -
```

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl describe pod -n nusyq-hub <pod-name>

# Check logs
kubectl logs -n nusyq-hub <pod-name>

# Check events
kubectl get events -n nusyq-hub --sort-by='.lastTimestamp'
```

### Image pull errors

For local images with docker-desktop:

```bash
# Ensure image exists
docker images | grep nusyq-hub

# Set imagePullPolicy to IfNotPresent in deployment.yaml
```

### Database connection issues

```bash
# Check postgres is running
kubectl get pods -n nusyq-hub -l app=postgres

# Check postgres logs
kubectl logs -n nusyq-hub -l app=postgres

# Test connection
kubectl exec -it -n nusyq-hub deployment/nusyq-hub -- \
  python -c "import psycopg2; psycopg2.connect('postgres://nusyq:nusyq@postgres-service:5432/nusyq')"
```

## Cleanup

```bash
# Delete all resources
kubectl delete -k deploy/k8s/

# Or delete namespace (cascades to all resources)
kubectl delete namespace nusyq-hub
```

## Environment-Specific Deployments

### Development

```bash
kubectl apply -k deploy/k8s/
```

### Production

Create overlays:

```bash
mkdir -p deploy/k8s/overlays/production
```

Use kustomize to manage environment-specific configs.

## Monitoring

### Resource Usage

```bash
# Pod resource usage
kubectl top pods -n nusyq-hub

# Node resource usage
kubectl top nodes
```

### Scaling

```bash
# Scale deployment
kubectl scale deployment/nusyq-hub -n nusyq-hub --replicas=3

# Autoscaling
kubectl autoscale deployment/nusyq-hub -n nusyq-hub \
  --min=1 --max=10 --cpu-percent=80
```

## Advanced

### Using Helm

Convert to Helm chart:

```bash
mkdir -p deploy/helm/nusyq-hub
# Move manifests to templates/ and add values.yaml
```

### CI/CD Integration

GitHub Actions example:

```yaml
- name: Deploy to Kubernetes
  run: |
    kubectl apply -k deploy/k8s/
    kubectl rollout status -n nusyq-hub deployment/nusyq-hub
```

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize](https://kustomize.io/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
