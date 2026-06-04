"""LLM 统一调用封装。"""
from typing import Callable, Generator, Iterable, List, Optional

from openai import OpenAI

from core.config import AppSettings
from utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """OpenAI Compatible API 客户端。"""

    def __init__(self, settings: AppSettings):
        settings.ensure_valid(require_api_key=True)
        self.settings = settings
        self._client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self._embedding_client = OpenAI(
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_base_url,
        )

    @property
    def client(self) -> OpenAI:
        return self._client

    def chat(
        self,
        messages: List[dict],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        model = model or self.settings.model_name
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=False,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.exception("chat 调用失败")
            raise RuntimeError(f"模型调用失败：{exc}") from exc

    def stream_chat(
        self,
        messages: List[dict],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        model = model or self.settings.model_name
        try:
            stream = self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            for chunk in stream:
                try:
                    delta = chunk.choices[0].delta.content or ""
                except (AttributeError, IndexError, TypeError):
                    delta = ""
                if delta:
                    yield delta
        except Exception as exc:
            logger.exception("stream_chat 调用失败")
            raise RuntimeError(f"流式模型调用失败：{exc}") from exc

    def stream_chat_collect(
        self,
        messages: List[dict],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        on_delta: Optional[Callable[[str], None]] = None,
    ) -> str:
        """流式输出并拼接为完整字符串，可选每段回调（如 Streamlit placeholder）。"""
        full = ""
        for delta in self.stream_chat(
            messages, model=model, temperature=temperature
        ):
            full += delta
            if on_delta:
                on_delta(full)
        return full

    def embed_texts(self, texts: Iterable[str]) -> List[List[float]]:
        try:
            response = self._embedding_client.embeddings.create(
                model=self.settings.embedding_model,
                input=list(texts),
            )
            return [item.embedding for item in response.data]
        except Exception as exc:
            logger.exception("embeddings 调用失败")
            hint = ""
            err = str(exc).lower()
            if "404" in err:
                hint = (
                    "（Embedding 接口 404：请确认已配置 DASHSCOPE_API_KEY，"
                    f"且 EMBEDDING_MODEL={self.settings.embedding_model} 与"
                    f" EMBEDDING_BASE_URL={self.settings.embedding_base_url} 匹配通义 compatible-mode）"
                )
            raise RuntimeError(f"向量化失败：{exc}{hint}") from exc
