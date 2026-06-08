"""AI 对话工作台布局：自定义 Shell · 侧边栏 · 消息流 · 输入栏。"""
from __future__ import annotations

import html
from contextlib import contextmanager
from typing import Any, Callable, Dict, Generator, List, Optional

import streamlit as st

from agents.prompts import SYSTEM_PROMPTS
from core.config import (
    ConfigError,
    api_key_missing_message,
    format_key_loaded_hint,
    get_vendor_models,
    load_settings,
    normalize_sidebar_override,
    select_model_index,
    VENDOR_CHATTONGYI,
    VENDOR_DEEPSEEK,
)
from ui.theme import AGENT_ICONS, MODE_META, MODEL_PROVIDER_ICONS, WORK_MODE_ICONS
from utils.metrics import format_avg_response_ms, load_metrics

MODES = ["多轮对话", "RAG 知识库", "Agent 工具"]

_DEFAULT_META = {
    "title": "MJZ AI Pro",
    "subtitle": "多轮对话 · 知识库检索 · Agent 工具，一站式 AI 工作台",
    "tag": "",
}

DEFAULT_SUGGESTIONS = [
    "总结上传文档",
    "分析知识库内容",
    "生成项目汇报文案",
]

PRODUCT_SUBTITLE = "多轮对话 · 知识库检索 · Agent 工具，一站式 AI 工作台"


def _resolve_mode_meta(mode: str) -> dict:
    raw = MODE_META.get(mode, {})
    if not isinstance(raw, dict):
        return dict(_DEFAULT_META)
    return {
        "title": raw.get("title") or raw.get("tagline") or mode or _DEFAULT_META["title"],
        "subtitle": raw.get("subtitle") or raw.get("hint") or PRODUCT_SUBTITLE,
        "tag": raw.get("tag") or raw.get("icon") or "",
    }


def _nav_section(title: str, icon: str = "") -> None:
    glyph = html.escape(icon) if icon else ""
    st.markdown(
        f'<div class="ws-nav-section">'
        f'<span class="ws-nav-section-icon">{glyph}</span>'
        f'<span class="ws-nav-section-title">{html.escape(title)}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _mode_label(mode: str) -> str:
    return f"{WORK_MODE_ICONS.get(mode, '·')}  {mode}"


def _vendor_label(vendor: str) -> str:
    label = "通义千问" if vendor == VENDOR_CHATTONGYI else "DeepSeek"
    return f"{MODEL_PROVIDER_ICONS.get(label, '·')}  {label}"


def render_sidebar() -> Dict[str, Any]:
    """原生 sidebar 控件，返回运行配置。"""
    st.markdown(
        """
<div class="ws-logo">
  <div class="ws-logo-icon">M</div>
  <div class="ws-logo-text">
    <h2>MJZ AI Pro</h2>
    <p>AI 知识库与多智能体工作台</p>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="ws-sidebar-group">', unsafe_allow_html=True)
    _nav_section("工作模式", "◆")
    mode = st.radio(
        "工作模式",
        MODES,
        format_func=_mode_label,
        label_visibility="collapsed",
        key="ws_mode",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="ws-sidebar-group">', unsafe_allow_html=True)
    _nav_section("模型", "◇")
    vendor = st.radio(
        "模型提供商",
        [VENDOR_CHATTONGYI, VENDOR_DEEPSEEK],
        format_func=_vendor_label,
        label_visibility="collapsed",
        key="ws_vendor",
    )
    model_options = get_vendor_models(vendor)
    model_name = st.selectbox(
        "对话模型",
        model_options,
        index=select_model_index(vendor, model_options),
        label_visibility="collapsed",
        key="ws_model",
    )
    st.caption("Temperature")
    temperature = st.slider(
        "Temperature",
        0.0,
        2.0,
        0.7,
        0.1,
        label_visibility="collapsed",
        key="ws_temp",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if mode == "多轮对话":
        st.markdown('<div class="ws-sidebar-group">', unsafe_allow_html=True)
        _nav_section("智能体", "✦")
        agent_labels = [f"{AGENT_ICONS.get(k, '·')}  {k}" for k in SYSTEM_PROMPTS]
        agent_keys = list(SYSTEM_PROMPTS.keys())
        picked = st.selectbox(
            "角色",
            agent_labels,
            label_visibility="collapsed",
            key="ws_agent",
        )
        agent_type = agent_keys[agent_labels.index(picked)]
        keep_history = st.checkbox(
            "切换角色时保留历史",
            value=False,
            key="ws_keep_history",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        agent_type = "通用聊天助手"
        keep_history = False

    with st.expander("⚙ 设置", expanded=False):
        api_key_input = st.text_input(
            "API Key",
            type="password",
            placeholder="留空则读取 .env",
            key="ws_api_key",
        )
        try:
            preview = load_settings(
                api_key_override=api_key_input,
                vendor=vendor,
                model_override=model_name,
            )
            if not normalize_sidebar_override(api_key_input):
                hint = format_key_loaded_hint(preview.openai_api_key)
                if hint:
                    st.caption(hint)
                if mode == "RAG 知识库":
                    embed = format_key_loaded_hint(
                        preview.embedding_api_key, label="向量"
                    )
                    if embed:
                        st.caption(embed)
            elif not preview.openai_api_key:
                st.caption("Key 为空，请检查输入。")
        except ConfigError:
            st.caption(api_key_missing_message(vendor))

        snap = load_metrics()
        st.markdown(
            f"""
<div class="ws-inline-metrics">
  <span class="ws-inline-metric">访问 {snap.visit_count}</span>
  <span class="ws-inline-metric">响应 {html.escape(format_avg_response_ms(snap))}</span>
  <span class="ws-inline-metric">文档 {snap.documents_processed}</span>
</div>
""",
            unsafe_allow_html=True,
        )

    if mode == "多轮对话":
        if st.button("清空当前会话", use_container_width=True, key="ws_clear_chat"):
            st.session_state["_clear_chat_pending"] = True

        from utils.export_chat import build_export_filename, export_chat_to_markdown

        export_title = f"MJZ AI Pro · {agent_type}"
        export_md = export_chat_to_markdown(
            st.session_state.get("messages", []),
            title=export_title,
        )
        st.download_button(
            "导出当前对话 Markdown",
            data=export_md,
            file_name=build_export_filename(),
            mime="text/markdown",
            use_container_width=True,
            key="ws_export_chat",
        )

    return {
        "mode": mode,
        "vendor": vendor,
        "model_name": model_name,
        "temperature": temperature,
        "agent_type": agent_type,
        "keep_history": keep_history,
        "api_key_input": st.session_state.get("ws_api_key", ""),
    }


@contextmanager
def render_app_shell() -> Generator[Dict[str, Any], None, None]:
    """
    兼容旧调用：使用原生 st.sidebar + 主内容区。
    用法: with render_app_shell() as cfg: ...
    """
    with st.sidebar:
        cfg = render_sidebar()
    yield cfg


def render_main_header(
    mode: str,
    *,
    agent_type: str = "",
    title: str = "MJZ AI Pro",
    subtitle: str = "",
) -> None:
    """中央区域顶部标题（紧凑）。"""
    meta = _resolve_mode_meta(mode)
    sub = subtitle or meta["subtitle"] or PRODUCT_SUBTITLE
    if mode == "多轮对话" and agent_type and not subtitle:
        icon = AGENT_ICONS.get(agent_type, "◈")
        sub = f"{icon} {agent_type} · {sub}"

    st.markdown(
        f"""
<header class="main-header ws-main-header gsap-hero">
  <span class="ws-mode-tag gsap-hero-item">{html.escape(meta["tag"])}</span>
  <h1 class="gsap-hero-item">{html.escape(title or meta["title"])}</h1>
  <p class="ws-header-sub gsap-hero-item">{html.escape(sub)}</p>
</header>
""",
        unsafe_allow_html=True,
    )


def render_hero(mode: str, *, agent_type: str = "") -> None:
    """兼容旧名。"""
    render_main_header(mode, agent_type=agent_type)


def render_suggestion_cards(
    suggestions: List[str],
    *,
    key_prefix: str = "ws_suggest",
) -> None:
    if not suggestions:
        return
    st.markdown('<div class="ws-suggest-row gsap-suggest">', unsafe_allow_html=True)
    cols = st.columns(len(suggestions))
    for idx, (col, text) in enumerate(zip(cols, suggestions)):
        with col:
            if st.button(text, key=f"{key_prefix}_{idx}", use_container_width=True):
                st.session_state["_suggestion_prompt"] = text
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


render_suggestion_chips = render_suggestion_cards


def render_empty_state(
    icon: str,
    title: str,
    hint: str,
    *,
    suggestions: Optional[List[str]] = None,
    suggest_key: str = "ws_suggest",
) -> None:
    st.markdown(
        f"""
<div class="ws-empty gsap-empty">
  <div class="ws-empty-visual">
    <div class="ws-empty-icon">{html.escape(icon)}</div>
    <div class="ws-empty-glow"></div>
  </div>
  <h3>{html.escape(title)}</h3>
  <p class="ws-empty-hint">{html.escape(hint)}</p>
  <div class="ws-empty-features">
    <span>多轮上下文</span>
    <span>知识库检索</span>
    <span>Agent 工具</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    if suggestions:
        render_suggestion_cards(suggestions, key_prefix=suggest_key)


def _file_type_icon(name: str) -> str:
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return {
        "pdf": "📕",
        "docx": "📘",
        "doc": "📘",
        "xlsx": "📗",
        "xls": "📗",
        "txt": "📄",
        "md": "📄",
        "png": "🖼",
        "jpg": "🖼",
        "jpeg": "🖼",
    }.get(ext, "📎")


def _format_file_size(size: Optional[int]) -> str:
    if not size:
        return "—"
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def render_upload_panel(
    uploader_key: str,
    file_types: List[str],
    *,
    formats_hint: str = "",
    options_body: Optional[Callable[[Any], None]] = None,
    file_card: Optional[dict] = None,
    on_remove: Optional[Callable[[], None]] = None,
) -> Any:
    """底部输入区上方的上传扩展面板。"""
    from ui.upload_zone import render_drag_drop_uploader

    st.markdown('<div class="ws-upload-panel gsap-upload-panel">', unsafe_allow_html=True)
    st.markdown('<p class="ws-upload-panel-title">附件</p>', unsafe_allow_html=True)

    if file_card:
        fname = html.escape(file_card.get("filename", "文件"))
        fsize = _format_file_size(file_card.get("size"))
        ficon = _file_type_icon(file_card.get("filename", ""))
        st.markdown(
            f"""
<div class="ws-file-card">
  <span class="ws-file-icon">{ficon}</span>
  <div class="ws-file-meta">
    <span class="ws-file-name">{fname}</span>
    <span class="ws-file-size">{fsize}</span>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        if on_remove and st.button("删除文件", key=f"{uploader_key}_remove", type="secondary"):
            on_remove()
            st.rerun()

    uploaded = render_drag_drop_uploader(
        uploader_key,
        file_types,
        formats_hint=formats_hint,
        help_text="拖入或点击选择文件",
    )

    if options_body is not None:
        st.divider()
        options_body(uploaded)

    st.markdown("</div>", unsafe_allow_html=True)
    return uploaded


def render_attachment_chip(filename: str, detail: str = "") -> None:
    detail_html = (
        f'<span class="ws-attach-chip-detail">{html.escape(detail)}</span>'
        if detail
        else ""
    )
    st.markdown(
        f"""
<div class="ws-attach-chip gsap-card">
  <span class="ws-attach-chip-icon">📎</span>
  <span class="ws-attach-chip-name">{html.escape(filename)}</span>
  {detail_html}
</div>
""",
        unsafe_allow_html=True,
    )


def render_attachment_card(title: str, body: str) -> None:
    render_attachment_chip(title, body)


def render_citation_cards(items: List[Any]) -> None:
    if not items:
        return
    blocks = ""
    for item in items:
        source = html.escape(getattr(item, "source", "未知来源"))
        idx = html.escape(str(getattr(item, "chunk_index", "")))
        preview = html.escape(getattr(item, "content", "")[:280])
        blocks += f"""
<div class="ws-card ws-card-cite gsap-card">
  <p class="ws-card-label">引用来源</p>
  <p class="ws-card-title">{source} · #{idx}</p>
  <p class="ws-card-body">{preview}…</p>
</div>
"""
    st.markdown(f'<div class="ws-card-stack">{blocks}</div>', unsafe_allow_html=True)


def render_chat_messages(
    messages: List[dict],
    format_fn: Callable[[Any], str],
    *,
    show_empty: bool = True,
    empty_icon: str = "✦",
    empty_title: str = "开始对话",
    empty_hint: str = "选择下方建议，或在底部输入框开始对话",
    suggestions: Optional[List[str]] = None,
) -> None:
    visible = [m for m in messages if m.get("role") != "system"]

    st.markdown('<section class="chat-stage">', unsafe_allow_html=True)

    if show_empty and len(visible) <= 1:
        render_empty_state(
            empty_icon,
            empty_title,
            empty_hint,
            suggestions=suggestions or DEFAULT_SUGGESTIONS,
        )

    if len(visible) > 1:
        st.markdown('<div class="ws-chat-thread">', unsafe_allow_html=True)
    for msg in visible:
        role = msg.get("role", "assistant")
        with st.chat_message(role):
            st.markdown(format_fn(msg.get("content", "")))
    if len(visible) > 1:
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</section>", unsafe_allow_html=True)


def render_composer_attach(
    uploader_key: str,
    file_types: List[str],
    *,
    formats_hint: str = "",
    options_body: Optional[Callable[[Any], None]] = None,
) -> Any:
    """兼容旧 API：渲染上传面板。"""
    return render_upload_panel(
        uploader_key,
        file_types,
        formats_hint=formats_hint,
        options_body=options_body,
    )


def render_input_bar(
    placeholder: str = "输入消息，Enter 发送…",
    *,
    key: str = "ws_chat_input",
    attachment_chip: Optional[tuple[str, str]] = None,
    upload_panel_renderer: Optional[Callable[[], Any]] = None,
) -> Optional[str]:
    """底部 chat_input（使用 Streamlit 原生 st.chat_input）。"""
    if attachment_chip:
        render_attachment_chip(attachment_chip[0], attachment_chip[1])
    user_input = st.chat_input(placeholder, key=key)
    st.caption("MJZ AI 可能会犯错，请核实重要信息")
    return user_input


# 兼容旧名称
render_chat_header = render_hero
render_chat_area = render_chat_messages
render_chat_messages = render_chat_area

__all__ = [
    "DEFAULT_SUGGESTIONS",
    "PRODUCT_SUBTITLE",
    "render_app_shell",
    "render_sidebar",
    "render_main_header",
    "render_hero",
    "render_chat_header",
    "render_chat_messages",
    "render_chat_area",
    "render_empty_state",
    "render_suggestion_cards",
    "render_suggestion_chips",
    "render_input_bar",
    "render_upload_panel",
    "render_attachment_card",
    "render_attachment_chip",
    "render_citation_cards",
    "render_composer_attach",
]
