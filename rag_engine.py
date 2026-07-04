"""
Track 2.9: RAG Engine
Connect Retriever + Grounded Prompt Builder + Local LLM.

Pipeline:
  Question
    ↓ Retriever (Track 2.7)
    ↓ Top Chunks
    ↓ Prompt Builder (Track 2.8)
    ↓ Local LLM (Ollama — reuses Track 1 integration)
    ↓ Citation Engine (Track 2.10)
    ↓ Answer with Sources
"""

import os
import requests
from typing import Dict, Any, Optional, List

from retrieval_engine import retrieve_with_context
from prompt_builder import build_grounded_prompt
from citation_engine import build_citations, format_answer_with_citations


# ─── Configuration ────────────────────────────────────────────────────────────

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", 300))


# ─── RAG Query Pipeline ──────────────────────────────────────────────────────

def rag_query(
    question: str,
    workspace_id: int,
    top_k: int = 5,
    similarity_threshold: float = 0.75,
    document_lookup: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Full RAG pipeline: Question → Retrieve → Prompt → LLM → Citation → Answer.

    Args:
        question: The user's question.
        workspace_id: Workspace to search documents in.
        top_k: Number of chunks to retrieve.
        similarity_threshold: Minimum similarity for retrieved chunks.
        document_lookup: Optional dict mapping document_id → document info.

    Returns:
        Dict with:
          answer: LLM's grounded response
          sources: list of citation objects
          sources_text: human-readable sources
          chunks_used: number of chunks used for context
          retrieval_results: raw retrieved chunks (for debugging)
    """
    # Step 1: Retrieve relevant chunks
    retrieved_chunks = retrieve_with_context(
        question=question,
        workspace_id=workspace_id,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
        document_lookup=document_lookup,
    )

    # Step 2: Build grounded prompt
    prompt = build_grounded_prompt(question, retrieved_chunks)

    # Step 3: Send to local LLM (Ollama)
    try:
        ollama_response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=OLLAMA_TIMEOUT,
        )
        ollama_response.raise_for_status()
        llm_answer = ollama_response.json().get("response", "")
    except requests.exceptions.ConnectionError:
        llm_answer = (
            "Error: Could not connect to the local LLM (Ollama). "
            "Please ensure Ollama is running on " + OLLAMA_BASE_URL
        )
    except Exception as e:
        llm_answer = f"Error communicating with LLM: {str(e)}"

    # Step 4: Build citations
    citations = build_citations(retrieved_chunks, document_lookup)

    # Step 5: Format answer with citations
    result = format_answer_with_citations(llm_answer, citations)
    result["chunks_used"] = len(retrieved_chunks)
    result["retrieval_results"] = [
        {
            "chunk_id": c.get("chunk_id"),
            "document_id": c.get("document_id"),
            "document": c.get("document", c.get("document_id", "")),
            "page": c.get("page"),
            "similarity_score": c.get("similarity_score", 0),
            "chunk_text_preview": c.get("chunk_text", "")[:200] + "..."
            if len(c.get("chunk_text", "")) > 200
            else c.get("chunk_text", ""),
        }
        for c in retrieved_chunks
    ]

    return result
