"""
Business entity model for Autonomous Business Platform
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class BusinessSize(str, Enum):
    """Business size categories"""

    SOLO = "solo"  # 1 person
    SMALL = "small"  # 2-10 people
    MEDIUM = "medium"  # 11-50 people


class Industry(str, Enum):
    """Industry categories"""

    CONSULTING = "consulting"
    ECOMMERCE = "ecommerce"
    CONTENT_CREATION = "content_creation"
    SOFTWARE = "software"
    MARKETING = "marketing"
    DESIGN = "design"
    COACHING = "coaching"
    REAL_ESTATE = "real_estate"
    FINANCE = "finance"
    LEGAL = "legal"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    OTHER = "other"


class SubscriptionTier(str, Enum):
    """Subscription tiers"""

    FREE = "free"  # Trial/limited
    STARTER = "starter"  # $49/month
    PROFESSIONAL = "professional"  # $149/month
    ENTERPRISE = "enterprise"  # $499/month


class BusinessConfig(BaseModel):
    """Business configuration settings"""

    # Agent settings
    active_agents: List[str] = Field(
        default_factory=list, description="List of active agent IDs"
    )
    agent_settings: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Agent-specific configuration"
    )

    # Integration settings
    integrations: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Connected tool integrations"
    )

    # Workflow settings
    auto_workflows: bool = Field(
        default=True, description="Enable automatic workflow execution"
    )
    workflow_notifications: bool = Field(
        default=True, description="Send workflow notifications"
    )

    # Business hours
    business_hours: Dict[str, Any] = Field(
        default_factory=lambda: {
            "timezone": "UTC",
            "monday": {"start": "09:00", "end": "17:00"},
            "tuesday": {"start": "09:00", "end": "17:00"},
            "wednesday": {"start": "09:00", "end": "17:00"},
            "thursday": {"start": "09:00", "end": "17:00"},
            "friday": {"start": "09:00", "end": "17:00"},
            "saturday": None,
            "sunday": None,
        },
        description="Business operating hours",
    )

    # Notification preferences
    notifications: Dict[str, bool] = Field(
        default_factory=lambda: {
            "email": True,
            "slack": False,
            "sms": False,
            "push": True,
        },
        description="Notification channel preferences",
    )

    # ROI tracking
    track_roi: bool = Field(default=True, description="Enable ROI tracking")
    hourly_rate: Optional[float] = Field(
        default=None, description="User's hourly rate for ROI calculation"
    )


class Business(BaseModel):  # pylint: disable=no-member
    """
    Business entity representing a user's business

    This is the core entity that owns agents, workflows, and integrations.
    """

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique business identifier",
    )

    name: str = Field(
        ...,
        description="Business name",
        min_length=1,
        max_length=200,
    )

    owner_id: str = Field(..., description="User ID of the business owner")

    industry: Industry = Field(
        default=Industry.OTHER,
        description="Business industry",
    )

    size: BusinessSize = Field(
        default=BusinessSize.SOLO,
        description="Business size",
    )

    description: Optional[str] = Field(
        default=None, description="Business description", max_length=1000
    )

    website: Optional[str] = Field(
        default=None,
        description="Business website URL",
    )

    # Subscription
    subscription_tier: SubscriptionTier = Field(
        default=SubscriptionTier.FREE, description="Current subscription tier"
    )

    subscription_started: datetime = Field(
        default_factory=datetime.utcnow, description="Subscription start date"
    )

    subscription_expires: Optional[datetime] = Field(
        default=None, description="Subscription expiration date"
    )

    # Configuration
    config: BusinessConfig = Field(
        default_factory=BusinessConfig, description="Business configuration"
    )

    # Metrics
    monthly_savings: float = Field(
        default=0.0,
        description="Estimated monthly savings from automation (USD)",
    )

    time_saved_hours: float = Field(
        default=0.0, description="Total hours saved through automation"
    )

    roi_percentage: float = Field(
        default=0.0, description="Return on investment percentage"
    )

    tasks_automated: int = Field(
        default=0, description="Total number of tasks automated"
    )

    workflows_active: int = Field(
        default=0,
        description="Number of active workflows",
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Business creation timestamp",
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    last_activity: Optional[datetime] = Field(
        default=None, description="Last activity timestamp"
    )

    # Status
    is_active: bool = Field(
        default=True,
        description="Whether the business is active",
    )

    is_onboarded: bool = Field(
        default=False, description="Whether onboarding is complete"
    )

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for Business."""

        json_schema_extra = {
            "example": {
                "id": "bus_123abc",
                "name": "Acme Consulting",
                "owner_id": "user_456def",
                "industry": "consulting",
                "size": "solo",
                "description": "Digital marketing consulting for SMBs",
                "website": "https://acmeconsulting.com",
                "subscription_tier": "professional",
                "monthly_savings": 2500.00,
                "time_saved_hours": 80.0,
                "roi_percentage": 1567.0,
                "tasks_automated": 245,
                "workflows_active": 12,
                "is_active": True,
                "is_onboarded": True,
            }
        }

    def calculate_roi(self) -> float:
        """
        Calculate ROI based on time saved and subscription cost

        Returns:
            ROI percentage
        """
        config = self.config  # pylint: disable=no-member
        hourly_rate = config.hourly_rate
        if not hourly_rate:
            return 0.0

        # Calculate monthly value of time saved
        monthly_value = self.time_saved_hours * hourly_rate

        # Get subscription cost
        tier_costs = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.STARTER: 49,
            SubscriptionTier.PROFESSIONAL: 149,
            SubscriptionTier.ENTERPRISE: 499,
        }
        monthly_cost = tier_costs.get(self.subscription_tier, 0)

        if monthly_cost == 0:
            return 0.0

        # ROI = (Value - Cost) / Cost * 100
        roi = ((monthly_value - monthly_cost) / monthly_cost) * 100
        return round(roi, 2)

    def update_metrics(
        self,
        time_saved: float = 0.0,
        tasks_completed: int = 0,
    ) -> None:
        """
        Update business metrics

        Args:
            time_saved: Hours saved in this update
            tasks_completed: Number of tasks completed
        """
        self.time_saved_hours += time_saved
        self.tasks_automated += tasks_completed

        # Recalculate ROI
        self.roi_percentage = self.calculate_roi()

        # Update monthly savings
        config = self.config  # pylint: disable=no-member
        hourly_rate = config.hourly_rate
        if hourly_rate:
            self.monthly_savings = self.time_saved_hours * hourly_rate

        self.updated_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()

    def add_agent(
        self, agent_id: str, settings: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add an agent to the business

        Args:
            agent_id: Agent identifier
            settings: Agent-specific settings
        """
        config = self.config  # pylint: disable=no-member
        active_agents = config.active_agents
        agent_settings = config.agent_settings

        if agent_id not in active_agents:
            active_agents.append(agent_id)

        if settings:
            agent_settings[agent_id] = settings

        self.updated_at = datetime.utcnow()

    def remove_agent(self, agent_id: str) -> None:
        """
        Remove an agent from the business

        Args:
            agent_id: Agent identifier
        """
        config = self.config  # pylint: disable=no-member
        active_agents = config.active_agents
        agent_settings = config.agent_settings

        if agent_id in active_agents:
            active_agents.remove(agent_id)

        if agent_id in agent_settings:
            del agent_settings[agent_id]

        self.updated_at = datetime.utcnow()

    def add_integration(
        self, integration_name: str, credentials: Dict[str, Any]
    ) -> None:
        """
        Add a tool integration

        Args:
            integration_name: Name of the integration
                (e.g., 'hubspot', 'gmail')
            credentials: Integration credentials and settings
        """
        config = self.config  # pylint: disable=no-member
        integrations = config.integrations
        integrations[integration_name] = credentials
        self.updated_at = datetime.utcnow()

    def remove_integration(self, integration_name: str) -> None:
        """
        Remove a tool integration

        Args:
            integration_name: Name of the integration
        """
        config = self.config  # pylint: disable=no-member
        integrations = config.integrations
        if integration_name in integrations:
            del integrations[integration_name]

        self.updated_at = datetime.utcnow()

    def is_integration_active(self, integration_name: str) -> bool:
        """
        Check if an integration is active

        Args:
            integration_name: Name of the integration

        Returns:
            True if integration is configured
        """
        config = self.config  # pylint: disable=no-member
        integrations = config.integrations
        return integration_name in integrations


# Made with Bob
