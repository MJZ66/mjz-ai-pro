"""GSAP 动效注入（Streamlit iframe → parent DOM）。"""
from __future__ import annotations

from pathlib import Path

import streamlit.components.v1 as components

_JS_CACHE: str | None = None


def _load_runtime_js() -> str:
    global _JS_CACHE
    if _JS_CACHE is None:
        js_path = Path(__file__).with_name("gsap_runtime.js")
        _JS_CACHE = js_path.read_text(encoding="utf-8")
    return _JS_CACHE


def inject_gsap_animations() -> None:
    """
    通过零高度 html 组件注入 GSAP 运行时。
    脚本在 iframe 内加载，通过 window.parent 操作 Streamlit 主文档。
    """
    runtime = _load_runtime_js()
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head><body>
<script>{runtime}</script>
</body></html>"""
    components.html(html, height=0, width=0, scrolling=False)
