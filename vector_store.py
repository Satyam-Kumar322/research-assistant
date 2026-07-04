"""
Track 2.6: Vector Database Layer
Store and search vectors efficiently using FAISS.

Technology: FAISS (CPU)
Features:
  • Index creation
  • Index update
  • Similarity search
  • Per-workspace index isolation
  • Persistent storage to disk
"""

import os
import json
import numpy as np
import faiss
from typing import List, Dict, Any, Optional, Tuple
from threading import Lock


# ─── Configuration ────────────────────────────────────────────────────────────

VECTOR_INDEX_DIR = os.getenv("VECTOR_INDEX_DIR", "documents/vector_indices")

# ─── Thread-safe index cache ─────────────────────────────────────────────────

_index_cache: Dict[int, "WorkspaceIndex"] = {}
_cache_lock = Lock()


class WorkspaceIndex:
    """Manages a FAISS index and chunk metadata for a single workspace."""

    def __init__(self, workspace_id: int, dimension: int = 384):
        self.workspace_id = workspace_id
        self.dimension = dimension
        self.index_dir = os.path.join(VECTOR_INDEX_DIR, str(workspace_id))
        os.makedirs(self.index_dir, exist_ok=True)

        self.index_path = os.path.join(self.index_dir, "faiss.index")
        self.meta_path = os.path.join(self.index_dir, "chunk_meta.json")

        # chunk_meta: list of dicts parallel to FAISS index rows
        # Each entry: {chunk_id, document_id, page, chunk_index, chunk_text}
        self.chunk_meta: List[Dict[str, Any]] = []
        self.index: Optional[faiss.IndexFlatIP] = None  # Inner Product (cosine with normalized vecs)

        self._load()

    # ─── Persistence ──────────────────────────────────────────────────────

    def _load(self):
        """Load existing index and metadata from disk."""
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.chunk_meta = json.load(f)
                print(f"[VectorStore] Loaded index for workspace {self.workspace_id}: "
                      f"{self.index.ntotal} vectors")
            except Exception as e:
                print(f"[VectorStore] Error loading index for workspace {self.workspace_id}: {e}")
                self._create_empty()
        else:
            self._create_empty()

    def _create_empty(self):
        """Create a fresh empty index."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunk_meta = []

    def _save(self):
        """Persist index and metadata to disk."""
        os.makedirs(self.index_dir, exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.chunk_meta, f, ensure_ascii=False)
        print(f"[VectorStore] Saved index for workspace {self.workspace_id}: "
              f"{self.index.ntotal} vectors")

    # ─── Index Operations ─────────────────────────────────────────────────

    def add_chunks(self, chunks_with_vectors: List[Dict[str, Any]]):
        """
        Add chunks (with 'vector' field) to the FAISS index.

        Each chunk dict must have:
          chunk_id, document_id, page, chunk_text, chunk_index, vector
        """
        if not chunks_with_vectors:
            return

        vectors = np.array(
            [c["vector"] for c in chunks_with_vectors], dtype=np.float32
        )

        # Normalize for cosine similarity (IndexFlatIP)
        faiss.normalize_L2(vectors)

        self.index.add(vectors)

        for chunk in chunks_with_vectors:
            self.chunk_meta.append({
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "page": chunk["page"],
                "chunk_text": chunk["chunk_text"],
                "chunk_index": chunk["chunk_index"],
            })

        self._save()

    def delete_document(self, document_id: str):
        """
        Remove all vectors belonging to a specific document.
        Rebuilds the index without those vectors.
        """
        if not self.chunk_meta:
            return

        # Find indices to keep
        keep_indices = [
            i for i, meta in enumerate(self.chunk_meta)
            if meta["document_id"] != document_id
        ]

        if len(keep_indices) == len(self.chunk_meta):
            return  # Nothing to delete

        if not keep_indices:
            # All vectors belong to this document — clear everything
            self._create_empty()
            self._save()
            return

        # Reconstruct vectors for kept indices
        kept_vectors = np.array(
            [self.index.reconstruct(i) for i in keep_indices], dtype=np.float32
        )
        kept_meta = [self.chunk_meta[i] for i in keep_indices]

        # Rebuild index
        self._create_empty()
        self.index.add(kept_vectors)
        self.chunk_meta = kept_meta
        self._save()

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        similarity_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Search the index for the most similar chunks.

        Args:
            query_vector: The query embedding vector.
            top_k: Number of top results to return.
            similarity_threshold: Minimum similarity score (0.0–1.0).

        Returns:
            List of dicts with chunk metadata + similarity score, sorted by score desc.
        """
        if self.index.ntotal == 0:
            return []

        query = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(query)

        # Search
        actual_k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query, actual_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.chunk_meta):
                continue
            if float(score) < similarity_threshold:
                continue

            result = self.chunk_meta[idx].copy()
            result["similarity_score"] = round(float(score), 4)
            results.append(result)

        return results

    @property
    def total_vectors(self) -> int:
        """Return the total number of vectors in the index."""
        return self.index.ntotal if self.index else 0


# ─── Public API ───────────────────────────────────────────────────────────────

def get_workspace_index(workspace_id: int, dimension: int = 384) -> WorkspaceIndex:
    """
    Get or create a WorkspaceIndex (cached, thread-safe).

    Args:
        workspace_id: The workspace to get the index for.
        dimension: Embedding vector dimension.

    Returns:
        A WorkspaceIndex instance.
    """
    with _cache_lock:
        if workspace_id not in _index_cache:
            _index_cache[workspace_id] = WorkspaceIndex(workspace_id, dimension)
        return _index_cache[workspace_id]


def index_chunks(workspace_id: int, chunks_with_vectors: List[Dict[str, Any]]):
    """
    Add embedded chunks to a workspace's FAISS index.

    POST /vector/index equivalent.
    """
    ws_index = get_workspace_index(workspace_id)
    ws_index.add_chunks(chunks_with_vectors)
    return {"status": "indexed", "vectors_added": len(chunks_with_vectors),
            "total_vectors": ws_index.total_vectors}


def search_vectors(
    workspace_id: int,
    query_vector: List[float],
    top_k: int = 5,
    similarity_threshold: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Search a workspace's FAISS index.

    POST /vector/search equivalent.
    """
    ws_index = get_workspace_index(workspace_id)
    return ws_index.search(query_vector, top_k, similarity_threshold)


def delete_document_vectors(workspace_id: int, document_id: str):
    """Remove all vectors for a document from a workspace index."""
    ws_index = get_workspace_index(workspace_id)
    ws_index.delete_document(document_id)
