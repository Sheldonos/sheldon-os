"""
AI Tool Data Models

Models for AI tools in the Right.ai marketplace.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ToolStatus(str, Enum):
    """Tool status enumeration."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    MAINTENANCE = "maintenance"
    BETA = "beta"
    COMING_SOON = "coming_soon"


class PricingModel(str, Enum):
    """Pricing model enumeration."""

    PER_CALL = "per_call"
    PER_TOKEN = "per_token"
    PER_MINUTE = "per_minute"
    PER_MB = "per_mb"
    PER_IMAGE = "per_image"
    PER_SECOND = "per_second"
    TIERED = "tiered"
    CUSTOM = "custom"


class ToolCategory(str, Enum):
    """Tool category enumeration."""

    LLM = "llm"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DATA = "data"
    CODE = "code"
    SEARCH = "search"
    TRANSLATION = "translation"
    OCR = "ocr"
    SPEECH = "speech"
    EMBEDDING = "embedding"
    CLASSIFICATION = "classification"
    DETECTION = "detection"
    GENERATION = "generation"
    OPTIMIZATION = "optimization"
    OTHER = "other"


class ToolCapability(BaseModel):
    """
    Tool capability definition.

    Describes what a tool can do and its parameters.
    """

    name: str = Field(..., description="Capability name")
    description: str = Field(..., description="Capability description")
    input_schema: Dict[str, Any] = Field(
        ...,
        description="JSON schema for inputs",
    )
    output_schema: Dict[str, Any] = Field(
        ...,
        description="JSON schema for outputs",
    )
    examples: List[Dict[str, Any]] = Field(
        default_factory=list, description="Usage examples"
    )
    rate_limit: Optional[int] = Field(
        None, description="Rate limit for this capability"
    )

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for ToolCapability."""

        json_schema_extra = {
            "example": {
                "name": "generate_text",
                "description": "Generate text from a prompt",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "max_tokens": {"type": "integer"},
                    },
                    "required": ["prompt"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "tokens_used": {"type": "integer"},
                    },
                },
                "examples": [
                    {
                        "input": {"prompt": "Hello world", "max_tokens": 100},
                        "output": {
                            "text": "Hello! How can I help you?",
                            "tokens_used": 8,
                        },
                    }
                ],
                "rate_limit": 100,
            }
        }


class ToolVersion(BaseModel):
    """
    Tool version information.

    Tracks different versions of a tool.
    """

    version: str = Field(
        ...,
        description="Version number (semver)",
    )
    released_at: datetime = Field(..., description="Release date")
    changelog: str = Field(
        ...,
        description="What changed in this version",
    )
    deprecated: bool = Field(
        default=False,
        description="Is this version deprecated",
    )
    breaking_changes: bool = Field(
        default=False, description="Contains breaking changes"
    )

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for ToolVersion."""

        json_schema_extra = {
            "example": {
                "version": "2.1.0",
                "released_at": "2024-01-15T10:00:00Z",
                "changelog": "Added support for streaming responses",
                "deprecated": False,
                "breaking_changes": False,
            }
        }


class RateLimit(BaseModel):
    """Rate limit configuration."""

    requests_per_minute: int = Field(..., description="Requests per minute")
    requests_per_hour: int = Field(..., description="Requests per hour")
    requests_per_day: int = Field(..., description="Requests per day")
    burst_limit: Optional[int] = Field(None, description="Burst limit")


class AITool(BaseModel):
    """
    AI Tool model.

    Represents an AI tool available in the Right.ai marketplace.
    """

    # Identity
    id: str = Field(..., description="Unique tool identifier")
    name: str = Field(..., description="Tool name")
    slug: str = Field(..., description="URL-friendly slug")
    description: str = Field(..., description="Tool description")
    long_description: Optional[str] = Field(
        None,
        description="Detailed description",
    )

    # Provider information
    provider: str = Field(..., description="Tool provider name")
    provider_url: Optional[str] = Field(
        None,
        description="Provider website",
    )
    provider_contact: Optional[str] = Field(
        None,
        description="Provider contact email",
    )

    # Categorization
    category: ToolCategory = Field(..., description="Primary category")
    tags: List[str] = Field(default_factory=list, description="Search tags")
    use_cases: List[str] = Field(
        default_factory=list,
        description="Common use cases",
    )

    # Pricing
    pricing_model: PricingModel = Field(
        ...,
        description="How the tool is priced",
    )
    base_price: float = Field(..., description="Base price per unit", ge=0)
    currency: str = Field(default="USD", description="Currency code")
    free_tier: Optional[Dict[str, Any]] = Field(
        None,
        description="Free tier limits",
    )
    volume_discounts: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Volume discount tiers",
    )

    # Technical details
    capabilities: List[ToolCapability] = Field(
        ...,
        description="Tool capabilities",
    )
    mcp_endpoint: Optional[str] = Field(
        None,
        description="MCP protocol endpoint",
    )
    api_endpoint: Optional[str] = Field(
        None,
        description="REST API endpoint",
    )
    api_version: str = Field(
        default="1.0",
        description="API version",
    )
    authentication: str = Field(
        default="api_key",
        description="Authentication method",
    )

    # Performance metrics
    avg_response_time: float = Field(
        default=0.0,
        description="Average response time (ms)",
        ge=0,
    )
    success_rate: float = Field(
        default=1.0,
        description="Success rate (0-1)",
        ge=0,
        le=1,
    )
    uptime: float = Field(
        default=0.999,
        description="Uptime percentage",
        ge=0,
        le=1,
    )

    # Rate limits
    rate_limits: RateLimit = Field(
        ...,
        description="Rate limit configuration",
    )

    # Usage statistics
    total_calls: int = Field(
        default=0,
        description="Total API calls",
        ge=0,
    )
    total_users: int = Field(
        default=0,
        description="Total unique users",
        ge=0,
    )
    monthly_calls: int = Field(
        default=0,
        description="Calls this month",
        ge=0,
    )

    # Ratings and reviews
    rating: float = Field(
        default=0.0,
        description="Average rating (0-5)",
        ge=0,
        le=5,
    )
    reviews_count: int = Field(
        default=0,
        description="Number of reviews",
        ge=0,
    )

    # Status and metadata
    status: ToolStatus = Field(
        default=ToolStatus.ACTIVE,
        description="Tool status",
    )
    version: str = Field(
        default="1.0.0",
        description="Current version",
    )
    versions: List[ToolVersion] = Field(
        default_factory=list,
        description="Version history",
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp",
    )
    last_used_at: Optional[datetime] = Field(
        None,
        description="Last usage timestamp",
    )

    # Documentation
    documentation_url: Optional[str] = Field(
        None,
        description="Documentation URL",
    )
    examples_url: Optional[str] = Field(
        None,
        description="Examples URL",
    )
    support_url: Optional[str] = Field(
        None,
        description="Support URL",
    )

    # Compliance and security
    data_retention_days: Optional[int] = Field(
        None, description="Data retention period"
    )
    gdpr_compliant: bool = Field(default=False, description="GDPR compliant")
    hipaa_compliant: bool = Field(default=False, description="HIPAA compliant")
    soc2_certified: bool = Field(default=False, description="SOC 2 certified")

    # Additional metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @validator("slug")
    @classmethod
    def validate_slug(cls, v):
        """Validate slug format."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                (
                    "Slug must contain only alphanumeric characters, "
                    "hyphens, and underscores"
                )
            )
        return v.lower()

    @validator("base_price")
    @classmethod
    def validate_price(cls, v):
        """Validate price is reasonable."""
        if v < 0:
            raise ValueError("Price cannot be negative")
        if v > 1000000:
            raise ValueError("Price seems unreasonably high")
        return round(v, 4)  # Round to 4 decimal places

    def calculate_cost(self, usage: Dict[str, Any]) -> float:
        """
        Calculate cost for a given usage.

        Args:
            usage: Usage details (tokens, minutes, calls, etc.)

        Returns:
            Cost in base currency
        """
        usage_key_map = {
            PricingModel.PER_TOKEN: "tokens",
            PricingModel.PER_MINUTE: "minutes",
            PricingModel.PER_MB: "mb",
            PricingModel.PER_IMAGE: "images",
            PricingModel.PER_SECOND: "seconds",
        }

        if self.pricing_model == PricingModel.PER_CALL:
            return self.base_price

        usage_key = usage_key_map.get(self.pricing_model)
        if usage_key is None:
            return self.base_price

        usage_amount = float(usage.get(usage_key, 0))
        return self.base_price * usage_amount

    def is_available(self) -> bool:
        """Check if tool is available for use."""
        return self.status in [ToolStatus.ACTIVE, ToolStatus.BETA]

    def get_capability(self, name: str) -> Optional[ToolCapability]:
        """Get a specific capability by name."""
        for cap in self.capabilities:
            if cap.name == name:
                return cap
        return None

    def to_marketplace_listing(self) -> Dict[str, Any]:
        """Convert to marketplace listing format."""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "provider": self.provider,
            "category": self.category.value,
            "tags": self.tags,
            "pricing": {
                "model": self.pricing_model.value,
                "base_price": self.base_price,
                "currency": self.currency,
            },
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "total_users": self.total_users,
            "status": self.status.value,
            "avg_response_time": self.avg_response_time,
            "success_rate": self.success_rate,
        }

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for Tool."""

        json_schema_extra = {
            "example": {
                "id": "tool_gpt4_turbo",
                "name": "GPT-4 Turbo",
                "slug": "gpt-4-turbo",
                "description": (
                    "Most capable GPT-4 model with 128K context"
                ),
                "provider": "OpenAI",
                "category": "llm",
                "tags": ["language-model", "chat", "completion"],
                "pricing_model": "per_token",
                "base_price": 0.00001,
                "capabilities": [
                    {
                        "name": "chat_completion",
                        "description": "Generate chat completions",
                        "input_schema": {"type": "object"},
                        "output_schema": {"type": "object"},
                    }
                ],
                "rate_limits": {
                    "requests_per_minute": 500,
                    "requests_per_hour": 10000,
                    "requests_per_day": 100000,
                },
                "rating": 4.8,
                "reviews_count": 1250,
                "status": "active",
            }
        }


class ToolReview(BaseModel):
    """Tool review model."""

    id: str = Field(..., description="Review ID")
    tool_id: str = Field(..., description="Tool ID")
    user_id: str = Field(..., description="User ID")
    rating: float = Field(..., description="Rating (1-5)", ge=1, le=5)
    title: str = Field(..., description="Review title")
    content: str = Field(..., description="Review content")
    pros: List[str] = Field(default_factory=list, description="Pros")
    cons: List[str] = Field(default_factory=list, description="Cons")
    helpful_count: int = Field(
        default=0,
        description="Helpful votes",
        ge=0,
    )
    verified_purchase: bool = Field(
        default=False,
        description="Verified purchase",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for ToolReview."""

        json_schema_extra = {
            "example": {
                "id": "review_123",
                "tool_id": "tool_gpt4_turbo",
                "user_id": "user_456",
                "rating": 5.0,
                "title": "Excellent for complex tasks",
                "content": (
                    "GPT-4 Turbo handles complex reasoning tasks "
                    "exceptionally well."
                ),
                "pros": ["Fast", "Accurate", "Large context"],
                "cons": ["Expensive for high volume"],
                "helpful_count": 42,
                "verified_purchase": True,
            }
        }


# Made with Bob
