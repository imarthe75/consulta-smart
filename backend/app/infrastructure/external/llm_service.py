# LLM Service - Multi-provider support (Groq, Gemini, OpenAI, Claude)

from typing import Optional, List
from abc import ABC, abstractmethod
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


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
    """Groq LLM provider"""
    
    def __init__(self, api_key: str = settings.GROQ_API_KEY):
        from groq import Groq as GroqClient
        self.client = GroqClient(api_key=api_key)
        self.chat_model = settings.GROQ_MODEL
        # Usar OpenRouter para embeddings (compatible con OpenAI SDK)
        logger.info(f"DEBUG: OPENAI_API_KEY={bool(settings.OPENAI_API_KEY)}, OPENAI_BASE_URL={settings.OPENAI_BASE_URL}")
        if settings.OPENAI_API_KEY and settings.OPENAI_BASE_URL:
            self.embedding_model = "openai/text-embedding-3-small"
            import openai
            logger.info(f"DEBUG: Initializing OpenAI client with base_url={settings.OPENAI_BASE_URL}")
            self.openai_client = openai.OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )
            self.use_openai_embeddings = True
            logger.info(f"✅ GroqProvider initialized with OpenRouter embeddings")
        elif settings.OPENAI_API_KEY:
            # Fallback a OpenAI directo si no hay OPENAI_BASE_URL
            self.embedding_model = "text-embedding-3-small"
            import openai
            self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            self.use_openai_embeddings = True
            logger.info(f"⚠️ GroqProvider initialized with OpenAI embeddings (no base_url)")
        else:
            # Fallback: usar un modelo local o placeholder
            self.embedding_model = "placeholder"
            self.openai_client = None
            self.use_openai_embeddings = False
            logger.warning("❌ GroqProvider: No embedding API configured, using placeholder")
    
    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        """Chat with Groq with automatic model fallback for 429 errors"""
        models_to_try = [self.chat_model, "llama-3.1-8b-instant", "llama3-8b-8192"]
        last_exception = None
        
        for model in models_to_try:
            try:
                logger.info(f"📤 Calling Groq with model {model}")
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=settings.TOP_P
                )
                return response.choices[0].message.content
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()
                if "rate limit" in error_str or "429" in error_str:
                    logger.warning(f"⚠️ Groq model {model} rate limited, trying next model...")
                    continue
                else:
                    break
        
        logger.error(f"Error calling Groq chat: {last_exception}")
        raise last_exception

    async def embed(self, text: str) -> List[float]:
        """Generate embedding LOCALLY using Sentence Transformers (384-dim, free)"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Use same model as document embeddings for consistency
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = model.encode(text, convert_to_tensor=False)
            
            logger.info(f"✅ Embedding generated locally: {len(embedding)} dimensions (Sentence Transformers)")
            return embedding.tolist()
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            raise


class GeminiProvider(LLMProvider):
    """Google Gemini provider"""
    
    def __init__(self, api_key: str = settings.GOOGLE_API_KEY):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        """Chat with Gemini using native system instructions"""
        try:
            # Get system prompt if provided
            system_prompt = kwargs.get('system', '')
            
            # Use specific model with system prompt if provided
            model = self.model
            if system_prompt:
                import google.generativeai as genai
                model = genai.GenerativeModel(
                    model_name=settings.GEMINI_MODEL,
                    system_instruction=system_prompt
                )
            
            # Convert OpenAI format to Gemini format
            contents = []
            for msg in messages:
                contents.append({
                    "role": "user" if msg["role"] == "user" else "model",
                    "parts": [msg["content"]]
                })
            
            response = await model.generate_content_async(
                contents,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens
                }
            )
            
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini chat: {e}")
            raise
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding LOCALLY (same as Groq, for consistency)"""
        try:
            from sentence_transformers import SentenceTransformer
            
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = model.encode(text, convert_to_tensor=False)
            
            logger.info(f"✅ Embedding generated locally: {len(embedding)} dimensions")
            return embedding.tolist()
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            raise


class VertexAIProvider(LLMProvider):
    """Google Cloud Vertex AI provider"""
    
    def __init__(
        self, 
        project_id: str = settings.GCP_PROJECT_ID,
        location: str = settings.GCP_LOCATION
    ):
        import vertexai
        import os
        from vertexai.generative_models import GenerativeModel
        
        # Usar credenciales explícitas si están configuradas
        if settings.GCP_CREDENTIALS_JSON and os.path.exists(settings.GCP_CREDENTIALS_JSON):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GCP_CREDENTIALS_JSON
            logger.info(f"🔑 Using Vertex AI credentials from: {settings.GCP_CREDENTIALS_JSON}")
        
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel(settings.VERTEX_MODEL)
    
    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """Chat with Vertex AI using native system instructions"""
        try:
            # Get system prompt if provided
            system_prompt = kwargs.get('system', '')
            
            # Use specific model with system prompt if provided
            model = self.model
            if system_prompt:
                from vertexai.generative_models import GenerativeModel
                model = GenerativeModel(
                    model_name=settings.VERTEX_MODEL,
                    system_instruction=system_prompt
                )
            
            # Convert OpenAI format to Vertex format
            # Note: Vertex AI expect Content objects or similar
            from vertexai.generative_models import Content, Part
            
            contents = []
            for msg in messages:
                contents.append(Content(
                    role="user" if msg["role"] == "user" else "model",
                    parts=[Part.from_text(msg["content"])]
                ))
            
            response = await model.generate_content_async(
                contents,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens
                }
            )
            
            return response.text
        except Exception as e:
            logger.error(f"Error calling Vertex AI chat: {e}")
            raise

    async def embed(self, text: str) -> List[float]:
        """Generate embedding LOCALLY (consistency)"""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            raise


class LLMService:
    """LLM Service - Factory for providers"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self, provider: str = settings.LLM_PROVIDER):
        self.provider_name = provider
        
        if provider == "groq":
            self.provider = GroqProvider()
        elif provider == "gemini":
            self.provider = GeminiProvider()
        elif provider == "vertex":
            self.provider = VertexAIProvider()
        # Add more providers as needed
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
        
        logger.info(f"LLM Service initialized with provider: {provider}")
    
    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        """Send chat request"""
        return await self.provider.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding"""
        return await self.provider.embed(text)


def get_llm_provider() -> LLMService:
    """Factory function to get singleton LLM service instance"""
    return LLMService.get_instance()
