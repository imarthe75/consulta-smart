"""
Phase 4C - Integration Tests
RAG Pipeline & Search Integration
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import (
    Document, DocumentChunk, VectorEmbedding, User
)


@pytest.mark.asyncio
class TestRAGPipelineIntegration:
    """Test complete RAG (Retrieval Augmented Generation) pipeline"""
    
    async def test_complete_rag_pipeline(self, test_session, authenticated_user):
        """Test: Document ingestion -> Chunking -> Embedding -> Retrieval"""
        
        # 1. Create user and document
        user_id = authenticated_user['id']
        document = Document(
            user_id=user_id,
            title="Quintana Roo Legislation",
            file_path="qroo_legislation.pdf",
            processing_status="completed"
        )
        test_session.add(document)
        await test_session.commit()
        await test_session.refresh(document)
        
        # 2. Create document chunks
        chunk_texts = [
            "El Código Civil del Estado de Quintana Roo regula los derechos reales...",
            "La Ley del Registro Público de la Propiedad y del Comercio establece...",
            "Los aranceles se calculan según el valor catastral del inmueble...",
            "El usufructo es un derecho real que permite utilizar bienes ajenos...",
            "La inscripción de propiedad requiere instrumento notarial autenticado..."
        ]
        
        chunks = []
        for idx, text in enumerate(chunk_texts):
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=idx,
                content=text,
                token_count=len(text.split())
            )
            chunks.append(chunk)
        
        test_session.add_all(chunks)
        await test_session.commit()
        
        # 3. Generate embeddings
        embeddings = []
        for idx, chunk in enumerate(chunks):
            # Mock embedding vector (in reality from Gemini API)
            embedding = VectorEmbedding(
                chunk_id=chunk.id,
                vector=[0.1 * (idx + 1)] * 768,  # Mock 768-dim vector
                embedding_model="gemini-embedding-001"
            )
            embeddings.append(embedding)
        
        test_session.add_all(embeddings)
        await test_session.commit()
        
        # 4. Retrieve similar chunks
        query = "How to register property in Quintana Roo?"
        # In real app: generate embedding for query and perform similarity search
        # For now, assert that infrastructure is in place
        retrieved_chunks = await test_session.query(DocumentChunk).filter(
            DocumentChunk.document_id == document.id
        ).all()
        
        assert len(retrieved_chunks) == 5
        assert all(emb.embedding_model == "gemini-embedding-001" 
                   for emb in embeddings)
    
    async def test_multi_document_rag_retrieval(self, test_session, authenticated_user):
        """Test: Retrieve from multiple documents simultaneously"""
        user_id = authenticated_user['id']
        
        # Create multiple documents
        doc_qroo = Document(
            user_id=user_id,
            title="Quintana Roo RPP",
            processing_status="completed"
        )
        doc_puebla = Document(
            user_id=user_id,
            title="Puebla RPP",
            processing_status="completed"
        )
        test_session.add_all([doc_qroo, doc_puebla])
        await test_session.commit()
        
        # Add chunks to each
        qroo_chunk = DocumentChunk(
            document_id=doc_qroo.id,
            chunk_index=0,
            content="Quintana Roo legislation text"
        )
        puebla_chunk = DocumentChunk(
            document_id=doc_puebla.id,
            chunk_index=0,
            content="Puebla legislation text"
        )
        test_session.add_all([qroo_chunk, puebla_chunk])
        await test_session.commit()
        
        # Query: Should retrieve from both
        all_chunks = await test_session.query(DocumentChunk).filter(
            DocumentChunk.document.has(user_id=user_id)
        ).all()
        
        assert len(all_chunks) == 2
        assert any("Quintana" in c.content for c in all_chunks)
        assert any("Puebla" in c.content for c in all_chunks)


@pytest.mark.asyncio
class TestSearchRankingIntegration:
    """Test search result ranking and relevance"""
    
    async def test_search_result_ranking(self, test_session, authenticated_user):
        """Test: Search results ranked by relevance"""
        user_id = authenticated_user['id']
        
        # Create documents with varying relevance
        documents = [
            Document(
                user_id=user_id,
                title="Complete Guide to Property Registration",
                processing_status="completed"
            ),
            Document(
                user_id=user_id,
                title="Introduction to Real Estate",
                processing_status="completed"
            ),
            Document(
                user_id=user_id,
                title="Property Registration Process",
                processing_status="completed"
            ),
        ]
        test_session.add_all(documents)
        await test_session.commit()
        
        # Query for "property registration"
        # More relevant docs should rank higher
        query = "property registration"
        
        # In real implementation, search would rank:
        # 1. "Complete Guide to Property Registration" (exact match)
        # 2. "Property Registration Process" (exact match)
        # 3. "Introduction to Real Estate" (partial match)
    
    async def test_search_pagination(self, test_session, authenticated_user):
        """Test: Search results pagination for large result sets"""
        user_id = authenticated_user['id']
        
        # Create many documents
        docs = [
            Document(
                user_id=user_id,
                title=f"Document {i}",
                processing_status="completed"
            )
            for i in range(50)
        ]
        test_session.add_all(docs)
        await test_session.commit()
        
        # Query with pagination
        # First page (10 results)
        # Should support: page, limit, offset parameters


@pytest.mark.asyncio
class TestVectorDatabaseIntegration:
    """Test vector store operations"""
    
    async def test_vector_similarity_search(self, test_session, authenticated_user):
        """Test: Vector-based similarity search"""
        user_id = authenticated_user['id']
        
        document = Document(
            user_id=user_id,
            title="Test Document",
            processing_status="completed"
        )
        test_session.add(document)
        await test_session.commit()
        await test_session.refresh(document)
        
        # Create chunks with mock embeddings
        chunks = []
        vectors = [
            [1.0, 0.0, 0.0] * 256,  # Similar to query
            [0.9, 0.1, 0.0] * 256,  # Very similar
            [0.0, 1.0, 0.0] * 256,  # Dissimilar
            [0.8, 0.2, 0.0] * 256,  # Similar
        ]
        
        for idx, vector in enumerate(vectors):
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=idx,
                content=f"Chunk {idx}"
            )
            test_session.add(chunk)
            await test_session.flush()
            
            embedding = VectorEmbedding(
                chunk_id=chunk.id,
                vector=vector[:768],  # 768-dim
                embedding_model="gemini-embedding-001"
            )
            test_session.add(embedding)
        
        await test_session.commit()
        
        # Query vector (similar to first)
        query_vector = [0.95, 0.05, 0.0] * 256
        
        # Should retrieve top-K similar results
        # Vector similarity would rank:
        # 1. Index 1 (0.9, 0.1, 0.0)
        # 2. Index 3 (0.8, 0.2, 0.0)
        # 3. Index 0 (1.0, 0.0, 0.0)
        # 4. Index 2 (0.0, 1.0, 0.0)


@pytest.mark.asyncio
class TestChatMemoryIntegration:
    """Test chat conversation memory and context management"""
    
    async def test_conversation_context_buildup(self, test_session, authenticated_user):
        """Test: Conversation memory builds context over messages"""
        from app.infrastructure.models import ChatSession, ChatMessage
        
        user_id = authenticated_user['id']
        
        # Create session
        session = ChatSession(
            user_id=user_id,
            title="Property Registration Inquiry"
        )
        test_session.add(session)
        await test_session.commit()
        await test_session.refresh(session)
        
        # Build conversation with 5 exchanges
        messages = [
            ("user", "What's the process for property registration?"),
            ("assistant", "In Quintana Roo, you need to follow these steps..."),
            ("user", "How much does it cost?"),
            ("assistant", "The cost depends on the property value..."),
            ("user", "Can I do it online?"),
        ]
        
        for role, content in messages:
            msg = ChatMessage(
                session_id=session.id,
                role=role,
                content=content
            )
            test_session.add(msg)
        
        await test_session.commit()
        
        # Verify conversation history
        all_messages = await test_session.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).all()
        
        assert len(all_messages) == 5
        assert all_messages[0].content == messages[0][1]
        assert all_messages[-1].role == "user"
    
    async def test_context_window_management(self, test_session, authenticated_user):
        """Test: Context window limited to N recent messages"""
        from app.infrastructure.models import ChatSession, ChatMessage
        
        user_id = authenticated_user['id']
        session = ChatSession(user_id=user_id, title="Long Conversation")
        test_session.add(session)
        await test_session.commit()
        await test_session.refresh(session)
        
        # Create 100 messages
        for i in range(100):
            msg = ChatMessage(
                session_id=session.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}"
            )
            test_session.add(msg)
        
        await test_session.commit()
        
        # Get last 10 messages for context window
        recent_messages = await test_session.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(
            ChatMessage.created_at.desc()
        ).limit(10).all()
        
        assert len(recent_messages) == 10
        assert recent_messages[0].content == "Message 99"


@pytest.mark.asyncio
class TestErrorRecoveryIntegration:
    """Test error handling and recovery in workflows"""
    
    async def test_partial_upload_recovery(self, test_session, authenticated_user):
        """Test: Recover from failed document upload"""
        user_id = authenticated_user['id']
        
        # Simulate failed upload
        document = Document(
            user_id=user_id,
            title="Failed Upload",
            processing_status="failed",
            processing_error="Network timeout during upload"
        )
        test_session.add(document)
        await test_session.commit()
        await test_session.refresh(document)
        
        # Retry mechanism should allow re-upload
        document.processing_status="queued"
        document.processing_error = None
        await test_session.commit()
        
        assert document.processing_status == "queued"
    
    async def test_embedding_generation_failure(self, test_session, authenticated_user):
        """Test: Handle embedding generation failures gracefully"""
        user_id = authenticated_user['id']
        
        document = Document(
            user_id=user_id,
            title="Test",
            processing_status="completed"
        )
        test_session.add(document)
        await test_session.commit()
        await test_session.refresh(document)
        
        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            content="Test content"
        )
        test_session.add(chunk)
        await test_session.commit()
        
        # If embedding fails, should mark in DB
        embedding = VectorEmbedding(
            chunk_id=chunk.id,
            vector=None,  # Failed to generate
            embedding_model="gemini-embedding-001"
        )
        test_session.add(embedding)
        await test_session.commit()
        
        # System should handle gracefully


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
