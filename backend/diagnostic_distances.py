
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.infrastructure.knowledge_base import KnowledgeBase
from app.core.config import settings

async def run_diagnostic_with_db():
    # Motor de BD real
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    kb = KnowledgeBase()
    queries = [
        "inscripción de escrituras", # Técnica (Control)
        "cuál es el trámite para lo que me dejó mi abuelo",
        "quiero vender mi pedacito de tierra",
        "mis papeles",
        "receta de lasaña"
    ]
    
    print("\n🔬 DIAGNÓSTICO CON BASE DE DATOS ACTIVA")
    print("-" * 50)
    
    async with async_session() as session:
        for query in queries:
            try:
                # Aquí forzamos la búsqueda con la sesión activa
                docs = await kb.search_in_knowledge_async(query, session=session, top_k=3)
                
                print(f"QUERY: {query}")
                if not docs:
                    print("❌ RESULTADO: 0 documentos encontrados.")
                else:
                    for i, doc in enumerate(docs):
                        dist = doc.get('relevance', '1.0').split(':')[-1].strip()
                        print(f"  [{i+1}] DISTANCIA: {dist} | FUENTE: {doc.get('source')}")
                print("-" * 50)
            except Exception as e:
                print(f"❌ Error en {query}: {e}")

if __name__ == "__main__":
    asyncio.run(run_diagnostic_with_db())
