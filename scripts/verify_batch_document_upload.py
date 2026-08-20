#!/usr/bin/env python3
"""
Verificación: el endpoint admin/chatbot/documents/upload (backend/app/routes/admin.py)
acepta múltiples archivos en un solo POST (`files: List[UploadFile]`), procesando cada
uno independientemente -- éxito, error de formato, duplicado exacto omitido y duplicado
por título renombrado -- sin que el fallo de un archivo aborte el resto del lote.

Este script llama la función de la ruta directamente (bypass de la dependencia HTTP/auth,
igual que el resto de scripts de verificación de esta sesión) porque necesita construir
`UploadFile` reales con contenido binario controlado, contra la BD Postgres real (no
sqlite -- pgvector/to_tsvector no están disponibles ahí, ver backend/tests/conftest.py:41).

Usa category='__verify_batch_upload__' para no tocar datos reales de ningún tenant, y
limpia (borra) todo lo que inserta al finalizar, incluso si una aserción falla.
"""

import sys
import os
import asyncio
import io
import logging

sys.path.insert(0, '/app')

logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

os.environ.setdefault("APP_ENV", "development")

TEST_CATEGORY = "__verify_batch_upload__"
ADMIN_USER_ID = "019f8527-cd97-7250-9a51-861c06808a0b"  # system@casmarts.internal, roles=['admin']


def make_upload_file(filename: str, content: bytes, content_type: str = "text/plain"):
    from starlette.datastructures import UploadFile as StarletteUploadFile
    return StarletteUploadFile(filename=filename, file=io.BytesIO(content), headers={"content-type": content_type})


async def main():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    from app.core.config import settings
    from app.routes.admin import upload_chatbot_document
    from app.infrastructure.models import Document, DocumentChunk

    engine = create_async_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    current_user = {"id": ADMIN_USER_ID, "roles": ["admin"]}
    all_ok = True

    async def cleanup(session):
        await session.execute(
            text("DELETE FROM document_chunks WHERE document_id IN "
                 "(SELECT id FROM documents WHERE category = :cat)"),
            {"cat": TEST_CATEGORY},
        )
        await session.execute(text("DELETE FROM documents WHERE category = :cat"), {"cat": TEST_CATEGORY})
        await session.commit()

    async with SessionLocal() as session:
        await cleanup(session)  # por si quedó basura de una corrida anterior fallida

        try:
            # === Caso 1: 3 archivos válidos y distintos en un solo POST ===
            print("=== Caso 1: lote de 3 archivos nuevos y válidos ===")
            files_batch1 = [
                make_upload_file("doc_a.txt", b"Contenido de prueba A " * 50),
                make_upload_file("doc_b.txt", b"Contenido de prueba B " * 50),
                make_upload_file("doc_c.md", b"# Contenido de prueba C\n\n" + b"lorem ipsum " * 50),
            ]
            result1 = await upload_chatbot_document(
                files=files_batch1, file=None, title=None,
                category=TEST_CATEGORY, doc_type="reglamentos",
                db=session, current_user=current_user,
            )
            print(f"  status={result1['status']} processed={result1['processed_count']} "
                  f"new={result1['new_files_count']} failed={result1['failed_count']}")
            ok1 = (result1["status"] == "success" and result1["processed_count"] == 3
                   and result1["new_files_count"] == 3 and result1["failed_count"] == 0)
            print(f"  {'✅ OK' if ok1 else '❌ FALLO'}: se esperaban 3 procesados/3 nuevos/0 fallidos")
            all_ok = all_ok and ok1

            # Verificar chunks reales en BD (no solo la respuesta del endpoint)
            chunk_count_res = await session.execute(
                text("SELECT COUNT(*) FROM document_chunks dc JOIN documents d ON dc.document_id = d.id "
                     "WHERE d.category = :cat"),
                {"cat": TEST_CATEGORY},
            )
            real_chunk_count = chunk_count_res.scalar()
            print(f"  Chunks reales insertados en BD: {real_chunk_count}")
            ok1b = real_chunk_count > 0
            print(f"  {'✅ OK' if ok1b else '❌ FALLO'}: debe haber al menos 1 chunk embebido en BD")
            all_ok = all_ok and ok1b

            # === Caso 2: re-subir el mismo contenido exacto de doc_a -> duplicate_omitted ===
            print("\n=== Caso 2: re-subida de contenido idéntico (debe omitirse, no reemplazar) ===")
            files_dup = [make_upload_file("doc_a_again.txt", b"Contenido de prueba A " * 50)]
            result2 = await upload_chatbot_document(
                files=files_dup, file=None, title=None,
                category=TEST_CATEGORY, doc_type="reglamentos",
                db=session, current_user=current_user,
            )
            print(f"  status={result2['status']} results={result2['results']}")
            ok2 = (result2["duplicate_omitted_count"] == 1 and result2["new_files_count"] == 0
                   and result2["results"][0]["status"] == "duplicate_omitted")
            print(f"  {'✅ OK' if ok2 else '❌ FALLO'}: debía omitirse por hash de contenido idéntico")
            all_ok = all_ok and ok2

            # === Caso 3: mismo título, contenido distinto -> duplicate_renamed (no error) ===
            print("\n=== Caso 3: mismo título ('doc_a.txt'), contenido distinto -> se renombra ===")
            files_rename = [make_upload_file("doc_a.txt", b"Contenido COMPLETAMENTE DIFERENTE " * 60)]
            result3 = await upload_chatbot_document(
                files=files_rename, file=None, title=None,
                category=TEST_CATEGORY, doc_type="reglamentos",
                db=session, current_user=current_user,
            )
            print(f"  status={result3['status']} results={result3['results']}")
            r3 = result3["results"][0]
            ok3 = (r3["status"] == "duplicate_renamed" and r3["document"]["title"] != "doc_a.txt"
                   and r3["document"]["title"].startswith("doc_a.txt"))
            print(f"  {'✅ OK' if ok3 else '❌ FALLO'}: título esperado con sufijo de fecha, obtenido: "
                  f"{r3['document']['title'] if 'document' in r3 else '(sin document)'}")
            all_ok = all_ok and ok3

            # === Caso 4: lote mixto -- 1 válido + 1 formato no soportado -> el válido NO se pierde ===
            print("\n=== Caso 4: lote mixto (1 válido + 1 formato rechazado) ===")
            files_mixed = [
                make_upload_file("doc_d.txt", b"Contenido de prueba D " * 50),
                make_upload_file("imagen.png", b"\x89PNG\r\n\x1a\nfakepngbytes"),
            ]
            result4 = await upload_chatbot_document(
                files=files_mixed, file=None, title=None,
                category=TEST_CATEGORY, doc_type="reglamentos",
                db=session, current_user=current_user,
            )
            print(f"  status={result4['status']} processed={result4['processed_count']} "
                  f"failed={result4['failed_count']} results={result4['results']}")
            ok4 = (result4["processed_count"] == 1 and result4["failed_count"] == 1
                   and any(r["status"] == "success" for r in result4["results"])
                   and any(r["status"] == "error" for r in result4["results"]))
            print(f"  {'✅ OK' if ok4 else '❌ FALLO'}: el archivo válido debía procesarse pese al error del otro")
            all_ok = all_ok and ok4

        finally:
            await cleanup(session)
            verify_res = await session.execute(
                text("SELECT COUNT(*) FROM documents WHERE category = :cat"), {"cat": TEST_CATEGORY}
            )
            remaining = verify_res.scalar()
            print(f"\n=== Limpieza: documentos de prueba restantes tras cleanup: {remaining} "
                  f"({'✅ OK' if remaining == 0 else '❌ QUEDÓ BASURA DE PRUEBA'}) ===")
            all_ok = all_ok and (remaining == 0)

    print(f"\n{'='*60}")
    print(f"RESULTADO FINAL: {'✅ TODOS LOS CASOS PASARON' if all_ok else '❌ HAY CASOS FALLIDOS'}")
    print(f"{'='*60}")
    return all_ok


if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
