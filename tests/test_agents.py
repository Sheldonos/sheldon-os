"""
Tests for agent system
"""


import pytest

from src.agents.agent_factory import AgentFactory, AgentTemplate
from src.agents.agent_registry import AgentRegistry
from src.agents.base_agent import AgentCapability, AgentState, BaseAgent
from src.agents.lifecycle_manager import LifecycleManager


class MockAgent(BaseAgent):
    """Test helper agent implementation."""

    async def _execute_task_impl(self, task_data):
        """Simple test implementation."""
        return {"result": "success", "data": task_data}


class TestBaseAgent:
    """Test base agent functionality"""

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization"""
        agent = MockAgent(
            agent_type="test",
            capabilities=[AgentCapability.TASK_EXECUTION],
        )

        assert agent.agent_type == "test"
        assert agent.state == AgentState.INITIALIZING
        assert AgentCapability.TASK_EXECUTION in agent.capabilities

    @pytest.mark.asyncio
    async def test_agent_start_stop(self):
        """Test starting and stopping agent"""
        agent = MockAgent(agent_type="test")

        # Start
        await agent.start()
        assert agent.state == AgentState.IDLE
        assert agent.started_at is not None

        # Stop
        await agent.stop()
        assert agent.state == AgentState.TERMINATED
        assert agent.stopped_at is not None

    @pytest.mark.asyncio
    async def test_agent_execute_task(self):
        """Test task execution"""
        agent = MockAgent(agent_type="test")
        await agent.start()

        try:
            result = await agent.execute_task(
                task_id="test_task",
                task_data={"input": "test"},
            )

            assert result["result"] == "success"
            assert agent.metrics.tasks_completed == 1

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_agent_context(self):
        """Test agent context management"""
        agent = MockAgent(agent_type="test")

        # Update context
        agent.update_context("key1", "value1")
        agent.update_context("key2", "value2")

        # Get context
        assert agent.get_context("key1") == "value1"
        assert agent.get_context("key2") == "value2"

        # Get all context
        context = agent.get_context()
        assert "key1" in context
        assert "key2" in context


class TestAgentFactory:
    """Test agent factory"""

    def test_factory_initialization(self):
        """Test factory initialization"""
        factory = AgentFactory()
        assert len(factory.templates) == 0
        assert len(factory.created_agents) == 0

    def test_register_template(self):
        """Test registering templates"""
        factory = AgentFactory()

        template = AgentTemplate(
            name="test_template",
            agent_type="test",
            agent_class=MockAgent,
            capabilities=[AgentCapability.TASK_EXECUTION],
        )

        factory.register_template(template)
        assert "test_template" in factory.templates

    @pytest.mark.asyncio
    async def test_create_agent(self):
        """Test creating agents"""
        factory = AgentFactory()

        # Register template
        template = AgentTemplate(
            name="test_template",
            agent_type="test",
            agent_class=MockAgent,
            capabilities=[AgentCapability.TASK_EXECUTION],
        )
        factory.register_template(template)

        # Create agent
        agent = await factory.create_agent("test_template")
        assert agent is not None
        assert agent.agent_type == "test"
        assert agent.agent_id in factory.created_agents

    @pytest.mark.asyncio
    async def test_create_and_deploy(self):
        """Test creating and deploying agents"""
        factory = AgentFactory()

        # Register template
        template = AgentTemplate(
            name="test_template",
            agent_type="test",
            agent_class=MockAgent,
            capabilities=[AgentCapability.TASK_EXECUTION],
        )
        factory.register_template(template)

        # Create and deploy
        agent = await factory.create_and_deploy("test_template")
        assert agent is not None
        assert agent.state == AgentState.IDLE

        # Cleanup
        await factory.terminate_agent(agent.agent_id)


class TestAgentRegistry:
    """Test agent registry"""

    def test_registry_initialization(self):
        """Test registry initialization"""
        registry = AgentRegistry()
        assert len(registry.agents) == 0

    def test_register_agent(self):
        """Test registering agents"""
        registry = AgentRegistry()
        agent = MockAgent(agent_type="test")

        success = registry.register(agent)
        assert success is True
        assert agent.agent_id in registry.agents

    def test_find_by_type(self):
        """Test finding agents by type"""
        registry = AgentRegistry()

        # Register multiple agents
        agent1 = MockAgent(agent_type="type1")
        agent2 = MockAgent(agent_type="type2")
        agent3 = MockAgent(agent_type="type1")

        registry.register(agent1)
        registry.register(agent2)
        registry.register(agent3)

        # Find by type
        type1_agents = registry.find_by_type("type1")
        assert len(type1_agents) == 2

    def test_find_by_capability(self):
        """Test finding agents by capability"""
        registry = AgentRegistry()

        # Register agents with different capabilities
        agent1 = MockAgent(
            agent_type="test",
            capabilities=[AgentCapability.TASK_EXECUTION],
        )
        agent2 = MockAgent(
            agent_type="test",
            capabilities=[AgentCapability.CODE_GENERATION],
        )

        registry.register(agent1)
        registry.register(agent2)

        # Find by capability
        exec_agents = registry.find_by_capability(
            AgentCapability.TASK_EXECUTION
        )
        assert len(exec_agents) == 1


class TestLifecycleManager:
    """Test lifecycle manager"""

    @pytest.mark.asyncio
    async def test_lifecycle_initialization(self):
        """Test lifecycle manager initialization"""
        factory = AgentFactory()
        registry = AgentRegistry()
        lifecycle = LifecycleManager(factory, registry)

        assert lifecycle.factory == factory
        assert lifecycle.registry == registry

    @pytest.mark.asyncio
    async def test_create_agent_with_lifecycle(self):
        """Test creating agent with lifecycle tracking"""
        factory = AgentFactory()
        registry = AgentRegistry()
        lifecycle = LifecycleManager(factory, registry)

        # Register template
        template = AgentTemplate(
            name="test_template",
            agent_type="test",
            agent_class=MockAgent,
            capabilities=[AgentCapability.TASK_EXECUTION],
        )
        factory.register_template(template)

        # Create agent
        agent = await lifecycle.create_agent("test_template")
        assert agent is not None
        assert agent.agent_id in registry.agents

        # Check lifecycle events
        events = lifecycle.get_agent_lifecycle(agent.agent_id)
        assert len(events) > 0

        # Cleanup
        await lifecycle.terminate_agent(agent.agent_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
