"""
MCP Server Registry
Manages registration and discovery of MCP servers
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ServerStatus(Enum):
    """MCP Server status"""

    UNKNOWN = "unknown"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    UNHEALTHY = "unhealthy"


@dataclass
class MCPServerInfo:
    """Information about an MCP server"""

    server_id: str
    name: str
    version: str
    endpoint: str
    capabilities: List[str]
    status: ServerStatus = ServerStatus.UNKNOWN
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "server_id": self.server_id,
            "name": self.name,
            "version": self.version,
            "endpoint": self.endpoint,
            "capabilities": self.capabilities,
            "status": self.status.value,
            "metadata": self.metadata,
            "registered_at": self.registered_at.isoformat(),
            "last_heartbeat": (
                self.last_heartbeat.isoformat()
                if self.last_heartbeat
                else None
            ),
            "error_message": self.error_message,
        }


class MCPServerRegistry:
    """
    Registry for MCP servers
    Handles server registration, discovery, and lifecycle tracking
    """

    def __init__(self):
        self._servers: Dict[str, MCPServerInfo] = {}
        self._lock = asyncio.Lock()
        self._discovery_callbacks: List[Callable] = []
        logger.info("MCP Server Registry initialized")

    async def register_server(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        server_id: str,
        name: str,
        version: str,
        endpoint: str,
        capabilities: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MCPServerInfo:
        """
        Register a new MCP server

        Args:
            server_id: Unique server identifier
            name: Server name
            version: Server version
            endpoint: Server endpoint URL
            capabilities: List of server capabilities
            metadata: Additional server metadata

        Returns:
            MCPServerInfo: Registered server information
        """
        async with self._lock:
            if server_id in self._servers:
                logger.warning(
                    "Server %s already registered, updating", server_id
                )

            server_info = MCPServerInfo(
                server_id=server_id,
                name=name,
                version=version,
                endpoint=endpoint,
                capabilities=capabilities,
                status=ServerStatus.STARTING,
                metadata=metadata or {},
            )

            self._servers[server_id] = server_info
            logger.info("Registered MCP server: %s (%s)", name, server_id)

            # Notify discovery callbacks
            await self._notify_discovery_callbacks("registered", server_info)

            return server_info

    async def unregister_server(self, server_id: str) -> bool:
        """
        Unregister an MCP server

        Args:
            server_id: Server identifier

        Returns:
            bool: True if server was unregistered
        """
        async with self._lock:
            if server_id not in self._servers:
                logger.warning(
                    "Server %s not found for unregistration", server_id
                )
                return False

            server_info = self._servers[server_id]
            del self._servers[server_id]
            logger.info(
                "Unregistered MCP server: %s (%s)",
                server_info.name,
                server_id,
            )

            # Notify discovery callbacks
            await self._notify_discovery_callbacks("unregistered", server_info)

            return True

    async def update_server_status(
        self,
        server_id: str,
        status: ServerStatus,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Update server status

        Args:
            server_id: Server identifier
            status: New status
            error_message: Optional error message

        Returns:
            bool: True if status was updated
        """
        async with self._lock:
            if server_id not in self._servers:
                logger.warning(
                    "Server %s not found for status update", server_id
                )
                return False

            server_info = self._servers[server_id]
            old_status = server_info.status
            server_info.status = status
            server_info.error_message = error_message

            logger.info(
                "Server %s status: %s -> %s",
                server_id,
                old_status.value,
                status.value,
            )

            # Notify discovery callbacks on status change
            if old_status != status:
                await self._notify_discovery_callbacks(
                    "status_changed",
                    server_info,
                )

            return True

    async def update_heartbeat(self, server_id: str) -> bool:
        """
        Update server heartbeat timestamp

        Args:
            server_id: Server identifier

        Returns:
            bool: True if heartbeat was updated
        """
        async with self._lock:
            if server_id not in self._servers:
                return False

            self._servers[server_id].last_heartbeat = datetime.utcnow()
            return True

    async def get_server(self, server_id: str) -> Optional[MCPServerInfo]:
        """
        Get server information

        Args:
            server_id: Server identifier

        Returns:
            Optional[MCPServerInfo]: Server information or None
        """
        async with self._lock:
            return self._servers.get(server_id)

    async def list_servers(
        self,
        status: Optional[ServerStatus] = None,
        capability: Optional[str] = None,
    ) -> List[MCPServerInfo]:
        """
        List registered servers

        Args:
            status: Filter by status
            capability: Filter by capability

        Returns:
            List[MCPServerInfo]: List of servers
        """
        async with self._lock:
            servers = list(self._servers.values())

            if status:
                servers = [s for s in servers if s.status == status]

            if capability:
                servers = [s for s in servers if capability in s.capabilities]

            return servers

    async def discover_servers(
        self, capability: Optional[str] = None
    ) -> List[MCPServerInfo]:
        """
        Discover available servers

        Args:
            capability: Filter by capability

        Returns:
            List[MCPServerInfo]: List of available servers
        """
        # Get running servers
        servers = await self.list_servers(
            status=ServerStatus.RUNNING, capability=capability
        )

        if capability:
            logger.info(
                "Discovered %s servers with capability '%s'",
                len(servers),
                capability,
            )
        else:
            logger.info("Discovered %s servers", len(servers))

        return servers

    def add_discovery_callback(self, callback: Callable):
        """
        Add a callback for server discovery events

        Args:
            callback: Async callback function(event_type, server_info)
        """
        self._discovery_callbacks.append(callback)
        logger.debug("Added discovery callback: %s", callback.__name__)

    def remove_discovery_callback(self, callback: Callable):
        """
        Remove a discovery callback

        Args:
            callback: Callback function to remove
        """
        if callback in self._discovery_callbacks:
            self._discovery_callbacks.remove(callback)
            logger.debug(
                "Removed discovery callback: %s", callback.__name__
            )

    async def _notify_discovery_callbacks(
        self, event_type: str, server_info: MCPServerInfo
    ):
        """
        Notify all discovery callbacks

        Args:
            event_type: Type of event (
                registered, unregistered, status_changed
            )
            server_info: Server information
        """
        for callback in self._discovery_callbacks:
            try:
                await callback(event_type, server_info)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.error(
                    "Error in discovery callback %s: %s",
                    callback.__name__,
                    exc,
                )

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get registry statistics

        Returns:
            Dict[str, Any]: Statistics
        """
        async with self._lock:
            total = len(self._servers)
            by_status: Dict[str, int] = {}

            for server in self._servers.values():
                status = server.status.value
                by_status[status] = by_status.get(status, 0) + 1

            return {
                "total_servers": total,
                "by_status": by_status,
                "callbacks_registered": len(self._discovery_callbacks),
            }

    async def clear(self):
        """Clear all registered servers"""
        async with self._lock:
            self._servers.clear()
            logger.info("Cleared all registered servers")


# Made with Bob
