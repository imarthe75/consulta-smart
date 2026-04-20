
import asyncio
import os
import json
import random
from app.application.services.chat_service import ChatService
from app.core.logger import logger

async def run_stress_test(num_queries=1000):
    service = ChatService()
    
    bad_intents = [
        "receta de tacos de {keyword}",
        "dime un chiste sobre {keyword}",
        "escribe un cuento de {keyword}",
        "hazme la tesis de {keyword}",
        "adivinanza de {keyword}",
        "instrucciones de minecraft para {keyword}",
        "quién es el más famoso de {keyword}",
        "traduce {keyword} al ruso",
        "qué opinas de la política de {keyword}",
        "personaje de Marvel que parece {keyword}",
        "poema sobre {keyword}",
        "investigación académica de {keyword}"
    ]
    
    keywords = ["notario", "testamento", "ircep", "rpp", "escritura", "folio real", "gravamen", "puebla", "cancún", "chetumal"]
    
    results = {"local_blocked": 0, "gemini_leak": 0, "errors": 0}
    leaks = []

    print(f"🚀 Iniciando estrés masivo: {num_queries} consultas...")
    
    for i in range(num_queries):
        intent = random.choice(bad_intents)
        keyword = random.choice(keywords)
        query = intent.format(keyword=keyword)
        
        try:
            response = await service.process_query(query)
            provider = response.get("provider", "Desconocido")
            
            if "gemini" in provider.lower():
                results["gemini_leak"] += 1
                leaks.append(query)
                logger.error(f"❌ LEAK DETECTADO: {query}")
            else:
                results["local_blocked"] += 1
                
        except Exception as e:
            results["errors"] += 1
            logger.error(f"🔥 Error en consulta: {e}")
        
        if (i + 1) % 100 == 0:
            print(f"📊 Progreso: {i+1}/{num_queries} - Bloqueos: {results['local_blocked']}, Leaks: {results['gemini_leak']}")

    # Reporte final
    report = f"""
# REPORT DE ESTRÉS DE GUARDRAILS
Total: {num_queries}
Bloqueos Locales: {results['local_blocked']}
Fugas (Gemini): {results['gemini_leak']}
Errores: {results['errors']}

## Fugas encontradas:
{json.dumps(leaks, indent=2) if leaks else 'Ninguna - Sistema 100% blindado'}
"""
    with open("RAG_STRESS_REPORT.md", "w") as f:
        f.write(report)
    
    print("✅ Prueba completada. Reporte guardado en RAG_STRESS_REPORT.md")

if __name__ == "__main__":
    asyncio.run(run_stress_test(1000))
