# AGENT.MD - Experto en Consultas Ciudadanas
## Módulo: consulta-smart
## Protocolo: GENESIS

### 1. Identidad
Este agente es la cara pública del ecosistema. Su foco es la resolución de dudas sobre trámites registrales (RPP) mediante una interfaz RAG.

### 2. Stack Tecnológico
*   **Orquestación RAG:** LangChain / LangGraph.
*   **Vector DB:** pgvector (en Core).
*   **Frontend:** Vite + React (según metadata de web app).
*   **Inferencia:** Groq (Llama 3) para velocidad.

### 3. Integración Core
*   Consulta el conocimiento indexado por `bootstrap.py` en `core-casmarts`.
*   Valida identidad vía Keycloak.

---
*Protocolo Resident Agent Genesis activado.*
