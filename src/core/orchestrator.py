"""
Sheldon OS Main Orchestrator

The orchestrator is the central coordination engine that:
- Manages multi-agent coordination
- Handles task delegation and execution
- Monitors system health
- Implements self-learning capabilities
- Coordinates with memory and context systems
- Makes strategic decisions
"""

import asyncio
import uuid
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from agents.base_agent import AgentCapability, AgentState, BaseAgent
from agents.lifecycle_manager import LifecycleEvent
from .config import Config
from .context_manager import ContextManager
from .memory_system import MemoryPriority, MemorySystem, MemoryType

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""

    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    MINIMAL = 1


@dataclass
class Task:
    """Represents a task in the system"""

    id: str
    name: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    assigned_to: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "assigned_to": self.assigned_to,
            "started_at": (
                self.started_at.isoformat() if self.started_at else None
            ),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "result": self.result,
            "error": self.error,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }


@dataclass
class AgentStatus:
    """Status of an agent in the system"""

    agent_id: str
    agent_type: str
    status: str  # active, idle, busy, error, offline
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_heartbeat: Optional[datetime] = None
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System-wide metrics"""

    timestamp: datetime
    total_agents: int
    active_agents: int
    idle_agents: int
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    failed_tasks: int
    avg_task_duration: float
    system_load: float
    memory_usage: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_agents": self.total_agents,
            "active_agents": self.active_agents,
            "idle_agents": self.idle_agents,
            "total_tasks": self.total_tasks,
            "pending_tasks": self.pending_tasks,
            "in_progress_tasks": self.in_progress_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "avg_task_duration": self.avg_task_duration,
            "system_load": self.system_load,
            "memory_usage": self.memory_usage,
        }


class Orchestrator:  # pylint: disable=too-many-public-methods
    """Main orchestration engine for Sheldon OS

    The orchestrator is responsible for:
    - Task management and delegation
    - Agent coordination and monitoring
    - Resource allocation
    - System health monitoring
    - Self-learning and optimization
    - Strategic decision making
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        memory_system: Optional[MemorySystem] = None,
        context_manager: Optional[ContextManager] = None,
        lifecycle_manager: Optional[Any] = None,
    ):
        """Initialize orchestrator

        Args:
            config: System configuration (optional)
            memory_system: Memory system instance
            context_manager: Context manager instance
            lifecycle_manager: Lifecycle manager instance
        """
        self.config = config or Config()
        self.memory = memory_system or MemorySystem(
            short_term_capacity=self.config.memory.short_term_capacity,
            long_term_capacity=self.config.memory.long_term_capacity,
            consolidation_interval=self.config.memory.consolidation_interval,
            retention_days=self.config.memory.retention_days,
        )
        self.context = context_manager or ContextManager(config=self.config)
        self.lifecycle = lifecycle_manager
        self._agent_objects: Dict[str, Any] = {}

        # Task management
        self.tasks: Dict[str, Task] = {}
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()

        # Agent management
        self.agents: Dict[str, AgentStatus] = {}
        self.agent_capabilities: Dict[str, Set[str]] = defaultdict(set)

        # System state
        self.running = False
        self.start_time: Optional[datetime] = None

        # Performance tracking
        self.task_durations: List[float] = []
        self.decisions_made: List[Dict[str, Any]] = []

        # Background tasks
        self._worker_tasks: List[asyncio.Task] = []
        self._monitor_task: Optional[asyncio.Task] = None
        self._learning_task: Optional[asyncio.Task] = None

        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = defaultdict(list)

    async def start(self):
        """Start the orchestrator"""
        if self.running:
            return

        self.running = True
        self.start_time = datetime.utcnow()

        # Start subsystems
        await self.memory.start()
        await self.context.start()

        # Start worker tasks
        num_workers = (
            self.config.agent.max_concurrent_agents // 10
        )  # 10 tasks per worker
        for i in range(max(1, num_workers)):
            task = asyncio.create_task(self._worker_loop(f"worker_{i}"))
            self._worker_tasks.append(task)

        # Start monitoring
        self._monitor_task = asyncio.create_task(self._monitor_loop())

        # Start self-learning
        self._learning_task = asyncio.create_task(self._learning_loop())

        # Store startup in memory
        await self.memory.store(
            content={
                "event": "orchestrator_started",
                "timestamp": self.start_time.isoformat(),
                "config": self.config.to_dict(),
            },
            memory_type=MemoryType.EPISODIC,
            priority=MemoryPriority.HIGH,
            tags=["system", "startup"],
        )

        # Update context
        await self.context.update_context(
            "system_state",
            {
                "status": "running",
                "start_time": self.start_time.isoformat(),
            },
        )

        await self._emit_event("orchestrator_started", {})

    async def stop(self):
        """Stop the orchestrator"""
        if not self.running:
            return

        self.running = False

        # Cancel all worker tasks
        for task in self._worker_tasks:
            task.cancel()

        if self._monitor_task:
            self._monitor_task.cancel()

        if self._learning_task:
            self._learning_task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)

        if self._monitor_task:
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        if self._learning_task:
            try:
                await self._learning_task
            except asyncio.CancelledError:
                pass

        # Stop subsystems
        await self.memory.stop()
        await self.context.stop()

        # Store shutdown in memory
        uptime = (
            (datetime.utcnow() - self.start_time).total_seconds()
            if self.start_time
            else 0
        )
        await self.memory.store(
            content={
                "event": "orchestrator_stopped",
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": uptime,
            },
            memory_type=MemoryType.EPISODIC,
            priority=MemoryPriority.HIGH,
            tags=["system", "shutdown"],
        )

        await self._emit_event("orchestrator_stopped", {})

    async def create_task(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        name: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new task

        Args:
            name: Task name
            description: Task description
            priority: Task priority
            dependencies: List of task IDs this task depends on
            metadata: Additional metadata

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())

        task = Task(
            id=task_id,
            name=name,
            description=description,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow(),
            dependencies=dependencies or [],
            metadata=metadata or {},
        )

        self.tasks[task_id] = task

        # Add to queue (priority is inverted for PriorityQueue)
        await self.task_queue.put((-priority.value, task_id))

        # Store in memory
        await self.memory.store(
            content=task.to_dict(),
            memory_type=MemoryType.SHORT_TERM,
            priority=MemoryPriority.MEDIUM,
            tags=["task", "created", name],
        )

        await self._emit_event(
            "task_created", {"task_id": task_id, "task": task.to_dict()}
        )

        return task_id

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID

        Args:
            task_id: Task ID

        Returns:
            Task or None
        """
        return self.tasks.get(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task

        Args:
            task_id: Task ID

        Returns:
            True if cancelled, False if not found or already completed
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        if task.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]:
            return False

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()

        await self._emit_event("task_cancelled", {"task_id": task_id})

        return True

    async def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Register an agent with the orchestrator

        Args:
            agent_id: Unique agent ID
            agent_type: Type of agent
            capabilities: List of agent capabilities
            metadata: Additional metadata

        Returns:
            True if registered successfully
        """
        if agent_id in self.agents:
            return False

        status = AgentStatus(
            agent_id=agent_id,
            agent_type=agent_type,
            status="active",
            capabilities=capabilities,
            last_heartbeat=datetime.utcnow(),
            metadata=metadata or {},
        )

        self.agents[agent_id] = status

        # Index capabilities
        for capability in capabilities:
            self.agent_capabilities[capability].add(agent_id)

        # Store in memory
        await self.memory.store(
            content={
                "event": "agent_registered",
                "agent_id": agent_id,
                "agent_type": agent_type,
                "capabilities": capabilities,
            },
            memory_type=MemoryType.SHORT_TERM,
            priority=MemoryPriority.MEDIUM,
            tags=["agent", "registered", agent_type],
        )

        await self._emit_event("agent_registered", {"agent_id": agent_id})

        return True

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent

        Args:
            agent_id: Agent ID

        Returns:
            True if unregistered successfully
        """
        agent = self.agents.pop(agent_id, None)
        if not agent:
            return False

        # Remove from capability index
        for capability in agent.capabilities:
            self.agent_capabilities[capability].discard(agent_id)

        await self._emit_event("agent_unregistered", {"agent_id": agent_id})

        return True

    async def update_agent_heartbeat(self, agent_id: str) -> bool:
        """Update agent heartbeat

        Args:
            agent_id: Agent ID

        Returns:
            True if updated successfully
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return False

        agent.last_heartbeat = datetime.utcnow()
        return True

    async def get_metrics(self) -> SystemMetrics:
        """Get current system metrics

        Returns:
            System metrics
        """
        # Count task statuses
        status_counts: Dict[TaskStatus, int] = defaultdict(int)
        for task in self.tasks.values():
            status_counts[task.status] += 1

        # Count agent statuses
        agent_status_counts: Dict[str, int] = defaultdict(int)
        for agent in self.agents.values():
            agent_status_counts[agent.status] += 1

        # Calculate average task duration
        avg_duration = (
            sum(self.task_durations) / len(self.task_durations)
            if self.task_durations
            else 0.0
        )

        # Calculate system load (tasks per agent)
        system_load = len(self.tasks) / max(len(self.agents), 1)

        metrics = SystemMetrics(
            timestamp=datetime.utcnow(),
            total_agents=len(self.agents),
            active_agents=agent_status_counts.get("active", 0)
            + agent_status_counts.get("busy", 0),
            idle_agents=agent_status_counts.get("idle", 0),
            total_tasks=len(self.tasks),
            pending_tasks=status_counts.get(TaskStatus.PENDING, 0),
            in_progress_tasks=status_counts.get(TaskStatus.IN_PROGRESS, 0),
            completed_tasks=status_counts.get(TaskStatus.COMPLETED, 0),
            failed_tasks=status_counts.get(TaskStatus.FAILED, 0),
            avg_task_duration=avg_duration,
            system_load=system_load,
            memory_usage=0.0,
        )

        return metrics

    def register_event_callback(self, event_type: str, callback: Callable):
        """Register a callback for an event type

        Args:
            event_type: Type of event
            callback: Async callback function
        """
        self.event_callbacks[event_type].append(callback)

    async def _worker_loop(self, worker_id: str):
        """Worker loop for processing tasks"""
        while self.running:
            try:
                # Get next task from queue (with timeout)
                try:
                    priority, task_id = await asyncio.wait_for(
                        self.task_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                task = self.tasks.get(task_id)
                if not task or task.status != TaskStatus.PENDING:
                    continue

                # Check dependencies
                if not await self._check_dependencies(task):
                    # Re-queue task
                    await self.task_queue.put((priority, task_id))
                    await asyncio.sleep(1)
                    continue

                # Find suitable agent
                agent_id = await self._find_agent_for_task(task)
                if not agent_id:
                    # Re-queue task
                    await self.task_queue.put((priority, task_id))
                    await asyncio.sleep(1)
                    continue

                # Assign and execute task
                await self._execute_task(task, agent_id)

            except asyncio.CancelledError:
                break
            except Exception as exc:  # pylint: disable=broad-exception-caught
                print(f"Error in worker {worker_id}: {exc}")
                await asyncio.sleep(1)

    async def _monitor_loop(self):
        """Monitor system health and performance"""
        while self.running:
            try:
                # Collect metrics
                metrics = await self.get_metrics()

                # Update context
                await self.context.update_context("metrics", metrics.to_dict())

                # Check agent health
                await self._check_agent_health()

                # Store metrics in memory
                await self.memory.store(
                    content=metrics.to_dict(),
                    memory_type=MemoryType.SHORT_TERM,
                    priority=MemoryPriority.LOW,
                    tags=["metrics", "system"],
                )

                await asyncio.sleep(self.config.agent.health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as exc:  # pylint: disable=broad-exception-caught
                print(f"Error in monitor loop: {exc}")
                await asyncio.sleep(60)

    async def _learning_loop(self):
        """Self-learning and optimization loop"""
        while self.running:
            try:
                # Analyze patterns in completed tasks
                await self._analyze_task_patterns()

                # Optimize agent allocation
                await self._optimize_agent_allocation()

                # Learn from failures
                await self._learn_from_failures()

                # Update strategies
                await self._update_strategies()

                await asyncio.sleep(3600)  # Run every hour

            except asyncio.CancelledError:
                break
            except Exception as exc:  # pylint: disable=broad-exception-caught
                print(f"Error in learning loop: {exc}")
                await asyncio.sleep(3600)

    async def _check_dependencies(self, task: Task) -> bool:
        """Check if task dependencies are satisfied"""
        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True

    async def _find_agent_for_task(self, task: Task) -> Optional[str]:
        """Find a suitable agent for a task."""
        _ = task

        # Simple implementation: find any available agent
        for agent_id, agent in self.agents.items():
            if agent.status in {"idle", "active"}:
                return agent_id

        return None

    async def _execute_task(self, task: Task, agent_id: str):
        """Execute a task with an agent"""
        task.status = TaskStatus.ASSIGNED
        task.assigned_to = agent_id
        task.started_at = datetime.utcnow()

        agent = self.agents[agent_id]
        agent.status = "busy"
        agent.current_task = task.id

        await self._emit_event(
            "task_started",
            {
                "task_id": task.id,
                "agent_id": agent_id,
            },
        )

        try:
            task.status = TaskStatus.IN_PROGRESS

            # Simulate task execution
            await asyncio.sleep(1)

            # Mark as completed
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()

            # Track duration
            duration = (task.completed_at - task.started_at).total_seconds()
            self.task_durations.append(duration)

            # Update agent stats
            agent.tasks_completed += 1
            agent.status = "active"
            agent.current_task = None

            await self._emit_event(
                "task_completed",
                {
                    "task_id": task.id,
                    "agent_id": agent_id,
                    "duration": duration,
                },
            )

        except Exception as exc:  # pylint: disable=broad-exception-caught
            task.status = TaskStatus.FAILED
            task.error = str(exc)
            task.completed_at = datetime.utcnow()

            agent.tasks_failed += 1
            agent.status = "active"
            agent.current_task = None

            # Retry if possible
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                await self.task_queue.put((-task.priority.value, task.id))

            await self._emit_event(
                "task_failed",
                {
                    "task_id": task.id,
                    "agent_id": agent_id,
                    "error": str(exc),
                },
            )

    async def _check_agent_health(self):
        """Check health of all agents"""
        timeout = timedelta(
            seconds=self.config.agent.health_check_interval * 2
        )
        now = datetime.utcnow()

        for agent_id, agent in list(self.agents.items()):
            if agent.last_heartbeat and (now - agent.last_heartbeat) > timeout:
                agent.status = "offline"
                await self._emit_event("agent_offline", {"agent_id": agent_id})

    async def _analyze_task_patterns(self):
        """Analyze patterns in task execution."""
        patterns = await self.memory.find_patterns()

        if patterns:
            await self.memory.store(
                content={"patterns": [p.__dict__ for p in patterns]},
                memory_type=MemoryType.SEMANTIC,
                priority=MemoryPriority.HIGH,
                tags=["patterns", "analysis"],
            )

    async def _optimize_agent_allocation(self):
        """Optimize how agents are allocated to tasks."""
        idle_agents = sum(
            1 for agent in self.agents.values() if agent.status == "idle"
        )
        busy_agents = sum(
            1 for agent in self.agents.values() if agent.status == "busy"
        )
        await self.memory.store(
            content={
                "idle_agents": idle_agents,
                "busy_agents": busy_agents,
                "queued_tasks": self.task_queue.qsize(),
            },
            memory_type=MemoryType.SHORT_TERM,
            priority=MemoryPriority.LOW,
            tags=["optimization", "agent_allocation"],
        )

    async def _learn_from_failures(self):
        """Learn from failed tasks."""
        failed_tasks = [
            task for task in self.tasks.values() if task.status == TaskStatus.FAILED
        ]

        if not failed_tasks:
            return

        recent_failures = failed_tasks[-10:]
        failure_summary = {
            "failed_tasks": [task.to_dict() for task in recent_failures],
            "failure_count": len(failed_tasks),
            "retryable_failures": sum(
                1 for task in recent_failures if task.retry_count < task.max_retries
            ),
        }
        await self.memory.store(
            content=failure_summary,
            memory_type=MemoryType.SEMANTIC,
            priority=MemoryPriority.HIGH,
            tags=["failures", "learning"],
        )

    async def _update_strategies(self):
        """Update orchestration strategies based on learning."""
        await self.memory.store(
            content={
                "decisions_recorded": len(self.decisions_made),
                "task_history_size": len(self.task_durations),
            },
            memory_type=MemoryType.SHORT_TERM,
            priority=MemoryPriority.LOW,
            tags=["strategy", "learning"],
        )

    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to registered callbacks"""
        callbacks = self.event_callbacks.get(event_type, [])

        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                print(f"Error in event callback for {event_type}: {exc}")

    # Integration compatibility methods

    async def initialize(self):
        """Initialize orchestrator (async wrapper for start)"""
        await self.start()

    async def cleanup(self):
        """Cleanup orchestrator (async wrapper for stop)"""
        await self.stop()

    async def create_agent(
        self,
        agent_type: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create and register an agent

        Args:
            agent_type: Type of agent to create
            config: Agent configuration

        Returns:
            Agent ID
        """
        # Create a simple agent implementation for testing
        class SimpleAgent(  # pylint: disable=missing-class-docstring
            BaseAgent
        ):
            async def _execute_task_impl(
                self, task_data: Dict[str, Any]
            ) -> Dict[str, Any]:
                return {"status": "completed", "result": task_data}

        # Create agent instance
        agent = SimpleAgent(
            agent_type=agent_type,
            capabilities=[AgentCapability.TASK_EXECUTION],
            config=config or {},
        )

        # Start agent
        await agent.start()
        self._agent_objects[agent.agent_id] = agent

        # Register with orchestrator using string capabilities.
        await self.register_agent(
            agent_id=agent.agent_id,
            agent_type=agent_type,
            capabilities=["task_execution"],
            metadata=config or {},
        )

        if self.lifecycle:
            self.lifecycle.registry.register(agent)
            await self.lifecycle.start_agent(agent.agent_id)
            await self.lifecycle._record_event(  # pylint: disable=protected-access
                agent.agent_id,
                LifecycleEvent.CREATED,
            )
            await self.lifecycle._record_event(  # pylint: disable=protected-access
                agent.agent_id,
                LifecycleEvent.STARTED,
            )

        agent_status = self.agents.get(agent.agent_id)
        if agent_status:
            agent_status.status = "active"

        return agent.agent_id

    async def execute_task(self, agent_id: str, task: Any, **kwargs) -> Any:
        """Execute a task on a specific agent."""
        agent = self._agent_objects.get(agent_id)
        agent_status = self.agents.get(agent_id)

        task_payload = task if isinstance(task, dict) else {"task": task}
        task_name = (
            task_payload.get("name")
            or task_payload.get("task")
            or str(task)
        )

        if agent_status:
            agent_status.status = "busy"
            agent_status.current_task = task_name
            agent_status.last_heartbeat = datetime.utcnow()

        result: Any
        previous_agent_state = None
        try:
            if agent is not None:
                previous_agent_state = agent.state
                agent.state = AgentState.BUSY
                result = await agent.execute_task(
                    task_id=str(uuid.uuid4()),
                    task_data=task_payload,
                )
            else:
                result = {"status": "completed", "result": task_payload}

            if (
                isinstance(result, dict)
                and "result" in result
                and len(result) == 2
                and result.get("status") == "completed"
            ):
                normalized_result = result["result"]
            else:
                normalized_result = result

            if not kwargs.get("fallback_on_memory_failure"):
                await self.memory.store_memory(
                    agent_id=agent_id,
                    memory_type="task_execution",
                    content={"task": task_name, "result": normalized_result},
                    metadata={"timestamp": datetime.utcnow().isoformat()},
                )
            else:
                try:
                    await self.memory.store_memory(
                        agent_id=agent_id,
                        memory_type="task_execution",
                        content={
                            "task": task_name,
                            "result": normalized_result,
                        },
                        metadata={"timestamp": datetime.utcnow().isoformat()},
                    )
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    logger.debug(
                        "Skipping fallback memory persistence for agent %s: %s",
                        agent_id,
                        exc,
                    )

            try:
                await self.context.create_snapshot(
                    agent_id=agent_id,
                    context={"task": task_name, "result": normalized_result},
                    snapshot_type="task_execution",
                    metadata={"timestamp": datetime.utcnow().isoformat()},
                )
            except Exception:  # pylint: disable=broad-exception-caught
                logger.debug(
                    "Skipping context snapshot for agent %s task %s",
                    agent_id,
                    task_name,
                )

            if agent is not None:
                agent.state = AgentState.IDLE
                if self.lifecycle:
                    await self.lifecycle.start_agent(agent_id)
            if agent_status:
                agent_status.status = "active"
                agent_status.current_task = None

            return normalized_result
        except Exception:  # pylint: disable=broad-exception-caught
            if agent is not None and previous_agent_state is not None:
                agent.state = previous_agent_state
                if self.lifecycle and previous_agent_state == AgentState.IDLE:
                    await self.lifecycle.start_agent(agent_id)
                elif self.lifecycle:
                    self.lifecycle.registry.update_agent_state(
                        agent_id,
                        previous_agent_state,
                    )
            if agent_status:
                agent_status.status = "failed"
            raise

    async def get_agent_context(self, agent_id: str) -> Dict[str, Any]:
        """Get agent context from memory system."""
        memory_types = [
            "conversation",
            "task_execution",
            "long_term",
            "working",
            "progress",
        ]
        context: Dict[str, Any] = {
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        for memory_type in memory_types:
            memories = await self.memory.retrieve_memories(
                agent_id=agent_id,
                memory_type=memory_type,
                limit=20,
            )
            if memories:
                context[memory_type] = memories

        return context

    async def restore_agent_state(
        self,
        agent_id: str,
        snapshot_id: str,
    ) -> Dict[str, Any]:
        """Restore agent state from a snapshot."""
        snapshot = await self.context.get_snapshot(snapshot_id=snapshot_id)
        if not snapshot:
            return {}

        restored_context = (
            snapshot.get("system_state", {})
            if isinstance(snapshot, dict)
            else {}
        )
        await self.memory.store_memory(
            agent_id=agent_id,
            memory_type="episodic",
            content=restored_context,
            metadata={
                "snapshot_id": snapshot_id,
                "restored_at": datetime.utcnow().isoformat(),
            },
        )
        return restored_context

    async def get_handoff_context(
        self,
        agent_id: str,
        snapshot_id: str,
    ) -> Dict[str, Any]:
        """Get handoff context for agent transition

        Args:
            agent_id: Agent ID
            snapshot_id: Snapshot ID

        Returns:
            Handoff context dictionary
        """
        handoffs = await self.context.get_handoffs(agent_id=agent_id)
        handoff = next((h for h in handoffs if h.id == snapshot_id), None)
        if not handoff:
            return {}

        return handoff.context

    async def pause_agent(self, agent_id: str) -> bool:
        """Pause an agent

        Args:
            agent_id: Agent ID

        Returns:
            True if paused successfully
        """
        if self.lifecycle:
            return bool(await self.lifecycle.pause_agent(agent_id))

        # Fallback: update agent status
        agent_status = self.agents.get(agent_id)
        if agent_status:
            agent_status.status = "paused"
            return True

        return False

    async def resume_agent(self, agent_id: str) -> bool:
        """Resume a paused agent

        Args:
            agent_id: Agent ID

        Returns:
            True if resumed successfully
        """
        if self.lifecycle:
            return bool(await self.lifecycle.resume_agent(agent_id))

        # Fallback: update agent status
        agent_status = self.agents.get(agent_id)
        if agent_status:
            agent_status.status = "active"
            return True

        return False

    async def terminate_agent(self, agent_id: str) -> bool:
        """Terminate an agent

        Args:
            agent_id: Agent ID

        Returns:
            True if terminated successfully
        """
        if self.lifecycle:
            await self.lifecycle.terminate_agent(agent_id)

        self._agent_objects.pop(agent_id, None)
        agent_status = self.agents.get(agent_id)
        if agent_status:
            agent_status.status = "terminated"
            return True

        return await self.unregister_agent(agent_id)

    async def start_long_task(
        self,
        agent_id: str,
        task: Dict[str, Any],
    ) -> str:
        """Start a long-running task

        Args:
            agent_id: Agent ID
            task: Task data

        Returns:
            Task ID
        """
        task_payload = task if isinstance(task, dict) else {"task": task}
        task_id = await self.create_task(
            name=task_payload.get("name", "Long Running Task"),
            description=task_payload.get(
                "description", f"Long running task for agent {agent_id}"
            ),
            priority=TaskPriority.LOW,
            metadata={
                "agent_id": agent_id,
                "task_data": task_payload,
                "long_running": True,
            },
        )

        async def _checkpoint_loop() -> None:
            agent_obj = self._agent_objects.get(agent_id)
            checkpoint_interval = (
                agent_obj.config.get("checkpoint_interval", 5)
                if agent_obj is not None
                else 5
            )
            for progress in (0.25, 0.5, 0.75):
                await asyncio.sleep(checkpoint_interval)
                await self.memory.store_memory(
                    agent_id=agent_id,
                    memory_type="progress",
                    content={"task_id": task_id, "progress": progress},
                    metadata={"timestamp": datetime.utcnow().isoformat()},
                )
                await self.context.create_snapshot(
                    agent_id=agent_id,
                    context={"task_id": task_id, "progress": progress},
                    snapshot_type="checkpoint",
                    metadata={"timestamp": datetime.utcnow().isoformat()},
                )

        asyncio.create_task(_checkpoint_loop())
        return task_id

    async def check_agent_health(self, agent_id: str) -> Dict[str, Any]:
        """Check agent health status

        Args:
            agent_id: Agent ID

        Returns:
            Health status dictionary
        """
        if self.lifecycle:
            is_healthy = await self.lifecycle.check_agent_health(agent_id)
            if not is_healthy:
                await self.lifecycle.handle_agent_failure(agent_id)
            return {
                "agent_id": agent_id,
                "healthy": is_healthy,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Fallback: check agent status
        agent_status = self.agents.get(agent_id)
        if not agent_status:
            return {
                "agent_id": agent_id,
                "healthy": False,
                "error": "Agent not found",
            }

        # Check heartbeat
        if agent_status.last_heartbeat:
            time_since_heartbeat = (
                datetime.utcnow() - agent_status.last_heartbeat
            ).total_seconds()
            is_healthy = time_since_heartbeat < 300  # 5 minutes
        else:
            is_healthy = False

        return {
            "agent_id": agent_id,
            "healthy": is_healthy,
            "status": agent_status.status,
            "last_heartbeat": (
                agent_status.last_heartbeat.isoformat()
                if agent_status.last_heartbeat
                else None
            ),
        }

    async def recover_agent(
        self,
        agent_id: str,
        snapshot_id: str,
    ) -> bool:
        """Recover agent from failure using snapshot

        Args:
            agent_id: Agent ID
            snapshot_id: Snapshot ID to restore from

        Returns:
            True if recovered successfully
        """
        restored = await self.restore_agent_state(agent_id, snapshot_id)
        if restored is None:
            return False

        if self.lifecycle:
            lifecycle_status = await self.lifecycle.get_agent_status(agent_id)
            if lifecycle_status is None:
                recovered_agent_id = await self.create_agent(
                    agent_type="recovered",
                    config={"restored_agent_id": agent_id},
                )

                recovered_agent = self._agent_objects.pop(
                    recovered_agent_id,
                    None,
                )
                recovered_status = self.agents.pop(
                    recovered_agent_id,
                    None,
                )

                if recovered_agent is not None:
                    self.lifecycle.registry.unregister(recovered_agent_id)
                    recovered_agent.agent_id = agent_id
                    self._agent_objects[agent_id] = recovered_agent
                    self.lifecycle.registry.register(recovered_agent)

                if recovered_status is not None:
                    recovered_status.agent_id = agent_id
                    recovered_status.status = "active"
                    self.agents[agent_id] = recovered_status
            elif lifecycle_status == "paused":
                await self.lifecycle.resume_agent(agent_id)
            elif lifecycle_status == "failed":
                lifecycle_agent = self.lifecycle.registry.get(agent_id)
                if lifecycle_agent is not None:
                    await self.lifecycle.start_agent(agent_id)

        if agent_id not in self.agents:
            self.agents[agent_id] = AgentStatus(
                agent_id=agent_id,
                agent_type="recovered",
                status="active",
                last_heartbeat=datetime.utcnow(),
                capabilities=["task_execution"],
                metadata={"recovered_from_snapshot": snapshot_id},
            )

        if agent_id not in self._agent_objects and self.lifecycle:
            lifecycle_agent = self.lifecycle.registry.get(agent_id)
            if lifecycle_agent is not None:
                self._agent_objects[agent_id] = lifecycle_agent

        agent_status = self.agents.get(agent_id)
        if agent_status:
            agent_status.status = "active"
            return True

        return (
            self.lifecycle is not None
            and self.lifecycle.registry.get(agent_id) is not None
        )

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status

        Args:
            None

        Returns:
            System health dictionary
        """
        # Get metrics
        metrics = await self.get_metrics()

        # Calculate health indicators
        total_agents = len(self.agents)
        active_agents = sum(
            1 for a in self.agents.values() if a.status == "active"
        )
        failed_agents = sum(
            1 for a in self.agents.values() if a.status == "failed"
        )
        failed_tasks = sum(
            1 for t in self.tasks.values() if t.status == TaskStatus.FAILED
        )

        if self.lifecycle:
            lifecycle_statuses: Dict[str, str] = {}
            for agent in self.lifecycle.registry.list_all():
                lifecycle_status = await self.lifecycle.get_agent_status(
                    agent.agent_id
                )
                if lifecycle_status is not None:
                    lifecycle_statuses[agent.agent_id] = lifecycle_status

            total_agents = max(total_agents, len(lifecycle_statuses))
            active_agents = sum(
                1
                for status in lifecycle_statuses.values()
                if status == "active"
            )
            failed_agents = sum(
                1
                for status in lifecycle_statuses.values()
                if status == "failed"
            )

        # Determine overall health
        if total_agents == 0:
            health_status = "unknown"
        elif active_agents / total_agents > 0.8:
            health_status = "healthy"
        elif active_agents / total_agents > 0.5:
            health_status = "degraded"
        else:
            health_status = "unhealthy"

        return {
            "status": health_status,
            "total_agents": total_agents,
            "active_agents": active_agents,
            "failed_agents": failed_agents,
            "total_tasks": metrics.total_tasks,
            "completed_tasks": metrics.completed_tasks,
            "failed_tasks": failed_tasks,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def update_agent_status(
        self,
        agent_id: str,
        status: str,
    ) -> bool:
        """Update agent status

        Args:
            agent_id: Agent ID
            status: New status

        Returns:
            True if updated successfully
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return False

        agent.status = status
        agent.last_heartbeat = datetime.utcnow()

        return True


# Made with Bob
