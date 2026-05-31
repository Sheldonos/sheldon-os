"""
MCP Configuration Manager
Manages MCP server configurations
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """MCP Server configuration"""

    server_id: str
    name: str
    version: str
    endpoint: str
    capabilities: list
    enabled: bool = True
    auto_start: bool = True
    health_check_interval: int = 30
    failure_threshold: int = 3
    timeout: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPServerConfig":
        """Create from dictionary"""
        return cls(**data)


class MCPConfigManager:
    """
    Configuration manager for MCP servers
    Handles loading, saving, and managing server configurations
    """

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".sheldon-os" / "mcp"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "servers.json"
        self._configs: Dict[str, MCPServerConfig] = {}
        logger.info(
            "MCP Config Manager initialized (config_dir=%s)",
            self.config_dir,
        )

        # Load existing configurations
        self._load_configs()

    def _load_configs(self):
        """Load configurations from file"""
        if not self.config_file.exists():
            logger.info("No existing configuration file found")
            return

        try:
            with open(self.config_file, "r", encoding="utf-8") as file_handle:
                data = json.load(file_handle)

            for server_id, config_data in data.items():
                self._configs[server_id] = MCPServerConfig.from_dict(
                    config_data
                )

            logger.info(
                "Loaded %s server configurations", len(self._configs)
            )

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error loading configurations: %s", exc)

    def _save_configs(self):
        """Save configurations to file"""
        try:
            data = {
                server_id: config.to_dict()
                for server_id, config in self._configs.items()
            }

            with open(self.config_file, "w", encoding="utf-8") as file_handle:
                json.dump(data, file_handle, indent=2)

            logger.debug(
                "Saved %s server configurations", len(self._configs)
            )

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error saving configurations: %s", exc)

    def add_server_config(self, config: MCPServerConfig) -> bool:
        """
        Add a server configuration

        Args:
            config: Server configuration

        Returns:
            bool: True if added successfully
        """
        try:
            if config.server_id in self._configs:
                logger.warning(
                    "Configuration for server %s already exists",
                    config.server_id,
                )
                return False

            self._configs[config.server_id] = config
            self._save_configs()

            logger.info(
                "Added configuration for server: %s (%s)",
                config.name,
                config.server_id,
            )
            return True

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error adding server configuration: %s", exc)
            return False

    def update_server_config(
        self,
        server_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """
        Update a server configuration

        Args:
            server_id: Server identifier
            updates: Configuration updates

        Returns:
            bool: True if updated successfully
        """
        try:
            if server_id not in self._configs:
                logger.error(
                    "Configuration for server %s not found", server_id
                )
                return False

            config = self._configs[server_id]

            # Update fields
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                else:
                    logger.warning(
                        "Unknown configuration field: %s", key
                    )

            self._save_configs()

            logger.info(
                "Updated configuration for server %s", server_id
            )
            return True

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error updating server configuration: %s", exc)
            return False

    def remove_server_config(self, server_id: str) -> bool:
        """
        Remove a server configuration

        Args:
            server_id: Server identifier

        Returns:
            bool: True if removed successfully
        """
        try:
            if server_id not in self._configs:
                logger.warning(
                    "Configuration for server %s not found", server_id
                )
                return False

            del self._configs[server_id]
            self._save_configs()

            logger.info(
                "Removed configuration for server %s", server_id
            )
            return True

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error removing server configuration: %s", exc)
            return False

    def get_server_config(self, server_id: str) -> Optional[MCPServerConfig]:
        """
        Get a server configuration

        Args:
            server_id: Server identifier

        Returns:
            Optional[MCPServerConfig]: Server configuration or None
        """
        return self._configs.get(server_id)

    def list_server_configs(
        self, enabled_only: bool = False
    ) -> Dict[str, MCPServerConfig]:
        """
        List all server configurations

        Args:
            enabled_only: Only return enabled servers

        Returns:
            Dict[str, MCPServerConfig]: Server configurations
        """
        if enabled_only:
            return {
                server_id: config
                for server_id, config in self._configs.items()
                if config.enabled
            }
        return self._configs.copy()

    def enable_server(self, server_id: str) -> bool:
        """
        Enable a server

        Args:
            server_id: Server identifier

        Returns:
            bool: True if enabled successfully
        """
        return self.update_server_config(server_id, {"enabled": True})

    def disable_server(self, server_id: str) -> bool:
        """
        Disable a server

        Args:
            server_id: Server identifier

        Returns:
            bool: True if disabled successfully
        """
        return self.update_server_config(server_id, {"enabled": False})

    def get_auto_start_servers(self) -> Dict[str, MCPServerConfig]:
        """
        Get servers configured for auto-start

        Returns:
            Dict[str, MCPServerConfig]: Auto-start server configurations
        """
        return {
            server_id: config
            for server_id, config in self._configs.items()
            if config.enabled and config.auto_start
        }

    def import_config(self, config_file: Path) -> bool:
        """
        Import configurations from a file

        Args:
            config_file: Path to configuration file

        Returns:
            bool: True if imported successfully
        """
        try:
            with open(config_file, "r", encoding="utf-8") as file_handle:
                data = json.load(file_handle)

            imported_count = 0
            for _, config_data in data.items():
                config = MCPServerConfig.from_dict(config_data)
                if self.add_server_config(config):
                    imported_count += 1

            logger.info(
                "Imported %s server configurations", imported_count
            )
            return True

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error importing configurations: %s", exc)
            return False

    def export_config(self, export_file: Path) -> bool:
        """
        Export configurations to a file

        Args:
            export_file: Path to export file

        Returns:
            bool: True if exported successfully
        """
        try:
            data = {
                server_id: config.to_dict()
                for server_id, config in self._configs.items()
            }

            with open(export_file, "w", encoding="utf-8") as file_handle:
                json.dump(data, file_handle, indent=2)

            logger.info(
                "Exported %s server configurations to %s",
                len(self._configs),
                export_file,
            )
            return True

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error exporting configurations: %s", exc)
            return False

    def clear_configs(self):
        """Clear all configurations"""
        self._configs.clear()
        self._save_configs()
        logger.info("Cleared all server configurations")


# Made with Bob
