#!/bin/bash

# CogniVerve-AI Deployment Script
# This script deploys CogniVerve-AI to various cloud providers

set -e

# Configuration
PROJECT_NAME="cogniverve-ai"
BACKEND_IMAGE="cogniverve/backend"
FRONTEND_IMAGE="cogniverve/frontend"
VERSION=${1:-"latest"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    if ! command -v kubectl &> /dev/null; then
        warn "kubectl is not installed - Kubernetes deployment will not be available"
    fi
    
    if ! command -v terraform &> /dev/null; then
        warn "Terraform is not installed - Infrastructure provisioning will not be available"
    fi
    
    log "Dependencies check completed"
}

# Build Docker images
build_images() {
    log "Building Docker images..."
    
    # Build backend image
    log "Building backend image..."
    docker build -t ${BACKEND_IMAGE}:${VERSION} ./backend
    
    # Build frontend image
    log "Building frontend image..."
    docker build -t ${FRONTEND_IMAGE}:${VERSION} ./frontend
    
    log "Docker images built successfully"
}

# Deploy to local Docker Compose
deploy_local() {
    log "Deploying to local Docker Compose..."
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        log "Creating .env file..."
        cat > .env << EOF
# Database
DATABASE_URL=postgresql://cogniverve:cogniverve123@postgres:5432/cogniverve_db
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1

# Frontend
VITE_API_URL=http://localhost:8000
EOF
    fi
    
    # Start services
    docker-compose up -d
    
    log "Local deployment completed"
    log "Frontend: http://localhost:3000"
    log "Backend API: http://localhost:8000"
    log "API Docs: http://localhost:8000/docs"
}

# Deploy to Kubernetes
deploy_k8s() {
    log "Deploying to Kubernetes..."
    
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is required for Kubernetes deployment"
    fi
    
    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
    fi
    
    # Create namespace if it doesn't exist
    kubectl create namespace cogniverve --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply infrastructure components
    log "Deploying infrastructure components..."
    kubectl apply -f k8s/infrastructure.yaml -n cogniverve
    
    # Wait for database to be ready
    log "Waiting for database to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres -n cogniverve --timeout=300s
    
    # Apply application components
    log "Deploying application components..."
    kubectl apply -f k8s/deployment.yaml -n cogniverve
    
    # Wait for deployments to be ready
    log "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available deployment/cogniverve-backend -n cogniverve --timeout=300s
    kubectl wait --for=condition=available deployment/cogniverve-frontend -n cogniverve --timeout=300s
    
    log "Kubernetes deployment completed"
    
    # Get service URLs
    log "Getting service information..."
    kubectl get services -n cogniverve
    kubectl get ingress -n cogniverve
}

# Deploy to AWS ECS
deploy_aws() {
    log "Deploying to AWS ECS..."
    
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is required for AWS deployment"
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured"
    fi
    
    # Deploy using Terraform
    if command -v terraform &> /dev/null; then
        log "Using Terraform for AWS infrastructure..."
        cd terraform/aws
        terraform init
        terraform plan
        terraform apply -auto-approve
        cd ../..
    else
        warn "Terraform not available - manual AWS setup required"
    fi
    
    log "AWS deployment completed"
}

# Deploy to Google Cloud Run
deploy_gcp() {
    log "Deploying to Google Cloud Run..."
    
    if ! command -v gcloud &> /dev/null; then
        error "Google Cloud SDK is required for GCP deployment"
    fi
    
    # Check GCP authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 &> /dev/null; then
        error "Not authenticated with Google Cloud"
    fi
    
    PROJECT_ID=$(gcloud config get-value project)
    if [ -z "$PROJECT_ID" ]; then
        error "No GCP project configured"
    fi
    
    log "Deploying to project: $PROJECT_ID"
    
    # Build and push images to Google Container Registry
    log "Building and pushing images..."
    docker tag ${BACKEND_IMAGE}:${VERSION} gcr.io/${PROJECT_ID}/${BACKEND_IMAGE}:${VERSION}
    docker tag ${FRONTEND_IMAGE}:${VERSION} gcr.io/${PROJECT_ID}/${FRONTEND_IMAGE}:${VERSION}
    
    docker push gcr.io/${PROJECT_ID}/${BACKEND_IMAGE}:${VERSION}
    docker push gcr.io/${PROJECT_ID}/${FRONTEND_IMAGE}:${VERSION}
    
    # Deploy to Cloud Run
    log "Deploying backend to Cloud Run..."
    gcloud run deploy cogniverve-backend \
        --image gcr.io/${PROJECT_ID}/${BACKEND_IMAGE}:${VERSION} \
        --platform managed \
        --region us-central1 \
        --allow-unauthenticated \
        --set-env-vars="ENVIRONMENT=production"
    
    log "Deploying frontend to Cloud Run..."
    gcloud run deploy cogniverve-frontend \
        --image gcr.io/${PROJECT_ID}/${FRONTEND_IMAGE}:${VERSION} \
        --platform managed \
        --region us-central1 \
        --allow-unauthenticated
    
    log "GCP deployment completed"
}

# Health check
health_check() {
    log "Performing health check..."
    
    local backend_url=${1:-"http://localhost:8000"}
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f "${backend_url}/health" &> /dev/null; then
            log "Health check passed"
            return 0
        fi
        
        log "Health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 10
        ((attempt++))
    done
    
    error "Health check failed after $max_attempts attempts"
}

# Cleanup
cleanup() {
    log "Cleaning up..."
    
    case ${1:-"local"} in
        "local")
            docker-compose down
            ;;
        "k8s")
            kubectl delete namespace cogniverve
            ;;
        *)
            warn "Unknown cleanup target: $1"
            ;;
    esac
    
    log "Cleanup completed"
}

# Main deployment function
main() {
    local deployment_target=${1:-"local"}
    local action=${2:-"deploy"}
    
    log "CogniVerve-AI Deployment Script"
    log "Target: $deployment_target"
    log "Action: $action"
    log "Version: $VERSION"
    
    case $action in
        "deploy")
            check_dependencies
            
            case $deployment_target in
                "local")
                    build_images
                    deploy_local
                    health_check
                    ;;
                "k8s"|"kubernetes")
                    build_images
                    deploy_k8s
                    ;;
                "aws")
                    build_images
                    deploy_aws
                    ;;
                "gcp")
                    build_images
                    deploy_gcp
                    ;;
                *)
                    error "Unknown deployment target: $deployment_target"
                    ;;
            esac
            ;;
        "cleanup")
            cleanup $deployment_target
            ;;
        "health")
            health_check ${3:-"http://localhost:8000"}
            ;;
        *)
            error "Unknown action: $action"
            ;;
    esac
    
    log "Deployment script completed successfully"
}

# Show usage
usage() {
    echo "Usage: $0 [target] [action] [version]"
    echo ""
    echo "Targets:"
    echo "  local      Deploy using Docker Compose (default)"
    echo "  k8s        Deploy to Kubernetes cluster"
    echo "  aws        Deploy to AWS ECS"
    echo "  gcp        Deploy to Google Cloud Run"
    echo ""
    echo "Actions:"
    echo "  deploy     Deploy the application (default)"
    echo "  cleanup    Clean up deployment"
    echo "  health     Perform health check"
    echo ""
    echo "Examples:"
    echo "  $0                           # Deploy locally"
    echo "  $0 k8s deploy v1.0.0        # Deploy v1.0.0 to Kubernetes"
    echo "  $0 local cleanup            # Clean up local deployment"
    echo "  $0 aws health               # Health check AWS deployment"
}

# Handle command line arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    usage
    exit 0
fi

# Run main function
main "$@"

