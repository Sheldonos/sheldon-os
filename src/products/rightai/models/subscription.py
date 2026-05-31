"""
Subscription Data Models

Models for platform subscriptions and credit management.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SubscriptionTierEnum(str, Enum):
    """Subscription tier enumeration."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration."""

    ACTIVE = "active"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


class SubscriptionTier(BaseModel):
    """
    Subscription tier definition.

    Defines features and limits for a subscription tier.
    """

    # Identity
    id: str = Field(..., description="Tier ID")
    name: str = Field(..., description="Tier name")
    slug: SubscriptionTierEnum = Field(..., description="Tier slug")

    # Pricing
    price: float = Field(..., description="Monthly price", ge=0)
    annual_price: Optional[float] = Field(
        None, description="Annual price (if different)", ge=0
    )
    currency: str = Field(default="USD", description="Currency code")

    # Credits
    monthly_credits: float = Field(
        ...,
        description="Monthly credits included",
        ge=0,
    )
    rollover_credits: bool = Field(
        default=False,
        description="Can credits roll over",
    )
    max_rollover: Optional[float] = Field(
        None,
        description="Max rollover amount",
    )

    # Overage
    overage_rate: float = Field(
        ...,
        description="Cost per credit over limit",
        ge=0,
    )
    overage_allowed: bool = Field(
        default=True,
        description="Allow overage usage",
    )

    # Features
    features: List[str] = Field(
        ...,
        description="Included features",
    )

    # Rate limits
    rate_limit_multiplier: float = Field(
        default=1.0,
        description="Rate limit multiplier",
        ge=0,
    )

    # Support
    support_level: str = Field(
        ...,
        description="Support level (basic, priority, dedicated)",
    )
    support_response_time: str = Field(
        ...,
        description="Support response time SLA",
    )

    # Limits
    max_team_members: Optional[int] = Field(
        None,
        description="Max team members",
    )
    max_projects: Optional[int] = Field(
        None,
        description="Max projects",
    )
    max_api_keys: Optional[int] = Field(
        None,
        description="Max API keys",
    )

    # Analytics
    analytics_retention_days: int = Field(
        ...,
        description="Analytics data retention",
        ge=0,
    )

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_annual_savings(self) -> float:
        """Calculate annual savings percentage."""
        if not self.annual_price:
            return 0.0
        monthly_total = self.price * 12
        if monthly_total == 0:
            return 0.0
        return ((monthly_total - self.annual_price) / monthly_total) * 100

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for SubscriptionTier."""

        json_schema_extra = {
            "example": {
                "id": "tier_pro",
                "name": "Pro",
                "slug": "pro",
                "price": 49.00,
                "annual_price": 490.00,
                "monthly_credits": 1000,
                "rollover_credits": True,
                "max_rollover": 2000,
                "overage_rate": 0.05,
                "features": [
                    "All Free features",
                    "1,000 monthly credits",
                    "Priority support",
                    "Advanced analytics",
                ],
                "support_level": "priority",
                "support_response_time": "4 hours",
            }
        }


class PlatformSubscription(BaseModel):
    """
    Platform subscription model.

    Represents a user's subscription to the Right.ai platform.
    """

    # Identity
    id: str = Field(..., description="Subscription ID")
    user_id: str = Field(..., description="User ID")

    # Tier
    tier: SubscriptionTierEnum = Field(..., description="Subscription tier")
    tier_id: str = Field(..., description="Tier definition ID")

    # Billing
    billing_cycle: str = Field(
        default="monthly", description="Billing cycle (monthly, annual)"
    )
    price: float = Field(..., description="Subscription price", ge=0)
    currency: str = Field(default="USD", description="Currency code")

    # Credits
    monthly_credits: float = Field(
        ...,
        description="Monthly credits allocation",
        ge=0,
    )
    used_credits: float = Field(
        default=0.0,
        description="Credits used this period",
        ge=0,
    )
    remaining_credits: float = Field(
        ...,
        description="Credits remaining",
        ge=0,
    )
    rollover_credits: float = Field(
        default=0.0,
        description="Rolled over credits",
        ge=0,
    )

    # Overage
    overage_rate: float = Field(
        ...,
        description="Overage rate per credit",
        ge=0,
    )
    overage_used: float = Field(
        default=0.0,
        description="Overage credits used",
        ge=0,
    )
    overage_cost: float = Field(
        default=0.0,
        description="Overage cost",
        ge=0,
    )

    # Features
    features: List[str] = Field(..., description="Enabled features")

    # Status
    status: SubscriptionStatus = Field(
        default=SubscriptionStatus.ACTIVE,
        description="Subscription status",
    )

    # Dates
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Subscription start date",
    )
    current_period_start: datetime = Field(
        default_factory=datetime.utcnow,
        description="Current period start",
    )
    current_period_end: datetime = Field(
        ...,
        description="Current period end",
    )
    renews_at: datetime = Field(..., description="Next renewal date")
    trial_end: Optional[datetime] = Field(
        None,
        description="Trial end date",
    )
    cancelled_at: Optional[datetime] = Field(
        None,
        description="Cancellation date",
    )
    ends_at: Optional[datetime] = Field(
        None,
        description="Subscription end date",
    )

    # Cancellation
    cancel_at_period_end: bool = Field(
        default=False,
        description="Cancel at period end",
    )
    cancellation_reason: Optional[str] = Field(
        None,
        description="Cancellation reason",
    )

    # Payment
    payment_method_id: Optional[str] = Field(
        None,
        description="Default payment method",
    )

    # External IDs
    stripe_subscription_id: Optional[str] = Field(
        None,
        description="Stripe subscription ID",
    )
    stripe_customer_id: Optional[str] = Field(
        None,
        description="Stripe customer ID",
    )

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status == SubscriptionStatus.ACTIVE

    def is_trial(self) -> bool:
        """Check if subscription is in trial."""
        if not self.trial_end:
            return False
        return datetime.utcnow() < self.trial_end

    def days_until_renewal(self) -> int:
        """Calculate days until renewal."""
        delta = self.renews_at - datetime.utcnow()
        return max(0, delta.days)

    def credit_usage_percentage(self) -> float:
        """Calculate credit usage percentage."""
        total = self.monthly_credits + self.rollover_credits
        if total == 0:
            return 0.0
        return (self.used_credits / total) * 100

    def has_feature(self, feature: str) -> bool:
        """Check if subscription has a feature."""
        return feature in self.features

    def reset_credits(self):
        """Reset credits for new billing period."""
        # Handle rollover
        if self.rollover_credits > 0:
            unused = self.remaining_credits
            self.rollover_credits = min(unused, self.rollover_credits)
        else:
            self.rollover_credits = 0.0

        # Reset counters
        self.used_credits = 0.0
        self.remaining_credits = self.monthly_credits + self.rollover_credits
        self.overage_used = 0.0
        self.overage_cost = 0.0

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for PlatformSubscription."""

        json_schema_extra = {
            "example": {
                "id": "sub_abc123",
                "user_id": "user_456",
                "tier": "pro",
                "tier_id": "tier_pro",
                "billing_cycle": "monthly",
                "price": 49.00,
                "monthly_credits": 1000,
                "used_credits": 450,
                "remaining_credits": 550,
                "status": "active",
                "current_period_start": "2024-01-01T00:00:00Z",
                "current_period_end": "2024-01-31T23:59:59Z",
                "renews_at": "2024-02-01T00:00:00Z",
            }
        }


class CreditBalance(BaseModel):
    """
    Credit balance model.

    Tracks credit balance and transactions.
    """

    # Identity
    user_id: str = Field(..., description="User ID")

    # Balance
    total_credits: float = Field(
        default=0.0, description="Total credits available", ge=0
    )
    subscription_credits: float = Field(
        default=0.0, description="Credits from subscription", ge=0
    )
    purchased_credits: float = Field(
        default=0.0,
        description="Purchased credits",
        ge=0,
    )
    promotional_credits: float = Field(
        default=0.0, description="Promotional credits", ge=0
    )
    rollover_credits: float = Field(
        default=0.0, description="Rolled over credits", ge=0
    )

    # Usage
    used_credits: float = Field(
        default=0.0,
        description="Credits used",
        ge=0,
    )
    reserved_credits: float = Field(
        default=0.0,
        description="Reserved credits",
        ge=0,
    )

    # Limits
    credit_limit: Optional[float] = Field(
        None,
        description="Credit limit (if any)",
    )
    low_balance_threshold: float = Field(
        default=100.0,
        description="Low balance alert threshold",
        ge=0,
    )

    # Alerts
    low_balance_alert_sent: bool = Field(
        default=False,
        description="Low balance alert sent",
    )

    # Timestamps
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    last_reset: Optional[datetime] = Field(
        None,
        description="Last credit reset",
    )

    def get_available_credits(self) -> float:
        """Get available credits (total - used - reserved)."""
        return max(
            0.0,
            self.total_credits - self.used_credits - self.reserved_credits,
        )

    def is_low_balance(self) -> bool:
        """Check if balance is low."""
        return self.get_available_credits() < self.low_balance_threshold

    def can_use_credits(self, amount: float) -> bool:
        """Check if user can use specified amount of credits."""
        available = self.get_available_credits()
        if self.credit_limit:
            return (
                available >= amount
                and (self.used_credits + amount) <= self.credit_limit
            )
        return available >= amount

    def use_credits(self, amount: float) -> bool:
        """Use credits if available."""
        if not self.can_use_credits(amount):
            return False
        self.used_credits += amount
        self.last_updated = datetime.utcnow()
        return True

    def add_credits(self, amount: float, source: str = "purchased"):
        """Add credits to balance."""
        if source == "subscription":
            self.subscription_credits += amount
        elif source == "purchased":
            self.purchased_credits += amount
        elif source == "promotional":
            self.promotional_credits += amount
        elif source == "rollover":
            self.rollover_credits += amount

        self.total_credits += amount
        self.last_updated = datetime.utcnow()

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for CreditBalance."""

        json_schema_extra = {
            "example": {
                "user_id": "user_456",
                "total_credits": 1550.0,
                "subscription_credits": 1000.0,
                "purchased_credits": 500.0,
                "promotional_credits": 50.0,
                "used_credits": 450.0,
                "reserved_credits": 0.0,
                "low_balance_threshold": 100.0,
            }
        }


class CreditTransaction(BaseModel):
    """
    Credit transaction model.

    Records credit additions and deductions.
    """

    # Identity
    id: str = Field(..., description="Transaction ID")
    user_id: str = Field(..., description="User ID")

    # Transaction details
    type: str = Field(
        ...,
        description="Transaction type (add, deduct, refund)",
    )
    amount: float = Field(..., description="Transaction amount")
    source: str = Field(..., description="Transaction source")

    # Balance
    balance_before: float = Field(
        ...,
        description="Balance before transaction",
        ge=0,
    )
    balance_after: float = Field(
        ...,
        description="Balance after transaction",
        ge=0,
    )

    # Context
    tool_usage_id: Optional[str] = Field(
        None,
        description="Related tool usage ID",
    )
    subscription_id: Optional[str] = Field(
        None,
        description="Related subscription ID",
    )
    purchase_id: Optional[str] = Field(
        None,
        description="Related purchase ID",
    )

    # Description
    description: str = Field(..., description="Transaction description")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for CreditTransaction."""

        json_schema_extra = {
            "example": {
                "id": "txn_abc123",
                "user_id": "user_456",
                "type": "deduct",
                "amount": 0.15,
                "source": "tool_usage",
                "balance_before": 1000.0,
                "balance_after": 999.85,
                "tool_usage_id": "usage_abc123",
                "description": "GPT-4 Turbo API call",
            }
        }


class CreditPurchase(BaseModel):
    """
    Credit purchase model.

    Records credit purchases.
    """

    # Identity
    id: str = Field(..., description="Purchase ID")
    user_id: str = Field(..., description="User ID")

    # Purchase details
    credits: float = Field(..., description="Credits purchased", ge=0)
    price: float = Field(..., description="Purchase price", ge=0)
    currency: str = Field(default="USD", description="Currency code")
    price_per_credit: float = Field(
        ...,
        description="Price per credit",
        ge=0,
    )

    # Payment
    payment_id: str = Field(..., description="Payment ID")
    payment_method_id: str = Field(..., description="Payment method used")

    # Status
    status: str = Field(
        default="completed",
        description="Purchase status",
    )

    # Expiration
    expires_at: Optional[datetime] = Field(
        None,
        description="Credit expiration date",
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for CreditPurchase."""

        json_schema_extra = {
            "example": {
                "id": "pur_abc123",
                "user_id": "user_456",
                "credits": 1000.0,
                "price": 50.00,
                "price_per_credit": 0.05,
                "payment_id": "pay_abc123",
                "status": "completed",
                "completed_at": "2024-01-15T10:00:00Z",
            }
        }


# Made with Bob
