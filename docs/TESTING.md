# Sheldon OS Testing Guide

Comprehensive guide for testing Sheldon OS across all components and products.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Coverage Requirements](#coverage-requirements)
6. [CI/CD Integration](#cicd-integration)
7. [Performance Testing](#performance-testing)
8. [Security Testing](#security-testing)

## Testing Philosophy

### Core Principles

1. **Test Pyramid**: Focus on unit tests (70%), integration tests (20%), E2E tests (10%)
2. **Fast Feedback**: Unit tests should run in <1 second each
3. **Isolation**: Each test should be independent and repeatable
4. **Realistic Data**: Use production-like test data
5. **Error Cases**: Test failure scenarios as thoroughly as success cases

### Test Categories

```
tests/
├── unit/              # Fast, isolated component tests
├── integration/       # Cross-component interaction tests
├── performance/       # Load, stress, and scalability tests
├── security/          # Security and vulnerability tests
└── fixtures/          # Reusable test data and utilities
```

## Test Structure

### Directory Organization

```
sheldon-os/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Shared pytest configuration
│   │
│   ├── unit/                          # Unit tests
│   │   ├── test_core.py              # Core system tests
│   │   ├── test_agents.py            # Agent system tests
│   │   └── test_intelligence.py      # Intelligence module tests
│   │
│   ├── integration/                   # Integration tests
│   │   ├── test_core_integration.py
│   │   ├── test_intelligence_integration.py
│   │   ├── test_products_integration.py
│   │   └── test_end_to_end.py
│   │
│   ├── performance/                   # Performance tests
│   │   ├── test_load.py
│   │   ├── test_stress.py
│   │   └── test_scalability.py
│   │
│   ├── security/                      # Security tests
│   │   ├── test_authentication.py
│   │   ├── test_authorization.py
│   │   └── test_vulnerabilities.py
│   │
│   └── fixtures/                      # Test fixtures
│       ├── core_fixtures.py
│       ├── intelligence_fixtures.py
│       └── product_fixtures.py
```

### Test Naming Conventions

```python
# Unit tests
def test_<component>_<action>_<expected_result>():
    """Test that component performs action with expected result"""
    pass

# Integration tests
def test_<system1>_integrates_with_<system2>():
    """Test integration between system1 and system2"""
    pass

# Performance tests
def test_<scenario>_under_<load_condition>():
    """Test scenario performance under load condition"""
    pass
```

## Running Tests

### Quick Start

```bash
# Run all tests
./scripts/run_tests.sh

# Run with verbose output
./scripts/run_tests.sh -v

# Run specific test markers
./scripts/run_tests.sh -m "not slow"

# Run without coverage
./scripts/run_tests.sh --no-coverage

# Fail fast (stop on first failure)
./scripts/run_tests.sh --failfast
```

### Unit Tests

```bash
# Run all unit tests
pytest tests/ --ignore=tests/integration --ignore=tests/performance

# Run specific test file
pytest tests/test_core.py -v

# Run specific test
pytest tests/test_core.py::test_orchestrator_creates_agent -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Integration Tests

```bash
# Run integration tests (requires Docker)
./scripts/run_integration.sh

# Run without cleanup (for debugging)
./scripts/run_integration.sh --no-cleanup

# Run specific integration test
pytest tests/integration/test_core_integration.py -v
```

### Performance Tests

```bash
# Run performance tests
./scripts/run_performance.sh

# Run light load tests only
pytest tests/performance/ -m "not heavy"

# Run with benchmarking
pytest tests/performance/ --benchmark-only
```

### Security Tests

```bash
# Run security tests
pytest tests/security/ -v

# Run security scan
bandit -r src/ -f json -o bandit-report.json

# Check dependencies
safety check --json
```

## Writing Tests

### Unit Test Example

```python
import pytest
from src.core.orchestrator import Orchestrator

class TestOrchestrator:
    """Test Orchestrator functionality"""
    
    @pytest.fixture
    def orchestrator(self, config):
        """Create orchestrator instance"""
        return Orchestrator(config=config)
    
    def test_creates_agent_successfully(self, orchestrator):
        """Test that orchestrator creates agent"""
        # Arrange
        agent_type = "research"
        config = {"name": "test_agent"}
        
        # Act
        agent_id = orchestrator.create_agent(
            agent_type=agent_type,
            config=config
        )
        
        # Assert
        assert agent_id is not None
        assert orchestrator.get_agent(agent_id) is not None
    
    def test_handles_invalid_agent_type(self, orchestrator):
        """Test that orchestrator handles invalid agent type"""
        # Arrange
        invalid_type = "nonexistent"
        
        # Act & Assert
        with pytest.raises(ValueError):
            orchestrator.create_agent(
                agent_type=invalid_type,
                config={}
            )
```

### Integration Test Example

```python
import pytest
import asyncio

class TestOrchestratorMemoryIntegration:
    """Test Orchestrator + Memory System integration"""
    
    @pytest.mark.asyncio
    async def test_orchestrator_stores_agent_memory(
        self, orchestrator, memory_system
    ):
        """Test that orchestrator stores agent interactions"""
        # Create agent
        agent_id = await orchestrator.create_agent(
            agent_type="research",
            config={"name": "test"}
        )
        
        # Execute task
        result = await orchestrator.execute_task(
            agent_id=agent_id,
            task="Test task"
        )
        
        # Verify memory stored
        memories = await memory_system.retrieve_memories(
            agent_id=agent_id,
            memory_type="task_execution"
        )
        
        assert len(memories) > 0
        assert memories[0]["task"] == "Test task"
```

### Performance Test Example

```python
import pytest
import time

class TestLoadPerformance:
    """Test system performance under load"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_handles_1000_concurrent_users(self, orchestrator):
        """Test 1,000 concurrent users"""
        async def simulate_user():
            start = time.time()
            agent_id = await orchestrator.create_agent(
                agent_type="test",
                config={}
            )
            await orchestrator.execute_task(agent_id, "Task")
            await orchestrator.terminate_agent(agent_id)
            return time.time() - start
        
        # Run 1,000 concurrent users
        results = await asyncio.gather(*[
            simulate_user() for _ in range(1000)
        ])
        
        # Assert performance targets
        avg_time = sum(results) / len(results)
        assert avg_time < 1.0  # <1s average
        assert max(results) < 5.0  # <5s max
```

## Coverage Requirements

### Target Coverage

- **Overall**: 80%+ coverage
- **Core Systems**: 90%+ coverage
- **Intelligence Modules**: 85%+ coverage
- **Product Models**: 80%+ coverage
- **Integration Points**: 100% coverage

### Measuring Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Check coverage threshold
coverage report --fail-under=80
```

### Coverage Configuration

```ini
# pytest.ini
[tool:pytest]
addopts = 
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80

[coverage:run]
source = src
omit = 
    */tests/*
    */migrations/*
    */__pycache__/*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

## CI/CD Integration

### GitHub Actions Workflow

Tests run automatically on:
- **Push** to main/develop branches
- **Pull Requests** to main/develop
- **Daily** at 2 AM UTC (scheduled)

### Workflow Jobs

1. **Unit Tests**: Run on Python 3.10, 3.11, 3.12
2. **Integration Tests**: Run with PostgreSQL + Redis
3. **Performance Tests**: Run on main branch only
4. **Security Tests**: Bandit + Safety checks
5. **Code Quality**: Black, Flake8, MyPy, Pylint

### Status Badges

Add to README.md:

```markdown
![Tests](https://github.com/your-org/sheldon-os/workflows/Test%20Suite/badge.svg)
![Coverage](https://codecov.io/gh/your-org/sheldon-os/branch/main/graph/badge.svg)
```

## Performance Testing

### Load Test Scenarios

```python
# Light Load: 100 users
pytest tests/performance/test_load.py::TestLightLoad -v

# Medium Load: 1,000 users
pytest tests/performance/test_load.py::TestMediumLoad -v

# Heavy Load: 10,000 users
pytest tests/performance/test_load.py::TestHeavyLoad -v -m heavy

# Sustained Load: 1 hour
pytest tests/performance/test_load.py::TestSustainedLoad -v -m sustained
```

### Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| API Response (p95) | <200ms | <500ms |
| Database Query (p95) | <50ms | <100ms |
| Memory Usage | <2GB | <4GB |
| CPU Usage | <70% | <90% |
| Error Rate | <0.1% | <1% |
| Throughput | >1000 req/s | >500 req/s |

### Benchmarking

```bash
# Run benchmarks
pytest tests/performance/ --benchmark-only

# Compare benchmarks
pytest-benchmark compare
```

## Security Testing

### Security Scan Tools

```bash
# Bandit: Python security linter
bandit -r src/ -f json -o bandit-report.json

# Safety: Dependency vulnerability checker
safety check --json --output safety-report.json

# OWASP Dependency Check
dependency-check --project sheldon-os --scan .
```

### Security Test Categories

1. **Authentication**: Password strength, token expiration, MFA
2. **Authorization**: RBAC, permission boundaries, privilege escalation
3. **Vulnerabilities**: SQL injection, XSS, CSRF, API security
4. **Data Protection**: Encryption, PII handling, secure storage

### Security Checklist

- [ ] All passwords hashed with bcrypt
- [ ] API keys encrypted at rest
- [ ] HTTPS enforced in production
- [ ] Rate limiting on all endpoints
- [ ] Input validation on all user data
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] CSRF tokens on state-changing operations
- [ ] Secure session management
- [ ] Regular dependency updates

## Best Practices

### DO ✅

- Write tests before fixing bugs (TDD)
- Use descriptive test names
- Test one thing per test
- Use fixtures for common setup
- Mock external dependencies
- Test error cases
- Keep tests fast (<1s for unit tests)
- Use parametrize for similar tests
- Document complex test scenarios

### DON'T ❌

- Test implementation details
- Use sleep() for timing
- Share state between tests
- Ignore flaky tests
- Skip writing tests for "simple" code
- Test framework code
- Use production data in tests
- Commit commented-out tests

## Troubleshooting

### Common Issues

**Tests fail locally but pass in CI:**
- Check Python version compatibility
- Verify environment variables
- Check for timezone issues
- Review file path differences

**Flaky tests:**
- Add retries for network operations
- Use proper async/await patterns
- Avoid race conditions
- Mock time-dependent code

**Slow tests:**
- Use pytest-xdist for parallel execution
- Mock expensive operations
- Use in-memory databases
- Optimize test fixtures

**Coverage gaps:**
- Review coverage report
- Add tests for uncovered branches
- Test error handling paths
- Add integration tests

## Resources

### Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

### Tools
- [pytest](https://pytest.org/) - Testing framework
- [pytest-cov](https://pytest-cov.readthedocs.io/) - Coverage plugin
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) - Async support
- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/) - Benchmarking
- [locust](https://locust.io/) - Load testing
- [bandit](https://bandit.readthedocs.io/) - Security linting
- [safety](https://pyup.io/safety/) - Dependency checking

## Support

For testing questions or issues:
- Create an issue on GitHub
- Contact the testing team
- Review test examples in `/tests/`
- Check CI/CD logs for failures

---

**Last Updated**: 2024-01-15
**Version**: 1.0.0