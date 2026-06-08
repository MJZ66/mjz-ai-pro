"""bm25_index 模块测试。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rag.bm25_index import BM25Index, tokenize  # noqa: E402
from rag.hybrid_fusion import build_chunk_id  # noqa: E402
from rag.text_splitter import TextChunk  # noqa: E402


def test_tokenize_mixed_zh_en():
    tokens = tokenize("Hello MJZ 世界 RAG123 系统 demo")
    assert "hello" in tokens
    assert "mjz" in tokens
    assert "rag123" in tokens or ("rag" in tokens and "123" in tokens)
    assert "demo" in tokens
    assert "世" in tokens
    assert "界" in tokens
    assert "系" in tokens
    assert "统" in tokens


def test_search_keyword_hit():
    index = BM25Index()
    index.add_chunks(
        [
            TextChunk(content="MJZ AI Pro is a RAG demo system.", source="a.md", chunk_index=0),
            TextChunk(content="Unrelated weather forecast for tomorrow.", source="b.md", chunk_index=0),
        ]
    )
    hits = index.search("RAG demo", top_k=2)
    assert hits
    assert hits[0][0] == build_chunk_id("a.md", 0)
    assert hits[0][1] > 0


def test_save_and_load(tmp_path):
    index = BM25Index()
    index.add_chunks(
        [
            TextChunk(content="知识库检索增强生成", source="kb.md", chunk_index=0),
            TextChunk(content="keyword retrieval baseline", source="kb.md", chunk_index=1),
        ]
    )
    index.save(str(tmp_path))

    loaded = BM25Index.load(str(tmp_path))
    assert len(loaded) == 2

    zh_hits = loaded.search("检索", top_k=1)
    en_hits = loaded.search("retrieval", top_k=1)
    assert zh_hits[0][0] == build_chunk_id("kb.md", 0)
    assert en_hits[0][0] == build_chunk_id("kb.md", 1)


def test_add_chunks_incremental():
    index = BM25Index()
    first = index.add_chunks(
        [TextChunk(content="first batch alpha", source="one.txt", chunk_index=0)]
    )
    second = index.add_chunks(
        [
            TextChunk(content="second batch beta", source="two.txt", chunk_index=0),
            TextChunk(content="duplicate should skip", source="one.txt", chunk_index=0),
        ]
    )
    assert first == 1
    assert second == 1
    assert len(index) == 2

    alpha_hits = index.search("alpha", top_k=1)
    beta_hits = index.search("beta", top_k=1)
    assert alpha_hits[0][0] == build_chunk_id("one.txt", 0)
    assert beta_hits[0][0] == build_chunk_id("two.txt", 0)
