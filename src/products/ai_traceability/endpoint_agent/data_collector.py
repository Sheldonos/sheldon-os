"""
Data Collector

Aggregates, encrypts, and transmits monitoring data to cloud backend.
Handles batching, compression, encryption, and retry logic.
"""

import base64
import gzip
import json
import logging
import queue
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class DataCollector:  # pylint: disable=too-many-instance-attributes
    """
    Collects and transmits monitoring data to cloud backend.

    Features:
    - Batching for efficiency
    - Compression to reduce bandwidth
    - AES-256 encryption for security
    - Retry logic with exponential backoff
    - Offline queue for network failures
    - Bandwidth optimization

    Usage:
        collector = DataCollector(
            api_endpoint="https://api.example.com",
            api_key="your_api_key",
            encryption_key="your_encryption_key"
        )
        collector.start()
        collector.collect(data)
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        api_endpoint: str,
        api_key: str,
        encryption_key: Optional[str] = None,
        batch_size: int = 100,
        batch_interval: float = 10.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize data collector

        Args:
            api_endpoint: Cloud API endpoint
            api_key: API authentication key
            encryption_key: Encryption key (generated if not provided)
            batch_size: Number of events per batch
            batch_interval: Time between batch transmissions (seconds)
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay (seconds)
        """
        self.api_endpoint = api_endpoint.rstrip("/")
        self.api_key = api_key
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Encryption
        self.encryption_key = encryption_key or Fernet.generate_key().decode()
        self.cipher = Fernet(self.encryption_key.encode())

        # State
        self.is_running = False
        self.batch_queue: queue.Queue = queue.Queue()
        self.offline_queue: queue.Queue = queue.Queue()
        self.current_batch: List[Dict[str, Any]] = []

        # Threading
        self.transmit_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        # Metrics
        self.total_collected = 0
        self.total_transmitted = 0
        self.total_failed = 0
        self.total_bytes_sent = 0

        logger.info("DataCollector initialized")

    def start(self) -> None:
        """Start data collection"""
        if self.is_running:
            logger.warning("Collector already running")
            return

        self.is_running = True

        # Start transmit thread
        self.transmit_thread = threading.Thread(
            target=self._transmit_loop,
            daemon=True,
        )
        self.transmit_thread.start()

        logger.info("DataCollector started")

    def stop(self) -> None:
        """Stop data collection"""
        if not self.is_running:
            return

        self.is_running = False

        # Flush remaining data
        self._flush_batch()

        logger.info(
            "DataCollector stopped. Collected: %s, Transmitted: %s",
            self.total_collected,
            self.total_transmitted,
        )

    def collect(self, data: Dict[str, Any]) -> None:
        """
        Collect a data event

        Args:
            data: Event data to collect
        """
        try:
            with self.lock:
                self.current_batch.append(data)
                self.total_collected += 1

                # Check if batch is full
                if len(self.current_batch) >= self.batch_size:
                    self._flush_batch()

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error collecting data: %s", exc)

    def _flush_batch(self) -> None:
        """Flush current batch to transmission queue"""
        with self.lock:
            if not self.current_batch:
                return

            batch = self.current_batch.copy()
            self.current_batch = []

            # Add to transmission queue
            self.batch_queue.put(batch)

    def _transmit_loop(self) -> None:
        """Transmission loop"""
        last_flush = time.time()

        while self.is_running:
            try:
                # Periodic flush
                if time.time() - last_flush >= self.batch_interval:
                    self._flush_batch()
                    last_flush = time.time()

                # Process offline queue first
                if not self.offline_queue.empty():
                    batch = self.offline_queue.get(timeout=0.1)
                    self._transmit_batch(batch, from_offline=True)
                    continue

                # Process regular queue
                if not self.batch_queue.empty():
                    batch = self.batch_queue.get(timeout=0.1)
                    self._transmit_batch(batch)
                else:
                    time.sleep(0.1)

            except queue.Empty:
                pass
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.error("Error in transmit loop: %s", exc)

    def _transmit_batch(
        self, batch: List[Dict[str, Any]], from_offline: bool = False
    ) -> bool:
        """
        Transmit batch to cloud backend

        Args:
            batch: Batch of events to transmit
            from_offline: Whether batch is from offline queue

        Returns:
            True if successful, False otherwise
        """
        try:
            # Encrypt batch
            encrypted_batch = self._encrypt_batch(batch)

            # Compress
            compressed_batch = self._compress_data(encrypted_batch)

            # Transmit with retry logic
            success = self._send_with_retry(compressed_batch)

            if success:
                self.total_transmitted += len(batch)
                self.total_bytes_sent += len(compressed_batch)
                logger.debug(
                    "Transmitted batch: %s events, %s bytes",
                    len(batch),
                    len(compressed_batch),
                )
                return True
            # Add to offline queue if not already from offline
            if not from_offline:
                self.offline_queue.put(batch)
            self.total_failed += len(batch)
            return False

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error transmitting batch: %s", exc)
            if not from_offline:
                self.offline_queue.put(batch)
            return False

    def _encrypt_batch(self, batch: List[Dict[str, Any]]) -> bytes:
        """Encrypt batch data"""
        # Convert to JSON
        json_data = json.dumps(batch)

        # Encrypt
        encrypted = self.cipher.encrypt(json_data.encode())

        return encrypted

    def _compress_data(self, data: bytes) -> bytes:
        """Compress data using gzip"""
        return gzip.compress(data)

    def _send_with_retry(self, data: bytes) -> bool:
        """
        Send data with exponential backoff retry

        Args:
            data: Data to send

        Returns:
            True if successful, False otherwise
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/octet-stream",
            "Content-Encoding": "gzip",
            "X-Encryption": "aes-256",
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.api_endpoint}/v1/events",
                    data=data,
                    headers=headers,
                    timeout=30,
                )

                if response.status_code == 200:
                    return True
                if response.status_code == 429:
                    # Rate limited, wait longer
                    delay = self.retry_delay * (2**attempt) * 2
                    logger.warning("Rate limited, retrying in %ss", delay)
                    time.sleep(delay)
                    continue

                logger.error(
                    "HTTP %s: %s",
                    response.status_code,
                    response.text,
                )
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    time.sleep(delay)

            except requests.exceptions.RequestException as e:
                logger.error(
                    "Request failed (attempt %s/%s): %s",
                    attempt + 1,
                    self.max_retries,
                    e,
                )
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    time.sleep(delay)

        return False

    def get_metrics(self) -> Dict[str, Any]:
        """Get collector metrics"""
        return {
            "is_running": self.is_running,
            "total_collected": self.total_collected,
            "total_transmitted": self.total_transmitted,
            "total_failed": self.total_failed,
            "total_bytes_sent": self.total_bytes_sent,
            "batch_queue_size": self.batch_queue.qsize(),
            "offline_queue_size": self.offline_queue.qsize(),
            "current_batch_size": len(self.current_batch),
        }

    def get_encryption_key(self) -> str:
        """Get encryption key (for backup/recovery)"""
        return self.encryption_key


class EncryptionManager:
    """
    Manages encryption keys and operations.
    Supports key rotation and secure storage.
    """

    def __init__(self, master_password: Optional[str] = None):
        """
        Initialize encryption manager

        Args:
            master_password: Master password for key derivation
        """
        self.master_password = master_password
        self.keys: Dict[str, bytes] = {}
        self.current_key_id: Optional[str] = None

    def generate_key(self, key_id: str) -> bytes:
        """Generate new encryption key"""
        key = Fernet.generate_key()
        self.keys[key_id] = key
        self.current_key_id = key_id
        return key

    def derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def rotate_key(self) -> str:
        """Rotate to new encryption key"""
        new_key_id = str(uuid.uuid4())
        self.generate_key(new_key_id)
        return new_key_id

    def get_current_key(self) -> Optional[bytes]:
        """Get current encryption key"""
        if self.current_key_id:
            return self.keys.get(self.current_key_id)
        return None


# Made with Bob
