"""
Tests Unitarios para HybridCacheLayer

Valida:
1. Caché exacta (Redis)
2. Búsqueda de similitud (embeddings)
3. Estrategia de fallback
4. Almacenamiento de respuestas
5. Estadísticas y ROI
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import numpy as np

# Importar la clase a probar
from app.infrastructure.cache_layer import HybridCacheLayer


class TestHybridCacheLayer:
    """Tests para HybridCacheLayer"""
    
    @pytest.fixture
    async def cache_layer(self):
        """Fixture: Crear instancia de cache con Redis mockeado"""
        with patch('app.infrastructure.cache_layer.redis.asyncio.from_url'):
            cache = HybridCacheLayer()
            # Mockear Redis
            cache.redis_client = AsyncMock()
            # Mockear modelo de embeddings
            cache.model = MagicMock()
            cache.model.encode = MagicMock(return_value=np.array([0.1, 0.2, 0.3]))
            yield cache
    
    # ========== TESTS: GENERACIÓN DE CLAVE ==========
    
    def test_generate_cache_key_deterministic(self, cache_layer):
        """Verifica que la misma query siempre genere la misma clave"""
        query = "¿Cuál es el costo de una escritura pública?"
        key1 = cache_layer._generate_cache_key(query)
        key2 = cache_layer._generate_cache_key(query)
        
        assert key1 == key2, "El hash debe ser determinístico"
        assert isinstance(key1, str), "La clave debe ser string"
    
    def test_generate_cache_key_case_insensitive(self, cache_layer):
        """Verifica que la clave sea case-insensitive"""
        query1 = "¿Cuál es el costo?"
        query2 = "¿CUÁL ES EL COSTO?"
        
        key1 = cache_layer._generate_cache_key(query1)
        key2 = cache_layer._generate_cache_key(query2)
        
        assert key1 == key2, "Las claves deben ser iguales (case-insensitive)"
    
    def test_generate_cache_key_ignore_whitespace(self, cache_layer):
        """Verifica que la clave ignore espacios extra"""
        query1 = "¿Cuál es el costo de una escritura?"
        query2 = "¿Cuál   es   el   costo   de   una   escritura?"
        
        key1 = cache_layer._generate_cache_key(query1)
        key2 = cache_layer._generate_cache_key(query2)
        
        assert key1 == key2, "Los espacios extra deben ignorarse"
    
    # ========== TESTS: CACHÉ EXACTA (REDIS) ==========
    
    @pytest.mark.asyncio
    async def test_exact_match_redis_hit(self, cache_layer):
        """Test: Encuentra respuesta exacta en Redis"""
        query = "¿Cuál es el costo de una escritura?"
        cached_response = {
            "response": "El costo es de $500 MXN",
            "sources": ["REQUISITOS_POR_ACTO.md"],
            "confidence": 1.0
        }
        
        # Mockear respuesta de Redis
        cache_key = cache_layer._generate_cache_key(query)
        cache_layer.redis_client.get = AsyncMock(
            return_value=json.dumps(cached_response).encode()
        )
        
        result = await cache_layer.get_exact_match(query)
        
        assert result is not None, "Debe encontrar el resultado en Redis"
        assert result["response"] == cached_response["response"]
        assert result["confidence"] == 1.0
        cache_layer.redis_client.get.assert_called_once_with(cache_key)
    
    @pytest.mark.asyncio
    async def test_exact_match_redis_miss(self, cache_layer):
        """Test: No encuentra en Redis, retorna None"""
        query = "Pregunta que no existe"
        
        # Mockear Redis sin resultado
        cache_layer.redis_client.get = AsyncMock(return_value=None)
        
        result = await cache_layer.get_exact_match(query)
        
        assert result is None, "Debe retornar None si no hay hit exacto"
    
    @pytest.mark.asyncio
    async def test_exact_match_invalid_json(self, cache_layer):
        """Test: Redis devuelve JSON inválido"""
        query = "Test query"
        
        # Mockear Redis con JSON inválido
        cache_layer.redis_client.get = AsyncMock(
            return_value=b"invalid json {{"
        )
        
        result = await cache_layer.get_exact_match(query)
        
        assert result is None, "Debe retornar None si JSON es inválido"
    
    # ========== TESTS: BÚSQUEDA DE SIMILITUD (EMBEDDINGS) ==========
    
    @pytest.mark.asyncio
    async def test_similarity_search_high_similarity(self, cache_layer):
        """Test: Encuentra respuesta similar (score > 0.75)"""
        query = "¿Cuánto cuesta una escritura?"
        similar_query = "¿Cuál es el costo de una escritura?"
        response = "El costo es $500 MXN"
        
        # Simular embeddings similares (cosino similarity ~0.9)
        query_embedding = np.array([1.0, 0.0, 0.0])
        cached_embedding = np.array([0.95, 0.1, 0.05])
        
        cache_layer.model.encode = MagicMock(
            side_effect=[query_embedding, cached_embedding]
        )
        
        # Mockear Redis con respuesta cacheada
        cache_layer.redis_client.hgetall = AsyncMock(
            return_value={
                b"query": similar_query.encode(),
                b"response": response.encode(),
                b"embedding": json.dumps([0.95, 0.1, 0.05]).encode(),
                b"sources": json.dumps(["doc.md"]).encode()
            }
        )
        
        result = await cache_layer.get_similar_match(query)
        
        assert result is not None, "Debe encontrar respuesta similar"
        assert result["response"] == response
        assert result["similarity_score"] >= 0.75
    
    @pytest.mark.asyncio
    async def test_similarity_search_low_similarity(self, cache_layer):
        """Test: No encuentra si similitud es baja (< 0.75)"""
        query = "¿Cuánto cuesta una escritura?"
        
        # Simular embeddings muy diferentes (cosino similarity ~0.2)
        query_embedding = np.array([1.0, 0.0, 0.0])
        cached_embedding = np.array([0.1, 0.9, 0.1])
        
        cache_layer.model.encode = MagicMock(
            side_effect=[query_embedding, cached_embedding]
        )
        
        cache_layer.redis_client.hgetall = AsyncMock(
            return_value={
                b"query": b"Ligeramente diferente",
                b"response": b"Algo",
                b"embedding": json.dumps([0.1, 0.9, 0.1]).encode(),
                b"sources": json.dumps(["doc.md"]).encode()
            }
        )
        
        result = await cache_layer.get_similar_match(query)
        
        assert result is None or result.get("similarity_score", 0) < 0.75, \
            "Debe ignorar respuestas poco similares"
    
    @pytest.mark.asyncio
    async def test_similarity_search_empty_cache(self, cache_layer):
        """Test: Maneja caché vacía sin errores"""
        query = "¿Este es mi primer query?"
        
        cache_layer.model.encode = MagicMock(
            return_value=np.array([0.1, 0.2, 0.3])
        )
        cache_layer.redis_client.hgetall = AsyncMock(return_value={})
        
        result = await cache_layer.get_similar_match(query)
        
        assert result is None, "Debe retornar None si no hay items cacheados"
    
    # ========== TESTS: ESTRATEGIA DE FALLBACK ==========
    
    @pytest.mark.asyncio
    async def test_fallback_exact_match_found(self, cache_layer):
        """Test: Retorna hit exacto sin buscar similares"""
        query = "¿Costo de escritura?"
        exact_response = {"response": "Exacto", "confidence": 1.0}
        
        cache_layer.get_exact_match = AsyncMock(return_value=exact_response)
        cache_layer.get_similar_match = AsyncMock()  # No debe llamarse
        
        result = await cache_layer.get_with_fallback(query)
        
        assert result == exact_response
        cache_layer.get_exact_match.assert_called_once()
        cache_layer.get_similar_match.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_fallback_similar_match_found(self, cache_layer):
        """Test: Busca similares si no hay exacto"""
        query = "¿Cuánto cuesta una escritura?"
        similar_response = {
            "response": "Similar",
            "similarity_score": 0.82
        }
        
        cache_layer.get_exact_match = AsyncMock(return_value=None)
        cache_layer.get_similar_match = AsyncMock(return_value=similar_response)
        
        result = await cache_layer.get_with_fallback(query)
        
        assert result == similar_response
        cache_layer.get_exact_match.assert_called_once()
        cache_layer.get_similar_match.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fallback_no_match(self, cache_layer):
        """Test: Retorna None si no hay exacto ni similar"""
        query = "Pregunta por primera vez"
        
        cache_layer.get_exact_match = AsyncMock(return_value=None)
        cache_layer.get_similar_match = AsyncMock(return_value=None)
        
        result = await cache_layer.get_with_fallback(query)
        
        assert result is None
        cache_layer.get_exact_match.assert_called_once()
        cache_layer.get_similar_match.assert_called_once()
    
    # ========== TESTS: ALMACENAMIENTO ==========
    
    @pytest.mark.asyncio
    async def test_store_response_success(self, cache_layer):
        """Test: Almacena respuesta con embedding y TTL"""
        query = "¿Costo de escritura?"
        response = "Es $500"
        sources = ["doc.md"]
        
        query_embedding = np.array([0.1, 0.2, 0.3])
        cache_layer.model.encode = MagicMock(return_value=query_embedding)
        
        cache_layer.redis_client.hset = AsyncMock()
        cache_layer.redis_client.expire = AsyncMock()
        
        await cache_layer.store_response(query, response, sources)
        
        # Verificar que se llamó a hset
        cache_layer.redis_client.hset.assert_called_once()
        # Verificar que se configuró TTL
        cache_layer.redis_client.expire.assert_called_once()
        
        # Verificar que se pasó TTL correcto (24h = 86400s)
        call_args = cache_layer.redis_client.expire.call_args
        assert call_args[0][1] == 86400, "TTL debe ser 24 horas"
    
    @pytest.mark.asyncio
    async def test_store_response_error_handling(self, cache_layer):
        """Test: Maneja errores al almacenar sin romper el flujo"""
        query = "¿Costo?"
        response = "Respuesta"
        
        cache_layer.model.encode = MagicMock(
            return_value=np.array([0.1, 0.2, 0.3])
        )
        cache_layer.redis_client.hset = AsyncMock(
            side_effect=Exception("Redis error")
        )
        
        # No debe lanzar excepción
        result = await cache_layer.store_response(query, response, [])
        assert result is None or isinstance(result, dict)
    
    # ========== TESTS: ESTADÍSTICAS ==========
    
    @pytest.mark.asyncio
    async def test_cache_stats_hit_rate(self, cache_layer):
        """Test: Calcula correctamente hit rate"""
        cache_layer.stats = {
            "total_queries": 100,
            "cache_hits": 60,
            "cache_misses": 40
        }
        
        stats = await cache_layer.get_cache_stats()
        
        assert "hit_rate_percentage" in stats
        assert stats["hit_rate_percentage"] == 60.0
    
    @pytest.mark.asyncio
    async def test_cache_stats_cost_savings(self, cache_layer):
        """Test: Calcula ahorros de costo correctamente"""
        cache_layer.stats = {
            "total_queries": 100,
            "cache_hits": 60,
            "tokens_saved": 60000
        }
        
        stats = await cache_layer.get_cache_stats()
        
        assert "estimated_cost_savings_usd" in stats
        # Con 60% hit rate: $0.00 (hit) + $0.0003 (20% miss full)
        # Estimado: 60% * 0 + 20% * 0.0005 = $0.0001 por query
    
    # ========== TESTS: LIMPIAR CACHÉ ==========
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, cache_layer):
        """Test: Limpia toda la caché correctamente"""
        cache_layer.redis_client.flushdb = AsyncMock()
        
        await cache_layer.clear_cache()
        
        cache_layer.redis_client.flushdb.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_clear_cache_error_handling(self, cache_layer):
        """Test: Maneja errores al limpiar sin romper"""
        cache_layer.redis_client.flushdb = AsyncMock(
            side_effect=Exception("Redis error")
        )
        
        # No debe lanzar excepción
        result = await cache_layer.clear_cache()
        assert result is None
    
    # ========== TESTS: CIERRE ==========
    
    @pytest.mark.asyncio
    async def test_close_redis_connection(self, cache_layer):
        """Test: Cierra conexión Redis correctamente"""
        cache_layer.redis_client.close = AsyncMock()
        
        await cache_layer.close()
        
        cache_layer.redis_client.close.assert_called_once()


class TestCacheROICalculation:
    """Tests para cálculos de ROI y ahorros"""
    
    @pytest.mark.asyncio
    async def test_roi_estimation_60_percent_hit_rate(self):
        """Test: ROI con 60% hit rate (objetivo)"""
        # Supuestos:
        # - 10,000 queries/mes
        # - 60% hit rate (caché)
        # - Costo Groq: $0.0005/query
        
        monthly_queries = 10000
        hit_rate = 0.60
        cost_per_query = 0.0005
        
        # Queries que van a LLM:
        llm_queries = monthly_queries * (1 - hit_rate)
        # Estimado: 20% nuevas queries (full LLM), 20% similares (minimal LLM)
        estimated_llm_cost = (monthly_queries * 0.2 * cost_per_query) + \
                            (monthly_queries * 0.2 * cost_per_query * 0.1)
        
        # Costo sin caché: 10,000 * $0.0005 = $5/mes
        cost_without_cache = monthly_queries * cost_per_query
        
        # Ahorro mensual
        monthly_savings = cost_without_cache - estimated_llm_cost
        
        assert monthly_savings > 0, "Debe haber ahorros"
        assert monthly_savings / cost_without_cache >= 0.5, \
            "Ahorro debe ser >= 50% del costo original"
    
    @pytest.mark.asyncio
    async def test_cost_comparison_groq_vs_groq_cached(self):
        """Test: Comparación costo Groq vs Groq + caché"""
        annual_queries = 10000 * 12  # 120,000 queries/año
        
        # Groq sin caché
        cost_groq_full = annual_queries * 0.0005  # $60/año
        
        # Groq + caché (60% hit, so 40% go to LLM)
        queries_to_llm = annual_queries * 0.4
        # 50% nuevas (full), 50% similares (minimal)
        cost_groq_cached = (queries_to_llm * 0.5 * 0.0005) + \
                           (queries_to_llm * 0.5 * 0.0005 * 0.1)
        
        # Además: Infraestructura caché (Redis + CPU minimal)
        cache_infrastructure = 12 * 10  # $10/mes = $120/año
        total_cost_cached = cost_groq_cached + cache_infrastructure
        
        assert total_cost_cached < cost_groq_full, \
            "Groq cached debe ser más barato"
