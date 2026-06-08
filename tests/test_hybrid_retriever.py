"""hybrid Retriever 集成测试。"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

pytest.importorskip("chromadb")

from rag.bm25_index import BM25Index  # noqa: E402
from rag.hybrid_fusion import build_chunk_id  # noqa: E402
from rag.retriever import Retriever  # noqa: E402
from rag.text_splitter import TextChunk  # noqa: E402
from rag.vector_store import VectorStore  # noqa: E402


def _make_hybrid_store(tmp_path: Path):
    store = VectorStore(str(tmp_path / "chroma_hybrid"))
    bm25 = BM25Index()

    chunks = [
        TextChunk(
            content="General vector anchor document about weather and climate trends.",
            source="anchor.md",
            chunk_index=0,
        ),
        TextChunk(
            content="Special unique_keyword_zeta_marker appears only in this chunk.",
            source="keyword.md",
            chunk_index=0,
        ),
        TextChunk(
            content="Another filler document about unrelated sports and travel.",
            source="filler.md",
            chunk_index=0,
        ),
    ]

    embeddings = [
        [1.0, 0.0, 0.0, 0.0] + [0.0] * 12,
        [0.0, 1.0, 0.0, 0.0] + [0.0] * 12,
        [0.0, 0.0, 1.0, 0.0] + [0.0] * 12,
    ]
    store.add_chunks(chunks, embeddings)
    bm25.add_chunks(chunks)
    return store, bm25


def test_hybrid_includes_bm25_keyword_chunk(tmp_path):
    store, bm25 = _make_hybrid_store(tmp_path)
    query_embedding = [0.95, 0.05, 0.0, 0.0] + [0.0] * 12

    vector_retriever = Retriever(store, top_k=1, mode="vector")
    hybrid_retriever = Retriever(
        store,
        top_k=2,
        mode="hybrid",
        bm25_index=bm25,
    )

    vector_results = vector_retriever.retrieve(
        "unique_keyword_zeta_marker",
        query_embedding,
    )
    hybrid_results = hybrid_retriever.retrieve(
        "unique_keyword_zeta_marker",
        query_embedding,
    )

    assert vector_results[0].source == "anchor.md"
    keyword_id = build_chunk_id("keyword.md", 0)
    hybrid_ids = {build_chunk_id(r.source, r.chunk_index) for r in hybrid_results}
    assert keyword_id in hybrid_ids


def test_hybrid_deduplicates_by_source_and_chunk_index(tmp_path):
    store, bm25 = _make_hybrid_store(tmp_path)
    query_embedding = [0.95, 0.05, 0.0, 0.0] + [0.0] * 12

    retriever = Retriever(
        store,
        top_k=3,
        mode="hybrid",
        bm25_index=bm25,
    )
    results = retriever.retrieve("unique_keyword_zeta_marker", query_embedding)

    keys = [(item.source, item.chunk_index) for item in results]
    assert len(keys) == len(set(keys))


def test_hybrid_without_bm25_index_falls_back_to_vector(tmp_path):
    store, _ = _make_hybrid_store(tmp_path)
    query_embedding = [0.95, 0.05, 0.0, 0.0] + [0.0] * 12

    vector_retriever = Retriever(store, top_k=2, mode="vector")
    hybrid_retriever = Retriever(store, top_k=2, mode="hybrid", bm25_index=None)

    vector_results = vector_retriever.retrieve("weather", query_embedding)
    hybrid_results = hybrid_retriever.retrieve("weather", query_embedding)

    assert len(vector_results) == len(hybrid_results)
    for left, right in zip(vector_results, hybrid_results):
        assert left == right


def test_hybrid_with_empty_bm25_index_falls_back_to_vector(tmp_path):
    store, _ = _make_hybrid_store(tmp_path)
    query_embedding = [0.95, 0.05, 0.0, 0.0] + [0.0] * 12
    empty_bm25 = BM25Index()

    vector_retriever = Retriever(store, top_k=2, mode="vector")
    hybrid_retriever = Retriever(
        store,
        top_k=2,
        mode="hybrid",
        bm25_index=empty_bm25,
    )

    vector_results = vector_retriever.retrieve("weather", query_embedding)
    hybrid_results = hybrid_retriever.retrieve("weather", query_embedding)

    assert vector_results == hybrid_results


def test_hybrid_bm25_only_hit_has_no_distance(tmp_path):
    store = VectorStore(str(tmp_path / "chroma_dist"))
    bm25 = BM25Index()

    anchor_chunks = [
        TextChunk(
            content=f"Anchor filler document number {i} about climate trends.",
            source=f"anchor_{i}.md",
            chunk_index=0,
        )
        for i in range(5)
    ]
    keyword_chunk = TextChunk(
        content="Only bm25 unique_token_gamma content here.",
        source="keyword_only.md",
        chunk_index=0,
    )
    chunks = anchor_chunks + [keyword_chunk]

    embeddings = [[1.0, 0.0, 0.0, 0.0] + [0.0] * 12 for _ in anchor_chunks]
    embeddings.append([0.0, 1.0, 0.0, 0.0] + [0.0] * 12)

    store.add_chunks(chunks, embeddings)
    bm25.add_chunks(chunks)

    retriever = Retriever(
        store,
        top_k=2,
        mode="hybrid",
        bm25_index=bm25,
        candidate_multiplier=1,
    )
    query_embedding = [1.0, 0.0, 0.0, 0.0] + [0.0] * 12
    results = retriever.retrieve("unique_token_gamma", query_embedding)

    keyword_hit = next(
        r for r in results if r.source == "keyword_only.md" and r.chunk_index == 0
    )
    assert "unique_token_gamma" in keyword_hit.content
    assert keyword_hit.distance is None
