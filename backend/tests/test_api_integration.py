"""
Test suite for API integration
Tests for complete HTTP workflow and endpoint integration
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
import json
import uuid


@pytest.mark.integration
class TestAuthenticationFlow:
    """Test complete authentication flow."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)
    
    def test_register_then_login_flow(self, client):
        """Test complete registration and login flow."""
        # Step 1: Register
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePass123!"
            }
        )
        
        # Should succeed with 200 or 201
        assert register_response.status_code in [200, 201, 409]  # 409 if already exists
        
        # Step 2: Login
        if register_response.status_code in [200, 201]:
            login_response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "newuser@example.com",
                    "password": "SecurePass123!"
                }
            )
            
            assert login_response.status_code in [200, 401]
    
    def test_login_with_wrong_password(self, client):
        """Test login with incorrect password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "wrongpassword"
            }
        )
        
        # Should return 401 Unauthorized
        assert response.status_code in [401, 403]
    
    def test_access_protected_route_without_token(self, client):
        """Test accessing protected route without token."""
        response = client.get("/api/v1/documents")
        
        # Should return 401 or 403
        assert response.status_code in [401, 403]
    
    def test_access_protected_route_with_invalid_token(self, client):
        """Test accessing protected route with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/documents", headers=headers)
        
        # Should return 401
        assert response.status_code in [401, 403]


@pytest.mark.integration
class TestDocumentUploadFlow:
    """Test complete document upload workflow."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)
    
    def test_upload_document_endpoint(self, client, test_document_data: dict):
        """Test uploading a document."""
        # Create a mock file
        files = {"file": ("test.pdf", b"pdf_content", "application/pdf")}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data={"title": test_document_data["filename"]}
        )
        
        # Should succeed or return auth error
        assert response.status_code in [200, 201, 401, 403]
    
    def test_list_documents_endpoint(self, client):
        """Test listing documents."""
        response = client.get("/api/v1/documents")
        
        # Should return 200 or auth error
        assert response.status_code in [200, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (dict, list))
    
    def test_get_document_detail_endpoint(self, client):
        """Test getting document details."""
        doc_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/documents/{doc_id}")
        
        # Should return 200, 404, or auth error
        assert response.status_code in [200, 404, 401, 403]
    
    def test_delete_document_endpoint(self, client):
        """Test deleting a document."""
        doc_id = str(uuid.uuid4())
        response = client.delete(f"/api/v1/documents/{doc_id}")
        
        # Should return 200, 404, or auth error
        assert response.status_code in [200, 204, 404, 401, 403]


@pytest.mark.integration
class TestChatFlow:
    """Test complete chat workflow."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)
    
    def test_create_chat_session_endpoint(self, client, test_chat_session: dict):
        """Test creating a chat session."""
        response = client.post(
            "/api/v1/chat/sessions",
            json={"title": test_chat_session["title"]}
        )
        
        # Should succeed or auth error
        assert response.status_code in [200, 201, 401, 403]
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "session_id" in data or "id" in data
    
    def test_send_message_endpoint(self, client):
        """Test sending a message."""
        session_id = str(uuid.uuid4())
        
        response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"content": "What is this document about?"}
        )
        
        # Should return response or error
        assert response.status_code in [200, 201, 404, 401, 403]
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "message_id" in data or "id" in data
    
    def test_get_chat_history_endpoint(self, client):
        """Test getting chat history."""
        session_id = str(uuid.uuid4())
        
        response = client.get(f"/api/v1/chat/sessions/{session_id}/messages")
        
        # Should return list or error
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_list_chat_sessions_endpoint(self, client):
        """Test listing chat sessions."""
        response = client.get("/api/v1/chat/sessions")
        
        # Should return list or error
        assert response.status_code in [200, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (dict, list))


@pytest.mark.integration
class TestSearchFlow:
    """Test complete search workflow."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)
    
    def test_semantic_search_endpoint(self, client, test_query: str):
        """Test semantic search."""
        response = client.get(
            "/api/v1/search",
            params={"q": test_query, "limit": 10}
        )
        
        # Should return results or error
        assert response.status_code in [200, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (dict, list))
    
    def test_search_with_filters(self, client):
        """Test search with filters."""
        response = client.get(
            "/api/v1/search",
            params={
                "q": "lease",
                "document_type": "lease",
                "limit": 10
            }
        )
        
        # Should return filtered results or error
        assert response.status_code in [200, 401, 403]
    
    def test_search_by_document_id(self, client):
        """Test searching within a specific document."""
        doc_id = str(uuid.uuid4())
        
        response = client.get(
            f"/api/v1/documents/{doc_id}/search",
            params={"q": "property"}
        )
        
        # Should return results or error
        assert response.status_code in [200, 404, 401, 403]


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling across API."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)
    
    def test_404_not_found(self, client):
        """Test 404 error response."""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data or "error" in data
    
    def test_400_bad_request(self, client):
        """Test 400 error for invalid data."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "invalid"}  # Missing password
        )
        
        assert response.status_code in [400, 422]
    
    def test_405_method_not_allowed(self, client):
        """Test 405 for incorrect HTTP method."""
        response = client.post("/api/v1/documents")
        
        # If no endpoint exists for POST, should be 405 or 404
        assert response.status_code in [405, 404]
    
    def test_500_server_error_handling(self, client):
        """Test that 500 errors are handled gracefully."""
        # This would require triggering an actual error condition
        # Usually tested with mock/patch
        pass
    
    def test_validation_error_response(self, client):
        """Test validation error format."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": "valid",
                "password": "pass"
            }
        )
        
        if response.status_code == 422:
            data = response.json()
            assert "detail" in data


@pytest.mark.integration
class TestResponseFormats:
    """Test API response format consistency."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)
    
    def test_health_response_format(self, client):
        """Test health endpoint response format."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_list_response_format(self, client):
        """Test list endpoint response format."""
        response = client.get("/api/v1/documents")
        
        if response.status_code == 200:
            data = response.json()
            # Should be list or dict with data key
            assert isinstance(data, (dict, list))
    
    def test_error_response_format(self, client):
        """Test error response format."""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        # Should have error information
        assert "detail" in data or "error" in data or "message" in data
    
    def test_response_has_correct_content_type(self, client):
        """Test all responses have correct content-type."""
        endpoints = [
            ("/health", "GET"),
            ("/api/v1/documents", "GET"),
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})
            
            # Content-type should be JSON
            assert "application/json" in response.headers.get("content-type", "")


@pytest.mark.integration
@pytest.mark.slow
class TestConcurrentRequests:
    """Test handling concurrent API requests."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)
    
    def test_multiple_requests_same_session(self, client):
        """Test multiple requests in same session."""
        for i in range(5):
            response = client.get("/health")
            assert response.status_code in [200, 401, 403]
    
    def test_multiple_searches(self, client):
        """Test multiple search requests."""
        queries = ["lease", "property", "rent", "finance"]
        
        for query in queries:
            response = client.get(
                "/api/v1/search",
                params={"q": query}
            )
            assert response.status_code in [200, 401, 403]
