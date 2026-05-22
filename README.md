# Employee Management API - Platform Engineering Golden Path

A comprehensive Platform Engineering implementation demonstrating standardized Kubernetes deployments, containerization, Helm charts, and multi-environment configuration management for an Internal Developer Platform (IDP).

## 📋 Project Overview

This project implements a reusable **Golden Path** deployment framework for an internal Employee Management API, addressing key Platform Engineering challenges:

- ✅ Eliminated duplicated Kubernetes YAML files through Helm templating
- ✅ Standardized deployment patterns across development teams
- ✅ Environment-agnostic configuration management
- ✅ Automated scaling and operational readiness
- ✅ Simplified developer onboarding experience
- ✅ Production-grade deployment standards

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Platform Engineering Layer             │
│  (Standardized Helm Charts & Deployment Abstractions)   │
└─────────────────────────────────────────────────────────┘
         ↓              ↓              ↓
    ┌────────┐    ┌──────────┐    ┌──────────┐
    │   Dev  │    │ Staging  │    │  Prod    │
    │ Values │    │  Values  │    │  Values  │
    └────────┘    └──────────┘    └──────────┘
         ↓              ↓              ↓
┌─────────────────────────────────────────────────────────┐
│       Kubernetes Cluster (Single Helm Chart)           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │Deployment│  │Service   │  │ConfigMap │  │  HPA   │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
│  ┌──────────┐                                           │
│  │ Ingress  │                                           │
│  └──────────┘                                           │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│         Docker Container (Python Flask App)            │
│  • Lightweight containerization                         │
│  • Health check endpoints                              │
│  • Production-ready configuration                       │
└─────────────────────────────────────────────────────────┘
```

## 📦 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|----------|
| **Application** | Python Flask | RESTful API runtime |
| **Containerization** | Docker | Application packaging |
| **Orchestration** | Kubernetes | Container orchestration |
| **Package Manager** | Helm | Kubernetes template management |
| **Local K8s** | Minikube | Development environment |

## 🚀 Quick Start

### Prerequisites

```bash
# Verify required tools are installed
docker --version      # Docker 20.10+
kubectl version       # Kubernetes 1.20+
helm version          # Helm 3.0+
minikube version      # Minikube 1.20+
```

### 1-Minute Quick Deploy

```bash
# Clone repository
git clone https://github.com/charanspy/employee-platform.git
cd employee-platform

# Start Kubernetes
minikube start --cpus=4 --memory=8192
minikube addons enable ingress
minikube addons enable metrics-server

# Build and push Docker image
docker build -t your-dockerhub/employee-api:v1 -f docker/Dockerfile .
docker push your-dockerhub/employee-api:v1

# Update image in values
sed -i 's|repository:.*|repository: your-dockerhub/employee-api|' helm/employee-api/values.yaml

# Deploy with Helm
helm install employee-dev \
  ./helm/employee-api \
  -f helm/employee-api/values.yaml \
  -f helm/employee-api/values-dev.yaml \
  --namespace dev --create-namespace

# Port forward and test
kubectl port-forward -n dev svc/employee-dev-employee-api 8080:80 &
curl http://localhost:8080/employees
```

### Detailed Setup

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for comprehensive step-by-step instructions.

## 📁 Project Structure

```
employee-platform/
├── app/
│   ├── main.py                 # Flask application with all endpoints
│   ├── requirements.txt         # Python dependencies (Flask)
│   └── __init__.py
├── docker/
│   ├── Dockerfile              # Multi-stage Docker build
│   └── .dockerignore           # Docker build exclusions
├── helm/
│   └── employee-api/
│       ├── Chart.yaml          # Helm chart metadata
│       ├── values.yaml          # Base configuration values
│       ├── values-dev.yaml      # Development environment overrides
│       ├── values-staging.yaml  # Staging environment overrides
│       ├── values-prod.yaml     # Production environment overrides
│       └── templates/
│           ├── _helpers.tpl     # Reusable Helm functions
│           ├── configmap.yaml   # Environment configuration
│           ├── deployment.yaml  # Pod deployment spec
│           ├── service.yaml     # Service exposure
│           ├── ingress.yaml     # Hostname-based routing
│           └── hpa.yaml         # Auto-scaling configuration
├── README.md                    # This file
├── DEPLOYMENT.md                # Step-by-step deployment guide
└── ARCHITECTURE.md              # Design patterns and decisions
```

## 🔧 API Endpoints

### Root Endpoint
```bash
GET /
```
Returns application and environment information.
```json
{
  "app": "Employee API",
  "env": "dev"
}
```

### Employees Endpoint
```bash
GET /employees
```
Returns list of all employees with full details.
```json
[
  {"id": 1, "name": "Alice", "department": "HR"},
  {"id": 2, "name": "Bob", "department": "IT"}
]
```

### Health Endpoint
```bash
GET /health
```
Used by Kubernetes probes to verify pod health.
```json
{
  "status": "healthy"
}
```

### Info Endpoint
```bash
GET /info
```
Displays deployment-specific metadata.
```json
{
  "environment": "dev",
  "team": "Platform Engineering",
  "version": "1.0"
}
```

## 🎯 Helm Configuration

### Base Values (applies to all environments)

```yaml
namespace: dev
replicaCount: 2

image:
  repository: your-dockerhub/employee-api
  tag: v1

service:
  type: ClusterIP
  port: 80
  targetPort: 5000

resources:
  requests:
    cpu: "200m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "256Mi"

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 5
  cpuUtilization: 70
```

### Environment-Specific Configuration

#### Development (`values-dev.yaml`)
- 2 replicas (minimal resource usage)
- Max 5 replicas for testing scaling
- CPU threshold: 70%

#### Staging (`values-staging.yaml`)
- 3 replicas (production-like setup)
- Max 8 replicas
- CPU threshold: 70%

#### Production (`values-prod.yaml`)
- 5 replicas (always running)
- Max 10 replicas for high traffic
- CPU threshold: 70%

## 📊 Deployment Commands

### Install Release

```bash
# Development
helm install employee-dev ./helm/employee-api \
  -f helm/employee-api/values.yaml \
  -f helm/employee-api/values-dev.yaml \
  --namespace dev --create-namespace

# Staging
helm install employee-staging ./helm/employee-api \
  -f helm/employee-api/values.yaml \
  -f helm/employee-api/values-staging.yaml \
  --namespace staging --create-namespace

# Production
helm install employee-prod ./helm/employee-api \
  -f helm/employee-api/values.yaml \
  -f helm/employee-api/values-prod.yaml \
  --namespace prod --create-namespace
```

### Validate Chart

```bash
# Lint for errors
helm lint ./helm/employee-api

# Preview manifests
helm template employee-dev ./helm/employee-api \
  -f helm/employee-api/values-dev.yaml
```

### Upgrade Release

```bash
helm upgrade employee-dev ./helm/employee-api \
  -f helm/employee-api/values.yaml \
  -f helm/employee-api/values-dev.yaml \
  --namespace dev
```

### View Release History

```bash
# See all revisions
helm history employee-dev -n dev

# Rollback to previous
helm rollback employee-dev -n dev

# Uninstall release
helm uninstall employee-dev -n dev
```

## 🛠️ Kubernetes Management

### View Resources

```bash
# Pods
kubectl get pods -n dev
kubectl describe pod <pod-name> -n dev

# Services
kubectl get services -n dev

# ConfigMaps
kubectl get configmaps -n dev

# HPA status
kubectl get hpa -n dev
kubectl describe hpa employee-dev-employee-api -n dev
```

### Monitor Pods

```bash
# View logs
kubectl logs -n dev deployment/employee-dev-employee-api

# Follow logs live
kubectl logs -n dev deployment/employee-dev-employee-api -f

# Port forward for local access
kubectl port-forward -n dev svc/employee-dev-employee-api 8080:80

# Resource usage
kubectl top pods -n dev
```

### Troubleshooting

```bash
# Get events
kubectl get events -n dev --sort-by='.lastTimestamp'

# Describe deployment
kubectl describe deployment -n dev employee-dev-employee-api

# Check HPA scaling
kubectl describe hpa -n dev employee-dev-employee-api

# Execute in pod
kubectl exec -it <pod-name> -n dev -- /bin/bash
```

## 🌐 Ingress Access

### Configure Local Access

```bash
# Get Minikube IP
MINIKUBE_IP=$(minikube ip)

# Add to /etc/hosts
echo "$MINIKUBE_IP employee.local" | sudo tee -a /etc/hosts

# Test via Ingress
curl http://employee.local/
curl http://employee.local/employees
```

## 📈 Autoscaling

### HPA Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  minReplicas: 2        # Minimum pods
  maxReplicas: 5        # Maximum pods
  targetCPUUtilizationPercentage: 70  # Scale when CPU > 70%
```

### Monitor Scaling

```bash
# Watch HPA status
kubectl get hpa -n dev -w

# Check metrics
kubectl top pods -n dev

# View scaling events
kubectl get events -n dev --field-selector reason=SuccessfulRescale
```

## 🔒 Security Features

- ✅ Non-root container execution
- ✅ Read-only root filesystem
- ✅ Resource limits enforcement
- ✅ Network isolation via ClusterIP
- ✅ ConfigMap-based configuration
- ✅ ServiceAccount RBAC isolation

## 📚 Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Step-by-step deployment guide with validation
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Design patterns, architecture decisions, and extensibility

## 🐛 Troubleshooting

### Common Issues

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| **ImagePullBackOff** | `kubectl describe pod` | Verify image pushed to registry |
| **CrashLoopBackOff** | `kubectl logs --previous` | Check app startup errors |
| **Service not accessible** | `kubectl get endpoints` | Verify pod ready state |
| **HPA not scaling** | `kubectl top pods` | Enable metrics-server addon |

See **[DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting)** for detailed troubleshooting guide.

## 🤝 Onboarding New Applications

To deploy a new application using this Golden Path:

1. Copy `helm/employee-api` directory
2. Update `Chart.yaml` with new app name
3. Modify `values.yaml` for your service
4. Create environment-specific `values-{env}.yaml` files
5. Update Docker image path
6. Deploy using same Helm commands

## 📊 Key Platform Engineering Outcomes

| Outcome | Achievement |
|---------|-------------|
| **Code Reuse** | 100% Helm chart reuse across environments |
| **Deployment Time** | Single `helm install` command |
| **Configuration Safety** | Environment configs tracked in Git |
| **Scalability** | Automatic scaling via HPA |
| **Reliability** | Health checks and rolling updates |
| **Onboarding** | Copy, configure, deploy pattern |

## 🎓 Learning Outcomes

This implementation demonstrates:

- Container design with Docker multi-stage builds
- Kubernetes deployment patterns and best practices
- Helm chart templating and configuration management
- Multi-environment deployment strategies
- Horizontal Pod Autoscaling and resource management
- Ingress routing and traffic management
- Platform engineering principles and abstractions
- Infrastructure as Code (IaC) practices
- Operational readiness patterns

## 📚 Best Practices Implemented

- ✅ Infrastructure as Code (IaC)
- ✅ Configuration as Code with values files
- ✅ DRY (Don't Repeat Yourself) through templating
- ✅ Environment parity (same templates, different config)
- ✅ Declarative deployments
- ✅ Health monitoring and probes
- ✅ Resource governance with limits
- ✅ Automatic scaling based on metrics
- ✅ Zero-downtime rolling updates
- ✅ Container security best practices

## 🔄 CI/CD Ready

This implementation integrates seamlessly with CI/CD pipelines:

```bash
# Validate
helm lint ./helm/employee-api

# Test
helm template employee-dev ./helm/employee-api -f values-dev.yaml

# Deploy
helm upgrade --install employee-dev ./helm/employee-api \
  -f values-prod.yaml --namespace prod
```

## 📞 Support & Resources

- **Issues:** Check [troubleshooting section](#-troubleshooting)
- **Documentation:** See DEPLOYMENT.md and ARCHITECTURE.md
- **Logs:** `kubectl logs -n <namespace> deployment/<name>`
- **Events:** `kubectl get events -n <namespace> --sort-by='.lastTimestamp'`

## 📄 Project Information

| Aspect | Details |
|--------|----------|
| **Type** | Platform Engineering Assignment |
| **Framework** | Helm 3 + Kubernetes 1.24+ |
| **Language** | Python 3.9 + Flask |
| **Status** | Production Ready |
| **Version** | 1.0 |
| **Last Updated** | May 2026 |

---

**Ready to deploy?** Start with the [Quick Start](#-quick-start) or read [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

**Want to understand the design?** See [ARCHITECTURE.md](ARCHITECTURE.md) for comprehensive architecture documentation.