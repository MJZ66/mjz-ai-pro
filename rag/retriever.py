"""Top-K 检索。"""
from dataclasses import dataclass
from typing import List, Optional

from rag.vector_store import VectorStore
from utils.logger import get_logger, user_friendly_error

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    content: str
    source: str
    chunk_index: int
    distance: Optional[float] = None


class Retriever:
    def __init__(self, vector_store: VectorStore, top_k: int = 4):
        self.vector_store = vector_store
        self.top_k = top_k

    def retrieve(
        self,
        query: str,
        query_embedding: List[float],
    ) -> List[RetrievedChunk]:
        if not query.strip():
            return []

        collection = self.vector_store._get_collection()
        if collection.count() == 0:
            return []

        try:
            result = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(self.top_k, collection.count()),
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
