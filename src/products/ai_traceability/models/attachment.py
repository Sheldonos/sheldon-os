"""
Attachment Model

Represents files uploaded to LLM platforms during sessions.
Tracks metadata, classification, and security analysis.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FileType(str, Enum):
    """File type categories"""

    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    CODE = "code"
    ARCHIVE = "archive"
    DATA = "data"
    OTHER = "other"


class DataClassification(str, Enum):
    """Data classification levels"""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


class ScanStatus(str, Enum):
    """Security scan status"""

    PENDING = "pending"
    SCANNING = "scanning"
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    ERROR = "error"


class Attachment(BaseModel):
    """
    Attachment Model

    Tracks files uploaded to LLM platforms with security analysis.
    Includes content classification, malware scanning, and DLP checks.

    Attributes:
        id: Unique attachment identifier
        session_id: Associated session ID
        user_id: User identifier
        filename: Original filename
        file_extension: File extension
        file_type: Categorized file type
        size_bytes: File size in bytes
        hash_md5: MD5 hash
        hash_sha256: SHA-256 hash
        uploaded_at: Upload timestamp
        llm_platform: Target LLM platform
        classification: Data classification level
        contains_pii: Whether file contains PII
        contains_confidential: Whether file contains confidential data
        scan_status: Security scan status
        scan_results: Detailed scan results
        dlp_violations: DLP policy violations detected
        allowed: Whether upload was allowed
        blocked_reason: Reason if blocked
        metadata: Additional metadata
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str
    organization_id: str

    # File information
    filename: str
    file_extension: str
    file_type: FileType
    mime_type: Optional[str] = None
    size_bytes: int

    # Hashing
    hash_md5: str
    hash_sha256: str

    # Timing
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    scanned_at: Optional[datetime] = None

    # Platform
    llm_platform: str
    upload_url: Optional[str] = None

    # Classification
    classification: DataClassification = DataClassification.INTERNAL
    classification_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Content analysis
    contains_pii: bool = False
    pii_types: List[str] = Field(default_factory=list)
    contains_confidential: bool = False
    confidential_markers: List[str] = Field(default_factory=list)
    contains_code: bool = False
    programming_languages: List[str] = Field(default_factory=list)

    # Security
    scan_status: ScanStatus = ScanStatus.PENDING
    scan_results: Dict[str, Any] = Field(default_factory=dict)
    malware_detected: bool = False
    malware_signatures: List[str] = Field(default_factory=list)

    # DLP
    dlp_violations: List[str] = Field(default_factory=list)
    dlp_rules_checked: List[str] = Field(default_factory=list)

    # Access control
    allowed: bool = True
    blocked: bool = False
    blocked_reason: Optional[str] = None
    blocked_at: Optional[datetime] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extracted_text: Optional[str] = None
    page_count: Optional[int] = None

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for Attachment."""

        json_schema_extra = {
            "example": {
                "id": "att_123456",
                "session_id": "session_789",
                "user_id": "user_123",
                "organization_id": "org_456",
                "filename": "financial_report.pdf",
                "file_extension": "pdf",
                "file_type": "document",
                "size_bytes": 2048576,
                "hash_sha256": "abc123...",
                "classification": "confidential",
                "scan_status": "clean",
            }
        }

    def classify_file_type(self) -> FileType:
        """Classify file type based on extension"""
        extension_map = {
            # Documents
            "pdf": FileType.DOCUMENT,
            "doc": FileType.DOCUMENT,
            "docx": FileType.DOCUMENT,
            "txt": FileType.DOCUMENT,
            "rtf": FileType.DOCUMENT,
            "odt": FileType.DOCUMENT,
            # Spreadsheets
            "xls": FileType.SPREADSHEET,
            "xlsx": FileType.SPREADSHEET,
            "csv": FileType.SPREADSHEET,
            "ods": FileType.SPREADSHEET,
            # Presentations
            "ppt": FileType.PRESENTATION,
            "pptx": FileType.PRESENTATION,
            "odp": FileType.PRESENTATION,
            # Images
            "jpg": FileType.IMAGE,
            "jpeg": FileType.IMAGE,
            "png": FileType.IMAGE,
            "gif": FileType.IMAGE,
            "bmp": FileType.IMAGE,
            "svg": FileType.IMAGE,
            # Code
            "py": FileType.CODE,
            "js": FileType.CODE,
            "ts": FileType.CODE,
            "java": FileType.CODE,
            "cpp": FileType.CODE,
            "c": FileType.CODE,
            "go": FileType.CODE,
            "rs": FileType.CODE,
            # Archives
            "zip": FileType.ARCHIVE,
            "tar": FileType.ARCHIVE,
            "gz": FileType.ARCHIVE,
            "rar": FileType.ARCHIVE,
            # Data
            "json": FileType.DATA,
            "xml": FileType.DATA,
            "yaml": FileType.DATA,
            "sql": FileType.DATA,
        }

        ext = self.file_extension.lower().lstrip(".")
        self.file_type = extension_map.get(ext, FileType.OTHER)
        return self.file_type

    def calculate_risk_score(self) -> float:
        """Calculate risk score for this attachment"""
        score = 0.0

        # Size-based risk
        if self.size_bytes > 100 * 1024 * 1024:  # > 100MB
            score += 20.0
        elif self.size_bytes > 10 * 1024 * 1024:  # > 10MB
            score += 10.0

        # Classification-based risk
        classification_scores = {
            DataClassification.PUBLIC: 0.0,
            DataClassification.INTERNAL: 10.0,
            DataClassification.CONFIDENTIAL: 30.0,
            DataClassification.RESTRICTED: 50.0,
            DataClassification.TOP_SECRET: 80.0,
        }
        score += classification_scores.get(self.classification, 0.0)

        # Content-based risk
        if self.contains_pii:
            score += 25.0
        if self.contains_confidential:
            score += 30.0
        if self.malware_detected:
            score += 100.0  # Critical

        # DLP violations
        score += len(self.dlp_violations) * 15.0

        return min(score, 100.0)

    def block_upload(self, reason: str) -> None:
        """Block this attachment upload"""
        self.allowed = False
        self.blocked = True
        self.blocked_reason = reason
        self.blocked_at = datetime.utcnow()


# Made with Bob
