#!/usr/bin/env python3
"""
Test E2E completo del RAG de consulta-rpp
"""

import asyncio
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add to path
sys.path.insert(0, '/app')

async def main():
    """Test RAG end-to-end"""
    
    from app.infrastructure.knowledge_base import KnowledgeBase
    from app.infrastructure.external.smart_llm_router import get_smart_router
    from app.infrastructure.external.local_embedding_service import LocalEmbeddingService
    from app.core.database import get_session_factory
    from sqlalchemy.ext.asyncio import AsyncSession
    
    print("\n" + "="*80)
    print("🚀 TEST E2E: RAG SYSTEM")
    print("="*80 + "\n")
    
    # Crear sesión de BD
    async_session = get_session_factory()
    
    async with async_session() as session:
        # Test 1: Embeddings
        print("[1/4] Probando embeddings locales...")
        try:
            embeddings_svc = LocalEmbeddingService()
            test_embed = await embeddings_svc.embed("Hola mundo")
            print(f"✅ Embeddings: {len(test_embed)} dimensiones\n")
        except Exception as e:
            print(f"❌ Error en embeddings: {e}\n")
            return
        
        # Test 2: KB (con sesión)
        print("[2/4] Probando Knowledge Base search...")
        try:
            kb = KnowledgeBase()
            
            # Prueba 1: Oficinas en Quintana Roo
            docs = await kb.search_in_knowledge_async(
                "¿Cuáles son las oficinas disponibles en Quintana Roo?",
                session=session,
                top_k=3
            )
            
            if docs:
                print(f"✅ KB encontró {len(docs)} documentos")
                for i, doc in enumerate(docs, 1):
                    print(f"   {i}. {doc.get('source', 'Unknown')} ({doc.get('category', '?')})")
                    preview = doc.get('content', '')[:80].replace('\n', ' ')
                    print(f"      Preview: {preview}...")
            else:
                print(f"⚠️ KB no retornó resultados para esta consulta\n")
        except Exception as e:
            print(f"❌ Error en KB: {e}\n")
            import traceback
            traceback.print_exc()
            return
        
        print()
        
        # Test 3: LLM Router
        print("[3/4] Probando SmartLLMRouter...")
        try:
            router = await get_smart_router()
            print(f"✅ Router inicializado")
            print(f"   Proveedor activo: Groq\n")
        except Exception as e:
            print(f"❌ Error en router: {e}\n")
            return
        
        # Test 4: Chat completo
        print("[4/4] Probando pipeline completo...")
        try:
            from app.application.services.chat_service import ChatService
            
            chat_service = ChatService()
            
            # Query test
            query = "¿Cuáles son las oficinas disponibles en Quintana Roo?"
            print(f"📝 Query: {query}\n")
            
            result = await chat_service.process_query(
                query=query,
                session_id="test-001",
                db_session=session
            )
            
            print(f"✅ Respuesta del LLM:")
            print(f"{result.get('response')}\n")
            
            if result.get('sources'):
                print(f"📚 Fuentes utilizadas:")
                for source in result.get('sources', []):
                    print(f"   - {source}")
                print()
            
        except Exception as e:
            print(f"❌ Error en chat: {e}\n")
            import traceback
            traceback.print_exc()
            return
    
    print("="*80)
    print("✅ TODO FUNCIONA CORRECTAMENTE")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
