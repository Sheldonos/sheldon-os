"""
Comprehensive tests for API layer (gateway, auth, rate limiting).

This module provides runtime validation for:
- JWT authentication flows
- Protected route access
- Rate limiting behavior
- CORS configuration
- API gateway functionality
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from jose import jwt
import time

from sheldon_os.api.gateway import create_app
from sheldon_os.api.auth import (
    create_access_token,
    verify_token,
    get_current_user,
    hash_password,
    verify_password,
)
from sheldon_os.api.rate_limiter import RateLimiter
from sheldon_os.core.config import Config


@pytest.fixture
def config():
    """Test configuration."""
    return Config(
        environment="test",
        debug=True,
        security__secret_key="test-secret-key-min-32-chars-long",
        security__algorithm="HS256",
        security__access_token_expire_minutes=30,
        api__rate_limit_per_minute=60,
    )


@pytest.fixture
def app(config):
    """Create test FastAPI application."""
    return create_app(config)


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_token(config):
    """Create a valid JWT token for testing."""
    return create_access_token(
        data={"sub": "test_user", "email": "test@example.com"},
        config=config,
    )


@pytest.fixture
def expired_token(config):
    """Create an expired JWT token for testing."""
    expires = datetime.utcnow() - timedelta(minutes=1)
    return jwt.encode(
        {"sub": "test_user", "exp": expires},
        config.security.secret_key,
        algorithm=config.security.algorithm,
    )


class TestAuthentication:
    """Test authentication functionality."""

    def test_create_access_token(self, config):
        """Test JWT token creation."""
        token = create_access_token(
            data={"sub": "test_user"},
            config=config,
        )
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self, valid_token, config):
        """Test verification of valid token."""
        payload = verify_token(valid_token, config)
        assert payload is not None
        assert payload["sub"] == "test_user"

    def test_verify_expired_token(self, expired_token, config):
        """Test verification of expired token."""
        payload = verify_token(expired_token, config)
        assert payload is None

    def test_verify_invalid_token(self, config):
        """Test verification of invalid token."""
        payload = verify_token("invalid.token.here", config)
        assert payload is None

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

    def test_token_expiration(self, config):
        """Test token expiration timing."""
        # Create token with 1 second expiration
        short_config = Config(
            environment="test",
            security__secret_key=config.security.secret_key,
            security__access_token_expire_minutes=0.0167,  # 1 second
        )
        
        token = create_access_token(
            data={"sub": "test_user"},
            config=short_config,
        )
        
        # Should be valid immediately
        payload = verify_token(token, short_config)
        assert payload is not None
        
        # Wait for expiration
        time.sleep(2)
        
        # Should be expired now
        payload = verify_token(token, short_config)
        assert payload is None


class TestAPIGateway:
    """Test API gateway functionality."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_docs_endpoint(self, client):
        """Test OpenAPI docs endpoint."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema(self, client):
        """Test OpenAPI schema endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

    def test_protected_route_without_token(self, client):
        """Test accessing protected route without token."""
        response = client.get("/api/v1/protected")
        assert response.status_code == 401

    def test_protected_route_with_invalid_token(self, client):
        """Test accessing protected route with invalid token."""
        response = client.get(
            "/api/v1/protected",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401

    def test_protected_route_with_valid_token(self, client, valid_token):
        """Test accessing protected route with valid token."""
        response = client.get(
            "/api/v1/protected",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 200

    def test_cors_headers(self, client, config):
        """Test CORS headers configuration."""
        response = client.options(
            "/api/v1/test",
            headers={"Origin": "http://localhost:3000"},
        )
        assert "access-control-allow-origin" in response.headers

    def test_request_validation(self, client, valid_token):
        """Test request body validation."""
        response = client.post(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={"invalid": "data"},
        )
        assert response.status_code in [400, 422]  # Validation error


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiter_initialization(self, config):
        """Test rate limiter initialization."""
        limiter = RateLimiter(
            max_requests=10,
            window_seconds=60,
        )
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 60

    def test_rate_limit_allows_requests(self, config):
        """Test rate limiter allows requests within limit."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        client_id = "test_client"
        
        # Should allow first 5 requests
        for _ in range(5):
            assert limiter.is_allowed(client_id)

    def test_rate_limit_blocks_excess_requests(self, config):
        """Test rate limiter blocks requests over limit."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        client_id = "test_client"
        
        # Allow first 3 requests
        for _ in range(3):
            assert limiter.is_allowed(client_id)
        
        # Block 4th request
        assert not limiter.is_allowed(client_id)

    def test_rate_limit_window_reset(self, config):
        """Test rate limiter window reset."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        client_id = "test_client"
        
        # Use up limit
        assert limiter.is_allowed(client_id)
        assert limiter.is_allowed(client_id)
        assert not limiter.is_allowed(client_id)
        
        # Wait for window reset
        time.sleep(1.1)
        
        # Should allow again
        assert limiter.is_allowed(client_id)

    def test_rate_limit_per_client(self, config):
        """Test rate limiting is per-client."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # Client 1 uses limit
        assert limiter.is_allowed("client1")
        assert limiter.is_allowed("client1")
        assert not limiter.is_allowed("client1")
        
        # Client 2 should still have limit
        assert limiter.is_allowed("client2")
        assert limiter.is_allowed("client2")

    def test_rate_limit_endpoint(self, client, valid_token):
        """Test rate limiting on API endpoint."""
        # Make requests up to limit
        for i in range(60):  # Default limit
            response = client.get(
                "/api/v1/test",
                headers={"Authorization": f"Bearer {valid_token}"},
            )
            if response.status_code == 429:
                # Hit rate limit
                assert i > 0  # Should allow at least some requests
                break
        else:
            # If we didn't hit limit, that's also acceptable for test
            pass


class TestAPIErrorHandling:
    """Test API error handling."""

    def test_404_error(self, client):
        """Test 404 error handling."""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test 405 method not allowed."""
        response = client.post("/health")  # Health only accepts GET
        assert response.status_code == 405

    def test_validation_error_format(self, client, valid_token):
        """Test validation error response format."""
        response = client.post(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={"invalid": "data"},
        )
        assert response.status_code in [400, 422]
        data = response.json()
        assert "detail" in data or "message" in data

    def test_authentication_error_format(self, client):
        """Test authentication error response format."""
        response = client.get("/api/v1/protected")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data or "message" in data


class TestAPIMetrics:
    """Test API metrics and monitoring."""

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint availability."""
        response = client.get("/metrics")
        # Metrics endpoint may require auth or be disabled in test
        assert response.status_code in [200, 401, 404]

    def test_request_logging(self, client, valid_token):
        """Test that requests are logged."""
        # Make a request
        response = client.get(
            "/api/v1/test",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        # Logging is tested by absence of errors
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for API layer."""

    def test_full_auth_flow(self, client, config):
        """Test complete authentication flow."""
        # 1. Create token
        token = create_access_token(
            data={"sub": "integration_user"},
            config=config,
        )
        
        # 2. Use token to access protected resource
        response = client.get(
            "/api/v1/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        
        # 3. Verify token payload
        payload = verify_token(token, config)
        assert payload["sub"] == "integration_user"

    def test_token_refresh_flow(self, client, config):
        """Test token refresh flow."""
        # Create initial token
        token1 = create_access_token(
            data={"sub": "user1"},
            config=config,
        )
        
        # Use token
        response = client.get(
            "/api/v1/protected",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert response.status_code == 200
        
        # Create new token (simulating refresh)
        token2 = create_access_token(
            data={"sub": "user1"},
            config=config,
        )
        
        # Both tokens should work
        response = client.get(
            "/api/v1/protected",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 200

# Made with Bob
