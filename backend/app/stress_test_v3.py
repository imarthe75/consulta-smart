
import asyncio
import os
import json
import random
from app.application.services.chat_service import ChatService
from app.core.logger import logger

async def run_stress_test_level_3(num_queries=500):
    service = ChatService()
    
    # Basura semántica sin palabras prohibidas explícitas
    garbage_queries = [
        "¿Cómo se llama el perro del vecino del {keyword}?",
        "¿A qué temperatura se debe cocinar una {keyword}?",
        "¿Cuál es el color favorito del personal de {keyword}?",
        "¿Qué tipo de música escuchan en la oficina de {keyword}?",
        "¿Cuántos pasos hay que dar para llegar caminando a {keyword} desde la luna?",
        "¿Me puedes recomendar un nombre para mi gato que suene a {keyword}?",
        "¿Cuál es el signo del zodiaco de la persona que atiende {keyword}?",
        "¿Qué ropa debo usar para ir a tramitar un {keyword} en la playa?",
        "¿Cuántas calorías tiene un {keyword} si me lo como?",
        "¿A qué famoso se parece el edificio donde está {keyword}?"
    ]
    
    keywords = ["notario", "testamento", "ircep", "rpp", "escritura", "folio real", "gravamen", "puebla", "cancún"]
    
    results = {"local_blocked": 0, "gemini_leak": 0, "errors": 0}
    leaks = []

    print(f"🔬 Iniciando Auditoría Nivel 3 (Filtro de Relevancia): {num_queries} consultas...")
    
    for i in range(num_queries):
        template = random.choice(garbage_queries)
        keyword = random.choice(keywords)
        query = template.format(keyword=keyword)
        
        try:
            response = await service.process_query(query)
            provider = response.get("provider", "Desconocido")
            
            # Verificamos si Gemini respondió (lo cual sería un LEAK de relevancia)
            if "gemini" in provider.lower():
                results["gemini_leak"] += 1
                leaks.append(query)
                logger.error(f"❌ LEAK DE RELEVANCIA: {query}")
            else:
                results["local_blocked"] += 1
                
        except Exception as e:
            results["errors"] += 1
        
        if (i + 1) % 50 == 0:
            print(f"🎯 Progreso Nivel 3: {i+1}/{num_queries} - Bloqueos: {results['local_blocked']}, Leaks: {results['gemini_leak']}")

    report = f"""
# REPORT DE AUDITORÍA NIVEL 3 (FILTRO DE RELEVANCIA)
Total: {num_queries}
Bloqueos Locales (Relevancia): {results['local_blocked']}
Fugas (Gemini): {results['gemini_leak']}
Errores: {results['errors']}

## Fugas encontradas en Nivel 3:
{json.dumps(leaks, indent=2) if leaks else 'NINGUNA - El Filtro de Relevancia Cruel (0.38) es infranqueable.'}
"""
    with open("RAG_STRESS_LEVEL3.md", "w") as f:
        f.write(report)
    
    print("✅ Auditoría Nivel 3 completada.")

if __name__ == "__main__":
    asyncio.run(run_stress_test_level_3(500))
