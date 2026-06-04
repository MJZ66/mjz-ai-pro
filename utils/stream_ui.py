"""稳定的流式输出（避免 placeholder.markdown 触发 React removeChild）。"""
from __future__ import annotations

from typing import Callable, List, Optional

import streamlit as st

from agents.chat_agent import ChatAgent


def stream_chat_into_message(
    agent: ChatAgent,
    messages: List[dict],
    *,
    temperature: float = 0.7,
    model: Optional[str] = None,
) -> str:
    """
    在 assistant 气泡中安全输出回复。
    优先一次性渲染；若支持则使用 write_stream。
    """
    with st.chat_message("assistant"):

        def _token_generator():
            for delta in agent.llm.stream_chat(
                agent.ensure_system(list(messages)),
                model=model,
                temperature=temperature,
            ):
                yield delta

        if hasattr(st, "write_stream"):
            try:
                text = st.write_stream(_token_generator()) or ""
                if text:
                    return text
            except Exception:
                pass

        with st.spinner("生成中…"):
            text = agent.stream_reply(
                messages,
                temperature=temperature,
                model=model,
                on_delta=None,
            )
        st.markdown(text)
        return text
