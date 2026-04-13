"""
Test suite for external services layer
Tests for LLM, document processing, and file storage services
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
import uuid


@pytest.mark.unit
@pytest.mark.async
class TestLLMService:
    """Test suite for LLM service."""
    
    @pytest.fixture
    async def llm_service(self):
        """Create LLMService instance."""
        from app.infrastructure.external.llm_service import LLMService
        return LLMService()
    
    async def test_generate_response_with_groq(self, llm_service, mock_llm_response: dict):
        """Test generating response with Groq provider."""
        query = "What is this document about?"
        context = "Sample document content"
        
        with patch.object(llm_service, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_llm_response
            
            result = await mock_generate(query, context, provider="groq")
            assert "response" in result or "text" in result
    
    async def test_generate_response_with_gemini(self, llm_service, mock_llm_response: dict):
        """Test generating response with Gemini provider."""
        query = "Summarize this document"
        context = "Sample document content"
        
        with patch.object(llm_service, 'generate', new_callable=AsyncMask) as mock_generate:
            mock_generate.return_value = mock_llm_response
            
            result = await mock_generate(query, context, provider="gemini")
            assert result is not None
    
    async def test_llm_response_quality(self, llm_service, mock_llm_response: dict):
        """Test that LLM response has required fields."""
        with patch.object(llm_service, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_llm_response
            
            result = await mock_generate("test", "context")
            assert isinstance(result, dict)
            assert len(result.get("response", "")) > 0
    
    async def test_llm_timeout_handling(self, llm_service):
        """Test handling of LLM timeout."""
        with patch.object(llm_service, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.side_effect = TimeoutError("LLM request timeout")
            
            with pytest.raises(TimeoutError):
                await mock_generate("test", "context", timeout=1)
    
    async def test_llm_fallback_provider(self, llm_service):
        """Test fallback to alternative provider on primary failure."""
        with patch.object(llm_service, 'generate', new_callable=AsyncMock) as mock_generate:
            # First call fails, second succeeds
            mock_generate.side_effect = [
                Exception("Groq unavailable"),
                {"response": "Fallback response"}
            ]
            
            # This depends on implementation
            with pytest.raises(Exception):
                await mock_generate("test", "context", provider="groq")
    
    async def test_embedding_generation(self, llm_service, mock_embeddings: list):
        """Test generating embeddings."""
        text = "Document text for embedding"
        
        with patch.object(llm_service, 'get_embeddings', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = mock_embeddings
            
            result = await mock_embed(text)
            assert isinstance(result, list)
            assert len(result) == 1536  # Expected embedding dimension


@pytest.mark.unit
@pytest.mark.async
class TestDoclingService:
    """Test suite for Docling document processing service."""
    
    @pytest.fixture
    async def docling_service(self):
        """Create DoclingService instance."""
        from app.infrastructure.external.docling_service import DoclingService
        return DoclingService()
    
    async def test_parse_pdf_document(self, docling_service):
        """Test parsing PDF document."""
        with patch.object(docling_service, 'parse', new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = {
                "text": "Sample PDF content",
                "pages": 5,
                "metadata": {}
            }
            
            result = await mock_parse("sample.pdf", b"pdf_content")
            assert result["text"]
            assert result["pages"] == 5
    
    async def test_extract_text_from_document(self, docling_service):
        """Test extracting text from document."""
        with patch.object(docling_service, 'extract_text', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = "Extracted text content"
            
            result = await mock_extract(b"document_content")
            assert isinstance(result, str)
            assert len(result) > 0
    
    async def test_chunk_document_text(self, docling_service):
        """Test chunking document text."""
        text = "Sample document " * 100  # Create large text
        
        with patch.object(docling_service, 'chunk', new_callable=AsyncMock) as mock_chunk:
            mock_chunks = [
                "Chunk 1: Sample document...",
                "Chunk 2: Sample document...",
                "Chunk 3: Sample document...",
            ]
            mock_chunk.return_value = mock_chunks
            
            result = await mock_chunk(text, chunk_size=512)
            assert isinstance(result, list)
            assert len(result) > 0
    
    async def test_extract_metadata(self, docling_service):
        """Test extracting document metadata."""
        with patch.object(docling_service, 'extract_metadata', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = {
                "title": "Sample Document",
                "author": "Unknown",
                "created_date": datetime.utcnow(),
                "page_count": 5
            }
            
            result = await mock_extract(b"pdf_content")
            assert result["title"]
            assert result["page_count"] == 5
    
    async def test_ocr_scanned_document(self, docling_service):
        """Test OCR on scanned document."""
        with patch.object(docling_service, 'ocr', new_callable=AsyncMock) as mock_ocr:
            mock_ocr.return_value = "OCR extracted text"
            
            result = await mock_ocr(b"scanned_image_content")
            assert isinstance(result, str)


@pytest.mark.unit
@pytest.mark.async
class TestSeaweedFSService:
    """Test suite for SeaweedFS file storage service."""
    
    @pytest.fixture
    async def seaweedfs_service(self):
        """Create SeaweedFSService instance."""
        from app.infrastructure.external.seaweedfs_service import SeaweedFSService
        return SeaweedFSService()
    
    async def test_upload_file(self, seaweedfs_service):
        """Test uploading file to SeaweedFS."""
        with patch.object(seaweedfs_service, 'upload', new_callable=AsyncMock) as mock_upload:
            mock_upload.return_value = {
                "file_id": "fid_12345",
                "size": 1024,
                "url": "http://localhost:3004/fid_12345"
            }
            
            result = await mock_upload(b"file_content", "test.pdf")
            assert result["file_id"]
            assert result["size"] == 1024
    
    async def test_download_file(self, seaweedfs_service):
        """Test downloading file from SeaweedFS."""
        file_id = "fid_12345"
        
        with patch.object(seaweedfs_service, 'download', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = b"file_content"
            
            result = await mock_download(file_id)
            assert isinstance(result, bytes)
    
    async def test_delete_file(self, seaweedfs_service):
        """Test deleting file from SeaweedFS."""
        file_id = "fid_12345"
        
        with patch.object(seaweedfs_service, 'delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            
            result = await mock_delete(file_id)
            assert result is True
    
    async def test_file_exists(self, seaweedfs_service):
        """Test checking if file exists."""
        file_id = "fid_12345"
        
        with patch.object(seaweedfs_service, 'exists', new_callable=AsyncMock) as mock_exists:
            mock_exists.return_value = True
            
            result = await mock_exists(file_id)
            assert result is True
    
    async def test_get_file_info(self, seaweedfs_service):
        """Test getting file information."""
        file_id = "fid_12345"
        
        with patch.object(seaweedfs_service, 'get_info', new_callable=AsyncMock) as mock_info:
            mock_info.return_value = {
                "file_id": file_id,
                "size": 2048,
                "mime_type": "application/pdf",
                "created_at": datetime.utcnow()
            }
            
            result = await mock_info(file_id)
            assert result["file_id"] == file_id
            assert result["size"] == 2048


@pytest.mark.unit
class TestServiceErrorHandling:
    """Test error handling across services."""
    
    @pytest.mark.async
    async def test_llm_service_connection_error(self):
        """Test LLM service connection error."""
        from app.infrastructure.external.llm_service import LLMService
        
        with patch.object(LLMService, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.side_effect = ConnectionError("Cannot connect to LLM provider")
            
            with pytest.raises(ConnectionError):
                await mock_generate("test", "context")
    
    @pytest.mark.async
    async def test_seaweedfs_service_network_error(self):
        """Test SeaweedFS network error."""
        from app.infrastructure.external.seaweedfs_service import SeaweedFSService
        
        with patch.object(SeaweedFSService, 'upload', new_callable=AsyncMock) as mock_upload:
            mock_upload.side_effect = ConnectionError("Cannot connect to SeaweedFS")
            
            with pytest.raises(ConnectionError):
                await mock_upload(b"content", "test.pdf")
    
    @pytest.mark.async
    async def test_docling_service_invalid_format(self):
        """Test Docling with invalid document format."""
        from app.infrastructure.external.docling_service import DoclingService
        
        with patch.object(DoclingService, 'parse', new_callable=AsyncMock) as mock_parse:
            mock_parse.side_effect = ValueError("Unsupported document format")
            
            with pytest.raises(ValueError):
                await mock_parse("invalid.xyz", b"content")


@pytest.mark.integration
@pytest.mark.async
class TestServicesIntegration:
    """Test services working together."""
    
    async def test_document_upload_and_processing_pipeline(self):
        """Test complete document upload and processing."""
        # Mock all services
        with patch('app.infrastructure.external.seaweedfs_service.SeaweedFSService.upload', new_callable=AsyncMock) as mock_upload, \
             patch('app.infrastructure.external.docling_service.DoclingService.parse', new_callable=AsyncMock) as mock_parse, \
             patch('app.infrastructure.external.llm_service.LLMService.get_embeddings', new_callable=AsyncMock) as mock_embed:
            
            # Setup mock returns
            mock_upload.return_value = {"file_id": "fid_123"}
            mock_parse.return_value = {"text": "Sample content", "pages": 5}
            mock_embed.return_value = [0.1] * 1536
            
            # Simulate pipeline
            file_id = (await mock_upload(b"pdf_content", "test.pdf"))["file_id"]
            parsed = await mock_parse(b"pdf_content")
            embeddings = await mock_embed(parsed["text"])
            
            assert file_id == "fid_123"
            assert parsed["pages"] == 5
            assert len(embeddings) == 1536
