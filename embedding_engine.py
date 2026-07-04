"""
Track 2.5: Embedding Engine
Convert text chunks into vector embeddings using sentence-transformers.

Recommended Models:
  • all-MiniLM-L6-v2  (default, ~80 MB, 384-dim)
  • BGE-small-en-v1.5
  • all-MiniLM-L12-v2

Pipeline:
  Chunk → Embedding Model → Vector
"""

import os
import numpy as np
from typing import List, Dict, Any, Optional

# ─── Configuration ────────────────────────────────────────────────────────────

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIMENSION = 384  # MiniLM-L6-v2 output dimension

# ─── Singleton Model Loader ──────────────────────────────────────────────────

_model = None


def get_embedding_model():
    """
    Lazy-load and return the SentenceTransformer model (singleton).
    The model is loaded once and reused across all requests.
    """
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print(f"[Embedding Engine] Loading model: {EMBEDDING_MODEL_NAME}...")
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        print(f"[Embedding Engine] Model loaded. Dimension: {_model.get_embedding_dimension()}")
    return _model


def get_embedding_dimension() -> int:
    """Return the embedding vector dimension for the current model."""
    model = get_embedding_model()
    return model.get_embedding_dimension()


# ─── Single Embedding ────────────────────────────────────────────────────────

def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding vector for a single text string.

    Args:
        text: The input text to embed.

    Returns:
        A list of floats representing the embedding vector.
    """
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


# ─── Batch Embeddings ────────────────────────────────────────────────────────

def generate_embeddings(texts: List[str], batch_size: int = 64) -> List[List[float]]:
    """
    Generate embedding vectors for a batch of texts.

    Args:
        texts: List of input texts to embed.
        batch_size: Number of texts to process at once.

    Returns:
        List of embedding vectors.
    """
    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=batch_size,
        show_progress_bar=False,
    )
    return embeddings.tolist()


# ─── Chunk Embedding Pipeline ────────────────────────────────────────────────

def embed_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Embed a list of chunk dicts, adding 'vector' field to each.

    Input chunks must have at least: chunk_id, chunk_text
    Output adds: vector (list of floats)

    Args:
        chunks: List of chunk dictionaries from the chunking engine.

    Returns:
        The same chunks with 'vector' field added.
    """
    if not chunks:
        return []

    texts = [chunk["chunk_text"] for chunk in chunks]
    vectors = generate_embeddings(texts)

    for chunk, vector in zip(chunks, vectors):
        chunk["vector"] = vector

    return chunks
