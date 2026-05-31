"""
Endpoint Agent

Cross-platform monitoring agent for AI usage traceability.
Captures keystrokes, tracks attachments, and detects LLM usage.

Components:
- keystroke_monitor: Real-time keystroke capture
- attachment_tracker: File upload monitoring
- llm_detector: LLM platform detection
- data_collector: Data aggregation and encryption
- agent_installer: Cross-platform installation
"""

from .attachment_tracker import AttachmentTracker
from .data_collector import DataCollector
from .keystroke_monitor import KeystrokeMonitor
from .llm_detector import LLMDetector

__all__ = [
    "KeystrokeMonitor",
    "AttachmentTracker",
    "LLMDetector",
    "DataCollector",
]

# Made with Bob
