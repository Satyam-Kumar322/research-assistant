from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime


# ─── User Schemas ────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Token Schemas ────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    id_token: str



# ─── Workspace Schemas ────────────────────────────────────────────────────────

class WorkspaceCreate(BaseModel):
    project_name: str
    description: Optional[str] = None

    @field_validator("project_name")
    @classmethod
    def project_name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Project name cannot be empty")
        return v.strip()


class WorkspaceResponse(BaseModel):
    workspace_id: int
    user_id: int
    project_name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Generic Response ─────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    success: bool = True


# ─── Document Schemas ────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    document_id: str
    workspace_id: int
    title: Optional[str]
    authors: Optional[str]
    path: str
    original_filename: Optional[str] = None
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    page_count: Optional[int] = None
    keywords: Optional[str] = None
    upload_date: datetime

    class Config:
        from_attributes = True


class DocumentMetadata(BaseModel):
    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[str] = None
    page_count: Optional[int] = None
    file_size_bytes: Optional[int] = None
    keywords: Optional[str] = None
    doi: Optional[str] = None


class DocumentTextOutput(BaseModel):
    document_id: str
    page: int
    text: str


# ─── RAG Schemas (Tracks 2.4–2.10) ──────────────────────────────────────────

class RAGQueryRequest(BaseModel):
    question: str
    workspace_id: int
    top_k: int = 5
    similarity_threshold: float = 0.75
    chunking_strategy: str = "recursive"


class CitationResponse(BaseModel):
    document: str
    document_id: str
    page: int
    chunk: int
    chunk_id: str
    similarity_score: float = 0.0


class RAGQueryResponse(BaseModel):
    answer: str
    sources: List[CitationResponse] = []
    sources_text: str = ""
    chunks_used: int = 0


class EmbeddingRequest(BaseModel):
    text: str


class EmbeddingResponse(BaseModel):
    text: str
    vector: List[float]
    dimension: int


class VectorSearchRequest(BaseModel):
    query: str
    workspace_id: int
    top_k: int = 5
    similarity_threshold: float = 0.0


class ChunkResponse(BaseModel):
    chunk_id: str
    document_id: str
    page: Optional[int] = None
    chunk_text: str
    chunk_index: int
    similarity_score: float = 0.0

