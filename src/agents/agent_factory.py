"""
Agent Factory

Creates, configures, and deploys agents on-demand.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from .base_agent import AgentCapability, AgentState, BaseAgent


@dataclass
class AgentTemplate:
    """Template for creating agents"""

    name: str
    agent_type: str
    agent_class: Type[BaseAgent]
    capabilities: List[AgentCapability]
    default_config: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "agent_type": self.agent_type,
            "capabilities": [c.value for c in self.capabilities],
            "description": self.description,
            "version": self.version,
            "default_config": self.default_config,
        }


class AgentFactory:
    """Factory for creating and deploying agents

    Responsibilities:
    - Register agent templates
    - Create agents from templates
    - Configure agent capabilities
    - Deploy agents to execution environment
    - Track created agents
    """

    def __init__(
        self,
        config: Optional[Any] = None,
        registry: Optional[Any] = None,
    ):
        """Initialize agent factory"""
        self.config = config
        self.registry = registry
        self.templates: Dict[str, AgentTemplate] = {}
        self.created_agents: Dict[str, BaseAgent] = {}
        self.agent_count_by_type: Dict[str, int] = {}

        # Statistics
        self.stats = {
            "total_created": 0,
            "total_deployed": 0,
            "total_failed": 0,
        }

    async def initialize(self):
        """Compatibility wrapper for async initialization."""
        return None

    async def cleanup(self):
        """Compatibility wrapper for async cleanup."""
        await self.terminate_all()

    def register_template(self, template: AgentTemplate):
        """Register an agent template

        Args:
            template: Agent template to register
        """
        self.templates[template.name] = template

    def get_template(self, name: str) -> Optional[AgentTemplate]:
        """Get an agent template

        Args:
            name: Template name

        Returns:
            Agent template or None
        """
        return self.templates.get(name)

    def list_templates(self) -> List[AgentTemplate]:
        """List all registered templates

        Returns:
            List of agent templates
        """
        return list(self.templates.values())

    async def create_agent(
        self,
        template_name: str,
        agent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        capabilities: Optional[List[AgentCapability]] = None,
    ) -> BaseAgent:
        """Create an agent from a template

        Args:
            template_name: Name of template to use
            agent_id: Optional agent ID
            config: Optional configuration overrides
            capabilities: Optional capability overrides

        Returns:
            Created agent instance

        Raises:
            ValueError: If template not found
        """
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")

        # Merge configurations
        agent_config = {**template.default_config}
        if config:
            agent_config.update(config)

        # Use template capabilities or overrides
        agent_capabilities = capabilities or template.capabilities

        # Create agent instance
        try:
            agent = template.agent_class(
                agent_id=agent_id,
                agent_type=template.agent_type,
                capabilities=agent_capabilities,
                config=agent_config,
            )

            # Track created agent
            self.created_agents[agent.agent_id] = agent

            # Update statistics
            self.stats["total_created"] += 1
            self.agent_count_by_type[template.agent_type] = (
                self.agent_count_by_type.get(template.agent_type, 0) + 1
            )

            return agent

        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.stats["total_failed"] += 1
            raise RuntimeError(f"Failed to create agent: {exc}") from exc

    async def create_custom_agent(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        agent_class: Type[BaseAgent],
        agent_type: str,
        agent_id: Optional[str] = None,
        capabilities: Optional[List[AgentCapability]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> BaseAgent:
        """Create a custom agent without a template

        Args:
            agent_class: Agent class to instantiate
            agent_type: Type of agent
            agent_id: Optional agent ID
            capabilities: Agent capabilities
            config: Agent configuration

        Returns:
            Created agent instance
        """
        try:
            agent = agent_class(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=capabilities or [AgentCapability.TASK_EXECUTION],
                config=config or {},
            )

            # Track created agent
            self.created_agents[agent.agent_id] = agent

            # Update statistics
            self.stats["total_created"] += 1
            self.agent_count_by_type[agent_type] = (
                self.agent_count_by_type.get(agent_type, 0) + 1
            )

            return agent

        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.stats["total_failed"] += 1
            raise RuntimeError(
                f"Failed to create custom agent: {exc}"
            ) from exc

    async def deploy_agent(self, agent: BaseAgent) -> bool:
        """Deploy an agent (start it)

        Args:
            agent: Agent to deploy

        Returns:
            True if deployed successfully
        """
        try:
            await agent.start()
            if self.registry is not None:
                self.registry.register(agent)
            self.stats["total_deployed"] += 1
            return True
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"Failed to deploy agent {agent.agent_id}: {exc}")
            return False

    async def create_and_deploy(
        self,
        template_name: str,
        agent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        capabilities: Optional[List[AgentCapability]] = None,
    ) -> BaseAgent:
        """Create and deploy an agent in one step

        Args:
            template_name: Name of template to use
            agent_id: Optional agent ID
            config: Optional configuration overrides
            capabilities: Optional capability overrides

        Returns:
            Created and deployed agent
        """
        agent = await self.create_agent(
            template_name=template_name,
            agent_id=agent_id,
            config=config,
            capabilities=capabilities,
        )

        await self.deploy_agent(agent)

        return agent

    async def terminate_agent(self, agent_id: str) -> bool:
        """Terminate an agent

        Args:
            agent_id: Agent ID

        Returns:
            True if terminated successfully
        """
        agent = self.created_agents.get(agent_id)
        if not agent:
            return False

        try:
            await agent.stop()
            if self.registry is not None:
                self.registry.unregister(agent_id)
            del self.created_agents[agent_id]
            return True
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"Failed to terminate agent {agent_id}: {exc}")
            return False

    async def terminate_all(self):
        """Terminate all agents"""
        for agent_id in list(self.created_agents.keys()):
            await self.terminate_agent(agent_id)

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID

        Args:
            agent_id: Agent ID

        Returns:
            Agent instance or None
        """
        return self.created_agents.get(agent_id)

    def list_agents(
        self,
        agent_type: Optional[str] = None,
        state: Optional[AgentState] = None,
    ) -> List[BaseAgent]:
        """List agents

        Args:
            agent_type: Filter by agent type
            state: Filter by agent state

        Returns:
            List of agents
        """
        agents = list(self.created_agents.values())

        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]

        if state:
            agents = [a for a in agents if a.state == state]

        return agents

    def get_statistics(self) -> Dict[str, Any]:
        """Get factory statistics

        Returns:
            Statistics dictionary
        """
        return {
            **self.stats,
            "active_agents": len(self.created_agents),
            "registered_templates": len(self.templates),
            "agents_by_type": dict(self.agent_count_by_type),
        }

    async def clone_agent(
        self,
        source_agent_id: str,
        new_agent_id: Optional[str] = None,
    ) -> Optional[BaseAgent]:
        """Clone an existing agent

        Args:
            source_agent_id: ID of agent to clone
            new_agent_id: Optional ID for new agent

        Returns:
            Cloned agent or None if source not found
        """
        source = self.created_agents.get(source_agent_id)
        if not source:
            return None

        # Create new agent with same configuration
        cloned = await self.create_custom_agent(
            agent_class=type(source),
            agent_type=source.agent_type,
            agent_id=new_agent_id,
            capabilities=source.capabilities,
            config=source.config.copy(),
        )

        return cloned

    async def scale_agents(
        self,
        template_name: str,
        count: int,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[BaseAgent]:
        """Create and deploy multiple agents from a template

        Args:
            template_name: Template to use
            count: Number of agents to create
            config: Optional configuration

        Returns:
            List of created agents
        """
        agents = []

        for i in range(count):
            try:
                agent = await self.create_and_deploy(
                    template_name=template_name,
                    config=config,
                )
                agents.append(agent)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                print(f"Failed to create agent {i + 1}/{count}: {exc}")

        return agents


# Built-in agent templates will be registered here
def register_builtin_templates(factory: AgentFactory):
    """Register built-in agent templates."""
    _ = factory


# Made with Bob
