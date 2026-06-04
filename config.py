"""兼容层：请优先使用 core.config。"""
from core.config import (  # noqa: F401
    AppSettings,
    CHATONGYI_MODELS,
    ConfigError,
    DEEPSEEK_MODELS,
    VENDOR_CHATTONGYI,
    VENDOR_DEEPSEEK,
    api_key_missing_message,
    get_vendor_models,
    load_settings,
    select_model_index,
)

# 兼容旧测试中的 resolve_api_key
def resolve_api_key(vendor: str, sidebar_key: str = "") -> str:
    settings = load_settings(api_key_override=sidebar_key, vendor=vendor)
    return settings.openai_api_key


def get_vendor_base_url(vendor: str) -> str:
    return load_settings(vendor=vendor).openai_base_url
