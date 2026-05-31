"""
MCP Server Manager
Manages MCP server lifecycle and connections
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from .health_monitor import MCPHealthMonitor
from .protocol import MCPProtocol
from .server_registry import MCPServerRegistry, ServerStatus

logger = logging.getLogger(__name__)


class MCPServerManager:
    """
    Manages MCP server lifecycle
    Handles starting, stopping, and monitoring servers
    """

    def __init__(
        self,
        registry: Optional[MCPServerRegistry] = None,
        health_monitor: Optional[MCPHealthMonitor] = None,
    ):
        self.registry = registry or MCPServerRegistry()
        self.health_monitor = health_monitor or MCPHealthMonitor(self.registry)
        self._connections: Dict[str, MCPProtocol] = {}
        self._restart_tasks: Dict[str, asyncio.Task] = {}
        self._auto_restart_enabled = True
        logger.info("MCP Server Manager initialized")

    async def start_server(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        server_id: str,
        name: str,
        version: str,
        endpoint: str,
        capabilities: list,
        metadata: Optional[Dict[str, Any]] = None,
        auto_connect: bool = True,
    ) -> bool:
        """
        Start an MCP server

        Args:
            server_id: Unique server identifier
            name: Server name
            version: Server version
            endpoint: Server endpoint URL
            capabilities: List of capabilities
            metadata: Additional metadata
            auto_connect: Automatically connect after registration

        Returns:
            bool: True if server started successfully
        """
        try:
            # Register server
            await self.registry.register_server(
                server_id=server_id,
                name=name,
                version=version,
                endpoint=endpoint,
                capabilities=capabilities,
                metadata=metadata,
            )

            logger.info("Starting MCP server: %s (%s)", name, server_id)

            # Update status to starting
            await self.registry.update_server_status(
                server_id,
                ServerStatus.STARTING,
            )

            # Connect if auto_connect enabled
            if auto_connect:
                success = await self.connect_server(server_id)
                if not success:
                    await self.registry.update_server_status(
                        server_id, ServerStatus.ERROR, "Failed to connect"
                    )
                    return False

            # Start health monitoring
            await self.health_monitor.start_monitoring(server_id)

            # Update status to running
            await self.registry.update_server_status(
                server_id,
                ServerStatus.RUNNING,
            )

            logger.info("MCP server started: %s (%s)", name, server_id)
            return True

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error starting server %s: %s", server_id, exc)
            await self.registry.update_server_status(
                server_id, ServerStatus.ERROR, str(exc)
            )
            return False

    async def stop_server(self, server_id: str, graceful: bool = True) -> bool:
        """
        Stop an MCP server

        Args:
            server_id: Server identifier
            graceful: Perform graceful shutdown

        Returns:
            bool: True if server stopped successfully
        """
        try:
            server_info = await self.registry.get_server(server_id)
            if not server_info:
                logger.warning("Server %s not found", server_id)
                return False

            logger.info(
                "Stopping MCP server: %s (%s)",
                server_info.name,
                server_id,
            )

            _ = graceful
            # Update status
            await self.registry.update_server_status(
                server_id,
                ServerStatus.STOPPING,
            )

            # Stop health monitoring
            await self.health_monitor.stop_monitoring(server_id)

            # Cancel restart task if exists
            if server_id in self._restart_tasks:
                self._restart_tasks[server_id].cancel()
                del self._restart_tasks[server_id]

            # Disconnect
            if server_id in self._connections:
                await self._connections[server_id].disconnect()
                del self._connections[server_id]

            # Update status
            await self.registry.update_server_status(
                server_id,
                ServerStatus.STOPPED,
            )

            logger.info(
                "MCP server stopped: %s (%s)",
                server_info.name,
                server_id,
            )
            return True

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error stopping server %s: %s", server_id, exc)
            return False

    async def restart_server(self, server_id: str) -> bool:
        """
        Restart an MCP server

        Args:
            server_id: Server identifier

        Returns:
            bool: True if server restarted successfully
        """
        logger.info("Restarting MCP server: %s", server_id)

        # Get server info before stopping
        server_info = await self.registry.get_server(server_id)
        if not server_info:
            logger.error("Server %s not found", server_id)
            return False

        # Stop server
        await self.stop_server(server_id, graceful=True)

        # Wait a bit
        await asyncio.sleep(1)

        # Start server again
        return await self.start_server(
            server_id=server_info.server_id,
            name=server_info.name,
            version=server_info.version,
            endpoint=server_info.endpoint,
            capabilities=server_info.capabilities,
            metadata=server_info.metadata,
        )

    async def connect_server(self, server_id: str) -> bool:
        """
        Connect to an MCP server

        Args:
            server_id: Server identifier

        Returns:
            bool: True if connected successfully
        """
        try:
            server_info = await self.registry.get_server(server_id)
            if not server_info:
                logger.error("Server %s not found", server_id)
                return False

            # Create protocol connection
            protocol = MCPProtocol(server_info.endpoint)

            # Connect
            success = await protocol.connect()
            if not success:
                logger.error("Failed to connect to server %s", server_id)
                return False

            # Store connection
            self._connections[server_id] = protocol

            logger.info(
                "Connected to MCP server: %s (%s)",
                server_info.name,
                server_id,
            )
            return True

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error connecting to server %s: %s", server_id, exc)
            return False

    async def disconnect_server(self, server_id: str) -> bool:
        """
        Disconnect from an MCP server

        Args:
            server_id: Server identifier

        Returns:
            bool: True if disconnected successfully
        """
        try:
            if server_id not in self._connections:
                logger.warning(
                    "No connection found for server %s", server_id
                )
                return False

            await self._connections[server_id].disconnect()
            del self._connections[server_id]

            logger.info("Disconnected from MCP server: %s", server_id)
            return True

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error(
                "Error disconnecting from server %s: %s",
                server_id,
                exc,
            )
            return False

    async def execute_tool(
        self, server_id: str, tool_name: str, parameters: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Execute a tool on an MCP server

        Args:
            server_id: Server identifier
            tool_name: Tool name
            parameters: Tool parameters

        Returns:
            Optional[Any]: Tool execution result
        """
        try:
            if server_id not in self._connections:
                logger.error("No connection to server %s", server_id)
                return None

            protocol = self._connections[server_id]
            result = await protocol.execute_tool(tool_name, parameters)

            return result

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error(
                "Error executing tool %s on server %s: %s",
                tool_name,
                server_id,
                exc,
            )
            return None

    async def handle_server_failure(self, server_id: str):
        """
        Handle server failure

        Args:
            server_id: Server identifier
        """
        logger.warning("Handling failure for server %s", server_id)

        # Update status
        await self.registry.update_server_status(
            server_id, ServerStatus.UNHEALTHY, "Server health check failed"
        )

        # Auto-restart if enabled
        if self._auto_restart_enabled:
            logger.info(
                "Scheduling auto-restart for server %s", server_id
            )

            # Cancel existing restart task
            if server_id in self._restart_tasks:
                self._restart_tasks[server_id].cancel()

            # Schedule restart
            task = asyncio.create_task(self._auto_restart_server(server_id))
            self._restart_tasks[server_id] = task

    async def _auto_restart_server(self, server_id: str):
        """
        Auto-restart a failed server with exponential backoff

        Args:
            server_id: Server identifier
        """
        max_attempts = 5
        base_delay = 5  # seconds

        for attempt in range(max_attempts):
            delay = base_delay * (2**attempt)
            logger.info(
                "Auto-restart attempt %s/%s for server %s in %ss",
                attempt + 1,
                max_attempts,
                server_id,
                delay,
            )

            await asyncio.sleep(delay)

            success = await self.restart_server(server_id)
            if success:
                logger.info(
                    "Successfully restarted server %s", server_id
                )
                if server_id in self._restart_tasks:
                    del self._restart_tasks[server_id]
                return

        logger.error(
            "Failed to restart server %s after %s attempts",
            server_id,
            max_attempts,
        )
        await self.registry.update_server_status(
            server_id,
            ServerStatus.ERROR,
            f"Failed to restart after {max_attempts} attempts",
        )

    async def get_server_connection(
        self,
        server_id: str,
    ) -> Optional[MCPProtocol]:
        """
        Get server connection

        Args:
            server_id: Server identifier

        Returns:
            Optional[MCPProtocol]: Protocol connection or None
        """
        return self._connections.get(server_id)

    async def list_connections(self) -> Dict[str, MCPProtocol]:
        """
        List all active connections

        Returns:
            Dict[str, MCPProtocol]: Active connections
        """
        return self._connections.copy()

    def enable_auto_restart(self):
        """Enable automatic server restart on failure"""
        self._auto_restart_enabled = True
        logger.info("Auto-restart enabled")

    def disable_auto_restart(self):
        """Disable automatic server restart on failure"""
        self._auto_restart_enabled = False
        logger.info("Auto-restart disabled")

    async def shutdown(self):
        """Shutdown all servers and cleanup"""
        logger.info("Shutting down MCP Server Manager")

        # Stop all servers
        server_ids = list(self._connections.keys())
        for server_id in server_ids:
            await self.stop_server(server_id)

        # Stop health monitor
        await self.health_monitor.shutdown()

        logger.info("MCP Server Manager shutdown complete")


# Made with Bob
