# Modelos ORM de Base de Datos (SQLAlchemy)

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, JSON, Enum, ForeignKey, Index, Computed
from sqlalchemy.orm import relationship, synonym
from datetime import datetime
from uuid6 import uuid7
from pgvector.sqlalchemy import Vector

from app.core.database import Base
from app.domain.entities import DocumentStatus, DocumentCategory


class UserModel(Base):
    """ORM Model para User"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid7()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True) # Hash de contraseña opcional si se usa autenticación local
    username = Column(String(50), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    roles = Column(JSON, default=["user"])
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("DocumentModel", back_populates="user", lazy="select")
    chat_sessions = relationship("ChatSessionModel", back_populates="user", lazy="select")
    
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_username', 'username'),
    )


class DocumentModel(Base):
    """ORM Model para Document"""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid7()))
    title = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    file_type = Column(String(20), nullable=False)
    seaweedfs_file_id = Column(String(255), nullable=True, unique=True)
    file_path = Column(String(255), nullable=True)
    status = Column(String(20), default="pending", nullable=False, index=True)
    processing_status = synonym("status")
    chunk_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    group_id = Column(String(36), nullable=True, index=True)
    version = Column(Integer, default=1, nullable=False)
    version_label = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    effective_date = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True)
    doc_metadata = Column(JSON, default={})
    processing_error = Column(Text, nullable=True)
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", back_populates="documents")
    chunks = relationship("DocumentChunkModel", back_populates="document", lazy="select", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_document_user_id', 'user_id'),
        Index('idx_document_status', 'status'),
        Index('idx_document_category', 'category'),
    )


class DocumentChunkModel(Base):
    """ORM Model para Document Chunks"""
    __tablename__ = "document_chunks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid7()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    chunk_number = Column(Integer, nullable=False)
    chunk_index = synonym("chunk_number")
    text = Column(Text, nullable=False)
    content = synonym("text")
    token_count = Column(Integer, default=0)
    embedding = Column(Vector(384), nullable=True) # SentenceTransformer all-MiniLM-L6-v2 (384 dimensions)
    doc_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("DocumentModel", back_populates="chunks")
    
    __table_args__ = (
        Index('idx_chunk_document_id', 'document_id'),
    )


class VectorEmbeddingModel(Base):
    """ORM Model para embeddings vectoriales"""
    __tablename__ = "vector_embeddings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid7()))
    chunk_id = Column(String(36), ForeignKey("document_chunks.id"), nullable=False, index=True)
    vector = Column(JSON, nullable=False)
    embedding_model = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    chunk = relationship("DocumentChunkModel", lazy="select")

    __table_args__ = (
        Index('idx_vector_embedding_chunk_id', 'chunk_id'),
    )

class ChatSessionModel(Base):
    """ORM Model para Chat Session"""
    __tablename__ = "chat_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid7()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    doc_metadata = Column(JSON, default={})
    total_tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", back_populates="chat_sessions")
    messages = relationship("ChatMessageModel", back_populates="session", lazy="select", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_session_user_id', 'user_id'),
    )


class ChatMessageModel(Base):
    """ORM Model para Chat Messages"""
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid7()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    sources = Column(JSON, default=[])
    feedback_rating = Column(String(10), nullable=True)  # 'up', 'down' o None
    feedback_text = Column(Text, nullable=True)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    session = relationship("ChatSessionModel", back_populates="messages")
    
    __table_args__ = (
        Index('idx_message_session_id', 'session_id'),
    )


class SystemConfigModel(Base):
    """ORM Model para configuraciones dinámicas del sistema (Prompts, etc)"""
    __tablename__ = "system_configs"
    
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatbotProfileModel(Base):
    """ORM Model para perfiles/temas del chatbot"""
    __tablename__ = "chatbot_profiles"

    id = Column(String(50), primary_key=True)  # e.g., 'default', 'rpp', 'catastro'
    name = Column(String(255), nullable=False)
    system_prompt = Column(Text, nullable=True)
    welcome_message = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)
    subtitle = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)
    icon = Column(String(50), nullable=True, default="Bot")
    primary_color = Column(String(50), nullable=True, default="#004a87")
    strictness_level = Column(String(50), nullable=True, default="strict") # strict (Solo RAG), hybrid (RAG + Apoyo Web)
    strictness_score = Column(Integer, nullable=True, default=80) # Slider 0-100% de rigidez RAG
    temperature = Column(Float, nullable=True, default=0.1) # Creatividad / Determinismo del LLM
    top_p = Column(Float, nullable=True, default=0.9)
    forbidden_topics = Column(Text, nullable=True, default="deportes, futbol, cine, cocina, politica, chismes, entretenimiento")
    rejection_message = Column(Text, nullable=True, default="Mi función está limitada exclusivamente a la asesoría sobre trámites, normativa y servicios del Registro Público. No puedo asistirle con temas ajenos.")
    llm_provider = Column(String(50), nullable=True, default="default")  # 'default', 'groq', 'openai', 'gemini', 'nvidia', 'ollama'
    llm_model = Column(String(100), nullable=True)     # e.g., 'llama3-70b-8192', 'gpt-4o', 'gemini-1.5-pro'
    custom_api_key = Column(String(255), nullable=True) # API key enmascarada / personalizada por tema
    config_metadata = Column(JSON, default={}) # Almacenamiento optimizado de configuraciones complejas en formato JSON
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PromptTestCaseModel(Base):
    """ORM Model para casos de prueba de regresión de System Prompts por perfil/tenant"""
    __tablename__ = "prompt_test_cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid7()))
    profile_id = Column(String(50), ForeignKey("chatbot_profiles.id"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    expected_keywords = Column(JSON, default=[])  # Lista de términos/requisitos esperados en la respuesta
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ChatbotProfileAuditLogModel(Base):
    """Bitácora de cambios de chatbot_profiles (práctica CMMI CM — gestión de configuración).

    HALLAZGO real (2026-07-22): un usuario corrompió el system_prompt del tema
    'general' vía el generador de prompts, y no existía forma de revertirlo — la
    tabla chatbot_profiles no tenía historial de cambios. Esta tabla guarda un
    snapshot antes/después de cada creación/edición/borrado, con quién y cuándo,
    para poder auditar y restaurar sin depender de memoria humana o de reconstruir
    el valor "de fábrica" a mano.

    No se guarda custom_api_key en los snapshots (ni siquiera cifrada) — el
    historial de auditoría es una superficie adicional de exposición si alguna vez
    se filtra, y no aporta valor de negocio guardar la clave ahí.
    """
    __tablename__ = "chatbot_profile_audit_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid7()))
    profile_id = Column(String(50), nullable=False, index=True)  # sin FK: debe sobrevivir al borrado del perfil
    action = Column(String(20), nullable=False)  # 'create' | 'update' | 'delete' | 'restore'
    changed_by_id = Column(String(36), nullable=True)
    changed_by_email = Column(String(255), nullable=True)
    before = Column(JSON, nullable=True)  # snapshot previo (NULL en 'create')
    after = Column(JSON, nullable=True)   # snapshot resultante (NULL en 'delete')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_profile_audit_profile_id', 'profile_id'),
        Index('idx_profile_audit_created_at', 'created_at'),
    )


User = UserModel
Document = DocumentModel
DocumentChunk = DocumentChunkModel
VectorEmbedding = VectorEmbeddingModel
ChatSession = ChatSessionModel
ChatMessage = ChatMessageModel
SystemConfig = SystemConfigModel
ChatbotProfile = ChatbotProfileModel
PromptTestCase = PromptTestCaseModel
ChatbotProfileAuditLog = ChatbotProfileAuditLogModel

__all__ = [
    "User", "Document", "DocumentChunk", "VectorEmbedding", "ChatSession", "ChatMessage",
    "SystemConfig", "ChatbotProfile", "PromptTestCase", "ChatbotProfileAuditLog",
    "UserModel", "DocumentModel", "DocumentChunkModel", "VectorEmbeddingModel",
    "ChatSessionModel", "ChatMessageModel", "SystemConfigModel", "ChatbotProfileModel",
    "PromptTestCaseModel", "ChatbotProfileAuditLogModel"
]
