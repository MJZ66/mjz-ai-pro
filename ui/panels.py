"""避免「拆开的 HTML div + 中间插入组件」导致 Streamlit/React DOM 错误。"""
from __future__ import annotations

from contextlib import contextmanager

import streamlit as st


@contextmanager
def streamlit_panel(title: str, icon: str = ""):
    """
    用原生 expander 承载面板，不再用 open/close 的裸 </div> 包裹组件。
    """
    label = f"{icon} {title}".strip() if icon else title
    with st.expander(label, expanded=True):
        yield
