import asyncio
import json
import time
import statistics
import urllib.request
import urllib.parse
from typing import List

BASE_URL = "http://localhost:3001"

def login():
    url = f"{BASE_URL}/api/v1/auth/login"
    data = urllib.parse.urlencode({
        "username": "demo@example.com",
        "password": "password123"
    }).encode()
    
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            return res.get("access_token")
    except Exception as e:
        print(f"Login failed: {e}")
        return None

async def send_chat_request(token: str, query: str):
    # La ruta real corregida segun chat.py es /api/v1/chat/query
    url = f"{BASE_URL}/api/v1/chat/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # El DTO ChatQueryDTO espera 'message' en lugar de 'content'
    data = json.dumps({
        "message": query,
        "session_id": "stress-test-session"
    }).encode()
    
    start = time.perf_counter()
    try:
        loop = asyncio.get_event_loop()
        def do_request():
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.getcode()

        status_code = await loop.run_in_executor(None, do_request)
        elapsed = time.perf_counter() - start
        return elapsed, status_code
    except Exception as e:
        # print(f"Request failed: {e}")
        return 0, 500

async def stress_test(concurrency: int = 2, total_requests: int = 4):
    print(f"--- Iniciando estrés (urllib): {concurrency} concurrente, {total_requests} total ---")
    token = login()
    if not token:
        print("No se pudo obtener el token.")
        return

    queries = [
        "¿Cuáles son los requisitos para una compraventa?",
        "¿Cómo inscribir una hipoteca?"
    ]
    
    all_results = []
    for i in range(0, total_requests, concurrency):
        batch_size = min(concurrency, total_requests - i)
        tasks = [send_chat_request(token, queries[j % len(queries)]) for j in range(batch_size)]
        results = await asyncio.gather(*tasks)
        all_results.extend(results)
        print(f"Procesadas {len(all_results)}/{total_requests} peticiones...")

    times = [r[0] for r in all_results if r[1] == 200]
    errors = [r[1] for r in all_results if r[1] != 200]
    
    print(f"\nResultados:")
    print(f"  Exitosas: {len(times)}")
    print(f"  Fallidas: {len(errors)}")
    if times:
        print(f"  Promedio: {statistics.mean(times):.2f}s")
    else:
        print("  Error: Verifique las rutas en el backend.")

if __name__ == "__main__":
    asyncio.run(stress_test())
