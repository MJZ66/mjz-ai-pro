"""统一日志。"""
import logging
import sys
from typing import Optional

_CONFIGURED = False


def setup_logging(level: int = logging.INFO) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root = logging.getLogger("mjz")
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(handler)
    _CONFIGURED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    setup_logging()
    if name and name.startswith("mjz"):
        return logging.getLogger(name)
    return logging.getLogger(f"mjz.{name or 'app'}")


def user_friendly_error(exc: Exception) -> str:
    """将异常转为用户可读提示。"""
    message = str(exc).strip()
    lowered = message.lower()
    if "api key" in lowered or "authentication" in lowered or "401" in lowered:
        return (
            "API Key 无效或未配置。若选 DeepSeek，请确认 .env 中为 DEEPSEEK_API_KEY；"
            "若选通义，请用 DASHSCOPE_API_KEY。侧边栏留空时会自动读 代码文件/.env。"
        )
    if "rate limit" in lowered or "429" in lowered:
        return "模型调用过于频繁，请稍后重试。"
    if "timeout" in lowered or "timed out" in lowered:
        return "请求超时，请检查网络或稍后重试。"
    if "404" in lowered and ("embedding" in lowered or "向量化" in message):
        return (
            "向量化接口不可用（404）。RAG 需通义 Embedding：请在 .env 配置 "
            "DASHSCOPE_API_KEY，EMBEDDING_MODEL=text-embedding-v3，"
            "EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1。"
            "若侧边栏选的是 DeepSeek，对话仍可用 DeepSeek，但向量必须用通义 Key。"
        )
    if "vector" in lowered or "chroma" in lowered or "embedding" in lowered:
        return "知识库加载或检索失败，请重新上传文档后重试。"
    if "pdf" in lowered or "parse" in lowered or "document" in lowered:
        return "文件解析失败，请确认文件格式为 txt / md / pdf 且内容可读。"
    if message:
        return f"操作失败：{message[:200]}"
    return "操作失败，请稍后重试或查看日志。"
