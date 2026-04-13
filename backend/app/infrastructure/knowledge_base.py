# Knowledge Base Service - Búsqueda RAG en PostgreSQL + pgvector

from typing import List, Dict, Any, Optional
from app.core.logger import logger
from sqlalchemy import text
from app.infrastructure.external.llm_service import get_llm_provider


class KnowledgeBase:
    """Gestiona la base de conocimiento usando PostgreSQL + pgvector"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KnowledgeBase, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.llm = get_llm_provider()
        logger.info("✅ KnowledgeBase: Inicializado con búsqueda en PostgreSQL+pgvector")
    
    async def search_in_knowledge_async(
        self, 
        query: str, 
        session=None, 
        top_k: int = 3, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca información relevante en PostgreSQL con filtrado de versiones y vigencia.
        Combina búsqueda por texto (exacta) y vectorial (semántica).
        """
        if session is None:
            logger.warning("⚠️ No se proporcionó sesión de BD")
            return []
        
        # Filtros por defecto: Solo documentos activos/vigentes
        if filters is None:
            filters = {"is_active": True}
        
        logger.info(f"🔍 Búsqueda híbrida (filtros: {filters}) para: {query[:100]}")
        
        results_map = {}

        # 1. Búsqueda por Texto (Palabras clave)
        try:
            text_results = await self.search_in_knowledge_text_async(query, session, top_k, filters)
            for res in text_results:
                results_map[res["id"]] = res
                results_map[res["id"]]["method"] = "text"
        except Exception as e:
            logger.error(f"❌ Error en búsqueda por texto: {e}")

        # 2. Búsqueda Vectorial (Semántica)
        try:
            query_embedding = await self.llm.embed(query)
            
            where_clauses = ["dc.embedding IS NOT NULL"]
            params = {
                "query_embedding": query_embedding,
                "top_k": top_k
            }
            
            if filters.get("is_active") is not None:
                where_clauses.append("d.is_active = :is_active")
                params["is_active"] = filters["is_active"]
            
            if filters.get("category"):
                where_clauses.append("d.category = :category")
                params["category"] = filters["category"]

            if filters.get("version_label"):
                where_clauses.append("d.version_label = :version_label")
                params["version_label"] = filters["version_label"]
            
            where_str = " AND ".join(where_clauses)
            
            sql_query = text(f"""
                SELECT 
                    dc.id,
                    dc.text,
                    d.title,
                    d.category,
                    d.version_label,
                    (dc.embedding <=> :query_embedding::vector) as distance
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE {where_str}
                ORDER BY distance
                LIMIT :top_k
            """)
            
            result = await session.execute(sql_query, params)
            rows = result.fetchall()
            
            for row in rows:
                doc_id = row[0]
                if doc_id not in results_map:
                    results_map[doc_id] = {
                        "id": doc_id,
                        "content": row[1],
                        "source": f"{row[2]} ({row[4]})" if row[4] else row[2],
                        "category": row[3],
                        "version_label": row[4],
                        "relevance": f"Distancia: {row[5]:.3f}",
                        "method": "vector"
                    }
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda vectorial: {e}")
            if session:
                await session.rollback()

        final_results = list(results_map.values())
        
        if final_results:
            logger.info(f"✅ Híbrido: Encontrados {len(final_results)} documentos relevantes")
        
        # Retornar los más relevantes (priorizando texto si hay coincidencia, o simplemente los primeros top_k)
        return final_results[:top_k * 2]

    async def search_in_knowledge_text_async(
        self, 
        query: str, 
        session=None, 
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Versión de búsqueda por texto con filtrado estructurado.
        """
        if session is None:
            logger.warning("⚠️ No session provided to text search")
            return []
        
        # Filtros por defecto
        if filters is None:
            filters = {"is_active": True}
        
        try:
            # Extraer palabras clave
            stopwords = {"¿", "?", "y", "o", "la", "el", "de", "para", "en", "son", "es", "que", "qué", "cuáles", "cuál", "cual", "cuales"}
            keywords = [w.strip() for w in query.lower().split() if w.strip() not in stopwords and len(w.strip()) > 2]
            
            if not keywords:
                return []
            
            search_patterns = " | ".join(keywords)
            
            # Construir filtros SQL
            where_clauses = ["to_tsvector('spanish', dc.text) @@ query"]
            params = {"query": search_patterns, "top_k": top_k}
            
            if filters.get("is_active") is not None:
                where_clauses.append("d.is_active = :is_active")
                params["is_active"] = filters["is_active"]
            
            if filters.get("category"):
                where_clauses.append("d.category = :category")
                params["category"] = filters["category"]

            where_str = " AND ".join(where_clauses)
            
            sql_query = text(f"""
                SELECT 
                    dc.id,
                    dc.text,
                    d.title,
                    d.category,
                    d.version_label,
                    ts_rank(to_tsvector('spanish', dc.text), query) as relevance
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id,
                to_tsquery('spanish', :query) query
                WHERE {where_str}
                ORDER BY relevance DESC
                LIMIT :top_k
            """)
            
            result = await session.execute(sql_query, params)
            rows = result.fetchall()
            
            # Fallback a ILIKE si no hay resultados
            if len(rows) == 0:
                conditions = " OR ".join([f"dc.text ILIKE :keyword_{i}" for i in range(len(keywords))])
                where_clauses_ilike = [f"({conditions})"]
                
                if filters.get("is_active") is not None:
                    where_clauses_ilike.append("d.is_active = :is_active")
                
                where_str_ilike = " AND ".join(where_clauses_ilike)
                
                sql_query = text(f"""
                    SELECT 
                        dc.id,
                        dc.text,
                        d.title,
                        d.category,
                        d.version_label
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE {where_str_ilike}
                    LIMIT :top_k
                """)
                
                params_ilike = {f"keyword_{i}": f"%{kw}%" for i, kw in enumerate(keywords)}
                params_ilike["top_k"] = top_k
                if filters.get("is_active") is not None:
                    params_ilike["is_active"] = filters["is_active"]
                
                result = await session.execute(sql_query, params_ilike)
                rows = result.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    "id": row[0],
                    "content": row[1],
                    "source": f"{row[2]} ({row[4]})" if row[4] else row[2],
                    "category": row[3],
                    "version_label": row[4],
                    "relevance": "Búsqueda por palabras clave"
                })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Text search error: {e}", exc_info=True)
            if session:
                await session.rollback()
            return []
    
    def search_in_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Versión fallback síncrona - retorna vacío"""
        logger.warning("⚠️ search_in_knowledge() llamada - debe usarse search_in_knowledge_async()")
        return []
    
    def get_system_context(self) -> str:
        """Obtiene el contexto del sistema para inyectar en el prompt del LLM"""
        return """
## Base de Conocimiento: Registro Público de la Propiedad

Tienes acceso a documentos específicos sobre:
- **Costos y Aranceles** (Puebla, Quintana Roo)
- **Procedimientos** registrales regionales
- **Legislación** aplicable

INSTRUCCIONES:
1. Usa la información inyectada de los documentos
2. Cita explícitamente la fuente y región
3. Proporciona datos precisos: montos exactos, estados específicos
4. Si no tienes información exacta, admítelo

---
"""
    
    def get_knowledge_summary(self) -> str:
        """Obtiene un resumen genérico"""
        return """
## Base de Conocimiento (PostgreSQL + pgvector)
- Sistema: Búsqueda vectorial
- Documentos: RPP registry (Puebla, Quintana Roo)
- Tipos: Costos, Procedimientos, Legislación
"""


def get_knowledge_base() -> KnowledgeBase:
    """Factory para obtener la instancia singleton"""
    return KnowledgeBase()
