"""
Authentication Manager
Handles API authentication and authorization
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Authentication and authorization manager
    """

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = "HS256"
        logger.info("Auth Manager initialized")

    def create_token(
        self, user_id: str, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT token"""
        if expires_delta is None:
            expires_delta = timedelta(hours=24)

        expire = datetime.utcnow() + expires_delta
        payload = {"user_id": user_id, "exp": expire}

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
