"""config 模块测试。"""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config import (  # noqa: E402
    ConfigError,
    VENDOR_CHATTONGYI,
    VENDOR_DEEPSEEK,
    api_key_missing_message,
    load_settings,
    select_model_index,
)
from config import get_vendor_base_url, resolve_api_key  # noqa: E402


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in [
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "MODEL_NAME",
        "EMBEDDING_MODEL",
        "VECTOR_STORE_DIR",
        "DASHSCOPE_API_KEY",
        "DEEPSEEK_API_KEY",
        "DASHSCOPE_BASE_URL",
        "DEEPSEEK_BASE_URL",
        "DASHSCOPE_MODEL",
        "DEEPSEEK_MODEL",
    ]:
        monkeypatch.delenv(key, raising=False)


def test_load_settings_openai_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("MODEL_NAME", "gpt-test")
    s = load_settings(vendor=VENDOR_CHATTONGYI)
    assert s.openai_api_key == "sk-test"
    assert s.openai_base_url == "https://api.example.com/v1"
    assert s.model_name == "gpt-test"


def test_resolve_dashscope_fallback(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "ds-key")
    assert resolve_api_key(VENDOR_CHATTONGYI, "") == "ds-key"


def test_resolve_sidebar_priority(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "env-key")
    assert resolve_api_key(VENDOR_CHATTONGYI, "sidebar") == "sidebar"


def test_deepseek_no_dashscope_mix(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "only-ds")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert resolve_api_key(VENDOR_DEEPSEEK, "") == ""


def test_deepseek_prefers_deepseek_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-tongyi")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deep")
    assert resolve_api_key(VENDOR_DEEPSEEK, "") == "sk-deep"


def test_config_error_when_missing_key():
    s = load_settings(vendor=VENDOR_CHATTONGYI)
    with pytest.raises(ConfigError):
        s.ensure_valid(require_api_key=True)


def test_vendor_base_url(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_BASE_URL", "https://dash.custom/v1")
    assert "dash.custom" in get_vendor_base_url(VENDOR_CHATTONGYI)


def test_api_key_messages():
    assert "OPENAI" in api_key_missing_message(VENDOR_CHATTONGYI) or "DASHSCOPE" in api_key_missing_message(
        VENDOR_CHATTONGYI
    )


def test_select_model_index(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_MODEL", "qwen-max")
    assert select_model_index(
        VENDOR_CHATTONGYI,
        ["qwen-plus", "qwen-max", "qwen-turbo"],
    ) == 1
