import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rag.text_splitter import split_text


def test_split_returns_chunks():
    text = "a" * 2000
    chunks = split_text(text, source="demo.txt", chunk_size=800, chunk_overlap=100)
    assert len(chunks) >= 2
    assert chunks[0].source == "demo.txt"
    assert chunks[0].chunk_index == 0


def test_split_empty():
    assert split_text("") == []
