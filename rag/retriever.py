"""Top-K 检索。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from rag.hybrid_fusion import ChunkRef, build_chunk_id, rrf_fuse
from rag.vector_store import VectorStore
from utils.logger import get_logger, user_friendly_error

if TYPE_CHECKING:
    from rag.bm25_index import BM25Index

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    content: str
    source: str
    chunk_index: int
    distance: Optional[float] = None


class Retriever:
    def __init__(
        self,
        vector_store: VectorStore,
        top_k: int = 4,
        *,
        mode: str = "vector",
        bm25_index: BM25Index | None = None,
        rrf_k: int = 60,
        candidate_multiplier: int = 2,
    ):
        self.vector_store = vector_store
        self.top_k = top_k
        self.mode = mode
        self.bm25_index = bm25_index
        self.rrf_k = rrf_k
        self.candidate_multiplier = candidate_multiplier

    def retrieve(
        self,
        query: str,
        query_embedding: List[float],
    ) -> List[RetrievedChunk]:
        if self.mode == "vector":
            return self._retrieve_vector(query, query_embedding)
        if self.mode == "hybrid":
            return self._retrieve_hybrid(query, query_embedding)
        raise ValueError(f"Unknown retrieval mode: {self.mode}")

    def _candidate_k(self) -> int:
        return max(self.top_k * self.candidate_multiplier, self.top_k)

    def _bm25_available(self) -> bool:
        if self.bm25_index is None:
            return False
        try:
            return len(self.bm25_index) > 0
        except Exception:
            logger.warning("BM25 索引不可用，回退向量检索")
            return False

    def _retrieve_vector(
        self,
        query: str,
        query_embedding: List[float],
        *,
        top_k: Optional[int] = None,
    ) -> List[RetrievedChunk]:
        if not query.strip():
            return []

        collection = self.vector_store._get_collection()
        if collection.count() == 0:
            return []

        limit = self.top_k if top_k is None else top_k

        try:
            result = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(limit, collection.count()),
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            logger.exception("检索失败")
            raise RuntimeError(user_friendly_error(exc)) from exc

        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        chunks: List[RetrievedChunk] = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            meta = meta or {}
            chunks.append(
                RetrievedChunk(
                    content=doc,
                    source=meta.get("source", "unknown"),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    distance=dist,
                )
            )
        return chunks

    def _retrieve_hybrid(
        self,
        query: str,
        query_embedding: List[float],
    ) -> List[RetrievedChunk]:
        if not self._bm25_available():
            return self._retrieve_vector(query, query_embedding)

        candidate_k = self._candidate_k()
        vector_hits = self._retrieve_vector(
            query,
            query_embedding,
            top_k=candidate_k,
        )
        bm25_hits = self.bm25_index.search(query, top_k=candidate_k)

        vector_refs = [self._to_chunk_ref(hit) for hit in vector_hits]
        bm25_refs = self._bm25_hits_to_refs(bm25_hits)

        if not vector_refs and not bm25_refs:
            return []

        fused = rrf_fuse(
            vector_refs,
            bm25_refs,
            top_k=self.top_k,
            k=self.rrf_k,
        )
        return self._fused_to_retrieved(fused, vector_hits)

    @staticmethod
    def _to_chunk_ref(chunk: RetrievedChunk) -> ChunkRef:
        return ChunkRef(
            chunk_id=build_chunk_id(chunk.source, chunk.chunk_index),
            source=chunk.source,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            distance=chunk.distance,
        )

    def _bm25_hits_to_refs(
        self,
        hits: List[tuple[str, float]],
    ) -> List[ChunkRef]:
        refs: List[ChunkRef] = []
        for chunk_id, score in hits:
            indexed = self.bm25_index.get_chunk(chunk_id)
            if indexed is None:
                continue
            refs.append(
                ChunkRef(
                    chunk_id=indexed.chunk_id,
                    source=indexed.source,
                    chunk_index=indexed.chunk_index,
                    content=indexed.content,
                    bm25_score=score,
                )
            )
        return refs

    @staticmethod
    def _fused_to_retrieved(
        fused,
        vector_hits: List[RetrievedChunk],
    ) -> List[RetrievedChunk]:
        distance_map = {
            build_chunk_id(hit.source, hit.chunk_index): hit.distance
            for hit in vector_hits
        }
        results: List[RetrievedChunk] = []
        seen: set[tuple[str, int]] = set()

        for item in fused:
            key = (item.source, item.chunk_index)
            if key in seen:
                continue
            seen.add(key)
            results.append(
                RetrievedChunk(
                    content=item.content,
                    source=item.source,
                    chunk_index=item.chunk_index,
                    distance=distance_map.get(item.chunk_id),
                )
            )
        return results
