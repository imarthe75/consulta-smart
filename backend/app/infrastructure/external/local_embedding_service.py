"""
Servicio LocalEmbedding: Genera embeddings con Sentence Transformers
Usado cuando LLM API no está disponible o sin créditos
Optimizado con carga diferida (Lazy Loading) para evitar bloqueos en el arranque
"""

from typing import List, Optional
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class LocalEmbeddingService:
    """Genera embeddings locales sin APIs usando sentence-transformers"""
    
    # Modelo pequeño, rápido, 384 dimensiones
    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        """Inicialización ligera: no carga el modelo todavía"""
        self.model_name = model_name
        self._model = None
        self._dimension = None
        self._lock = asyncio.Lock()
        logger.info(f"⏳ LocalEmbeddingService preparado para carga diferida: {model_name}")

    async def _get_model(self):
        """Carga el modelo solo cuando es necesario (Thread-safe)"""
        async with self._lock:
            if self._model is None:
                from sentence_transformers import SentenceTransformer
                logger.info(f"🚀 Cargando modelo de embeddings en segundo plano: {self.model_name}...")
                
                # Ejecutar en hilo separado para no bloquear el loop de eventos
                loop = asyncio.get_running_loop()
                self._model = await loop.run_in_executor(
                    None, 
                    lambda: SentenceTransformer(self.model_name)
                )
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info(f"✅ Modelo de embeddings listo (Dim: {self._dimension})")
        return self._model

    async def embed(self, text: str) -> List[float]:
        """Genera embedding para un texto"""
        if not text or not isinstance(text, str):
            raise ValueError("Texto inválido")
        
        try:
            model = await self._get_model()
            # Delegar cálculo pesado a un hilo separado
            loop = asyncio.get_running_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: model.encode(text.strip(), convert_to_tensor=False)
            )
            
            if hasattr(embedding, 'tolist'):
                return embedding.tolist()
            return list(embedding)
        
        except Exception as e:
            logger.error(f"❌ Error generando embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Genera embeddings para múltiples textos"""
        if not texts:
            return []
        
        try:
            model = await self._get_model()
            loop = asyncio.get_running_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: model.encode(texts, batch_size=batch_size, show_progress_bar=False, convert_to_tensor=False)
            )
            
            return [emb.tolist() if hasattr(emb, 'tolist') else list(emb) for emb in embeddings]
        
        except Exception as e:
            logger.error(f"❌ Error generando embeddings en batch: {e}")
            raise
