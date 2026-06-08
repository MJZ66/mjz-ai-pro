"""hybrid_fusion (RRF) 模块测试。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rag.hybrid_fusion import (  # noqa: E402
    ChunkRef,
    build_chunk_id,
    rrf_fuse,
)


def _ref(source: str, idx: int, content: str, **kwargs) -> ChunkRef:
    return ChunkRef(
        chunk_id=build_chunk_id(source, idx),
        source=source,
        chunk_index=idx,
        content=content,
        **kwargs,
    )


def test_build_chunk_id_matches_vector_store_format():
    assert build_chunk_id("demo.md", 0) == "demo.md::chunk_0"
    assert build_chunk_id("a.pdf", 3) == "a.pdf::chunk_3"


def test_rrf_empty_inputs():
    assert rrf_fuse([], top_k=4) == []
    assert rrf_fuse([], [], top_k=4) == []


def test_rrf_top_k_non_positive():
    a = [_ref("a.txt", 0, "one")]
    assert rrf_fuse(a, top_k=0) == []
    assert rrf_fuse(a, top_k=-1) == []


def test_rrf_single_list_only():
    ranked = [
        _ref("doc.md", 0, "alpha"),
        _ref("doc.md", 1, "beta"),
        _ref("doc.md", 2, "gamma"),
    ]
    fused = rrf_fuse(ranked, top_k=2, k=60)
    assert len(fused) == 2
    assert fused[0].chunk_id == build_chunk_id("doc.md", 0)
    assert fused[1].chunk_id == build_chunk_id("doc.md", 1)
    assert fused[0].content == "alpha"
    assert fused[0].rrf_score > fused[1].rrf_score


def test_rrf_both_lists_overlap_boosts_shared_chunk():
    shared = _ref("doc.md", 1, "overlap chunk")
    vector_only = _ref("doc.md", 0, "vector winner")
    bm25_only = _ref("doc.md", 2, "bm25 winner")

    vector_list = [vector_only, shared]
    bm25_list = [shared, bm25_only]

    fused = rrf_fuse(vector_list, bm25_list, top_k=3, k=60)
    ids = [item.chunk_id for item in fused]

    assert len(fused) == 3
    assert shared.chunk_id in ids
    shared_hit = next(item for item in fused if item.chunk_id == shared.chunk_id)
    vector_hit = next(item for item in fused if item.chunk_id == vector_only.chunk_id)
    assert shared_hit.rrf_score > vector_hit.rrf_score


def test_rrf_deduplication_no_duplicate_ids():
    a = _ref("x.txt", 0, "same")
    b = _ref("x.txt", 0, "same")
    fused = rrf_fuse([a], [b], top_k=4, k=60)
    assert len(fused) == 1
    assert fused[0].chunk_id == build_chunk_id("x.txt", 0)


def test_rrf_k_parameter_affects_score_not_relative_order_within_single_list():
    ranked = [
        _ref("a.txt", 0, "first"),
        _ref("a.txt", 1, "second"),
    ]
    low_k = rrf_fuse(ranked, top_k=2, k=1)[0].rrf_score
    high_k = rrf_fuse(ranked, top_k=2, k=100)[0].rrf_score
    assert low_k > high_k
    order = [item.chunk_id for item in rrf_fuse(ranked, top_k=2, k=100)]
    assert order[0] == build_chunk_id("a.txt", 0)


def test_rrf_respects_top_k_cap():
    ranked = [_ref("f.txt", i, f"c{i}") for i in range(10)]
    fused = rrf_fuse(ranked, top_k=3, k=60)
    assert len(fused) == 3
