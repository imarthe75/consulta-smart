#!/usr/bin/env python3
"""
Load all RPP documentation to database with proper chunking and deduplication
"""

import os
import sys
import asyncio
import uuid
from pathlib import Path
from typing import Dict, List

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

async def load_rpp_documents():
    """Load all RPP documentation files"""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from app.core.config import settings
    from app.infrastructure.models import DocumentModel, DocumentChunkModel
    
    # Connect to database
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Find all RPP documentation
    docs_dir = Path(__file__).parent.parent / "docs" / "rpp-registry"
    
    # Map to store documents with region info to load regional variants
    unique_docs: Dict[str, Path] = {}
    
    print("📚 Buscando documentos RPP...")
    print("-" * 60)
    
    # Scan all markdown files - prioritize files by path to get regional variants
    for md_file in sorted(docs_dir.glob("**/*.md")):
        # Skip README and INDEX
        if md_file.name in ("README.md", "INDEX.md"):
            continue
        
        # Skip files in the nested rpp-registry/rpp-registry dir (duplicates)
        if "rpp-registry/rpp-registry" in str(md_file):
            continue
        
        # Create a unique key that includes region for multi-region docs
        # For docs with same name in puebla/ and quintana-roo/, load both
        parent_dir = md_file.parent.name
        if parent_dir in ("puebla", "quintana-roo"):
            # Add region suffix to differentiate regional variants
            key = f"{md_file.stem}_{parent_dir}"
        else:
            key = md_file.name
        
        # Add to unique documents (using key to allow regional variants)
        unique_docs[key] = md_file
        region_info = f"({parent_dir})" if parent_dir in ("puebla", "quintana-roo") else ""
        print(f"  ✓ {md_file.name} {region_info}")
    
    print(f"\n📋 Total de documentos únicos: {len(unique_docs)}")
    print("-" * 60)
    
    # System user ID (from existing users)
    system_user_id = "019d73a6-d320-7c49-bee7-b19f368473ec"
    
    loaded_docs = 0
    loaded_chunks = 0
    skipped_docs = 0
    
    # Load each document
    async with async_session() as session:
        for doc_name, doc_path in sorted(unique_docs.items()):
            print(f"\n📄 {doc_name}... ", end="", flush=True)
            
            try:
                # Read file content
                content = doc_path.read_text(encoding='utf-8', errors='ignore')
                
                if not content or len(content) < 50:
                    print("⚠️  (vacío o muy pequeño, saltando)")
                    skipped_docs += 1
                    continue
                
                # Check if document already exists (by title)
                from sqlalchemy import select
                doc_title = doc_name.replace('.md', '')
                existing = await session.execute(
                    select(DocumentModel).where(DocumentModel.title == doc_title)
                )
                if existing.scalar_one_or_none():
                    print("⏭️  (ya existe)")
                    skipped_docs += 1
                    continue
                
                # Create document record
                doc_id = str(uuid.uuid4())
                document = DocumentModel(
                    id=doc_id,
                    title=doc_title,
                    category='documentacion_rpp',
                    user_id=system_user_id,
                    file_type='md',
                    status='processed'
                )
                session.add(document)
                await session.flush()
                
                # Split into chunks (1000 chars with 200 char overlap)
                chunk_size = 1000
                overlap = 200
                chunk_num = 0
                
                for i in range(0, len(content), chunk_size - overlap):
                    chunk_text = content[i:i+chunk_size].strip()
                    
                    if not chunk_text or len(chunk_text) < 10:
                        break
                    
                    chunk = DocumentChunkModel(
                        id=str(uuid.uuid4()),
                        document_id=doc_id,
                        chunk_number=chunk_num,
                        text=chunk_text
                    )
                    session.add(chunk)
                    chunk_num += 1
                    loaded_chunks += 1
                
                # Commit this document and its chunks
                await session.commit()
                print(f"✅ ({chunk_num} chunks, {len(content)} chars)")
                loaded_docs += 1
                
            except Exception as e:
                print(f"❌ ERROR: {str(e)[:60]}")
                await session.rollback()
                skipped_docs += 1
    
    print("\n" + "=" * 60)
    print(f"📊 RESUMEN:")
    print(f"   ✅ Documentos cargados: {loaded_docs}")
    print(f"   📋 Total chunks creados: {loaded_chunks}")
    print(f"   ⏭️  Documentos saltados: {skipped_docs}")
    print("=" * 60)
    
    return loaded_docs, loaded_chunks

async def main():
    try:
        loaded_docs, loaded_chunks = await load_rpp_documents()
        
        print(f"\n🚀 Próximo paso: Generar embeddings para {loaded_chunks} nuevos chunks...")
        print("   Ejecuta: docker exec consultarpp-celery-worker celery -A app.workers.celery_app call app.workers.celery_app.generate_embeddings_local_task --args='[null, 1000]'")
        
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
