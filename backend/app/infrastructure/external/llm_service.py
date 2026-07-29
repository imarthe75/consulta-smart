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

def _with_system(messages: List[dict], system: Optional[str]) -> List[dict]:
    """Antepone el system prompt como mensaje 'system' para clientes OpenAI-compatibles.

    HALLAZGO: GroqProvider/NvidiaNimProvider/_OpenAICompatibleProvider recibían
    `system` vía **kwargs pero nunca lo usaban — el system_prompt (incluyendo los
    guardrails de TEMAS PROHIBIDOS) se perdía silenciosamente en cualquier tema
    configurado con esos proveedores. Gemini/Vertex sí lo aplicaban (usan
    `system_instruction` nativo), por eso el bug no era evidente en todos los temas.
    """
    if not system:
        return messages
    return [{"role": "system", "content": system}, *messages]


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
                messages=_with_system(messages, kwargs.get("system")),
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
                messages=_with_system(messages, kwargs.get("system")),
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


class OllamaProvider(LLMProvider):
    """Ollama Provider (motor local u on-premise, expone API compatible con OpenAI en /v1).

    A diferencia de los demás proveedores, no requiere API key (el "secreto" real es
    la red/host donde vive el servidor Ollama). `base_url` es obligatorio a nivel de
    tema porque cada instalación on-prem vive en una dirección distinta; no hay un
    endpoint público universal como con los proveedores cloud.
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        from openai import AsyncOpenAI
        base_url = (base_url or settings.OLLAMA_BASE_URL or "").rstrip("/")
        if not base_url:
            raise ValueError("OllamaProvider requiere base_url (endpoint del servidor Ollama)")
        if not model:
            raise ValueError("OllamaProvider requiere un modelo explícito (ej. 'llama3.1', 'qwen2.5')")
        if not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"
        # Ollama no valida la API key, pero el SDK de OpenAI exige un valor no vacío
        self.client = AsyncOpenAI(api_key="ollama", base_url=base_url)
        self.chat_model = model
        logger.info(f"✅ OllamaProvider initialized: {base_url} ({self.chat_model})")

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
                messages=_with_system(messages, kwargs.get("system")),
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ Error in Ollama: {e}")
            raise

    async def embed(self, text: str) -> List[float]:
        service = get_local_embedding_service()
        return await service.embed(text)


class MistralProvider(LLMProvider):
    """Mistral AI provider (API compatible con OpenAI)"""

    def __init__(self, api_key: str, base_url: Optional[str] = None, model: Optional[str] = None):
        from openai import AsyncOpenAI
        if not api_key:
            raise ValueError("MistralProvider requiere api_key")
        if not model:
            raise ValueError("MistralProvider requiere un modelo explícito (ej. 'mistral-large-latest')")
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url or settings.MISTRAL_BASE_URL)
        self.chat_model = model
        logger.info(f"✅ MistralProvider initialized: {self.chat_model}")

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
                messages=_with_system(messages, kwargs.get("system")),
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ Error in Mistral: {e}")
            raise

    async def embed(self, text: str) -> List[float]:
        service = get_local_embedding_service()
        return await service.embed(text)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider"""

    def __init__(self, api_key: str, model: Optional[str] = None):
        from anthropic import AsyncAnthropic
        if not api_key:
            raise ValueError("AnthropicProvider requiere api_key")
        if not model:
            raise ValueError("AnthropicProvider requiere un modelo explícito (ej. 'claude-sonnet-4-5')")
        self.client = AsyncAnthropic(api_key=api_key)
        self.chat_model = model
        logger.info(f"✅ AnthropicProvider initialized: {self.chat_model}")

    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        try:
            response = await self.client.messages.create(
                model=self.chat_model,
                system=kwargs.get("system") or "",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return "".join(block.text for block in response.content if block.type == "text")
        except Exception as e:
            logger.error(f"❌ Error in Anthropic: {e}")
            raise

    async def embed(self, text: str) -> List[float]:
        # Anthropic no ofrece endpoint de embeddings propio
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
