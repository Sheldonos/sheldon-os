"""
MCP Health Monitor
Monitors health of MCP servers and triggers recovery
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict

from .server_registry import MCPServerRegistry, ServerStatus

logger = logging.getLogger(__name__)


class MCPHealthMonitor:
    """
    Health monitor for MCP servers
    Performs periodic health checks and triggers recovery
    """

    def __init__(
        self,
        registry: MCPServerRegistry,
        check_interval: int = 30,
        failure_threshold: int = 3,
    ):
        self.registry = registry
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._failure_counts: Dict[str, int] = {}
        self._failure_callbacks: list[Callable] = []
        logger.info(
            "MCP Health Monitor initialized (interval=%ss, threshold=%s)",
            check_interval,
            failure_threshold,
        )

    async def start_monitoring(self, server_id: str):
        """
        Start monitoring a server

        Args:
            server_id: Server identifier
        """
        if server_id in self._monitoring_tasks:
            logger.warning("Already monitoring server %s", server_id)
            return

        # Reset failure count
        self._failure_counts[server_id] = 0

        # Create monitoring task
        task = asyncio.create_task(self._monitor_server(server_id))
        self._monitoring_tasks[server_id] = task

        logger.info("Started monitoring server %s", server_id)

    async def stop_monitoring(self, server_id: str):
        """
        Stop monitoring a server

        Args:
            server_id: Server identifier
        """
        if server_id not in self._monitoring_tasks:
            logger.warning("Not monitoring server %s", server_id)
            return

        # Cancel monitoring task
        self._monitoring_tasks[server_id].cancel()
        del self._monitoring_tasks[server_id]

        # Clean up failure count
        if server_id in self._failure_counts:
            del self._failure_counts[server_id]

        logger.info("Stopped monitoring server %s", server_id)

    async def _monitor_server(self, server_id: str):
        """
        Monitor a server continuously

        Args:
            server_id: Server identifier
        """
        logger.debug("Monitoring loop started for server %s", server_id)

        try:
            while True:
                await asyncio.sleep(self.check_interval)

                # Perform health check
                is_healthy = await self._check_server_health(server_id)

                if is_healthy:
                    # Reset failure count on success
                    self._failure_counts[server_id] = 0

                    # Update heartbeat
                    await self.registry.update_heartbeat(server_id)
                else:
                    # Increment failure count
                    self._failure_counts[server_id] = (
                        self._failure_counts.get(server_id, 0) + 1
                    )

                    logger.warning(
                        "Health check failed for server %s (%s/%s)",
                        server_id,
                        self._failure_counts[server_id],
                        self.failure_threshold,
                    )

                    # Check if threshold exceeded
                    if (
                        self._failure_counts[server_id]
                        >= self.failure_threshold
                    ):
                        logger.error(
                            "Server %s exceeded failure threshold",
                            server_id,
                        )
                        await self._handle_server_failure(server_id)

        except asyncio.CancelledError:
            logger.debug("Monitoring cancelled for server %s", server_id)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error(
                "Error in monitoring loop for server %s: %s",
                server_id,
                exc,
            )

    async def _check_server_health(self, server_id: str) -> bool:
        """
        Check if a server is healthy

        Args:
            server_id: Server identifier

        Returns:
            bool: True if server is healthy
        """
        try:
            server_info = await self.registry.get_server(server_id)
            if not server_info:
                logger.error("Server %s not found in registry", server_id)
                return False

            # Check if server is in running state
            if server_info.status != ServerStatus.RUNNING:
                return False

            # Check last heartbeat time
            if server_info.last_heartbeat:
                time_since_heartbeat = (
                    datetime.utcnow() - server_info.last_heartbeat
                )
                max_heartbeat_age = timedelta(seconds=self.check_interval * 2)

                if time_since_heartbeat > max_heartbeat_age:
                    logger.warning(
                        "Server %s heartbeat too old: %ss",
                        server_id,
                        time_since_heartbeat.total_seconds(),
                    )
                    return False

            return True

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error(
                "Error checking health for server %s: %s",
                server_id,
                exc,
            )
            return False

    async def _handle_server_failure(self, server_id: str):
        """
        Handle server failure

        Args:
            server_id: Server identifier
        """
        logger.error("Handling failure for server %s", server_id)

        # Update server status
        await self.registry.update_server_status(
            server_id,
            ServerStatus.UNHEALTHY,
            f"Failed {self.failure_threshold} consecutive health checks",
        )

        # Notify failure callbacks
        for callback in self._failure_callbacks:
            try:
                await callback(server_id)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.error("Error in failure callback: %s", exc)

    def add_failure_callback(self, callback: Callable):
        """
        Add a callback for server failures

        Args:
            callback: Async callback function(server_id)
        """
        self._failure_callbacks.append(callback)
        logger.debug("Added failure callback: %s", callback.__name__)

    def remove_failure_callback(self, callback: Callable):
        """
        Remove a failure callback

        Args:
            callback: Callback function to remove
        """
        if callback in self._failure_callbacks:
            self._failure_callbacks.remove(callback)
            logger.debug("Removed failure callback: %s", callback.__name__)

    async def get_health_status(self, server_id: str) -> Dict[str, Any]:
        """
        Get health status for a server

        Args:
            server_id: Server identifier

        Returns:
            Dict[str, any]: Health status information
        """
        server_info = await self.registry.get_server(server_id)
        if not server_info:
            return {"error": "Server not found"}

        is_monitoring = server_id in self._monitoring_tasks
        failure_count = self._failure_counts.get(server_id, 0)

        return {
            "server_id": server_id,
            "status": server_info.status.value,
            "is_monitoring": is_monitoring,
            "failure_count": failure_count,
            "failure_threshold": self.failure_threshold,
            "last_heartbeat": (
                server_info.last_heartbeat.isoformat()
                if server_info.last_heartbeat
                else None
            ),
            "error_message": server_info.error_message,
        }

    async def get_all_health_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get health status for all monitored servers

        Returns:
            Dict[str, Dict[str, any]]: Health status for all servers
        """
        status = {}
        for server_id in self._monitoring_tasks:
            status[server_id] = await self.get_health_status(server_id)
        return status

    async def shutdown(self):
        """Shutdown health monitor"""
        logger.info("Shutting down MCP Health Monitor")

        # Cancel all monitoring tasks
        for server_id in list(self._monitoring_tasks.keys()):
            await self.stop_monitoring(server_id)

        logger.info("MCP Health Monitor shutdown complete")


# Made with Bob
