"""Reciprocal Rank Fusion (RRF) for hybrid retrieval."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass(frozen=True)
class ChunkRef:
    """Single chunk reference from one retrieval path (vector or BM25)."""

    chunk_id: str
    source: str
    chunk_index: int
    content: str
    distance: Optional[float] = None
    bm25_score: Optional[float] = None


@dataclass(frozen=True)
class FusedChunk:
    """RRF-fused chunk (internal; not exposed as RetrievedChunk extension)."""

    chunk_id: str
    source: str
    chunk_index: int
    content: str
    rrf_score: float


def build_chunk_id(source: str, chunk_index: int) -> str:
    """Align with VectorStore id format: ``{source}::chunk_{index}``."""
    return f"{source}::chunk_{chunk_index}"


def rrf_fuse(
    *ranked_lists: Sequence[ChunkRef],
    top_k: int,
    k: int = 60,
) -> List[FusedChunk]:
    """
    Fuse multiple ranked lists with Reciprocal Rank Fusion.

    Each list is ordered best-first; rank starts at 1 within each list.
    Chunks are deduplicated by ``chunk_id``.
    """
    if top_k <= 0:
        return []

    non_empty = [lst for lst in ranked_lists if lst]
    if not non_empty:
        return []

    scores: dict[str, float] = {}
    meta: dict[str, ChunkRef] = {}

    for ranked in non_empty:
        for rank, item in enumerate(ranked, start=1):
            scores[item.chunk_id] = scores.get(item.chunk_id, 0.0) + 1.0 / (k + rank)
            if item.chunk_id not in meta:
                meta[item.chunk_id] = item

    ordered = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
    results: List[FusedChunk] = []
    for chunk_id, score in ordered[:top_k]:
        ref = meta[chunk_id]
        results.append(
            FusedChunk(
                chunk_id=ref.chunk_id,
                source=ref.source,
                chunk_index=ref.chunk_index,
                content=ref.content,
                rrf_score=score,
            )
        )
    return results
