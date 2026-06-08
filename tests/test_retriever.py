import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

pytest.importorskip("chromadb")

from rag.retriever import RetrievedChunk, Retriever  # noqa: E402
from rag.text_splitter import split_text  # noqa: E402
from rag.vector_store import VectorStore  # noqa: E402


def _build_store(tmp_path: Path) -> VectorStore:
    store = VectorStore(str(tmp_path / "chroma_test"))
    chunks = split_text("MJZ AI Pro RAG system demo content.", source="demo.md")
    embeddings = [[0.01 * (i + 1)] * 16 for i in range(len(chunks))]
    store.add_chunks(chunks, embeddings)
    return store


def test_vector_store_ingest_and_count(tmp_path):
    store = _build_store(tmp_path)
    assert store.count() >= 1


def test_retriever_default_mode_is_vector(tmp_path):
    store = _build_store(tmp_path)
    retriever = Retriever(store)
    assert retriever.mode == "vector"


def test_retriever_vector_mode_matches_legacy_behavior(tmp_path):
    store = _build_store(tmp_path)
    query_embedding = [0.01] * 16
    default_retriever = Retriever(store, top_k=2)
    explicit_retriever = Retriever(store, top_k=2, mode="vector")

    default_results = default_retriever.retrieve("RAG demo", query_embedding)
    explicit_results = explicit_retriever.retrieve("RAG demo", query_embedding)

    assert isinstance(default_results, list)
    assert all(isinstance(item, RetrievedChunk) for item in default_results)
    assert len(default_results) == len(explicit_results) <= 2
    for left, right in zip(default_results, explicit_results):
        assert left.content == right.content
        assert left.source == right.source
        assert left.chunk_index == right.chunk_index
        assert left.distance == right.distance


def test_retriever_unknown_mode_raises_value_error(tmp_path):
    store = _build_store(tmp_path)
    retriever = Retriever(store, mode="semantic")
    with pytest.raises(ValueError, match="Unknown retrieval mode"):
        retriever.retrieve("query", [0.01] * 16)
