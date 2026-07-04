from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from utils import get_current_user
import models
from text_cleaning import clean_text

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────────

class CleanTextRequest(BaseModel):
    text: str
    remove_urls: bool = True
    remove_emails: bool = True
    remove_symbols: bool = True
    remove_copyright: bool = True


class CleanTextResponse(BaseModel):
    raw_text: str
    clean_text: str
    raw_length: int
    clean_length: int
    noise_removed_percent: float


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/clean-text", response_model=CleanTextResponse)
def clean_raw_text(
    request: CleanTextRequest,
    current_user: models.User = Depends(get_current_user)
):
    """
    Clean a raw text string directly.
    Useful for testing the cleaning pipeline.
    """
    cleaned = clean_text(request.text)

    raw_len = len(request.text)
    clean_len = len(cleaned)
    reduction = round((1 - clean_len / max(raw_len, 1)) * 100, 1)

    return CleanTextResponse(
        raw_text=request.text,
        clean_text=cleaned,
        raw_length=raw_len,
        clean_length=clean_len,
        noise_removed_percent=reduction
    )


@router.post("/clean-document/{document_id}")
def clean_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Clean all extracted pages of an uploaded document.
    Reads from documents/raw_text/ and saves to documents/clean_text/
    """
    import json
    import os

    # Verify document belongs to current user
    document = db.query(models.Document).join(models.Workspace).filter(
        models.Document.document_id == document_id,
        models.Workspace.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found or access denied"
        )

    raw_text_dir = "documents/raw_text"
    clean_text_dir = "documents/clean_text"
    os.makedirs(clean_text_dir, exist_ok=True)

    # Find all page files for this document
    try:
        page_files = sorted([
            f for f in os.listdir(raw_text_dir)
            if f.startswith(document_id) and f.endswith(".json")
        ])
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Raw text directory not found. Please upload a document first."
        )

    if not page_files:
        raise HTTPException(
            status_code=404,
            detail="No raw text files found for this document."
        )

    cleaned_pages = 0
    skipped_pages = 0
    total_raw_chars = 0
    total_clean_chars = 0
    results = []

    for page_file in page_files:
        raw_path = os.path.join(raw_text_dir, page_file)

        with open(raw_path, "r", encoding="utf-8") as f:
            page_data = json.load(f)

        raw_text = page_data.get("text", "")
        page_num = page_data.get("page", 0)

        # Skip blank or image pages
        if raw_text == "[IMAGE_OR_BLANK_PAGE]" or not raw_text.strip():
            skipped_pages += 1
            continue

        total_raw_chars += len(raw_text)

        # Clean the text
        cleaned = clean_text(raw_text)
        total_clean_chars += len(cleaned)

        # Save cleaned page
        clean_data = {
            "document_id": document_id,
            "page": page_num,
            "raw_text": raw_text,
            "clean_text": cleaned,
            "raw_length": len(raw_text),
            "clean_length": len(cleaned),
        }

        clean_path = os.path.join(
            clean_text_dir,
            f"{document_id}_page_{page_num}_clean.json"
        )
        with open(clean_path, "w", encoding="utf-8") as f:
            json.dump(clean_data, f, indent=4, ensure_ascii=False)

        results.append({
            "page": page_num,
            "raw_length": len(raw_text),
            "clean_length": len(cleaned),
            "reduction_percent": round(
                (1 - len(cleaned) / max(len(raw_text), 1)) * 100, 1
            )
        })
        cleaned_pages += 1

    return {
        "success": True,
        "message": f"Successfully cleaned {cleaned_pages} pages",
        "stats": {
            "document_id": document_id,
            "total_pages": len(page_files),
            "cleaned_pages": cleaned_pages,
            "skipped_pages": skipped_pages,
            "total_raw_chars": total_raw_chars,
            "total_clean_chars": total_clean_chars,
            "noise_removed_percent": round(
                (1 - total_clean_chars / max(total_raw_chars, 1)) * 100, 1
            ),
            "pages": results
        }
    }


@router.get("/cleaned-text/{document_id}")
def get_document_cleaned_text(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get the full cleaned text of a document combined.
    Used as input for RAG chunking in next objective.
    """
    import json
    import os

    # Verify document belongs to current user
    document = db.query(models.Document).join(models.Workspace).filter(
        models.Document.document_id == document_id,
        models.Workspace.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found or access denied"
        )

    clean_text_dir = "documents/clean_text"

    try:
        page_files = sorted([
            f for f in os.listdir(clean_text_dir)
            if f.startswith(document_id) and f.endswith("_clean.json")
        ])
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Clean text not found. Run /clean-document first."
        )

    if not page_files:
        raise HTTPException(
            status_code=404,
            detail="No cleaned pages found. Run /clean-document first."
        )

    full_text = []
    for page_file in page_files:
        path = os.path.join(clean_text_dir, page_file)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        full_text.append(data.get("clean_text", ""))

    combined = "\n\n".join(full_text)

    return {
        "document_id": document_id,
        "title": document.title,
        "clean_text": combined,
        "total_characters": len(combined),
        "total_words": len(combined.split())
    }