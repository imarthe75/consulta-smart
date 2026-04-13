
import os
import vertexai
from google.cloud import aiplatform
from google.oauth2 import service_account
from app.core.config import settings

def discover_models():
    print(f"Checking credentials at: {settings.GCP_CREDENTIALS_JSON}")
    if not os.path.exists(settings.GCP_CREDENTIALS_JSON):
        print("❌ Credentials file not found.")
        return

    try:
        credentials = service_account.Credentials.from_service_account_file(settings.GCP_CREDENTIALS_JSON)
        aiplatform.init(
            project=settings.GCP_PROJECT_ID,
            location=settings.GCP_LOCATION,
            credentials=credentials
        )
        
        print(f"Project: {settings.GCP_PROJECT_ID}")
        print(f"Location: {settings.GCP_LOCATION}")

        # Try to list models (this lists deployed models/base models depending on API)
        # Note: listing foundation models in Vertex is sometimes tricky via SDK
        # We will try to 'Get' known ones to see which returns a valid object
        
        test_names = [
            "gemini-1.5-flash-002",
            "gemini-1.5-flash-001",
            "gemini-1.5-flash",
            "gemini-1.0-pro-002",
            "gemini-1.0-pro",
            "gemini-1.5-pro-002",
            "gemini-1.5-pro-001",
            "gemini-1.5-pro",
            "gemini-3.1-flash-lite-preview",
            "gemini-3.1-pro-preview"
        ]

        from vertexai.generative_models import GenerativeModel
        
        print("\n--- Discovery Results ---")
        available = []
        for name in test_names:
            try:
                model = GenerativeModel(name)
                # We do a tiny request to verify actual availability (not just init)
                response = model.generate_content("test", generation_config={"max_output_tokens": 1})
                print(f"✅ {name}: AVAILABLE")
                available.append(name)
            except Exception as e:
                err_msg = str(e).split('\n')[0]
                print(f"❌ {name}: {err_msg[:100]}")
        
        if available:
            print(f"\nRecommended model for .env: VERTEX_MODEL={available[0]}")
        else:
            print("\nNo models found available with current credentials/region.")

    except Exception as e:
        print(f"General error: {e}")

if __name__ == "__main__":
    discover_models()
