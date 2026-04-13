
import google.generativeai as genai
import os
from app.core.config import settings

def list_gemini_models():
    print("--- Listing Gemini Native Models ---")
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Model: {m.name}")
    except Exception as e:
        print(f"Error listing Gemini models: {e}")

def list_vertex_models():
    print("\n--- Listing Vertex AI Models ---")
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        vertexai.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_LOCATION)
        # Vertex doesn't have a simple 'list_models' in the generative_models SDK 
        # that works like the genai one, but we can try to initialize some common ones
        common_models = ["gemini-1.5-pro-001", "gemini-1.5-pro-002", "gemini-1.5-flash-001", "gemini-1.5-flash-002"]
        for name in common_models:
            try:
                model = GenerativeModel(name)
                # Just a dummy call to see if it's found
                print(f"Vertex model {name} initialized.")
            except Exception as e:
                print(f"Vertex model {name} failed: {e}")
    except Exception as e:
        print(f"Error initializing Vertex: {e}")

if __name__ == "__main__":
    list_gemini_models()
    list_vertex_models()
