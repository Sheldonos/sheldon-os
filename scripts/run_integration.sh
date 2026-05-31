#!/bin/bash
# Run integration tests with test environment

set -e

echo "======================================="
echo "Running Sheldon OS Integration Tests"
echo "======================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check dependencies
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose is not installed${NC}"
    exit 1
fi

if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    exit 1
fi

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Parse arguments
CLEANUP=true
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cleanup)
            CLEANUP=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Start test environment
echo -e "${BLUE}Starting test environment...${NC}"
docker-compose -f docker/docker-compose.test.yml up -d

# Wait for services to be ready
echo -e "${BLUE}Waiting for services to be ready...${NC}"
sleep 10

# Check if services are healthy
echo -e "${BLUE}Checking service health...${NC}"
docker-compose -f docker/docker-compose.test.yml ps

# Run integration tests
echo ""
echo -e "${YELLOW}Running integration tests...${NC}"
echo ""

PYTEST_CMD="pytest tests/integration/ --maxfail=1"

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v -s"
fi

eval $PYTEST_CMD
TEST_EXIT_CODE=$?

# Cleanup
if [ "$CLEANUP" = true ]; then
    echo ""
    echo -e "${BLUE}Cleaning up test environment...${NC}"
    docker-compose -f docker/docker-compose.test.yml down -v
fi

echo ""
echo "======================================="

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All integration tests passed!${NC}"
else
    echo -e "${RED}✗ Integration tests failed${NC}"
    
    if [ "$CLEANUP" = false ]; then
        echo ""
        echo "Test environment is still running for debugging"
        echo "View logs: docker-compose -f docker/docker-compose.test.yml logs"
        echo "Cleanup: docker-compose -f docker/docker-compose.test.yml down -v"
    fi
fi

echo "======================================="

exit $TEST_EXIT_CODE

# Made with Bob
