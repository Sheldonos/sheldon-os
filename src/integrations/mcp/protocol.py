"""
MCP Protocol Implementation
Handles MCP protocol communication
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


class MCPProtocol:
    """
    MCP Protocol implementation
    Handles communication with MCP servers
    """

    def __init__(self, endpoint: str, timeout: int = 30):
        self.endpoint = endpoint
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._last_request_time: Optional[datetime] = None
        logger.debug(
            "MCP Protocol initialized for endpoint: %s", endpoint
        )

    async def connect(self) -> bool:
        """
        Connect to MCP server

        Returns:
            bool: True if connected successfully
        """
        try:
            if self._session is None:
                self._session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                )

            # Test connection with ping
            response = await self._send_request("ping", {})
            if response and response.get("status") == "ok":
                self._connected = True
                logger.info("Connected to MCP server: %s", self.endpoint)
                return True

            logger.error(
                "Failed to connect to MCP server: %s", self.endpoint
            )
            return False

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error(
                "Error connecting to MCP server %s: %s",
                self.endpoint,
                exc,
            )
            return False

    async def disconnect(self):
        """Disconnect from MCP server"""
        try:
            if self._session:
                await self._session.close()
                self._session = None

            self._connected = False
            logger.info(
                "Disconnected from MCP server: %s", self.endpoint
            )

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error(
                "Error disconnecting from MCP server %s: %s",
                self.endpoint,
                exc,
            )

    async def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Execute a tool on the MCP server

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters

        Returns:
            Optional[Any]: Tool execution result
        """
        if not self._connected:
            logger.error("Not connected to MCP server")
            return None

        try:
            payload = {"tool": tool_name, "parameters": parameters}

            response = await self._send_request("execute_tool", payload)

            if response and response.get("status") == "success":
                return response.get("result")

            error = (
                response.get("error", "Unknown error")
                if response
                else "No response"
            )
            logger.error("Tool execution failed: %s", error)
            return None

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error executing tool %s: %s", tool_name, exc)
            return None

    async def list_tools(self) -> Optional[list]:
        """
        List available tools on the MCP server

        Returns:
            Optional[list]: List of available tools
        """
        if not self._connected:
            logger.error("Not connected to MCP server")
            return None

        try:
            response = await self._send_request("list_tools", {})

            if response and response.get("status") == "success":
                tools = response.get("tools", [])
                return tools if isinstance(tools, list) else None

            return None

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error(
                "Error listing tools from %s: %s",
                self.endpoint,
                exc,
            )
            return None

    async def get_tool_schema(
        self,
        tool_name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get schema for a specific tool

        Args:
            tool_name: Name of the tool

        Returns:
            Optional[Dict[str, Any]]: Tool schema
        """
        if not self._connected:
            logger.error("Not connected to MCP server")
            return None

        try:
            payload = {"tool": tool_name}
            response = await self._send_request("get_tool_schema", payload)

            if response and response.get("status") == "success":
                return response.get("schema")

            return None

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error(
                "Error getting tool schema for %s: %s", tool_name, exc
            )
            return None

    async def ping(self) -> bool:
        """
        Ping the MCP server

        Returns:
            bool: True if server responds
        """
        try:
            response = await self._send_request("ping", {})
            return response is not None and response.get("status") == "ok"

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error pinging MCP server: %s", exc)
            return False

    async def get_server_info(self) -> Optional[Dict[str, Any]]:
        """
        Get server information

        Returns:
            Optional[Dict[str, Any]]: Server information
        """
        try:
            response = await self._send_request("get_info", {})

            if response and response.get("status") == "success":
                return response.get("info")

            return None

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error getting server info: %s", exc)
            return None

    async def _send_request(
        self, method: str, payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Send a request to the MCP server

        Args:
            method: Request method
            payload: Request payload

        Returns:
            Optional[Dict[str, Any]]: Response data
        """
        if not self._session:
            logger.error("No active session")
            return None

        try:
            self._last_request_time = datetime.utcnow()

            request_data = {
                "jsonrpc": "2.0",
                "method": method,
                "params": payload,
                "id": self._generate_request_id(),
            }

            async with self._session.post(
                self.endpoint,
                json=request_data,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get("result")
                    return result if isinstance(result, dict) else None

                logger.error(
                    "Request failed with status %s", response.status
                )
                return None

        except asyncio.TimeoutError:
            logger.error("Request timeout for method %s", method)
            return None
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error sending request %s: %s", method, exc)
            return None

    def _generate_request_id(self) -> str:
        """Generate a unique request ID"""
        return f"{datetime.utcnow().timestamp()}"

    @property
    def is_connected(self) -> bool:
        """Check if connected to server"""
        return self._connected

    @property
    def last_request_time(self) -> Optional[datetime]:
        """Get last request time"""
        return self._last_request_time


# Made with Bob
