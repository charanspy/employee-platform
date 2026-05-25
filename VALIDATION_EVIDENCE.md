# Validation Evidence Guide

This document describes the expected output and evidence for each deployment validation step.

---

## 📸 Expected Outputs & Validation Evidence

### 1. Docker Image Build Validation

#### Command:
```bash
eval $(minikube docker-env)
cd ~/employee-platform
docker build -t employee-api:v1 -f docker/Dockerfile .
```

#### Expected Output:
```
Sending build context to Docker daemon  XX.XXkB
Step 1/7 : FROM python:3.9-slim
 ---> abc123def456
Step 2/7 : WORKDIR /app
 ---> Running in def456abc123
Step 3/7 : COPY app/requirements.txt .
 ---> abc123def456
Step 4/7 : RUN pip install --no-cache-dir -r requirements.txt
 ---> Running in abc123def456
Collecting flask
Successfully installed flask-X.X.X
Step 5/7 : COPY app/ .
 ---> abc123def456
Step 6/7 : EXPOSE 5000
 ---> abc123def456
Step 7/7 : CMD ["python", "main.py"]
 ---> abc123def456
Successfully built abc123def456
Successfully tagged employee-api:v1
```

#### Verification:
```bash
docker images | grep employee-api
# REPOSITORY       TAG    IMAGE ID         CREATED          SIZE
# employee-api     v1     abc123def456     X minutes ago     156MB
```

 **Evidence Collected:** Image successfully built and stored in Minikube

---

### 2. Helm Chart Validation

#### Command:
```bash
helm lint ./helm/employee-api
```

#### Expected Output:
```
==> Linting ./helm/employee-api
[OK] no issues found
```

 **Evidence Collected:** Helm chart syntax is valid

---

### 3. Development Environment Deployment

#### Command:
```bash
helm install employee-dev \
  ./helm/employee-api \
  -f helm/employee-api/values.yaml \
  -f helm/employee-api/values-dev.yaml \
  --namespace dev \
  --create-namespace
```

#### Expected Output:
```
NAME: employee-dev
LAST DEPLOYED: XXX XXX XX XX:XX:XX XXXX
NAMESPACE: dev
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
```

#### Verification:
```bash
kubectl get pods -n dev
```

Expected output:
```
NAME                                              READY  STATUS    RESTARTS  AGE
employee-dev-employee-api-xxxxx                  1/1    Running   0         XX
employee-dev-employee-api-yyyyy                  1/1    Running   0         XX
```

 **Evidence Collected:** Pods are running in dev namespace

---

### 4. ConfigMap Verification

#### Command:
```bash
kubectl describe configmap employee-dev-employee-api-config -n dev
```

#### Expected Output:
```
Name:         employee-dev-employee-api-config
Namespace:    dev
Labels:       app.kubernetes.io/managed-by=Helm
Annotations:  meta.helm.sh/release-name: employee-dev
              meta.helm.sh/release-namespace: dev

Data
====
ENV:
----
dev

TEAM:
----
platform

BinaryData
====

Events:  <none>
```

 **Evidence Collected:** Environment configuration is properly set

---

### 5. Service Verification

#### Command:
```bash
kubectl get svc -n dev
```

#### Expected Output:
```
NAME                          TYPE       CLUSTER-IP      EXTERNAL-IP  PORT(S)
employee-dev-employee-api     ClusterIP  10.96.XXX.XXX   <none>       80/TCP
kubernetes                    ClusterIP  10.96.0.1       <none>       443/TCP
```

 **Evidence Collected:** Service is created and listening on port 80

---

### 6. HPA Configuration Verification

#### Command:
```bash
kubectl get hpa -n dev
```

#### Expected Output:
```
NAME                       REFERENCE                              TARGETS         MINPODS  MAXPODS  REPLICAS  AGE
employee-dev-employee-api  Deployment/employee-dev-employee-api   0%/70%          2        5        2         XX
```

#### Detailed HPA Status:
```bash
kubectl describe hpa employee-dev-employee-api -n dev
```

Expected output showing:
```
Name:                                   employee-dev-employee-api
Namespace:                              dev
Labels:                                 app.kubernetes.io/managed-by=Helm
Annotations:                            meta.helm.sh/release-name: employee-dev
CreationTimestamp:                      XXX
Reference:                              Deployment/employee-dev-employee-api
Metrics:                                ( current / target )
  resource cpu on pods  (as a percentage of request):  0% (0) / 70%
Min replicas:                           2
Max replicas:                           5
Deployment pods:                        2 current / 2 desired
```

 **Evidence Collected:** HPA is configured with correct min/max replicas and CPU threshold

---

### 7. Ingress Configuration Verification

#### Command:
```bash
kubectl get ingress -n dev
```

#### Expected Output:
```
NAME                      CLASS   HOSTS              ADDRESS          PORTS  AGE
employee-dev-employee-api nginx   employee.local     10.96.XXX.XXX    80     XX
```

#### Detailed Ingress Configuration:
```bash
kubectl describe ingress -n dev
```

Expected output:
```
Name:             employee-dev-employee-api
Namespace:        dev
Address:          10.96.XXX.XXX
Ingress Class:    nginx
Default backend:  <default>
Rules:
  Host              Path  Backends
  ----              ----  --------
  employee.local    /     employee-dev-employee-api:80 (10.244.X.X:5000)
Annotations:        kubernetes.io/ingress.class: nginx
                    nginx.ingress.kubernetes.io/rewrite-target: /
```

 **Evidence Collected:** Ingress is properly configured with hostname and backend service

---

### 8. API Endpoint Testing

#### Setup Port Forward:
```bash
kubectl port-forward -n dev svc/employee-dev-employee-api 8080:80 &
```

#### Test Root Endpoint:
```bash
curl http://localhost:8080/
```

Expected output:
```json
{"app":"Employee API","env":"dev"}
```

#### Test Employees Endpoint:
```bash
curl http://localhost:8080/employees
```

Expected output:
```json
[{"id":1,"name":"Alice","department":"HR"},{"id":2,"name":"Bob","department":"IT"}]
```

#### Test Health Endpoint:
```bash
curl http://localhost:8080/health
```

Expected output:
```json
{"status":"healthy"}
```

#### Test Info Endpoint:
```bash
curl http://localhost:8080/info
```

Expected output:
```json
{"environment":"dev","team":"Platform Engineering","version":"1.0"}
```

 **Evidence Collected:** All API endpoints are responding correctly with expected data

---

### 9. Staging Environment Deployment

#### Command:
```bash
helm install employee-staging \
  ./helm/employee-api \
  -f helm/employee-api/values.yaml \
  -f helm/employee-api/values-staging.yaml \
  --namespace staging \
  --create-namespace
```

#### Expected Output:
```
NAME: employee-staging
LAST DEPLOYED: XXX XXX XX XX:XX:XX XXXX
NAMESPACE: staging
STATUS: deployed
REVISION: 1
```

#### Verification:
```bash
kubectl get pods -n staging
kubectl get hpa -n staging
```

Expected:
- 3 pods running (replicas: 3)
- HPA with 2-5 replicas target
- Ingress host: `employee-staging.local`

 **Evidence Collected:** Staging environment deployed with correct configuration

---

### 10. Production Environment Deployment

#### Command:
```bash
helm install employee-prod \
  ./helm/employee-api \
  -f helm/employee-api/values.yaml \
  -f helm/employee-api/values-prod.yaml \
  --namespace prod \
  --create-namespace
```

#### Expected Output:
```
NAME: employee-prod
LAST DEPLOYED: XXX XXX XX XX:XX:XX XXXX
NAMESPACE: prod
STATUS: deployed
REVISION: 1
```

#### Verification:
```bash
kubectl get pods -n prod
kubectl get hpa -n prod
```

Expected:
- 5 pods running (replicas: 5)
- HPA with 5-10 replicas target
- Ingress host: `employee-prod.local`

 **Evidence Collected:** Production environment deployed with correct high-availability configuration

---

### 11. Multi-Environment Ingress Verification

#### Command:
```bash
kubectl get ingress -A
```

Expected output showing all three environments with unique hostnames:
```
NAMESPACE  NAME                      CLASS  HOSTS                    ADDRESS         PORTS  AGE
dev        employee-dev-employee-api nginx  employee.local           10.96.XXX.XXX   80     XX
staging    employee-staging-employee-api nginx  employee-staging.local 10.96.YYY.YYY   80     XX
prod       employee-prod-employee-api nginx  employee-prod.local     10.96.ZZZ.ZZZ   80     XX
```

 **Evidence Collected:** No ingress conflicts - unique hostnames per environment

---

### 12. Pod Logs Verification

#### Command:
```bash
kubectl logs -n dev deployment/employee-dev-employee-api
```

Expected output showing Flask startup:
```
 * Running on http://0.0.0.0:5000
 * Debug mode: off
```

 **Evidence Collected:** Application is running correctly with Flask server active

---

### 13. Helm Release Status

#### Command:
```bash
helm list -A
```

Expected output:
```
NAME              NAMESPACE  STATUS  CHART          VERSION
employee-dev      dev        deployed  employee-api-0.1.0  1
employee-staging  staging    deployed  employee-api-0.1.0  1
employee-prod     prod       deployed  employee-api-0.1.0  1
```

 **Evidence Collected:** All three Helm releases are deployed and active

---

### 14. Template Rendering Verification

#### Command:
```bash
helm template employee-dev ./helm/employee-api \
  -f helm/employee-api/values.yaml \
  -f helm/employee-api/values-dev.yaml | head -50
```

Expected output showing rendered Kubernetes manifests (YAML) without errors.

**Evidence Collected:** Helm templates render correctly with configuration merging

---

### 15. Autoscaling Behavior (Optional - Load Testing)

#### Watch Autoscaling:
```bash
kubectl get hpa -n dev -w
```

#### Generate Load (in another terminal):
```bash
kubectl run -it --rm load-generator --image=busybox /bin/sh

# Inside the pod:
while sleep 0.01; do wget -q -O- http://employee-dev-employee-api/; done
```

#### Expected Output:
HPA should show increasing CPU utilization and scaling up replicas:
```
NAME                       REFERENCE                              TARGETS         MINPODS  MAXPODS  REPLICAS  AGE
employee-dev-employee-api  Deployment/employee-dev-employee-api   5%/70%          2        5        2         XX
employee-dev-employee-api  Deployment/employee-dev-employee-api   45%/70%         2        5        3         XX
employee-dev-employee-api  Deployment/employee-dev-employee-api   68%/70%         2        5        4         XX
employee-dev-employee-api  Deployment/employee-dev-employee-api   25%/70%         2        5        4         XX
```

 **Evidence Collected:** Autoscaling responds to CPU load and scales pods dynamically

---

## 📋 Complete Validation Checklist

Use this checklist to track all evidence collected:

- [ ] Docker image built successfully
- [ ] Helm chart validates without errors
- [ ] Development environment deployed with 2 pods
- [ ] Staging environment deployed with 3 pods
- [ ] Production environment deployed with 5 pods
- [ ] ConfigMap contains correct environment variables
- [ ] Service is accessible
- [ ] HPA configured with correct min/max replicas
- [ ] All three ingress resources created with unique hostnames
- [ ] Root endpoint returns correct data
- [ ] Employees endpoint returns employee list
- [ ] Health endpoint returns healthy status
- [ ] Info endpoint returns environment details
- [ ] All three Helm releases are active
- [ ] Pod logs show Flask server running
- [ ] Ingress routing works correctly
- [ ] Autoscaling responds to load (optional)

---

## 📊 Evidence Summary Template

When submitting validation evidence, include:

1. **Docker Build Evidence**
   - Screenshot of `docker build` successful completion
   - Screenshot of `docker images | grep employee-api`

2. **Helm Validation Evidence**
   - Output of `helm lint ./helm/employee-api`
   - Output of `helm template` showing rendered manifests

3. **Deployment Evidence**
   - Screenshots of `kubectl get pods -n dev/staging/prod`
   - Screenshots of `helm list -A` showing all releases

4. **Configuration Evidence**
   - Output of `kubectl describe configmap` for each environment
   - Output of `kubectl get ingress -A` showing unique hostnames

5. **API Endpoint Evidence**
   - curl output for all four endpoints (/, /employees, /health, /info)
   - Port-forward and connection screenshot

6. **Autoscaling Evidence** (Optional)
   - Screenshot of `kubectl get hpa -n dev -w` showing scaling activity
   - Pod count increasing under load

---

##  Validation Complete

Once all checkpoints have been verified and evidence collected, your Platform Engineering Golden Path implementation is complete and ready for production deployment.
