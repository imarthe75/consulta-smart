# Service Manager — Base de Conocimiento RAG (PostgreSQL + pgvector + Hybrid Retrieval)

from typing import List, Dict, Any, Optional
from app.core.logger import logger
from sqlalchemy import text
from app.infrastructure.external.llm_service import get_local_embedding_service


class KnowledgeBase:
    """
    Gestiona la base de conocimiento usando PostgreSQL + pgvector.
    
    Implementa un orquestador de búsqueda híbrida (Retrieval-Augmented Generation) que combina:
    1. Búsqueda vectorial semántica (vía `pgvector` con distancia de coseno `<=>`).
    2. Búsqueda léxica por palabras clave / full-text search (`to_tsvector` / `ts_rank` y fallback `ILIKE`).
    
    Patrón Singleton: garantiza la reutilización de la instancia de embedding service en toda la aplicación.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KnowledgeBase, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Servicio local de incrustaciones de texto (SentenceTransformers)
        self.llm = get_local_embedding_service()
        logger.info("✅ KnowledgeBase: Inicializado con búsqueda en PostgreSQL+pgvector usando embeddings locales")
    
    async def search_in_knowledge_async(
        self, 
        query: str, 
        session=None, 
        top_k: int = 3, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda Híbrida Principal: Ejecuta la búsqueda léxica y vectorial en paralelo,
        fusionando y deduplicando los resultados para garantizar la máxima relevancia.

        @param query: Texto de la consulta introducida por el usuario.
        @param session: Sesión asíncrona de SQLAlchemy.
        @param top_k: Número máximo de fragmentos relevantes a retornar.
        @param filters: Diccionario de filtros opcionales (ej. {"category": profile_id, "is_active": True}).
        """
        if session is None:
            logger.warning("⚠️ No se proporcionó sesión de BD")
            return []
        
        # Filtros por defecto: Solo documentos activos/vigentes
        if filters is None:
            filters = {"is_active": True}
        
        logger.info(f"🔍 Búsqueda híbrida (filtros: {filters}) para: {query[:100]}")
        
        results_map = {}

        # 1. Búsqueda Léxica / Palabras clave (Full-Text Search)
        try:
            text_results = await self.search_in_knowledge_text_async(query, session, top_k, filters)
            for res in text_results:
                results_map[res["id"]] = res
                results_map[res["id"]]["method"] = "text"
        except Exception as e:
            logger.error(f"❌ Error en búsqueda por texto: {e}")

        # 2. Búsqueda Vectorial Semántica (pgvector)
        try:
            # Generar incrustación vectorial para la consulta
            query_embedding = await self.llm.embed(query)
            
            # Formatear el vector para la sintaxis nativa de pgvector/asyncpg '[v1, v2, ...]'
            vec_fmt = f"[{','.join(map(str, query_embedding))}]"
            
            params = {
                "query_embedding": vec_fmt,
                "top_k": top_k,
                "is_active": True
            }
            
            # Consulta SQL optimizada exponiendo chunk_number y version_label para las citas de fuente
            sql_vector = text("""
                SELECT 
                    dc.id, dc.text, d.title, d.category, d.version_label,
                    (dc.embedding <=> CAST(:query_embedding AS vector)) as distance,
                    dc.chunk_number, d.id as document_id
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.is_active = :is_active AND dc.embedding IS NOT NULL
                ORDER BY distance
                LIMIT :top_k
            """)
            
            result = await session.execute(sql_vector, params)
            rows = result.fetchall()
            
            for row in rows:
                chunk_id = row[0]
                title    = row[2] or ""
                ver      = row[4]
                results_map[chunk_id] = {
                    "id":           chunk_id,
                    "document_id":  row[7],
                    "content":      row[1],
                    "source":       f"{title} ({ver})" if ver else title,
                    "title":        title,
                    "chunk_number": row[6],
                    "category":     row[3],
                    "version_label": ver,
                    "relevance":    f"Distancia: {row[5]:.3f}",
                    "method":       "vector"
                }
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda vectorial: {e}")
            if session:
                await session.rollback()

        # Ordenar y retornar los resultados consolidados de ambas fuentes
        final_results = list(results_map.values())
        return final_results[:top_k * 2]

    async def search_in_knowledge_text_async(
        self, 
        query: str, 
        session=None, 
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda por coincidencia de texto (Palabras Clave) mediante `to_tsvector` en español.
        Incluye fallback a coincidencia parcial `ILIKE` en caso de no hallar coincidencia exacta en el diccionario.
        """
        if session is None:
            logger.warning("⚠️ No session provided to text search")
            return []
        
        if filters is None:
            filters = {"is_active": True}
        
        try:
            # Filtrado de palabras vacías (stopwords) en español
            stopwords = {"¿", "?", "y", "o", "la", "el", "de", "para", "en", "son", "es", "que", "qué", "cuáles", "cuál", "cual", "cuales"}
            keywords = [w.strip() for w in query.lower().split() if w.strip() not in stopwords and len(w.strip()) > 2]
            
            if not keywords:
                return []
            
            # Construcción de query tsvector en sintaxis OR
            search_patterns = " | ".join(keywords)
            
            params = {
                "query_str": search_patterns,
                "top_k": top_k,
                "is_active": filters.get("is_active", True)
            }
            
            filter_clauses = ["d.is_active = :is_active", "to_tsvector('spanish', dc.text) @@ to_tsquery('spanish', :query_str)"]
            
            if filters.get("category"):
                filter_clauses.append("d.category = :category")
                params["category"] = filters["category"]
            
            where_stmt = " AND ".join(filter_clauses)
            
            sql_text = text(f"""
                SELECT 
                    dc.id,
                    dc.text,
                    d.title,
                    d.category,
                    d.version_label,
                    ts_rank(to_tsvector('spanish', dc.text), to_tsquery('spanish', :query_str)) as relevance
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE {where_stmt}
                ORDER BY relevance DESC
                LIMIT :top_k
            """)
            
            result = await session.execute(sql_text, params)
            rows = result.fetchall()
            
            # Fallback a coincidencia ILIKE si tsvector no retorna resultados
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
                title = row[2] or ""
                ver   = row[4]
                results.append({
                    "id":           row[0],
                    "content":      row[1],
                    "source":       f"{title} ({ver})" if ver else title,
                    "title":        title,
                    "chunk_number": None,
                    "category":     row[3],
                    "version_label": ver,
                    "relevance":    "Búsqueda por palabras clave"
                })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Text search error: {e}", exc_info=True)
            if session:
                await session.rollback()
            return []
    
    def search_in_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Método síncrono legacy (desaconsejado)."""
        logger.warning("⚠️ search_in_knowledge() llamada - debe usarse search_in_knowledge_async()")
        return []

def get_knowledge_base() -> KnowledgeBase:
    """Función de fábrica para obtener la instancia singleton de KnowledgeBase."""
    return KnowledgeBase()
