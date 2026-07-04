"""
Track 2.7: Retrieval Engine
Retrieve the most relevant chunks for a given question.

Pipeline:
  Question → Embedding → Vector Search → Top K Chunks

Configuration:
  top_k = 5
  similarity_threshold = 0.75
"""

from typing import List, Dict, Any, Optional

from embedding_engine import generate_embedding
from vector_store import search_vectors


# ─── Configuration ────────────────────────────────────────────────────────────

DEFAULT_TOP_K = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.75


# ─── Retrieval Pipeline ──────────────────────────────────────────────────────

def retrieve(
    question: str,
    workspace_id: int,
    top_k: int = DEFAULT_TOP_K,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> List[Dict[str, Any]]:
    """
    Retrieve the most relevant chunks for a question from a workspace.

    Pipeline:
      1. Embed the question using the embedding model
      2. Search the workspace's FAISS index
      3. Filter by similarity threshold
      4. Return top-K chunks with metadata

    Args:
        question: The user's question text.
        workspace_id: The workspace to search within.
        top_k: Number of top results to return.
        similarity_threshold: Minimum cosine similarity score (0.0–1.0).

    Returns:
        List of chunk dicts sorted by similarity (desc), each containing:
          chunk_id, document_id, page, chunk_text, chunk_index, similarity_score
    """
    # Step 1: Embed the question
    query_vector = generate_embedding(question)

    # Step 2 & 3: Search FAISS index with threshold
    results = search_vectors(
        workspace_id=workspace_id,
        query_vector=query_vector,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
    )

    # Step 4: Results are already sorted by similarity (FAISS returns sorted)
    return results


def retrieve_with_context(
    question: str,
    workspace_id: int,
    top_k: int = DEFAULT_TOP_K,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    document_lookup: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve chunks and enrich with document metadata (filename, title).

    Same as retrieve(), but adds 'document' and 'original_filename' fields
    from the document_lookup if provided.

    Args:
        question: The user's question text.
        workspace_id: The workspace to search within.
        top_k: Number of top results to return.
        similarity_threshold: Minimum cosine similarity score.
        document_lookup: Dict mapping document_id → {original_filename, title, ...}

    Returns:
        List of enriched chunk dicts.
    """
    chunks = retrieve(question, workspace_id, top_k, similarity_threshold)

    if document_lookup:
        for chunk in chunks:
            doc_id = chunk.get("document_id", "")
            if doc_id in document_lookup:
                doc_info = document_lookup[doc_id]
                chunk["document"] = doc_info.get("original_filename", doc_info.get("title", doc_id))
                chunk["original_filename"] = doc_info.get("original_filename", "")

    return chunks
