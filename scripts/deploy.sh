#!/bin/bash
set -e

# Sheldon OS Deployment Script
# Usage: ./deploy.sh [environment] [version]

ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
validate_environment() {
    if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
        log_error "Invalid environment: $ENVIRONMENT"
        log_info "Valid environments: development, staging, production"
        exit 1
    fi
    log_success "Environment validated: $ENVIRONMENT"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check kustomize
    if ! command -v kustomize &> /dev/null; then
        log_warning "kustomize not found, using kubectl kustomize"
    fi
    
    log_success "All prerequisites met"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    
    cd "$PROJECT_ROOT"
    
    IMAGE_NAME="ghcr.io/sheldon-os/sheldon-os:$VERSION"
    
    docker build \
        -f docker/Dockerfile.prod \
        -t "$IMAGE_NAME" \
        --build-arg VERSION="$VERSION" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD)" \
        .
    
    log_success "Docker image built: $IMAGE_NAME"
}

# Push Docker image
push_image() {
    log_info "Pushing Docker image to registry..."
    
    IMAGE_NAME="ghcr.io/sheldon-os/sheldon-os:$VERSION"
    
    docker push "$IMAGE_NAME"
    
    log_success "Docker image pushed: $IMAGE_NAME"
}

# Update Kubernetes manifests
update_manifests() {
    log_info "Updating Kubernetes manifests..."
    
    cd "$PROJECT_ROOT/k8s/overlays/$ENVIRONMENT"
    
    # Update image tag
    kustomize edit set image "ghcr.io/sheldon-os/sheldon-os:$VERSION"
    
    log_success "Manifests updated with version: $VERSION"
}

# Deploy to Kubernetes
deploy_to_kubernetes() {
    log_info "Deploying to Kubernetes ($ENVIRONMENT)..."
    
    cd "$PROJECT_ROOT"
    
    # Apply manifests
    kubectl apply -k "k8s/overlays/$ENVIRONMENT"
    
    # Wait for rollout
    log_info "Waiting for rollout to complete..."
    kubectl rollout status deployment/sheldon-os -n sheldon-os --timeout=10m
    
    log_success "Deployment completed"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check pods
    log_info "Checking pods..."
    kubectl get pods -n sheldon-os
    
    # Check services
    log_info "Checking services..."
    kubectl get services -n sheldon-os
    
    # Check ingress
    log_info "Checking ingress..."
    kubectl get ingress -n sheldon-os
    
    log_success "Deployment verification complete"
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    if [ -f "$SCRIPT_DIR/health_check.sh" ]; then
        bash "$SCRIPT_DIR/health_check.sh" "$ENVIRONMENT"
    else
        log_warning "Health check script not found, skipping..."
    fi
}

# Run smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."
    
    if [ -f "$SCRIPT_DIR/smoke_tests.sh" ]; then
        bash "$SCRIPT_DIR/smoke_tests.sh" "$ENVIRONMENT"
    else
        log_warning "Smoke test script not found, skipping..."
    fi
}

# Rollback on failure
rollback() {
    log_error "Deployment failed, initiating rollback..."
    
    kubectl rollout undo deployment/sheldon-os -n sheldon-os
    kubectl rollout status deployment/sheldon-os -n sheldon-os
    
    log_success "Rollback completed"
    exit 1
}

# Main deployment flow
main() {
    log_info "🚀 Starting Sheldon OS deployment"
    log_info "Environment: $ENVIRONMENT"
    log_info "Version: $VERSION"
    echo ""
    
    # Validate and check
    validate_environment
    check_prerequisites
    
    # Build and push (skip for production if using CI/CD)
    if [ "$ENVIRONMENT" != "production" ]; then
        build_image
        push_image
    fi
    
    # Deploy
    update_manifests
    deploy_to_kubernetes || rollback
    
    # Verify
    verify_deployment
    run_health_checks
    run_smoke_tests
    
    echo ""
    log_success "✅ Deployment completed successfully!"
    log_info "Environment: $ENVIRONMENT"
    log_info "Version: $VERSION"
    log_info "Timestamp: $(date)"
}

# Trap errors
trap rollback ERR

# Run main
main

# Made with Bob
