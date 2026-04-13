#!/usr/bin/env python3
"""
Script: Generar Embeddings Locales - Versión Simplificada
Usa conexión PostgreSQL directa (psycopg2) para evitar problemas con SQLAlchemy
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import execute_batch

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 32


class SimpleEmbeddingGenerator:
    """Genera embeddings usando psycopg2 directo (sin SQLAlchemy)"""
    
    def __init__(self, db_url: str):
        logger.info(f"🤖 Cargando modelo: {MODEL_NAME}")
        self.model = SentenceTransformer(MODEL_NAME)
        logger.info(f"✓ Modelo cargado (dimensiones: {self.model.get_sentence_embedding_dimension()})")
        
        # Parsear URL de conexión
        self.db_url = db_url
        self.conn = None
    
    def connect(self):
        """Conectar a PostgreSQL"""
        try:
            # URL format: postgresql://user:password@localhost:5432/dbname
            self.conn = psycopg2.connect(self.db_url)
            logger.info("✓ Conectado a PostgreSQL")
        except Exception as e:
            logger.error(f"Error conectando: {e}")
            raise
    
    def get_chunks_without_embeddings(self, limit: int = None, document_id: str = None) -> List[Tuple]:
        """Obtiene chunks sin embeddings"""
        cursor = self.conn.cursor()
        
        query = "SELECT id, text FROM document_chunks WHERE embedding IS NULL"
        params = []
        
        if document_id:
            query += " AND document_id = %s"
            params.append(document_id)
        
        query += " ORDER BY created_at ASC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, params if params else ())
        result = cursor.fetchall()
        cursor.close()
        
        return result
    
    def generate_embeddings(self, texts: List[str]) -> List:
        """Genera embeddings para textos"""
        logger.info(f"   🔄 Generando embeddings para {len(texts)} chunks...")
        embeddings = self.model.encode(texts, show_progress_bar=False, batch_size=BATCH_SIZE)
        logger.info(f"   ✓ {len(embeddings)} embeddings generados")
        return embeddings
    
    def save_embeddings_batch(self, chunks_with_embeddings: List) -> int:
        """Guarda embeddings en batch usando COPY o INSERT"""
        cursor = self.conn.cursor()
        updated = 0
        
        try:
            # Preparar datos: (id, embedding_array)
            data = []
            for chunk_id, embedding in chunks_with_embeddings:
                # Convertir embedding a formato pgvector - Sin padding, solo 384 dimensiones
                emb_list = embedding.tolist()
                emb_str = "[" + ",".join(map(str, emb_list)) + "]"
                data.append((chunk_id, emb_str))
            
            # Ejecutar en batch - Cast explícito a vector(384)
            query = """
                UPDATE document_chunks 
                SET embedding = %s::vector(384)
                WHERE id = %s
            """
            
            # Invertir parámetros para que coincidan con el query
            params = [(emb, cid) for cid, emb in data]
            execute_batch(cursor, query, params, page_size=100)
            
            self.conn.commit()
            updated = len(data)
            logger.info(f"   ✅ {updated} embeddings guardados")
        
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            self.conn.rollback()
        
        finally:
            cursor.close()
        
        return updated
    
    def run(self, limit: int = None, document_id: str = None) -> bool:
        """Ejecutar generación de embeddings"""
        logger.info("=" * 80)
        logger.info("🚀 GENERANDO EMBEDDINGS LOCALES (SENTENCE-TRANSFORMERS)")
        logger.info("=" * 80)
        
        try:
            self.connect()
            
            # Obtener chunks
            logger.info("\n[STEP 1] Buscando chunks sin embeddings...")
            chunks = self.get_chunks_without_embeddings(limit=limit, document_id=document_id)
            
            if not chunks:
                logger.warning("⚠️  No hay chunks pendientes")
                return False
            
            logger.info(f"   Encontrados: {len(chunks)} chunks\n")
            
            # Procesar por batches
            logger.info("[STEP 2] Generando embeddings por batches...\n")
            
            total_processed = 0
            batch_size = 128
            
            for batch_idx in range(0, len(chunks), batch_size):
                batch_end = min(batch_idx + batch_size, len(chunks))
                batch_chunks = chunks[batch_idx:batch_end]
                
                logger.info(f"   Batch {batch_idx // batch_size + 1}/{(len(chunks) + batch_size - 1) // batch_size}")
                logger.info(f"   Procesando chunks {batch_idx + 1}-{batch_end} de {len(chunks)}")
                
                try:
                    # Extraer textos
                    texts = [ch[1] for ch in batch_chunks]
                    chunk_ids = [ch[0] for ch in batch_chunks]
                    
                    # Generar embeddings
                    embeddings = self.generate_embeddings(texts)
                    
                    # Guardar
                    chunks_with_emb = list(zip(chunk_ids, embeddings))
                    updated = self.save_embeddings_batch(chunks_with_emb)
                    total_processed += updated
                
                except Exception as e:
                    logger.error(f"   ❌ Error en batch: {e}")
                    continue
            
            # Estadísticas finales
            logger.info("\n" + "=" * 80)
            logger.info(f"✅ COMPLETADO: {total_processed} embeddings generados")
            logger.info("=" * 80)
            
            # Stats
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL")
            with_emb = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM document_chunks")
            total = cursor.fetchone()[0]
            cursor.close()
            
            logger.info(f"\n📊 Estadísticas:")
            logger.info(f"   • Chunks con embedding: {with_emb}/{total}")
            logger.info(f"   • Cobertura: {(with_emb/total*100):.1f}%")
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Error: {e}", exc_info=True)
            return False
        
        finally:
            if self.conn:
                self.conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Generar embeddings locales (versión simplificada psycopg2)"
    )
    parser.add_argument(
        "--document-id",
        help="UUID del documento",
        type=str
    )
    parser.add_argument(
        "--limit",
        help="Límite máximo de chunks",
        type=int
    )
    
    args = parser.parse_args()
    
    # Obtener URL base de la configuración
    db_host = os.getenv("DB_HOST", "postgres")
    db_port = os.getenv("DB_PORT", "5432")
    db_user = os.getenv("DB_USER", "consultarpp_user")
    db_password = os.getenv("DB_PASSWORD", "***DB_PASSWORD_REDACTED***")
    db_name = os.getenv("DB_NAME", "consultarpp")
    
    # Construir URL
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    generator = SimpleEmbeddingGenerator(db_url)
    
    try:
        result = generator.run(
            limit=args.limit,
            document_id=args.document_id
        )
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
