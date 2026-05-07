# LLM Service - Multi-provider support (Groq, Gemini, Vertex AI)

from typing import Optional, List
from abc import ABC, abstractmethod
import json
import logging
import asyncio

from app.core.config import settings
from app.core.logger import logger
from app.infrastructure.external.local_embedding_service import LocalEmbeddingService

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    logger.error("❌ google-genai library NOT FOUND at runtime!")

# Singleton for local embeddings
_local_embedding_service = None

def get_local_embedding_service():
    global _local_embedding_service
    if _local_embedding_service is None:
        _local_embedding_service = LocalEmbeddingService()
    return _local_embedding_service

class LLMProvider(ABC):
    """Abstract base for LLM providers"""
    
    @abstractmethod
    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        """Send chat request to LLM"""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for text"""
        pass


class GroqProvider(LLMProvider):
    """Groq LLM provider (Fast fallback)"""
    
    def __init__(self, api_key: str = settings.GROQ_API_KEY):
        from groq import AsyncGroq
        self.client = AsyncGroq(api_key=api_key)
        self.chat_model = settings.GROQ_MODEL
        logger.info(f"✅ GroqProvider initialized (Modern Async)")

    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ Error in Groq: {e}")
            raise

    async def embed(self, text: str) -> List[float]:
        service = get_local_embedding_service()
        return await service.embed(text)


class GeminiProvider(LLMProvider):
    """Google Gemini provider (Modern Unified SDK)"""
    
    def __init__(self, api_key: str = settings.GOOGLE_API_KEY):
        if not HAS_GENAI:
            raise ImportError("Google GenAI SDK is missing or could not be loaded")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY must be provided")
            
        # Initialize the modern Unified Client
        self.client = genai.Client(api_key=api_key)
        self.model_name = settings.GEMINI_MODEL
        logger.info(f"✅ GeminiProvider initialized (Unified SDK): {self.model_name}")
    
    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        import asyncio
        import random
        from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
        
        # Prepare contents
        contents = []
        for msg in messages:
            contents.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [{"text": msg["content"]}]
            })
        
        system_instruction = kwargs.get("system", None)

        @retry(
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(Exception), # We will filter inside or outside
            before_sleep=lambda retry_state: logger.warning(f"⚠️ Gemini saturated. Retrying ({retry_state.attempt_number}/5)...")
        )
        def _sync_chat_with_retry():
            try:
                return self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                        "system_instruction": system_instruction
                    }
                )
            except Exception as e:
                err_text = str(e).lower()
                if "503" in err_text or "429" in err_text or "resource_exhausted" in err_text or "unavailable" in err_text:
                    raise # Trigger tenacity retry
                raise e # Fatal error, don't retry

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(_sync_chat_with_retry),
                timeout=30.0
            )
            return response.text
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Gemini API TIMEOUT (30s)")
            raise Exception("Timeout in Gemini API")
        except Exception as e:
            logger.error(f"❌ Gemini API Final Failure after retries: {e}")
            raise

    async def embed(self, text: str) -> List[float]:
        service = get_local_embedding_service()
        return await service.embed(text)


class VertexAIProvider(LLMProvider):
    """Vertex AI Provider (Enterprise Fallback using Unified SDK)"""
    
    def __init__(self, project_id: Optional[str] = None, location: Optional[str] = None):
        project_id = project_id or settings.GCP_PROJECT_ID
        location = location or settings.GCP_LOCATION
        if not project_id:
            raise ValueError("GCP_PROJECT_ID must be configured for Vertex AI")

        try:
            from google import genai
            # Use Unified Client for Vertex too
            self.client = genai.Client(vertexai=True, project=project_id, location=location)
            self.model_name = settings.VERTEX_MODEL or settings.GEMINI_MODEL
            logger.info(f"✅ Vertex AI initialized via Unified SDK: {self.model_name}")
        except Exception as e:
            logger.warning(f"⚠️ Vertex AI initialization failed: {e}")
            self.client = None
            self.model_name = settings.VERTEX_MODEL or settings.GEMINI_MODEL

    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        if not self.client:
            raise Exception("Vertex AI not available")
            
        # Prepare contents (Conversational History)
        contents = []
        for msg in messages:
            contents.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [{"text": msg["content"]}]
            })
        
        system_instruction = kwargs.get("system", None)

        try:
            # Use Async Unified Client for Vertex with explicit timeout
            # and safety settings to avoid blocked responses causing delays
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                        "system_instruction": system_instruction
                    }
                ),
                timeout=30.0 # Timeout de 30 segundos para evitar colapsos
            )
            return response.text
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Vertex AI TIMEOUT (30s) for model {self.model_name}")
            raise Exception("Timeout in Vertex AI")
        except Exception as e:
            logger.error(f"❌ Vertex AI API Failure: {e}")
            raise

    async def embed(self, text: str) -> List[float]:
        service = get_local_embedding_service()
        return await service.embed(text)


class NvidiaNimProvider(LLMProvider):
    """NVIDIA NIM provider (OpenAI compatible)"""
    
    def __init__(self, api_key: str = settings.NVIDIA_NIM_API_KEY):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=settings.NVIDIA_NIM_BASE_URL
        )
        self.chat_model = settings.NVIDIA_NIM_MODEL
        logger.info(f"✅ NvidiaNimProvider initialized: {self.chat_model}")

    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ Error in NVIDIA NIM: {e}")
            raise

    async def embed(self, text: str) -> List[float]:
        # NIM doesn't provide embeddings in the same way or we prefer local for speed/cost
        service = get_local_embedding_service()
        return await service.embed(text)


class LLMService:
    """Main LLM service orchestrator"""
    
    def __init__(self):
        from app.infrastructure.external.smart_llm_router import SmartLLMRouter
        self.router = SmartLLMRouter()
        logger.info("✅ LLMService (Orchestrator) initialized")

    async def chat(self, messages: List[dict], **kwargs) -> str:
        """Delegate chat to router"""
        return await self.router.chat(messages, **kwargs)

    async def embed(self, text: str) -> List[float]:
        """Delegate embedding to router or local service"""
        service = get_local_embedding_service()
        return await service.embed(text)

def get_llm_provider(name: str = "gemini") -> LLMProvider:
    """Factory for LLM providers"""
    if name == "groq":
        return GroqProvider()
    elif name == "vertex":
        return VertexAIProvider()
    elif name == "nvidia":
        return NvidiaNimProvider()
    else:
        return GeminiProvider()

def get_llm_service() -> LLMService:
    """Singleton for LLMService"""
    return LLMService()
