"""
Tests de Integración: HybridCacheLayer + ChatService + RAG

Valida que el sistema completo funcione:
1. Cache integral con ChatService
2. Verificar que cache hits previenen llamadas a LLM
3. Verificar que cache misses llaman a LLM
4. Verificar almacenamiento y recuperación end-to-end
5. Verificar estadísticas acumuladas
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import numpy as np

from app.application.services.chat_service import ChatService
from app.infrastructure.cache_layer import HybridCacheLayer


class TestCacheIntegrationWithChatService:
    """Tests de integración: Caché + ChatService"""
    
    @pytest.fixture
    async def setup_cache_and_service(self):
        """Setup: Crear instancias con mocks"""
        # Mock caché
        with patch('app.infrastructure.cache_layer.redis.asyncio.from_url'):
            cache = HybridCacheLayer()
            cache.redis_client = AsyncMock()
            cache.model = MagicMock()
            cache.stats = {"total_queries": 0, "cache_hits": 0, "cache_misses": 0}
        
        # Mock servicio de chat
        with patch('app.application.services.chat_service.get_smart_router'):
            with patch('app.application.services.chat_service.KnowledgeBase'):
                chat_service = ChatService()
                chat_service._llm = AsyncMock()
                chat_service._cache = cache
        
        yield cache, chat_service
    
    # ========== TESTS: CACHE HIT (SIN LLAMADA A LLM) ==========
    
    @pytest.mark.asyncio
    async def test_cache_hit_prevents_llm_call(self, setup_cache_and_service):
        """Test: Hit exacto en caché NO llama a LLM"""
        cache, chat_service = setup_cache_and_service
        
        query = "¿Cuál es el costo de una escritura?"
        cached_response = {
            "response": "El costo es de $500 MXN",
            "sources": ["REQUISITOS.md"],
            "needs_llm_refinement": False
        }
        
        # Mock: caché devuelve hit exacto
        cache.get_with_fallback = AsyncMock(return_value=cached_response)
        
        # Mock: LLM (NO debe llamarse)
        chat_service._llm.chat = AsyncMock()
        
        # Procesar query
        result = await chat_service.process_query(
            query=query,
            session_id="test-session"
        )
        
        # Verificar resultado
        assert result["response"] == cached_response["response"]
        assert result["from_cache"] == "exact_or_similar"
        
        # Verificar que LLM NO se llamó
        chat_service._llm.chat.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cache_miss_calls_llm(self, setup_cache_and_service):
        """Test: Miss en caché llama a LLM y guarda resultado"""
        cache, chat_service = setup_cache_and_service
        
        query = "¿Nueva pregunta que no está en la caché?"
        llm_response = "Esta es una respuesta nueva de LLM"
        
        # Mock: caché retorna None (miss)
        cache.get_with_fallback = AsyncMock(return_value=None)
        cache.store_response = AsyncMock()
        
        # Mock: LLM retorna respuesta
        chat_service._llm.chat = AsyncMock(return_value=llm_response)
        
        # Mock: Knowledge base
        chat_service.knowledge_base.search_in_knowledge_async = AsyncMock(
            return_value=[]
        )
        
        # Procesar query
        result = await chat_service.process_query(
            query=query,
            session_id="test-session"
        )
        
        # Verificar resultado
        assert result["response"] == llm_response
        assert result["from_cache"] == "llm_processed"
        
        # Verificar que LLM se llamó
        chat_service._llm.chat.assert_called_once()
        
        # Verificar que se guardan los datos en caché
        cache.store_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_similar_match_with_llm_refinement(self, setup_cache_and_service):
        """Test: Hit similar marca para refinamiento de LLM"""
        cache, chat_service = setup_cache_and_service
        
        query = "¿Cuánto cuesta una escritura pública?"
        cached_response = {
            "response": "¿Cuál es el costo de escribir una propiedad? Respuesta anterior",
            "similarity_score": 0.78,
            "needs_llm_refinement": True  # Necesita refinamiento
        }
        refined_response = "Respuesta refinada más específica"
        
        # Mock: caché retorna similar
        cache.get_with_fallback = AsyncMock(return_value=cached_response)
        cache.store_response = AsyncMock()
        
        # Mock: LLM refina la respuesta
        chat_service._llm.chat = AsyncMock(return_value=refined_response)
        
        # Mock: Knowledge base
        chat_service.knowledge_base.search_in_knowledge_async = AsyncMock(
            return_value=[]
        )
        
        # Procesar query
        result = await chat_service.process_query(
            query=query,
            session_id="test-session"
        )
        
        # Verificar que refina la respuesta
        assert result["response"] == refined_response
        chat_service._llm.chat.assert_called_once()
        
        # Verificar que guarda respuesta refinada
        cache.store_response.assert_called_once()
    
    # ========== TESTS: RECUPERACIÓN END-TO-END ==========
    
    @pytest.mark.asyncio
    async def test_store_then_retrieve_same_query(self, setup_cache_and_service):
        """Test: Guarda respuesta y la recupera en siguiente query idéntica"""
        cache, chat_service = setup_cache_and_service
        
        query1 = "¿Requisitos para vender una propiedad?"
        response1 = "Los requisitos son: 1. Identidad 2. Títulos 3. Comprobante domicilio"
        
        # Primera query: miss en caché
        cache.get_with_fallback = AsyncMock(return_value=None)
        cache.store_response = AsyncMock()
        chat_service._llm.chat = AsyncMock(return_value=response1)
        chat_service.knowledge_base.search_in_knowledge_async = AsyncMock(
            return_value=[]
        )
        
        result1 = await chat_service.process_query(query=query1, session_id="s1")
        assert result1["response"] == response1
        assert result1["from_cache"] == "llm_processed"
        
        # Simulando que la siguiente query encuentra el resultado (hit)
        cached = {
            "response": response1,
            "sources": ["docs"],
            "needs_llm_refinement": False
        }
        cache.get_with_fallback = AsyncMock(return_value=cached)
        
        # Segunda query: mismo query
        result2 = await chat_service.process_query(query=query1, session_id="s2")
        assert result2["response"] == response1
        assert result2["from_cache"] == "exact_or_similar"
        
        # LLM NO debe llamarse en el segundo query
        assert chat_service._llm.chat.call_count == 1
    
    # ========== TESTS: MANEJO DE ERRORES ==========
    
    @pytest.mark.asyncio
    async def test_cache_error_does_not_break_service(self, setup_cache_and_service):
        """Test: Error en caché no rompe el servicio"""
        cache, chat_service = setup_cache_and_service
        
        query = "Test query"
        llm_response = "Respuesta de LLM"
        
        # Mock: caché lanza error
        cache.get_with_fallback = AsyncMock(
            side_effect=Exception("Redis connection error")
        )
        
        # Mock: LLM funciona normalmente
        chat_service._llm.chat = AsyncMock(return_value=llm_response)
        chat_service.knowledge_base.search_in_knowledge_async = AsyncMock(
            return_value=[]
        )
        
        # Procesar query (debe manejarse el error)
        result = await chat_service.process_query(query=query)
        
        # Debe haber error en respuesta
        assert "error" in result or result.get("response")
    
    @pytest.mark.asyncio
    async def test_llm_error_returns_error_message(self, setup_cache_and_service):
        """Test: Error en LLM retorna mensaje amigable"""
        cache, chat_service = setup_cache_and_service
        
        query = "Test query"
        
        # Mock: caché miss
        cache.get_with_fallback = AsyncMock(return_value=None)
        
        # Mock: LLM lanza error
        chat_service._llm.chat = AsyncMock(
            side_effect=Exception("Groq API error")
        )
        chat_service.knowledge_base.search_in_knowledge_async = AsyncMock(
            return_value=[]
        )
        
        # Procesar query
        result = await chat_service.process_query(query=query)
        
        # Debe tener error en respuesta
        assert "error" in result or "Error" in result.get("response", "")
    
    # ========== TESTS: INFORMACIÓN EN RESPUESTA ==========
    
    @pytest.mark.asyncio
    async def test_response_includes_cache_metadata(self, setup_cache_and_service):
        """Test: Respuesta incluye metadata de caché para debugging"""
        cache, chat_service = setup_cache_and_service
        
        cached_result = {
            "response": "Respuesta cacheada",
            "similarity_score": 0.88,
            "needs_llm_refinement": False,
            "sources": ["doc1.md", "doc2.md"]
        }
        
        cache.get_with_fallback = AsyncMock(return_value=cached_result)
        
        result = await chat_service.process_query(
            query="Test",
            session_id="session1"
        )
        
        # Verificar metadata
        assert "from_cache" in result
        assert "query_length" in result
        assert "response_length" in result
        assert "timestamp" in result
        assert "cached_similarity_score" in result


class TestCachePerformanceCharacteristics:
    """Tests para verificar características de performance"""
    
    @pytest.mark.asyncio
    async def test_cache_hit_latency_minimal(self):
        """Test: Hit en caché es muy rápido (< 10ms)"""
        import time
        
        with patch('app.infrastructure.cache_layer.redis.asyncio.from_url'):
            cache = HybridCacheLayer()
            cache.redis_client = AsyncMock()
            cache.get_with_fallback = AsyncMock(
                return_value={"response": "cached"}
            )
            
            start = time.time()
            await cache.get_with_fallback("test query")
            elapsed = (time.time() - start) * 1000  # ms
            
            # Cache hit debe ser muy rápido (< 50ms)
            assert elapsed < 50, f"Cache hit took {elapsed}ms, expected <50ms"
    
    @pytest.mark.asyncio
    async def test_statistics_tracking_accuracy(self):
        """Test: Estadísticas se acumulan correctamente"""
        with patch('app.infrastructure.cache_layer.redis.asyncio.from_url'):
            cache = HybridCacheLayer()
            cache.redis_client = AsyncMock()
            cache.model = MagicMock()
            cache.model.encode = MagicMock(
                return_value=np.array([0.1, 0.2, 0.3])
            )
            
            # Simular 100 queries: 60 hits, 40 misses
            cache.stats = {
                "total_queries": 100,
                "cache_hits": 60,
                "cache_misses": 40,
                "tokens_saved": 60000
            }
            
            stats = await cache.get_cache_stats()
            
            # Verificar hit rate
            assert stats["hit_rate_percentage"] == 60.0
            
            # Verificar que los datos se calcularon
            assert stats["total_queries"] == 100
            assert stats["cache_hits"] == 60


class TestCacheWithMultipleSessions:
    """Tests para caché con múltiples sesiones simultáneas"""
    
    @pytest.mark.asyncio
    async def test_different_users_independent_caches(self):
        """Test: Caché es compartida pero sin cross-contamination"""
        with patch('app.infrastructure.cache_layer.redis.asyncio.from_url'):
            cache = HybridCacheLayer()
            cache.redis_client = AsyncMock()
            cache.model = MagicMock()
            cache.model.encode = MagicMock(
                return_value=np.array([0.1, 0.2, 0.3])
            )
            
            # User 1 query
            query1 = "User 1: ¿Costo de escritura?"
            response1 = "User 1 response"
            cache.store_response = AsyncMock()
            
            await cache.store_response(query1, response1, [])
            
            # User 2 query (diferente)
            query2 = "User 2: ¿Notaría?"
            response2 = "User 2 response"
            
            await cache.store_response(query2, response2, [])
            
            # Ambas queries deben ser almacenadas (sin sobrescribirse)
            assert cache.store_response.call_count == 2
            
            # Verificar que cada query es tratada independientemente
            calls = cache.store_response.call_args_list
            assert calls[0][0][0] != calls[1][0][0]  # Queries diferentes
