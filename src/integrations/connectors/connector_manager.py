"""
Connector Manager
Manages all external tool connectors
"""

import logging
from typing import Dict, Optional, Type

from .base_connector import BaseConnector, ConnectorConfig

logger = logging.getLogger(__name__)


class ConnectorManager:
    """
    Manages external tool connectors
    """

    def __init__(self):
        self._connectors: Dict[str, BaseConnector] = {}
        self._connector_types: Dict[str, Type[BaseConnector]] = {}
        logger.info("Connector Manager initialized")

    def register_connector_type(
        self, connector_type: str, connector_class: Type[BaseConnector]
    ):
        """Register a connector type"""
        self._connector_types[connector_type] = connector_class
        logger.info("Registered connector type: %s", connector_type)

    async def create_connector(
        self, config: ConnectorConfig
    ) -> Optional[BaseConnector]:
        """Create and initialize a connector"""
        if config.connector_type not in self._connector_types:
            logger.error(
                "Unknown connector type: %s", config.connector_type
            )
            return None

        connector_class = self._connector_types[config.connector_type]
        connector = connector_class(config)

        success = await connector.connect()
        if success:
            self._connectors[config.connector_id] = connector
            logger.info("Created connector: %s", config.connector_id)
            return connector

        return None

    async def get_connector(
        self,
        connector_id: str,
    ) -> Optional[BaseConnector]:
        """Get a connector by ID"""
        return self._connectors.get(connector_id)

    async def remove_connector(self, connector_id: str) -> bool:
        """Remove a connector"""
        if connector_id in self._connectors:
            await self._connectors[connector_id].disconnect()
            del self._connectors[connector_id]
            logger.info("Removed connector: %s", connector_id)
            return True
        return False

    async def shutdown(self):
        """Shutdown all connectors"""
        for connector in self._connectors.values():
            await connector.disconnect()
        self._connectors.clear()
        logger.info("Connector Manager shutdown complete")
