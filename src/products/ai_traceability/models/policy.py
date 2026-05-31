"""
Policy Model

Defines policies for AI usage governance and compliance.
Supports rule-based enforcement with flexible actions.
"""

import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PolicyType(str, Enum):
    """Type of policy"""

    CONTENT_FILTER = "content_filter"
    DATA_LOSS_PREVENTION = "data_loss_prevention"
    USAGE_LIMIT = "usage_limit"
    PLATFORM_RESTRICTION = "platform_restriction"
    TIME_RESTRICTION = "time_restriction"
    ATTACHMENT_CONTROL = "attachment_control"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"


class Severity(str, Enum):
    """Policy violation severity"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ActionType(str, Enum):
    """Actions to take on policy violation"""

    ALERT = "alert"
    BLOCK = "block"
    LOG = "log"
    NOTIFY = "notify"
    QUARANTINE = "quarantine"
    REQUIRE_APPROVAL = "require_approval"
    ENCRYPT = "encrypt"
    REDACT = "redact"


class RuleOperator(str, Enum):
    """Operators for rule conditions"""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    MATCHES_REGEX = "matches_regex"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"


class Policy(BaseModel):
    """
    Policy Model

    Defines governance policies for AI usage with rule-based enforcement.
    Supports flexible conditions, actions, and compliance requirements.

    Attributes:
        id: Unique policy identifier
        name: Policy name
        description: Policy description
        policy_type: Type of policy
        organization_id: Organization this policy applies to
        rules: List of rule conditions
        actions: Actions to take on violation
        severity: Violation severity level
        enabled: Whether policy is active
        priority: Execution priority (higher = earlier)
        applies_to_users: User IDs this applies to (empty = all)
        applies_to_groups: Group IDs this applies to
        applies_to_platforms: LLM platforms this applies to
        schedule: Time-based schedule (cron format)
        exceptions: Exception rules
        metadata: Additional metadata
        created_at: Creation timestamp
        updated_at: Last update timestamp
        created_by: Creator user ID
        updated_by: Last updater user ID
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    policy_type: PolicyType
    organization_id: str

    # Rules and conditions
    rules: List[Dict[str, Any]] = Field(default_factory=list)
    rule_logic: str = "AND"  # AND or OR

    # Actions
    actions: List[ActionType] = Field(default_factory=list)
    action_config: Dict[str, Any] = Field(default_factory=dict)

    # Severity
    severity: Severity = Severity.MEDIUM

    # Status
    enabled: bool = True
    priority: int = Field(default=100, ge=0, le=1000)

    # Scope
    applies_to_users: List[str] = Field(default_factory=list)
    applies_to_groups: List[str] = Field(default_factory=list)
    applies_to_platforms: List[str] = Field(default_factory=list)
    applies_to_departments: List[str] = Field(default_factory=list)

    # Scheduling
    schedule: Optional[str] = None  # Cron format
    active_hours: Optional[Dict[str, Any]] = None

    # Exceptions
    exceptions: List[Dict[str, Any]] = Field(default_factory=list)
    whitelist: List[str] = Field(default_factory=list)
    blacklist: List[str] = Field(default_factory=list)

    # Compliance
    compliance_frameworks: List[str] = Field(default_factory=list)
    regulatory_requirements: List[str] = Field(default_factory=list)

    # Notifications
    notify_users: List[str] = Field(default_factory=list)
    notify_admins: bool = True
    notification_channels: List[str] = Field(default_factory=list)

    # Metrics
    violation_count: int = 0
    last_violation: Optional[datetime] = None
    enforcement_count: int = 0

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    updated_by: Optional[str] = None
    version: int = 1

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for Policy."""

        json_schema_extra = {
            "example": {
                "id": "policy_123",
                "name": "PII Detection Policy",
                "description": "Detect and block PII in AI prompts",
                "policy_type": "data_loss_prevention",
                "organization_id": "org_456",
                "rules": [
                    {
                        "field": "content",
                        "operator": "matches_regex",
                        "value": r"\b\d{3}-\d{2}-\d{4}\b",
                        "description": "SSN pattern",
                    }
                ],
                "actions": ["alert", "block"],
                "severity": "critical",
                "enabled": True,
            }
        }

    def evaluate_rules(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate policy rules against context

        Args:
            context: Context data to evaluate
                (session, keystroke, attachment, etc.)

        Returns:
            True if policy is violated, False otherwise
        """
        if not self.rules:
            return False

        results = [self._evaluate_rule(rule, context) for rule in self.rules]

        if self.rule_logic == "AND":
            return all(results)
        return any(results)

    def _evaluate_rule(
        self,
        rule: Dict[str, Any],
        context: Dict[str, Any],
    ) -> bool:
        """Evaluate a single policy rule against the provided context."""
        field = rule.get("field")
        operator = rule.get("operator")
        value = rule.get("value")

        if not isinstance(field, str):
            return False

        field_value = context.get(field)
        if field_value is None:
            return False

        evaluators = {
            RuleOperator.EQUALS: lambda: field_value == value,
            RuleOperator.NOT_EQUALS: lambda: field_value != value,
            RuleOperator.CONTAINS: lambda: self._contains_value(field_value, value),
            RuleOperator.NOT_CONTAINS: lambda: not self._contains_value(
                field_value, value
            ),
            RuleOperator.MATCHES_REGEX: lambda: self._matches_regex(
                field_value, value
            ),
            RuleOperator.GREATER_THAN: lambda: self._compare_numeric(
                field_value, value, greater_than=True
            ),
            RuleOperator.LESS_THAN: lambda: self._compare_numeric(
                field_value, value, greater_than=False
            ),
            RuleOperator.IN_LIST: lambda: isinstance(value, list)
            and field_value in value,
            RuleOperator.NOT_IN_LIST: lambda: isinstance(value, list)
            and field_value not in value,
        }

        if not isinstance(operator, RuleOperator):
            return False

        evaluator = evaluators.get(operator)
        return evaluator() if evaluator is not None else False

    def _contains_value(self, field_value: Any, value: Any) -> bool:
        """Check whether a string value is contained in the field value."""
        return isinstance(value, str) and value in str(field_value)

    def _matches_regex(self, field_value: Any, value: Any) -> bool:
        """Check whether a regex pattern matches the field value."""
        return isinstance(value, str) and bool(re.search(value, str(field_value)))

    def _compare_numeric(
        self,
        field_value: Any,
        value: Any,
        *,
        greater_than: bool,
    ) -> bool:
        """Compare numeric values safely for policy evaluation."""
        try:
            numeric_field_value = float(str(field_value))
            numeric_rule_value = float(str(value))
        except (TypeError, ValueError):
            return False

        if greater_than:
            return numeric_field_value > numeric_rule_value
        return numeric_field_value < numeric_rule_value

    def check_scope(
        self, user_id: str, platform: str, group_id: Optional[str] = None
    ) -> bool:
        """Check if policy applies to given scope"""
        # Check user scope
        if self.applies_to_users and user_id not in self.applies_to_users:
            return False

        # Check group scope
        if self.applies_to_groups and group_id:
            if group_id not in self.applies_to_groups:
                return False

        # Check platform scope
        if (
            self.applies_to_platforms
            and platform not in self.applies_to_platforms
        ):
            return False

        # Check whitelist/blacklist
        if self.whitelist and user_id in self.whitelist:
            return False

        if self.blacklist and user_id in self.blacklist:
            return True

        return True

    def record_violation(self) -> None:
        """Record a policy violation"""
        self.violation_count += 1
        self.last_violation = datetime.utcnow()

    def record_enforcement(self) -> None:
        """Record a policy enforcement action"""
        self.enforcement_count += 1

    def update_version(self, updated_by: str) -> None:
        """Update policy version"""
        self.version += 1
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by


# Predefined policy templates
POLICY_TEMPLATES = {
    "pii_detection": {
        "name": "PII Detection",
        "description": "Detect and prevent PII in AI interactions",
        "policy_type": PolicyType.DATA_LOSS_PREVENTION,
        "rules": [
            {
                "field": "content",
                "operator": RuleOperator.MATCHES_REGEX,
                "value": r"\b\d{3}-\d{2}-\d{4}\b",
                "description": "SSN",
            },
            {
                "field": "content",
                "operator": RuleOperator.MATCHES_REGEX,
                "value": (
                    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\."
                    r"[A-Z|a-z]{2,}\b"
                ),
                "description": "Email",
            },
        ],
        "actions": [ActionType.ALERT, ActionType.BLOCK],
        "severity": Severity.CRITICAL,
    },
    "confidential_data": {
        "name": "Confidential Data Protection",
        "description": "Prevent confidential data leakage",
        "policy_type": PolicyType.DATA_LOSS_PREVENTION,
        "rules": [
            {
                "field": "classification",
                "operator": RuleOperator.IN_LIST,
                "value": ["confidential", "restricted", "top_secret"],
            }
        ],
        "actions": [ActionType.ALERT, ActionType.BLOCK, ActionType.NOTIFY],
        "severity": Severity.CRITICAL,
    },
    "usage_limit": {
        "name": "Daily Usage Limit",
        "description": "Limit daily AI usage per user",
        "policy_type": PolicyType.USAGE_LIMIT,
        "rules": [
            {
                "field": "daily_token_count",
                "operator": RuleOperator.GREATER_THAN,
                "value": 100000,
            }
        ],
        "actions": [ActionType.ALERT, ActionType.NOTIFY],
        "severity": Severity.MEDIUM,
    },
    "platform_restriction": {
        "name": "Platform Whitelist",
        "description": "Only allow approved LLM platforms",
        "policy_type": PolicyType.PLATFORM_RESTRICTION,
        "rules": [
            {
                "field": "llm_platform",
                "operator": RuleOperator.NOT_IN_LIST,
                "value": ["chatgpt", "claude"],
            }
        ],
        "actions": [ActionType.BLOCK, ActionType.ALERT],
        "severity": Severity.HIGH,
    },
}

# Made with Bob
