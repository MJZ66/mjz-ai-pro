"""rag_agent 模块测试。"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

pytest.importorskip("chromadb")

from rag.bm25_index import BM25_INDEX_FILENAME, BM25Index  # noqa: E402
from rag.hybrid_fusion import build_chunk_id  # noqa: E402
from rag.rag_agent import RAGAgent  # noqa: E402
from rag.vector_store import VectorStore  # noqa: E402


class FakeLLM:
    def embed_texts(self, texts):
        return [[0.01 * (i + 1)] * 16 for i in range(len(texts))]


class FakeUpload:
    name = "kb.md"
    type = "text/plain"

    def read(self):
        return (
            b"MJZ AI Pro hybrid retrieval keyword baseline content. "
            b"Knowledge base indexing test document."
        )


def test_ingest_creates_bm25_index_file(tmp_path):
    persist_dir = tmp_path / "chroma"
    store = VectorStore(str(persist_dir))
    agent = RAGAgent(FakeLLM(), store)

    assert agent.retriever.mode == "vector"

    count, message = agent.ingest_upload(FakeUpload())
    assert count > 0
    assert "成功入库" in message

    bm25_path = persist_dir / BM25_INDEX_FILENAME
    assert bm25_path.is_file()


def test_ingest_bm25_can_search_keyword(tmp_path):
    persist_dir = tmp_path / "chroma"
    store = VectorStore(str(persist_dir))
    agent = RAGAgent(FakeLLM(), store)

    agent.ingest_upload(FakeUpload())

    hits = agent.bm25_index.search("keyword baseline", top_k=1)
    assert hits
    assert hits[0][0] == build_chunk_id("kb.md", 0)


def test_bm25_load_failure_falls_back_to_empty_index(tmp_path, monkeypatch):
    persist_dir = tmp_path / "chroma"
    persist_dir.mkdir(parents=True)
    (persist_dir / BM25_INDEX_FILENAME).write_text("{ invalid json", encoding="utf-8")

    store = VectorStore(str(persist_dir))
    agent = RAGAgent(FakeLLM(), store)

    assert len(agent.bm25_index) == 0
    assert agent.retriever.mode == "vector"

    count, _ = agent.ingest_upload(FakeUpload())
    assert count > 0
    assert (persist_dir / BM25_INDEX_FILENAME).is_file()
    assert agent.bm25_index.search("keyword baseline", top_k=1)
