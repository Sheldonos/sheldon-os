"""
Sheldon OS Agent System

This module contains the agent management system including:
- BaseAgent: Base class for all agents
- AgentFactory: Creates and deploys agents
- AgentRegistry: Tracks all agents
- LifecycleManager: Manages agent lifecycles
"""

from .agent_factory import AgentFactory, AgentTemplate
from .agent_registry import AgentRegistry
from .base_agent import AgentCapability, AgentState, BaseAgent
from .lifecycle_manager import LifecycleManager

__all__ = [
    "BaseAgent",
    "AgentCapability",
    "AgentState",
    "AgentFactory",
    "AgentTemplate",
    "AgentRegistry",
    "LifecycleManager",
]

__version__ = "0.1.0"

# Made with Bob
