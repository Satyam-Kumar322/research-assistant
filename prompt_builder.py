"""
Track 2.8: Grounded Prompt Builder
Force LLM responses to rely ONLY on uploaded documents.

Strict Grounded Prompt:
  You are a research assistant. Answer ONLY from the supplied context.
  If information is unavailable, reply:
    "Information not found in uploaded documents."
  Never use outside knowledge.

  Context: {retrieved_chunks}
  Question: {user_query}
"""

from typing import List, Dict, Any


# ─── Prompt Templates ────────────────────────────────────────────────────────

GROUNDED_SYSTEM_PROMPT = """You are a research assistant. Answer ONLY from the supplied context below.
If the information is not available in the context, reply exactly:
"Information not found in uploaded documents."
Never use outside knowledge. Always cite which source document and page your answer comes from."""

CONTEXT_CHUNK_TEMPLATE = """[Source: {document} | Page: {page}]
{text}"""

FULL_PROMPT_TEMPLATE = """{system_prompt}

Context:
{context}

Question: {question}

Answer (cite sources):"""


# ─── Prompt Builder ───────────────────────────────────────────────────────────

def format_chunk_for_context(chunk: Dict[str, Any]) -> str:
    """
    Format a single retrieved chunk for inclusion in the prompt context.

    Args:
        chunk: A chunk dict with at least: chunk_text, document_id/document, page

    Returns:
        Formatted context string with source attribution.
    """
    document_name = chunk.get("document", chunk.get("original_filename", chunk.get("document_id", "unknown")))
    page = chunk.get("page", "?")
    text = chunk.get("chunk_text", "")

    return CONTEXT_CHUNK_TEMPLATE.format(
        document=document_name,
        page=page,
        text=text.strip(),
    )


def build_grounded_prompt(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
) -> str:
    """
    Build a complete grounded prompt for the LLM.

    Pipeline:
      Retrieved Chunks → Format with source tags → Assemble prompt

    Args:
        question: The user's question.
        retrieved_chunks: List of chunk dicts from the retrieval engine.

    Returns:
        A fully formatted prompt string ready to send to the LLM.
    """
    if not retrieved_chunks:
        # No context available — still use the grounded template
        context = "[No relevant context found in uploaded documents.]"
    else:
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            formatted = format_chunk_for_context(chunk)
            context_parts.append(f"--- Chunk {i} ---\n{formatted}")
        context = "\n\n".join(context_parts)

    return FULL_PROMPT_TEMPLATE.format(
        system_prompt=GROUNDED_SYSTEM_PROMPT,
        context=context,
        question=question,
    )
