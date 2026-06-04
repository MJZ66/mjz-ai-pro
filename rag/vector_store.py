"""向量存储，基于 ChromaDB 持久化。"""
from typing import List, Optional

from rag.text_splitter import TextChunk
from utils.logger import get_logger, user_friendly_error

logger = get_logger(__name__)


class VectorStoreError(Exception):
    """向量库操作失败。"""


class VectorStore:
    def __init__(self, persist_dir: str, collection_name: str = "mjz_rag"):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self._collection = None

    def _get_collection(self):
        if self._collection is not None:
            return self._collection
        try:
            import chromadb
        except ImportError as exc:
            raise VectorStoreError(
                "未安装 chromadb，请执行 pip install chromadb"
            ) from exc

        try:
            client = chromadb.PersistentClient(path=self.persist_dir)
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            return self._collection
        except Exception as exc:
            logger.exception("ChromaDB 初始化失败")
            raise VectorStoreError(user_friendly_error(exc)) from exc

    def add_chunks(
        self,
        chunks: List[TextChunk],
        embeddings: List[List[float]],
    ) -> int:
        if not chunks:
            return 0
        if len(chunks) != len(embeddings):
            raise VectorStoreError("分块数量与向量数量不一致")

        collection = self._get_collection()
        ids = []
        documents = []
        metadatas = []

        for chunk, vector in zip(chunks, embeddings):
            doc_id = f"{chunk.source}::chunk_{chunk.chunk_index}"
            ids.append(doc_id)
            documents.append(chunk.content)
            metadatas.append(
                {
                    "source": chunk.source,
                    "chunk_index": chunk.chunk_index,
                }
            )

        try:
            collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            return len(ids)
        except Exception as exc:
            logger.exception("向量入库失败")
            raise VectorStoreError(user_friendly_error(exc)) from exc

    def count(self) -> int:
        collection = self._get_collection()
        return collection.count()

    def clear(self) -> None:
        try:
            import chromadb

            client = chromadb.PersistentClient(path=self.persist_dir)
            try:
                client.delete_collection(self.collection_name)
            except Exception:
                pass
            self._collection = None
        except Exception as exc:
            logger.exception("清空向量库失败")
            raise VectorStoreError(user_friendly_error(exc)) from exc
