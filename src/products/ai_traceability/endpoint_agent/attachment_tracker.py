"""
Attachment Tracker

Monitors file uploads to LLM platforms.
Tracks metadata, performs security scanning, and enforces DLP policies.
"""

import hashlib
import logging
import mimetypes
import os
import queue
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class AttachmentTracker:  # pylint: disable=too-many-instance-attributes
    """
    File upload monitoring for LLM platforms.

    Features:
    - Real-time upload detection
    - File metadata extraction
    - Content classification
    - Security scanning
    - DLP policy enforcement
    - Hash calculation for deduplication

    Usage:
        tracker = AttachmentTracker(
            on_attachment=handle_attachment,
            llm_detector=detector
        )
        tracker.start()
    """

    def __init__(
        self,
        on_attachment: Optional[Callable[[Dict[str, Any]], None]] = None,
        llm_detector: Optional[Any] = None,
        scan_enabled: bool = True,
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
    ):
        """
        Initialize attachment tracker

        Args:
            on_attachment: Callback for attachment events
            llm_detector: LLM detector instance
            scan_enabled: Enable security scanning
            max_file_size: Maximum file size to track (bytes)
        """
        self.on_attachment = on_attachment
        self.llm_detector = llm_detector
        self.scan_enabled = scan_enabled
        self.max_file_size = max_file_size

        # State
        self.is_running = False
        self.tracked_files: Dict[str, Dict[str, Any]] = {}
        self.upload_queue: queue.Queue = queue.Queue()

        # Threading
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        # Metrics
        self.total_attachments = 0
        self.total_bytes = 0
        self.blocked_attachments = 0

        logger.info("AttachmentTracker initialized")

    def start(self) -> None:
        """Start monitoring attachments"""
        if self.is_running:
            logger.warning("Tracker already running")
            return

        self.is_running = True

        # Start monitor thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
        )
        self.monitor_thread.start()

        logger.info("AttachmentTracker started")

    def stop(self) -> None:
        """Stop monitoring attachments"""
        if not self.is_running:
            return

        self.is_running = False

        logger.info(
            "AttachmentTracker stopped. Total: %s, Blocked: %s",
            self.total_attachments,
            self.blocked_attachments,
        )

    def track_upload(
        self, file_path: str, destination: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track a file upload

        Args:
            file_path: Path to file being uploaded
            destination: Destination URL or platform

        Returns:
            Attachment metadata
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error("File not found: %s", file_path)
                return {}

            # Get file info
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size

            # Check size limit
            if file_size > self.max_file_size:
                logger.warning("File too large: %s bytes", file_size)
                return self._create_blocked_attachment(
                    file_path,
                    "File too large",
                )

            # Extract metadata
            metadata = self._extract_metadata(file_path, file_size)

            # Get LLM context
            if self.llm_detector:
                context = self.llm_detector.get_context()
                metadata["llm_platform"] = context.get("platform", "unknown")
                metadata["destination"] = (
                    destination or context.get("window_title", "")
                )

            # Perform security scan
            if self.scan_enabled:
                scan_result = self._scan_file(file_path)
                metadata["scan_result"] = scan_result

                if scan_result.get("malicious", False):
                    return self._create_blocked_attachment(
                        file_path, "Malware detected"
                    )

            # Classify content
            classification = self._classify_content(file_path, metadata)
            metadata["classification"] = classification

            # Check DLP policies
            dlp_result = self._check_dlp_policies(metadata)
            if not dlp_result["allowed"]:
                return self._create_blocked_attachment(
                    file_path,
                    dlp_result["reason"],
                )

            # Track attachment
            with self.lock:
                self.tracked_files[metadata["hash_sha256"]] = metadata
                self.total_attachments += 1
                self.total_bytes += file_size

            # Call callback
            if self.on_attachment:
                try:
                    self.on_attachment(metadata)
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    logger.error("Error in attachment callback: %s", exc)

            logger.info(
                "Tracked attachment: %s (%s bytes)",
                metadata["filename"],
                file_size,
            )
            return metadata

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error tracking upload: %s", exc)
            return {}

    def _extract_metadata(
        self,
        file_path: str,
        file_size: int,
    ) -> Dict[str, Any]:
        """Extract file metadata"""
        path = Path(file_path)

        # Calculate hashes
        hash_md5, hash_sha256 = self._calculate_hashes(file_path)

        # Get MIME type
        mime_type, _ = mimetypes.guess_type(file_path)

        metadata = {
            "filename": path.name,
            "file_extension": path.suffix.lstrip("."),
            "file_path": str(path.absolute()),
            "size_bytes": file_size,
            "hash_md5": hash_md5,
            "hash_sha256": hash_sha256,
            "mime_type": mime_type or "application/octet-stream",
            "uploaded_at": datetime.utcnow().isoformat(),
            "modified_at": datetime.fromtimestamp(
                os.path.getmtime(file_path)
            ).isoformat(),
        }

        return metadata

    def _calculate_hashes(self, file_path: str) -> tuple:
        """Calculate MD5 and SHA-256 hashes"""
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                # Read in chunks for large files
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
                    sha256_hash.update(chunk)

            return md5_hash.hexdigest(), sha256_hash.hexdigest()

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error calculating hashes: %s", exc)
            return "", ""

    def _scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        Perform security scan on file

        In production, this would integrate with:
        - ClamAV for malware scanning
        - YARA rules for pattern matching
        - Cloud-based scanning services
        """
        _ = file_path
        # Placeholder for security scanning
        scan_result = {
            "scanned": True,
            "scan_time": datetime.utcnow().isoformat(),
            "malicious": False,
            "threats": [],
            "scanner": "placeholder",
        }

        # Placeholder for future scanner integration.
        # Example: ClamAV, VirusTotal API, etc.

        return scan_result

    def _classify_content(
        self,
        file_path: str,
        metadata: Dict[str, Any],
    ) -> str:
        """
        Classify file content

        Returns classification level:
        public, internal, confidential, restricted
        """
        _ = file_path
        # Simple classification based on file type and name
        filename = metadata["filename"].lower()
        extension = metadata["file_extension"].lower()

        # Check for sensitive keywords in filename
        sensitive_keywords = [
            "confidential",
            "secret",
            "private",
            "internal",
            "ssn",
            "password",
            "credential",
            "financial",
        ]

        if any(keyword in filename for keyword in sensitive_keywords):
            return "confidential"

        # Classify by file type
        sensitive_extensions = ["key", "pem", "p12", "pfx", "cer"]
        if extension in sensitive_extensions:
            return "restricted"

        # Default classification
        return "internal"

    def _check_dlp_policies(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check DLP policies

        In production, this would integrate with enterprise DLP systems
        """
        # Placeholder for DLP policy checking
        result = {
            "allowed": True,
            "reason": "",
            "policies_checked": [],
        }

        # Example policy: Block files with "confidential" classification
        if metadata.get("classification") == "restricted":
            result["allowed"] = False
            result["reason"] = "Restricted content not allowed"

        # Placeholder for future DLP integration.

        return result

    def _create_blocked_attachment(
        self,
        file_path: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Create metadata for blocked attachment"""
        with self.lock:
            self.blocked_attachments += 1

        return {
            "filename": Path(file_path).name,
            "blocked": True,
            "blocked_reason": reason,
            "blocked_at": datetime.utcnow().isoformat(),
        }

    def _monitor_loop(self) -> None:
        """Monitor loop for file system changes"""
        # This would integrate with file system watchers
        # to detect uploads in real-time
        while self.is_running:
            try:
                # Process upload queue
                if not self.upload_queue.empty():
                    upload_info = self.upload_queue.get(timeout=1)
                    self.track_upload(**upload_info)
            except queue.Empty:
                pass
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.error("Error in monitor loop: %s", exc)

    def get_metrics(self) -> Dict[str, Any]:
        """Get tracking metrics"""
        return {
            "is_running": self.is_running,
            "total_attachments": self.total_attachments,
            "total_bytes": self.total_bytes,
            "blocked_attachments": self.blocked_attachments,
            "tracked_files_count": len(self.tracked_files),
        }

    def get_tracked_files(self) -> List[Dict[str, Any]]:
        """Get list of tracked files"""
        with self.lock:
            return list(self.tracked_files.values())


class FileSystemWatcher:
    """
    Watches file system for upload activity.
    Detects when files are being uploaded to browsers or apps.
    """

    def __init__(
        self,
        tracker: AttachmentTracker,
        watch_paths: Optional[List[str]] = None,
    ):
        """
        Initialize file system watcher

        Args:
            tracker: Attachment tracker instance
            watch_paths: Paths to watch
            (default: Downloads, Desktop, Documents)
        """
        self.tracker = tracker
        self.watch_paths = watch_paths or self._get_default_paths()
        self.is_running = False

    def _get_default_paths(self) -> List[str]:
        """Get default paths to watch"""
        home = Path.home()
        return [
            str(home / "Downloads"),
            str(home / "Desktop"),
            str(home / "Documents"),
        ]

    def start(self) -> None:
        """Start watching file system"""
        self.is_running = True

    def stop(self) -> None:
        """Stop watching file system"""
        self.is_running = False


# Made with Bob
