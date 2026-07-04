"""
Track 2.10: Citation Engine
Provide traceable evidence for every RAG answer.

Citation Metadata Format:
  {
    "document": "paper1.pdf",
    "page": 12,
    "chunk": 45,
    "chunk_id": "..."
  }

Output Example:
  Answer: ...
  Sources:
    - paper1.pdf  Page 12
    - paper2.pdf  Page 8
"""

from typing import List, Dict, Any, Optional


# ─── Citation Builder ─────────────────────────────────────────────────────────

def build_citations(
    retrieved_chunks: List[Dict[str, Any]],
    document_lookup: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Build citation metadata from retrieved chunks.

    Args:
        retrieved_chunks: List of chunk dicts from the retrieval engine.
            Each must have: chunk_id, document_id, page, chunk_index
        document_lookup: Optional dict mapping document_id → document info
            (with 'original_filename', 'title', etc.)

    Returns:
        List of citation dicts with:
          document, document_id, page, chunk, chunk_id, similarity_score
    """
    citations = []
    seen = set()  # Deduplicate by (document_id, page)

    for chunk in retrieved_chunks:
        document_id = chunk.get("document_id", "")
        page = chunk.get("page", 0)
        dedup_key = (document_id, page)

        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        # Resolve document filename
        doc_name = "unknown"
        if document_lookup and document_id in document_lookup:
            doc_info = document_lookup[document_id]
            doc_name = (
                doc_info.get("original_filename")
                or doc_info.get("title")
                or document_id
            )
        else:
            doc_name = chunk.get("document", chunk.get("original_filename", document_id))

        citations.append({
            "document": doc_name,
            "document_id": document_id,
            "page": page,
            "chunk": chunk.get("chunk_index", 0),
            "chunk_id": chunk.get("chunk_id", ""),
            "similarity_score": chunk.get("similarity_score", 0.0),
        })

    # Sort by document name then page
    citations.sort(key=lambda c: (c["document"], c["page"]))
    return citations


# ─── Format Answer with Citations ────────────────────────────────────────────

def format_answer_with_citations(
    answer: str,
    citations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Combine the LLM answer with structured citation data.

    Args:
        answer: The raw LLM response text.
        citations: List of citation dicts from build_citations().

    Returns:
        Dict with:
          answer: the answer text
          sources: list of citation objects
          sources_text: human-readable sources string
    """
    if not citations:
        return {
            "answer": answer,
            "sources": [],
            "sources_text": "No sources available.",
        }

    # Build human-readable sources list
    source_lines = []
    for citation in citations:
        source_lines.append(f"  - {citation['document']}  Page {citation['page']}")

    sources_text = "Sources:\n" + "\n".join(source_lines)

    return {
        "answer": answer,
        "sources": citations,
        "sources_text": sources_text,
    }
