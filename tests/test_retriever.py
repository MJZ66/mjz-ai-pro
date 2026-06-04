import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

pytest.importorskip("chromadb")

from rag.text_splitter import split_text
from rag.vector_store import VectorStore


def test_vector_store_ingest_and_count(tmp_path):
    store = VectorStore(str(tmp_path / "chroma_test"))
    chunks = split_text("MJZ AI Pro RAG system demo content.", source="demo.md")
    embeddings = [[0.01 * (i + 1)] * 16 for i in range(len(chunks))]
    n = store.add_chunks(chunks, embeddings)
    assert n == len(chunks)
    assert store.count() >= n
