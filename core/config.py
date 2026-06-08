"""统一配置管理，兼容 OpenAI Compatible API。"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

# 代码文件/ 目录（与 app.py、.env 同级），避免 Streamlit 工作目录变化导致读不到 .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_project_env() -> Path:
    """加载项目根目录下的 .env，并兼容当前工作目录中的 .env。"""
    primary = PROJECT_ROOT / ".env"
    if primary.is_file():
        load_dotenv(primary, override=False)
    load_dotenv(override=False)
    return primary


load_project_env()

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"
DEFAULT_EMBEDDING_MODEL = "text-embedding-v3"
DEFAULT_VECTOR_STORE_DIR = "data/vector_store"
DEFAULT_RAG_RETRIEVAL_MODE = "vector"
VALID_RAG_RETRIEVAL_MODES = frozenset({"vector", "hybrid"})

# 厂商常量（UI 层使用）
VENDOR_CHATTONGYI = "ChatTongYi"
VENDOR_DEEPSEEK = "DeepSeek"

CHATONGYI_MODELS = ["qwen-plus", "qwen-max", "qwen-turbo"]
DEEPSEEK_MODELS = ["deepseek-chat", "deepseek-reasoner"]


class ConfigError(Exception):
    """配置缺失或无效。"""


@dataclass
class AppSettings:
    openai_api_key: str
    openai_base_url: str
    model_name: str
    embedding_model: str
    embedding_api_key: str
    embedding_base_url: str
    vector_store_dir: str
    vendor: str = VENDOR_CHATTONGYI
    rag_retrieval_mode: str = DEFAULT_RAG_RETRIEVAL_MODE

    def validate(self, require_api_key: bool = True) -> List[str]:
        errors: List[str] = []
        if require_api_key and not self.openai_api_key:
            errors.append(
                "未配置 OPENAI_API_KEY（或厂商专用 Key）。"
                "请在 .env 或侧边栏中填写。"
            )
        if not self.openai_base_url:
            errors.append("OPENAI_BASE_URL 不能为空。")
        if not self.model_name:
            errors.append("MODEL_NAME 不能为空。")
        if not self.embedding_model:
            errors.append("EMBEDDING_MODEL 不能为空。")
        if not self.embedding_api_key:
            errors.append(
                "未配置向量模型 API Key。"
                "RAG 需 EMBEDDING_API_KEY 或 DASHSCOPE_API_KEY（DeepSeek 对话时也需通义 Key 做向量化）。"
            )
        if not self.embedding_base_url:
            errors.append("EMBEDDING_BASE_URL 不能为空。")
        return errors

    def ensure_valid(self, require_api_key: bool = True) -> None:
        errors = self.validate(require_api_key=require_api_key)
        if errors:
            raise ConfigError(" ".join(errors))


def _first_non_empty(*values: Optional[str]) -> str:
    for value in values:
        if value and str(value).strip():
            return str(value).strip()
    return ""


def normalize_sidebar_override(value: Optional[str]) -> str:
    """侧边栏留空时不覆盖 .env。"""
    return (value or "").strip()


def resolve_rag_retrieval_mode(raw: Optional[str] = None) -> str:
    """
    解析 RAG 检索模式：vector（默认）或 hybrid。
    非法值静默回退为 vector，与项目其他 env 默认值策略一致。
    """
    mode = _first_non_empty(
        raw,
        os.getenv("RAG_RETRIEVAL_MODE"),
        DEFAULT_RAG_RETRIEVAL_MODE,
    ).lower()
    if mode in VALID_RAG_RETRIEVAL_MODES:
        return mode
    return DEFAULT_RAG_RETRIEVAL_MODE


def _normalize_openai_base_url(url: str) -> str:
    """保证 OpenAI SDK 使用带 /v1 的 base_url。"""
    u = (url or "").strip().rstrip("/")
    if not u:
        return u
    if u.endswith("/v1"):
        return u
    return f"{u}/v1"


def _resolve_embedding_settings(
    vendor: str,
    chat_api_key: str,
) -> tuple[str, str, str]:
    """
    解析 RAG 向量化用的 Key / Base URL / Model。
    DeepSeek 不提供 embedding，固定走通义 compatible-mode。
    """
    model = _first_non_empty(
        os.getenv("EMBEDDING_MODEL"),
        DEFAULT_EMBEDDING_MODEL,
    )
    custom_base = _first_non_empty(os.getenv("EMBEDDING_BASE_URL"))
    custom_key = _first_non_empty(os.getenv("EMBEDDING_API_KEY"))

    dash_key = _first_non_empty(
        custom_key,
        os.getenv("DASHSCOPE_API_KEY"),
        os.getenv("OPENAI_API_KEY"),
    )
    dash_base = _normalize_openai_base_url(
        custom_base
        or os.getenv("DASHSCOPE_BASE_URL")
        or DEFAULT_BASE_URL
    )

    if vendor == VENDOR_DEEPSEEK:
        return dash_key, dash_base, model

    chat_base = _normalize_openai_base_url(
        custom_base or os.getenv("OPENAI_BASE_URL") or DEFAULT_BASE_URL
    )
    embed_key = _first_non_empty(custom_key, chat_api_key)
    embed_base = custom_base or chat_base
    embed_base = _normalize_openai_base_url(embed_base)
    return embed_key, embed_base, model


def load_settings(
    *,
    api_key_override: str = "",
    base_url_override: str = "",
    model_override: str = "",
    vendor: str = VENDOR_CHATTONGYI,
) -> AppSettings:
    """
    从环境变量加载配置，支持 UI 覆盖项。
    优先 OPENAI_*，并兼容 DASHSCOPE_* / DEEPSEEK_*。
    """
    sidebar_key = normalize_sidebar_override(api_key_override)

    if vendor == VENDOR_DEEPSEEK:
        env_key = _first_non_empty(
            sidebar_key,
            os.getenv("DEEPSEEK_API_KEY"),
            # 勿把通义 OPENAI_API_KEY 用于 DeepSeek 对话，否则易报 401
        )
        env_base = _normalize_openai_base_url(
            _first_non_empty(
                base_url_override,
                os.getenv("DEEPSEEK_BASE_URL"),
                os.getenv("OPENAI_BASE_URL"),
                "https://api.deepseek.com",
            )
        )
        env_model = _first_non_empty(
            model_override,
            os.getenv("DEEPSEEK_MODEL"),
            os.getenv("MODEL_NAME"),
            "deepseek-chat",
        )
    else:
        env_key = _first_non_empty(
            sidebar_key,
            os.getenv("DASHSCOPE_API_KEY"),
            os.getenv("OPENAI_API_KEY"),
        )
        env_base = _normalize_openai_base_url(
            _first_non_empty(
                base_url_override,
                os.getenv("DASHSCOPE_BASE_URL"),
                os.getenv("OPENAI_BASE_URL"),
                DEFAULT_BASE_URL,
            )
        )
        env_model = _first_non_empty(
            model_override,
            os.getenv("DASHSCOPE_MODEL"),
            os.getenv("MODEL_NAME"),
            DEFAULT_MODEL,
        )

    vector_dir = _first_non_empty(
        os.getenv("VECTOR_STORE_DIR"),
        DEFAULT_VECTOR_STORE_DIR,
    )

    embed_key, embed_base, embed_model = _resolve_embedding_settings(
        vendor, env_key
    )

    rag_mode = resolve_rag_retrieval_mode()

    return AppSettings(
        openai_api_key=env_key,
        openai_base_url=env_base,
        model_name=env_model,
        embedding_model=embed_model,
        embedding_api_key=embed_key,
        embedding_base_url=embed_base,
        vector_store_dir=str(Path(vector_dir).resolve()),
        vendor=vendor,
        rag_retrieval_mode=rag_mode,
    )


def get_vendor_models(vendor: str) -> List[str]:
    if vendor == VENDOR_DEEPSEEK:
        return list(DEEPSEEK_MODELS)
    return list(CHATONGYI_MODELS)


def select_model_index(vendor: str, model_options: List[str]) -> int:
    settings = load_settings(vendor=vendor)
    if settings.model_name in model_options:
        return model_options.index(settings.model_name)
    return 0


def api_key_missing_message(vendor: str = VENDOR_CHATTONGYI) -> str:
    env_hint = f"项目 .env 路径：{PROJECT_ROOT / '.env'}"
    if vendor == VENDOR_DEEPSEEK:
        return (
            "未检测到 DeepSeek API Key。请在 .env 配置 DEEPSEEK_API_KEY，"
            f"或在侧边栏填写。{env_hint}"
        )
    return (
        "未检测到通义 API Key。请在 .env 配置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY，"
        f"或在侧边栏填写。{env_hint}"
    )


def format_key_loaded_hint(api_key: str, *, label: str = "对话") -> str:
    if not api_key:
        return ""
    return f"已从 .env 加载{label} Key（…{api_key[-4:]}）"
