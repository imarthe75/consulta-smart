"""
Servicio LocalEmbedding: Genera embeddings con Sentence Transformers
Usado cuando LLM API no está disponible o sin créditos
"""

from typing import List, Optional
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class LocalEmbeddingService:
    """Genera embeddings locales sin APIs usando sentence-transformers"""
    
    # Modelo pequeño, rápido, 384 dimensiones
    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        """Inicializa con modelo"""
        try:
            logger.info(f"Cargando modelo de embeddings: {model_name}")
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"✓ Modelo listo. Dimensiones: {self.dimension}")
        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {e}")
            raise
    
    async def embed(self, text: str) -> List[float]:
        """
        Genera embedding para un texto
        Retorna: Lista de floats (384 dimensiones)
        """
        if not text or not isinstance(text, str):
            raise ValueError("Texto inválido")
        
        try:
            # Generar embedding
            embedding = self.model.encode(text.strip(), convert_to_tensor=False)
            
            # Convertir a lista
            return embedding.tolist()
        
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Genera embeddings para múltiples textos
        Retorna: Lista de embeddings
        """
        if not texts:
            return []
        
        try:
            # Generar embeddings en batch
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_tensor=False
            )
            
            # Convertir a lista de listas
            return [emb.tolist() for emb in embeddings]
        
        except Exception as e:
            logger.error(f"Error generando embeddings en batch: {e}")
            raise
    
    async def similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similitud entre dos textos (0-1)
        """
        try:
            from sentence_transformers.util import pytorch_cos_sim
            
            emb1 = self.model.encode(text1, convert_to_tensor=True)
            emb2 = self.model.encode(text2, convert_to_tensor=True)
            
            similarity = pytorch_cos_sim(emb1, emb2)[0][0].item()
            return float(similarity)
        
        except Exception as e:
            logger.error(f"Error calculando similitud: {e}")
            raise
