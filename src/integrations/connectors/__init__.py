"""
External Tool Connectors
Provides connectors for external business tools
"""

from .base_connector import BaseConnector, ConnectorConfig
from .connector_manager import ConnectorManager
from .crm_connector import CRMConnector
from .email_connector import EmailConnector
from .slack_connector import SlackConnector

__all__ = [
    "BaseConnector",
    "ConnectorConfig",
    "ConnectorManager",
    "SlackConnector",
    "EmailConnector",
    "CRMConnector",
]
