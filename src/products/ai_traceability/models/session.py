"""
AI Session Model

Represents a user's interaction session with an LLM platform.
Tracks session metadata, activity, and risk assessment.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LLMPlatform(str, Enum):
    """Supported LLM platforms"""

    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    GEMINI = "gemini"
    COPILOT = "copilot"
    BARD = "bard"
    PERPLEXITY = "perplexity"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    """Risk assessment levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class SessionStatus(str, Enum):
    """Session status"""

    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    FLAGGED = "flagged"


class AISession(BaseModel):
    """
    AI Session Model

    Tracks a complete user interaction session with an LLM platform.
    Includes activity metrics, risk scoring, and policy violations.

    Attributes:
        id: Unique session identifier
        user_id: User identifier
        organization_id: Organization identifier
        llm_platform: LLM platform being used
        platform_version: Version of the LLM platform
        start_time: Session start timestamp
        end_time: Session end timestamp (None if active)
        last_activity: Last activity timestamp
        total_keystrokes: Total keystrokes in session
        total_tokens_estimated: Estimated tokens sent
        attachments: List of attachment IDs
        risk_score: Calculated risk score (0-100)
        risk_level: Risk level classification
        policy_violations: List of policy violation IDs
        status: Current session status
        metadata: Additional session metadata
        ip_address: User IP address
        user_agent: Browser/app user agent
        device_id: Device identifier
        location: Geographic location (if available)
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    organization_id: str

    # Platform information
    llm_platform: LLMPlatform
    platform_version: Optional[str] = None
    platform_url: Optional[str] = None

    # Timing
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: Optional[int] = None

    # Activity metrics
    total_keystrokes: int = 0
    total_tokens_estimated: int = 0
    total_prompts: int = 0
    total_responses: int = 0
    attachments: List[str] = Field(default_factory=list)

    # Risk assessment
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    risk_level: RiskLevel = RiskLevel.NONE
    risk_factors: List[str] = Field(default_factory=list)

    # Policy compliance
    policy_violations: List[str] = Field(default_factory=list)
    policies_checked: List[str] = Field(default_factory=list)

    # Status
    status: SessionStatus = SessionStatus.ACTIVE

    # Context
    metadata: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_id: Optional[str] = None
    location: Optional[Dict[str, str]] = None

    # Flags
    contains_pii: bool = False
    contains_confidential: bool = False
    requires_review: bool = False
    reviewed: bool = False
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for AISession."""

        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user_123",
                "organization_id": "org_456",
                "llm_platform": "chatgpt",
                "platform_version": "gpt-4",
                "start_time": "2024-01-15T10:30:00Z",
                "total_keystrokes": 1250,
                "total_tokens_estimated": 850,
                "risk_score": 35.5,
                "risk_level": "medium",
                "status": "active",
            }
        }

    def calculate_duration(self) -> Optional[int]:
        """Calculate session duration in seconds"""
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds())
        return int((datetime.utcnow() - self.start_time).total_seconds())

    def update_risk_score(self, factors: List[str]) -> float:
        """
        Update risk score based on detected factors

        Risk factors and their weights:
        - PII detected: +30
        - Confidential data: +40
        - Policy violation: +25
        - Large attachment: +10
        - Unusual activity pattern: +15
        """
        score = 0.0

        risk_weights = {
            "pii_detected": 30.0,
            "confidential_data": 40.0,
            "policy_violation": 25.0,
            "large_attachment": 10.0,
            "unusual_pattern": 15.0,
            "excessive_tokens": 20.0,
            "suspicious_keywords": 25.0,
        }

        for factor in factors:
            score += risk_weights.get(factor, 5.0)

        # Cap at 100
        self.risk_score = min(score, 100.0)

        # Update risk level
        if self.risk_score >= 75:
            self.risk_level = RiskLevel.CRITICAL
        elif self.risk_score >= 50:
            self.risk_level = RiskLevel.HIGH
        elif self.risk_score >= 25:
            self.risk_level = RiskLevel.MEDIUM
        elif self.risk_score > 0:
            self.risk_level = RiskLevel.LOW
        else:
            self.risk_level = RiskLevel.NONE

        self.risk_factors = factors
        return self.risk_score

    def add_violation(self, policy_id: str) -> None:
        """Add a policy violation"""
        if policy_id not in self.policy_violations:
            self.policy_violations.append(policy_id)
            self.requires_review = True

    def complete_session(self) -> None:
        """Mark session as completed"""
        self.end_time = datetime.utcnow()
        self.duration_seconds = self.calculate_duration()
        self.status = SessionStatus.COMPLETED

    def flag_session(self, reason: str) -> None:
        """Flag session for review"""
        self.status = SessionStatus.FLAGGED
        self.requires_review = True
        if "flag_reason" not in self.metadata:
            self.metadata["flag_reason"] = []
        self.metadata["flag_reason"].append(reason)


# Made with Bob
