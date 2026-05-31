"""
Tool Usage Data Models

Models for tracking AI tool usage and metrics.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UsageStatus(str, Enum):
    """Usage status enumeration."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    INSUFFICIENT_CREDITS = "insufficient_credits"


class ToolUsage(BaseModel):
    """
    Tool usage record.

    Tracks individual tool executions for billing and analytics.
    """

    # Identity
    id: str = Field(..., description="Unique usage ID")
    user_id: str = Field(..., description="User who executed the tool")
    tool_id: str = Field(..., description="Tool that was executed")
    capability: str = Field(..., description="Capability that was used")

    # Execution details
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Execution timestamp"
    )
    execution_time: float = Field(
        ..., description="Execution time in milliseconds", ge=0
    )
    status: UsageStatus = Field(..., description="Execution status")

    # Input/Output
    input_data: Dict[str, Any] = Field(
        ...,
        description="Input data (sanitized)",
    )
    output_data: Optional[Dict[str, Any]] = Field(
        None, description="Output data (sanitized)"
    )
    input_size: int = Field(
        ...,
        description="Input size in bytes",
        ge=0,
    )
    output_size: int = Field(
        default=0,
        description="Output size in bytes",
        ge=0,
    )

    # Usage metrics (depends on pricing model)
    tokens_used: Optional[int] = Field(
        None,
        description="Tokens used (for LLMs)",
        ge=0,
    )
    minutes_used: Optional[float] = Field(
        None, description="Minutes used (for audio/video)", ge=0
    )
    mb_processed: Optional[float] = Field(
        None, description="MB processed (for data)", ge=0
    )
    images_generated: Optional[int] = Field(
        None,
        description="Images generated",
        ge=0,
    )

    # Cost
    cost: float = Field(..., description="Cost in USD", ge=0)
    credits_used: float = Field(..., description="Credits deducted", ge=0)

    # Error handling
    error_message: Optional[str] = Field(
        None,
        description="Error message if failed",
    )
    error_code: Optional[str] = Field(
        None,
        description="Error code if failed",
    )
    retry_count: int = Field(default=0, description="Number of retries", ge=0)

    # Context
    session_id: Optional[str] = Field(
        None,
        description="Session ID for grouping",
    )
    workflow_id: Optional[str] = Field(
        None, description="Workflow ID if part of workflow"
    )
    agent_id: Optional[str] = Field(
        None,
        description="Agent ID if executed by agent",
    )

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization",
    )

    # Performance
    queue_time: Optional[float] = Field(
        None, description="Time spent in queue (ms)", ge=0
    )
    network_time: Optional[float] = Field(
        None, description="Network latency (ms)", ge=0
    )
    processing_time: Optional[float] = Field(
        None, description="Actual processing time (ms)", ge=0
    )

    def is_successful(self) -> bool:
        """Check if usage was successful."""
        return self.status == UsageStatus.SUCCESS

    def get_total_time(self) -> float:
        """Get total time including queue and network."""
        total = self.execution_time
        if self.queue_time:
            total += self.queue_time
        if self.network_time:
            total += self.network_time
        return total

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for ToolUsage."""

        json_schema_extra = {
            "example": {
                "id": "usage_abc123",
                "user_id": "user_456",
                "tool_id": "tool_gpt4_turbo",
                "capability": "chat_completion",
                "timestamp": "2024-01-15T10:30:00Z",
                "execution_time": 1250.5,
                "status": "success",
                "input_data": {"prompt": "Hello world"},
                "output_data": {"text": "Hello! How can I help?"},
                "input_size": 1024,
                "output_size": 2048,
                "tokens_used": 150,
                "cost": 0.0015,
                "credits_used": 0.0015,
            }
        }


class UsageMetrics(BaseModel):
    """
    Aggregated usage metrics.

    Summary statistics for a time period.
    """

    # Time period
    period_start: datetime = Field(..., description="Period start")
    period_end: datetime = Field(..., description="Period end")

    # Identifiers
    user_id: Optional[str] = Field(
        None,
        description="User ID (if user-specific)",
    )
    tool_id: Optional[str] = Field(
        None,
        description="Tool ID (if tool-specific)",
    )

    # Usage counts
    total_calls: int = Field(default=0, description="Total API calls", ge=0)
    successful_calls: int = Field(
        default=0,
        description="Successful calls",
        ge=0,
    )
    failed_calls: int = Field(default=0, description="Failed calls", ge=0)

    # Performance
    avg_execution_time: float = Field(
        default=0.0, description="Average execution time (ms)", ge=0
    )
    p50_execution_time: float = Field(
        default=0.0, description="P50 execution time (ms)", ge=0
    )
    p95_execution_time: float = Field(
        default=0.0, description="P95 execution time (ms)", ge=0
    )
    p99_execution_time: float = Field(
        default=0.0, description="P99 execution time (ms)", ge=0
    )

    # Success rate
    success_rate: float = Field(
        default=0.0, description="Success rate (0-1)", ge=0, le=1
    )

    # Resource usage
    total_tokens: int = Field(default=0, description="Total tokens used", ge=0)
    total_minutes: float = Field(
        default=0.0,
        description="Total minutes used",
        ge=0,
    )
    total_mb: float = Field(
        default=0.0,
        description="Total MB processed",
        ge=0,
    )

    # Cost
    total_cost: float = Field(
        default=0.0,
        description="Total cost in USD",
        ge=0,
    )
    total_credits: float = Field(
        default=0.0,
        description="Total credits used",
        ge=0,
    )
    avg_cost_per_call: float = Field(
        default=0.0, description="Average cost per call", ge=0
    )

    # Error analysis
    error_breakdown: Dict[str, int] = Field(
        default_factory=dict, description="Error counts by type"
    )

    # Top capabilities
    top_capabilities: List[Dict[str, Any]] = Field(
        default_factory=list, description="Most used capabilities"
    )

    def calculate_success_rate(self):
        """Calculate success rate."""
        if self.total_calls == 0:
            self.success_rate = 0.0
        else:
            self.success_rate = self.successful_calls / self.total_calls

    def calculate_avg_cost(self):
        """Calculate average cost per call."""
        if self.total_calls == 0:
            self.avg_cost_per_call = 0.0
        else:
            self.avg_cost_per_call = self.total_cost / self.total_calls

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for UsageSummary."""

        json_schema_extra = {
            "example": {
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-01-31T23:59:59Z",
                "user_id": "user_456",
                "total_calls": 1000,
                "successful_calls": 980,
                "failed_calls": 20,
                "avg_execution_time": 1250.5,
                "success_rate": 0.98,
                "total_tokens": 150000,
                "total_cost": 150.00,
                "avg_cost_per_call": 0.15,
            }
        }


class UsageAggregation(BaseModel):
    """
    Usage aggregation for analytics.

    Flexible aggregation by different dimensions.
    """

    # Aggregation metadata
    aggregation_type: str = Field(
        ..., description="Type of aggregation (hourly, daily, weekly, monthly)"
    )
    timestamp: datetime = Field(..., description="Aggregation timestamp")

    # Dimensions
    dimensions: Dict[str, str] = Field(
        ..., description="Aggregation dimensions (user_id, tool_id, etc.)"
    )

    # Metrics
    metrics: UsageMetrics = Field(..., description="Aggregated metrics")

    # Trends
    trend_vs_previous: Optional[float] = Field(
        None, description="% change vs previous period"
    )
    trend_direction: Optional[str] = Field(
        None,
        description="up, down, or stable",
    )

    # Forecasting
    forecasted_next_period: Optional[float] = Field(
        None, description="Forecasted usage for next period"
    )
    confidence_interval: Optional[Dict[str, float]] = Field(
        None, description="Confidence interval"
    )

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for UsageAggregation."""

        json_schema_extra = {
            "example": {
                "aggregation_type": "daily",
                "timestamp": "2024-01-15T00:00:00Z",
                "dimensions": {
                    "user_id": "user_456",
                    "tool_id": "tool_gpt4_turbo",
                },
                "metrics": {
                    "total_calls": 100,
                    "successful_calls": 98,
                    "total_cost": 15.00,
                },
                "trend_vs_previous": 15.5,
                "trend_direction": "up",
            }
        }


class UsageAlert(BaseModel):
    """
    Usage alert for monitoring.

    Alerts for unusual usage patterns or threshold breaches.
    """

    id: str = Field(..., description="Alert ID")
    user_id: str = Field(..., description="User ID")
    alert_type: str = Field(
        ...,
        description="Alert type (cost, rate_limit, anomaly)",
    )
    severity: str = Field(
        ...,
        description="Severity (info, warning, critical)",
    )

    # Alert details
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    threshold: Optional[float] = Field(
        None,
        description="Threshold that was breached",
    )
    current_value: Optional[float] = Field(None, description="Current value")

    # Context
    tool_id: Optional[str] = Field(None, description="Related tool ID")
    time_window: Optional[str] = Field(
        None, description="Time window (e.g., '1h', '24h')"
    )

    # Status
    acknowledged: bool = Field(
        default=False,
        description="Has been acknowledged",
    )
    resolved: bool = Field(
        default=False,
        description="Has been resolved",
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = Field(None)
    resolved_at: Optional[datetime] = Field(None)

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for UsageAlert."""

        json_schema_extra = {
            "example": {
                "id": "alert_789",
                "user_id": "user_456",
                "alert_type": "cost",
                "severity": "warning",
                "title": "High usage detected",
                "message": (
                    "Your usage has exceeded 80% of your monthly budget"
                ),
                "threshold": 100.0,
                "current_value": 85.0,
                "time_window": "24h",
                "acknowledged": False,
                "resolved": False,
            }
        }


class UsageQuota(BaseModel):  # pylint: disable=too-many-instance-attributes
    """
    Usage quota for rate limiting.

    Tracks quotas and limits for users.
    """

    user_id: str = Field(..., description="User ID")
    tool_id: Optional[str] = Field(
        None,
        description="Tool ID (if tool-specific)",
    )

    # Quota limits
    calls_per_minute: int = Field(..., description="Calls per minute limit")
    calls_per_hour: int = Field(..., description="Calls per hour limit")
    calls_per_day: int = Field(..., description="Calls per day limit")

    # Current usage
    current_minute_calls: int = Field(
        default=0, description="Calls in current minute", ge=0
    )
    current_hour_calls: int = Field(
        default=0, description="Calls in current hour", ge=0
    )
    current_day_calls: int = Field(
        default=0,
        description="Calls in current day",
        ge=0,
    )

    # Reset times
    minute_reset_at: datetime = Field(
        ...,
        description="When minute counter resets",
    )
    hour_reset_at: datetime = Field(
        ...,
        description="When hour counter resets",
    )
    day_reset_at: datetime = Field(
        ...,
        description="When day counter resets",
    )

    # Status
    is_rate_limited: bool = Field(
        default=False,
        description="Currently rate limited",
    )
    rate_limit_until: Optional[datetime] = Field(
        None,
        description="Rate limited until",
    )

    def check_rate_limit(self) -> bool:
        """Check if user is within rate limits."""
        now = datetime.utcnow()

        # Reset counters if needed
        if now >= self.minute_reset_at:
            self.current_minute_calls = 0
            self.minute_reset_at = now.replace(second=0, microsecond=0)

        if now >= self.hour_reset_at:
            self.current_hour_calls = 0
            self.hour_reset_at = now.replace(minute=0, second=0, microsecond=0)

        if now >= self.day_reset_at:
            self.current_day_calls = 0
            self.day_reset_at = now.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

        # Check limits
        if self.current_minute_calls >= self.calls_per_minute:
            self.is_rate_limited = True
            self.rate_limit_until = self.minute_reset_at
            return False

        if self.current_hour_calls >= self.calls_per_hour:
            self.is_rate_limited = True
            self.rate_limit_until = self.hour_reset_at
            return False

        if self.current_day_calls >= self.calls_per_day:
            self.is_rate_limited = True
            self.rate_limit_until = self.day_reset_at
            return False

        self.is_rate_limited = False
        self.rate_limit_until = None
        return True

    def increment_usage(self):
        """Increment usage counters."""
        self.current_minute_calls += 1
        self.current_hour_calls += 1
        self.current_day_calls += 1

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for UsageQuota."""

        json_schema_extra = {
            "example": {
                "user_id": "user_456",
                "calls_per_minute": 100,
                "calls_per_hour": 1000,
                "calls_per_day": 10000,
                "current_minute_calls": 45,
                "current_hour_calls": 523,
                "current_day_calls": 3421,
                "is_rate_limited": False,
            }
        }


# Made with Bob
