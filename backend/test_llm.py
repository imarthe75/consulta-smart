
import os
import asyncio
from app.core.config import settings
from app.infrastructure.external.llm_service import VertexAIProvider, GeminiProvider, GroqProvider

async def test_providers():
    print(f"Testing providers with settings:")
    print(f"GCP_PROJECT_ID: {settings.GCP_PROJECT_ID}")
    print(f"VERTEX_MODEL: {settings.VERTEX_MODEL}")
    print(f"GEMINI_MODEL: {settings.GEMINI_MODEL}")
    
    messages = [{"role": "user", "content": "Hola, ¿quién eres?"}]
    
    print("\n--- Testing Vertex AI ---")
    try:
        vertex = VertexAIProvider()
        response = await vertex.chat(messages, system="Eres un asistente.")
        print(f"Vertex Success: {response[:50]}...")
    except Exception as e:
        print(f"Vertex Failed: {e}")

    print("\n--- Testing Gemini Native ---")
    try:
        gemini = GeminiProvider()
        response = await gemini.chat(messages, system="Eres un asistente.")
        print(f"Gemini Success: {response[:50]}...")
    except Exception as e:
        print(f"Gemini Failed: {e}")

    print("\n--- Testing Groq ---")
    try:
        groq = GroqProvider()
        response = await groq.chat(messages)
        print(f"Groq Success: {response[:50]}...")
    except Exception as e:
        print(f"Groq Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_providers())
