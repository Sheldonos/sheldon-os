"""
Base Agent Class

Defines the standard interface and functionality for all agents in Sheldon OS.
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class AgentState(Enum):
    """Agent operational states"""

    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    PAUSED = "paused"
    ERROR = "error"
    TERMINATED = "terminated"


class AgentCapability(Enum):
    """Standard agent capabilities"""

    # Core capabilities
    TASK_EXECUTION = "task_execution"
    DATA_PROCESSING = "data_processing"
    DECISION_MAKING = "decision_making"

    # Communication
    NATURAL_LANGUAGE = "natural_language"
    API_INTEGRATION = "api_integration"

    # Specialized
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"
    CONTENT_CREATION = "content_creation"
    RESEARCH = "research"
    PLANNING = "planning"
    MONITORING = "monitoring"

    # Business operations
    SALES = "sales"
    MARKETING = "marketing"
    CUSTOMER_SERVICE = "customer_service"
    FINANCE = "finance"

    # Technical
    DEPLOYMENT = "deployment"
    TESTING = "testing"
    DEBUGGING = "debugging"
    OPTIMIZATION = "optimization"


@dataclass
class AgentMetrics:
    """Agent performance metrics"""

    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    success_rate: float = 0.0
    last_active: Optional[datetime] = None

    def update(self, success: bool, execution_time: float):
        """Update metrics after task execution"""
        if success:
            self.tasks_completed += 1
        else:
            self.tasks_failed += 1

        self.total_execution_time += execution_time
        total_tasks = self.tasks_completed + self.tasks_failed
        self.average_execution_time = (
            self.total_execution_time / total_tasks if total_tasks > 0 else 0.0
        )
        self.success_rate = (
            self.tasks_completed / total_tasks if total_tasks > 0 else 0.0
        )
        self.last_active = datetime.utcnow()


class BaseAgent(ABC):  # pylint: disable=too-many-instance-attributes
    """Base class for all agents in Sheldon OS

    All agents must inherit from this class and implement the required methods.
    Provides standard interface for:
    - Task execution
    - State management
    - Communication
    - Error handling
    - Performance tracking
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_type: str = "base",
        capabilities: Optional[List[AgentCapability]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize base agent

        Args:
            agent_id: Unique agent identifier (generated if not provided)
            agent_type: Type of agent
            capabilities: List of agent capabilities
            config: Agent configuration
        """
        self.agent_id = agent_id or str(uuid.uuid4())
        self.agent_type = agent_type
        self.capabilities = capabilities or [AgentCapability.TASK_EXECUTION]
        self.config = config or {}

        # State management
        self.state = AgentState.INITIALIZING
        self.current_task: Optional[str] = None

        # Performance tracking
        self.metrics = AgentMetrics()

        # Communication
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.event_callbacks: Dict[str, List[Callable]] = {}

        # Lifecycle
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.stopped_at: Optional[datetime] = None

        # Context and memory
        self.context: Dict[str, Any] = {}
        self.memory: List[Dict[str, Any]] = []

        # Error tracking
        self.errors: List[Dict[str, Any]] = []

        # Background tasks
        self._running = False
        self._message_handler_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the agent"""
        if self._running:
            return

        self._running = True
        self.started_at = datetime.utcnow()
        self.state = AgentState.IDLE

        # Start message handler
        self._message_handler_task = asyncio.create_task(
            self._message_handler_loop()
        )

        # Call initialization hook
        await self.on_start()

        await self._emit_event("agent_started", {"agent_id": self.agent_id})

    async def stop(self):
        """Stop the agent"""
        if not self._running:
            return

        self._running = False
        self.stopped_at = datetime.utcnow()
        self.state = AgentState.TERMINATED

        # Cancel message handler
        if self._message_handler_task:
            self._message_handler_task.cancel()
            try:
                await self._message_handler_task
            except asyncio.CancelledError:
                pass

        # Call cleanup hook
        await self.on_stop()

        await self._emit_event("agent_stopped", {"agent_id": self.agent_id})

    async def execute_task(
        self,
        task_id: str,
        task_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a task

        Args:
            task_id: Task identifier
            task_data: Task data and parameters

        Returns:
            Task result
        """
        if self.state not in [AgentState.IDLE, AgentState.BUSY]:
            raise RuntimeError(
                f"Agent cannot execute task in state: {self.state}"
            )

        self.state = AgentState.BUSY
        self.current_task = task_id
        start_time = datetime.utcnow()

        try:
            # Execute task
            result = await self._execute_task_impl(task_data)

            # Update metrics
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.update(success=True, execution_time=execution_time)

            # Store in memory
            self.memory.append(
                {
                    "task_id": task_id,
                    "timestamp": start_time.isoformat(),
                    "execution_time": execution_time,
                    "success": True,
                    "result": result,
                }
            )

            await self._emit_event(
                "task_completed",
                {
                    "agent_id": self.agent_id,
                    "task_id": task_id,
                    "execution_time": execution_time,
                },
            )

            return result

        except Exception as e:
            # Handle error
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.update(success=False, execution_time=execution_time)

            error_info = {
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "error_type": type(e).__name__,
            }
            self.errors.append(error_info)

            await self._emit_event(
                "task_failed",
                {
                    "agent_id": self.agent_id,
                    "task_id": task_id,
                    "error": str(e),
                },
            )

            raise

        finally:
            self.state = AgentState.IDLE
            self.current_task = None

    async def send_message(self, message: Dict[str, Any]):
        """Send a message to the agent

        Args:
            message: Message data
        """
        await self.message_queue.put(message)

    def register_event_callback(self, event_type: str, callback: Callable):
        """Register a callback for an event type

        Args:
            event_type: Type of event
            callback: Callback function
        """
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)

    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has a capability

        Args:
            capability: Capability to check

        Returns:
            True if agent has capability
        """
        return capability in self.capabilities

    def get_status(self) -> Dict[str, Any]:
        """Get agent status

        Returns:
            Status dictionary
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "state": self.state.value,
            "current_task": self.current_task,
            "capabilities": [c.value for c in self.capabilities],
            "metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "tasks_failed": self.metrics.tasks_failed,
                "success_rate": self.metrics.success_rate,
                "average_execution_time": self.metrics.average_execution_time,
            },
            "uptime": (
                (datetime.utcnow() - self.started_at).total_seconds()
                if self.started_at
                else 0
            ),
            "created_at": self.created_at.isoformat(),
        }

    def update_context(self, key: str, value: Any):
        """Update agent context

        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value

    def get_context(self, key: Optional[str] = None) -> Any:
        """Get agent context

        Args:
            key: Context key (None for all context)

        Returns:
            Context value or full context
        """
        if key is None:
            return self.context
        return self.context.get(key)

    # Abstract methods that must be implemented by subclasses

    @abstractmethod
    async def _execute_task_impl(
        self, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute task implementation

        This method must be implemented by subclasses to define
        the actual task execution logic.

        Args:
            task_data: Task data and parameters

        Returns:
            Task result
        """
        raise NotImplementedError

    # Optional hooks that can be overridden by subclasses

    async def on_start(self):
        """Called when agent starts

        Override this method to perform initialization tasks.
        """
        return None

    async def on_stop(self):
        """Called when agent stops

        Override this method to perform cleanup tasks.
        """
        return None

    async def on_message(self, message: Dict[str, Any]):
        """Called when agent receives a message

        Override this method to handle custom messages.

        Args:
            message: Message data
        """
        _ = message
        return None

    # Internal methods

    async def _message_handler_loop(self):
        """Background task for handling messages"""
        while self._running:
            try:
                # Get message with timeout
                try:
                    message = await asyncio.wait_for(
                        self.message_queue.get(), timeout=1.0
                    )
                    await self.on_message(message)
                except asyncio.TimeoutError:
                    continue

            except asyncio.CancelledError:
                break
            except Exception as exc:  # pylint: disable=broad-exception-caught
                print(
                    f"Error in message handler for agent "
                    f"{self.agent_id}: {exc}"
                )
                await asyncio.sleep(1)

    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to registered callbacks

        Args:
            event_type: Type of event
            data: Event data
        """
        callbacks = self.event_callbacks.get(event_type, [])

        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                print(f"Error in event callback for {event_type}: {exc}")


# Made with Bob
