"""
Subscription Model
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class SubscriptionTier(Enum):
    """Subscription tiers"""

    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    VIP = "vip"


@dataclass
class Subscription:  # pylint: disable=too-many-instance-attributes
    """Subscription"""

    subscription_id: str
    creator_id: str
    subscriber_id: str
    tier: SubscriptionTier
    price: float
    status: str = "active"
    started_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "subscription_id": self.subscription_id,
            "creator_id": self.creator_id,
            "subscriber_id": self.subscriber_id,
            "tier": self.tier.value,
            "price": self.price,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "expires_at": (
                self.expires_at.isoformat()
                if self.expires_at
                else None
            ),
            "metadata": self.metadata,
        }
