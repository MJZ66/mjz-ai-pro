"""MJZ AI Pro — Chat Workspace 主题与样式注入。"""
from __future__ import annotations

from pathlib import Path

WORK_MODE_ICONS = {
    "多轮对话": "💬",
    "RAG 知识库": "📚",
    "Agent 工具": "🛠️",
}

MODEL_PROVIDER_ICONS = {
    "通义千问": "◉",
    "DeepSeek": "◉",
}

MODE_META = {
    "多轮对话": {
        "title": "MJZ AI Pro",
        "subtitle": "多轮对话 · 知识库检索 · Agent 工具，一站式 AI 工作台",
        "tag": "对话",
    },
    "RAG 知识库": {
        "title": "知识库问答",
        "subtitle": "上传文档，基于检索增强生成回答",
        "tag": "RAG",
    },
    "Agent 工具": {
        "title": "Agent 工具箱",
        "subtitle": "计算器、文本摘要与可扩展工具",
        "tag": "Tools",
    },
}

AGENT_ICONS = {
    "通用聊天助手": "💬",
    "法律助手": "⚖",
    "代码助手": "⌘",
    "简历分析助手": "📋",
    "文件助手": "📁",
    "小红书爆款文案助手": "✦",
}

def _load_css() -> str:
    css_path = Path(__file__).with_name("theme.css")
    return css_path.read_text(encoding="utf-8")


def inject_custom_css() -> None:
    """注入工作台 CSS。"""
    import streamlit as st

    st.markdown(f"<style>{_load_css()}</style>", unsafe_allow_html=True)


inject_theme = inject_custom_css
