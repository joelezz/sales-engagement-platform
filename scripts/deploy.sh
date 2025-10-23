#!/bin/bash

# Sales Engagement Platform Deployment Script
set -e

# Configuration
NAMESPACE="sales-engagement"
IMAGE_TAG=${1:-"latest"}
REGISTRY=${REGISTRY:-"your-registry.com"}
IMAGE_NAME="$REGISTRY/sales-engagement/api:$IMAGE_TAG"

echo "🚀 Starting deployment of Sales Engagement Platform"
echo "📦 Image: $IMAGE_NAME"
echo "🎯 Namespace: $NAMESPACE"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if we're connected to the cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Not connected to Kubernetes cluster"
    exit 1
fi

# Build and push Docker image
echo "🔨 Building Docker image..."
docker build -t $IMAGE_NAME .

echo "📤 Pushing Docker image..."
docker push $IMAGE_NAME

# Create namespace if it doesn't exist
echo "🏗️  Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Apply ConfigMap and Secrets
echo "⚙️  Applying configuration..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Apply database and Redis (if using managed services, skip this)
if [ "$DEPLOY_DATABASES" = "true" ]; then
    echo "🗄️  Deploying databases..."
    kubectl apply -f k8s/postgres.yaml
    kubectl apply -f k8s/redis.yaml
    
    # Wait for databases to be ready
    echo "⏳ Waiting for databases to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=300s
    kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=300s
fi

# Run database migrations
echo "🔄 Running database migrations..."
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: migration-$(date +%s)
  namespace: $NAMESPACE
spec:
  template:
    spec:
      containers:
      - name: migration
        image: $IMAGE_NAME
        command: ["alembic", "upgrade", "head"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: sales-engagement-secrets
              key: DATABASE_URL
      restartPolicy: Never
  backoffLimit: 3
EOF

# Apply services
echo "🌐 Applying services..."
kubectl apply -f k8s/service.yaml

# Apply deployments
echo "🚀 Applying deployments..."
kubectl apply -f k8s/deployment.yaml

# Apply HPA
echo "📈 Applying auto-scaling..."
kubectl apply -f k8s/hpa.yaml

# Apply ingress
echo "🌍 Applying ingress..."
kubectl apply -f k8s/ingress.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/sales-engagement-api -n $NAMESPACE --timeout=600s
kubectl rollout status deployment/sales-engagement-celery -n $NAMESPACE --timeout=600s

# Verify deployment
echo "✅ Verifying deployment..."
kubectl get pods -n $NAMESPACE
kubectl get services -n $NAMESPACE
kubectl get ingress -n $NAMESPACE

# Run health check
echo "🏥 Running health check..."
API_URL=$(kubectl get ingress sales-engagement-ingress -n $NAMESPACE -o jsonpath='{.spec.rules[0].host}')
if curl -f "https://$API_URL/health" > /dev/null 2>&1; then
    echo "✅ Health check passed!"
else
    echo "⚠️  Health check failed. Check the logs:"
    kubectl logs -l app=sales-engagement-api -n $NAMESPACE --tail=50
fi

echo "🎉 Deployment completed successfully!"
echo "🌐 API URL: https://$API_URL"
echo "📚 Documentation: https://$API_URL/docs"

# Show useful commands
echo ""
echo "📋 Useful commands:"
echo "  View logs: kubectl logs -f -l app=sales-engagement-api -n $NAMESPACE"
echo "  Scale up: kubectl scale deployment sales-engagement-api --replicas=5 -n $NAMESPACE"
echo "  Port forward: kubectl port-forward svc/sales-engagement-api-service 8000:80 -n $NAMESPACE"
echo "  Delete deployment: kubectl delete namespace $NAMESPACE"