import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.config import load_settings


def test_embedding_and_vector_defaults(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    s = load_settings()
    assert s.embedding_model
    assert "vector" in s.vector_store_dir.lower() or "data" in s.vector_store_dir
