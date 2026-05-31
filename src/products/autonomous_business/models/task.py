"""
Task model for Autonomous Business Platform
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status"""

    PENDING = "pending"  # Waiting to start
    RUNNING = "running"  # Currently executing
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Failed with error
    CANCELLED = "cancelled"  # Cancelled by user
    TIMEOUT = "timeout"  # Exceeded timeout
    WAITING = "waiting"  # Waiting for condition/approval


class TaskPriority(str, Enum):
    """Task priority levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(BaseModel):  # pylint: disable=too-many-instance-attributes
    """
    Task execution record

    Represents a single execution of a workflow step or agent action.
    """

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique task identifier",
    )

    workflow_id: str = Field(
        ...,
        description="Workflow that spawned this task",
    )

    workflow_execution_id: str = Field(
        ..., description="Specific workflow execution instance"
    )

    step_id: Optional[str] = Field(
        default=None, description="Workflow step ID (if from workflow)"
    )

    agent_id: Optional[str] = Field(
        default=None, description="Agent executing this task"
    )

    business_id: str = Field(..., description="Business that owns this task")

    # Task details
    type: str = Field(
        ..., description="Task type (e.g., 'send_email', 'create_invoice')"
    )

    name: str = Field(
        ...,
        description="Task name",
        min_length=1,
        max_length=200,
    )

    description: Optional[str] = Field(
        default=None,
        description="Task description",
    )

    # Status
    status: TaskStatus = Field(
        default=TaskStatus.PENDING, description="Current task status"
    )

    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM, description="Task priority"
    )

    # Input/Output
    input_data: Dict[str, Any] = Field(
        default_factory=dict, description="Input parameters for the task"
    )

    output_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Task output/results"
    )

    # Execution
    started_at: Optional[datetime] = Field(
        default=None, description="Task start timestamp"
    )

    completed_at: Optional[datetime] = Field(
        default=None, description="Task completion timestamp"
    )

    execution_time: Optional[float] = Field(
        default=None, description="Execution time in seconds"
    )

    # Error handling
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed",
    )

    error_details: Optional[Dict[str, Any]] = Field(
        default=None, description="Detailed error information"
    )

    retry_count: int = Field(default=0, description="Number of retry attempts")

    max_retries: int = Field(default=3, description="Maximum retry attempts")

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Task creation timestamp"
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    created_by: str = Field(..., description="User ID who created the task")

    # Context
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for task execution"
    )

    tags: list[str] = Field(default_factory=list, description="Task tags")

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for Task."""

        json_schema_extra = {
            "example": {
                "id": "task_123abc",
                "workflow_id": "wf_456def",
                "workflow_execution_id": "exec_789ghi",
                "step_id": "step_101",
                "agent_id": "email_agent",
                "business_id": "bus_202",
                "type": "send_email",
                "name": "Send welcome email to new lead",
                "status": "completed",
                "priority": "medium",
                "input_data": {
                    "to": "lead@example.com",
                    "subject": "Welcome!",
                    "template": "welcome",
                },
                "output_data": {
                    "message_id": "msg_303",
                    "sent_at": "2024-01-15T10:30:00Z",
                },
                "execution_time": 2.5,
            }
        }

    def start(self) -> None:
        """Mark task as started"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete(self, output_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark task as completed

        Args:
            output_data: Task output/results
        """
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        if output_data:
            self.output_data = output_data

        # Calculate execution time
        if self.started_at:
            self.execution_time = (
                self.completed_at - self.started_at
            ).total_seconds()

    def fail(
        self,
        error: str,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Mark task as failed

        Args:
            error: Error message
            error_details: Detailed error information
        """
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.error = error

        if error_details:
            self.error_details = error_details

        # Calculate execution time
        if self.started_at:
            self.execution_time = (
                self.completed_at - self.started_at
            ).total_seconds()

    def cancel(self) -> None:
        """Cancel the task"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        # Calculate execution time if started
        if self.started_at:
            self.execution_time = (
                self.completed_at - self.started_at
            ).total_seconds()

    def timeout(self) -> None:
        """Mark task as timed out"""
        self.status = TaskStatus.TIMEOUT
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.error = "Task exceeded timeout limit"

        # Calculate execution time
        if self.started_at:
            self.execution_time = (
                self.completed_at - self.started_at
            ).total_seconds()

    def retry(self) -> bool:
        """
        Attempt to retry the task

        Returns:
            True if retry is allowed, False if max retries reached
        """
        if self.retry_count >= self.max_retries:
            return False

        self.retry_count += 1
        self.status = TaskStatus.PENDING
        self.error = None
        self.error_details = None
        self.updated_at = datetime.utcnow()

        return True

    def wait(self) -> None:
        """Mark task as waiting"""
        self.status = TaskStatus.WAITING
        self.updated_at = datetime.utcnow()

    @property
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state"""
        return self.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        ]

    @property
    def is_successful(self) -> bool:
        """Check if task completed successfully"""
        return self.status == TaskStatus.COMPLETED

    @property
    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return (
            self.status == TaskStatus.FAILED
            and self.retry_count < self.max_retries
        )


# Made with Bob
