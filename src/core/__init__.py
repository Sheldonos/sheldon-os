"""
Sheldon OS Core Module

This module contains the core components of the Sheldon OS system including:
- Orchestrator: Main coordination engine
- Memory System: Advanced memory management
- Context Manager: Context handoff and state management
- Configuration: System-wide configuration
"""

from .config import Config
from .context_manager import ContextManager
from .memory_system import MemorySystem
from .orchestrator import Orchestrator

__all__ = [
    "Orchestrator",
    "MemorySystem",
    "ContextManager",
    "Config",
]

__version__ = "0.1.0"

# Made with Bob
