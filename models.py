from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    is_active = Column(Boolean, default=True)
    oauth_provider = Column(String(50), nullable=True)   # e.g., "google", "github"
    oauth_id = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    workspaces = relationship("Workspace", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String(255), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    login_time = Column(DateTime(timezone=True), server_default=func.now())
    expiry_time = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationship
    user = relationship("User", back_populates="sessions")


class Workspace(Base):
    __tablename__ = "workspaces"

    workspace_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="workspaces")
    documents = relationship("Document", back_populates="workspace", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    document_id = Column(String(36), primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.workspace_id"), nullable=False)
    title = Column(String(500), nullable=True)
    authors = Column(String(1000), nullable=True)
    path = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=True)
    file_type = Column(String(20), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    keywords = Column(String(2000), nullable=True)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workspace = relationship("Workspace", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """Track 2.4: Stores chunk metadata for the chunking engine."""
    __tablename__ = "document_chunks"

    chunk_id = Column(String(36), primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.document_id"), nullable=False)
    page = Column(Integer, nullable=True)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    strategy = Column(String(20), nullable=True)  # fixed / recursive / semantic
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    document = relationship("Document", back_populates="chunks")


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String, index=True)
    user_message = Column(String)
    bot_reply = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
