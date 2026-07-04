"""
Track 2.4: Chunking Engine
Split documents into meaningful chunks using multiple strategies.
"""

import uuid
import re
from typing import List, Dict, Any, Optional


# ─── Chunk Data Structure ─────────────────────────────────────────────────────

def _make_chunk(document_id: str, page: int, chunk_text: str, chunk_index: int) -> Dict[str, Any]:
    """Create a standardized chunk dictionary."""
    return {
        "chunk_id": str(uuid.uuid4()),
        "document_id": document_id,
        "page": page,
        "chunk_text": chunk_text.strip(),
        "chunk_index": chunk_index,
    }


# ─── Token Counting ──────────────────────────────────────────────────────────

def _count_tokens(text: str) -> int:
    """Approximate token count using whitespace splitting.
    Falls back to simple splitting if tiktoken is unavailable."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        # Rough approximation: ~4 chars per token
        return len(text) // 4


def _split_text_by_tokens(text: str, max_tokens: int) -> List[str]:
    """Split text into pieces that fit within max_tokens."""
    words = text.split()
    pieces = []
    current_piece = []
    current_count = 0

    for word in words:
        word_tokens = _count_tokens(word)
        if current_count + word_tokens > max_tokens and current_piece:
            pieces.append(" ".join(current_piece))
            current_piece = []
            current_count = 0
        current_piece.append(word)
        current_count += word_tokens

    if current_piece:
        pieces.append(" ".join(current_piece))

    return pieces


# ─── Level 1: Fixed-Size Chunking ────────────────────────────────────────────

def fixed_size_chunking(
    pages_text: List[Dict[str, Any]],
    document_id: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[Dict[str, Any]]:
    """
    Level 1: Fixed-size chunking with token overlap.
    Splits text into chunks of `chunk_size` tokens with `overlap` token overlap.
    """
    chunks = []
    chunk_index = 0

    for page_data in pages_text:
        page = page_data.get("page", 1)
        text = page_data.get("text", "")

        if not text or text == "[IMAGE_OR_BLANK_PAGE]":
            continue

        words = text.split()
        if not words:
            continue

        # Build token-aware windows
        start = 0
        while start < len(words):
            # Take chunk_size tokens worth of words
            end = start
            token_count = 0
            chunk_words = []

            while end < len(words) and token_count < chunk_size:
                chunk_words.append(words[end])
                token_count += _count_tokens(words[end])
                end += 1

            chunk_text = " ".join(chunk_words)
            if chunk_text.strip():
                chunks.append(_make_chunk(document_id, page, chunk_text, chunk_index))
                chunk_index += 1

            # Move forward by (chunk_size - overlap) tokens
            overlap_words = 0
            overlap_tokens = 0
            while overlap_words < len(chunk_words) and overlap_tokens < overlap:
                overlap_tokens += _count_tokens(chunk_words[-(overlap_words + 1)])
                overlap_words += 1

            step = max(1, len(chunk_words) - overlap_words)
            start += step

    return chunks


# ─── Level 2: Recursive Chunking ─────────────────────────────────────────────

def _recursive_split(
    text: str,
    separators: List[str],
    max_tokens: int,
) -> List[str]:
    """Recursively split text using a hierarchy of separators."""
    if _count_tokens(text) <= max_tokens:
        return [text] if text.strip() else []

    if not separators:
        # Last resort: split by token count
        return _split_text_by_tokens(text, max_tokens)

    separator = separators[0]
    remaining_separators = separators[1:]

    parts = text.split(separator)
    result = []
    current_chunk = ""

    for part in parts:
        candidate = (current_chunk + separator + part) if current_chunk else part

        if _count_tokens(candidate) <= max_tokens:
            current_chunk = candidate
        else:
            if current_chunk.strip():
                if _count_tokens(current_chunk) <= max_tokens:
                    result.append(current_chunk)
                else:
                    result.extend(_recursive_split(current_chunk, remaining_separators, max_tokens))
            current_chunk = part

    if current_chunk.strip():
        if _count_tokens(current_chunk) <= max_tokens:
            result.append(current_chunk)
        else:
            result.extend(_recursive_split(current_chunk, remaining_separators, max_tokens))

    return result


def recursive_chunking(
    pages_text: List[Dict[str, Any]],
    document_id: str,
    max_tokens: int = 500,
) -> List[Dict[str, Any]]:
    """
    Level 2: Recursive chunking.
    Splits by paragraph → newline → sentence → space.
    """
    separators = ["\n\n", "\n", ". ", " "]
    chunks = []
    chunk_index = 0

    for page_data in pages_text:
        page = page_data.get("page", 1)
        text = page_data.get("text", "")

        if not text or text == "[IMAGE_OR_BLANK_PAGE]":
            continue

        text_chunks = _recursive_split(text, separators, max_tokens)

        for chunk_text in text_chunks:
            if chunk_text.strip():
                chunks.append(_make_chunk(document_id, page, chunk_text, chunk_index))
                chunk_index += 1

    return chunks


# ─── Level 3: Semantic Chunking ──────────────────────────────────────────────

def semantic_chunking(
    pages_text: List[Dict[str, Any]],
    document_id: str,
    max_tokens: int = 500,
    similarity_threshold: float = 0.75,
) -> List[Dict[str, Any]]:
    """
    Level 3: Semantic chunking.
    Groups sentences by embedding similarity — sentences that are semantically
    related stay together in the same chunk.
    """
    # Lazy import to avoid circular dependency
    from embedding_engine import get_embedding_model

    model = get_embedding_model()

    chunks = []
    chunk_index = 0

    for page_data in pages_text:
        page = page_data.get("page", 1)
        text = page_data.get("text", "")

        if not text or text == "[IMAGE_OR_BLANK_PAGE]":
            continue

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            continue

        if len(sentences) == 1:
            chunks.append(_make_chunk(document_id, page, sentences[0], chunk_index))
            chunk_index += 1
            continue

        # Compute embeddings for all sentences
        import numpy as np
        embeddings = model.encode(sentences, normalize_embeddings=True)

        # Group sentences by similarity
        current_group = [sentences[0]]
        current_tokens = _count_tokens(sentences[0])

        for i in range(1, len(sentences)):
            sim = float(np.dot(embeddings[i], embeddings[i - 1]))
            sentence_tokens = _count_tokens(sentences[i])

            if sim >= similarity_threshold and (current_tokens + sentence_tokens) <= max_tokens:
                current_group.append(sentences[i])
                current_tokens += sentence_tokens
            else:
                # Flush current group
                chunk_text = " ".join(current_group)
                if chunk_text.strip():
                    chunks.append(_make_chunk(document_id, page, chunk_text, chunk_index))
                    chunk_index += 1
                current_group = [sentences[i]]
                current_tokens = sentence_tokens

        # Flush remaining
        if current_group:
            chunk_text = " ".join(current_group)
            if chunk_text.strip():
                chunks.append(_make_chunk(document_id, page, chunk_text, chunk_index))
                chunk_index += 1

    return chunks


# ─── Main Entry Point ────────────────────────────────────────────────────────

def chunk_document(
    pages_text: List[Dict[str, Any]],
    document_id: str,
    strategy: str = "recursive",
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[Dict[str, Any]]:
    """
    Chunk a document using the specified strategy.

    Args:
        pages_text: List of page dicts with 'page' and 'text' keys
        document_id: UUID of the document
        strategy: 'fixed', 'recursive', or 'semantic'
        chunk_size: Max tokens per chunk
        overlap: Token overlap (only for fixed-size)

    Returns:
        List of chunk dicts with chunk_id, document_id, page, chunk_text, chunk_index
    """
    if strategy == "fixed":
        return fixed_size_chunking(pages_text, document_id, chunk_size, overlap)
    elif strategy == "recursive":
        return recursive_chunking(pages_text, document_id, chunk_size)
    elif strategy == "semantic":
        return semantic_chunking(pages_text, document_id, chunk_size)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}. Use 'fixed', 'recursive', or 'semantic'.")
