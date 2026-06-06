"""可复用 UI 组件（HTML + Streamlit）。"""
from __future__ import annotations

import html

import streamlit as st

from utils.metrics import MetricsSnapshot, format_avg_response_ms


def render_metrics_dashboard(snap: MetricsSnapshot) -> None:
    """主区域数据概览条。"""
    st.markdown(
        f"""
<div class="mjz-dash">
  <div class="mjz-stat-card mjz-stat-a">
    <span class="mjz-stat-label">访问量</span>
    <span class="mjz-stat-value">{snap.visit_count}</span>
    <span class="mjz-stat-sub">会话累计</span>
  </div>
  <div class="mjz-stat-card mjz-stat-b">
    <span class="mjz-stat-label">平均响应</span>
    <span class="mjz-stat-value">{html.escape(format_avg_response_ms(snap))}</span>
    <span class="mjz-stat-sub">LLM 端到端</span>
  </div>
  <div class="mjz-stat-card mjz-stat-c">
    <span class="mjz-stat-label">文档处理</span>
    <span class="mjz-stat-value">{snap.documents_processed}</span>
    <span class="mjz-stat-sub">{snap.chunks_indexed} 片段已索引</span>
  </div>
  <div class="mjz-stat-card mjz-stat-d">
    <span class="mjz-stat-label">附件解析</span>
    <span class="mjz-stat-value">{snap.attachments_parsed}</span>
    <span class="mjz-stat-sub">{snap.llm_calls} 次模型调用</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_sidebar_mini_stats(visit_count: int, avg_response: str) -> None:
    """侧边栏精简统计。"""
    st.markdown(
        f"""
<div class="mjz-sidebar-mini-stats">
  <div class="mjz-mini-stat">
    <span>访问量</span>
    <strong>{visit_count}</strong>
  </div>
  <div class="mjz-mini-stat">
    <span>平均响应</span>
    <strong>{html.escape(avg_response)}</strong>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_ready_banner(icon: str, title: str, hint: str) -> None:
    st.markdown(
        f"""
<div class="mjz-ready">
  <div class="mjz-ready-icon">{html.escape(icon)}</div>
  <div>
    <p class="mjz-ready-title">{html.escape(title)}</p>
    <p class="mjz-ready-hint">{html.escape(hint)}</p>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_step_flow(steps: list[tuple[str, str]]) -> None:
    """横向步骤引导（如 RAG 流程）。"""
    items = ""
    for i, (num, label) in enumerate(steps, start=1):
        items += f"""
<div class="mjz-step">
  <span class="mjz-step-num">{num}</span>
  <span class="mjz-step-text">{html.escape(label)}</span>
</div>
"""
        if i < len(steps):
            items += '<div class="mjz-step-line"></div>'
    st.markdown(f'<div class="mjz-steps">{items}</div>', unsafe_allow_html=True)


def render_tool_cards(tools: list[tuple[str, str]]) -> None:
    cards = ""
    for name, desc in tools:
        cards += f"""
<div class="mjz-tool-card">
  <strong>{html.escape(name)}</strong>
  <p>{html.escape(desc)}</p>
</div>
"""
    st.markdown(f'<div class="mjz-tool-grid">{cards}</div>', unsafe_allow_html=True)


def render_upload_visual(title: str = "拖入文件", subtitle: str = "") -> None:
    st.markdown(
        f"""
<div class="mjz-upload-visual">
  <div class="mjz-upload-ring"></div>
  <div class="mjz-upload-icon">↑</div>
  <p class="mjz-upload-title">{html.escape(title)}</p>
  <p class="mjz-upload-sub">{html.escape(subtitle)}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def render_result_card(title: str, body: str, *, variant: str = "default") -> None:
    """纯文本结果卡片。"""
    cls = f"mjz-result mjz-result-{variant}"
    st.markdown(
        f"""
<div class="{cls}">
  <p class="mjz-result-title">{html.escape(title)}</p>
  <div class="mjz-result-body">{html.escape(body)}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_markdown_result(title: str, body: str, *, variant: str = "default") -> None:
    """Markdown 结果（RAG / 摘要等）。"""
    cls = f"mjz-result mjz-result-{variant}"
    st.markdown(
        f'<div class="{cls}"><p class="mjz-result-title">{html.escape(title)}</p></div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.markdown(body)
