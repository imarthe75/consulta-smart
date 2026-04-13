
import os
import vertexai
from google.cloud import aiplatform
from google.oauth2 import service_account
from app.core.config import settings
from vertexai.generative_models import GenerativeModel

def probe_regions():
    credentials = None
    if os.path.exists(settings.GCP_CREDENTIALS_JSON):
        credentials = service_account.Credentials.from_service_account_file(settings.GCP_CREDENTIALS_JSON)
    
    regions = ["us-central1", "us-east1", "us-west1", "europe-west1", "europe-west4", "asia-northeast1"]
    model_name = "gemini-1.5-flash-002"
    
    print(f"Probing {model_name} across regions...")
    
    for region in regions:
        try:
            vertexai.init(project=settings.GCP_PROJECT_ID, location=region, credentials=credentials)
            model = GenerativeModel(model_name)
            response = model.generate_content("test", generation_config={"max_output_tokens": 1})
            print(f"✅ FOUND in {region}")
            return region
        except Exception as e:
            msg = str(e).split('\n')[0]
            print(f"❌ {region}: {msg[:80]}")
    return None

if __name__ == "__main__":
    probe_regions()
