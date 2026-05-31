"""
Agent Lifecycle Manager

Manages the complete lifecycle of agents from creation to termination.
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .agent_factory import AgentFactory
from .agent_registry import AgentRegistry
from .base_agent import AgentState, BaseAgent


class LifecycleEvent(Enum):
    """Agent lifecycle events"""

    CREATED = "created"
    STARTED = "started"
    PAUSED = "paused"
    RESUMED = "resumed"
    STOPPED = "stopped"
    TERMINATED = "terminated"
    ERROR = "error"
    HEALTH_CHECK_FAILED = "health_check_failed"


class LifecycleManager:  # pylint: disable=too-many-instance-attributes
    """Manages agent lifecycles

    Responsibilities:
    - Monitor agent health
    - Handle agent failures
    - Restart failed agents
    - Graceful shutdown
    - Resource cleanup
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        factory: Optional[AgentFactory] = None,
        registry: Optional[AgentRegistry] = None,
        health_check_interval: int = 60,
        restart_on_failure: bool = True,
        max_restart_attempts: int = 3,
        config: Optional[Any] = None,
    ):
        """Initialize lifecycle manager

        Args:
            factory: Agent factory
            registry: Agent registry
            health_check_interval: Seconds between health checks
            restart_on_failure: Whether to restart failed agents
            max_restart_attempts: Maximum restart attempts
        """
        self.config = config
        self.factory = factory or AgentFactory(config=config)
        self.registry = registry or AgentRegistry(config=config)
        self.health_check_interval = health_check_interval
        self.restart_on_failure = restart_on_failure
        self.max_restart_attempts = max_restart_attempts

        # Lifecycle tracking
        self.lifecycle_events: Dict[str, List[Dict[str, Any]]] = {}
        self.restart_attempts: Dict[str, int] = {}
        self.last_health_check: Dict[str, datetime] = {}

        # Event callbacks
        self.event_callbacks: Dict[LifecycleEvent, List[Callable]] = {}

        # Background tasks
        self._running = False
        self._health_check_task: Optional[asyncio.Task] = None

        # Statistics
        self.stats = {
            "total_restarts": 0,
            "total_failures": 0,
            "total_health_checks": 0,
        }

    async def start(self):
        """Start lifecycle manager"""
        if self._running:
            return

        self._running = True
        self._health_check_task = asyncio.create_task(
            self._health_check_loop()
        )

    async def stop(self):
        """Stop lifecycle manager"""
        if not self._running:
            return

        self._running = False

        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

    async def initialize(self):
        """Compatibility wrapper for async initialization."""
        await self.start()

    async def cleanup(self):
        """Compatibility wrapper for async cleanup."""
        await self.stop()

    async def create_agent(
        self,
        template_name: str,
        agent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        auto_start: bool = True,
    ) -> BaseAgent:
        """Create an agent with lifecycle tracking

        Args:
            template_name: Template name
            agent_id: Optional agent ID
            config: Optional configuration
            auto_start: Whether to start agent immediately

        Returns:
            Created agent
        """
        # Create agent
        agent = await self.factory.create_agent(
            template_name=template_name,
            agent_id=agent_id,
            config=config,
        )

        # Register agent
        self.registry.register(agent)

        # Track lifecycle event
        await self._record_event(agent.agent_id, LifecycleEvent.CREATED)

        # Start if requested
        if auto_start:
            await self.start_agent(agent.agent_id)

        return agent

    async def start_agent(self, agent_id: str) -> bool:
        """Start an agent

        Args:
            agent_id: Agent ID

        Returns:
            True if started successfully
        """
        agent = self.registry.get(agent_id)
        if not agent:
            return False

        try:
            await agent.start()
            self.registry.update_agent_state(agent_id, AgentState.IDLE)
            await self._record_event(agent_id, LifecycleEvent.STARTED)
            return True
        except Exception as exc:  # pylint: disable=broad-exception-caught
            await self._record_event(
                agent_id,
                LifecycleEvent.ERROR,
                {"error": str(exc)},
            )
            return False

    async def stop_agent(self, agent_id: str, graceful: bool = True) -> bool:
        """Stop an agent

        Args:
            agent_id: Agent ID
            graceful: Whether to stop gracefully

        Returns:
            True if stopped successfully
        """
        agent = self.registry.get(agent_id)
        if not agent:
            return False

        try:
            if graceful:
                # Wait for current task to complete
                if agent.current_task:
                    await asyncio.sleep(1)

            await agent.stop()
            self.registry.update_agent_state(agent_id, AgentState.TERMINATED)
            await self._record_event(agent_id, LifecycleEvent.STOPPED)
            return True
        except Exception as exc:  # pylint: disable=broad-exception-caught
            await self._record_event(
                agent_id,
                LifecycleEvent.ERROR,
                {"error": str(exc)},
            )
            return False

    async def terminate_agent(self, agent_id: str) -> bool:
        """Terminate an agent and preserve terminal state for inspection."""
        stopped = await self.stop_agent(agent_id, graceful=False)
        agent = self.registry.get(agent_id)

        if agent is not None:
            self.registry.update_agent_state(agent_id, AgentState.TERMINATED)

        await self._record_event(agent_id, LifecycleEvent.TERMINATED)

        if stopped:
            self.restart_attempts.pop(agent_id, None)
            self.last_health_check.pop(agent_id, None)

        return stopped or agent is not None

    async def restart_agent(self, agent_id: str) -> bool:
        """Restart an agent

        Args:
            agent_id: Agent ID

        Returns:
            True if restarted successfully
        """
        # Check restart attempts
        attempts = self.restart_attempts.get(agent_id, 0)
        if attempts >= self.max_restart_attempts:
            print(f"Max restart attempts reached for agent {agent_id}")
            return False

        # Stop agent
        await self.stop_agent(agent_id, graceful=False)

        # Wait a bit
        await asyncio.sleep(1)

        # Start agent
        success = await self.start_agent(agent_id)

        if success:
            self.restart_attempts[agent_id] = attempts + 1
            self.stats["total_restarts"] += 1

        return success

    async def pause_agent(self, agent_id: str) -> bool:
        """Pause an agent

        Args:
            agent_id: Agent ID

        Returns:
            True if paused successfully
        """
        agent = self.registry.get(agent_id)
        if not agent:
            return False

        agent.state = AgentState.PAUSED
        self.registry.update_agent_state(agent_id, AgentState.PAUSED)
        await self._record_event(agent_id, LifecycleEvent.PAUSED)

        return True

    async def resume_agent(self, agent_id: str) -> bool:
        """Resume a paused agent

        Args:
            agent_id: Agent ID

        Returns:
            True if resumed successfully
        """
        agent = self.registry.get(agent_id)
        if not agent or agent.state != AgentState.PAUSED:
            return False

        agent.state = AgentState.IDLE
        self.registry.update_agent_state(agent_id, AgentState.IDLE)
        await self._record_event(agent_id, LifecycleEvent.RESUMED)

        return True

    async def get_agent_status(self, agent_id: str) -> Optional[str]:
        """Return integration-friendly agent status string."""
        agent = self.registry.get(agent_id)
        if not agent:
            return None

        mapping = {
            AgentState.INITIALIZING: "initializing",
            AgentState.IDLE: "active",
            AgentState.BUSY: "active",
            AgentState.PAUSED: "paused",
            AgentState.ERROR: "failed",
            AgentState.TERMINATED: "terminated",
        }
        return mapping.get(agent.state, agent.state.value)

    async def mark_agent_failed(self, agent_id: str, error: str) -> bool:
        """Mark an agent as failed for integration tests."""
        agent = self.registry.get(agent_id)
        if not agent:
            return False

        self.registry.update_agent_state(agent_id, AgentState.ERROR)
        await self._record_event(
            agent_id, LifecycleEvent.ERROR, {"error": error}
        )
        return True

    async def check_agent_health(self, agent_id: str) -> bool:
        """Check agent health

        Args:
            agent_id: Agent ID

        Returns:
            True if healthy
        """
        agent = self.registry.get(agent_id)
        if not agent:
            return False

        self.last_health_check[agent_id] = datetime.utcnow()
        self.stats["total_health_checks"] += 1

        # Check if agent is responsive
        try:
            if agent.state == AgentState.ERROR:
                return False

            if agent.state == AgentState.BUSY and agent.current_task:
                started_at = agent.started_at or datetime.utcnow()
                if (datetime.utcnow() - started_at).total_seconds() > (
                    self.health_check_interval * 10
                ):
                    return False

            return True

        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(
                f"Health check failed for agent {agent_id}: {exc}"
            )
            await self._record_event(
                agent_id,
                LifecycleEvent.HEALTH_CHECK_FAILED,
                {"error": str(exc)},
            )
            return False

    async def handle_agent_failure(self, agent_id: str):
        """Handle agent failure

        Args:
            agent_id: Agent ID
        """
        self.stats["total_failures"] += 1

        if self.restart_on_failure:
            print(f"Attempting to restart failed agent {agent_id}")
            await self.restart_agent(agent_id)
            return

        print(f"Agent {agent_id} failed, restart disabled")
        await self.terminate_agent(agent_id)

    def register_event_callback(
        self, event: LifecycleEvent, callback: Callable
    ):
        """Register a callback for lifecycle events

        Args:
            event: Lifecycle event
            callback: Callback function
        """
        if event not in self.event_callbacks:
            self.event_callbacks[event] = []
        self.event_callbacks[event].append(callback)

    def get_agent_lifecycle(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get lifecycle events for an agent

        Args:
            agent_id: Agent ID

        Returns:
            List of lifecycle events
        """
        return self.lifecycle_events.get(agent_id, [])

    def get_statistics(self) -> Dict[str, Any]:
        """Get lifecycle manager statistics

        Returns:
            Statistics dictionary
        """
        return {
            **self.stats,
            "tracked_agents": len(self.lifecycle_events),
            "agents_with_restarts": len(self.restart_attempts),
        }

    async def _health_check_loop(self):
        """Background task for health checks"""
        while self._running:
            try:
                # Check all registered agents
                for agent in self.registry.list_all():
                    healthy = await self.check_agent_health(agent.agent_id)

                    if not healthy:
                        await self.handle_agent_failure(agent.agent_id)

                await asyncio.sleep(self.health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as exc:  # pylint: disable=broad-exception-caught
                print(f"Error in health check loop: {exc}")
                await asyncio.sleep(self.health_check_interval)

    async def _record_event(
        self,
        agent_id: str,
        event: LifecycleEvent,
        data: Optional[Dict[str, Any]] = None,
    ):
        """Record a lifecycle event

        Args:
            agent_id: Agent ID
            event: Lifecycle event
            data: Optional event data
        """
        if agent_id not in self.lifecycle_events:
            self.lifecycle_events[agent_id] = []

        event_record = {
            "event": event.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {},
        }

        self.lifecycle_events[agent_id].append(event_record)

        # Emit event to callbacks
        await self._emit_event(event, {"agent_id": agent_id, **event_record})

    async def _emit_event(  # pylint: disable=duplicate-code
        self, event: LifecycleEvent, data: Dict[str, Any]
    ):
        """Emit event to registered callbacks

        Args:
            event: Lifecycle event
            data: Event data
        """
        callbacks = self.event_callbacks.get(event, [])

        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                print(
                    f"Error in lifecycle event callback for "
                    f"{event.value}: {exc}"
                )


# Made with Bob
