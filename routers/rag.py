"""
RAG API Router
Exposes Tracks 2.4–2.10 as REST endpoints.

Endpoints:
  POST /api/rag/index/{workspace_id}                  — Index all documents in a workspace
  POST /api/rag/index/{workspace_id}/{document_id}    — Index a single document
  POST /api/rag/query                                 — RAG query with citation-aware response
  POST /api/rag/embedding/generate                    — Generate embedding for raw text
  POST /api/rag/vector/search                         — Direct vector similarity search
"""

import json
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from utils import get_current_user
import models
import schemas

from chunking_engine import chunk_document
from embedding_engine import generate_embedding, generate_embeddings, embed_chunks
from vector_store import index_chunks, search_vectors, delete_document_vectors, get_workspace_index
from retrieval_engine import retrieve
from rag_engine import rag_query


router = APIRouter()


# ─── Request / Response Models ────────────────────────────────────────────────

class RAGQueryRequest(BaseModel):
    question: str
    workspace_id: int
    top_k: int = Field(default=5, ge=1, le=50)
    similarity_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    chunking_strategy: str = Field(default="recursive", pattern="^(fixed|recursive|semantic)$")


class EmbeddingRequest(BaseModel):
    text: str


class VectorSearchRequest(BaseModel):
    query: str
    workspace_id: int
    top_k: int = Field(default=5, ge=1, le=50)
    similarity_threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class IndexRequest(BaseModel):
    chunking_strategy: str = Field(default="recursive", pattern="^(fixed|recursive|semantic)$")
    chunk_size: int = Field(default=500, ge=50, le=2000)
    overlap: int = Field(default=50, ge=0, le=200)


# ─── Helper: Build document lookup ───────────────────────────────────────────

def _build_document_lookup(db: Session, workspace_id: int) -> dict:
    """Build a dict mapping document_id → document info for a workspace."""
    documents = db.query(models.Document).filter(
        models.Document.workspace_id == workspace_id
    ).all()
    return {
        doc.document_id: {
            "original_filename": doc.original_filename,
            "title": doc.title,
            "document_id": doc.document_id,
        }
        for doc in documents
    }


# ─── Helper: Index a single document ────────────────────────────────────────

def _index_single_document(
    document: models.Document,
    db: Session,
    strategy: str = "recursive",
    chunk_size: int = 500,
    overlap: int = 50,
) -> dict:
    """
    Full pipeline for a single document:
    Extract text → Chunk → Embed → Index into FAISS → Save chunks to DB.
    """
    document_id = document.document_id
    workspace_id = document.workspace_id

    # Step 1: Load extracted text pages
    pages_text = _load_document_pages(document_id)
    if not pages_text:
        return {"document_id": document_id, "status": "skipped", "reason": "no text found"}

    # Step 2: Remove existing chunks & vectors for this document (re-index)
    db.query(models.DocumentChunk).filter(
        models.DocumentChunk.document_id == document_id
    ).delete()
    delete_document_vectors(workspace_id, document_id)

    # Step 3: Chunk the document
    chunks = chunk_document(
        pages_text=pages_text,
        document_id=document_id,
        strategy=strategy,
        chunk_size=chunk_size,
        overlap=overlap,
    )

    if not chunks:
        return {"document_id": document_id, "status": "skipped", "reason": "no chunks produced"}

    # Step 4: Embed chunks
    chunks = embed_chunks(chunks)

    # Step 5: Save chunks to DB
    for chunk in chunks:
        db_chunk = models.DocumentChunk(
            chunk_id=chunk["chunk_id"],
            document_id=document_id,
            page=chunk["page"],
            chunk_text=chunk["chunk_text"],
            chunk_index=chunk["chunk_index"],
            strategy=strategy,
        )
        db.add(db_chunk)

    # Step 6: Index into FAISS
    result = index_chunks(workspace_id, chunks)

    db.commit()

    return {
        "document_id": document_id,
        "status": "indexed",
        "chunks_created": len(chunks),
        "vectors_total": result["total_vectors"],
    }


def _load_document_pages(document_id: str) -> list:
    """Load extracted text pages from the raw_text storage."""
    raw_text_dir = "documents/raw_text"
    pages = []

    if not os.path.exists(raw_text_dir):
        return pages

    # Find all page files for this document
    prefix = f"{document_id}_page_"
    page_files = sorted([
        f for f in os.listdir(raw_text_dir)
        if f.startswith(prefix) and f.endswith(".json")
    ])

    for page_file in page_files:
        filepath = os.path.join(raw_text_dir, page_file)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                page_data = json.load(f)
                pages.append(page_data)
        except Exception as e:
            print(f"[RAG Router] Error loading {filepath}: {e}")

    return pages


# ─── POST /api/rag/index/{workspace_id} ─────────────────────────────────────

@router.post("/index/{workspace_id}")
def index_workspace(
    workspace_id: int,
    request: IndexRequest = IndexRequest(),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Index all documents in a workspace.
    Chunks → Embeds → Stores in FAISS for each document.
    """
    # Verify workspace belongs to user
    workspace = db.query(models.Workspace).filter(
        models.Workspace.workspace_id == workspace_id,
        models.Workspace.user_id == current_user.id,
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    documents = db.query(models.Document).filter(
        models.Document.workspace_id == workspace_id
    ).all()

    if not documents:
        raise HTTPException(status_code=404, detail="No documents found in workspace")

    results = []
    for doc in documents:
        try:
            result = _index_single_document(
                document=doc,
                db=db,
                strategy=request.chunking_strategy,
                chunk_size=request.chunk_size,
                overlap=request.overlap,
            )
            results.append(result)
        except Exception as e:
            results.append({
                "document_id": doc.document_id,
                "status": "error",
                "reason": str(e),
            })

    total_chunks = sum(r.get("chunks_created", 0) for r in results)
    return {
        "workspace_id": workspace_id,
        "documents_processed": len(results),
        "total_chunks_created": total_chunks,
        "details": results,
    }


# ─── POST /api/rag/index/{workspace_id}/{document_id} ───────────────────────

@router.post("/index/{workspace_id}/{document_id}")
def index_document(
    workspace_id: int,
    document_id: str,
    request: IndexRequest = IndexRequest(),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Index a single document in a workspace."""
    document = db.query(models.Document).join(models.Workspace).filter(
        models.Document.document_id == document_id,
        models.Document.workspace_id == workspace_id,
        models.Workspace.user_id == current_user.id,
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found in workspace")

    try:
        result = _index_single_document(
            document=document,
            db=db,
            strategy=request.chunking_strategy,
            chunk_size=request.chunk_size,
            overlap=request.overlap,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


# ─── POST /api/rag/query ────────────────────────────────────────────────────

@router.post("/query")
def query_rag(
    request: RAGQueryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    RAG query: retrieve relevant chunks, build grounded prompt,
    send to LLM, return citation-aware response.
    """
    # Verify workspace belongs to user
    workspace = db.query(models.Workspace).filter(
        models.Workspace.workspace_id == request.workspace_id,
        models.Workspace.user_id == current_user.id,
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check if workspace has any indexed vectors
    ws_index = get_workspace_index(request.workspace_id)
    if ws_index.total_vectors == 0:
        raise HTTPException(
            status_code=400,
            detail="No documents have been indexed in this workspace. "
                   "Use POST /api/rag/index/{workspace_id} first.",
        )

    # Build document lookup for citations
    document_lookup = _build_document_lookup(db, request.workspace_id)

    # Run RAG pipeline
    result = rag_query(
        question=request.question,
        workspace_id=request.workspace_id,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
        document_lookup=document_lookup,
    )

    return result


# ─── POST /api/rag/embedding/generate ───────────────────────────────────────

@router.post("/embedding/generate")
def generate_embedding_api(
    request: EmbeddingRequest,
    current_user: models.User = Depends(get_current_user),
):
    """
    Track 2.5 API: Generate an embedding vector for raw text.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    vector = generate_embedding(request.text)
    return {
        "text": request.text,
        "vector": vector,
        "dimension": len(vector),
    }


# ─── POST /api/rag/vector/search ────────────────────────────────────────────

@router.post("/vector/search")
def vector_search_api(
    request: VectorSearchRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Track 2.6 API: Direct vector similarity search.
    Embeds the query and searches the workspace's FAISS index.
    """
    # Verify workspace belongs to user
    workspace = db.query(models.Workspace).filter(
        models.Workspace.workspace_id == request.workspace_id,
        models.Workspace.user_id == current_user.id,
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    query_vector = generate_embedding(request.query)
    results = search_vectors(
        workspace_id=request.workspace_id,
        query_vector=query_vector,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
    )

    return {
        "query": request.query,
        "workspace_id": request.workspace_id,
        "results_count": len(results),
        "chunks": results,
    }
