# Sheldon OS Integrations

## Overview

The Sheldon OS integration layer provides comprehensive connectivity to external services, MCP servers, and business tools. This document covers all integration capabilities including MCP server management, external tool connectors, and the API gateway.

## Table of Contents

1. [MCP Server Management](#mcp-server-management)
2. [External Tool Connectors](#external-tool-connectors)
3. [API Gateway](#api-gateway)
4. [Authentication & Authorization](#authentication--authorization)
5. [Rate Limiting](#rate-limiting)
6. [Usage Examples](#usage-examples)

## MCP Server Management

### Overview

The MCP (Model Context Protocol) server management system provides lifecycle management, health monitoring, and configuration for MCP servers.

### Components

#### Server Registry

Manages registration and discovery of MCP servers.

```python
from sheldon_os.integrations.mcp import MCPServerRegistry

registry = MCPServerRegistry()

# Register a server
await registry.register_server(
    server_id="my-server",
    name="My MCP Server",
    version="1.0.0",
    endpoint="http://localhost:8080",
    capabilities=["tool_execution", "data_processing"]
)

# Discover servers
servers = await registry.discover_servers(capability="tool_execution")
```

#### Server Manager

Handles server lifecycle operations.

```python
from sheldon_os.integrations.mcp import MCPServerManager

manager = MCPServerManager()

# Start a server
await manager.start_server(
    server_id="my-server",
    name="My MCP Server",
    version="1.0.0",
    endpoint="http://localhost:8080",
    capabilities=["tool_execution"]
)

# Execute a tool
result = await manager.execute_tool(
    server_id="my-server",
    tool_name="process_data",
    parameters={"data": "example"}
)

# Stop a server
await manager.stop_server("my-server")
```

#### Health Monitor

Monitors server health and triggers recovery.

```python
from sheldon_os.integrations.mcp import MCPHealthMonitor

monitor = MCPHealthMonitor(registry, check_interval=30, failure_threshold=3)

# Start monitoring
await monitor.start_monitoring("my-server")

# Add failure callback
async def on_failure(server_id):
    print(f"Server {server_id} failed!")

monitor.add_failure_callback(on_failure)

# Get health status
status = await monitor.get_health_status("my-server")
```

#### Configuration Manager

Manages server configurations.

```python
from sheldon_os.integrations.mcp import MCPConfigManager, MCPServerConfig

config_manager = MCPConfigManager()

# Add server configuration
config = MCPServerConfig(
    server_id="my-server",
    name="My MCP Server",
    version="1.0.0",
    endpoint="http://localhost:8080",
    capabilities=["tool_execution"],
    enabled=True,
    auto_start=True
)

config_manager.add_server_config(config)

# Get auto-start servers
auto_start = config_manager.get_auto_start_servers()
```

### Features

- **Automatic Discovery**: Find available MCP servers by capability
- **Health Monitoring**: Continuous health checks with configurable intervals
- **Auto-Restart**: Automatic recovery with exponential backoff
- **Configuration Management**: Persistent server configurations
- **Event Callbacks**: Subscribe to server lifecycle events

## External Tool Connectors

### Overview

External tool connectors provide standardized interfaces to business tools like Slack, email, and CRM systems.

### Base Connector

All connectors inherit from `BaseConnector`:

```python
from sheldon_os.integrations.connectors import BaseConnector, ConnectorConfig

class MyConnector(BaseConnector):
    async def connect(self) -> bool:
        # Implementation
        pass
    
    async def disconnect(self):
        # Implementation
        pass
    
    async def health_check(self) -> bool:
        # Implementation
        pass
    
    async def execute_action(self, action: str, parameters: dict) -> any:
        # Implementation
        pass
```

### Available Connectors

#### Slack Connector

```python
from sheldon_os.integrations.connectors import SlackConnector, ConnectorConfig

config = ConnectorConfig(
    connector_id="slack-1",
    connector_type="slack",
    api_key="xoxb-your-token"
)

slack = SlackConnector(config)
await slack.connect()

# Send message
result = await slack.execute_action(
    "send_message",
    {"channel": "#general", "text": "Hello!"}
)

# Create channel
result = await slack.execute_action(
    "create_channel",
    {"name": "new-channel", "is_private": False}
)
```

#### Email Connector

```python
from sheldon_os.integrations.connectors import EmailConnector, ConnectorConfig

config = ConnectorConfig(
    connector_id="email-1",
    connector_type="email",
    api_key="your-api-key"
)

email = EmailConnector(config)
await email.connect()

# Send email
result = await email.execute_action(
    "send_email",
    {
        "to": "user@example.com",
        "subject": "Hello",
        "body": "Email content"
    }
)
```

#### CRM Connector

```python
from sheldon_os.integrations.connectors import CRMConnector, ConnectorConfig

config = ConnectorConfig(
    connector_id="crm-1",
    connector_type="crm",
    api_key="your-api-key"
)

crm = CRMConnector(config)
await crm.connect()

# Create contact
result = await crm.execute_action(
    "create_contact",
    {
        "name": "John Doe",
        "email": "john@example.com",
        "company": "Acme Inc"
    }
)
```

### Connector Manager

Centralized management of all connectors:

```python
from sheldon_os.integrations.connectors import ConnectorManager

manager = ConnectorManager()

# Register connector types
manager.register_connector_type("slack", SlackConnector)
manager.register_connector_type("email", EmailConnector)
manager.register_connector_type("crm", CRMConnector)

# Create connector
connector = await manager.create_connector(config)

# Get connector
connector = await manager.get_connector("slack-1")

# Remove connector
await manager.remove_connector("slack-1")
```

### Features

- **Unified Interface**: Consistent API across all connectors
- **Rate Limiting**: Built-in rate limiting per connector
- **Health Checks**: Automatic connection health monitoring
- **Error Handling**: Robust error handling and retry logic
- **Extensible**: Easy to add new connectors

## API Gateway

### Overview

The API Gateway provides REST and GraphQL endpoints for external access to Sheldon OS.

### Setup

```python
from sheldon_os.api import APIGateway

gateway = APIGateway()

# Run the gateway
gateway.run(host="0.0.0.0", port=8000)
```

### Endpoints

#### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "healthy"
}
```

#### List Agents

```bash
GET /api/v1/agents
```

#### Create Agent

```bash
POST /api/v1/agents
Content-Type: application/json

{
  "name": "My Agent",
  "type": "sales",
  "config": {}
}
```

### Authentication

```python
from sheldon_os.api import AuthManager

auth = AuthManager(secret_key="your-secret-key")

# Create token
token = auth.create_token(user_id="user123")

# Verify token
payload = auth.verify_token(token)
```

### Rate Limiting

```python
from sheldon_os.api import RateLimiter

limiter = RateLimiter(requests_per_minute=60)

# Check rate limit
if limiter.check_rate_limit(client_id="client123"):
    # Process request
    pass
else:
    # Return 429 Too Many Requests
    pass
```

### Features

- **RESTful API**: Standard REST endpoints
- **JWT Authentication**: Secure token-based auth
- **Rate Limiting**: Configurable per-client limits
- **CORS Support**: Cross-origin resource sharing
- **API Versioning**: Support for multiple API versions
- **OpenAPI Documentation**: Auto-generated API docs

## Authentication & Authorization

### JWT Tokens

```python
from sheldon_os.api import AuthManager
from datetime import timedelta

auth = AuthManager(secret_key="your-secret-key")

# Create token with custom expiration
token = auth.create_token(
    user_id="user123",
    expires_delta=timedelta(hours=24)
)

# Verify token
payload = auth.verify_token(token)
if payload:
    user_id = payload["user_id"]
    # Process authenticated request
```

### API Keys

API keys can be configured in the environment:

```bash
SHELDON_OS_API_KEY=your-api-key
```

### OAuth Support

OAuth 2.0 support for third-party integrations (coming soon).

## Rate Limiting

### Configuration

```python
from sheldon_os.api import RateLimiter

# 60 requests per minute
limiter = RateLimiter(requests_per_minute=60)

# 1000 requests per minute
limiter = RateLimiter(requests_per_minute=1000)
```

### Usage

```python
client_id = request.headers.get("X-Client-ID")

if not limiter.check_rate_limit(client_id):
    return {"error": "Rate limit exceeded"}, 429
```

## Usage Examples

### Complete Integration Example

```python
import asyncio
from sheldon_os.integrations.mcp import MCPServerManager
from sheldon_os.integrations.connectors import ConnectorManager, SlackConnector
from sheldon_os.api import APIGateway

async def main():
    # Setup MCP server
    mcp_manager = MCPServerManager()
    await mcp_manager.start_server(
        server_id="tools-server",
        name="Tools Server",
        version="1.0.0",
        endpoint="http://localhost:8080",
        capabilities=["tool_execution"]
    )
    
    # Setup connectors
    connector_manager = ConnectorManager()
    connector_manager.register_connector_type("slack", SlackConnector)
    
    # Create Slack connector
    slack_config = ConnectorConfig(
        connector_id="slack-1",
        connector_type="slack",
        api_key="xoxb-your-token"
    )
    slack = await connector_manager.create_connector(slack_config)
    
    # Send notification
    await slack.execute_action(
        "send_message",
        {"channel": "#notifications", "text": "System started!"}
    )
    
    # Start API gateway
    gateway = APIGateway()
    gateway.run()

if __name__ == "__main__":
    asyncio.run(main())
```

## Best Practices

1. **Error Handling**: Always wrap connector calls in try-except blocks
2. **Rate Limiting**: Respect rate limits to avoid service disruptions
3. **Health Monitoring**: Enable health monitoring for critical services
4. **Configuration Management**: Use configuration files for server settings
5. **Security**: Never commit API keys or secrets to version control
6. **Logging**: Enable detailed logging for troubleshooting
7. **Testing**: Test integrations in staging before production

## Troubleshooting

### Common Issues

**MCP Server Connection Failed**
- Check server endpoint is accessible
- Verify network connectivity
- Check server logs for errors

**Connector Authentication Failed**
- Verify API key is correct
- Check token expiration
- Ensure proper permissions

**Rate Limit Exceeded**
- Reduce request frequency
- Implement exponential backoff
- Contact support for limit increase

## Support

For issues or questions:
- GitHub Issues: https://github.com/sheldon-os/sheldon-os/issues
- Documentation: https://docs.sheldon-os.com
- Email: support@sheldon-os.com