"""
Transaction Model
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


@dataclass
class Transaction:  # pylint: disable=too-many-instance-attributes
    """Financial transaction"""

    transaction_id: str
    creator_id: str
    amount: float
    currency: str = "USD"
    transaction_type: str = "subscription"
    status: str = "completed"
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "transaction_id": self.transaction_id,
            "creator_id": self.creator_id,
            "amount": self.amount,
            "currency": self.currency,
            "transaction_type": self.transaction_type,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
