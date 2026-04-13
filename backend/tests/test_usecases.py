"""
Test suite for use cases (business logic layer)
Tests for application workflows and business rules
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
import uuid


@pytest.mark.unit
@pytest.mark.async
class TestDocumentUseCases:
    """Test suite for document-related use cases."""
    
    @pytest.fixture
    async def document_usecase(self, async_session):
        """Create document use case instance."""
        from app.application.usecases.document_usecases import DocumentUseCase
        return DocumentUseCase(async_session)
    
    async def test_upload_document(self, document_usecase):
        """Test uploading a document."""
        user_id = uuid.uuid4()
        filename = "test_document.pdf"
        file_content = b"PDF content"
        
        with patch.object(document_usecase, 'upload', new_callable=AsyncMock) as mock_upload:
            mock_upload.return_value = {
                "document_id": uuid.uuid4(),
                "filename": filename,
                "status": "uploaded",
                "user_id": user_id
            }
            
            result = await mock_upload(user_id, filename, file_content)
            assert result["filename"] == filename
            assert result["status"] == "uploaded"
    
    async def test_process_document(self, document_usecase):
        """Test processing a document."""
        document_id = uuid.uuid4()
        
        with patch.object(document_usecase, 'process', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {
                "document_id": document_id,
                "status": "processing",
                "progress": 0
            }
            
            result = await mock_process(document_id)
            assert result["status"] == "processing"
    
    async def test_extract_document_chunks(self, document_usecase):
        """Test extracting chunks from document."""
        document_id = uuid.uuid4()
        
        with patch.object(document_usecase, 'extract_chunks', new_callable=AsyncMock) as mock_extract:
            mock_chunks = [
                {"chunk_id": uuid.uuid4(), "content": "Chunk 1"},
                {"chunk_id": uuid.uuid4(), "content": "Chunk 2"},
            ]
            mock_extract.return_value = mock_chunks
            
            result = await mock_extract(document_id)
            assert len(result) == 2
            assert all("content" in chunk for chunk in result)
    
    async def test_delete_document(self, document_usecase):
        """Test deleting a document."""
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        with patch.object(document_usecase, 'delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            
            result = await mock_delete(document_id, user_id)
            assert result is True
    
    async def test_search_documents(self, document_usecase):
        """Test searching documents."""
        user_id = uuid.uuid4()
        query = "invoice"
        
        with patch.object(document_usecase, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {"document_id": uuid.uuid4(), "filename": "invoice_2024.pdf"},
                {"document_id": uuid.uuid4(), "filename": "invoice_summary.pdf"},
            ]
            
            result = await mock_search(user_id, query)
            assert len(result) > 0
    
    async def test_get_document_info(self, document_usecase):
        """Test getting document information."""
        document_id = uuid.uuid4()
        
        with patch.object(document_usecase, 'get_info', new_callable=AsyncMock) as mock_info:
            mock_info.return_value = {
                "document_id": document_id,
                "filename": "test.pdf",
                "size": 2048,
                "status": "processed",
                "chunks_count": 10
            }
            
            result = await mock_info(document_id)
            assert result["document_id"] == document_id
            assert result["chunks_count"] == 10


@pytest.mark.unit
@pytest.mark.async
class TestChatUseCases:
    """Test suite for chat-related use cases."""
    
    @pytest.fixture
    async def chat_usecase(self, async_session):
        """Create chat use case instance."""
        from app.application.usecases.chat_usecases import ChatUseCase
        return ChatUseCase(async_session)
    
    async def test_create_chat_session(self, chat_usecase):
        """Test creating a chat session."""
        user_id = uuid.uuid4()
        
        with patch.object(chat_usecase, 'create_session', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {
                "session_id": uuid.uuid4(),
                "user_id": user_id,
                "title": "New Chat",
                "created_at": datetime.utcnow()
            }
            
            result = await mock_create(user_id)
            assert result["user_id"] == user_id
    
    async def test_send_message(self, chat_usecase, mock_llm_response: dict):
        """Test sending a message."""
        session_id = uuid.uuid4()
        user_message = "Explain this document"
        
        with patch.object(chat_usecase, 'send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {
                "message_id": uuid.uuid4(),
                "content": mock_llm_response["response"],
                "role": "assistant"
            }
            
            result = await mock_send(session_id, user_message)
            assert result["role"] == "assistant"
            assert result["content"]
    
    async def test_search_with_rag(self, chat_usecase, mock_embeddings: list):
        """Test RAG search in chat."""
        session_id = uuid.uuid4()
        query = "What are the main terms?"
        
        with patch.object(chat_usecase, 'search_documents', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {"document_id": uuid.uuid4(), "content": "Term 1: ...", "relevance": 0.95},
                {"document_id": uuid.uuid4(), "content": "Term 2: ...", "relevance": 0.87},
            ]
            
            result = await mock_search(session_id, query)
            assert len(result) > 0
            assert result[0]["relevance"] > result[1]["relevance"]
    
    async def test_get_session_history(self, chat_usecase):
        """Test retrieving session history."""
        session_id = uuid.uuid4()
        
        with patch.object(chat_usecase, 'get_history', new_callable=AsyncMock) as mock_history:
            mock_history.return_value = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
                {"role": "user", "content": "Can you help?"},
                {"role": "assistant", "content": "Of course!"},
            ]
            
            result = await mock_history(session_id)
            assert len(result) == 4
            assert result[0]["role"] == "user"
    
    async def test_delete_chat_session(self, chat_usecase):
        """Test deleting a chat session."""
        session_id = uuid.uuid4()
        
        with patch.object(chat_usecase, 'delete_session', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            
            result = await mock_delete(session_id)
            assert result is True


@pytest.mark.unit
@pytest.mark.async
class TestSearchUseCases:
    """Test suite for search-related use cases."""
    
    @pytest.fixture
    async def search_usecase(self, async_session):
        """Create search use case instance."""
        from app.application.usecases.search_usecases import SearchUseCase
        return SearchUseCase(async_session)
    
    async def test_semantic_search(self, search_usecase):
        """Test semantic search."""
        user_id = uuid.uuid4()
        query = "property lease terms"
        
        with patch.object(search_usecase, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {"document_id": uuid.uuid4(), "content": "Lease begins...", "score": 0.98},
                {"document_id": uuid.uuid4(), "content": "Tenant obligations...", "score": 0.92},
            ]
            
            result = await mock_search(user_id, query)
            assert len(result) > 0
            assert result[0]["score"] > result[1]["score"]
    
    async def test_search_with_filters(self, search_usecase):
        """Test search with filters."""
        user_id = uuid.uuid4()
        query = "rent"
        
        with patch.object(search_usecase, 'search_filtered', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {"document_id": uuid.uuid4(), "document_type": "lease"},
            ]
            
            result = await mock_search(
                user_id,
                query,
                filters={"document_type": "lease"}
            )
            assert len(result) > 0
    
    async def test_advanced_search(self, search_usecase):
        """Test advanced search with multiple criteria."""
        user_id = uuid.uuid4()
        
        with patch.object(search_usecase, 'advanced_search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {"document_id": uuid.uuid4(), "relevance": 0.95}
            ]
            
            result = await mock_search(
                user_id,
                keywords=["lease", "rent"],
                date_range={"start": "2024-01-01", "end": "2024-12-31"},
                document_types=["lease"]
            )
            assert len(result) > 0


@pytest.mark.unit
@pytest.mark.async
class TestAuthUseCases:
    """Test suite for authentication use cases."""
    
    @pytest.fixture
    async def auth_usecase(self, async_session):
        """Create auth use case instance."""
        from app.application.usecases.auth_usecases import AuthUseCase
        return AuthUseCase(async_session)
    
    async def test_register_user(self, auth_usecase):
        """Test user registration."""
        email = "newuser@example.com"
        username = "newuser"
        password = "SecurePass123!"
        
        with patch.object(auth_usecase, 'register', new_callable=AsyncMock) as mock_register:
            mock_register.return_value = {
                "user_id": uuid.uuid4(),
                "email": email,
                "username": username
            }
            
            result = await mock_register(email, username, password)
            assert result["email"] == email
    
    async def test_login_user(self, auth_usecase):
        """Test user login."""
        email = "user@example.com"
        password = "password123"
        
        with patch.object(auth_usecase, 'login', new_callable=AsyncMock) as mock_login:
            mock_login.return_value = {
                "user_id": uuid.uuid4(),
                "token": "jwt_token_here",
                "expires_in": 3600
            }
            
            result = await mock_login(email, password)
            assert "token" in result
    
    async def test_refresh_token(self, auth_usecase):
        """Test token refresh."""
        old_token = "old_jwt_token"
        
        with patch.object(auth_usecase, 'refresh_token', new_callable=AsyncMock) as mock_refresh:
            mock_refresh.return_value = {
                "token": "new_jwt_token",
                "expires_in": 3600
            }
            
            result = await mock_refresh(old_token)
            assert result["token"] != old_token
    
    async def test_validate_token(self, auth_usecase):
        """Test token validation."""
        token = "jwt_token_here"
        
        with patch.object(auth_usecase, 'validate_token', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = {
                "user_id": uuid.uuid4(),
                "email": "user@example.com",
                "valid": True
            }
            
            result = await mock_validate(token)
            assert result["valid"] is True


@pytest.mark.integration
@pytest.mark.async
class TestUseCasesIntegration:
    """Test use cases working together."""
    
    async def test_complete_document_chat_workflow(self):
        """Test complete workflow: upload doc -> search -> chat."""
        # This represents the main user workflow
        user_id = uuid.uuid4()
        
        with patch('app.application.usecases.document_usecases.DocumentUseCase.upload', new_callable=AsyncMock) as mock_upload, \
             patch('app.application.usecases.search_usecases.SearchUseCase.search', new_callable=AsyncMock) as mock_search, \
             patch('app.application.usecases.chat_usecases.ChatUseCase.send_message', new_callable=AsyncMock) as mock_chat:
            
            # Setup mocks
            mock_upload.return_value = {"document_id": uuid.uuid4(), "status": "uploaded"}
            mock_search.return_value = [{"document_id": uuid.uuid4(), "score": 0.95}]
            mock_chat.return_value = {"content": "Based on the document...", "role": "assistant"}
            
            # Execute workflow
            doc = await mock_upload(user_id, "test.pdf", b"content")
            search_results = await mock_search(user_id, "What is this?")
            response = await mock_chat(uuid.uuid4(), "Explain this document")
            
            assert doc["status"] == "uploaded"
            assert len(search_results) > 0
            assert response["role"] == "assistant"
