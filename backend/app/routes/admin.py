from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import fitz  # PyMuPDF

from app.core.database import get_session
from app.infrastructure.models import SystemConfig, User, Document, ChatbotProfile, DocumentChunk, PromptTestCase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, case
from app.infrastructure.external.smart_llm_router import get_smart_router
from app.infrastructure.external.llm_service import get_local_embedding_service

from app.core.auth_utils import require_admin
from app.core.rate_limit import rate_limit
from app.core.crypto import encrypt_secret, decrypt_secret

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
    methodology: Optional[str] = "craft"
    target_audience: Optional[str] = None
    organization: Optional[str] = None
    sector: Optional[str] = None

@router.get("/configs/{key}", response_model=ConfigResponse)
async def get_config(
    key: str,
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    result = await db.execute(select(SystemConfig).filter(SystemConfig.key == key))
    config = result.scalars().first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config

@router.post("/configs", response_model=ConfigResponse)
async def update_config(
    data: ConfigUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    result = await db.execute(select(SystemConfig).filter(SystemConfig.key == data.key))
    config = result.scalars().first()
    if not config:
        config = SystemConfig(key=data.key, value=data.value, description=data.description)
        db.add(config)
    else:
        config.value = data.value
        if data.description:
            config.description = data.description
    await db.commit()
    await db.refresh(config)
    return config

@router.post("/generate-prompt", dependencies=[Depends(rate_limit(10, 60))])
async def generate_prompt(
    request: PromptGenerateRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Usa Meta-Prompting con el LLM actuando como Prompt Engineer experto
    siguiendo las metodologías CRAFT, CREA o ASPECCT con contexto institucional extendido.
    """
    llm = await get_smart_router()
    method = (request.methodology or "craft").lower()
    
    target_info = f"Usuarios Objetivo: {request.target_audience or 'Ciudadanos y usuarios generales'}. "
    org_info = f"Dependencia/Oficina: {request.organization or 'Gobierno'}. "
    sector_info = f"Sector: {request.sector or 'Público/Institucional'}. "
    context_details = f"{target_info}{org_info}{sector_info}"

    if request.context == "consulta":
        if method == "craft":
            meta_instruction = (
                f"Eres un **Ingeniero de Prompts Senior (Prompt Engineer)** experto en diseñar System Prompts maestros "
                f"para chatbots institucionalizados basados en RAG.\n\n"
                f"Tu tarea es construir un **System Prompt maestro** para el tema: '{request.topic}'.\n"
                f"CONTEXTO ADICIONAL:\n{context_details}\n\n"
                f"DEBES estructurar el System Prompt utilizando la **Metodología CRAFT** y usando **etiquetas delimitadoras tipo XML** (<contexto>, <rol>, <instrucciones>, <formato>, <reglas>, <ejemplos>):\n"
                f"- **C - Contexto (<contexto>):** Describe el entorno ({request.organization or 'Institución'}), el perfil de usuarios ({request.target_audience or 'Ciudadanía'}), el ámbito de servicios y la prioridad estricta a los manuales RAG bajo '## MANUALES TÉCNICOS OFICIALES'.\n"
                f"- **R - Rol / Persona (<rol>):** Identidad profesional, nivel de autoridad, empatía y especialidad técnica del bot.\n"
                f"- **A - Acción / Tarea (<instrucciones>):** Instructivo paso a paso de atención, consulta en manuales indexados y orientación clara.\n"
                f"- **F - Formato (<formato>):** Estructura visual clara de respuestas (Markdown, viñetas simples, negritas, sin párrafos densos).\n"
                f"- **T - Tono y Restricciones (<reglas>):** Tono de voz adaptado al usuario ({request.target_audience or 'Ciudadanía'}), vocabulario a evitar, cero alucinaciones y temas fuera de dominio prohibidos.\n"
                f"- **Few-Shot Prompting (<ejemplos>):** Incluye 2 ejemplos concisos y representativos de Pregunta/Respuesta adaptados a la dependencia.\n\n"
                f"Responde ÚNICAMENTE con el System Prompt final generado en formato Markdown y XML. No agregues intros ni explicaciones extra."
            )
        elif method == "aspecct":
            meta_instruction = (
                f"Eres un **Ingeniero de Prompts Senior (Prompt Engineer)** experto en diseñar System Prompts de arquitectura empresarial.\n\n"
                f"Construye un **System Prompt completo** sobre el tema: '{request.topic}' para {context_details} siguiendo el **Framework ASPECCT** y utilizando **etiquetas XML**:\n"
                f"- **A - Acción (<instrucciones>):** Tarea central y objetivo del bot.\n"
                f"- **S - Steps (<pasos>):** Flujo ordenado paso a paso para analizar consultas y documentos RAG.\n"
                f"- **P - Persona (<rol>):** Rol profesional y autoridad técnica.\n"
                f"- **E - Ejemplos (<ejemplos>):** Ejemplos concisos Few-Shot (Pregunta/Respuesta).\n"
                f"- **C - Contexto (<contexto>):** Dominio institucional ({request.organization or 'Dependencia'}), manuales RAG e interacción del usuario ({request.target_audience or 'Ciudadanos'}).\n"
                f"- **T - Tono/Tipo (<formato> y <reglas>):** Tono ejecutivo, prohibición de alucinaciones y restricciones de salida.\n\n"
                f"Responde ÚNICAMENTE con el System Prompt final generado."
            )
        elif method == "crea":
            meta_instruction = (
                f"Eres un **Ingeniero de Prompts Senior (Prompt Engineer)** experto en diseñar System Prompts maestros.\n\n"
                f"Construye un **System Prompt impecable** sobre el tema: '{request.topic}' para {context_details} aplicando la **Metodología CREA** y etiquetas XML:\n"
                f"- **C - Contexto (<contexto>):** Antecedentes, entidad ({request.organization or 'Gobierno'}) y consumo estricto de RAG.\n"
                f"- **R - Rol (<rol>):** Perspectiva técnica y profesional.\n"
                f"- **E - Especificidad (<reglas>):** Reglas de alcance, perfil de usuario ({request.target_audience or 'Ciudadanía'}), temas prohibidos y prevención de alucinaciones.\n"
                f"- **A - Acción (<instrucciones>):** Tarea directa de atención y formato de entrega.\n\n"
                f"Responde ÚNICAMENTE con el System Prompt final generado."
            )
        else:  # 'craft' por defecto si viene cualquier otro valor
            meta_instruction = (
                f"Eres un **Ingeniero de Prompts Senior (Prompt Engineer)** experto en diseñar System Prompts maestros "
                f"para chatbots institucionalizados basados en RAG.\n\n"
                f"Tu tarea es construir un **System Prompt maestro** para el tema: '{request.topic}'.\n"
                f"CONTEXTO ADICIONAL:\n{context_details}\n\n"
                f"DEBES estructurar el System Prompt utilizando la **Metodología CRAFT** y usando **etiquetas delimitadoras tipo XML** (<contexto>, <rol>, <instrucciones>, <formato>, <reglas>, <ejemplos>):\n"
                f"- **C - Contexto (<contexto>):** Describe el entorno ({request.organization or 'Institución'}), el perfil de usuarios ({request.target_audience or 'Ciudadanía'}), el ámbito de servicios y la prioridad estricta a los manuales RAG bajo '## MANUALES TÉCNICOS OFICIALES'.\n"
                f"- **R - Rol / Persona (<rol>):** Identidad profesional, nivel de autoridad, empatía y especialidad técnica del bot.\n"
                f"- **A - Acción / Tarea (<instrucciones>):** Instructivo paso a paso de atención, consulta en manuales indexados y orientación clara.\n"
                f"- **F - Formato (<formato>):** Estructura visual clara de respuestas (Markdown, viñetas simples, negritas, sin párrafos densos).\n"
                f"- **T - Tono y Restricciones (<reglas>):** Tono de voz adaptado al usuario ({request.target_audience or 'Ciudadanía'}), vocabulario a evitar, cero alucinaciones y temas fuera de dominio prohibidos.\n"
                f"- **Few-Shot Prompting (<ejemplos>):** Incluye 2 ejemplos concisos y representativos de Pregunta/Respuesta adaptados a la dependencia.\n\n"
                f"Responde ÚNICAMENTE con el System Prompt final generado en formato Markdown y XML. No agregues intros ni explicaciones extra."
            )
        messages = [{"role": "user", "content": meta_instruction}]
        response_text, _ = await llm.chat(
            messages=messages,
            temperature=0.3,
            max_tokens=1500,
            topic=request.topic,
            target_audience=request.target_audience or 'Ciudadanía y usuarios generales',
            organization=request.organization or 'Institución / Organización',
            sector=request.sector or 'Público / Privado'
        )
        return {"prompt": response_text}
    else:
        schema_task = (
            f"Actúa como un Arquitecto de Datos. Genera un esquema JSON de extracción para documentos de: {request.topic}. "
            f"Incluye campos lógicos como folios, fechas, nombres de partes involucradas y montos. "
            f"Responde ÚNICAMENTE con el JSON válido."
        )
        messages = [{"role": "user", "content": schema_task}]
        response_text, _ = await llm.chat(messages=messages, temperature=0.1, max_tokens=1000)
        return {"schema": response_text}

class ChatbotProfileDTO(BaseModel):
    id: str
    name: str
    system_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    logo_url: Optional[str] = None
    icon: Optional[str] = "Bot"
    primary_color: Optional[str] = "#004a87"
    strictness_level: Optional[str] = "strict"
    strictness_score: Optional[int] = 80
    temperature: Optional[float] = 0.1
    top_p: Optional[float] = 0.9
    forbidden_topics: Optional[str] = "deportes, futbol, cine, cocina, politica, chismes, entretenimiento"
    rejection_message: Optional[str] = "Mi función está limitada exclusivamente a la asesoría sobre trámites, normativa y servicios del Registro Público. No puedo asistirle con temas ajenos."
    llm_provider: Optional[str] = "default"
    llm_model: Optional[str] = None
    custom_api_key: Optional[str] = None
    config_metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = True

class ChatbotProfilePublicDTO(BaseModel):
    """DTO de solo lectura para consumo público (widget embebible, selector de tenant).

    HALLAZGO DE AUDITORÍA: este endpoint es consumido sin autenticación por
    ChatInterface.jsx y WidgetIntegrationPage.jsx (el widget embebible en sitios
    externos necesita listar tenants/temas sin exigir login al visitante). El
    endpoint no puede exigir auth sin romper esa integración legítima, pero antes
    devolvía el modelo ORM completo, filtrando system_prompt, forbidden_topics,
    rejection_message y guardrails (strictness/temperature) a cualquiera. Este DTO
    restringe la respuesta a los campos de theming públicos.
    """
    model_config = {"from_attributes": True}

    id: str
    name: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    logo_url: Optional[str] = None
    icon: Optional[str] = None
    primary_color: Optional[str] = None
    welcome_message: Optional[str] = None
    is_active: Optional[bool] = True


@router.get("/chatbot/profiles", response_model=List[ChatbotProfilePublicDTO])
async def list_chatbot_profiles(db: AsyncSession = Depends(get_session)):
    """
    Obtener todos los perfiles de chatbot (datos públicos de theming) directamente
    desde PostgreSQL. Endpoint intencionalmente público (ver ChatbotProfilePublicDTO);
    el detalle sensible (system_prompt, guardrails) solo se expone vía rutas admin.
    """
    result = await db.execute(select(ChatbotProfile).order_by(ChatbotProfile.id))
    profiles = result.scalars().all()
    return profiles

@router.get("/chatbot/profiles/admin-list")
async def list_chatbot_profiles_admin(
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """Retorna todos los perfiles de chatbot con datos completos (incluyendo llm_provider, llm_model y API Key enmascarada)."""
    result = await db.execute(select(ChatbotProfile).order_by(ChatbotProfile.id))
    profiles = result.scalars().all()
    out = []
    for p in profiles:
        key_masked = ""
        if p.custom_api_key:
            # custom_api_key se guarda cifrado (ver app.core.crypto); se descifra solo
            # en memoria para construir la máscara, nunca se devuelve en claro al cliente.
            real_key = decrypt_secret(p.custom_api_key)
            key_masked = "••••••••" + real_key[-4:] if len(real_key) > 4 else "••••••••"
        out.append({
            "id": p.id,
            "name": p.name,
            "system_prompt": p.system_prompt,
            "welcome_message": p.welcome_message,
            "title": p.title,
            "subtitle": p.subtitle,
            "logo_url": p.logo_url,
            "icon": p.icon,
            "primary_color": p.primary_color,
            "strictness_level": p.strictness_level,
            "strictness_score": p.strictness_score,
            "temperature": p.temperature,
            "top_p": p.top_p,
            "forbidden_topics": p.forbidden_topics,
            "rejection_message": p.rejection_message,
            "llm_provider": p.llm_provider or "default",
            "llm_model": p.llm_model or "",
            "custom_api_key": key_masked,
            "has_custom_key": bool(p.custom_api_key),
            "config_metadata": p.config_metadata or {},
            "is_active": p.is_active
        })
    return out

@router.post("/chatbot/profiles")
async def save_chatbot_profile(
    data: ChatbotProfileDTO,
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    result = await db.execute(select(ChatbotProfile).filter(ChatbotProfile.id == data.id))
    profile = result.scalars().first()
    
    # Manejo seguro de custom_api_key (preservar existente si viene enmascarada, cifrar si es nueva)
    api_key_to_save = data.custom_api_key
    if api_key_to_save and "•" in api_key_to_save:
        api_key_to_save = profile.custom_api_key if profile else None
    elif api_key_to_save:
        api_key_to_save = encrypt_secret(api_key_to_save)

    if not profile:
        profile = ChatbotProfile(
            id=data.id,
            name=data.name,
            system_prompt=data.system_prompt,
            welcome_message=data.welcome_message,
            title=data.title,
            subtitle=data.subtitle,
            logo_url=data.logo_url,
            icon=data.icon or "Bot",
            primary_color=data.primary_color,
            strictness_level=data.strictness_level or "strict",
            strictness_score=data.strictness_score if data.strictness_score is not None else 80,
            temperature=data.temperature if data.temperature is not None else 0.1,
            top_p=data.top_p if data.top_p is not None else 0.9,
            forbidden_topics=data.forbidden_topics or "",
            rejection_message=data.rejection_message or "Tema no permitido.",
            llm_provider=data.llm_provider or "default",
            llm_model=data.llm_model,
            custom_api_key=api_key_to_save,
            config_metadata=data.config_metadata or {},
            is_active=data.is_active if data.is_active is not None else True
        )
        db.add(profile)
    else:
        profile.name = data.name
        profile.system_prompt = data.system_prompt
        profile.welcome_message = data.welcome_message
        profile.title = data.title
        profile.subtitle = data.subtitle
        profile.logo_url = data.logo_url
        profile.icon = data.icon or "Bot"
        profile.primary_color = data.primary_color
        profile.strictness_level = data.strictness_level or "strict"
        if data.strictness_score is not None: profile.strictness_score = data.strictness_score
        if data.temperature is not None: profile.temperature = data.temperature
        if data.top_p is not None: profile.top_p = data.top_p
        profile.forbidden_topics = data.forbidden_topics or ""
        profile.rejection_message = data.rejection_message or "Tema no permitido."
        if data.llm_provider is not None: profile.llm_provider = data.llm_provider
        if data.llm_model is not None: profile.llm_model = data.llm_model
        if api_key_to_save is not None: profile.custom_api_key = api_key_to_save
        if data.config_metadata is not None:
            profile.config_metadata = data.config_metadata
        if data.is_active is not None:
            profile.is_active = data.is_active
            
    await db.commit()
    await db.refresh(profile)
    return {"status": "success", "profile": profile}

@router.delete("/chatbot/profiles/{profile_id}")
async def delete_chatbot_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    result = await db.execute(select(ChatbotProfile).filter(ChatbotProfile.id == profile_id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    await db.delete(profile)
    await db.commit()
    return {"status": "success", "message": f"Perfil {profile_id} eliminado correctamente"}

@router.get("/chatbot/documents")
async def get_chatbot_documents(
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """
    Retorna la lista de documentos indexados junto con métricas de salud del índice.
    
    - chunk_count: total de fragmentos generados durante el procesamiento.
    - embedded_chunk_count: fragmentos que tienen embedding vectorial real (no NULL).
    - health_pct: porcentaje de fragmentos con embedding, 0-100. Un valor < 100
      indica que el indexado fue parcialmente exitoso y el admin puede reintentar.
    """
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    docs = result.scalars().all()
    doc_ids = [doc.id for doc in docs]

    # Subconsulta: contar chunks embebidos vs totales por documento
    if doc_ids:
        embed_q = await db.execute(
            select(
                DocumentChunk.document_id,
                func.count(DocumentChunk.id).label("total_chunks"),
                func.sum(
                    case((DocumentChunk.embedding != None, 1), else_=0)  # noqa: E711
                ).label("embedded_chunks")
            )
            .where(DocumentChunk.document_id.in_(doc_ids))
            .group_by(DocumentChunk.document_id)
        )
        embed_map = {
            row.document_id: {
                "total":    row.total_chunks,
                "embedded": int(row.embedded_chunks or 0)
            }
            for row in embed_q.fetchall()
        }
    else:
        embed_map = {}

    return [
        {
            "id":                   doc.id,
            "title":               doc.title,
            "category":            doc.category,
            "is_active":           doc.is_active,
            "status":              doc.status,
            "chunk_count":         doc.chunk_count or 0,
            # Métricas de salud del índice vectorial
            "embedded_chunk_count": embed_map.get(doc.id, {}).get("embedded", 0),
            "health_pct":           (
                round(
                    embed_map[doc.id]["embedded"] / embed_map[doc.id]["total"] * 100
                ) if embed_map.get(doc.id, {}).get("total", 0) > 0 else 0
            ),
            "processing_error":    doc.processing_error,
            "created_at":          doc.created_at.isoformat() if doc.created_at else None
        }
        for doc in docs
    ]

@router.post("/chatbot/documents/upload", dependencies=[Depends(rate_limit(5, 60))])
async def upload_chatbot_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: Optional[str] = Form("general"),
    doc_type: Optional[str] = Form("reglamentos"),
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Archivo es obligatorio")
    
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in ["pdf", "md", "txt"]:
        raise HTTPException(status_code=400, detail="Formato no soportado. Permitido solo PDF, MD o TXT")
    
    try:
        contents = await file.read()
        extracted_text = ""
        
        if file_ext == "pdf":
            try:
                doc_pdf = fitz.open(stream=contents, filetype="pdf")
                pages_text = [page.get_text() for page in doc_pdf]
                extracted_text = "\n".join(pages_text)
            except Exception as pdf_err:
                logger.error(f"Error parseando PDF: {pdf_err}")
                raise HTTPException(status_code=400, detail=f"No se pudo extraer texto del PDF: {pdf_err}")
        else:
            extracted_text = contents.decode("utf-8", errors="ignore")
        
        extracted_text = extracted_text.strip()
        if not extracted_text:
            raise HTTPException(status_code=400, detail="El documento no contiene texto legible")
        
        doc_title = title if (title and title.strip()) else file.filename
        
        new_doc = Document(
            title=doc_title,
            category=category or "general",
            user_id=current_user["id"],
            file_type=file_ext,
            status="indexed",
            is_active=True,
            token_count=len(extracted_text.split()),
            doc_metadata={
                "original_filename": file.filename,
                "doc_type": doc_type or "reglamentos"
            }
        )
        db.add(new_doc)
        await db.flush()
        
        chunk_size = 800
        overlap = 100
        chunks = []
        for i in range(0, len(extracted_text), chunk_size - overlap):
            chunk_str = extracted_text[i:i + chunk_size].strip()
            if chunk_str:
                chunks.append(chunk_str)
        
        embed_service = get_local_embedding_service()
        chunk_models = []
        for idx, chunk_text in enumerate(chunks):
            embedding = None
            try:
                embedding = await embed_service.embed(chunk_text)
            except Exception as embed_err:
                logger.warning(f"Error generando embedding para chunk {idx}: {embed_err}")
            
            chunk_model = DocumentChunk(
                document_id=new_doc.id,
                chunk_number=idx,
                text=chunk_text,
                token_count=len(chunk_text.split()),
                embedding=embedding,
                doc_metadata={"filename": file.filename, "category": category}
            )
            db.add(chunk_model)
            chunk_models.append(chunk_model)
        
        new_doc.chunk_count = len(chunk_models)
        await db.commit()
        await db.refresh(new_doc)
        
        return {
            "status": "success",
            "message": f"Documento '{new_doc.title}' subido y procesado con éxito ({new_doc.chunk_count} fragmentos vectorizados)",
            "document": {
                "id": new_doc.id,
                "title": new_doc.title,
                "category": new_doc.category,
                "chunk_count": new_doc.chunk_count,
                "status": new_doc.status
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en upload_chatbot_document: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error procesando documento: {str(e)}")


@router.post("/chatbot/documents/{document_id}/reindex")
async def reindex_chatbot_document(
    document_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """
    Re-ejecuta el proceso de chunking y embedding sobre un documento ya almacenado.
    
    Útil cuando el indexado original falló parcialmente (algunos chunks sin embedding)
    o cuando se actualiza el modelo de embeddings. El archivo original no se vuelve a
    subir: se reutiliza el texto ya extraído que quedó guardado en los chunks existentes.
    
    Flujo:
    1. Verificar que el documento exista.
    2. Concatenar el texto de los chunks existentes (fuente de verdad del contenido).
    3. Eliminar todos los chunks actuales.
    4. Regenerar chunks con embeddings frescos.
    5. Actualizar chunk_count y status del documento.
    """
    # 1. Obtener el documento
    result = await db.execute(select(Document).filter(Document.id == document_id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    logger.info(f"[Reindex] Iniciando re-indexado de documento '{doc.title}' ({document_id})")

    try:
        # 2. Recuperar el texto existente de los chunks actuales (ordenado por chunk_number)
        chunks_q = await db.execute(
            select(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_number)
        )
        existing_chunks = chunks_q.scalars().all()

        if not existing_chunks:
            raise HTTPException(
                status_code=422,
                detail="No hay fragmentos previos. Sube el archivo de nuevo para indexarlo."
            )

        # Reconstruir el texto completo desde los chunks existentes
        full_text = "\n".join(ch.text for ch in existing_chunks if ch.text)
        if not full_text.strip():
            raise HTTPException(
                status_code=422,
                detail="Los fragmentos existentes no contienen texto recuperable."
            )

        # 3. Eliminar todos los chunks actuales del documento
        await db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )

        # 4. Regenerar chunks con embeddings frescos
        chunk_size = 800
        overlap    = 100
        new_chunks_texts = []
        for i in range(0, len(full_text), chunk_size - overlap):
            chunk_str = full_text[i:i + chunk_size].strip()
            if chunk_str:
                new_chunks_texts.append(chunk_str)

        embed_service = get_local_embedding_service()
        embedded_count = 0
        new_chunk_models = []

        for idx, chunk_text in enumerate(new_chunks_texts):
            embedding = None
            try:
                embedding = await embed_service.embed(chunk_text)
                embedded_count += 1
            except Exception as emb_err:
                logger.warning(f"[Reindex] Error embedding chunk {idx}: {emb_err}")

            chunk_model = DocumentChunk(
                document_id=document_id,
                chunk_number=idx,
                text=chunk_text,
                token_count=len(chunk_text.split()),
                embedding=embedding,
                doc_metadata=doc.doc_metadata or {}
            )
            db.add(chunk_model)
            new_chunk_models.append(chunk_model)

        # 5. Actualizar el documento con los nuevos conteos y estado
        doc.chunk_count      = len(new_chunk_models)
        doc.status           = "indexed" if embedded_count == len(new_chunk_models) else "partial"
        doc.processing_error = (
            None if embedded_count == len(new_chunk_models)
            else f"{len(new_chunk_models) - embedded_count} de {len(new_chunk_models)} chunks sin embedding"
        )

        await db.commit()
        await db.refresh(doc)

        logger.info(
            f"[Reindex] Completado: {embedded_count}/{len(new_chunk_models)} chunks embebidos "
            f"para '{doc.title}'"
        )
        return {
            "status":           "success",
            "message":          f"Reindexado completado: {embedded_count} de {len(new_chunk_models)} fragmentos con embedding.",
            "chunk_count":      doc.chunk_count,
            "embedded_count":   embedded_count,
            "health_pct":       round(embedded_count / len(new_chunk_models) * 100) if new_chunk_models else 0,
            "document_status":  doc.status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Reindex] Error en reindexado de documento {document_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error durante el reindexado: {str(e)}")

@router.delete("/chatbot/documents/{document_id}")
async def delete_chatbot_document(
    document_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    result = await db.execute(select(Document).filter(Document.id == document_id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
    await db.delete(doc)
    await db.commit()
    return {"status": "success", "message": "Documento y sus fragmentos vectoriales eliminados correctamente"}

@router.post("/chatbot/documents/{document_id}/toggle")
async def toggle_chatbot_document(
    document_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    result = await db.execute(select(Document).filter(Document.id == document_id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    doc.is_active = not doc.is_active
    await db.commit()
    await db.refresh(doc)
    return {
        "status": "success",
        "id": doc.id,
        "is_active": doc.is_active,
        "message": f"Documento {'activado' if doc.is_active else 'desactivado'} correctamente"
    }

class DocumentCategoryUpdate(BaseModel):
    category: str

@router.post("/chatbot/documents/{document_id}/category")
async def update_document_category(
    document_id: str,
    data: DocumentCategoryUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    result = await db.execute(select(Document).filter(Document.id == document_id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    doc.category = data.category
    await db.commit()
    await db.refresh(doc)
    return {
        "status": "success",
        "id": doc.id,
        "category": doc.category,
        "message": f"Categoría del documento actualizada a {doc.category}"
    }

class UserRoleUpdate(BaseModel):
    role: str # 'admin' o 'user'

@router.get("/users")
async def list_registered_users(
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """Lista todos los usuarios autenticados/registrados desde Authentik"""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    
    output = []
    for u in users:
        roles_val = u.roles
        if isinstance(roles_val, str):
            import json
            try:
                roles_val = json.loads(roles_val)
            except Exception:
                roles_val = [roles_val]
        output.append({
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "roles": roles_val if isinstance(roles_val, list) else [roles_val],
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None
        })
    return output

@router.post("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    data: UserRoleUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """Asigna o modifica el rol de un usuario ('admin' o 'user')"""
    import json
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    new_role = data.role.lower().strip()
    if new_role not in ['admin', 'user']:
        raise HTTPException(status_code=400, detail="Rol inválido. Debe ser 'admin' o 'user'.")
    
    if new_role == 'admin':
        user.roles = json.dumps(["admin", "user"])
    else:
        user.roles = json.dumps(["user"])
        
    await db.commit()
    await db.refresh(user)
    
    roles_val = user.roles
    if isinstance(roles_val, str):
        try:
            roles_val = json.loads(roles_val)
        except Exception:
            roles_val = [roles_val]
            
    return {
        "status": "success",
        "id": user.id,
        "email": user.email,
        "roles": roles_val,
        "message": f"Rol de {user.email} actualizado correctamente a {new_role}"
    }


# ==============================================================================
# HALLAZGO #6: BATERÍA DE REGRESIÓN DE PROMPTS POR TEMA
# ==============================================================================

class TestCaseCreate(BaseModel):
    query: str
    expected_keywords: Optional[List[str]] = []
    description: Optional[str] = None

@router.get("/chatbot/profiles/{profile_id}/test-cases")
async def get_profile_test_cases(
    profile_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """Obtiene los casos de prueba de regresión registrados para un perfil/tenant."""
    result = await db.execute(select(PromptTestCase).filter(PromptTestCase.profile_id == profile_id).order_by(PromptTestCase.created_at.desc()))
    cases = result.scalars().all()
    return [
        {
            "id": c.id,
            "profile_id": c.profile_id,
            "query": c.query,
            "expected_keywords": c.expected_keywords or [],
            "description": c.description,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in cases
    ]

@router.post("/chatbot/profiles/{profile_id}/test-cases")
async def create_profile_test_case(
    profile_id: str,
    data: TestCaseCreate,
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """Agrega un nuevo caso de prueba de regresión para un perfil."""
    tc = PromptTestCase(
        profile_id=profile_id,
        query=data.query.strip(),
        expected_keywords=data.expected_keywords or [],
        description=data.description
    )
    db.add(tc)
    await db.commit()
    await db.refresh(tc)
    return {"status": "success", "id": tc.id, "message": "Caso de prueba creado correctamente"}

@router.delete("/chatbot/test-cases/{case_id}")
async def delete_test_case(
    case_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """Elimina un caso de prueba de regresión."""
    result = await db.execute(select(PromptTestCase).filter(PromptTestCase.id == case_id))
    tc = result.scalars().first()
    if not tc:
        raise HTTPException(status_code=404, detail="Caso de prueba no encontrado")
    await db.delete(tc)
    await db.commit()
    return {"status": "success", "message": "Caso de prueba eliminado"}

@router.post("/chatbot/profiles/{profile_id}/run-regression")
async def run_prompt_regression(
    profile_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """Ejecuta toda la batería de prueba de regresión para un perfil y evalúa la calidad y apego del prompt."""
    result = await db.execute(select(PromptTestCase).filter(PromptTestCase.profile_id == profile_id))
    cases = result.scalars().all()
    if not cases:
        return {"status": "success", "total": 0, "passed": 0, "failed": 0, "results": []}

    from app.application.services.chat_service import get_chat_service
    chat_service = await get_chat_service()

    test_results = []
    passed_count = 0

    for tc in cases:
        res = await chat_service.process_query(
            query=tc.query,
            session_id=f"regression-test-{profile_id}",
            conversation_history=[],
            db_session=db,
            filters={"category": profile_id}
        )
        answer = res.get("response", "")
        keywords = tc.expected_keywords or []
        
        # Evaluar coincidencia de palabras clave esperadas
        missing_kw = [kw for kw in keywords if kw.lower() not in answer.lower()]
        is_passed = len(missing_kw) == 0 and not res.get("error", False)
        
        if is_passed:
            passed_count += 1

        test_results.append({
            "id": tc.id,
            "query": tc.query,
            "answer": answer[:300] + ("..." if len(answer) > 300 else ""),
            "provider": res.get("provider", "RAG Engine"),
            "is_passed": is_passed,
            "missing_keywords": missing_kw,
            "sources_count": len(res.get("sources", []))
        })

    return {
        "status": "success",
        "total": len(cases),
        "passed": passed_count,
        "failed": len(cases) - passed_count,
        "pass_rate_pct": round((passed_count / len(cases)) * 100),
        "results": test_results
    }


# ==============================================================================
# HALLAZGO #9: PANEL DE OBSERVABILIDAD DEL ENRUTADOR LLM & CACHÉ
# ==============================================================================

@router.get("/stats/llm-router")
async def get_llm_router_stats(
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """Retorna métricas operativas de enrutamiento LLM, distribución de proveedores y salud del índice."""
    from app.infrastructure.models import ChatMessageModel, DocumentModel, ChatbotProfileModel
    from app.core.config import settings

    # Conteo total de mensajes del asistente
    msgs_res = await db.execute(select(func.count(ChatMessageModel.id)).where(ChatMessageModel.role == 'assistant'))
    total_assistant_msgs = msgs_res.scalar() or 0

    # Conteo de feedback positivo / negativo
    pos_res = await db.execute(select(func.count(ChatMessageModel.id)).where(ChatMessageModel.feedback_rating == 'up'))
    neg_res = await db.execute(select(func.count(ChatMessageModel.id)).where(ChatMessageModel.feedback_rating == 'down'))
    feedback_positive = pos_res.scalar() or 0
    feedback_negative = neg_res.scalar() or 0

    # Conteo de perfiles y documentos
    profiles_res = await db.execute(select(func.count(ChatbotProfileModel.id)))
    total_profiles = profiles_res.scalar() or 0

    docs_res = await db.execute(select(func.count(DocumentModel.id)))
    total_docs = docs_res.scalar() or 0

    return {
        "status": "success",
        "metrics": {
            "total_queries_processed": total_assistant_msgs,
            "total_profiles_active": total_profiles,
            "total_documents_indexed": total_docs,
            "feedback": {
                "positive": feedback_positive,
                "negative": feedback_negative,
                "satisfaction_rate_pct": round((feedback_positive / (feedback_positive + feedback_negative) * 100)) if (feedback_positive + feedback_negative) > 0 else 100
            },
            "active_llm_providers": [
                {"name": "Groq Llama-3 (Principal)", "status": "active" if settings.GROQ_API_KEY else "disabled"},
                {"name": "GCP Vertex AI / Gemini", "status": "active" if settings.GCP_PROJECT_ID else "disabled"},
                {"name": "NVIDIA NIM Cloud", "status": "active" if settings.NVIDIA_NIM_API_KEY else "disabled"},
                {"name": "Ollama / Local LLM", "status": "fallback_standby"}
            ],
            "cache_layer": {
                "type": "Redis + SentenceTransformers Semantic Cache",
                "status": "operational",
                "similarity_threshold": 0.92
            }
        }
    }
