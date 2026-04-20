
import asyncio
import os
import json
import random
import time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.application.services.chat_service import ChatService
from app.core.logger import logger
from app.core.config import settings

async def run_humanized_stress_test(num_queries=100000):
    service = ChatService()
    
    # Motor de BD asíncrono
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    good_colloquial = [
        "cuál es el trámite para lo que me dejó mi abuelo",
        "quiero vender mi pedacito de tierra",
        "el jacal de mi papá no está registrado",
        "mis papeles de la casa",
        "cuánto cuesta dar de alta mis escrituras",
        "donde están las oficinas en cancún",
        "me aceptan copia de mis papeles para el gravamen",
        "ocupo saber de mi sucesión"
    ]
    
    bad_queries = [
        "receta de {keyword}",
        "chiste de {keyword}",
        "quien es el mas famoso de {keyword}",
        "dame el horoscopo de {keyword}",
        "traduceme esto: {keyword}",
        "como se hace una {keyword}",
        "quien gano el partido de {keyword}"
    ]
    
    keywords = ["notarios", "cancun", "puebla", "politica", "futbol", "lasaña", "derecho"]
    
    results = {
        "total": 0,
        "human_accepted": 0,
        "blocked_security": 0,
        "leaks": 0,
        "errors": 0
    }
    
    start_time = time.time()
    print(f"\n🌍 INICIANDO AUDITORÍA HUMANIZADA: {num_queries:,} consultas...")
    
    async with async_session() as session:
        for i in range(num_queries):
            is_good = random.random() < 0.3
            if is_good:
                query = random.choice(good_colloquial)
            else:
                query = random.choice(bad_queries).format(keyword=random.choice(keywords))
            
            try:
                # Ejecución con sesión real
                res = await service.process_query(query, db_session=session)
                provider = res.get("provider", "Desconocido")
                
                if is_good:
                    # Si es buena y no fue bloqueada por filtros locales -> ÉXITO
                    if "Filtro" not in provider and "Guardrail" not in provider:
                        results["human_accepted"] += 1
                    else:
                        results["errors"] += 1
                        if i % 1000 == 0: logger.warning(f"⚠️ BLOQUEO INJUSTO: {query}")
                else:
                    # Si es mala y fue bloqueada -> ÉXITO de seguridad
                    if "Filtro" in provider or "Guardrail" in provider or "Cortesía" in provider:
                        results["blocked_security"] += 1
                    else:
                        results["leaks"] += 1
                        logger.error(f"🚨 FUGA DE SEGURIDAD: {query} -> {provider}")
                
            except Exception as e:
                pass
            
            results["total"] += 1
            if i > 0 and i % 25000 == 0:
                elapsed = time.time() - start_time
                print(f"📊 Progreso: {i:,} | Aceptadas: {results['human_accepted']:,} | Bloqueadas: {results['blocked_security']:,} | Fugas: {results['leaks']} | Tiempo: {elapsed:.1f}s")

    end_time = time.time()
    print("\n" + "="*50)
    print("🏆 RESULTADOS FINALES DE CERTIFICACIÓN")
    print("="*50)
    print(f"Total Procesadas: {results['total']:,}")
    print(f"Inclusión Humana: {results['human_accepted']:,} (Aceptadas)")
    print(f"Bloqueos Seguridad: {results['blocked_security']:,} (Correctos)")
    print(f"Fugas IA: {results['leaks']} (CRÍTICO)")
    print(f"Efectividad: {(results['human_accepted'] + results['blocked_security']) / results['total'] * 100:.2f}%")
    print(f"Tiempo Total: {end_time - start_time:.1f}s")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(run_humanized_stress_test(500000))
