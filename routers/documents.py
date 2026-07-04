import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from utils import get_current_user
from document_processor import process_document, save_structured_output

router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

@router.post("/upload")
async def upload_document(
    workspace_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Submodule 2.2.1: Document Upload Service
    Upload a research paper, validate, extract text/metadata, and save to DB.
    Auto-indexes the document for RAG after upload.
    Returns document info + chunk_count.
    """
    # Verify workspace belongs to user
    workspace = db.query(models.Workspace).filter(
        models.Workspace.workspace_id == workspace_id,
        models.Workspace.user_id == current_user.id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Validation: extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: PDF, DOCX, TXT")

    # Read file and check size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds limit (50 MB)")

    document_id = str(uuid.uuid4())
    
    # Validation: duplicates
    # For simplicity, checking if filename already exists in the same workspace
    existing_doc = db.query(models.Document).filter(
        models.Document.workspace_id == workspace_id,
        models.Document.path.like(f"%{file.filename}")
    ).first()
    if existing_doc:
        raise HTTPException(status_code=400, detail="Document with this name already uploaded to the workspace")

    # Save raw file locally
    os.makedirs("documents/raw_files", exist_ok=True)
    raw_file_path = f"documents/raw_files/{document_id}{ext}"
    with open(raw_file_path, "wb") as f:
        f.write(file_bytes)

    # Submodule 2.2.2 - 2.2.4: Extraction
    try:
        pages_text, metadata = process_document(raw_file_path, document_id, ext)
        
        # Quality Validation Check: Text length > 0
        total_text_length = sum(len(p["text"]) for p in pages_text if p["text"] != "[IMAGE_OR_BLANK_PAGE]")
        if total_text_length == 0:
            raise ValueError("No text could be extracted or file is completely blank/image-only.")

    except Exception as e:
        # Cleanup
        if os.path.exists(raw_file_path):
            os.remove(raw_file_path)
        raise HTTPException(status_code=400, detail=f"Failed to process document: {e}")

    # Submodule 2.2.6: Storage Layer
    save_structured_output(document_id, pages_text, metadata)

    # Submodule 2.2.5: Database Table Insertion
    new_document = models.Document(
        document_id=document_id,
        workspace_id=workspace_id,
        title=metadata.title or file.filename,
        authors=metadata.authors,
        path=raw_file_path,
        original_filename=file.filename,
        file_type=ext.lstrip('.').upper(),
        file_size_bytes=metadata.file_size_bytes,
        page_count=metadata.page_count,
        keywords=metadata.keywords
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    # ─── Auto-index for RAG (Tracks 2.4–2.6) ─────────────────────────────
    chunk_count = 0
    try:
        from chunking_engine import chunk_document
        from embedding_engine import embed_chunks
        from vector_store import index_chunks as faiss_index_chunks

        chunks = chunk_document(pages_text, document_id, strategy="recursive", chunk_size=500, overlap=50)
        if chunks:
            chunks = embed_chunks(chunks)
            # Save chunks to DB
            for chunk in chunks:
                db_chunk = models.DocumentChunk(
                    chunk_id=chunk["chunk_id"],
                    document_id=document_id,
                    page=chunk["page"],
                    chunk_text=chunk["chunk_text"],
                    chunk_index=chunk["chunk_index"],
                    strategy="recursive",
                )
                db.add(db_chunk)
            # Index into FAISS
            faiss_index_chunks(workspace_id, chunks)
            db.commit()
            chunk_count = len(chunks)
            print(f"[Auto-Index] Indexed {chunk_count} chunks for document {document_id}")
    except Exception as e:
        print(f"[Auto-Index] Warning: Auto-indexing failed for {document_id}: {e}")
        # Don't fail the upload — indexing can be retried manually

    # Return document info + chunk_count
    return JSONResponse(content={
        "document_id": new_document.document_id,
        "workspace_id": new_document.workspace_id,
        "title": new_document.title,
        "authors": new_document.authors,
        "path": new_document.path,
        "original_filename": new_document.original_filename,
        "file_type": new_document.file_type,
        "file_size_bytes": new_document.file_size_bytes,
        "page_count": new_document.page_count,
        "keywords": new_document.keywords,
        "upload_date": new_document.upload_date.isoformat() if new_document.upload_date else None,
        "chunk_count": chunk_count,
    })


@router.get("/all", response_model=List[schemas.DocumentResponse])
def get_all_documents(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all documents for the authenticated user across all workspaces."""
    documents = db.query(models.Document).join(models.Workspace).filter(
        models.Workspace.user_id == current_user.id
    ).order_by(models.Document.upload_date.desc()).all()
    return documents


@router.get("/{document_id}/chunks")
def get_document_chunks(
    document_id: str,
    page: Optional[int] = Query(None, description="Filter by page number"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all chunks for a document, with optional page filter."""
    # Verify document belongs to user
    document = db.query(models.Document).join(models.Workspace).filter(
        models.Document.document_id == document_id,
        models.Workspace.user_id == current_user.id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    query = db.query(models.DocumentChunk).filter(
        models.DocumentChunk.document_id == document_id
    )
    if page is not None:
        query = query.filter(models.DocumentChunk.page == page)

    chunks = query.order_by(models.DocumentChunk.chunk_index.asc()).all()

    return {
        "document_id": document_id,
        "total_chunks": len(chunks),
        "chunks": [
            {
                "chunk_id": c.chunk_id,
                "chunk_index": c.chunk_index,
                "page": c.page,
                "chunk_text": c.chunk_text,
                "strategy": c.strategy,
            }
            for c in chunks
        ]
    }


@router.get("/{document_id}", response_model=schemas.DocumentResponse)
def get_document_details(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get full details of a single document."""
    document = db.query(models.Document).join(models.Workspace).filter(
        models.Document.document_id == document_id,
        models.Workspace.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.get("/", response_model=List[schemas.DocumentResponse])
def get_documents(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all documents in a workspace."""
    workspace = db.query(models.Workspace).filter(
        models.Workspace.workspace_id == workspace_id,
        models.Workspace.user_id == current_user.id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    documents = db.query(models.Document).filter(models.Document.workspace_id == workspace_id).all()
    return documents


@router.delete("/{document_id}", response_model=schemas.MessageResponse)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a document."""
    document = db.query(models.Document).join(models.Workspace).filter(
        models.Document.document_id == document_id,
        models.Workspace.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Optionally delete physical files here as well
    if os.path.exists(document.path):
        os.remove(document.path)

    db.delete(document)
    db.commit()

    return {"message": "Document deleted successfully", "success": True}
