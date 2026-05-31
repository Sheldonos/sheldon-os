"""
Workflow model for Autonomous Business Platform
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Workflow status"""

    DRAFT = "draft"  # Being created/edited
    ACTIVE = "active"  # Running
    PAUSED = "paused"  # Temporarily stopped
    ARCHIVED = "archived"  # No longer in use


class TriggerType(str, Enum):
    """Workflow trigger types"""

    MANUAL = "manual"  # User-initiated
    SCHEDULE = "schedule"  # Time-based (cron)
    EVENT = "event"  # Event-driven (webhook, integration event)
    CONDITION = "condition"  # Condition-based


class StepType(str, Enum):
    """Workflow step types"""

    AGENT_ACTION = "agent_action"  # Execute agent action
    API_CALL = "api_call"  # Make API request
    CONDITION = "condition"  # Conditional branching
    LOOP = "loop"  # Iterate over items
    WAIT = "wait"  # Wait for duration or condition
    HUMAN_APPROVAL = "human_approval"  # Require human approval
    NOTIFICATION = "notification"  # Send notification
    DATA_TRANSFORM = "data_transform"  # Transform data


class WorkflowTrigger(BaseModel):
    """Workflow trigger configuration"""

    type: TriggerType = Field(..., description="Trigger type")

    # Schedule trigger
    schedule: Optional[str] = Field(
        default=None, description="Cron expression for scheduled triggers"
    )

    # Event trigger
    event_type: Optional[str] = Field(
        default=None, description="Event type to listen for"
    )

    event_source: Optional[str] = Field(
        default=None, description="Event source (integration name)"
    )

    # Condition trigger
    condition: Optional[Dict[str, Any]] = Field(
        default=None, description="Condition expression"
    )

    # Configuration
    enabled: bool = Field(
        default=True,
        description="Whether trigger is enabled",
    )

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for WorkflowTrigger."""

        json_schema_extra = {
            "example": {
                "type": "schedule",
                "schedule": "0 9 * * 1-5",  # 9 AM weekdays
                "enabled": True,
            }
        }


class WorkflowStep(BaseModel):
    """Individual step in a workflow"""

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Step identifier",
    )

    name: str = Field(
        ...,
        description="Step name",
        min_length=1,
        max_length=200,
    )

    type: StepType = Field(..., description="Step type")

    # Agent action
    agent_id: Optional[str] = Field(
        default=None, description="Agent to execute (for agent_action type)"
    )

    action: Optional[str] = Field(
        default=None,
        description="Action to perform",
    )

    # API call
    api_endpoint: Optional[str] = Field(
        default=None,
        description="API endpoint URL",
    )

    api_method: Optional[str] = Field(
        default=None, description="HTTP method (GET, POST, etc.)"
    )

    api_headers: Optional[Dict[str, str]] = Field(
        default=None, description="API request headers"
    )

    # Input/Output
    input_mapping: Dict[str, Any] = Field(
        default_factory=dict, description="Input parameter mapping"
    )

    output_mapping: Dict[str, Any] = Field(
        default_factory=dict, description="Output variable mapping"
    )

    # Condition
    condition_expression: Optional[str] = Field(
        default=None, description="Condition expression (for condition type)"
    )

    on_true: Optional[str] = Field(
        default=None, description="Next step ID if condition is true"
    )

    on_false: Optional[str] = Field(
        default=None, description="Next step ID if condition is false"
    )

    # Loop
    loop_items: Optional[str] = Field(
        default=None, description="Variable containing items to loop over"
    )

    loop_variable: Optional[str] = Field(
        default=None, description="Variable name for current item"
    )

    # Wait
    wait_duration: Optional[int] = Field(
        default=None, description="Wait duration in seconds"
    )

    wait_condition: Optional[str] = Field(
        default=None, description="Condition to wait for"
    )

    # Error handling
    on_error: Optional[str] = Field(
        default=None,
        description="Next step ID on error (or 'retry', 'skip', 'fail')",
    )

    retry_count: int = Field(
        default=0,
        description="Number of retries on failure",
    )

    retry_delay: int = Field(
        default=60,
        description="Delay between retries in seconds",
    )

    # Execution
    timeout: int = Field(default=300, description="Step timeout in seconds")

    next_step: Optional[str] = Field(
        default=None, description="Next step ID (for linear flow)"
    )

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for WorkflowStep."""

        json_schema_extra = {
            "example": {
                "id": "step_123",
                "name": "Send welcome email",
                "type": "agent_action",
                "agent_id": "email_agent",
                "action": "send_email",
                "input_mapping": {
                    "to": "{{contact.email}}",
                    "subject": "Welcome!",
                    "template": "welcome_template",
                },
                "timeout": 60,
                "next_step": "step_124",
            }
        }


class Workflow(BaseModel):  # pylint: disable=too-many-instance-attributes,no-member
    """
    Workflow definition for business automation

    Workflows orchestrate multiple agents and integrations to automate
    complex business processes.
    """

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique workflow identifier",
    )

    business_id: str = Field(
        ...,
        description="Business that owns this workflow",
    )

    name: str = Field(
        ...,
        description="Workflow name",
        min_length=1,
        max_length=200,
    )

    description: Optional[str] = Field(
        default=None,
        description="Workflow description",
        max_length=1000,
    )

    # Trigger
    trigger: WorkflowTrigger = Field(
        ...,
        description="Workflow trigger configuration",
    )

    # Steps
    steps: List[WorkflowStep] = Field(
        default_factory=list, description="Workflow steps"
    )

    start_step: Optional[str] = Field(
        default=None, description="ID of the first step to execute"
    )

    # Agents involved
    agents_involved: List[str] = Field(
        default_factory=list,
        description="List of agent IDs used in this workflow",
    )

    # Status
    status: WorkflowStatus = Field(
        default=WorkflowStatus.DRAFT, description="Workflow status"
    )

    # Metrics
    execution_count: int = Field(
        default=0,
        description="Total number of executions",
    )

    success_count: int = Field(
        default=0,
        description="Number of successful executions",
    )

    failure_count: int = Field(
        default=0,
        description="Number of failed executions",
    )

    avg_execution_time: float = Field(
        default=0.0, description="Average execution time in seconds"
    )

    last_execution: Optional[datetime] = Field(
        default=None, description="Last execution timestamp"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Workflow creation timestamp"
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    created_by: str = Field(
        ...,
        description="User ID who created the workflow",
    )

    # Tags and categorization
    tags: List[str] = Field(
        default_factory=list,
        description="Workflow tags for organization",
    )

    category: Optional[str] = Field(
        default=None,
        description="Workflow category (e.g., 'sales', 'marketing')"
    )

    # Template
    is_template: bool = Field(
        default=False, description="Whether this is a template workflow"
    )

    template_id: Optional[str] = Field(
        default=None, description="Template ID if created from template"
    )

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for Workflow."""

        json_schema_extra = {
            "example": {
                "id": "wf_123abc",
                "business_id": "bus_456def",
                "name": "Lead Nurture Sequence",
                "description": "Automated email sequence for new leads",
                "status": "active",
                "execution_count": 1247,
                "success_count": 1198,
                "failure_count": 49,
                "avg_execution_time": 45.3,
                "tags": ["sales", "email", "automation"],
                "category": "sales",
            }
        }

    @property
    def success_rate(self) -> float:
        """Calculate workflow success rate"""
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100

    def add_step(self, step: WorkflowStep) -> None:
        """
        Add a step to the workflow

        Args:
            step: WorkflowStep to add
        """
        steps: List[WorkflowStep] = self.steps  # pylint: disable=no-member
        steps.append(step)

        # Update agents_involved
        if step.agent_id and step.agent_id not in self.agents_involved:
            self.agents_involved.append(step.agent_id)

        # Set as start step if first step
        if len(self.steps) == 1:
            self.start_step = step.id

        self.updated_at = datetime.utcnow()

    def remove_step(self, step_id: str) -> None:
        """
        Remove a step from the workflow

        Args:
            step_id: ID of step to remove
        """
        self.steps = [s for s in self.steps if s.id != step_id]

        # Update start_step if removed
        if self.start_step == step_id:
            self.start_step = self.steps[0].id if self.steps else None

        # Update next_step references
        for step in self.steps:
            if step.next_step == step_id:
                step.next_step = None

        self.updated_at = datetime.utcnow()

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """
        Get a step by ID

        Args:
            step_id: Step identifier

        Returns:
            WorkflowStep or None if not found
        """
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def activate(self) -> None:
        """Activate the workflow"""
        self.status = WorkflowStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def pause(self) -> None:
        """Pause the workflow"""
        self.status = WorkflowStatus.PAUSED
        self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """Archive the workflow"""
        self.status = WorkflowStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def record_execution(self, success: bool, execution_time: float) -> None:
        """
        Record a workflow execution

        Args:
            success: Whether execution was successful
            execution_time: Execution time in seconds
        """
        self.execution_count += 1

        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

        # Update average execution time
        total_time = self.avg_execution_time * (self.execution_count - 1)
        self.avg_execution_time = (
            total_time + execution_time
        ) / self.execution_count

        self.last_execution = datetime.utcnow()
        self.updated_at = datetime.utcnow()


# Made with Bob
