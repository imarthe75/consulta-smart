#!/usr/bin/env python3
"""
Script: Validar Knowledge Base (PostgreSQL)
Propósito: Verificar que los documentos RPP Registry estén correctamente indexados
Uso:
    python scripts/validate_kb.py
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class KBValidator:
    """Valida el estado de la knowledge base"""
    
    def __init__(self):
        self.settings = get_settings()
        self.engine = create_engine(str(self.settings.DATABASE_URL))
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_statistics(self) -> dict:
        """Estadísticas de la KB"""
        session = self.SessionLocal()
        try:
            # Total de documentos
            total = session.execute(text("SELECT COUNT(*) as count FROM documents")).scalar()
            
            # Por categoría
            by_category = session.execute(text("""
                SELECT category, COUNT(*) as count 
                FROM documents 
                GROUP BY category 
                ORDER BY count DESC
            """)).fetchall()
            
            # Por filename
            by_file = session.execute(text("""
                SELECT metadata, COUNT(*) as count 
                FROM documents 
                WHERE metadata LIKE 'filename=%'
                GROUP BY metadata 
                ORDER BY count DESC
            """)).fetchall()
            
            return {
                "total": total,
                "by_category": dict(by_category),
                "by_file": dict(by_file)
            }
        finally:
            session.close()
    
    def test_search(self, query: str) -> Optional[str]:
        """Prueba búsqueda de texto"""
        session = self.SessionLocal()
        try:
            result = session.execute(text("""
                SELECT title, SUBSTR(content, 1, 200) as preview
                FROM documents
                WHERE content ILIKE :query
                LIMIT 1
            """), {"query": f"%{query}%"}).fetchone()
            
            return result
        finally:
            session.close()
    
    def list_offices(self) -> list:
        """Lista las oficinas cargadas"""
        session = self.SessionLocal()
        try:
            results = session.execute(text("""
                SELECT DISTINCT title, category
                FROM documents
                WHERE category IN ('oficinas', 'oficinas_contactos_clave')
                LIMIT 20
            """)).fetchall()
            return results
        finally:
            session.close()
    
    def list_categories(self) -> dict:
        """Lista categorías disponibles"""
        session = self.SessionLocal()
        try:
            results = session.execute(text("""
                SELECT DISTINCT category, COUNT(*) as count
                FROM documents
                GROUP BY category
                ORDER BY count DESC
            """)).fetchall()
            return dict(results)
        finally:
            session.close()


async def main():
    logger.info("=" * 70)
    logger.info("📊 VALIDANDO KNOWLEDGE BASE")
    logger.info("=" * 70)
    
    validator = KBValidator()
    
    # Estadísticas
    logger.info("\n[1] ESTADÍSTICAS GENERALES")
    stats = validator.get_statistics()
    
    logger.info(f"   Total documentos: {stats['total']}")
    
    if stats['by_category']:
        logger.info("\n   📂 Por categoría:")
        for cat, count in stats['by_category'].items():
            logger.info(f"      • {cat}: {count}")
    else:
        logger.warning("   ⚠️ NO HAY DOCUMENTOS EN LA KB")
    
    # Categorías
    logger.info("\n[2] CATEGORÍAS DISPONIBLES")
    cats = validator.list_categories()
    if cats:
        for cat, count in cats.items():
            logger.info(f"   • {cat}: {count} docs")
    else:
        logger.warning("   ⚠️ No hay categorías")
    
    # Pruebas de búsqueda
    logger.info("\n[3] PRUEBAS DE BÚSQUEDA")
    
    test_queries = [
        ("Quintana Roo", "Oficinas en QRoo"),
        ("notario", "Notarios"),
        ("Chetumal", "Ciudad específica"),
        ("horario", "Información de horarios"),
        ("requisitos", "Requisitos de actos")
    ]
    
    found = 0
    for query, label in test_queries:
        result = validator.test_search(query)
        if result:
            logger.info(f"   ✅ '{label}': Encontrado")
            logger.info(f"      Título: {result[0]}")
            logger.info(f"      Preview: {result[1][:80]}...")
            found += 1
        else:
            logger.warning(f"   ❌ '{label}': NO encontrado")
    
    # Resultado final
    logger.info("\n" + "=" * 70)
    if stats['total'] > 0:
        logger.info(f"✅ KB OPERACIONAL: {stats['total']} documentos, {found}/{len(test_queries)} búsquedas exitosas")
    else:
        logger.error("❌ KB VACÍA: Ejecutar load_rpp_registry_to_kb.py primero")
    logger.info("=" * 70)
    
    return stats['total'] > 0


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        sys.exit(1)
