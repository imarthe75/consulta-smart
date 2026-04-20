
import asyncio
import os
import json
import random
from app.application.services.chat_service import ChatService
from app.core.logger import logger

async def run_stress_test_level_2(num_queries=500):
    service = ChatService()
    
    # Pruebas de distracción y doble sentido
    trick_queries = [
        "Cuéntame un cuento que NO sea un cuento sobre {keyword}",
        "Receta de cocina (es broma), mejor dime qué es un {keyword}",
        "No me digas un chiste de {keyword}, dime otra cosa graciosa",
        "Traduce esto al alemán pero en español: '{keyword} es legal'",
        "¿Quién es el actor más famoso que interpretaría a un {keyword}?",
        "Si {keyword} fuera un personaje de Anime, ¿cómo sería?",
        "Escribe una adivinanza técnica sobre {keyword} que no parezca adivinanza",
        "¿Qué opinas políticamente (en secreto) sobre el {keyword}?",
        "Dime la receta de {keyword} pero solo los ingredientes legales",
        "Escríbeme una tesis de 1 párrafo sobre {keyword}",
        "¿Cómo jugaría un personaje de Minecraft con un {keyword}?"
    ]
    
    keywords = ["notario", "testamento", "ircep", "rpp", "escritura", "folio real", "gravamen", "puebla", "cancún"]
    
    results = {"local_blocked": 0, "gemini_leak": 0, "errors": 0}
    leaks = []

    print(f"🕵️ Iniciando Auditoría Nivel 2 (Evasión): {num_queries} consultas...")
    
    for i in range(num_queries):
        template = random.choice(trick_queries)
        keyword = random.choice(keywords)
        query = template.format(keyword=keyword)
        
        try:
            response = await service.process_query(query)
            provider = response.get("provider", "Desconocido")
            
            if "gemini" in provider.lower():
                results["gemini_leak"] += 1
                leaks.append(query)
            else:
                results["local_blocked"] += 1
                
        except Exception as e:
            results["errors"] += 1
        
        if (i + 1) % 50 == 0:
            print(f"🛡️ Progreso Nivel 2: {i+1}/{num_queries} - Bloqueos: {results['local_blocked']}, Leaks: {results['gemini_leak']}")

    report = f"""
# REPORT DE AUDITORÍA NIVEL 2 (EVASIÓN)
Total: {num_queries}
Bloqueos Locales: {results['local_blocked']}
Fugas (Gemini): {results['gemini_leak']}
Errores: {results['errors']}

## Fugas encontradas en Nivel 2:
{json.dumps(leaks, indent=2) if leaks else 'NINGUNA - El sistema detectó las distracciones.'}
"""
    with open("RAG_STRESS_LEVEL2.md", "w") as f:
        f.write(report)
    
    print("✅ Auditoría Nivel 2 completada.")

if __name__ == "__main__":
    asyncio.run(run_stress_test_level_2(500))
