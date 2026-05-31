#!/bin/bash
# Run all unit tests with coverage

set -e

echo "================================"
echo "Running Sheldon OS Test Suite"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install pytest pytest-cov pytest-asyncio"
    exit 1
fi

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Parse arguments
COVERAGE=true
VERBOSE=false
MARKERS=""
FAILFAST=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -m|--markers)
            MARKERS="$2"
            shift 2
            ;;
        --failfast)
            FAILFAST=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest tests/"

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=src --cov-report=html --cov-report=term"
fi

if [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD -m \"$MARKERS\""
fi

if [ "$FAILFAST" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --maxfail=1"
fi

# Run tests
echo -e "${YELLOW}Running: $PYTEST_CMD${NC}"
echo ""

eval $PYTEST_CMD
TEST_EXIT_CODE=$?

echo ""
echo "================================"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    
    if [ "$COVERAGE" = true ]; then
        echo ""
        echo "Coverage report generated at: htmlcov/index.html"
        echo "Open with: open htmlcov/index.html"
    fi
else
    echo -e "${RED}✗ Tests failed${NC}"
fi

echo "================================"

exit $TEST_EXIT_CODE

# Made with Bob
