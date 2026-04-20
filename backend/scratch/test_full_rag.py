import requests
import json
import uuid

BASE_URL = "http://localhost:3001/api/v1"

def run_full_test():
    print("🚀 Iniciando prueba de estrés y funcionalidad ConsultaRPP 2026...")
    
    # 1. Login para obtener Token
    login_url = f"{BASE_URL}/auth/login"
    login_data = {
        "username": "demo@example.com",
        "password": "password123"
    }
    
    print(f"🔑 Intentando login como: {login_data['username']}")
    try:
        # FastAPI OAuth2 suele esperar Form-Data (data=) en lugar de JSON (json=)
        response = requests.post(login_url, data=login_data)
        if response.status_code != 200:
            print(f"❌ Fallo en login: {response.text}")
            return
        
        token = response.json().get("access_token")
        if not token:
            print("❌ No se recibió token en la respuesta")
            return
        print("✅ Autenticación exitosa.")
    except Exception as e:
        print(f"❌ Error de conexión en login: {e}")
        return

    # 2. Enviar consulta de RPP con Token
    chat_url = f"{BASE_URL}/chat/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    query = "Me aceptan una copia de mis papeles para pedir una constancia de libertad de gravámen?"
    session_id = str(uuid.uuid4())
    
    payload = {
        "message": query,
        "session_id": session_id
    }
    
    print(f"💬 Enviando consulta: '{query}'")
    try:
        response = requests.post(chat_url, headers=headers, json=payload, timeout=90)
        
        if response.status_code == 200:
            result = response.json()
            print(f"DEBUG Full Response: {json.dumps(result, indent=2)}")
            print("\n🤖 RESPUESTA DEL ASISTENTE EXPERTO:")
            print("-" * 50)
            print(result.get("response", "Sin respuesta"))
            print("-" * 50)
            print(f"\n✅ Prueba finalizada con éxito. Proveedor utilizado: {result.get('provider', 'N/A')}")
        else:
            print(f"❌ Fallo en consulta: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error durante la consulta de chat: {e}")

if __name__ == "__main__":
    run_full_test()
