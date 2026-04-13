# Docling Document Processing Service

from typing import Optional, List, Tuple
import os
import tempfile
import re

from app.core.logger import logger


class DoclingService:
    """Document parsing with Docling"""
    
    def __init__(self):
        try:
            from docling.document_converter import DocumentConverter
            from docling.document_converter import ConvertorConfig
            
            config = ConvertorConfig(timeout=30)
            self.converter = DocumentConverter(converter_config=config)
            logger.info("Docling service initialized")
        except ImportError:
            logger.warning("Docling not installed. Using basic text fallback if possible.")
            self.converter = None
    
    async def parse_document(self, file_path: str) -> str:
        """Parse document and extract text as markdown"""
        if not self.converter:
            raise ImportError("Docling is not installed on this system.")
        try:
            # Convert document
            result = self.converter.convert(file_path)
            
            # Export as markdown
            markdown_text = result.document.export_to_markdown()
            
            logger.info(f"Document parsed successfully: {file_path}")
            return markdown_text
        except Exception as e:
            logger.error(f"Error parsing document {file_path}: {e}")
            raise
    
    async def extract_text(self, file_path: str) -> str:
        """Extract plain text from document"""
        if not self.converter:
            # Fallback for plain text files
            if file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            raise ImportError("Docling is required for non-text formats.")
        
        try:
            result = self.converter.convert(file_path)
            text = result.document.export_to_text()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise


class TextProcessingService:
    """Service for cleaning and chunking text"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean extra whitespace and normalize text"""
        if not text:
            return ""
        # Remove multiple newlines and spaces
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()

    @staticmethod
    def extract_chunks(
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[Tuple[int, str]]:
        """Split text into chunks with overlap"""
        if not text:
            return []
            
        chunks = []
        # Basic chunking by character count with word awareness
        start = 0
        chunk_num = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # If not at the end of text, find the last space to avoid cutting words
            if end < len(text):
                last_space = text.rfind(' ', start, end)
                if last_space != -1:
                    end = last_space
            
            chunk_content = text[start:end].strip()
            if chunk_content:
                chunks.append((chunk_num, chunk_content))
                chunk_num += 1
            
            # Move start back for overlap
            start = end - overlap
            if start < 0: start = 0
            
            # Prevent infinite loop
            if end >= len(text):
                break
            if end <= start:
                start = end + 1
            
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks

    @staticmethod
    def count_tokens(text: str) -> int:
        """Estimate token count (approx ~4 chars per token)"""
        return len(text) // 4
