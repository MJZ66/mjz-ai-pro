"""文本摘要工具。"""
from typing import Optional

from core.llm_client import LLMClient

MAX_INPUT_CHARS = 6000


def summarize(text: str, llm_client: Optional[LLMClient] = None) -> str:
    content = (text or "").strip()
    if not content:
        return "请输入需要摘要的文本。"
    if len(content) > MAX_INPUT_CHARS:
        content = content[:MAX_INPUT_CHARS] + "\n...(已截断)"

    if llm_client is None:
        return _fallback_summary(content)

    messages = [
        {
            "role": "system",
            "content": "你是文本摘要助手，请用 3-5 条要点概括输入内容，简洁中文输出。",
        },
        {"role": "user", "content": content},
    ]
    return llm_client.chat(messages, temperature=0.3)


def _fallback_summary(text: str) -> str:
    sentences = [s.strip() for s in text.replace("\n", "。").split("。") if s.strip()]
    picked = sentences[:3]
    if not picked:
        return "内容过短，无法生成摘要。"
    return "摘要要点：\n" + "\n".join(f"- {s}" for s in picked)


TOOL_NAME = "text_summary"
TOOL_DESCRIPTION = "对输入文本生成简短摘要（调用 LLM）"
