from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.application.services.chat_service import get_chat_service

router = APIRouter(prefix="/perf", tags=["perf"])

class PerfIn(BaseModel):
    question: str

@router.post("/ask")
async def perf_ask(payload: PerfIn, db: AsyncSession = Depends(get_session)):
    chat_service = await get_chat_service()

    result = await chat_service.process_query(
        query=payload.question,
        session_id="perf-test",
        conversation_history=[],
        db_session=db
    )

    return {"answer": result.get("response")}
