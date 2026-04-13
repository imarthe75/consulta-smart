#!/usr/bin/env python3
"""
Cargar documentación RPP a la base de datos
"""

import os
import sys
import asyncio
import uuid
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

async def main():
    from sqlalchemy import text, create_engine, select
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    from app.infrastructure.models.document import Document
    from app.infrastructure.models.document_chunk import DocumentChunk
    
    # Connect to DB
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Root docs dir
    docs_dir = Path(__file__).parent.parent / "docs" / "rpp-registry"
    
    # Find unique markdown files
    found_files = {}
    for md_file in docs_dir.glob("**/*.md"):
        if md_file.name in ("README.md", "INDEX.md"):
            continue
        if md_file.name not in found_files:
            found_files[md_file.name] = md_file
    
    print(f"📚 Found {len(found_files)} unique documents")
    print("")
    
    # Get system user for documents
    system_user_id = "019d73a6-d320-7c49-bee7-b19f368473ec"
    
    loaded_docs = 0
    loaded_chunks = 0
    
    async with async_session() as session:
        for doc_name, doc_path in sorted(found_files.items()):
            print(f"   📄 {doc_name}... ", end="", flush=True)
            
            try:
                # Read content
                content = doc_path.read_text(encoding='utf-8')
                if not content:
                    print("❌ EMPTY")
                    continue
                
                # Create document
                doc_id = str(uuid.uuid4())
                doc = Document(
                    id=doc_id,
                    title=doc_name.replace('.md', ''),
                    category='documentacion',
                    user_id=system_user_id,
                    file_type='md',
                    status='processed'
                )
                session.add(doc)
                await session.flush()
                
                # Split into chunks
                chunk_size = 1000
                overlap = 200
                chunk_num = 0
                
                for i in range(0, len(content), chunk_size - overlap):
                    chunk_text = content[i:i+chunk_size]
                    if not chunk_text.strip():
                        break
                    
                    chunk = DocumentChunk(
                        id=str(uuid.uuid4()),
                        document_id=doc_id,
                        chunk_number=chunk_num,
                        text=chunk_text
                    )
                    session.add(chunk)
                    chunk_num += 1
                    loaded_chunks += 1
                
                await session.commit()
                print(f"✅ ({chunk_num} chunks)")
                loaded_docs += 1
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
                await session.rollback()
    
    print("")
    print(f"✅ Loaded {loaded_docs} documents with {loaded_chunks} chunks")

if __name__ == "__main__":
    asyncio.run(main())
