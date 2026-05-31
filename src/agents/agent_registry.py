"""
Agent Registry

Centralized registry for tracking and managing all agents in the system.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from .base_agent import AgentCapability, AgentState, BaseAgent


class AgentRegistry:
    """Central registry for agent management

    Responsibilities:
    - Track all registered agents
    - Index agents by type, capability, and state
    - Provide fast lookup and search
    - Maintain agent metadata
    """

    def __init__(self, config: Optional[Any] = None):
        """Initialize agent registry"""
        self.config = config
        # Primary storage
        self.agents: Dict[str, BaseAgent] = {}

        # Indexes for fast lookup
        self.by_type: Dict[str, Set[str]] = defaultdict(set)
        self.by_capability: Dict[AgentCapability, Set[str]] = defaultdict(set)
        self.by_state: Dict[AgentState, Set[str]] = defaultdict(set)

        # Statistics
        self.stats = {
            "total_registered": 0,
            "total_unregistered": 0,
            "current_count": 0,
        }

    def register(self, agent: BaseAgent) -> bool:
        """Register an agent

        Args:
            agent: Agent to register

        Returns:
            True if registered successfully, False if already registered
        """
        if agent.agent_id in self.agents:
            return False

        # Store agent
        self.agents[agent.agent_id] = agent

        # Update indexes
        self.by_type[agent.agent_type].add(agent.agent_id)
        self.by_state[agent.state].add(agent.agent_id)

        for capability in agent.capabilities:
            self.by_capability[capability].add(agent.agent_id)

        # Update statistics
        self.stats["total_registered"] += 1
        self.stats["current_count"] = len(self.agents)

        return True

    def unregister(self, agent_id: str) -> bool:
        """Unregister an agent

        Args:
            agent_id: Agent ID to unregister

        Returns:
            True if unregistered successfully, False if not found
        """
        agent = self.agents.pop(agent_id, None)
        if not agent:
            return False

        # Remove from indexes
        self.by_type[agent.agent_type].discard(agent_id)
        self.by_state[agent.state].discard(agent_id)

        for capability in agent.capabilities:
            self.by_capability[capability].discard(agent_id)

        # Update statistics
        self.stats["total_unregistered"] += 1
        self.stats["current_count"] = len(self.agents)

        return True

    def get(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID

        Args:
            agent_id: Agent ID

        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(agent_id)

    def find_by_type(self, agent_type: str) -> List[BaseAgent]:
        """Find agents by type

        Args:
            agent_type: Agent type to search for

        Returns:
            List of matching agents
        """
        agent_ids = self.by_type.get(agent_type, set())
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]

    def find_by_capability(
        self, capability: AgentCapability
    ) -> List[BaseAgent]:
        """Find agents by capability

        Args:
            capability: Capability to search for

        Returns:
            List of matching agents
        """
        agent_ids = self.by_capability.get(capability, set())
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]

    def find_by_state(self, state: AgentState) -> List[BaseAgent]:
        """Find agents by state

        Args:
            state: State to search for

        Returns:
            List of matching agents
        """
        agent_ids = self.by_state.get(state, set())
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]

    def list_all(self) -> List[BaseAgent]:
        """List all registered agents

        Returns:
            List of all agents
        """
        return list(self.agents.values())

    def update_agent_state(self, agent_id: str, new_state: AgentState) -> bool:
        """Update an agent's state in the registry

        Args:
            agent_id: Agent ID
            new_state: New state

        Returns:
            True if updated successfully
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return False

        # Remove from old state index
        old_state = agent.state
        self.by_state[old_state].discard(agent_id)

        # Update agent state
        agent.state = new_state

        # Add to new state index
        self.by_state[new_state].add(agent_id)

        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics

        Returns:
            Statistics dictionary
        """
        return {
            **self.stats,
            "by_type": {
                agent_type: len(agent_ids)
                for agent_type, agent_ids in self.by_type.items()
            },
            "by_state": {
                state.value: len(agent_ids)
                for state, agent_ids in self.by_state.items()
            },
            "by_capability": {
                capability.value: len(agent_ids)
                for capability, agent_ids in self.by_capability.items()
            },
        }

    async def initialize(self):
        """Compatibility wrapper for async initialization."""
        return None

    async def cleanup(self):
        """Compatibility wrapper for async cleanup."""
        self.clear()

    def clear(self):
        """Clear all agents from registry"""
        self.agents.clear()
        self.by_type.clear()
        self.by_capability.clear()
        self.by_state.clear()
        self.stats["current_count"] = 0


# Made with Bob
