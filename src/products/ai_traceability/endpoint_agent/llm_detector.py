"""
LLM Detector

Detects LLM platform usage across browsers, desktop apps, and APIs.
Provides context about active LLM sessions.
"""

import logging
import platform
import subprocess
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import psutil

try:
    import win32gui
    import win32process
except ImportError:  # pragma: no cover
    win32gui = None
    win32process = None

logger = logging.getLogger(__name__)


class LLMDetector:
    """
    Cross-platform LLM usage detector.

    Detects:
    - Browser-based LLMs (ChatGPT, Claude, Gemini, etc.)
    - Desktop apps (ChatGPT app, Claude app)
    - API usage
    - Custom LLM deployments

    Features:
    - Real-time detection
    - Context extraction (URL, window title, app name)
    - Platform identification
    - Session tracking
    """

    # Known LLM platforms and their identifiers
    LLM_PLATFORMS = {
        "chatgpt": {
            "urls": ["chat.openai.com", "chatgpt.com"],
            "processes": ["ChatGPT"],
            "window_titles": ["ChatGPT"],
        },
        "claude": {
            "urls": ["claude.ai", "anthropic.com/claude"],
            "processes": ["Claude"],
            "window_titles": ["Claude"],
        },
        "gemini": {
            "urls": ["gemini.google.com", "bard.google.com"],
            "processes": ["Gemini"],
            "window_titles": ["Gemini", "Bard"],
        },
        "copilot": {
            "urls": ["copilot.microsoft.com", "bing.com/chat"],
            "processes": ["Copilot", "Microsoft Copilot"],
            "window_titles": ["Copilot", "Microsoft Copilot"],
        },
        "perplexity": {
            "urls": ["perplexity.ai"],
            "processes": ["Perplexity"],
            "window_titles": ["Perplexity"],
        },
    }

    # Browser process names
    BROWSERS = [
        "chrome",
        "firefox",
        "safari",
        "edge",
        "brave",
        "opera",
        "Chrome",
        "Firefox",
        "Safari",
        "Edge",
        "Brave",
        "Opera",
        "Google Chrome",
        "Mozilla Firefox",
        "Microsoft Edge",
    ]

    def __init__(self, check_interval: float = 1.0):
        """
        Initialize LLM detector

        Args:
            check_interval: Interval to check for LLM activity (seconds)
        """
        self.check_interval = check_interval
        self.platform_system = platform.system()

        # State
        self.active_llm: Optional[str] = None
        self.active_context: Dict[str, Any] = {}
        self.detected_platforms: Set[str] = set()

        logger.info(
            "LLMDetector initialized on %s",
            self.platform_system,
        )

    def is_llm_active(self) -> bool:
        """Check if any LLM platform is currently active"""
        self._detect_active_llm()
        return self.active_llm is not None

    def get_active_platform(self) -> Optional[str]:
        """Get currently active LLM platform"""
        self._detect_active_llm()
        return self.active_llm

    def get_context(self) -> Dict[str, Any]:
        """Get context about active LLM session"""
        self._detect_active_llm()
        return self.active_context.copy()

    def _detect_active_llm(self) -> None:
        """Detect active LLM platform"""
        # Check browser-based LLMs
        browser_llm = self._detect_browser_llm()
        if browser_llm:
            self.active_llm = browser_llm
            return

        # Check desktop app LLMs
        app_llm = self._detect_app_llm()
        if app_llm:
            self.active_llm = app_llm
            return

        # No LLM detected
        self.active_llm = None
        self.active_context = {}

    def _detect_browser_llm(self) -> Optional[str]:
        """Detect LLM usage in browsers"""
        try:
            # Get active window info
            window_info = self._get_active_window()
            if not window_info:
                return None

            window_title = window_info.get("title", "").lower()
            process_name = window_info.get("process", "").lower()

            # Check if it's a browser
            is_browser = any(
                browser.lower() in process_name for browser in self.BROWSERS
            )
            if not is_browser:
                return None

            # Check window title for LLM platforms
            for platform_name, identifiers in self.LLM_PLATFORMS.items():
                # Check URLs in title
                for url in identifiers["urls"]:
                    if url in window_title:
                        self._update_context(
                            platform_name,
                            window_info,
                            "browser",
                        )
                        self.detected_platforms.add(platform_name)
                        return platform_name

                # Check window title patterns
                for title_pattern in identifiers["window_titles"]:
                    if title_pattern.lower() in window_title:
                        self._update_context(
                            platform_name,
                            window_info,
                            "browser",
                        )
                        self.detected_platforms.add(platform_name)
                        return platform_name

            return None

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error detecting browser LLM: %s", exc)
            return None

    def _detect_app_llm(self) -> Optional[str]:
        """Detect LLM desktop applications"""
        try:
            # Get running processes
            for proc in psutil.process_iter(["name", "exe"]):
                try:
                    proc_name = proc.info["name"]
                    matched_platform = self._match_process_to_platform(proc_name)
                    if matched_platform is None:
                        continue

                    self._update_context(
                        matched_platform,
                        {"process": proc_name},
                        "app",
                    )
                    self.detected_platforms.add(matched_platform)
                    return matched_platform

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return None

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error detecting app LLM: %s", exc)
            return None

    def _match_process_to_platform(self, proc_name: Optional[str]) -> Optional[str]:
        """Match a process name to a known LLM desktop platform."""
        if not proc_name:
            return None

        normalized_name = proc_name.lower()
        for platform_name, identifiers in self.LLM_PLATFORMS.items():
            for app_name in identifiers["processes"]:
                if app_name.lower() in normalized_name:
                    return platform_name
        return None

    def _get_active_window(self) -> Optional[Dict[str, Any]]:
        """Get active window information (platform-specific)"""
        try:
            if self.platform_system == "Darwin":  # macOS
                return self._get_active_window_macos()
            if self.platform_system == "Windows":
                return self._get_active_window_windows()
            if self.platform_system == "Linux":
                return self._get_active_window_linux()
            return None
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error getting active window: %s", exc)
            return None

    def _get_active_window_macos(self) -> Optional[Dict[str, Any]]:
        """Get active window on macOS"""
        try:
            # Use AppleScript to get active window
            script = (
                'tell application "System Events"\n'
                "set frontApp to name of first application process "
                'whose frontmost is true\n'
                "set frontWindow to name of front window of "
                "application process frontApp\n"
                'return frontApp & "|" & frontWindow\n'
                "end tell"
            )
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=1,
                check=False,
            )

            if result.returncode == 0:
                parts = result.stdout.strip().split("|")
                return {
                    "process": parts[0] if len(parts) > 0 else "",
                    "title": parts[1] if len(parts) > 1 else "",
                }

            return None

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.debug("Error getting macOS window: %s", exc)
            return None

    def _get_active_window_windows(self) -> Optional[Dict[str, Any]]:
        """Get active window on Windows"""
        try:
            if (
                self.platform_system != "Windows"
                or win32gui is None
                or win32process is None
            ):
                return None

            # Get foreground window
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)

            # Get process name
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)

            return {
                "process": process.name(),
                "title": title,
                "pid": pid,
            }

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.debug("Error getting Windows window: %s", exc)
            return None

    def _get_active_window_linux(self) -> Optional[Dict[str, Any]]:
        """Get active window on Linux"""
        try:
            # Use xdotool to get active window
            result = subprocess.run(
                ["xdotool", "getactivewindow", "getwindowname"],
                capture_output=True,
                text=True,
                timeout=1,
                check=False,
            )

            if result.returncode == 0:
                title = result.stdout.strip()

                # Get process name
                pid_result = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowpid"],
                    capture_output=True,
                    text=True,
                    timeout=1,
                    check=False,
                )

                if pid_result.returncode == 0:
                    pid = int(pid_result.stdout.strip())
                    process = psutil.Process(pid)

                    return {
                        "process": process.name(),
                        "title": title,
                        "pid": pid,
                    }

            return None

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.debug("Error getting Linux window: %s", exc)
            return None

    def _update_context(
        self, platform_name: str, window_info: Dict[str, Any], source: str
    ) -> None:
        """Update active context"""
        self.active_context = {
            "platform": platform_name,
            "source": source,  # 'browser' or 'app'
            "window_title": window_info.get("title", ""),
            "process_name": window_info.get("process", ""),
            "pid": window_info.get("pid"),
            "detected_at": datetime.utcnow().isoformat(),
            "platform_system": self.platform_system,
        }

    def get_all_detected_platforms(self) -> List[str]:
        """Get all platforms detected during session"""
        return list(self.detected_platforms)

    def reset_detection(self) -> None:
        """Reset detection state"""
        self.active_llm = None
        self.active_context = {}
        self.detected_platforms.clear()


class LLMSessionTracker:
    """
    Tracks LLM sessions over time.
    Detects session start/end and maintains session state.
    """

    def __init__(self, detector: LLMDetector, session_timeout: float = 300.0):
        """
        Initialize session tracker

        Args:
            detector: LLM detector instance
            session_timeout: Timeout for inactive sessions (seconds)
        """
        self.detector = detector
        self.session_timeout = session_timeout

        # Active sessions
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.current_session_id: Optional[str] = None

    def update(self) -> Optional[Dict[str, Any]]:
        """
        Update session tracking

        Returns:
            Session event if session started/ended, None otherwise
        """
        platform_name = self.detector.get_active_platform()

        if platform_name:
            # LLM is active
            if self.current_session_id is None:
                # New session started
                return self._start_session(platform_name)
            # Continue existing session
            self._update_session()
            return None
        # No LLM active
        if self.current_session_id:
            # Session ended
            return self._end_session()
        return None

    def _start_session(self, platform_name: str) -> Dict[str, Any]:
        """Start new session"""
        session_id = str(uuid.uuid4())
        self.current_session_id = session_id

        context = self.detector.get_context()

        session = {
            "session_id": session_id,
            "platform": platform_name,
            "start_time": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "context": context,
        }

        self.sessions[session_id] = session

        logger.info(
            "Session started: %s (%s)",
            session_id,
            platform_name,
        )

        return {
            "event": "session_start",
            "session": session,
        }

    def _update_session(self) -> None:
        """Update current session activity"""
        if (
            self.current_session_id
            and self.current_session_id in self.sessions
        ):
            self.sessions[self.current_session_id][
                "last_activity"
            ] = datetime.utcnow().isoformat()

    def _end_session(self) -> Dict[str, Any]:
        """End current session"""
        if not self.current_session_id:
            return {}

        session = self.sessions.get(self.current_session_id)
        if session:
            session["end_time"] = datetime.utcnow().isoformat()

            logger.info(
                "Session ended: %s",
                self.current_session_id,
            )

            event = {
                "event": "session_end",
                "session": session,
            }

            self.current_session_id = None
            return event

        return {}

    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """Get current active session"""
        if self.current_session_id:
            return self.sessions.get(self.current_session_id)
        return None


# Made with Bob
