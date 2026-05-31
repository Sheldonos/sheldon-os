"""
Tests for core components
"""


import pytest

from src.core.config import Config
from src.core.context_manager import (
    ContextInterval,
    ContextManager,
    ContextPriority,
)
from src.core.memory_system import MemoryPriority, MemorySystem, MemoryType
from src.core.orchestrator import Orchestrator, TaskPriority


class TestConfig:
    """Test configuration management"""

    def test_config_initialization(self):
        """Test config can be initialized"""
        config = Config()
        assert config.system_name == "Sheldon OS"
        assert config.version == "0.1.0"

    def test_config_database_url(self):
        """Test database URL generation"""
        config = Config()
        assert "postgresql://" in config.database.url

    def test_config_redis_url(self):
        """Test Redis URL generation"""
        config = Config()
        assert "redis://" in config.redis.url


class TestMemorySystem:
    """Test memory system"""

    @pytest.mark.asyncio
    async def test_memory_initialization(self):
        """Test memory system initialization"""
        memory = MemorySystem()
        assert memory.short_term_capacity == 1000
        assert memory.long_term_capacity == 100000
        assert memory.vector_backend == "zeroentropy"
        assert memory.graph_backend == "neo4j"
        assert memory.reranker_enabled is True

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self):
        """Test storing and retrieving memories"""
        memory = MemorySystem()

        # Store a memory
        memory_id = await memory.store(
            content={"test": "data"},
            memory_type=MemoryType.SHORT_TERM,
            priority=MemoryPriority.HIGH,
            tags=["test"],
        )

        assert memory_id is not None

        # Retrieve the memory
        entry = await memory.retrieve(memory_id)
        assert entry is not None
        assert entry.content == {"test": "data"}
        assert entry.memory_type == MemoryType.SHORT_TERM
        assert entry.embedding is not None
        assert isinstance(entry.embedding, list)

    @pytest.mark.asyncio
    async def test_search_by_tags(self):
        """Test searching memories by tags"""
        memory = MemorySystem()

        # Store multiple memories
        await memory.store(
            content={"data": 1},
            tags=["test", "important"],
        )
        await memory.store(
            content={"data": 2},
            tags=["test"],
        )

        # Search by tag
        results = await memory.search(tags=["test"])
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_hybrid_search_returns_ranked_candidates_and_summary(self):
        """Test hybrid retrieval with synthesis and gap analysis"""
        memory = MemorySystem()

        await memory.store(
            content=(
                "Zero entropy retrieval uses rerankers and knowledge "
                "graphs for better recall"
            ),
            memory_type=MemoryType.LONG_TERM,
            priority=MemoryPriority.HIGH,
            tags=["retrieval", "zeroentropy"],
            metadata={"agent_id": "research_agent"},
        )
        await memory.store(
            content=(
                "Hermes and OpenClaw rely on vector search for "
                "memory retrieval"
            ),
            memory_type=MemoryType.SEMANTIC,
            priority=MemoryPriority.MEDIUM,
            tags=["retrieval", "vector-search"],
            metadata={"agent_id": "research_agent"},
        )

        result = await memory.hybrid_search(
            "zero entropy rerankers knowledge graphs", limit=5
        )

        assert result.query == "zero entropy rerankers knowledge graphs"
        assert len(result.candidates) >= 1
        assert result.candidates[0].final_score > 0
        assert result.synthesized_summary is not None
        assert isinstance(result.gaps, list)
        assert result.metadata["vector_backend"] == "zeroentropy"

    @pytest.mark.asyncio
    async def test_hybrid_search_updates_graph_indexes(self):
        """Test graph/entity indexes are populated from stored memories"""
        memory = MemorySystem()

        memory_id = await memory.store(
            content="GBrain builds graph memory for retrieval orchestration",
            memory_type=MemoryType.LONG_TERM,
            tags=["gbrain", "graph"],
        )

        entry = await memory.retrieve(memory_id, update_access=False)
        assert entry is not None
        assert "entities" in entry.metadata
        assert len(entry.metadata["entities"]) > 0
        assert len(memory.entity_index) > 0
        assert len(memory.knowledge_graph) > 0

    @pytest.mark.asyncio
    async def test_store_memory_and_retrieve_memories_compatibility_api(self):
        """Test integration-friendly memory compatibility helpers"""
        memory = MemorySystem()

        await memory.store_memory(
            agent_id="agent-123",
            memory_type="task_execution",
            content={"task": "Research AI trends", "result": "done"},
            metadata={"source": "integration-test"},
        )

        memories = await memory.retrieve_memories(
            agent_id="agent-123",
            memory_type="task_execution",
            limit=10,
        )

        assert len(memories) == 1
        assert memories[0]["task"] == "Research AI trends"
        assert memories[0]["result"] == "done"

    @pytest.mark.asyncio
    async def test_query_with_synthesis_returns_structured_response(self):
        """Test synthesized query helper returns retrieval metadata"""
        memory = MemorySystem()

        await memory.store_memory(
            agent_id="agent-456",
            memory_type="semantic",
            content={
                "fact": (
                    "ZeroEntropy-style retrieval benefits from reranking"
                )
            },
        )

        response = await memory.query_with_synthesis(
            query="reranking benefits",
            limit=5,
        )

        assert response["query"] == "reranking benefits"
        assert "summary" in response
        assert "results" in response
        assert "gaps" in response
        assert len(response["results"]) >= 1

    @pytest.mark.asyncio
    async def test_memory_consolidation(self):
        """Test memory consolidation"""
        memory = MemorySystem()

        # Store some memories
        for i in range(5):
            await memory.store(
                content={"data": i},
                memory_type=MemoryType.SHORT_TERM,
            )

        # Consolidate
        await memory.consolidate()

        # Check statistics
        stats = memory.get_statistics()
        assert stats["consolidations"] >= 1


class TestContextManager:
    """Test context manager"""

    @pytest.mark.asyncio
    async def test_context_initialization(self):
        """Test context manager initialization"""
        context = ContextManager()
        assert context.current_context is not None

    @pytest.mark.asyncio
    async def test_update_and_get_context(self):
        """Test updating and getting context"""
        context = ContextManager()

        # Update context
        await context.update_context("test_key", "test_value")

        # Get context
        value = await context.get_context("test_key")
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_create_snapshot(self):
        """Test creating context snapshots"""
        context = ContextManager()

        # Create snapshot
        snapshot = await context.create_snapshot(
            interval=ContextInterval.HOURLY,
            priority=ContextPriority.HIGH,
            force=True,
        )

        assert snapshot is not None
        assert snapshot.interval == ContextInterval.HOURLY

    @pytest.mark.asyncio
    async def test_create_handoff(self):
        """Test creating context handoffs"""
        context = ContextManager()

        # Create handoff
        handoff_id = await context.create_handoff(
            from_agent="agent1",
            to_agent="agent2",
            context={"data": "test"},
            instructions=["Do this", "Do that"],
        )

        assert handoff_id is not None

        # Get handoffs
        handoffs = await context.get_handoffs(agent_id="agent2")
        assert len(handoffs) == 1


class TestOrchestrator:
    """Test orchestrator"""

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        config = Config()
        orchestrator = Orchestrator(config)

        assert orchestrator.config == config
        assert orchestrator.running is False

    @pytest.mark.asyncio
    async def test_orchestrator_start_stop(self):
        """Test starting and stopping orchestrator"""
        config = Config()
        orchestrator = Orchestrator(config)

        # Start
        await orchestrator.start()
        assert orchestrator.running is True

        # Stop
        await orchestrator.stop()
        assert orchestrator.running is False

    @pytest.mark.asyncio
    async def test_create_task(self):
        """Test creating tasks"""
        config = Config()
        orchestrator = Orchestrator(config)
        await orchestrator.start()

        try:
            # Create task
            task_id = await orchestrator.create_task(
                name="test_task",
                description="A test task",
                priority=TaskPriority.HIGH,
            )

            assert task_id is not None

            # Get task
            task = await orchestrator.get_task(task_id)
            assert task is not None
            assert task.name == "test_task"

        finally:
            await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_get_metrics(self):
        """Test getting system metrics"""
        config = Config()
        orchestrator = Orchestrator(config)
        await orchestrator.start()

        try:
            metrics = await orchestrator.get_metrics()
            assert metrics is not None
            assert metrics.total_agents >= 0
            assert metrics.total_tasks >= 0

        finally:
            await orchestrator.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
