#!/usr/bin/env python3
"""
Script: Validar Knowledge Base (PostgreSQL)
Propósito: Verificar que los documentos RPP Registry estén correctamente indexados
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def validate():
    logger.info("=" * 70)
    logger.info("📊 VALIDANDO KNOWLEDGE BASE (ASYNC)")
    logger.info("=" * 70)
    
    engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Estadísticas Generales
            logger.info("\n[1] ESTADÍSTICAS GENERALES")
            
            doc_count_res = await session.execute(text("SELECT COUNT(*) FROM documents"))
            total_docs = doc_count_res.scalar()
            
            chunk_count_res = await session.execute(text("SELECT COUNT(*) FROM document_chunks"))
            total_chunks = chunk_count_res.scalar()
            
            logger.info(f"   Total documentos: {total_docs}")
            logger.info(f"   Total chunks: {total_chunks}")
            
            if total_docs > 0:
                cat_res = await session.execute(text("""
                    SELECT category, COUNT(*) as count 
                    FROM documents 
                    GROUP BY category 
                    ORDER BY count DESC
                """))
                logger.info("\n   📂 Por categoría:")
                for row in cat_res:
                    logger.info(f"      • {row[0]}: {row[1]}")
            else:
                logger.warning("   ⚠️ NO HAY DOCUMENTOS EN LA KB")
            
            # 2. Pruebas de Búsqueda
            logger.info("\n[2] PRUEBAS DE BÚSQUEDA")
            
            test_queries = [
                ("Quintana Roo", "Oficinas en QRoo"),
                ("notario", "Notarios"),
                ("FRE", "Folio Real Electrónico"),
                ("QR", "Código QR"),
                ("requisitos", "Requisitos de actos")
            ]
            
            found = 0
            for query, label in test_queries:
                search_res = await session.execute(text("""
                    SELECT d.title, SUBSTR(c.text, 1, 200) as preview
                    FROM document_chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE c.text ILIKE :query
                    LIMIT 1
                """), {"query": f"%{query}%"})
                result = search_res.fetchone()
                
                if result:
                    logger.info(f"   ✅ '{label}': Encontrado")
                    logger.info(f"      Título: {result[0]}")
                    logger.info(f"      Preview: {result[1][:80]}...")
                    found += 1
                else:
                    logger.warning(f"   ❌ '{label}': NO encontrado")
            
            # Resultado final
            logger.info("\n" + "=" * 70)
            if total_docs > 0:
                logger.info(f"✅ KB OPERACIONAL: {total_docs} documentos, {found}/{len(test_queries)} búsquedas exitosas")
            else:
                logger.error("❌ KB VACÍA")
            logger.info("=" * 70)
            
            return total_docs > 0
            
        except Exception as e:
            logger.error(f"❌ Error en validación: {e}")
            return False
        finally:
            await session.close()

if __name__ == "__main__":
    result = asyncio.run(validate())
    sys.exit(0 if result else 1)
