"""
Keystroke Model

Represents individual keystroke events captured during AI interactions.
Stores encrypted content with context for analysis and compliance.
"""

import uuid
import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class KeystrokeType(str, Enum):
    """Type of keystroke event"""

    PROMPT = "prompt"
    RESPONSE = "response"
    EDIT = "edit"
    DELETE = "delete"
    PASTE = "paste"
    COMMAND = "command"


class Keystroke(BaseModel):
    """
    Keystroke Model

    Captures individual keystroke events during LLM interactions.
    Content is encrypted before storage for privacy and security.

    Attributes:
        id: Unique keystroke identifier
        session_id: Associated session ID
        user_id: User identifier
        timestamp: Keystroke timestamp
        content: Encrypted keystroke content
        content_hash: Hash of unencrypted content
        keystroke_type: Type of keystroke event
        llm_platform: LLM platform being used
        context: Additional context (window title, URL, etc.)
        is_encrypted: Whether content is encrypted
        encryption_key_id: ID of encryption key used
        character_count: Number of characters
        word_count: Estimated word count
        contains_code: Whether content appears to be code
        language_detected: Detected programming language (if code)
        sentiment_score: Sentiment analysis score (-1 to 1)
        metadata: Additional metadata
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str

    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sequence_number: int = 0

    # Content (encrypted)
    content: str  # Encrypted content
    content_hash: str  # SHA-256 hash of original content
    is_encrypted: bool = True
    encryption_key_id: Optional[str] = None

    # Classification
    keystroke_type: KeystrokeType = KeystrokeType.PROMPT
    llm_platform: str

    # Metrics
    character_count: int = 0
    word_count: int = 0
    token_count_estimated: int = 0

    # Analysis
    contains_code: bool = False
    language_detected: Optional[str] = None
    contains_pii: bool = False
    contains_confidential: bool = False
    sentiment_score: Optional[float] = Field(default=None, ge=-1.0, le=1.0)

    # Context
    context: Dict[str, Any] = Field(default_factory=dict)
    window_title: Optional[str] = None
    url: Optional[str] = None
    application: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for Keystroke."""

        json_schema_extra = {
            "example": {
                "id": "ks_123456",
                "session_id": "session_789",
                "user_id": "user_123",
                "timestamp": "2024-01-15T10:30:15Z",
                "content": "encrypted_content_here",
                "content_hash": "sha256_hash",
                "keystroke_type": "prompt",
                "llm_platform": "chatgpt",
                "character_count": 150,
                "word_count": 25,
            }
        }

    def estimate_tokens(self) -> int:
        """
        Estimate token count
        (rough approximation: 1 token ≈ 4 characters)
        """
        self.token_count_estimated = max(1, self.character_count // 4)
        return self.token_count_estimated

    def analyze_content_type(self, decrypted_content: str) -> None:
        """
        Analyze content to detect code, PII, etc.
        This should be called with decrypted content during processing.
        """
        # Simple code detection (presence of common programming keywords)
        code_indicators = [
            "def ",
            "function ",
            "class ",
            "import ",
            "const ",
            "var ",
            "let ",
            "if (",
            "for (",
            "while (",
            "=> {",
            "return ",
            "async ",
            "await ",
        ]
        self.contains_code = any(
            indicator in decrypted_content.lower()
            for indicator in code_indicators
        )

        # Simple PII detection (patterns for email, phone, SSN)
        pii_patterns = [
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
            r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # Phone
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
        ]
        self.contains_pii = any(
            re.search(pattern, decrypted_content) for pattern in pii_patterns
        )


# Made with Bob
