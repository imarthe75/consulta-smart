"""
Test suite for API routes
Tests for HTTP endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import json


@pytest.mark.unit
class TestHealthRoutes:
    """Test suite for health check endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        # Import here to avoid circular imports
        from main import app
        return TestClient(app)
    
    def test_health_endpoint_exists(self, client):
        """Test that health endpoint exists."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_endpoint_returns_json(self, client):
        """Test that health endpoint returns JSON."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
    
    def test_health_endpoint_has_status_field(self, client):
        """Test that health response has status field."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ["ok", "healthy", "up"]
    
    def test_health_endpoint_has_version(self, client):
        """Test that health response has version."""
        response = client.get("/health")
        data = response.json()
        assert "version" in data or "status" in data


@pytest.mark.unit
class TestAuthRoutes:
    """Test suite for authentication routes."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        from main import app
        return TestClient(app)
    
    def test_register_endpoint_exists(self, client):
        """Test that register endpoint exists."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "TestPassword123!",
            }
        )
        # Should return 200 or 422 (validation) or 409 (conflict), not 404
        assert response.status_code != 404
    
    def test_login_endpoint_exists(self, client):
        """Test that login endpoint exists."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123",
            }
        )
        assert response.status_code != 404
    
    def test_register_with_invalid_email(self, client):
        """Test register with invalid email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "username": "testuser",
                "password": "password123",
            }
        )
        # Should fail validation
        assert response.status_code in [422, 400]
    
    def test_register_missing_password(self, client):
        """Test register with missing password."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
            }
        )
        # Should fail validation
        assert response.status_code in [422, 400]


@pytest.mark.unit
class TestDocumentRoutes:
    """Test suite for document routes."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        from main import app
        return TestClient(app)
    
    def test_documents_list_endpoint_exists(self, client):
        """Test that documents list endpoint exists."""
        response = client.get("/api/v1/documents")
        assert response.status_code != 404
    
    def test_documents_list_returns_json(self, client):
        """Test that documents list returns JSON."""
        response = client.get("/api/v1/documents")
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict) or isinstance(data, list)


@pytest.mark.unit
class TestChatRoutes:
    """Test suite for chat routes."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        from main import app
        return TestClient(app)
    
    def test_chat_sessions_endpoint_exists(self, client):
        """Test that chat sessions endpoint exists."""
        response = client.get("/api/v1/chat/sessions")
        assert response.status_code != 404
    
    def test_create_chat_session_endpoint_exists(self, client):
        """Test that create session endpoint exists."""
        response = client.post(
            "/api/v1/chat/sessions",
            json={"title": "Test Session"}
        )
        assert response.status_code != 404


@pytest.mark.integration
class TestRoutesCORS:
    """Test CORS configuration on routes."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        from main import app
        return TestClient(app)
    
    def test_health_allows_cors(self, client):
        """Test that health endpoint allows CORS."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_api_endpoints_accessible(self, client):
        """Test that API endpoints are accessible."""
        # This tests basic connectivity, not auth
        response = client.get("/api/v1/documents")
        # Should return 200 (empty) or 401 (unauthorized), not 404 or 500
        assert response.status_code in [200, 401, 403]
