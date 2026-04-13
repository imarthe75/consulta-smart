
import google.generativeai as genai
import os
from app.core.config import settings

def test_specific_model(model_name):
    print(f"--- Testing Gemini Native Model: {model_name} ---")
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Ping")
        print(f"✅ Success: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

if __name__ == "__main__":
    test_specific_model("gemini-2.5-flash-lite")
