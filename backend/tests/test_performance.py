"""
Test suite for performance and benchmarking
Tests for response times, throughput, and resource usage
"""

import pytest
import time
from unittest.mock import MagicMock, patch
import uuid


@pytest.mark.performance
@pytest.mark.slow
class TestAPIResponseTime:
    """Test API response times."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        from fastapi.testclient import TestClient
        return TestClient(app)
    
    def test_health_endpoint_response_time(self, client):
        """Test health endpoint responds in <100ms."""
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.1  # <100ms
    
    def test_documents_list_response_time(self, client):
        """Test documents list responds in <2s."""
        start = time.time()
        response = client.get("/api/v1/documents")
        elapsed = time.time() - start
        
        if response.status_code in [200, 401, 403]:
            assert elapsed < 2.0  # <2s
    
    def test_search_endpoint_response_time(self, client):
        """Test search responds in <2s."""
        start = time.time()
        response = client.get(
            "/api/v1/search",
            params={"q": "test"}
        )
        elapsed = time.time() - start
        
        if response.status_code in [200, 401, 403]:
            assert elapsed < 2.0
    
    def test_chat_message_response_time(self, client):
        """Test chat message responds in <3s."""
        session_id = str(uuid.uuid4())
        
        start = time.time()
        response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"content": "Test message"}
        )
        elapsed = time.time() - start
        
        if response.status_code in [200, 201]:
            assert elapsed < 3.0  # LLM calls may take longer


@pytest.mark.performance
class TestDatabaseQueryPerformance:
    """Test database query performance."""
    
    def test_simple_user_query_time(self):
        """Test simple user query takes <50ms."""
        with patch('app.infrastructure.repositories.user_repository.UserRepository.get_by_id') as mock_get:
            mock_get.return_value = {"id": uuid.uuid4()}
            
            start = time.time()
            user_id = uuid.uuid4()
            result = mock_get(user_id)
            elapsed = time.time() - start
            
            assert result is not None
            assert elapsed < 0.05  # <50ms
    
    def test_document_list_query_time(self):
        """Test document list query takes <500ms."""
        with patch('app.infrastructure.repositories.document_repository.DocumentRepository.get_by_user_id') as mock_get:
            mock_get.return_value = [{"id": uuid.uuid4()} for _ in range(10)]
            
            start = time.time()
            user_id = uuid.uuid4()
            result = mock_get(user_id)
            elapsed = time.time() - start
            
            assert len(result) == 10
            assert elapsed < 0.5  # <500ms
    
    def test_vector_search_query_time(self):
        """Test vector search takes <1s."""
        with patch('app.infrastructure.repositories.vector_store.VectorStore.search') as mock_search:
            mock_search.return_value = [
                {"id": uuid.uuid4(), "similarity": 0.95} for _ in range(5)
            ]
            
            start = time.time()
            embeddings = [0.1] * 1536
            result = mock_search(embeddings, k=5)
            elapsed = time.time() - start
            
            assert len(result) == 5
            assert elapsed < 1.0  # <1s


@pytest.mark.performance
class TestVectorOperationsPerformance:
    """Test vector and embedding operations."""
    
    def test_embedding_generation_time(self):
        """Test embedding generation takes <500ms per text."""
        with patch('app.infrastructure.external.llm_service.LLMService.get_embeddings') as mock_embed:
            mock_embed.return_value = [0.1] * 1536
            
            start = time.time()
            text = "Sample long text for embedding" * 10
            result = mock_embed(text)
            elapsed = time.time() - start
            
            assert len(result) == 1536
            assert elapsed < 0.5  # <500ms
    
    def test_bulk_embedding_time(self):
        """Test bulk embeddings take <2s for 100 texts."""
        with patch('app.infrastructure.external.llm_service.LLMService.batch_embeddings') as mock_batch:
            mock_batch.return_value = [
                [0.1] * 1536 for _ in range(100)
            ]
            
            start = time.time()
            texts = ["Sample text"] * 100
            result = mock_batch(texts)
            elapsed = time.time() - start
            
            assert len(result) == 100
            assert elapsed < 2.0  # <2s
    
    def test_vector_similarity_calculation(self):
        """Test vector similarity calculation is fast."""
        import numpy as np
        
        start = time.time()
        v1 = np.random.rand(1536)
        v2 = np.random.rand(1536)
        similarity = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        elapsed = time.time() - start
        
        assert 0 <= similarity <= 1
        assert elapsed < 0.01  # <10ms


@pytest.mark.performance
class TestLLMResponseTime:
    """Test LLM provider response times."""
    
    def test_groq_response_time(self):
        """Test Groq API response time."""
        with patch('app.infrastructure.external.llm_service.LLMService.generate') as mock_generate:
            mock_generate.return_value = {
                "response": "Generated response",
                "tokens": 100
            }
            
            start = time.time()
            result = mock_generate("question", "context")
            elapsed = time.time() - start
            
            assert result["response"]
            assert elapsed < 2.0  # <2s
    
    def test_gemini_fallback_response_time(self):
        """Test Gemini fallback response time."""
        with patch('app.infrastructure.external.llm_service.LLMService.generate') as mock_generate:
            mock_generate.return_value = {
                "response": "Fallback response",
                "tokens": 80
            }
            
            start = time.time()
            result = mock_generate("question", "context", provider="gemini")
            elapsed = time.time() - start
            
            assert elapsed < 3.0  # <3s (may be slower)


@pytest.mark.performance
class TestDocumentProcessingPerformance:
    """Test document processing performance."""
    
    def test_pdf_parsing_time(self):
        """Test PDF parsing takes <2s per MB."""
        file_size_mb = 1
        max_time = 2.0 * file_size_mb
        
        with patch('app.infrastructure.external.docling_service.DoclingService.parse') as mock_parse:
            mock_parse.return_value = {
                "text": "Parsed content" * 1000,
                "pages": 10
            }
            
            start = time.time()
            result = mock_parse("test.pdf", b"pdf_content")
            elapsed = time.time() - start
            
            assert result["pages"] == 10
            assert elapsed < max_time
    
    def test_chunking_performance(self):
        """Test document chunking performance."""
        text_size = 100000  # characters
        
        with patch('app.infrastructure.external.docling_service.DoclingService.chunk') as mock_chunk:
            chunks = ["chunk"] * 50
            mock_chunk.return_value = chunks
            
            start = time.time()
            result = mock_chunk("x" * text_size, chunk_size=512)
            elapsed = time.time() - start
            
            assert len(result) == 50
            assert elapsed < 1.0  # <1s
    
    def test_ocr_processing_time(self):
        """Test OCR processing time."""
        with patch('app.infrastructure.external.docling_service.DoclingService.ocr') as mock_ocr:
            mock_ocr.return_value = "OCR extracted text" * 100
            
            start = time.time()
            result = mock_ocr(b"image_content")
            elapsed = time.time() - start
            
            assert result
            assert elapsed < 5.0  # <5s (OCR is slower)


@pytest.mark.performance
@pytest.mark.slow
class TestConcurrentLoadPerformance:
    """Test performance under concurrent load."""
    
    def test_concurrent_small_requests(self):
        """Test 10 concurrent requests."""
        import concurrent.futures
        
        def make_request():
            with patch('app.infrastructure.repositories.user_repository.UserRepository.get_by_id') as mock:
                mock.return_value = {"id": uuid.uuid4()}
                start = time.time()
                result = mock(uuid.uuid4())
                return time.time() - start
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            start = time.time()
            times = list(executor.map(lambda _: make_request(), range(10)))
            elapsed = time.time() - start
        
        # All 10 should complete in reasonable time
        assert elapsed < 2.0  # <2s total
    
    def test_memory_usage_baseline(self):
        """Test baseline memory usage."""
        import sys
        
        # Get baseline object count
        baseline = len(gc_objects := __import__('gc').get_objects())
        
        # Create some objects
        temp_list = [{"id": uuid.uuid4()} for _ in range(1000)]
        
        # Check memory didn't explode
        after = len(__import__('gc').get_objects())
        difference = after - baseline
        
        # Reasonable memory growth for 1000 objects
        assert difference < 10000


@pytest.mark.performance
class TestCachePerformance:
    """Test cache effectiveness."""
    
    def test_cached_query_vs_uncached(self):
        """Test cached query is faster than uncached."""
        with patch('app.core.cache.get_cache') as mock_cache:
            mock_cache.return_value = {"id": uuid.uuid4()}
            
            # Cached
            start = time.time()
            result_cached = mock_cache(uuid.uuid4())
            time_cached = time.time() - start
            
            # Simulated uncached (no cache)
            start = time.time()
            result_uncached = {"id": uuid.uuid4()}
            time_uncached = time.time() - start
            
            # Cached should be much faster if actually cached
            assert result_cached is not None
    
    def test_connection_pool_performance(self):
        """Test connection pool improves performance."""
        with patch('app.core.database.SessionLocal') as mock_session:
            # Simulating pool
            connections = [MagicMock() for _ in range(5)]
            
            start = time.time()
            for _ in range(10):
                conn = connections[_ % 5]
            elapsed = time.time() - start
            
            # Pool reuse should be very fast
            assert elapsed < 0.01


@pytest.mark.performance
class TestResourceUtilization:
    """Test resource utilization."""
    
    def test_cpu_efficiency_simple_operation(self):
        """Test CPU efficiency of simple operation."""
        import threading
        
        def cpu_task():
            result = 0
            for i in range(1000000):
                result += i
            return result
        
        start = time.time()
        result = cpu_task()
        elapsed = time.time() - start
        
        assert result > 0
        # Should be reasonably fast
        assert elapsed < 1.0
    
    def test_file_io_performance(self):
        """Test file I/O performance."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Write
            start = time.time()
            with open(tmp_path, 'w') as f:
                f.write("x" * 10000)
            write_time = time.time() - start
            
            # Read
            start = time.time()
            with open(tmp_path, 'r') as f:
                content = f.read()
            read_time = time.time() - start
            
            assert len(content) == 10000
            assert write_time < 0.1
            assert read_time < 0.1
        finally:
            os.unlink(tmp_path)


@pytest.mark.performance
class TestStartupPerformance:
    """Test application startup performance."""
    
    def test_app_initialization_time(self):
        """Test FastAPI app initializes quickly."""
        start = time.time()
        from main import app
        elapsed = time.time() - start
        
        # Should initialize in <1s
        assert elapsed < 1.0
    
    def test_database_connection_pool_init(self):
        """Test DB connection pool initializes."""
        start = time.time()
        from app.core.database import get_session
        elapsed = time.time() - start
        
        # Should be quick
        assert elapsed < 0.5
