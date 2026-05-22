# Detailed Deployment Guide

This document provides comprehensive step-by-step instructions for deploying the Employee Management API using the Golden Path framework.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Build & Push](#docker-build--push)
4. [Helm Deployment](#helm-deployment)
5. [Validation & Testing](#validation--testing)
6. [Production Deployment](#production-deployment)
7. [Monitoring & Troubleshooting](#monitoring--troubleshooting)

## Prerequisites

### Required Software

```bash
# Docker (version 20.10+)
docker --version

# kubectl (version 1.20+)
kubectl version --client

# Helm (version 3.0+)
helm version

# Minikube (version 1.20+, for local development)
minikube version
```

### System Requirements

- **CPU:** Minimum 2 cores (4 cores recommended)
- **Memory:** Minimum 4GB (8GB recommended)
- **Disk Space:** Minimum 20GB available
- **Internet:** Required for pulling images

### Docker Hub Account

Create a free account at https://hub.docker.com/ for pushing container images.

## Environment Setup

### Step 1: Start Kubernetes Cluster

```bash
# Start Minikube cluster with recommended settings
minikube start \
  --cpus=4 \
  --memory=8192 \
  --vm-driver=docker \
  --kubernetes-version=v1.24.0

# Expected output showing:
# 😄  minikube v1.26.0 on Docker 20.10.17
# ✅  Cluster is starting
# 🎉  minikube profile was successfully created
```

### Step 2: Verify Cluster Access

```bash
# Check cluster information
kubectl cluster-info

# Check node status
kubectl get nodes

# Expected output:
# NAME       STATUS   ROLES           AGE   VERSION
# minikube   Ready    control-plane   1m    v1.24.0
```

### Step 3: Enable Required Addons

```bash
# Enable Ingress addon for routing
minikube addons enable ingress

# Enable metrics-server for Horizontal Pod Autoscaler
minikube addons enable metrics-server

# Verify addons
minikube addons list | grep -E "ingress|metrics-server"
```

### Step 4: Create Namespaces

```bash
# Create namespaces for different environments
kubectl create namespace dev
kubectl create namespace staging
kubectl create namespace prod

# Verify namespaces created
kubectl get namespaces

# Output:
# NAME              STATUS   AGE
# default           Active   5m
# dev               Active   1m
# ingress-nginx     Active   2m
# kube-system       Active   5m
# prod              Active   1m
# staging           Active   1m
```

## Docker Build & Push

### Step 1: Build Docker Image

```bash
# Navigate to repository root
cd employee-platform

# Build Docker image
docker build \
  -t your-dockerhub-username/employee-api:v1 \
  -f docker/Dockerfile \
  .

# Expected output showing successful build with image ID

# Verify image was created
docker images | grep employee-api

# Output:
# REPOSITORY                              TAG   IMAGE ID       CREATED        SIZE
# your-dockerhub-username/employee-api   v1    abc123def456   10 seconds ago 156MB
```

### Step 2: Test Docker Image Locally

```bash
# Run container in background
docker run \
  -d \
  -p 5000:5000 \
  -e ENV=dev \
  -e TEAM=platform \
  --name employee-api-test \
  your-dockerhub-username/employee-api:v1

# Test endpoints in another terminal
curl http://localhost:5000/
# Expected: {"app": "Employee API", "env": "dev"}

curl http://localhost:5000/employees
# Expected: [{"id": 1, "name": "Alice", "department": "HR"}, ...]

curl http://localhost:5000/health
# Expected: {"status": "healthy"}

curl http://localhost:5000/info
# Expected: {"environment": "dev", "team": "Platform Engineering", "version": "1.0"}

# Stop test container
docker stop employee-api-test
docker rm employee-api-test
```

### Step 3: Push Image to Docker Hub

```bash
# Login to Docker Hub
docker login

# Prompts for credentials - enter your Docker Hub username and password

# Push image to registry
docker push your-dockerhub-username/employee-api:v1

# Expected: Layers pushed successfully

# Verify push successful
docker search your-dockerhub-username/employee-api
```

### Step 4: Update Helm Chart Values

Edit `helm/employee-api/values.yaml` and update the image repository:

```yaml
image:
  repository: your-dockerhub-username/employee-api
  tag: v1
```

## Helm Deployment

### Step 1: Validate Helm Chart

```bash
# Check chart for syntax errors
helm lint ./helm/employee-api

# Expected output:
# ==> Linting ./helm/employee-api
# [OK] no issues found

# Generate manifests to preview what will be deployed
helm template employee-dev \
  ./helm/employee-api \
  -f helm/employee-api/values.yaml \
  -f helm/employee-api/values-dev.yaml

# Review the output manifests for accuracy
```

### Step 2: Deploy Development Environment

```bash
# Install Helm release
helm install employee-dev \
  ./helm/employee-api \
  -f helm/employee-api/values.yaml \
  -f helm/employee-api/values-dev.yaml \
  --namespace dev \
  --create-namespace

# Expected output:
# NAME: employee-dev
# LAST DEPLOYED: Thu May 22 10:30:00 2026
# NAMESPACE: dev
# STATUS: deployed
# REVISION: 1

# Verify installation
helm list -n dev

# Output should show:
# NAME           NAMESPACE STATUS  CHART              VERSION
# employee-dev   dev       deployed employee-api-0.1.0 1
```

### Step 3: Deploy Staging Environment

```bash
# Install to staging namespace with staging config
helm install employee-staging \
  ./helm/employee-api \
  -f helm/employee-api/values.yaml \
  -f helm/employee-api/values-staging.yaml \
  --namespace staging \
  --create-namespace
```

### Step 4: Deploy Production Environment

```bash
# Install to production namespace with production config
helm install employee-prod \
  ./helm/employee-api \
  -f helm/employee-api/values.yaml \
  -f helm/employee-api/values-prod.yaml \
  --namespace prod \
  --create-namespace
```

## Validation & Testing

### Step 1: Verify Deployments

```bash
# Check all resources in development namespace
kubectl get all -n dev

# Expected output showing:
# - Pod(s) in Running state
# - Service with ClusterIP
# - Deployment with desired replicas
# - ReplicaSet managing pods

# Check pods specifically
kubectl get pods -n dev

# Output:
# NAME                                      READY   STATUS    RESTARTS   AGE
# employee-dev-employee-api-xxxxx           1/1     Running   0          2m
```

### Step 2: Check Pod Logs

```bash
# View deployment logs
kubectl logs -n dev deployment/employee-dev-employee-api

# Expected output showing Flask startup:
# * Running on http://0.0.0.0:5000

# Follow logs in real-time
kubectl logs -n dev deployment/employee-dev-employee-api -f

# View previous logs if pod restarted
kubectl logs -n dev deployment/employee-dev-employee-api --previous
```

### Step 3: Verify ConfigMap

```bash
# List ConfigMaps
kubectl get configmap -n dev

# View ConfigMap content
kubectl describe configmap employee-dev-employee-api-config -n dev

# Output should show:
# Data
# ====
# ENV:  dev
# TEAM: platform
```

### Step 4: Check HPA Status

```bash
# List HPA resources
kubectl get hpa -n dev

# Output:
# NAME                         REFERENCE                        TARGETS     MINPODS MAXPODS REPLICAS AGE
# employee-dev-employee-api   Deployment/employee-dev-employee-api  0%/70%  2      5       2        1m

# Get detailed HPA information
kubectl describe hpa employee-dev-employee-api -n dev

# Expected: minReplicas: 2, maxReplicas: 5, cpuUtilization: 70%
```

### Step 5: Port Forward & Test API

```bash
# Port forward service to localhost
kubectl port-forward -n dev svc/employee-dev-employee-api 8080:80 &

# Test all endpoints
echo "Testing Root Endpoint:"
curl http://localhost:8080/

echo "Testing Employees Endpoint:"
curl http://localhost:8080/employees

echo "Testing Health Endpoint:"
curl http://localhost:8080/health

echo "Testing Info Endpoint:"
curl http://localhost:8080/info

# Stop port forwarding
pkill port-forward
```

### Step 6: Verify Ingress

```bash
# Get Minikube IP
MINIKUBE_IP=$(minikube ip)
echo "Minikube IP: $MINIKUBE_IP"

# Add hostname to /etc/hosts
echo "$MINIKUBE_IP employee.local" | sudo tee -a /etc/hosts

# Verify entry
cat /etc/hosts | grep employee.local

# Test via Ingress hostname
curl http://employee.local/employees

# Expected: Returns employee list
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] Docker image built and pushed to registry
- [ ] All Helm templates validated with `helm lint`
- [ ] Production values configured correctly
- [ ] Resource limits set appropriately
- [ ] HPA settings match expected load
- [ ] Ingress hostname configured
- [ ] Team notifications sent
- [ ] Backup of current state created

### Production Deployment Process

```bash
# Perform dry run first
helm install employee-prod \
  ./helm/employee-api \
  -f helm/employee-api/values.yaml \
  -f helm/employee-api/values-prod.yaml \
  --namespace prod \
  --create-namespace \
  --dry-run \
  --debug

# Review output carefully, then deploy
helm install employee-prod \
  ./helm/employee-api \
  -f helm/employee-api/values.yaml \
  -f helm/employee-api/values-prod.yaml \
  --namespace prod \
  --create-namespace

# Monitor rollout progress
kubectl rollout status deployment/employee-prod-employee-api -n prod --timeout=5m

# Watch logs during deployment
kubectl logs -n prod deployment/employee-prod-employee-api -f
```

### Post-Deployment Validation

```bash
# Verify all pods are running
kubectl get pods -n prod

# Check resource usage
kubectl top pods -n prod

# Run health checks
curl https://your-production-domain/health
curl https://your-production-domain/employees

# Monitor initial stability
sleep 60
kubectl get pods -n prod
kubectl top pods -n prod
```

## Upgrading Deployments

### Update Application Version

```bash
# Build new image with new tag
docker build -t your-dockerhub-username/employee-api:v2 .
docker push your-dockerhub-username/employee-api:v2

# Update values.yaml
# Change: tag: v1 → tag: v2

# Upgrade Helm release
helm upgrade employee-dev \
  ./helm/employee-api \
  -f helm/employee-api/values.yaml \
  -f helm/employee-api/values-dev.yaml \
  --namespace dev

# Monitor rolling update
kubectl rollout status deployment/employee-dev-employee-api -n dev

# View rollout history
kubectl rollout history deployment/employee-dev-employee-api -n dev

# Rollback if issues occur
kubectl rollout undo deployment/employee-dev-employee-api -n dev
```

## Monitoring & Troubleshooting

### Common Issues & Solutions

#### Issue: Pods Stuck in ImagePullBackOff

```bash
# Diagnosis
kubectl describe pod -n dev <pod-name>

# Look for: "Failed to pull image"

# Solution steps:
# 1. Verify image exists locally
docker pull your-dockerhub-username/employee-api:v1

# 2. Check image name in values.yaml
grep repository helm/employee-api/values.yaml

# 3. Ensure image is pushed
docker push your-dockerhub-username/employee-api:v1

# 4. Delete pod to trigger pull retry
kubectl delete pod -n dev <pod-name>
```

#### Issue: Pods Crash Immediately

```bash
# View pod status
kubectl describe pod -n dev <pod-name>

# Check logs from before crash
kubectl logs -n dev <pod-name> --previous

# Common causes:
# - Application error
# - Missing environment variables
# - Resource exhaustion

# Solution:
# 1. Fix application code
# 2. Verify ConfigMap has required variables
# 3. Increase resource limits
# 4. Redeploy
```

#### Issue: Service Not Accessible

```bash
# Check service exists
kubectl get svc -n dev

# Verify service has endpoints
kubectl get endpoints -n dev employee-dev-employee-api

# Test directly inside cluster
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
# Inside pod: wget -O- http://employee-dev-employee-api/health

# Port forward and test
kubectl port-forward -n dev svc/employee-dev-employee-api 8080:80
curl http://localhost:8080/health
```

#### Issue: HPA Not Scaling

```bash
# Check metrics server is running
kubectl get deployment metrics-server -n kube-system

# If not running:
minikube addons enable metrics-server

# Wait for metrics to become available (60 seconds)
sleep 60

# Check metrics now available
kubectl top pods -n dev

# Check HPA status
kubectl describe hpa -n dev employee-dev-employee-api

# If still not scaling, check if CPU threshold exceeded
kubectl top pods -n dev --containers
```

### Debug Commands

```bash
# Get detailed pod information (YAML)
kubectl get pods -n dev -o yaml

# Get resource details
kubectl describe deployment -n dev employee-dev-employee-api

# View all events (sorted by time)
kubectl get events -n dev --sort-by='.lastTimestamp'

# Execute command inside pod
kubectl exec -it <pod-name> -n dev -- /bin/bash

# Check resource requests/limits
kubectl describe node

# View persistent logs
kubectl logs <pod-name> -n dev --tail=100
```

### Performance Tuning

#### Adjust Resource Limits

Edit `helm/employee-api/values.yaml`:

```yaml
resources:
  requests:
    cpu: "200m"      # Minimum guaranteed CPU
    memory: "128Mi"   # Minimum guaranteed memory
  limits:
    cpu: "500m"      # Maximum CPU allowed
    memory: "256Mi"   # Maximum memory allowed
```

#### Adjust HPA Settings

Edit `helm/employee-api/values-prod.yaml`:

```yaml
autoscaling:
  minReplicas: 2              # Minimum pods always running
  maxReplicas: 10             # Maximum pods to scale to
  cpuUtilization: 70          # Scale when CPU > 70%
```

### Monitoring Commands

```bash
# Real-time CPU and memory usage
kubectl top pods -n dev

# Continuous monitoring (updates every 5 seconds)
watch -n 5 'kubectl top pods -n dev'

# Monitor node resources
kubectl top nodes

# Watch HPA scaling decisions
kubectl get hpa -n dev -w

# Monitor events in real-time
kubectl get events -n dev -w
```

## Helm Management

### List Releases

```bash
# List all releases in namespace
helm list -n dev

# List all releases across all namespaces
helm list -A
```

### View Release History

```bash
# See all revisions of a release
helm history employee-dev -n dev

# Get details of specific revision
helm status employee-dev -n dev
```

### Rollback to Previous Version

```bash
# Rollback to previous revision
helm rollback employee-dev -n dev

# Rollback to specific revision (e.g., revision 1)
helm rollback employee-dev 1 -n dev
```

### Uninstall Release

```bash
# Remove release (keeps namespace)
helm uninstall employee-dev -n dev

# Verify removal
helm list -n dev
```

## CI/CD Integration

### Validation Pipeline

```bash
#!/bin/bash
# Validate Helm chart
helm lint ./helm/employee-api || exit 1

# Test template generation
helm template employee-dev \
  ./helm/employee-api \
  -f helm/employee-api/values-dev.yaml > /tmp/manifest.yaml || exit 1

# Validate Kubernetes manifests (if kubeconform available)
kubeconform /tmp/manifest.yaml || exit 1

echo "✅ All validation checks passed"
```

### Automated Deployment

```bash
#!/bin/bash
# Deploy to development
helm upgrade --install employee-dev \
  ./helm/employee-api \
  -f helm/employee-api/values.yaml \
  -f helm/employee-api/values-dev.yaml \
  --namespace dev \
  --create-namespace

# Wait for rollout
kubectl rollout status deployment/employee-dev-employee-api -n dev --timeout=5m

echo "✅ Deployment successful"
```

---

**Last Updated:** May 2026  
**Version:** 1.0