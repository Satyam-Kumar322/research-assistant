import os
import uuid
import json
import fitz  # PyMuPDF
from docx import Document as DocxDocument
from typing import List, Dict, Any, Tuple
from schemas import DocumentMetadata

def process_pdf(file_path: str, document_id: str) -> Tuple[List[Dict[str, Any]], DocumentMetadata]:
    """Extract text and metadata from a PDF file using PyMuPDF."""
    doc = fitz.open(file_path)
    pages_text = []
    
    # Metadata extraction
    metadata_dict = doc.metadata or {}
    title = metadata_dict.get("title") or ""
    authors = metadata_dict.get("author") or ""
    keywords = metadata_dict.get("keywords") or ""
    page_count = len(doc)
    
    for page_num in range(page_count):
        page = doc.load_page(page_num)
        text = page.get_text()
        
        # Quality check: corrupted or image-only page (simplified heuristic)
        if len(text.strip()) == 0:
            # Might be an image-only page or corrupted
            text = "[IMAGE_OR_BLANK_PAGE]"
            
        pages_text.append({
            "document_id": document_id,
            "page": page_num + 1,
            "text": text
        })
        
    doc.close()
    file_size_bytes = os.path.getsize(file_path)
    
    metadata = DocumentMetadata(
        title=title,
        authors=authors,
        page_count=page_count,
        file_size_bytes=file_size_bytes,
        keywords=keywords
    )
    
    return pages_text, metadata

def process_docx(file_path: str, document_id: str) -> Tuple[List[Dict[str, Any]], DocumentMetadata]:
    """Extract text and metadata from a DOCX file."""
    doc = DocxDocument(file_path)
    pages_text = []
    
    # Metadata extraction
    core_properties = doc.core_properties
    title = core_properties.title or ""
    authors = core_properties.author or ""
    keywords = core_properties.keywords or ""
    
    # Treat DOCX as a single continuous text or chunk by paragraphs
    # Since the schema asks for "page", we'll just treat the whole docx as page 1
    # or chunk by paragraphs. Let's combine all paragraphs as page 1 for simplicity.
    full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    
    if len(full_text.strip()) == 0:
        full_text = "[IMAGE_OR_BLANK_PAGE]"
        
    pages_text.append({
        "document_id": document_id,
        "page": 1,
        "text": full_text
    })
    
    file_size_bytes = os.path.getsize(file_path)
    
    metadata = DocumentMetadata(
        title=title,
        authors=authors,
        page_count=1,
        file_size_bytes=file_size_bytes,
        keywords=keywords
    )
    
    return pages_text, metadata

def process_txt(file_path: str, document_id: str) -> Tuple[List[Dict[str, Any]], DocumentMetadata]:
    """Extract text and metadata from a TXT file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
        
    pages_text = [{
        "document_id": document_id,
        "page": 1,
        "text": text
    }]
    
    file_size_bytes = os.path.getsize(file_path)
    metadata = DocumentMetadata(
        title=os.path.basename(file_path),
        page_count=1,
        file_size_bytes=file_size_bytes
    )
    
    return pages_text, metadata

def process_document(file_path: str, document_id: str, file_ext: str) -> Tuple[List[Dict[str, Any]], DocumentMetadata]:
    """Route document to appropriate processor based on extension."""
    if file_ext == ".pdf":
        return process_pdf(file_path, document_id)
    elif file_ext == ".docx":
        return process_docx(file_path, document_id)
    elif file_ext == ".txt":
        return process_txt(file_path, document_id)
    else:
        raise ValueError("Unsupported file format")

def save_structured_output(document_id: str, pages_text: List[Dict[str, Any]], metadata: DocumentMetadata):
    """Save extracted text and metadata to the storage layer."""
    os.makedirs("documents/raw_text", exist_ok=True)
    os.makedirs("documents/metadata", exist_ok=True)
    
    # Save raw text pages
    for page_data in pages_text:
        page_num = page_data["page"]
        text_path = f"documents/raw_text/{document_id}_page_{page_num}.json"
        with open(text_path, "w", encoding="utf-8") as f:
            json.dump(page_data, f, indent=4)
            
    # Save metadata
    metadata_path = f"documents/metadata/{document_id}.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata.model_dump(), f, indent=4)
