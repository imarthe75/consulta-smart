#!/usr/bin/env python3
"""
Verificación: la búsqueda RAG híbrida (vectorial + texto) de KnowledgeBase
no debe devolver chunks de una `category` distinta a la solicitada en `filters`.

Contexto: se detectó en producción (2026-08-19) que el chat del tenant "teca"
mostraba como "Fuentes Oficiales" documentos de otros temas (ej. RPP/IRCEP).
Causa: `search_in_knowledge_async` aplicaba `filters["category"]` en la rama de
búsqueda por texto pero NUNCA en la rama de búsqueda vectorial (pgvector), que
consultaba TODA la tabla `document_chunks` sin restricción de tenant.

Este script corre contra la base de datos REAL (no sqlite/mock, que no soporta
pgvector/to_tsvector) para probar el fix con datos de producción reales.
"""

import sys
import os
import asyncio
import logging

# Dentro del contenedor consulta-smart-backend, /app ES el paquete backend/
# (bind mount directo); /app/scripts es un mount aparte para este directorio.
sys.path.insert(0, '/app')

logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

os.environ.setdefault("APP_ENV", "development")


async def main():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    from app.core.config import settings
    from app.infrastructure.knowledge_base import KnowledgeBase

    engine = create_async_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        # 1. Confirmar que existen documentos en al menos 2 categorías distintas,
        #    con embeddings, para que la prueba sea real (no un falso positivo por
        #    falta de datos).
        cats = await session.execute(text(
            "SELECT d.category, COUNT(*) FROM document_chunks dc "
            "JOIN documents d ON dc.document_id = d.id "
            "WHERE dc.embedding IS NOT NULL AND d.is_active = true "
            "GROUP BY d.category ORDER BY 2 DESC"
        ))
        rows = cats.fetchall()
        print("=== Categorías con chunks embebidos activos ===")
        for cat, count in rows:
            print(f"  {cat!r}: {count} chunks")

        categories_present = {r[0] for r in rows}
        if "teca" not in categories_present:
            print("\n❌ ABORTA: no hay documentos activos con category='teca' en esta BD; "
                  "no se puede probar el escenario real reportado.")
            return False
        if len(categories_present) < 2:
            print("\n❌ ABORTA: solo existe una categoría; la prueba de fuga entre "
                  "tenants no es significativa sin al menos 2.")
            return False

        # 2. Query genérica, del tipo que plausiblemente matchea semánticamente
        #    contra CUALQUIER tema (trámites/requisitos son vocabulario común
        #    entre rpp/ircep/teca/etc.) -- es exactamente el tipo de consulta que
        #    antes del fix arrastraba resultados de otras categorías por la rama
        #    vectorial.
        query = "cuáles son los requisitos y el procedimiento para este trámite"

        kb = KnowledgeBase()

        print(f"\n=== Búsqueda CON filtro category='teca' (comportamiento real tras el fix) ===")
        docs_filtered = await kb.search_in_knowledge_async(
            query, session=session, top_k=5, filters={"category": "teca", "is_active": True}
        )
        cats_returned = {d["category"] for d in docs_filtered}
        for d in docs_filtered:
            print(f"  [{d['method']}] category={d['category']!r} title={d['title']!r}")
        print(f"Categorías presentes en el resultado: {cats_returned}")

        leaked = cats_returned - {"teca"}
        if leaked:
            print(f"\n❌ FALLO: la búsqueda filtrada por 'teca' devolvió categorías ajenas: {leaked}")
            return False
        if not docs_filtered:
            print("\n⚠️  ADVERTENCIA: la búsqueda no devolvió resultados (ni propios ni ajenos) "
                  "-- no es una fuga, pero tampoco prueba el filtro positivamente. "
                  "Reintenta con una query más cercana al contenido real de 'teca'.")
        else:
            print("\n✅ OK: todos los resultados pertenecen a category='teca', sin fuga de otros tenants.")

        # 3. Control negativo: la MISMA query sin filtro de category, para probar
        #    que el índice vectorial sí tiene matches de otras categorías para esta
        #    consulta -- es decir, que el escenario de fuga era real (no solo
        #    teórico) y que la rama vectorial sin filtro (comportamiento previo al
        #    fix) efectivamente los habría devuelto.
        print(f"\n=== Búsqueda SIN filtro de category (control negativo, simula el bug previo) ===")
        docs_unfiltered = await kb.search_in_knowledge_async(
            query, session=session, top_k=5, filters={"is_active": True}
        )
        cats_unfiltered = {d["category"] for d in docs_unfiltered}
        for d in docs_unfiltered:
            print(f"  [{d['method']}] category={d['category']!r} title={d['title']!r}")
        print(f"Categorías presentes sin filtro: {cats_unfiltered}")
        if cats_unfiltered - {"teca"}:
            print("✅ Confirma que sin el filtro de category SÍ aparecen otros tenants para esta "
                  "misma query -- el fix (paso 2 arriba) es lo que evita la fuga, no una casualidad "
                  "de que esta query no tuviera matches ajenos.")
        else:
            print("ℹ️  Esta query en particular no tuvo matches de otras categorías incluso sin "
                  "filtro -- no invalida el fix, solo que esta consulta puntual no dispara el caso.")

        return True


if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
