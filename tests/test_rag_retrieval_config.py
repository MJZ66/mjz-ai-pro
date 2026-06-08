"""RAG_RETRIEVAL_MODE 配置测试。"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

pytest.importorskip("chromadb")

from core.config import (  # noqa: E402
    DEFAULT_RAG_RETRIEVAL_MODE,
    load_settings,
    resolve_rag_retrieval_mode,
)
from rag.rag_agent import RAGAgent  # noqa: E402
from rag.vector_store import VectorStore  # noqa: E402


class FakeLLM:
    def embed_texts(self, texts):
        return [[0.01] * 16 for _ in texts]


def test_resolve_rag_retrieval_mode_default(monkeypatch):
    monkeypatch.delenv("RAG_RETRIEVAL_MODE", raising=False)
    assert resolve_rag_retrieval_mode() == DEFAULT_RAG_RETRIEVAL_MODE == "vector"


def test_resolve_rag_retrieval_mode_hybrid(monkeypatch):
    monkeypatch.setenv("RAG_RETRIEVAL_MODE", "hybrid")
    assert resolve_rag_retrieval_mode() == "hybrid"


def test_resolve_rag_retrieval_mode_case_insensitive(monkeypatch):
    monkeypatch.setenv("RAG_RETRIEVAL_MODE", "HYBRID")
    assert resolve_rag_retrieval_mode() == "hybrid"


def test_resolve_rag_retrieval_mode_invalid_fallback_to_vector(monkeypatch):
    monkeypatch.setenv("RAG_RETRIEVAL_MODE", "semantic")
    assert resolve_rag_retrieval_mode() == "vector"


def test_load_settings_includes_rag_retrieval_mode(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("RAG_RETRIEVAL_MODE", "hybrid")
    settings = load_settings()
    assert settings.rag_retrieval_mode == "hybrid"


def test_rag_agent_retriever_mode_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_RETRIEVAL_MODE", "hybrid")
    store = VectorStore(str(tmp_path / "chroma"))
    agent = RAGAgent(FakeLLM(), store)
    assert agent.retriever.mode == "hybrid"


def test_rag_agent_retriever_mode_default_vector(tmp_path, monkeypatch):
    monkeypatch.delenv("RAG_RETRIEVAL_MODE", raising=False)
    store = VectorStore(str(tmp_path / "chroma"))
    agent = RAGAgent(FakeLLM(), store)
    assert agent.retriever.mode == "vector"
