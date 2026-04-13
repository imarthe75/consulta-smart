#!/usr/bin/env python3
"""
Test directo del LLM sin pasar por la API
Útil para testing del flujo RAG
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_groq_directly():
    """Test Groq LLM provider directamente"""
    from groq import Groq
    import os
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("❌ GROQ_API_KEY no configurada")
        return False
    
    try:
        client = Groq(api_key=api_key)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": "¿Hola? Responde brevemente."}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        logger.info(f"✅ Groq responde: {response.choices[0].message.content}")
        return True
    except Exception as e:
        logger.error(f"❌ Error en Groq: {e}")
        return False


async def test_kb_search():
    """Test búsqueda en KB"""
    from app.infrastructure.knowledge_base import KnowledgeBase
    
    try:
        kb = KnowledgeBase()
        docs = await kb.search_in_knowledge_async(
            "¿Cuáles son las oficinas en Quintana Roo?",
            top_k=3
        )
        
        if docs:
            logger.info(f"✅ KB retorna {len(docs)} documentos:")
            for doc in docs:
                logger.info(f"   - {doc.get('source', 'Unknown')}: {doc.get('content', '')[:100]}")
            return True
        else:
            logger.warning("⚠️ KB no retorna documentos")
            return False
    except Exception as e:
        logger.error(f"❌ Error en KB: {e}")
        return False


async def test_embeddings():
    """Test embeddings locales"""
    from app.infrastructure.external.local_embedding_service import LocalEmbeddingService
    
    try:
        svc = LocalEmbeddingService()
        embedding = await svc.embed("Hola mundo")
        
        logger.info(f"✅ Embedding generado: {len(embedding)} dimensiones")
        return True
    except Exception as e:
        logger.error(f"❌ Error en embeddings: {e}")
        return False


async def main():
    """main"""
    os.environ["DATABASE_URL"] = "postgresql://consultarpp_user:password@postgres:5432/consultarpp"
    
    print("=" * 80)
    print("TESTING COMPONENTES RAG")
    print("=" * 80 + "\n")
    
    # Test 1: Embeddings locales
    print("[1/3] Testing embeddings locales...")
    result1 = await test_embeddings()
    print()
    
    # Test 2: KB search
    print("[2/3] Testing KB search...")
    result2 = await test_kb_search()
    print()
    
    # Test 3: Groq LLM
    print("[3/3] Testing Groq LLM...")
    result3 = await test_groq_directly()
    print()
    
    print("=" * 80)
    print("RESUMEN:")
    print(f"  Embeddings locales: {'✅ OK' if result1 else '❌ FAIL'}")
    print(f"  KB search:          {'✅ OK' if result2 else '❌ FAIL'}")
    print(f"  Groq LLM:           {'✅ OK' if result3 else '❌ FAIL'}")
    print("=" * 80 + "\n")
    
    if result1 and result3:
        logger.info("✅ RAG básico está listo - puedes hacer queries!")
    else:
        logger.warning("⚠️ Hay problemas en el setup")


if __name__ == "__main__":
    import os
    asyncio.run(main())
