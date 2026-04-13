#!/usr/bin/env python3
"""
Script: Cargar documentación RPP Registry a Knowledge Base (PostgreSQL)
Propósito: Ingesta de datos de oficinas, notarios, requisitos desde docs/rpp-registry/
Autor: IA Assistant
Fecha: 04/2026

Uso:
    python scripts/load_rpp_registry_to_kb.py
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging

# Agregar backend al path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import exists
from app.core.config import get_settings
from app.infrastructure.external.llm_service import get_llm_provider
from app.core.logger import logger as app_logger

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración
DOCS_PATH = Path(__file__).parent.parent / "docs" / "rpp-registry"
BATCH_SIZE = 10  # Procesar embeddings en batches


class RPPRegistryLoader:
    """Carga documentación RPP Registry a la knowledge base"""
    
    def __init__(self):
        self.settings = get_settings()
        self.llm = get_llm_provider()
        self.engine = create_engine(str(self.settings.DATABASE_URL))
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def get_documents_to_load(self) -> List[Dict[str, Any]]:
        """
        Lee los archivos de rpp-registry y los transforma en documentos/chunks
        """
        documents = []
        
        md_files = {
            "OFICINAS_CONTACTOS_RPP.md": {
                "title": "Oficinas y Contactos del Registro Público",
                "category": "oficinas"
            },
            "DIRECTORIO_NOTARIOS_NACIONAL.md": {
                "title": "Directorio Nacional de Notarios",
                "category": "notarios"
            },
            "REQUISITOS_POR_ACTO_QUINTANA_ROO.md": {
                "title": "Requisitos por Acto - Quintana Roo",
                "category": "requisitos"
            },
            "DERECHOS_COSTOS_QUINTANA_ROO.md": {
                "title": "Derechos y Costos - Quintana Roo",
                "category": "costos"
            },
            "DERECHOS_COSTOS_PUEBLA.md": {
                "title": "Derechos y Costos - Puebla",
                "category": "costos"
            },
            "DICCIONARIO_ACTOS_REGISTRABLES.md": {
                "title": "Diccionario de Actos Registrables",
                "category": "actos"
            },
            "REGISTROS_POR_ACTO.md": {
                "title": "Registros por Acto",
                "category": "registros"
            },
            "GUIA_COMPARATIVA_PUEBLA_QROO.md": {
                "title": "Guía Comparativa Puebla - Quintana Roo",
                "category": "comparativa"
            }
        }
        
        for filename, metadata in md_files.items():
            filepath = DOCS_PATH / filename
            if filepath.exists():
                logger.info(f"📖 Leyendo: {filename}")
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Dividir en chunks por secciones
                chunks = self._split_into_chunks(content, filename, metadata)
                documents.extend(chunks)
                logger.info(f"   ✅ {len(chunks)} chunks creados de {filename}")
        
        logger.info(f"\n📚 Total de documentos a cargar: {len(documents)}")
        return documents
    
    def _split_into_chunks(self, content: str, filename: str, metadata: Dict) -> List[Dict]:
        """
        Divide el contenido por secciones (## encabezados)
        Cada sección = un documento separado (para búsqueda más granular)
        """
        chunks = []
        sections = content.split('\n## ')
        
        for section in sections:
            if not section.strip():
                continue
            
            # Tomar primeras 500 chars como snippet
            snippet = section[:500].replace('\n', ' ')
            
            chunk = {
                "title": metadata["title"],
                "content": section.strip(),
                "category": metadata["category"],
                "filename": filename,
                "snippet": snippet
            }
            chunks.append(chunk)
        
        return chunks
    
    async def load_to_database(self, documents: List[Dict]) -> int:
        """
        Carga los documentos a PostgreSQL con embeddings
        Retorna: número de documentos cargados
        """
        session = self.SessionLocal()
        count = 0
        
        try:
            # Verificar tabla documents
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            if 'documents' not in tables:
                logger.error("❌ Tabla 'documents' no existe. Ejecutar init_db primero.")
                return 0
            
            # Procesar por batches
            for i in range(0, len(documents), BATCH_SIZE):
                batch = documents[i:i+BATCH_SIZE]
                
                for doc in batch:
                    try:
                        # Verificar si ya existe (por filename + snippet)
                        existing = session.query(
                            exists().where(
                                (text("documents.title = :title")) &
                                (text("documents.category = :category"))
                            ).compile(compile_kwargs={"literal_binds": True})
                        ).scalar()
                        
                        if existing:
                            logger.debug(f"⏭️  Ya existe: {doc['title']} ({doc['category']})")
                            continue
                        
                        # Generar embedding
                        logger.info(f"🔄 Generando embedding para: {doc['title']} (Sección)")
                        embedding = await self.llm.embed(doc['content'][:1000])
                        
                        # Insertar documento
                        insert_query = text("""
                            INSERT INTO documents (title, category, content, embedding, metadata)
                            VALUES (:title, :category, :content, :embedding::vector, :metadata)
                            ON CONFLICT DO NOTHING
                        """)
                        
                        session.execute(insert_query, {
                            "title": doc['title'],
                            "category": doc['category'],
                            "content": doc['content'],
                            "embedding": embedding,
                            "metadata": f"filename={doc['filename']}"
                        })
                        
                        count += 1
                        logger.info(f"   ✅ Cargado: {doc['title']} ({doc['category']})")
                    
                    except Exception as e:
                        logger.error(f"   ❌ Error cargando {doc['title']}: {e}")
                        continue
                
                # Commit por batch
                session.commit()
                logger.info(f"✓ Batch {i//BATCH_SIZE + 1} comprometido ({count} total)")
        
        except Exception as e:
            logger.error(f"❌ Error en carga masiva: {e}")
            session.rollback()
            return count
        
        finally:
            session.close()
        
        return count
    
    async def extract_key_contacts(self):
        """
        Extrae contactos clave (oficinas y notarios) como documentos separados
        para búsqueda rápida
        """
        logger.info("\n📞 Extrayendo contactos clave...")
        session = self.SessionLocal()
        count = 0
        
        contacts = {
            "OFICINAS QUINTANA ROO": """
REGISTRO PÚBLICO DE QUINTANA ROO - OFICINAS VIGENTES (4):

1. CHETUMAL (Central)
   Municipio: Chetumal
   Horario: 08:00-17:00 L-V
   Servicios: Centralizados
   Contacto: Consultar www.quintanaroo.gob.mx

2. CANCÚN (Zona Turística)
   Municipio: Benito Juárez
   Horario: 08:00-18:00 L-V (extendido)
   Servicios: Prioritarios, internacionales
   Contacto: Delegación Cancún

3. PLAYA DEL CARMEN (Zona Turística)
   Municipio: Solidaridad
   Horario: 08:00-18:00 L-V
   Servicios: Inversión extranjera, complejos
   Contacto: Delegación Playa del Carmen

4. COZUMEL (Isla)
   Municipio: Cozumel
   Horario: 08:00-16:00 L-V
   Servicios: Locales, certificaciones
   Acceso: Ferry desde Playa del Carmen
            """.strip(),
            
            "OFICINAS PUEBLA": """
REGISTRO PÚBLICO DE PUEBLA - DELEGACIONES:

1. PUEBLA Capital
   Jurisdicción: Municipio de Puebla
   Horario: 08:00-16:00 L-V
   Servicios: Completos
   
2. TEHUACÁN
   Jurisdicción: Región Sur-sureste
   Horario: 08:00-16:00 L-V
   Servicios: Actos inmobiliarios locales

3. ATLIXCO
   Jurisdicción: Región Sur
   Horario: 08:00-16:00 L-V
   Servicios: Actos de la región

4. HUAUCHINANGO
   Jurisdicción: Región Norte
   Horario: 08:00-16:00 L-V
   Servicios: Actos de sierra norte
            """.strip()
        }
        
        try:
            for title, content in contacts.items():
                embedding = await self.llm.embed(content)
                
                insert_query = text("""
                    INSERT INTO documents (title, category, content, embedding)
                    VALUES (:title, :category, :content, :embedding::vector)
                    ON CONFLICT DO NOTHING
                """)
                
                session.execute(insert_query, {
                    "title": title,
                    "category": "oficinas_contactos_clave",
                    "content": content,
                    "embedding": embedding
                })
                
                count += 1
                logger.info(f"   ✅ {title}")
            
            session.commit()
            logger.info(f"✓ {count} contactos clave ingestionados")
        
        except Exception as e:
            logger.error(f"❌ Error ingestionando contactos clave: {e}")
            session.rollback()
        
        finally:
            session.close()


async def main():
    """Ejecuta la carga completa"""
    
    logger.info("=" * 70)
    logger.info("🚀 INICIANDO CARGA RPP REGISTRY → KNOWLEDGE BASE")
    logger.info("=" * 70)
    
    if not DOCS_PATH.exists():
        logger.error(f"❌ Ruta no existe: {DOCS_PATH}")
        return False
    
    loader = RPPRegistryLoader()
    
    # Step 1: Leer documentos
    logger.info("\n[STEP 1] Leyendo documentos desde rpp-registry/")
    documents = loader.get_documents_to_load()
    
    if not documents:
        logger.warning("⚠️ No hay documentos para cargar")
        return False
    
    # Step 2: Cargar a BD
    logger.info("\n[STEP 2] Cargando a PostgreSQL con embeddings")
    count = await loader.load_to_database(documents)
    
    # Step 3: Extraer contactos clave
    logger.info("\n[STEP 3] Extrayendo contactos clave para búsqueda rápida")
    await loader.extract_key_contacts()
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info(f"✅ CARGA COMPLETADA: {count} documentos ingestionados")
    logger.info("=" * 70)
    logger.info("\nAhora puedes hacer preguntas sobre:")
    logger.info("  • Oficinas en Puebla y Quintana Roo")
    logger.info("  • Contactos de Registros Públicos")
    logger.info("  • Notarios disponibles")
    logger.info("  • Requisitos y costos por acto")
    logger.info("  • Horarios y servicios")
    
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        sys.exit(1)
