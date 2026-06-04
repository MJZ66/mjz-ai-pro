"""拖拽上传区域组件（基于 Streamlit file_uploader）。"""
from __future__ import annotations

from typing import Any, List, Optional, Union

import streamlit as st

DROP_ZONE_LABEL = "拖拽文件到此处，或点击选择文件"

RAG_UPLOAD_TYPES = ["txt", "md", "pdf", "docx", "xlsx", "xls"]


def upload_fingerprint(uploaded_file: Any) -> str:
    """用于检测用户是否新拖入了文件。"""
    if uploaded_file is None:
        return ""
    size = getattr(uploaded_file, "size", None)
    file_id = getattr(uploaded_file, "file_id", None) or uploaded_file.name
    return f"{uploaded_file.name}:{size}:{file_id}"


def _normalize_uploads(
    uploaded: Union[Any, List[Any], None],
    *,
    multiple: bool,
) -> List[Any]:
    if uploaded is None:
        return []
    if multiple:
        return list(uploaded) if isinstance(uploaded, list) else [uploaded]
    return [uploaded]


def render_drag_drop_uploader(
    key: str,
    file_types: List[str],
    *,
    multiple: bool = False,
    help_text: str = "",
    formats_hint: str = "",
) -> Union[Any, List[Any], None]:
    """
    渲染带拖拽提示的文件上传区。
    Streamlit 原生支持拖放；此处通过样式与文案强化体验。
    """
    hint = formats_hint or " · ".join(f.upper() for f in file_types[:8])
    if len(file_types) > 8:
        hint += " …"

    st.caption(f"⬆ 拖拽文件到下方区域，或点击选择 · {hint}")

    uploaded = st.file_uploader(
        DROP_ZONE_LABEL,
        type=file_types,
        key=key,
        accept_multiple_files=multiple,
        help=help_text or "将文件拖入上方虚线区域，松开即可上传",
        label_visibility="collapsed",
    )

    files = _normalize_uploads(uploaded, multiple=multiple)
    if not files:
        return None if not multiple else []

    if multiple:
        st.caption(f"已选择 {len(files)} 个文件：" + "、".join(f.name for f in files))
        return files

    st.caption(f"已选择：{files[0].name}")
    return files[0]


def is_new_upload(key: str, fingerprint: str) -> bool:
    """判断是否为本次会话中新拖入/选择的文件。"""
    if not fingerprint:
        return False
    state_key = f"_upload_fp_{key}"
    if st.session_state.get(state_key) == fingerprint:
        return False
    st.session_state[state_key] = fingerprint
    return True
