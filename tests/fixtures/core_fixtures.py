"""
Core Component Test Fixtures

Provides fixtures for core system components.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock

import pytest

from src.agents.agent_factory import AgentFactory
from src.agents.agent_registry import AgentRegistry
from src.agents.lifecycle_manager import LifecycleManager
from src.core.config import Config
from src.core.context_manager import ContextManager
from src.core.memory_system import MemorySystem
from src.core.orchestrator import Orchestrator


@pytest.fixture
def config():
    """Test configuration"""
    return Config(
        environment="test",
        database_url="sqlite:///:memory:",
        redis_url="redis://localhost:6379/1",
        log_level="DEBUG",
        max_agents=100,
        memory_retention_days=30,
    )


@pytest.fixture
async def memory_system(config):
    """Configured memory system instance"""
    system = MemorySystem(config=config)
    system.context_manager = None
    await system.initialize()
    yield system
    await system.cleanup()


@pytest.fixture
async def context_manager(config, memory_system):
    """Context manager with test configuration"""
    manager = ContextManager(config=config)
    memory_system.context_manager = manager
    await manager.initialize()
    yield manager
    await manager.cleanup()


@pytest.fixture
async def lifecycle_manager(config):
    """Lifecycle manager for agent management"""
    manager = LifecycleManager(config=config)
    await manager.initialize()
    yield manager
    await manager.cleanup()


@pytest.fixture
async def agent_registry(config):
    """Agent registry for tracking agents"""
    registry = AgentRegistry(config=config)
    await registry.initialize()
    yield registry
    await registry.cleanup()


@pytest.fixture
async def agent_factory(config, agent_registry):
    """Agent factory for creating agents"""
    factory = AgentFactory(config=config, registry=agent_registry)
    await factory.initialize()
    yield factory
    await factory.cleanup()


@pytest.fixture
async def orchestrator(
    config,
    memory_system,
    context_manager,
    lifecycle_manager,
):
    """Fully configured orchestrator instance"""
    orch = Orchestrator(
        config=config,
        memory_system=memory_system,
        context_manager=context_manager,
        lifecycle_manager=lifecycle_manager,
    )
    memory_system.context_manager = context_manager
    await orch.initialize()
    yield orch
    await orch.cleanup()


@pytest.fixture
def test_agents():
    """Collection of test agent configurations"""
    return [
        {
            "id": "test_agent_1",
            "type": "research",
            "name": "Research Agent",
            "capabilities": ["web_search", "data_analysis"],
            "config": {"max_iterations": 10},
        },
        {
            "id": "test_agent_2",
            "type": "business",
            "name": "Business Agent",
            "capabilities": ["sales", "marketing", "finance"],
            "config": {"industry": "technology"},
        },
        {
            "id": "test_agent_3",
            "type": "analysis",
            "name": "Analysis Agent",
            "capabilities": ["pattern_recognition", "forecasting"],
            "config": {"model": "advanced"},
        },
    ]


@pytest.fixture
def sample_memories():
    """Sample memory data for testing"""
    return [
        {
            "agent_id": "test_agent_1",
            "memory_type": "short_term",
            "content": {"task": "Research AI trends", "result": "Completed"},
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "importance": 0.8,
            },
        },
        {
            "agent_id": "test_agent_1",
            "memory_type": "long_term",
            "content": {"knowledge": "AI market growing 40% annually"},
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "importance": 0.9,
                "verified": True,
            },
        },
        {
            "agent_id": "test_agent_2",
            "memory_type": "working",
            "content": {"current_task": "Lead qualification", "progress": 0.6},
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "importance": 0.7,
            },
        },
    ]


@pytest.fixture
def sample_contexts():
    """Sample context snapshots for testing"""
    return [
        {
            "agent_id": "test_agent_1",
            "snapshot_type": "checkpoint",
            "context": {
                "state": "active",
                "progress": 0.5,
                "data": {"items_processed": 50},
            },
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "trigger": "periodic",
            },
        },
        {
            "agent_id": "test_agent_2",
            "snapshot_type": "handoff",
            "context": {
                "from_agent": "test_agent_1",
                "to_agent": "test_agent_2",
                "data": {"research_results": ["finding1", "finding2"]},
            },
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "trigger": "delegation",
            },
        },
    ]


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    return {
        "content": "This is a test response from the LLM",
        "model": "test-model",
        "tokens": 150,
        "finish_reason": "stop",
        "metadata": {"temperature": 0.7, "max_tokens": 500},
    }


@pytest.fixture
async def populated_memory_system(memory_system, sample_memories):
    """Memory system pre-populated with test data"""
    for memory in sample_memories:
        await memory_system.store_memory(
            agent_id=memory["agent_id"],
            memory_type=memory["memory_type"],
            content=memory["content"],
            metadata=memory["metadata"],
        )
    return memory_system


@pytest.fixture
async def populated_context_manager(context_manager, sample_contexts):
    """Context manager pre-populated with snapshots"""
    for context in sample_contexts:
        await context_manager.create_snapshot(
            agent_id=context["agent_id"],
            context=context["context"],
            snapshot_type=context["snapshot_type"],
            metadata=context["metadata"],
        )
    return context_manager


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_database():
    """Mock database connection"""
    db = Mock()
    db.execute = AsyncMock(return_value={"rows": []})
    db.fetch_one = AsyncMock(return_value=None)
    db.fetch_all = AsyncMock(return_value=[])
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def mock_redis():
    """Mock Redis connection"""
    redis = Mock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.exists = AsyncMock(return_value=False)
    redis.expire = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def performance_metrics():
    """Performance metrics collector"""

    class MetricsCollector:
        def __init__(self):
            self.metrics = {
                "response_times": [],
                "memory_usage": [],
                "cpu_usage": [],
                "errors": [],
            }

        def record_response_time(self, duration: float):
            self.metrics["response_times"].append(duration)

        def record_memory_usage(self, bytes_used: int):
            self.metrics["memory_usage"].append(bytes_used)

        def record_cpu_usage(self, percentage: float):
            self.metrics["cpu_usage"].append(percentage)

        def record_error(self, error: str):
            self.metrics["errors"].append(error)

        def get_summary(self) -> Dict[str, Any]:
            return {
                "avg_response_time": (
                    sum(self.metrics["response_times"])
                    / len(self.metrics["response_times"])
                    if self.metrics["response_times"]
                    else 0
                ),
                "max_response_time": (
                    max(self.metrics["response_times"])
                    if self.metrics["response_times"]
                    else 0
                ),
                "avg_memory_usage": (
                    sum(self.metrics["memory_usage"])
                    / len(self.metrics["memory_usage"])
                    if self.metrics["memory_usage"]
                    else 0
                ),
                "avg_cpu_usage": (
                    sum(self.metrics["cpu_usage"])
                    / len(self.metrics["cpu_usage"])
                    if self.metrics["cpu_usage"]
                    else 0
                ),
                "error_count": len(self.metrics["errors"]),
            }

    return MetricsCollector()


@pytest.fixture
async def test_environment(
    config,
    orchestrator,
    memory_system,
    context_manager,
    lifecycle_manager,
    agent_factory,
):
    """Complete test environment with all components"""
    env = {
        "config": config,
        "orchestrator": orchestrator,
        "memory_system": memory_system,
        "context_manager": context_manager,
        "lifecycle_manager": lifecycle_manager,
        "agent_factory": agent_factory,
    }

    # Initialize all components
    for component in env.values():
        if hasattr(component, "initialize"):
            await component.initialize()

    yield env

    # Cleanup all components
    for component in env.values():
        if hasattr(component, "cleanup"):
            await component.cleanup()


@pytest.fixture
def stress_test_config():
    """Configuration for stress testing"""
    return {
        "concurrent_users": 1000,
        "requests_per_user": 100,
        "ramp_up_time": 60,  # seconds
        "test_duration": 300,  # seconds
        "think_time": 1,  # seconds between requests
        "timeout": 30,  # seconds
    }


@pytest.fixture
def load_test_scenarios():
    """Load test scenarios"""
    return [
        {
            "name": "light_load",
            "users": 100,
            "duration": 60,
            "requests_per_second": 10,
        },
        {
            "name": "medium_load",
            "users": 1000,
            "duration": 300,
            "requests_per_second": 100,
        },
        {
            "name": "heavy_load",
            "users": 10000,
            "duration": 600,
            "requests_per_second": 1000,
        },
        {
            "name": "spike_load",
            "users": 50000,
            "duration": 60,
            "requests_per_second": 5000,
        },
    ]


@pytest.fixture
def cleanup_after_test():
    """Cleanup fixture that runs after each test"""
    yield
    # Cleanup code runs here after test completes
    # Clear any test data, reset states, etc.
    pass


# Autouse fixtures (run automatically)
@pytest.fixture(autouse=True)
async def reset_test_state():
    """Reset test state before each test"""
    # Reset any global state
    yield
    # Cleanup after test


@pytest.fixture(autouse=True)
def capture_logs(caplog):
    """Capture logs for all tests"""
    caplog.set_level("DEBUG")
    yield caplog


# Made with Bob
