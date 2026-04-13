
import os
from google.cloud import aiplatform
from google.oauth2 import service_account
from app.core.config import settings

def list_foundation_models():
    credentials = service_account.Credentials.from_service_account_file(settings.GCP_CREDENTIALS_JSON)
    aiplatform.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_LOCATION, credentials=credentials)
    
    # We can try to use the Model.list() but for foundation models it's often better
    # to check the actual publisher garden or just probe names.
    # High-level list of base models is usually not supported via Model.list() (which is for user-trained models)
    
    # Let's try to initialize and check permissions
    print(f"Probing models for project {settings.GCP_PROJECT_ID} in {settings.GCP_LOCATION}...")
    
    from vertexai.generative_models import GenerativeModel
    
    # Probing simplified names
    to_probe = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
    
    for name in to_probe:
        try:
            model = GenerativeModel(name)
            # Try a very simple call
            response = model.generate_content("ping", generation_config={"max_output_tokens": 1})
            print(f"✅ {name}: FOUND and RESPONDING")
        except Exception as e:
            print(f"❌ {name}: {e}")

if __name__ == "__main__":
    list_foundation_models()
