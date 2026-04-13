#!/bin/bash
# Quick diagnostic query without needing psql
docker compose exec -T backend python3 -c "
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check_db():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text('SELECT COUNT(*) FROM documents'))
        doc_count = result.scalar()
        result = await session.execute(text('SELECT COUNT(*) FROM document_chunks'))
        chunk_count = result.scalar()
        result = await session.execute(text('SELECT title FROM documents LIMIT 5'))
        titles = [row[0] for row in result.fetchall()]
        print(f'Documents: {doc_count}')
        print(f'Chunks: {chunk_count}')
        print(f'Sample titles: {titles}')

asyncio.run(check_db())
"
