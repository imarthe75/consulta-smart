"""
Phase 4C - Integration Tests
Complete end-to-end workflows across API layers
Testing: Authentication, Document Upload, Chat, Search
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient

from app.core.database import Base
from app.infrastructure.models import (
    User, Document, ChatSession, ChatMessage, 
    DocumentChunk, VectorEmbedding
)
from app.application.dtos.common_dtos import (
    UserLoginRequest, UserRegisterRequest, DocumentUploadRequest
)
from main import app


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create async test database engine"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create async test database session"""
    async_session = sessionmaker(
        test_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
async def test_client(test_session):
    """Create test API client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def authenticated_user(test_session) -> dict:
    """Create and authenticate a test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
        created_at=datetime.utcnow()
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "token": "mock_jwt_token"
    }


# ============================================================================
# INTEGRATION TESTS - AUTHENTICATION FLOW
# ============================================================================

@pytest.mark.asyncio
class TestAuthenticationFlow:
    """Test complete authentication workflow"""
    
    async def test_register_user_complete_flow(self, test_client, test_session):
        """Test: Register new user -> Verify in DB -> Login -> Get token"""
        # 1. Register user
        register_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "TestPass123!",
            "full_name": "New User"
        }
        
        response = await test_client.post(
            "/api/v1/auth/register",
            json=register_data
        )
        assert response.status_code == 201
        register_result = response.json()
        assert "token" in register_result
        assert register_result["user"]["email"] == register_data["email"]
        
        # 2. Verify user in database
        user = await test_session.query(User).filter(
            User.email == register_data["email"]
        ).first()
        assert user is not None
        assert user.username == register_data["username"]
        
        # 3. Login with registered credentials
        login_response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": register_data["email"],
                "password": register_data["password"]
            }
        )
        assert login_response.status_code == 200
        login_result = login_response.json()
        assert "token" in login_result
        assert login_result["user"]["id"] == user.id
    
    async def test_token_refresh_flow(self, test_client, authenticated_user):
        """Test: Use refresh token -> Get new access token"""
        # Initial login would provide refresh token
        refresh_response = await test_client.post(
            "/api/v1/auth/refresh",
            headers={
                "Authorization": f"Bearer {authenticated_user['token']}"
            }
        )
        
        assert refresh_response.status_code == 200
        new_token = refresh_response.json()
        assert "token" in new_token
    
    async def test_invalid_credentials_flow(self, test_client):
        """Test: Login with invalid credentials -> Error response"""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "error" in response.json()


# ============================================================================
# INTEGRATION TESTS - DOCUMENT UPLOAD & PROCESSING FLOW
# ============================================================================

@pytest.mark.asyncio
class TestDocumentUploadFlow:
    """Test complete document upload and processing workflow"""
    
    async def test_upload_pdf_parse_chunk_embed_flow(
        self, test_client, authenticated_user, test_session
    ):
        """Test: Upload PDF -> Parse -> Create chunks -> Generate embeddings"""
        # 1. Upload document
        file_data = {
            "file": ("test.pdf", b"PDF mock content", "application/pdf"),
            "title": "Test Document",
            "description": "Integration test document"
        }
        
        response = await test_client.post(
            "/api/v1/documents/upload",
            files=file_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        
        # 2. Verify document in database
        document = await test_session.query(Document).filter(
            Document.user_id == authenticated_user['id']
        ).first()
        assert document is not None
        assert document.title == file_data["title"]
        
        # 3. Document should be queued for processing
        assert document.processing_status == "queued"
        
        # 4. Simulate processing (would be async in real app)
        # Document parsing
        document.processing_status = "parsing"
        
        # Create chunks
        chunk1 = DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            content="First chunk of text",
            token_count=50
        )
        chunk2 = DocumentChunk(
            document_id=document.id,
            chunk_index=1,
            content="Second chunk of text",
            token_count=45
        )
        test_session.add_all([chunk1, chunk2])
        await test_session.commit()
        
        # Embeddings would be generated
        embedding1 = VectorEmbedding(
            chunk_id=chunk1.id,
            vector=[0.1] * 768,  # Mock embedding
            embedding_model="gemini-embedding-1"
        )
        embedding2 = VectorEmbedding(
            chunk_id=chunk2.id,
            vector=[0.2] * 768,
            embedding_model="gemini-embedding-1"
        )
        test_session.add_all([embedding1, embedding2])
        
        document.processing_status = "completed"
        await test_session.commit()
        
        # 5. Verify complete state
        await test_session.refresh(document)
        chunks = await test_session.query(DocumentChunk).filter(
            DocumentChunk.document_id == document.id
        ).all()
        assert len(chunks) == 2
    
    async def test_multiple_document_management(
        self, test_client, authenticated_user, test_session
    ):
        """Test: Upload multiple documents -> List -> Delete"""
        # 1. Upload first document
        doc1_response = await test_client.post(
            "/api/v1/documents/upload",
            files={"file": ("doc1.pdf", b"Content 1", "application/pdf")},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert doc1_response.status_code == 200
        
        # 2. Upload second document
        doc2_response = await test_client.post(
            "/api/v1/documents/upload",
            files={"file": ("doc2.pdf", b"Content 2", "application/pdf")},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert doc2_response.status_code == 200
        
        # 3. List documents
        list_response = await test_client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert list_response.status_code == 200
        documents = list_response.json()
        assert len(documents.get("documents", [])) >= 2
        
        # 4. Delete first document
        doc_id = doc1_response.json()["id"]
        delete_response = await test_client.delete(
            f"/api/v1/documents/{doc_id}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert delete_response.status_code == 204
        
        # 5. Verify deletion
        document = await test_session.query(Document).filter(
            Document.id == doc_id
        ).first()
        assert document.deleted_at is not None


# ============================================================================
# INTEGRATION TESTS - CHAT & CONVERSATION FLOW
# ============================================================================

@pytest.mark.asyncio
class TestChatConversationFlow:
    """Test complete chat conversation workflow"""
    
    async def test_create_session_send_message_get_response(
        self, test_client, authenticated_user, test_session
    ):
        """Test: Create chat session -> Send message -> Get LLM response"""
        # 1. Create chat session
        session_response = await test_client.post(
            "/api/v1/chat/sessions",
            json={"title": "Test Conversation"},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert session_response.status_code == 201
        session_id = session_response.json()["id"]
        
        # 2. Verify session in database
        session = await test_session.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()
        assert session is not None
        assert session.user_id == authenticated_user['id']
        
        # 3. Send message
        message_response = await test_client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"content": "What is property registration?"},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert message_response.status_code == 201
        user_message = message_response.json()
        
        # 4. Verify user message in database
        chat_message = await test_session.query(ChatMessage).filter(
            ChatMessage.id == user_message["id"]
        ).first()
        assert chat_message is not None
        assert chat_message.role == "user"
        
        # 5. Simulate LLM response (would be async in real app)
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content="Property registration is the legal process...",
            created_at=datetime.utcnow()
        )
        test_session.add(assistant_message)
        await test_session.commit()
        
        # 6. Get conversation history
        history_response = await test_client.get(
            f"/api/v1/chat/sessions/{session_id}/messages",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert history_response.status_code == 200
        messages = history_response.json()
        assert len(messages["messages"]) >= 2
    
    async def test_chat_with_document_context(
        self, test_client, authenticated_user, test_session
    ):
        """Test: Chat using document context from RAG pipeline"""
        # 1. Create document with chunks
        document = Document(
            user_id=authenticated_user['id'],
            title="RPP Test Document",
            file_path="test.pdf",
            processing_status="completed"
        )
        test_session.add(document)
        await test_session.commit()
        await test_session.refresh(document)
        
        # 2. Create chat session
        session = ChatSession(
            user_id=authenticated_user['id'],
            title="Query with RAG"
        )
        test_session.add(session)
        await test_session.commit()
        await test_session.refresh(session)
        
        # 3. Send query
        query_response = await test_client.post(
            f"/api/v1/chat/sessions/{session.id}/messages",
            json={
                "content": "How to dissolve a usufruct?",
                "document_id": str(document.id)
            },
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert query_response.status_code == 201
        
        # 4. Response should include document context
        response_msg = query_response.json()
        assert "document_id" in response_msg or "context" in response_msg


# ============================================================================
# INTEGRATION TESTS - SEARCH FLOW
# ============================================================================

@pytest.mark.asyncio
class TestSearchFlow:
    """Test complete semantic search workflow"""
    
    async def test_semantic_search_with_filters(
        self, test_client, authenticated_user, test_session
    ):
        """Test: Semantic search with state/type filters"""
        # 1. Create test documents with embeddings
        doc_qroo = Document(
            user_id=authenticated_user['id'],
            title="Quintana Roo Property Registration",
            metadata={"state": "quintana_roo", "type": "legislation"}
        )
        doc_puebla = Document(
            user_id=authenticated_user['id'],
            title="Puebla Property Registration",
            metadata={"state": "puebla", "type": "procedures"}
        )
        test_session.add_all([doc_qroo, doc_puebla])
        await test_session.commit()
        
        # 2. Search with state filter
        search_response = await test_client.get(
            "/api/v1/search",
            params={
                "query": "property registration",
                "state": "quintana_roo"
            },
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert search_response.status_code == 200
        results = search_response.json()
        
        # 3. Verify filtered results
        assert len(results["results"]) >= 1
        for result in results["results"]:
            assert result["metadata"]["state"] == "quintana_roo"
    
    async def test_search_within_document(
        self, test_client, authenticated_user, test_session
    ):
        """Test: Search within specific document"""
        # Setup
        document = Document(
            user_id=authenticated_user['id'],
            title="Test Doc"
        )
        test_session.add(document)
        await test_session.commit()
        await test_session.refresh(document)
        
        # Search within document
        response = await test_client.get(
            f"/api/v1/documents/{document.id}/search",
            params={"query": "usufruct"},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == 200


# ============================================================================
# INTEGRATION TESTS - DATA INTEGRITY
# ============================================================================

@pytest.mark.asyncio
class TestDataIntegrity:
    """Test data consistency across operations"""
    
    async def test_cascade_delete_on_user_deletion(
        self, test_session, authenticated_user
    ):
        """Test: Delete user -> Cascade delete all related data"""
        user_id = authenticated_user['id']
        
        # Create related data
        document = Document(user_id=user_id, title="Test")
        session = ChatSession(user_id=user_id, title="Chat")
        test_session.add_all([document, session])
        await test_session.commit()
        
        # Delete user
        user = await test_session.query(User).filter(
            User.id == user_id
        ).first()
        await test_session.delete(user)
        await test_session.commit()
        
        # Verify cascade
        remaining_docs = await test_session.query(Document).filter(
            Document.user_id == user_id
        ).all()
        assert len(remaining_docs) == 0
    
    async def test_transaction_rollback_on_error(self, test_session):
        """Test: Rollback changes if error occurs during transaction"""
        try:
            # Intentional error
            user = User(email="test@test.com")
            test_session.add(user)
            await test_session.flush()
            
            # This should fail
            raise Exception("Simulated error")
            
        except Exception:
            await test_session.rollback()
        
        # Verify rollback
        users = await test_session.query(User).all()
        assert len(users) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
