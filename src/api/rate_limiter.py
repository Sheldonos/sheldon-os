"""
Rate Limiter
Implements rate limiting for API requests
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict

logger = logging.getLogger(__name__)


class RateLimiter:  # pylint: disable=too-few-public-methods
    """
    Rate limiter for API requests
    """

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self._requests: Dict[str, list] = defaultdict(list)
        logger.info(
            "Rate Limiter initialized (%s req/min)", requests_per_minute
        )

    def check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)

        # Clean old requests
        self._requests[client_id] = [
            req_time
            for req_time in self._requests[client_id]
            if req_time > minute_ago
        ]

        # Check limit
        if len(self._requests[client_id]) >= self.requests_per_minute:
            logger.warning("Rate limit exceeded for client %s", client_id)
            return False

        # Add current request
        self._requests[client_id].append(now)
        return True
