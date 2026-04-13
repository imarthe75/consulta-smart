
import os
from google.cloud import aiplatform
from google.oauth2 import service_account
from app.core.config import settings

def list_all_available_models():
    credentials = service_account.Credentials.from_service_account_file(settings.GCP_CREDENTIALS_JSON)
    
    # We will iterate through a few regions and try to list model garden models if possible
    # But usually, it's easier to list the models that have been 'enabled' in the project
    
    regions = ["us-central1", "us-east1", "us-east4", "europe-west1"]
    
    for region in regions:
        print(f"\n--- Region: {region} ---")
        try:
            # We can't easily list foundation models via SDK without knowing the publisher
            # But we can try to get the 'model' object for a very basic one
            from google.cloud import aiplatform_v1
            client_options = {"api_endpoint": f"{region}-aiplatform.googleapis.com"}
            client = aiplatform_v1.ModelServiceClient(credentials=credentials, client_options=client_options)
            
            # This lists custom models, but maybe it gives us a hint
            parent = f"projects/{settings.GCP_PROJECT_ID}/locations/{region}"
            models = client.list_models(parent=parent)
            print(f"Custom models found: {list(models)}")
            
            # Now try the foundation models via vertexai init
            import vertexai
            from vertexai.generative_models import GenerativeModel
            vertexai.init(project=settings.GCP_PROJECT_ID, location=region, credentials=credentials)
            
            probe_list = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
            for p in probe_list:
                try:
                    m = GenerativeModel(p)
                    # Use a very short timeout/max tokens
                    res = m.generate_content("test", generation_config={"max_output_tokens": 1})
                    print(f"✅ FOUND {p} in {region}")
                except Exception as e:
                    print(f"❌ {p} in {region}: {str(e)[:100]}")
                    
        except Exception as e:
            print(f"Error in {region}: {e}")

if __name__ == "__main__":
    list_all_available_models()
