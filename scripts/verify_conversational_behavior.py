#!/usr/bin/env python3
"""
Verificación manual (contra BD/LLM reales) de:
  A) Preguntas de aclaración cuando la consulta es ambigua pero válida.
  B) Sugerencias de seguimiento (`suggestions`) al final de cada respuesta.
  C) Que las reglas de rechazo de temas fuera de dominio SIGUEN funcionando
     (el sufijo de aclaración no debe convertirse en una vía de escape).
  D) El interruptor por tema `show_provider_debug` (config_metadata) sí quita
     el sufijo "*LLM: ...*" cuando está apagado.

No se puede probar esto con pytest/sqlite: el fixture de tests es sqlite en
memoria y no soporta pgvector/to_tsvector (ver tests/conftest.py). Este script
corre contra la BD de desarrollo real, dentro del contenedor
consulta-smart-backend (sys.path apunta a /app, que ES el paquete backend/).
"""

import sys
import os
import asyncio
import logging

sys.path.insert(0, '/app')

logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

os.environ.setdefault("APP_ENV", "development")

AMBIGUOUS_QUERY = "¿Cuánto cuesta el trámite y cuánto tarda?"
NORMAL_QUERY = "¿Qué documentos necesito para hacer un trámite?"
OFFTOPIC_QUERY = "¿Cuál es la capital de Francia?"


async def main():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text, select
    from app.core.config import settings
    from app.application.services.chat_service import ChatService
    from app.infrastructure.models import ChatbotProfile

    engine = create_async_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    chat_service = ChatService()
    results = []

    async with SessionLocal() as session:
        profile_ids = [r[0] for r in (await session.execute(text("SELECT id FROM chatbot_profiles ORDER BY id"))).fetchall()]
        print(f"Perfiles reales encontrados: {profile_ids}\n")

        for pid in profile_ids:
            print("=" * 100)
            print(f"PERFIL: {pid}")
            print("=" * 100)
            row = {"profile": pid}

            # --- A) Aclaración ---
            r1 = await chat_service.process_query(query=AMBIGUOUS_QUERY, session_id=None, db_session=session, filters={"category": pid})
            print(f"\n[A] Consulta ambigua: {AMBIGUOUS_QUERY!r}")
            print(f"    Respuesta: {r1.get('response')!r}")
            looks_like_question = r1.get("response", "").strip().endswith("?") or "¿" in r1.get("response", "")
            row["A_pregunta_aclaracion"] = looks_like_question
            print(f"    -> ¿Parece pregunta de aclaración? {looks_like_question}")

            # --- B) Sugerencias ---
            r2 = await chat_service.process_query(query=NORMAL_QUERY, session_id=None, db_session=session, filters={"category": pid})
            print(f"\n[B] Consulta normal: {NORMAL_QUERY!r}")
            print(f"    Respuesta: {r2.get('response')!r}")
            print(f"    Suggestions: {r2.get('suggestions')!r}")
            marker_leaked = "SUGERENCIAS_JSON" in r2.get("response", "")
            row["B_suggestions_no_vacio"] = bool(r2.get("suggestions"))
            row["B_marker_no_filtrado"] = not marker_leaked
            print(f"    -> ¿suggestions no vacío? {bool(r2.get('suggestions'))} | ¿marcador NO filtrado al texto visible? {not marker_leaked}")

            # --- C) Rechazo fuera de dominio sigue firme ---
            r3 = await chat_service.process_query(query=OFFTOPIC_QUERY, session_id=None, db_session=session, filters={"category": pid})
            print(f"\n[C] Consulta fuera de tema: {OFFTOPIC_QUERY!r}")
            print(f"    Respuesta: {r3.get('response')!r}")
            resp_lower = r3.get("response", "").lower()
            rejected = any(kw in resp_lower for kw in ["no puedo", "limitad", "fuera de", "no está relacionad", "rechaz"])
            row["C_rechazo_firme"] = rejected
            print(f"    -> ¿Se ve como rechazo (no respondió la trivia)? {rejected}")

            results.append(row)
            print()

        # --- D) Interruptor show_provider_debug ---
        print("=" * 100)
        print("D) INTERRUPTOR show_provider_debug (config_metadata)")
        print("=" * 100)
        test_pid = profile_ids[0]
        stmt = select(ChatbotProfile).where(ChatbotProfile.id == test_pid)
        profile = (await session.execute(stmt)).scalars().first()
        original_metadata = dict(profile.config_metadata or {})

        try:
            profile.config_metadata = {**original_metadata, "show_provider_debug": False}
            await session.commit()
            r4 = await chat_service.process_query(query=NORMAL_QUERY, session_id=None, db_session=session, filters={"category": test_pid})
            print(f"Perfil de prueba: {test_pid} con show_provider_debug=False")
            print(f"    show_provider_debug devuelto por process_query: {r4.get('show_provider_debug')}")
            d_ok = r4.get("show_provider_debug") is False
            print(f"    -> ¿process_query respeta el flag? {d_ok}")
        finally:
            # Restaurar el estado original del perfil de prueba, pase lo que pase.
            profile.config_metadata = original_metadata
            await session.commit()
            print(f"    (config_metadata de '{test_pid}' restaurado a su valor original)")

    # --- Resumen ---
    print("\n" + "=" * 100)
    print("RESUMEN")
    print("=" * 100)
    header = f"{'perfil':<20} {'A:aclaración':<14} {'B:suggestions':<15} {'B:marker_ok':<13} {'C:rechazo':<10}"
    print(header)
    print("-" * len(header))
    all_ok = True
    for row in results:
        print(f"{row['profile']:<20} {str(row['A_pregunta_aclaracion']):<14} {str(row['B_suggestions_no_vacio']):<15} {str(row['B_marker_no_filtrado']):<13} {str(row['C_rechazo_firme']):<10}")
        if not (row['B_marker_no_filtrado'] and row['C_rechazo_firme']):
            all_ok = False
    print(f"\nNota: 'A:aclaración' y 'B:suggestions' son heurísticas de inspección automática (buscan '?'/'¿'\n"
          f"y lista no vacía) -- revisar el texto completo impreso arriba para confirmar con criterio humano.\n"
          f"'B:marker_ok' y 'C:rechazo' sí son verificaciones estrictas (no debe filtrarse el marcador\n"
          f"interno, y el rechazo fuera de dominio no debe romperse).")
    print(f"\n{'✅ TODO EN ORDEN' if all_ok else '⚠️  REVISAR heurísticas en falso arriba'} (D: ver arriba)")
    return all_ok


if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
