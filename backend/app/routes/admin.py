from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.core.database import get_db
from app.infrastructure.models import SystemConfig
from app.infrastructure.external.smart_llm_router import get_smart_router

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

class ConfigUpdate(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

class ConfigResponse(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    
class PromptGenerateRequest(BaseModel):
    topic: str
    context: str

@router.get("/configs/{key}", response_model=ConfigResponse)
def get_config(key: str, db: Session = Depends(get_db)):
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config

@router.post("/configs", response_model=ConfigResponse)
def update_config(data: ConfigUpdate, db: Session = Depends(get_db)):
    config = db.query(SystemConfig).filter(SystemConfig.key == data.key).first()
    if not config:
        config = SystemConfig(key=data.key, value=data.value, description=data.description)
        db.add(config)
    else:
        config.value = data.value
        if data.description:
            config.description = data.description
    db.commit()
    db.refresh(config)
    return config

@router.post("/generate-prompt")
async def generate_prompt(request: PromptGenerateRequest):
    """
    Usa el LLM para generar un prompt sistémico optimizado basado en el tema.
    """
    llm = get_smart_router()
    
    if request.context == "consulta":
        prompt_task = (
            f"Actúa como un Ingeniero de Prompts Senior. Genera un System Prompt altamente profesional "
            f"para un chatbot experto en: {request.topic}. "
            f"El prompt debe incluir: \n"
            f"1. Identidad clara.\n"
            f"2. Alcance (Scope) de temas válidos.\n"
            f"3. Instrucciones de cómo manejar documentos RAG.\n"
            f"4. Tono formal y ejecutivo.\n"
            f"5. Reglas de rechazo para temas fuera de dominio.\n"
            f"Responde ÚNICAMENTE con el texto del prompt, sin explicaciones adicionales."
        )
        response = await llm.agenerate(prompt_task)
        return {"prompt": response}
    else:
        # Lógica para IDP (Esquemas)
        schema_task = (
            f"Actúa como un Arquitecto de Datos. Genera un esquema JSON de extracción para documentos de: {request.topic}. "
            f"Incluye campos lógicos como folios, fechas, nombres de partes involucradas y montos. "
            f"Responde ÚNICAMENTE con el JSON válido."
        )
        response = await llm.agenerate(schema_task)
        # Intentar parsear JSON o devolver como string
        return {"schema": response}
