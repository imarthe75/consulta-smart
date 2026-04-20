
import google.generativeai as genai

def list_models():
    api_key = "AIzaSyB0XXBoBr0GBLBpHlcNwCn3AddI1Ow_1dg"
    genai.configure(api_key=api_key)
    
    print("--- Listing Available Models for API KEY ---")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Model ID: {m.name} | Display Name: {m.display_name}")
    except Exception as e:
        print(f"❌ Error listing models: {e}")

if __name__ == "__main__":
    list_models()
