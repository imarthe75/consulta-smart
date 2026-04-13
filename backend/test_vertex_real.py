
import vertexai
from vertexai.generative_models import GenerativeModel
import os
from app.core.config import settings

def test_vertex_models():
    from google.oauth2 import service_account
    credentials = None
    if os.path.exists(settings.GCP_CREDENTIALS_JSON):
        credentials = service_account.Credentials.from_service_account_file(settings.GCP_CREDENTIALS_JSON)
        print(f"Credentials loaded from {settings.GCP_CREDENTIALS_JSON}")
    
    vertexai.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_LOCATION, credentials=credentials)
    models = ["gemini-1.5-flash-002", "gemini-1.5-flash", "gemini-1.5-pro-002", "gemini-1.5-pro"]
    for name in models:
        print(f"\n--- Testing Vertex Model: {name} ---")
        try:
            model = GenerativeModel(name)
            response = model.generate_content("Hola")
            print(f"Success with {name}: {response.text}")
            return name
        except Exception as e:
            print(f"Failed {name}: {e}")
    return None

if __name__ == "__main__":
    test_vertex_models()
