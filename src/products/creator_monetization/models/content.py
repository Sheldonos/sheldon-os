"""
Content Model
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict


class ContentType(Enum):
    """Content types"""

    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    TEXT = "text"
    LIVE_STREAM = "live_stream"


@dataclass
class Content:  # pylint: disable=too-many-instance-attributes
    """Content item"""

    content_id: str
    creator_id: str
    title: str
    content_type: ContentType
    platform: str
    url: str
    description: str = ""
    thumbnail_url: str = ""
    views: int = 0
    likes: int = 0
    revenue: float = 0.0
    published_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content_id": self.content_id,
            "creator_id": self.creator_id,
            "title": self.title,
            "content_type": self.content_type.value,
            "platform": self.platform,
            "url": self.url,
            "description": self.description,
            "thumbnail_url": self.thumbnail_url,
            "views": self.views,
            "likes": self.likes,
            "revenue": self.revenue,
            "published_at": self.published_at.isoformat(),
            "metadata": self.metadata,
        }
