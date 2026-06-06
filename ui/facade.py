"""
UI 统一门面 — app.py 只从这里导入 UI 层内容。

设计原则：
1. 所有符号先在模块顶层注册兜底值，import 时立即可用
2. 子模块加载成功则覆盖兜底，失败则保留兜底
3. 模块末尾校验 __all__，缺失项打印 [FACADE WARNING]
"""
from __future__ import annotations

import importlib
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional

# ---------------------------------------------------------------------------
# app.py 当前实际导入清单（唯一真相源）
# ---------------------------------------------------------------------------
_APP_REQUIRED: List[str] = [
    "AGENT_ICONS",
    "RAG_UPLOAD_TYPES",
    "inject_custom_css",
    "inject_gsap_animations",
    "is_new_upload",
    "render_chat_area",
    "render_citation_cards",
    "render_drag_drop_uploader",
    "render_input_bar",
    "render_main_header",
    "render_sidebar",
    "render_sidebar_open_button",
    "render_sidebar_collapse_button",
    "render_upload_panel",
    "streamlit_panel",
    "upload_fingerprint",
]

# ---------------------------------------------------------------------------
# 兜底常量
# ---------------------------------------------------------------------------

AGENT_ICONS: Dict[str, str] = {
    "通用聊天助手": "💬",
    "RAG 知识库": "📚",
    "Agent 工具": "🛠️",
    "代码助手": "💻",
    "数据分析助手": "📊",
    "法律助手": "⚖",
    "简历分析助手": "📋",
    "文件助手": "📁",
    "小红书爆款文案助手": "✦",
}

WORK_MODE_ICONS: Dict[str, str] = {
    "多轮对话": "💬",
    "RAG 知识库": "📚",
    "Agent 工具": "🛠️",
}

MODEL_PROVIDER_ICONS: Dict[str, str] = {
    "通义千问": "◉",
    "DeepSeek": "◉",
}

MODEL_ICONS: Dict[str, str] = dict(MODEL_PROVIDER_ICONS)

MODE_META: Dict[str, dict] = {
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

RAG_UPLOAD_TYPES: List[str] = ["txt", "md", "pdf", "docx", "xlsx", "xls"]

# ---------------------------------------------------------------------------
# 兜底函数
# ---------------------------------------------------------------------------


def _noop(*_args: Any, **_kwargs: Any) -> Any:
    return None


def _noop_bool(*_args: Any, **_kwargs: Any) -> bool:
    return False


def _noop_str(*_args: Any, **_kwargs: Any) -> str:
    return ""


@contextmanager
def _fallback_render_app_shell() -> Generator[Dict[str, Any], None, None]:
    yield {
        "mode": "多轮对话",
        "vendor": "chat_tongyi",
        "model_name": "",
        "temperature": 0.7,
        "agent_type": "通用聊天助手",
        "keep_history": False,
        "api_key_input": "",
    }


def _fallback_inject_custom_css() -> None:
    try:
        import streamlit as st

        css_path = Path(__file__).with_name("theme.css")
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception:
        pass


def _fallback_inject_gsap_animations() -> None:
    pass


# 导出注册表：name -> object（先兜底，后覆盖）
_REGISTRY: Dict[str, Any] = {
    # 常量
    "AGENT_ICONS": AGENT_ICONS,
    "WORK_MODE_ICONS": WORK_MODE_ICONS,
    "MODEL_PROVIDER_ICONS": MODEL_PROVIDER_ICONS,
    "MODEL_ICONS": MODEL_ICONS,
    "MODE_META": MODE_META,
    "RAG_UPLOAD_TYPES": RAG_UPLOAD_TYPES,
    # app.py 必需函数
    "inject_custom_css": _fallback_inject_custom_css,
    "inject_gsap_animations": _fallback_inject_gsap_animations,
    "is_new_upload": _noop_bool,
    "upload_fingerprint": _noop_str,
    "render_sidebar": _noop,
    "render_sidebar_toggle": _noop,
    "render_sidebar_open_button": _noop,
    "render_sidebar_collapse_button": _noop,
    "render_main_header": _noop,
    "render_chat_area": _noop,
    "render_citation_cards": _noop,
    "render_input_bar": _noop,
    "render_upload_panel": _noop,
    "render_drag_drop_uploader": _noop,
    "streamlit_panel": _noop,
    # 扩展 / 兼容
    "inject_theme": _fallback_inject_custom_css,
    "render_app_shell": _fallback_render_app_shell,
    "render_hero": _noop,
    "render_empty_state": _noop,
    "render_suggestion_cards": _noop,
    "render_attachment_card": _noop,
    "render_composer_attach": _noop,
}


def _merge_dict(base: Dict[str, Any], extra: Any) -> None:
    if isinstance(extra, dict):
        base.update(extra)


def _safe_import(name: str) -> Any | None:
    try:
        return importlib.import_module(name)
    except Exception:
        return None


def _first_attr(module: Any, *names: str) -> Any | None:
    for name in names:
        obj = getattr(module, name, None)
        if obj is not None:
            return obj
    return None


def _bind_module(
    module: Any | None,
    mapping: Dict[str, tuple[str, ...]],
) -> None:
    """mapping: export_name -> (source_name, ...aliases)"""
    if module is None:
        return
    for export_name, sources in mapping.items():
        obj = _first_attr(module, *sources)
        if obj is not None:
            _REGISTRY[export_name] = obj


def _merge_constants() -> None:
    theme = _safe_import("ui.theme")
    if theme is not None:
        _merge_dict(AGENT_ICONS, getattr(theme, "AGENT_ICONS", None))
        _merge_dict(WORK_MODE_ICONS, getattr(theme, "WORK_MODE_ICONS", None))
        _merge_dict(MODEL_PROVIDER_ICONS, getattr(theme, "MODEL_PROVIDER_ICONS", None))
        _merge_dict(MODEL_PROVIDER_ICONS, getattr(theme, "MODEL_ICONS", None))
        _merge_dict(MODE_META, getattr(theme, "MODE_META", None))
        _REGISTRY["AGENT_ICONS"] = AGENT_ICONS
        _REGISTRY["WORK_MODE_ICONS"] = WORK_MODE_ICONS
        _REGISTRY["MODEL_PROVIDER_ICONS"] = MODEL_PROVIDER_ICONS
        _REGISTRY["MODEL_ICONS"] = MODEL_PROVIDER_ICONS
        _REGISTRY["MODE_META"] = MODE_META

    upload = _safe_import("ui.upload_zone")
    if upload is not None:
        types = getattr(upload, "RAG_UPLOAD_TYPES", None)
        if isinstance(types, list) and types:
            RAG_UPLOAD_TYPES[:] = types
            _REGISTRY["RAG_UPLOAD_TYPES"] = RAG_UPLOAD_TYPES


_merge_constants()

_layout = _safe_import("ui.layout")
_panels = _safe_import("ui.panels")
_upload = _safe_import("ui.upload_zone")
_animations = _safe_import("ui.animations")
_theme = _safe_import("ui.theme")

_bind_module(
    _layout,
    {
        "render_app_shell": ("render_app_shell",),
        "render_sidebar": ("render_sidebar",),
        "render_sidebar_toggle": ("render_sidebar_toggle",),
        "render_sidebar_open_button": ("render_sidebar_open_button",),
        "render_sidebar_collapse_button": ("render_sidebar_collapse_button",),
        "render_main_header": ("render_main_header", "render_hero", "render_chat_header"),
        "render_hero": ("render_hero", "render_main_header", "render_chat_header"),
        "render_chat_area": ("render_chat_area", "render_chat_messages"),
        "render_empty_state": ("render_empty_state",),
        "render_suggestion_cards": ("render_suggestion_cards", "render_suggestion_chips"),
        "render_input_bar": ("render_input_bar",),
        "render_upload_panel": ("render_upload_panel",),
        "render_attachment_card": ("render_attachment_card",),
        "render_citation_cards": ("render_citation_cards",),
        "render_composer_attach": ("render_composer_attach",),
    },
)

_bind_module(_panels, {"streamlit_panel": ("streamlit_panel",)})

_bind_module(
    _upload,
    {
        "render_drag_drop_uploader": ("render_drag_drop_uploader",),
        "is_new_upload": ("is_new_upload",),
        "upload_fingerprint": ("upload_fingerprint",),
    },
)

if _theme is not None:
    css_fn = _first_attr(_theme, "inject_custom_css", "inject_theme")
    if css_fn is not None and callable(css_fn):
        _REGISTRY["inject_custom_css"] = css_fn
        _REGISTRY["inject_theme"] = css_fn

if _animations is not None:
    gsap_fn = getattr(_animations, "inject_gsap_animations", None)
    if gsap_fn is not None and callable(gsap_fn):
        _REGISTRY["inject_gsap_animations"] = gsap_fn


def inject_custom_css() -> None:
    fn = _REGISTRY.get("inject_custom_css", _fallback_inject_custom_css)
    if callable(fn):
        fn()


def inject_gsap_animations() -> None:
    fn = _REGISTRY.get("inject_gsap_animations", _fallback_inject_gsap_animations)
    if callable(fn):
        fn()


inject_theme = inject_custom_css

# 将注册表写入模块 globals（保证 from ui.facade import X 一定成功）
for _name, _obj in _REGISTRY.items():
    globals()[_name] = _obj

# 函数名再次显式绑定，防止被覆盖为不可调用对象
render_sidebar = globals()["render_sidebar"]
render_sidebar_toggle = globals()["render_sidebar_toggle"]
render_sidebar_open_button = globals()["render_sidebar_open_button"]
render_sidebar_collapse_button = globals()["render_sidebar_collapse_button"]
render_main_header = globals()["render_main_header"]
render_chat_area = globals()["render_chat_area"]
render_citation_cards = globals()["render_citation_cards"]
render_input_bar = globals()["render_input_bar"]
render_upload_panel = globals()["render_upload_panel"]
render_drag_drop_uploader = globals()["render_drag_drop_uploader"]
streamlit_panel = globals()["streamlit_panel"]
is_new_upload = globals()["is_new_upload"]
upload_fingerprint = globals()["upload_fingerprint"]

__all__ = [
    "AGENT_ICONS",
    "WORK_MODE_ICONS",
    "MODEL_PROVIDER_ICONS",
    "MODEL_ICONS",
    "MODE_META",
    "RAG_UPLOAD_TYPES",
    "inject_custom_css",
    "inject_theme",
    "inject_gsap_animations",
    "is_new_upload",
    "upload_fingerprint",
    "render_app_shell",
    "render_sidebar",
    "render_sidebar_toggle",
    "render_sidebar_open_button",
    "render_sidebar_collapse_button",
    "render_main_header",
    "render_hero",
    "render_chat_area",
    "render_citation_cards",
    "render_input_bar",
    "render_upload_panel",
    "render_drag_drop_uploader",
    "render_empty_state",
    "render_suggestion_cards",
    "render_attachment_card",
    "render_composer_attach",
    "streamlit_panel",
]

# ---------------------------------------------------------------------------
# 启动时校验
# ---------------------------------------------------------------------------
for _check_name in __all__:
    if _check_name not in globals():
        print(f"[FACADE WARNING] missing: {_check_name}", file=sys.stderr)

for _check_name in _APP_REQUIRED:
    if _check_name not in globals():
        print(f"[FACADE WARNING] app required missing: {_check_name}", file=sys.stderr)
