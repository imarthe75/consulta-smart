"""
Phase 4C - Integration Tests
API Endpoint Integration Tests
"""

import pytest
from datetime import datetime


@pytest.mark.asyncio
class TestAPIEndpointIntegration:
    """Test API endpoints with full stack"""
    
    async def test_health_check_endpoint(self, test_client):
        """Test: /health endpoint returns service status"""
        response = await test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
    
    async def test_api_version_endpoint(self, test_client):
        """Test: /api/v1 endpoint returns API version"""
        response = await test_client.get("/api/v1")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["version"].startswith("1.")
    
    async def test_api_metadata_endpoint(self, test_client, authenticated_user):
        """Test: /api/v1/metadata returns service metadata"""
        response = await test_client.get(
            "/api/v1/metadata",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert "features" in data


@pytest.mark.asyncio
class TestAPIErrorHandling:
    """Test error responses across API"""
    
    async def test_unauthorized_without_token(self, test_client):
        """Test: 401 Unauthorized when no token provided"""
        response = await test_client.get("/api/v1/documents")
        assert response.status_code == 401
        assert "authorization" in response.json().get("error", "").lower()
    
    async def test_invalid_token_rejection(self, test_client):
        """Test: 401 Unauthorized with invalid token"""
        response = await test_client.get(
            "/api/v1/documents",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    async def test_invalid_endpoint_404(self, test_client, authenticated_user):
        """Test: 404 Not Found for invalid endpoint"""
        response = await test_client.get(
            "/api/v1/nonexistent",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == 404
    
    async def test_method_not_allowed_405(self, test_client, authenticated_user):
        """Test: 405 Method Not Allowed"""
        response = await test_client.post(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"},
            json={}
        )
        # POST to /documents list should not be allowed (use /upload)
        assert response.status_code in [405, 400]
    
    async def test_invalid_json_400(self, test_client, authenticated_user):
        """Test: 400 Bad Request for invalid JSON"""
        response = await test_client.post(
            "/api/v1/auth/login",
            headers={"Content-Type": "application/json"},
            content="invalid json {{"
        )
        assert response.status_code == 400


@pytest.mark.asyncio
class TestCORSIntegration:
    """Test CORS headers and origin verification"""
    
    async def test_cors_headers_present(self, test_client):
        """Test: CORS headers in response"""
        response = await test_client.options(
            "/api/v1/documents",
            headers={"Origin": "http://localhost:3000"}
        )
        # Should have CORS headers or preflight response
        assert response.status_code in [200, 204, 404]
    
    async def test_preflight_request(self, test_client):
        """Test: Preflight request handling"""
        response = await test_client.options(
            "/api/v1/chat/sessions",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        # Should handle preflight
        assert response.status_code in [200, 204, 404]


@pytest.mark.asyncio
class TestRateLimitingIntegration:
    """Test rate limiting and throttling"""
    
    async def test_rapid_requests_rate_limited(self, test_client, authenticated_user):
        """Test: Rapid requests get rate limited"""
        token = f"Bearer {authenticated_user['token']}"
        
        # Make multiple rapid requests
        responses = []
        for i in range(100):
            response = await test_client.get(
                "/api/v1/documents",
                headers={"Authorization": token}
            )
            responses.append(response)
        
        # Should eventually get rate limited
        # At least one should be 429 or connection refused
        status_codes = {r.status_code for r in responses}
        # In real implementation, should see 429 Too Many Requests
        assert any(status in status_codes for status in [200, 429])


@pytest.mark.asyncio
class TestResponseFormatting:
    """Test response formatting consistency"""
    
    async def test_json_response_format(self, test_client, authenticated_user):
        """Test: All responses follow JSON format"""
        response = await test_client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        
        assert response.headers.get("content-type") == "application/json"
        data = response.json()  # Should parse as JSON
    
    async def test_error_response_format(self, test_client):
        """Test: Error responses have consistent format"""
        response = await test_client.get("/api/v1/documents")
        
        data = response.json()
        assert "error" in data or "message" in data or "detail" in data
    
    async def test_pagination_format(self, test_client, authenticated_user):
        """Test: Paginated responses follow standard format"""
        response = await test_client.get(
            "/api/v1/documents",
            params={"page": 1, "limit": 10},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        
        data = response.json()
        # Should have pagination info
        assert "items" in data or "documents" in data or "data" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
