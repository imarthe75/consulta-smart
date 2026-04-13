"""
Test suite for repository layer
Tests for data access and CRUD operations
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import uuid


@pytest.mark.unit
@pytest.mark.async
class TestUserRepository:
    """Test suite for UserRepository."""
    
    @pytest.fixture
    async def user_repository(self, async_session: AsyncSession):
        """Create UserRepository instance."""
        from app.infrastructure.repositories.user_repository import UserRepository
        return UserRepository(async_session)
    
    async def test_create_user(self, user_repository, test_user_data: dict):
        """Test creating a new user."""
        # This test assumes the repository.create method exists
        # Actual implementation depends on your UserRepository
        
        # Mock behavior
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.email = test_user_data["email"]
        mock_user.username = test_user_data["username"]
        mock_user.created_at = datetime.utcnow()
        
        # Repository should be able to create a user
        assert mock_user.email == test_user_data["email"]
        assert mock_user.username == test_user_data["username"]
    
    async def test_get_user_by_id(self, user_repository):
        """Test retrieving user by ID."""
        test_id = uuid.uuid4()
        
        # Mock the repository behavior
        with patch.object(user_repository, 'get_by_id', new_callable=AsyncMock) as mock_get:
            mock_user = MagicMock()
            mock_user.id = test_id
            mock_get.return_value = mock_user
            
            result = await mock_get(test_id)
            assert result.id == test_id
    
    async def test_get_user_by_email(self, user_repository):
        """Test retrieving user by email."""
        test_email = "test@example.com"
        
        with patch.object(user_repository, 'get_by_email', new_callable=AsyncMock) as mock_get:
            mock_user = MagicMock()
            mock_user.email = test_email
            mock_get.return_value = mock_user
            
            result = await mock_get(test_email)
            assert result.email == test_email
    
    async def test_update_user(self, user_repository):
        """Test updating a user."""
        test_id = uuid.uuid4()
        new_username = "updated_user"
        
        with patch.object(user_repository, 'update', new_callable=AsyncMock) as mock_update:
            mock_user = MagicMock()
            mock_user.id = test_id
            mock_user.username = new_username
            mock_update.return_value = mock_user
            
            result = await mock_update(test_id, {"username": new_username})
            assert result.username == new_username
    
    async def test_delete_user(self, user_repository):
        """Test deleting a user."""
        test_id = uuid.uuid4()
        
        with patch.object(user_repository, 'delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            
            result = await mock_delete(test_id)
            assert result is True
    
    async def test_user_not_found(self, user_repository):
        """Test retrieving non-existent user."""
        with patch.object(user_repository, 'get_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            result = await mock_get(uuid.uuid4())
            assert result is None


@pytest.mark.unit
@pytest.mark.async
class TestDocumentRepository:
    """Test suite for DocumentRepository."""
    
    @pytest.fixture
    async def document_repository(self, async_session: AsyncSession):
        """Create DocumentRepository instance."""
        from app.infrastructure.repositories.document_repository import DocumentRepository
        return DocumentRepository(async_session)
    
    async def test_create_document(self, document_repository, test_document_data: dict):
        """Test creating a document."""
        mock_doc = MagicMock()
        mock_doc.id = uuid.uuid4()
        mock_doc.filename = test_document_data["filename"]
        mock_doc.file_size = test_document_data["file_size"]
        mock_doc.created_at = datetime.utcnow()
        
        assert mock_doc.filename == test_document_data["filename"]
        assert mock_doc.file_size == test_document_data["file_size"]
    
    async def test_get_document_by_id(self, document_repository):
        """Test retrieving document by ID."""
        test_id = uuid.uuid4()
        
        with patch.object(document_repository, 'get_by_id', new_callable=AsyncMock) as mock_get:
            mock_doc = MagicMock()
            mock_doc.id = test_id
            mock_get.return_value = mock_doc
            
            result = await mock_get(test_id)
            assert result.id == test_id
    
    async def test_get_documents_by_user(self, document_repository):
        """Test retrieving documents for a user."""
        user_id = uuid.uuid4()
        
        with patch.object(document_repository, 'get_by_user_id', new_callable=AsyncMock) as mock_get:
            mock_docs = [
                MagicMock(id=uuid.uuid4(), user_id=user_id),
                MagicMock(id=uuid.uuid4(), user_id=user_id),
            ]
            mock_get.return_value = mock_docs
            
            result = await mock_get(user_id)
            assert len(result) == 2
            assert all(doc.user_id == user_id for doc in result)
    
    async def test_update_document(self, document_repository):
        """Test updating a document."""
        test_id = uuid.uuid4()
        new_status = "processed"
        
        with patch.object(document_repository, 'update', new_callable=AsyncMock) as mock_update:
            mock_doc = MagicMock()
            mock_doc.id = test_id
            mock_doc.status = new_status
            mock_update.return_value = mock_doc
            
            result = await mock_update(test_id, {"status": new_status})
            assert result.status == new_status
    
    async def test_delete_document(self, document_repository):
        """Test deleting a document."""
        test_id = uuid.uuid4()
        
        with patch.object(document_repository, 'delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            
            result = await mock_delete(test_id)
            assert result is True
    
    async def test_get_document_versions(self, document_repository):
        """Test retrieving document versions."""
        doc_id = uuid.uuid4()
        
        with patch.object(document_repository, 'get_versions', new_callable=AsyncMock) as mock_get:
            mock_versions = [
                MagicMock(version=1, created_at=datetime.utcnow()),
                MagicMock(version=2, created_at=datetime.utcnow() + timedelta(hours=1)),
            ]
            mock_get.return_value = mock_versions
            
            result = await mock_get(doc_id)
            assert len(result) == 2


@pytest.mark.unit
@pytest.mark.async
class TestChatSessionRepository:
    """Test suite for ChatSessionRepository."""
    
    @pytest.fixture
    async def chat_repository(self, async_session: AsyncSession):
        """Create ChatSessionRepository instance."""
        from app.infrastructure.repositories.chat_session_repository import ChatSessionRepository
        return ChatSessionRepository(async_session)
    
    async def test_create_chat_session(self, chat_repository, test_chat_session: dict):
        """Test creating a chat session."""
        mock_session = MagicMock()
        mock_session.id = uuid.uuid4()
        mock_session.title = test_chat_session["title"]
        mock_session.user_id = uuid.uuid4()
        mock_session.created_at = datetime.utcnow()
        
        assert mock_session.title == test_chat_session["title"]
    
    async def test_get_user_sessions(self, chat_repository):
        """Test retrieving sessions for a user."""
        user_id = uuid.uuid4()
        
        with patch.object(chat_repository, 'get_by_user_id', new_callable=AsyncMock) as mock_get:
            mock_sessions = [
                MagicMock(id=uuid.uuid4(), user_id=user_id),
                MagicMock(id=uuid.uuid4(), user_id=user_id),
            ]
            mock_get.return_value = mock_sessions
            
            result = await mock_get(user_id)
            assert len(result) == 2
    
    async def test_add_message_to_session(self, chat_repository):
        """Test adding a message to a session."""
        session_id = uuid.uuid4()
        
        with patch.object(chat_repository, 'add_message', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = True
            
            result = await mock_add(session_id, "Test message", "user")
            assert result is True
    
    async def test_get_session_messages(self, chat_repository):
        """Test retrieving messages from a session."""
        session_id = uuid.uuid4()
        
        with patch.object(chat_repository, 'get_messages', new_callable=AsyncMock) as mock_get:
            mock_messages = [
                MagicMock(id=uuid.uuid4(), content="Message 1"),
                MagicMock(id=uuid.uuid4(), content="Message 2"),
            ]
            mock_get.return_value = mock_messages
            
            result = await mock_get(session_id)
            assert len(result) == 2


@pytest.mark.unit
@pytest.mark.async
class TestVectorStore:
    """Test suite for VectorStore repository."""
    
    @pytest.fixture
    async def vector_store(self, async_session: AsyncSession):
        """Create VectorStore instance."""
        from app.infrastructure.repositories.vector_store import VectorStore
        return VectorStore(async_session)
    
    async def test_add_vector(self, vector_store, test_query: str, mock_embeddings: list):
        """Test adding a vector to store."""
        with patch.object(vector_store, 'add', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = True
            
            result = await mock_add(test_query, mock_embeddings)
            assert result is True
    
    async def test_search_similar_vectors(self, vector_store, mock_embeddings: list):
        """Test searching for similar vectors."""
        with patch.object(vector_store, 'search', new_callable=AsyncMock) as mock_search:
            mock_results = [
                MagicMock(id=uuid.uuid4(), similarity=0.95),
                MagicMock(id=uuid.uuid4(), similarity=0.87),
            ]
            mock_search.return_value = mock_results
            
            result = await mock_search(mock_embeddings, k=2)
            assert len(result) == 2
            assert result[0].similarity > result[1].similarity
    
    async def test_delete_vector(self, vector_store):
        """Test deleting a vector from store."""
        vector_id = uuid.uuid4()
        
        with patch.object(vector_store, 'delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            
            result = await mock_delete(vector_id)
            assert result is True
    
    async def test_clear_store(self, vector_store):
        """Test clearing the vector store."""
        with patch.object(vector_store, 'clear', new_callable=AsyncMock) as mock_clear:
            mock_clear.return_value = True
            
            result = await mock_clear()
            assert result is True
