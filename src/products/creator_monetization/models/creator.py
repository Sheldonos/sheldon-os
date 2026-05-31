"""
Creator Model
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class Creator:  # pylint: disable=too-many-instance-attributes
    """Creator profile"""

    creator_id: str
    username: str
    email: str
    display_name: str
    bio: str = ""
    avatar_url: str = ""
    platforms: List[str] = field(default_factory=list)
    total_revenue: float = 0.0
    subscriber_count: int = 0
    content_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "creator_id": self.creator_id,
            "username": self.username,
            "email": self.email,
            "display_name": self.display_name,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "platforms": self.platforms,
            "total_revenue": self.total_revenue,
            "subscriber_count": self.subscriber_count,
            "content_count": self.content_count,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
