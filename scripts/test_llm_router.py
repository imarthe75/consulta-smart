#!/usr/bin/env python3
"""
Script: Prueba del Smart LLM Router
Verifica que Groq + Gemini + Embeddings locales funcionan correctamente
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Setup Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fake environment variables
os.environ.setdefault("APP_ENV", "development")


async def test_embeddings():
    """Prueba embeddings locales"""
    logger.info("\n" + "="*80)
    logger.info("🧪 TEST 1: Sentence Transformers (Embeddings Locales)")
    logger.info("="*80)
    
    try:
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        test_texts = [
            "¿Cuáles son las oficinas disponibles en Quintana Roo?",
            "Notarios en Puebla",
            "Requisitos para registrar una propiedad"
        ]
        
        for text in test_texts:
            embedding = model.encode(text)
            logger.info(f"✅ Embedding: {len(embedding)} dimensiones para: '{text[:50]}...'")
        
        logger.info("✅ Sentence Transformers funcionando correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en Sentence Transformers: {e}")
        return False


async def test_groq():
    """Prueba conexión a Groq"""
    logger.info("\n" + "="*80)
    logger.info("🧪 TEST 2: Groq Chat (Gratuito, 500/día)")
    logger.info("="*80)
    
    try:
        from app.infrastructure.external.llm_service import GroqProvider
        
        provider = GroqProvider()
        
        messages = [
            {
                "role": "user",
                "content": "Responde en una línea: ¿Qué es RPP (Registro Público de la Propiedad)?"
            }
        ]
        
        logger.info("📤 Enviando chat a Groq...")
        response = await provider.chat(messages=messages, temperature=0.3, max_tokens=100)
        
        logger.info(f"✅ Respuesta Groq: {response[:100]}...")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en Groq: {e}")
        return False


async def test_gemini():
    """Prueba conexión a Gemini"""
    logger.info("\n" + "="*80)
    logger.info("🧪 TEST 3: Google Gemini (Fallback, 10/min)")
    logger.info("="*80)
    
    try:
        from app.infrastructure.external.llm_service import GeminiProvider
        
        provider = GeminiProvider()
        
        messages = [
            {
                "role": "user",
                "content": "Responde en una línea: ¿Qué significa notario público?"
            }
        ]
        
        logger.info("📤 Enviando chat a Gemini...")
        response = await provider.chat(messages=messages, temperature=0.3, max_tokens=100)
        
        logger.info(f"✅ Respuesta Gemini: {response[:100]}...")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en Gemini: {e}")
        return False


async def test_smart_router():
    """Prueba Smart Router con fallback"""
    logger.info("\n" + "="*80)
    logger.info("🧪 TEST 4: Smart LLM Router (Groq → Gemini fallback)")
    logger.info("="*80)
    
    try:
        from app.infrastructure.external.smart_llm_router import get_smart_router
        
        router = await get_smart_router()
        
        logger.info("📊 Estado de proveedores:")
        status = router.get_status()
        for provider_name, provider_status in status.items():
            logger.info(f"  {provider_name}: {provider_status['status']}")
        
        messages = [
            {
                "role": "user",
                "content": "¿Cuál es el costo promedio de registrar una propiedad en México?"
            }
        ]
        
        logger.info("📤 Enviando chat a Smart Router...")
        response = await router.chat(messages=messages, temperature=0.5, max_tokens=150)
        
        logger.info(f"✅ Respuesta Router: {response[:150]}...")
        
        logger.info("\n📊 Estado final de proveedores:")
        status = router.get_status()
        for provider_name, provider_status in status.items():
            logger.info(f"  {provider_name}: {provider_status['status']} (éxitos: {provider_status['success_count']}, errores: {provider_status['error_count']})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en Smart Router: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Ejecuta todos los tests"""
    logger.info("\n🚀 INICIANDO PRUEBAS DEL SISTEMA")
    logger.info("="*80)
    
    results = {}
    
    # Test 1: Embeddings
    results["embeddings"] = await test_embeddings()
    
    # Test 2: Groq
    results["groq"] = await test_groq()
    
    # Test 3: Gemini
    results["gemini"] = await test_gemini()
    
    # Test 4: Smart Router
    results["smart_router"] = await test_smart_router()
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("📊 RESUMEN DE PRUEBAS")
    logger.info("="*80)
    
    for test_name, result in results.items():
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        logger.info(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n✅ TODAS LAS PRUEBAS PASARON - Sistema listo para producción")
        return 0
    else:
        logger.warning("\n❌ ALGUNAS PRUEBAS FALLARON - Ver errores arriba")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
