## Quick Start

# Start Minikube
minikube start

# Enable Ingress
minikube addons enable ingress

# Build Docker image
docker build -t <your-dockerhub>/employee-api:v1 -f docker/Dockerfile .

# Push image
docker push <your-dockerhub>/employee-api:v1

# Deploy using Helm (Dev)
helm install employee ./helm/employee-api -f values-dev.yaml