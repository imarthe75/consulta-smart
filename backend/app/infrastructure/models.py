# Modelos ORM de Base de Datos (SQLAlchemy)

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON, Enum, ForeignKey, Index, Computed
from sqlalchemy.orm import relationship
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
    status = Column(String(20), default="pending", nullable=False, index=True)
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
    text = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=True) # SentenceTransformer all-MiniLM-L6-v2 (384 dimensions)
    doc_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("DocumentModel", back_populates="chunks")
    
    __table_args__ = (
        Index('idx_chunk_document_id', 'document_id'),
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
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    session = relationship("ChatSessionModel", back_populates="messages")
    
    __table_args__ = (
        Index('idx_message_session_id', 'session_id'),
    )
