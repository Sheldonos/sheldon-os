#!/bin/bash
set -e

# Sheldon OS Health Check Script
# Usage: ./health_check.sh [environment]

ENVIRONMENT=${1:-staging}
MAX_RETRIES=30
RETRY_DELAY=10

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Get API URL based on environment
get_api_url() {
    case "$ENVIRONMENT" in
        production)
            echo "https://api.sheldon-os.com"
            ;;
        staging)
            echo "https://api-staging.sheldon-os.com"
            ;;
        development)
            echo "http://localhost:8000"
            ;;
        *)
            log_error "Unknown environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
}

# Check HTTP endpoint
check_endpoint() {
    local url=$1
    local endpoint=$2
    local expected_status=${3:-200}
    
    log_info "Checking $endpoint..."
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url$endpoint" || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        log_success "$endpoint returned $response"
        return 0
    else
        log_error "$endpoint returned $response (expected $expected_status)"
        return 1
    fi
}

# Check health endpoint
check_health() {
    local url=$1
    
    for i in $(seq 1 $MAX_RETRIES); do
        log_info "Health check attempt $i/$MAX_RETRIES..."
        
        if check_endpoint "$url" "/health" 200; then
            return 0
        fi
        
        if [ $i -lt $MAX_RETRIES ]; then
            log_warning "Waiting $RETRY_DELAY seconds before retry..."
            sleep $RETRY_DELAY
        fi
    done
    
    log_error "Health check failed after $MAX_RETRIES attempts"
    return 1
}

# Check readiness endpoint
check_readiness() {
    local url=$1
    
    log_info "Checking readiness..."
    
    if check_endpoint "$url" "/ready" 200; then
        return 0
    else
        log_error "Readiness check failed"
        return 1
    fi
}

# Check metrics endpoint
check_metrics() {
    local url=$1
    
    log_info "Checking metrics endpoint..."
    
    if check_endpoint "$url" "/metrics" 200; then
        return 0
    else
        log_warning "Metrics endpoint check failed (non-critical)"
        return 0
    fi
}

# Check API version
check_version() {
    local url=$1
    
    log_info "Checking API version..."
    
    version=$(curl -s "$url/version" | jq -r '.version' 2>/dev/null || echo "unknown")
    
    if [ "$version" != "unknown" ]; then
        log_success "API version: $version"
        return 0
    else
        log_warning "Could not retrieve API version"
        return 0
    fi
}

# Check database connectivity
check_database() {
    local url=$1
    
    log_info "Checking database connectivity..."
    
    db_status=$(curl -s "$url/health" | jq -r '.database' 2>/dev/null || echo "unknown")
    
    if [ "$db_status" = "healthy" ]; then
        log_success "Database is healthy"
        return 0
    else
        log_error "Database check failed: $db_status"
        return 1
    fi
}

# Check Redis connectivity
check_redis() {
    local url=$1
    
    log_info "Checking Redis connectivity..."
    
    redis_status=$(curl -s "$url/health" | jq -r '.redis' 2>/dev/null || echo "unknown")
    
    if [ "$redis_status" = "healthy" ]; then
        log_success "Redis is healthy"
        return 0
    else
        log_error "Redis check failed: $redis_status"
        return 1
    fi
}

# Check response time
check_response_time() {
    local url=$1
    local max_time=2
    
    log_info "Checking response time..."
    
    response_time=$(curl -s -o /dev/null -w "%{time_total}" "$url/health")
    
    if (( $(echo "$response_time < $max_time" | bc -l) )); then
        log_success "Response time: ${response_time}s (threshold: ${max_time}s)"
        return 0
    else
        log_warning "Response time: ${response_time}s exceeds threshold of ${max_time}s"
        return 0
    fi
}

# Main health check flow
main() {
    log_info "🏥 Starting Sheldon OS health checks"
    log_info "Environment: $ENVIRONMENT"
    echo ""
    
    API_URL=$(get_api_url)
    log_info "API URL: $API_URL"
    echo ""
    
    # Run all checks
    FAILED=0
    
    check_health "$API_URL" || FAILED=$((FAILED + 1))
    check_readiness "$API_URL" || FAILED=$((FAILED + 1))
    check_metrics "$API_URL" || true
    check_version "$API_URL" || true
    check_database "$API_URL" || FAILED=$((FAILED + 1))
    check_redis "$API_URL" || FAILED=$((FAILED + 1))
    check_response_time "$API_URL" || true
    
    echo ""
    
    if [ $FAILED -eq 0 ]; then
        log_success "✅ All critical health checks passed!"
        exit 0
    else
        log_error "❌ $FAILED critical health check(s) failed"
        exit 1
    fi
}

# Run main
main

# Made with Bob
