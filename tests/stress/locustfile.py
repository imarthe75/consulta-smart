import random
from locust import HttpUser, task, between

class ConsultaRPPStressUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Pre-login or setup if needed. Using fixed demo creds."""
        self.login()

    def login(self):
        resp = self.client.post("/api/v1/auth/login", data={
            "username": "demo@example.com",
            "password": "password123"
        })
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.headers = {}

    @task(3)
    def chat_query(self):
        """Simulate RAG chat questions"""
        questions = [
            "¿Cuáles son los requisitos para una compraventa?",
            "¿Cómo inscribir una hipoteca?",
            "Requisitos para cancelación de patrimonio de familia",
            "¿Qué documentos necesito para una donación?",
            "Horarios de atención del RPP"
        ]
        query = random.choice(questions)
        self.client.post("/api/v1/chat/message", json={
            "content": query,
            "session_id": "stress-test-session"
        }, headers=self.headers)

    @task(1)
    def list_documents(self):
        """Simulate browsing documents"""
        self.client.get("/api/v1/documents", headers=self.headers)

    @task(1)
    def health_check(self):
        """System health monitoring"""
        self.client.get("/api/v1/health")

