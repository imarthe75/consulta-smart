#!/usr/bin/env python3
"""
Script para cargar documentos RPP y generar embeddings
Uso: python3 load_documents.py
"""

import requests
import json
import sys
import time
from pathlib import Path

BASE_URL = "http://localhost:3001/api/v1"
DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "password123"

def print_step(step_num, message):
    print(f"\n{'='*70}")
    print(f"PASO {step_num}: {message}")
    print(f"{'='*70}")

def login():
    """Realizar login y obtener token JWT"""
    print_step(1, "Obtener Token JWT")
    
    data = {
        "username": DEMO_EMAIL,
        "password": DEMO_PASSWORD
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Error de autenticación: {response.status_code}")
            print(response.text)
            return None
        
        token = response.json().get("access_token")
        
        if not token:
            print("❌ No se obtuvo token")
            print(response.text)
            return None
        
        print(f"✅ Autenticación exitosa")
        print(f"Token: {token[:50]}...")
        return token
        
    except Exception as e:
        print(f"❌ Error en login: {e}")
        return None

def load_documents(token):
    """Cargar documentos RPP y generar embeddings"""
    print_step(2, "Cargar Documentos RPP y Generar Embeddings")
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print("Iniciando carga de documentos...")
        print("(Esto puede tomar varios minutos...)") 
        
        response = requests.post(
            f"{BASE_URL}/documents/load-rpp-registry",
            headers=headers,
            timeout=300  # 5 minutos de timeout
        )
        
        print(f"\nStatus HTTP: {response.status_code}")
        
        if response.status_code not in [200, 201]:
            print(f"❌ Error: {response.text}")
            return False
        
        result = response.json()
        
        # Mostrar resultado
        if result.get("status") == "success":
            data = result.get("data", {})
            print(f"\n✅ Documentos cargados exitosamente!")
            print(f"  • Documentos cargados: {data.get('loaded', 0)}")
            print(f"  • Total procesados: {data.get('total', 0)}")
            print(f"  • Errores: {data.get('errors', 0)}")
            print(f"  • Chunks creados: {data.get('total_chunks', 0)}")
            return True
        else:
            print(f"❌ {result.get('detail', 'Error desconocido')}")
            return False
            
    except Exception as e:
        print(f"❌ Error cargando documentos: {e}")
        return False

def verify_documents():
    """Verificar que los documentos se cargaron en la BD"""
    print_step(3, "Verificar Documentos en Base de Datos")
    
    try:
        # Esta es una verificación básica - idealmente habría un endpoint para esto
        print("Para verificar los documentos cargados:")
        print("  1. Ve a http://localhost:3000 en tu navegador")
        print("  2. Abre la sección 'Documentos'")
        print("  3. Deberías ver una lista de documentos RPP")
        print("\nO usa SQL:")
        print("  docker exec consultarpp-postgres psql -U consultarpp_user -d consultarpp -c \"SELECT COUNT(*) FROM documents;\"")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  CARGADOR DE DOCUMENTOS RPP CON EMBEDDINGS".center(68) + "║")
    print("║" + "  Consulta-RPP".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    # Verificar conectividad
    print("\n🔍 Verificando conectividad...")
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al backend en http://localhost:3001")
        print("Verifica que los contenedores estén corriendo:")
        print("  docker ps | grep consultarpp")
        sys.exit(1)
    except:
        pass  # Algún endpoint puede no existir pero al menos está activo
    
    print("✅ Backend disponible\n")
    
    # Login
    token = login()
    if not token:
        print("\n❌ No se pudo autenticar. Abortando.")
        sys.exit(1)
    
    # Cargar documentos
    if not load_documents(token):
        print("\n❌ Error cargando documentos. Abortando.")
        sys.exit(1)
    
    # Verificar
    verify_documents()
    
    print("\n" + "="*70)
    print("✅ PROCESO COMPLETADO")
    print("="*70)
    print("\nLos documentos y embeddings están listos. El sistema ahora")
    print("usará RAG para responder con información de los documentos RPP.")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
