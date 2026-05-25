# Architecture & Design Decisions

This document explains the architectural decisions and design patterns used in the Employee Management API platform.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Design Principles](#design-principles)
3. [Component Design](#component-design)
4. [Configuration Management](#configuration-management)
5. [Scaling Strategy](#scaling-strategy)
6. [Security Considerations](#security-considerations)
7. [Operational Patterns](#operational-patterns)

## Architecture Overview

### High-Level Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    Developer/User                          │
└────────────────────────┬─────────────────────────────────┘
                         │
                    HTTP/HTTPS
                         │
┌────────────────────────▼─────────────────────────────────┐
│                    Ingress Controller                      │
│              (nginx-ingress / Nginx)                       │
│  • Hostname-based routing                                │
│  • TLS termination                                       │
│  • Rate limiting                                         │
└────────────────────────┬─────────────────────────────────┘
                         │
                   Service Discovery
                         │
┌────────────────────────▼─────────────────────────────────┐
│                   Service (ClusterIP)                     │
│              Load balancing across pods                   │
└────────────────────────┬─────────────────────────────────┘
                         │
              Pod Replication (via Deployment)
                         │
    ┌────────────────┬────────────────┬────────────────┐
    │                │                │                │
┌───▼───┐        ┌───▼───┐       ┌────▼───┐       ┌───▼───┐
│ Pod 1 │        │ Pod 2 │       │ Pod 3  │       │ Pod 4 │
│ Flask │        │ Flask │       │ Flask  │       │ Flask │
│ App   │        │ App   │       │ App    │       │ App   │
└───────┘        └───────┘       └────────┘       └───────┘
    │                │                │                │
    └────────────────┴────────────────┴────────────────┘
             Monitored by HPA
          (Horizontal Pod Autoscaler)
```

### Component Interactions

```
┌──────────────────────────────────────────────┐
│         Helm Chart (Template Engine)          │
│  • Abstracts Kubernetes complexity           │
│  • Enables configuration management          │
│  • Supports multi-environment deployments    │
└──────────────────────┬───────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    ┌────────┐   ┌──────────┐   ┌─────────┐
    │Dev Cfg │   │Staging Cfg│  │Prod Cfg │
    │values  │   │values     │  │values   │
    └─────┬──┘   └────┬──────┘  └────┬────┘
         │            │              │
         └────────────┴──────────────┘
                  │
    ┌─────────────▼──────────────┐
    │  Kubernetes Manifests      │
    │  • Deployment             │
    │  • Service                │
    │  • ConfigMap              │
    │  • Ingress                │
    │  • HPA                    │
    │  • ServiceAccount         │
    └─────────────┬──────────────┘
                  │
    ┌─────────────▼──────────────┐
    │  Kubernetes Cluster        │
    │  • Pod orchestration       │
    │  • Service discovery       │
    │  • Load balancing          │
    │  • Auto-scaling            │
    └────────────────────────────┘
```

## Design Principles

### 1. Platform Engineering Paradigm

**Principle:** Separate platform concerns from application concerns

**Implementation:**
- **Platform Concerns:** Deployments, scaling, networking (Helm templates)
- **Application Concerns:** Business logic, endpoints (Python Flask app)

**Benefit:** Developers only modify `app/main.py` and `app/requirements.txt`; Operators manage Helm charts

### 2. Infrastructure as Code (IaC)

**Principle:** All infrastructure defined in version-controlled files

**Implementation:**
- Kubernetes manifests in YAML
- Helm charts for templating
- Environment configs in `values-*.yaml` files

**Benefit:**
- Reproducible deployments
- Version control history
- Code review process for changes
- Disaster recovery capability

### 3. Configuration Management Separation

**Principle:** Separate configuration from templates; different environments use same templates

**Implementation:**
- Base configuration: `values.yaml`
- Environment-specific: `values-dev.yaml`, `values-staging.yaml`, `values-prod.yaml`

**Example:**
```yaml
# Base values.yaml
replicaCount: 2
autoscaling:
  maxReplicas: 5

# Environment override (values-prod.yaml)
replicaCount: 5
autoscaling:
  maxReplicas: 10
# resource.limits.memory not specified = inherited from base
```

**Benefit:**
- Single source of truth for templates
- Environment-specific changes tracked separately
- Easy to promote configurations across environments

### 4. Don't Repeat Yourself (DRY)

**Principle:** Eliminate duplication through templating and reusability

**Implementation:**
- `_helpers.tpl` contains reusable functions
- Named resources use consistent naming via helpers
- Common labels applied to all resources

**Example:**
```helm
# _helpers.tpl
{{- define "employee-api.fullname" -}}
{{ .Release.Name }}-{{ .Chart.Name }}
{{- end }}

# Used in all manifests
name: {{ include "employee-api.fullname" . }}
```

**Benefit:**
- Reduced maintenance overhead
- Consistent naming across resources
- Easier refactoring

### 5. Multi-Environment Parity

**Principle:** Same deployment process for all environments

**Implementation:**
- Identical Helm templates for all environments
- Environment differentiation through values files only
- Same validation procedures across environments

**Benefit:**
- Reduced deployment errors
- Easier troubleshooting
- Predictable behavior

### 6. Declarative Over Imperative

**Principle:** Describe desired state, not how to achieve it

**Implementation:**
- Kubernetes Deployments (declarative)
- Not shell scripts or manual kubectl commands
- Let Kubernetes reconciliation engine manage state

**Benefit:**
- Self-healing infrastructure
- Automatic recovery from failures
- Transparent state management

## Component Design

### Docker Container Design

#### Multi-Stage Build

```dockerfile
# Stage 1: Builder
FROM python:3.9-slim as builder
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY app/ .
EXPOSE 5000
USER nobody
CMD ["python", "main.py"]
```

**Design Decisions:**
1. **Slim base image:** Reduces attack surface and image size
2. **Multi-stage build:** Final image excludes build artifacts
3. **Non-root user:** Security best practice
4. **User nobody:** Prevents privilege escalation

**Size Optimization:**
- Build image: ~500MB (includes build dependencies)
- Final image: ~156MB (only runtime dependencies)

### Kubernetes Deployment Design

#### Deployment Strategy

```yaml
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

**Design Decisions:**
- **RollingUpdate:** Zero-downtime updates
- **maxSurge: 1:** One extra pod during rollout (smooth traffic transition)
- **maxUnavailable: 0:** Always maintain minimum replicas

**Benefits:**
- No service interruption during updates
- Automatic rollback capability
- Gradual traffic shift

#### Resource Management

```yaml
resources:
  requests:
    cpu: "200m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "256Mi"
```

**Design Decisions:**
- **Requests:** Kubernetes reserves this amount for scheduling
- **Limits:** Kubernetes terminates pod if exceeded
- **Ratio (2.5:1):** Allows burst traffic handling

**Benefits:**
- Predictable resource allocation
- Prevents noisy neighbor problem
- Enables efficient bin-packing on nodes

#### Health Checks

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 10

livenessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 15
  periodSeconds: 20
```

**Design Decisions:**
- **Readiness Probe:** Checks if pod can receive traffic
- **Liveness Probe:** Checks if pod is healthy (crashes unhealthy pods)
- **Delay Times:** Allow app startup before probing

**Benefits:**
- Automatic failure detection
- Automatic recovery through pod restart
- Only routes traffic to healthy pods

### Service Design

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "employee-api.fullname" . }}
spec:
  type: ClusterIP
  ports:
    - port: 80
      targetPort: 5000
  selector:
    app: {{ include "employee-api.fullname" . }}
```

**Design Decisions:**
- **ClusterIP:** Internal-only service (better security than NodePort)
- **Port 80:** Standard HTTP port for ingress
- **Target port 5000:** Flask app port

**Benefits:**
- Load balancing across pods
- Service discovery via DNS
- Internal communication without exposure

### Ingress Design

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    kubernetes.io/ingress.class: nginx
spec:
  rules:
    - host: employee.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ include "employee-api.fullname" . }}
                port:
                  number: 80
```

**Design Decisions:**
- **Hostname-based routing:** Multiple services via single IP
- **NGINX class:** Standard ingress controller
- **Prefix pathType:** Matches all subpaths

**Benefits:**
- Single entry point for traffic
- Hostname-based virtual hosting
- Layer 7 (application) routing

## Configuration Management

### Values File Hierarchy

```
values.yaml (base, all environments)
    ↓
values-{env}.yaml (environment-specific overrides)
    ↓
Merged configuration
    ↓
Rendered Kubernetes manifests
```

### Configuration Override Pattern

```yaml
# values.yaml (base)
replicaCount: 2
resources:
  limits:
    memory: "256Mi"
autoscaling:
  maxReplicas: 5

# values-prod.yaml (override for production)
replicaCount: 5
autoscaling:
  maxReplicas: 10
# resource.limits.memory not specified = inherited from base
```

**How Helm Merges:**
1. Start with `values.yaml`
2. Merge in `values-prod.yaml`
3. Templates see merged result
4. Unspecified values use base defaults

### ConfigMap Pattern

```yaml
# From ConfigMap template
apiVersion: v1
kind: ConfigMap
data:
  ENV: {{ .Values.env.ENV | quote }}
  TEAM: {{ .Values.env.TEAM | quote }}
```

**Benefits:**
- Configuration as Kubernetes objects
- Change tracking via revision history
- Rolling pod restart on changes (via Deployment label trigger)

## Scaling Strategy

### Horizontal Pod Autoscaling (HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  scaleTargetRef:
    kind: Deployment
    name: employee-dev-employee-api
  minReplicas: 2
  maxReplicas: 5
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

**Scaling Logic:**
```
Current CPU Usage: 85%
Target: 70%
Desired Replicas = 2 * (85 / 70) = 2.43 ≈ 3 replicas

Result: Scale up from 2 to 3 pods
```

**Design Decisions:**
- **CPU-based scaling:** Most common metric
- **70% threshold:** Provides headroom for traffic spikes
- **Min: 2, Max: 5 (dev):** Protects against thrashing
- **Min: 2, Max: 10 (prod):** Higher capacity for production

**Benefits:**
- Automatic response to load
- Cost optimization (scale down when idle)
- High availability (multiple replicas)

### Scaling Limits

```yaml
# Development: Safe for experiments
minReplicas: 2      # Always running
maxReplicas: 5      # Cost-controlled

# Staging: Near-production
minReplicas: 2
maxReplicas: 8

# Production: High availability
minReplicas: 2      # Never less than 2
maxReplicas: 10     # Can scale for large traffic
```

## Security Considerations

### Defense in Depth

#### 1. Container Level

```dockerfile
# Non-root user
USER nobody
# Read-only root filesystem
RUN chmod 555 /
```

#### 2. Pod Level

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 65534
  fsReadOnlyRootFilesystem: true
```

#### 3. Network Level

```yaml
# Via Ingress
metadata:
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
```

#### 4. Service Level

```yaml
# ClusterIP only (no external exposure)
spec:
  type: ClusterIP
```

### Configuration Security

- Secrets managed separately (not in ConfigMaps)
- Sensitive data never committed to version control
- RBAC for pod access (via ServiceAccount)

## Operational Patterns

### Deployment Lifecycle

```
1. Development
   ├─ Fast iteration
   ├─ 2 replicas
   ├─ Low resource limits
   └─ Auto-scaling enabled

2. Staging
   ├─ Production-like
   ├─ 3 replicas
   ├─ Medium resource limits
   └─ Full testing

3. Production
   ├─ Stable, tested code
   ├─ 5 replicas
   ├─ Production resource limits
   └─ Aggressive scaling (max 10)
```

### Upgrade Process

```
1. Update code in Git
2. Build new Docker image
3. Push to registry
4. Update image tag in values.yaml
5. helm upgrade <release>
6. Kubernetes performs rolling update
7. Old pods gradually terminated
8. New pods receive traffic
9. Zero downtime maintained
```

### Rollback Process

```
1. Helm maintains release history
2. Identify problematic release: helm history <release>
3. Rollback: helm rollback <release> <revision>
4. Kubernetes reverts to previous state
5. Traffic redirected to known-good version
```

### Monitoring & Observability

```yaml
# Health checks provide availability signals
GET /health → 200 OK = healthy
GET /health → 5xx = unhealthy

# ConfigMap labels track configurations
kubectl describe cm <name>

# Events show scaling actions
kubectl get events --sort-by='.lastTimestamp'

# Metrics available for monitoring
kubectl top pods
kubectl top nodes
```

### Troubleshooting Workflow

```
Issue → Symptom → Investigation → Root Cause → Fix

Example:
• Issue: Slow response times
• Symptom: Pods consuming 95% CPU
• Investigation: kubectl top pods, kubectl describe hpa
• Root Cause: No scaling due to metrics-server issue
• Fix: Enable metrics-server addon
```

## Comparison: Golden Path vs Unstructured Approach

| Aspect | Golden Path | Without Structure |
|--------|------------|-------------------|
| **Templates** | Reusable Helm charts | Duplicated YAML files |
| **Configuration** | Environment-specific values | Hardcoded in manifests |
| **Scaling** | Declarative via HPA | Manual intervention |
| **Updates** | Rolling updates (zero downtime) | Downtime or manual |
| **Onboarding** | Copy chart, update config | Learn all details |
| **Debugging** | Standardized patterns | Ad-hoc approaches |
| **Reproducibility** | Guaranteed via templates | Error-prone |

## Extensibility

### Adding New Endpoints

1. Add endpoint to `app/main.py`
2. Redeploy application (same Helm chart)

### Adding New Features

1. Scaling: Modify `values.yaml`
2. Resources: Update `resources` section
3. Environment: Create `values-{env}.yaml`

### Adding New Services

1. Copy helm chart directory
2. Update `Chart.yaml`
3. Modify `values.yaml` for service
4. Deploy same way as employee-api

---
## Ingress Routing Architecture

### Hostname-Based Routing
- Single Ingress object routes to service
- Hostname: employee.local (configurable)
- Supports multiple paths for different endpoints

### Path-Based Routing (Enhanced)
- `/` → Main API endpoints
- `/health` → Health check (exact match)
- Future: `/api/v1/*` → Versioned endpoints

### Service Integration
- Ingress → Service (ClusterIP) → Pods
- Load balancing via Service
- DNS discovery inside cluster

### Traffic Flow Diagram
[Add ASCII diagram showing traffic flow]