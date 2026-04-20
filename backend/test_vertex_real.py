
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
    
    locations = ["us-central1", "us-east1", "southamerica-east1"]
    models = ["gemini-1.5-flash", "gemini-1.5-flash-001", "gemini-1.5-flash-002", "gemini-1.0-pro"]
    
    for loc in locations:
        print(f"\n>>>> Testing Location: {loc} <<<<")
        vertexai.init(project=settings.GCP_PROJECT_ID, location=loc, credentials=credentials)
        for name in models:
            print(f"--- Testing Model: {name} in {loc} ---")
            try:
                model = GenerativeModel(name)
                response = model.generate_content("Hola")
                print(f"✅ SUCCESS with {name} in {loc}: {response.text}")
                return name, loc
            except Exception as e:
                print(f"❌ Failed {name} in {loc}: {e}")
    return None, None

if __name__ == "__main__":
    test_vertex_models()
