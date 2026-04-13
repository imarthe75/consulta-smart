from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_session
from app.infrastructure.knowledge_base import get_knowledge_base
from app.core.auth_utils import get_current_user
from app.core.logger import logger

router = APIRouter(prefix="/api/v1/search", tags=["search"])

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10

@router.post("")
async def search_documents(
    request: SearchRequest,
    db_session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Buscar en la base de conocimiento"""
    try:
        kb = get_knowledge_base()
        results = await kb.search_in_knowledge_async(
            query=request.query,
            session=db_session,
            top_k=request.limit
        )
        
        return {
            "status": "success",
            "data": [
                {
                    "id": res["id"],
                    "content": res["content"],
                    "title": res["source"],
                    "category": res["category"],
                    "score": 0.95 if res["method"] == "text" else 0.85 # Simulación de score si no viene de la BD
                } for res in results
            ]
        }
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        raise HTTPException(status_code=500, detail=str(e))
