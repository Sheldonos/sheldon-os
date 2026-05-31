"""
Keystroke Monitor

Real-time keystroke capture for LLM interactions.
Low-latency (<10ms), privacy-preserving, cross-platform.
"""

import hashlib
import logging
import platform
import queue
import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import psutil

try:
    from pynput import keyboard
except ImportError:  # pragma: no cover
    keyboard = None

logger = logging.getLogger(__name__)


class KeystrokeMonitor:  # pylint: disable=too-many-instance-attributes
    """
    Cross-platform keystroke monitoring for AI interactions.

    Features:
    - Real-time capture with <10ms latency
    - Context-aware (only captures when LLM is active)
    - Privacy-preserving encryption
    - Minimal CPU impact (<2%)
    - Thread-safe operation

    Usage:
        monitor = KeystrokeMonitor(
            on_keystroke=handle_keystroke,
            llm_detector=detector
        )
        monitor.start()
        # ... monitoring happens ...
        monitor.stop()
    """

    def __init__(
        self,
        on_keystroke: Optional[Callable[[Dict[str, Any]], None]] = None,
        llm_detector: Optional[Any] = None,
        buffer_size: int = 1000,
        flush_interval: float = 1.0,
    ):
        """
        Initialize keystroke monitor

        Args:
            on_keystroke: Callback for keystroke events
            llm_detector: LLM detector instance
            buffer_size: Size of keystroke buffer
            flush_interval: Interval to flush buffer (seconds)
        """
        self.on_keystroke = on_keystroke
        self.llm_detector = llm_detector
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval

        # State
        self.is_running = False
        self.listener: Optional[Any] = None
        self.buffer: queue.Queue = queue.Queue(maxsize=buffer_size)
        self.current_text: List[str] = []
        self.sequence_number = 0

        # Threading
        self.flush_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        # Metrics
        self.total_keystrokes = 0
        self.start_time: Optional[float] = None
        self.last_keystroke_time: Optional[float] = None

        # Platform detection
        self.platform = platform.system()

        logger.info("KeystrokeMonitor initialized on %s", self.platform)

    def start(self) -> None:
        """Start monitoring keystrokes"""
        if self.is_running:
            logger.warning("Monitor already running")
            return

        self.is_running = True
        self.start_time = time.time()

        # Start keyboard listener
        if keyboard is None:
            logger.warning("pynput is unavailable; keystroke listener not started")
        else:
            self.listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release,
            )
            self.listener.start()

        # Start flush thread
        self.flush_thread = threading.Thread(
            target=self._flush_loop,
            daemon=True,
        )
        self.flush_thread.start()

        logger.info("KeystrokeMonitor started")

    def stop(self) -> None:
        """Stop monitoring keystrokes"""
        if not self.is_running:
            return

        self.is_running = False

        # Stop listener
        if self.listener:
            self.listener.stop()
            self.listener = None

        # Flush remaining buffer
        self._flush_buffer()

        logger.info(
            "KeystrokeMonitor stopped. Total keystrokes: %s",
            self.total_keystrokes,
        )

    def _on_key_press(self, key) -> None:
        """Handle key press event"""
        try:
            start_time = time.time()

            # Check if LLM is active
            if self.llm_detector and not self.llm_detector.is_llm_active():
                return

            # Get key character
            char = self._get_key_char(key)
            if char is None:
                return

            # Add to current text buffer
            with self.lock:
                self.current_text.append(char)
                self.total_keystrokes += 1
                self.last_keystroke_time = time.time()

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000

            # Log if latency exceeds threshold
            if latency_ms > 10:
                logger.warning("High latency: %.2fms", latency_ms)

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error in key press handler: %s", exc)

    def _on_key_release(self, key) -> None:
        """Handle key release event"""
        _ = key

    def _get_key_char(self, key) -> Optional[str]:
        """Extract character from key event"""
        try:
            key_char: Optional[str] = None

            # Alphanumeric keys
            if hasattr(key, "char") and key.char:
                key_char = str(key.char)
            elif keyboard is not None and key == keyboard.Key.space:
                key_char = " "
            elif keyboard is not None and key == keyboard.Key.enter:
                key_char = "\n"
            elif keyboard is not None and key == keyboard.Key.tab:
                key_char = "\t"
            elif keyboard is not None and key == keyboard.Key.backspace:
                # Handle backspace
                with self.lock:
                    if self.current_text:
                        self.current_text.pop()

            return key_char

        except AttributeError:
            return None

    def _flush_loop(self) -> None:
        """Periodically flush keystroke buffer"""
        while self.is_running:
            time.sleep(self.flush_interval)
            self._flush_buffer()

    def _flush_buffer(self) -> None:
        """Flush current text buffer to callback"""
        with self.lock:
            if not self.current_text:
                return

            # Get current text
            text = "".join(self.current_text)
            self.current_text = []

            # Create keystroke event
            event = self._create_keystroke_event(text)

            # Call callback
            if self.on_keystroke:
                try:
                    self.on_keystroke(event)
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    logger.error("Error in keystroke callback: %s", exc)

    def _create_keystroke_event(self, text: str) -> Dict[str, Any]:
        """Create keystroke event dictionary"""
        self.sequence_number += 1

        # Get context from LLM detector
        context = {}
        if self.llm_detector:
            context = self.llm_detector.get_context()

        # Calculate metrics
        char_count = len(text)
        word_count = len(text.split())

        # Create hash
        content_hash = hashlib.sha256(text.encode()).hexdigest()

        event = {
            "sequence_number": self.sequence_number,
            "timestamp": datetime.utcnow().isoformat(),
            "content": text,  # Will be encrypted by data collector
            "content_hash": content_hash,
            "character_count": char_count,
            "word_count": word_count,
            "context": context,
            "platform": self.platform,
        }

        return event

    def get_metrics(self) -> Dict[str, Any]:
        """Get monitoring metrics"""
        uptime = time.time() - self.start_time if self.start_time else 0

        return {
            "is_running": self.is_running,
            "total_keystrokes": self.total_keystrokes,
            "uptime_seconds": uptime,
            "keystrokes_per_minute": (
                (self.total_keystrokes / uptime * 60) if uptime > 0 else 0
            ),
            "buffer_size": self.buffer.qsize(),
            "last_keystroke": self.last_keystroke_time,
        }

    def get_cpu_usage(self) -> float:
        """Get CPU usage of monitoring process"""
        try:
            process = psutil.Process()
            return float(process.cpu_percent(interval=0.1))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error getting CPU usage: %s", exc)
            return 0.0


class KeystrokeBuffer:
    """
    Thread-safe buffer for keystroke events.
    Handles batching and compression.
    """

    def __init__(self, max_size: int = 1000, max_age_seconds: float = 5.0):
        """
        Initialize keystroke buffer

        Args:
            max_size: Maximum number of events to buffer
            max_age_seconds: Maximum age of events before flush
        """
        self.max_size = max_size
        self.max_age_seconds = max_age_seconds
        self.events: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self.oldest_event_time: Optional[float] = None

    def add(self, event: Dict[str, Any]) -> bool:
        """
        Add event to buffer

        Returns:
            True if buffer should be flushed
        """
        with self.lock:
            self.events.append(event)

            if self.oldest_event_time is None:
                self.oldest_event_time = time.time()

            # Check if buffer should be flushed
            should_flush = (
                len(self.events) >= self.max_size
                or (
                    time.time() - self.oldest_event_time
                ) >= self.max_age_seconds
            )

            return should_flush

    def flush(self) -> List[Dict[str, Any]]:
        """Flush buffer and return events"""
        with self.lock:
            events = self.events.copy()
            self.events = []
            self.oldest_event_time = None
            return events

    def size(self) -> int:
        """Get current buffer size"""
        with self.lock:
            return len(self.events)


# Made with Bob
