import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.config import (  # noqa: E402
    DEFAULT_BASE_URL,
    VENDOR_DEEPSEEK,
    load_settings,
)


def test_deepseek_uses_dashscope_for_embeddings(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-tongyi")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-dash")
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("EMBEDDING_BASE_URL", raising=False)

    s = load_settings(vendor=VENDOR_DEEPSEEK)
    assert s.openai_api_key == "sk-deepseek"  # DEEPSEEK_API_KEY，非 OPENAI
    assert s.embedding_api_key == "sk-dash"
    assert "dashscope" in s.embedding_base_url
    assert s.embedding_model == "text-embedding-v3"
    assert "deepseek" in s.openai_base_url


def test_tongyi_embeddings_share_compatible_base(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-tongyi")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-tongyi")
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)

    s = load_settings()
    assert s.embedding_api_key == "sk-tongyi"
    assert s.embedding_base_url.endswith("/v1")
    assert "dashscope" in s.embedding_base_url or DEFAULT_BASE_URL in s.embedding_base_url
