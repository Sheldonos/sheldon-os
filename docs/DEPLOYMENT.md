# Sheldon OS Deployment Guide

Complete guide for deploying Sheldon OS to production, staging, and development environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Methods](#deployment-methods)
- [Environment Configuration](#environment-configuration)
- [Monitoring & Observability](#monitoring--observability)
- [Troubleshooting](#troubleshooting)
- [Rollback Procedures](#rollback-procedures)

## Prerequisites

### Required Tools

- **Docker** (20.10+)
- **Kubernetes** (1.24+)
- **kubectl** (1.24+)
- **kustomize** (4.5+) or use `kubectl kustomize`
- **Helm** (3.0+) - optional
- **Git**

### Access Requirements

- Container registry access (GitHub Container Registry)
- Kubernetes cluster access (kubeconfig)
- Secrets management (for production)
- Monitoring stack access (Prometheus/Grafana)

### Infrastructure Requirements

**Development:**
- 2 CPU cores
- 4GB RAM
- 20GB storage

**Staging:**
- 4 CPU cores
- 8GB RAM
- 50GB storage

**Production:**
- 8+ CPU cores
- 16GB+ RAM
- 100GB+ storage
- Load balancer
- TLS certificates

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/sheldon-os/sheldon-os.git
cd sheldon-os
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your values
vim .env
```

### 3. Deploy to Development

```bash
# Using deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh development latest

# Or using Docker Compose
docker-compose -f docker/docker-compose.prod.yml up -d
```

### 4. Verify Deployment

```bash
# Run health checks
chmod +x scripts/health_check.sh
./scripts/health_check.sh development

# Check logs
docker-compose logs -f sheldon-os
```

## Deployment Methods

### Method 1: Automated Script (Recommended)

```bash
# Deploy to staging
./scripts/deploy.sh staging v1.0.0

# Deploy to production
./scripts/deploy.sh production v1.0.0
```

**Features:**
- Automated build and push
- Kubernetes deployment
- Health checks
- Automatic rollback on failure

### Method 2: Manual Kubernetes Deployment

```bash
# Build image
docker build -f docker/Dockerfile.prod -t ghcr.io/sheldon-os/sheldon-os:v1.0.0 .

# Push to registry
docker push ghcr.io/sheldon-os/sheldon-os:v1.0.0

# Update manifests
cd k8s/overlays/production
kustomize edit set image ghcr.io/sheldon-os/sheldon-os:v1.0.0

# Apply to cluster
kubectl apply -k k8s/overlays/production

# Watch rollout
kubectl rollout status deployment/prod-sheldon-os -n sheldon-os
```

### Method 3: Docker Compose (Development Only)

```bash
# Start all services
docker-compose -f docker/docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Method 4: CI/CD Pipeline (Production)

Production deployments use GitHub Actions:

```bash
# Tag release
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# GitHub Actions automatically:
# 1. Runs tests
# 2. Builds Docker image
# 3. Pushes to registry
# 4. Deploys to Kubernetes
# 5. Runs smoke tests
# 6. Notifies team
```

## Environment Configuration

### Development

**Purpose:** Local development and testing

**Configuration:**
```yaml
replicas: 1
resources:
  requests:
    cpu: 250m
    memory: 256Mi
  limits:
    cpu: 1000m
    memory: 1Gi
```

**Access:**
- URL: http://localhost:8000
- Metrics: http://localhost:9090

### Staging

**Purpose:** Pre-production testing and validation

**Configuration:**
```yaml
replicas: 2
resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 2000m
    memory: 2Gi
```

**Access:**
- URL: https://api-staging.sheldon-os.com
- Grafana: https://grafana-staging.sheldon-os.com

### Production

**Purpose:** Live production environment

**Configuration:**
```yaml
replicas: 5-20 (auto-scaling)
resources:
  requests:
    cpu: 1000m
    memory: 1Gi
  limits:
    cpu: 4000m
    memory: 4Gi
```

**Access:**
- URL: https://api.sheldon-os.com
- Grafana: https://grafana.sheldon-os.com

## Secrets Management

### Creating Secrets

```bash
# Create namespace
kubectl create namespace sheldon-os

# Create secrets from file
kubectl create secret generic sheldon-os-secrets \
  --from-literal=database-url="postgresql://user:pass@host:5432/db" \
  --from-literal=redis-url="redis://redis:6379/0" \
  --from-literal=secret-key="your-secret-key" \
  --from-literal=jwt-secret="your-jwt-secret" \
  --from-literal=openai-api-key="your-openai-key" \
  --from-literal=anthropic-api-key="your-anthropic-key" \
  -n sheldon-os

# Create TLS secret
kubectl create secret tls sheldon-os-tls \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key \
  -n sheldon-os
```

### Using External Secrets (Recommended)

```bash
# Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace

# Configure SecretStore (AWS Secrets Manager example)
kubectl apply -f - <<EOF
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: sheldon-os
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
EOF
```

## Monitoring & Observability

### Prometheus Metrics

**Available Metrics:**
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request duration
- `sheldon_os_active_agents` - Active agent count
- `sheldon_os_agent_failures_total` - Agent failures
- `container_memory_usage_bytes` - Memory usage
- `container_cpu_usage_seconds_total` - CPU usage

**Access:**
```bash
# Port-forward Prometheus
kubectl port-forward -n sheldon-os svc/prometheus 9091:9090

# Open browser
open http://localhost:9091
```

### Grafana Dashboards

**Pre-configured Dashboards:**
1. **System Overview** - Health, requests, errors
2. **Performance** - Response times, throughput
3. **Infrastructure** - CPU, memory, disk
4. **Business Metrics** - Users, revenue, adoption

**Access:**
```bash
# Port-forward Grafana
kubectl port-forward -n sheldon-os svc/grafana 3000:3000

# Login
# Username: admin
# Password: (from secret)
```

### Logging

**View Logs:**
```bash
# Application logs
kubectl logs -f deployment/sheldon-os -n sheldon-os

# All pods
kubectl logs -f -l app=sheldon-os -n sheldon-os

# Specific pod
kubectl logs -f pod/sheldon-os-xxxxx -n sheldon-os

# Previous container (after crash)
kubectl logs --previous pod/sheldon-os-xxxxx -n sheldon-os
```

### Alerts

**Critical Alerts:**
- High error rate (>5%)
- Database down
- Redis down
- Pod crash looping

**Warning Alerts:**
- High CPU (>80%)
- High memory (>90%)
- Slow response time (>2s)
- Low disk space (<20%)

## Troubleshooting

### Common Issues

#### 1. Pods Not Starting

```bash
# Check pod status
kubectl get pods -n sheldon-os

# Describe pod
kubectl describe pod/sheldon-os-xxxxx -n sheldon-os

# Check events
kubectl get events -n sheldon-os --sort-by='.lastTimestamp'
```

**Common Causes:**
- Image pull errors
- Resource constraints
- Configuration errors
- Secret not found

#### 2. High Error Rate

```bash
# Check application logs
kubectl logs -f deployment/sheldon-os -n sheldon-os | grep ERROR

# Check database connectivity
kubectl exec -it deployment/sheldon-os -n sheldon-os -- psql $DATABASE_URL -c "SELECT 1"

# Check Redis connectivity
kubectl exec -it deployment/sheldon-os -n sheldon-os -- redis-cli -u $REDIS_URL ping
```

#### 3. Slow Performance

```bash
# Check resource usage
kubectl top pods -n sheldon-os

# Check HPA status
kubectl get hpa -n sheldon-os

# Scale manually if needed
kubectl scale deployment/sheldon-os --replicas=10 -n sheldon-os
```

#### 4. Database Connection Pool Exhausted

```bash
# Check active connections
kubectl exec -it postgres-0 -- psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Increase pool size in ConfigMap
kubectl edit configmap sheldon-os-config -n sheldon-os
# Update DB_POOL_SIZE

# Restart pods
kubectl rollout restart deployment/sheldon-os -n sheldon-os
```

## Rollback Procedures

### Automatic Rollback

The deployment script automatically rolls back on failure.

### Manual Rollback

```bash
# View rollout history
kubectl rollout history deployment/sheldon-os -n sheldon-os

# Rollback to previous version
kubectl rollout undo deployment/sheldon-os -n sheldon-os

# Rollback to specific revision
kubectl rollout undo deployment/sheldon-os --to-revision=3 -n sheldon-os

# Check rollback status
kubectl rollout status deployment/sheldon-os -n sheldon-os
```

### Using Rollback Script

```bash
# Rollback to previous version
./scripts/rollback.sh production

# Rollback to specific revision
./scripts/rollback.sh production 3
```

## Best Practices

### Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Security scan completed
- [ ] Database migrations tested
- [ ] Secrets configured
- [ ] Monitoring alerts configured
- [ ] Rollback plan documented
- [ ] Team notified

### During Deployment

- [ ] Monitor metrics dashboard
- [ ] Watch application logs
- [ ] Check error rates
- [ ] Verify health checks
- [ ] Run smoke tests
- [ ] Monitor user impact

### Post-Deployment

- [ ] Verify all services healthy
- [ ] Check performance metrics
- [ ] Review error logs
- [ ] Update documentation
- [ ] Notify stakeholders
- [ ] Monitor for 24 hours

## Maintenance Windows

### Scheduled Maintenance

**Recommended Windows:**
- **Staging:** Anytime
- **Production:** Sunday 2-4 AM UTC (lowest traffic)

**Notification:**
- 7 days advance notice
- Status page update
- Email to customers
- In-app banner

### Emergency Maintenance

**Process:**
1. Assess severity
2. Notify team immediately
3. Update status page
4. Execute fix
5. Post-mortem within 24 hours

## Support

### Documentation
- Architecture: `/docs/architecture/`
- API Reference: `/docs/api/`
- Runbooks: `/docs/runbooks/`

### Contacts
- **On-Call:** PagerDuty
- **Slack:** #sheldon-os-ops
- **Email:** ops@sheldon-os.com

### Escalation
1. On-call engineer
2. Engineering lead
3. CTO
4. CEO (critical only)