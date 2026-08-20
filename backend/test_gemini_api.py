
import google.generativeai as genai
import os
import sys

def test_gemini_api():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Falta la variable de entorno GEMINI_API_KEY", file=sys.stderr)
        sys.exit(1)
    genai.configure(api_key=api_key)

    models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
    for name in models:
        print(f"--- Testing Gemini API Key with Model: {name} ---")
        try:
            model = genai.GenerativeModel(name)
            response = model.generate_content("Hola")
            print(f"✅ SUCCESS with {name}: {response.text}")
            return name
        except Exception as e:
            print(f"❌ Failed {name}: {e}")
    return None

if __name__ == "__main__":
    test_gemini_api()
