"""
Base Connector
Abstract base class for all external tool connectors
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ConnectorConfig:
    """Configuration for a connector"""

    connector_id: str
    connector_type: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    endpoint: Optional[str] = None
    timeout: int = 30
    retry_attempts: int = 3
    rate_limit: int = 100  # requests per minute
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseConnector(ABC):
    """
    Abstract base class for external tool connectors
    """

    def __init__(self, config: ConnectorConfig):
        self.config = config
        self._connected = False
        self._last_request_time: Optional[datetime] = None
        self._request_count = 0
        logger.info(
            "Initialized %s connector", self.config.connector_type
        )

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the external service"""
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self):
        """Disconnect from the external service"""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if connection is healthy"""
        raise NotImplementedError

    @abstractmethod
    async def execute_action(
        self,
        action: str,
        parameters: Dict[str, Any],
    ) -> Any:
        """Execute an action on the external service"""
        raise NotImplementedError

    @property
    def is_connected(self) -> bool:
        """Check if connector is connected"""
        return self._connected

    def _check_rate_limit(self) -> bool:
        """Check if rate limit is exceeded"""
        # Simple rate limiting implementation
        now = datetime.utcnow()
        if self._last_request_time:
            time_diff = (now - self._last_request_time).total_seconds()
            if time_diff < 60:  # Within 1 minute
                if self._request_count >= self.config.rate_limit:
                    return False
            else:
                self._request_count = 0

        self._last_request_time = now
        self._request_count += 1
        return True
