"""文档加载：委托 utils.file_utils，RAG 仅索引文本类文件。"""
from pathlib import Path
from typing import Any, Optional, Union

from utils.file_utils import FileLoadError
from utils.file_utils import load_from_bytes as _load_file

RAG_TEXT_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".xlsx", ".xls"}

DocumentLoadError = FileLoadError


def load_from_bytes(
    data: bytes,
    filename: str,
    *,
    mime_type: Optional[str] = None,
) -> str:
    loaded = _load_file(data, filename, mime_type=mime_type)
    if loaded.is_image:
        raise DocumentLoadError(
            "RAG 知识库暂不支持图片，请在「多轮对话」模式中上传图片。"
        )
    if loaded.extension not in RAG_TEXT_EXTENSIONS:
        raise DocumentLoadError(f"RAG 不支持该类型：{loaded.extension}")
    return loaded.text


def load_from_upload(uploaded_file: Any) -> tuple[str, str]:
    if uploaded_file is None:
        return "", ""
    name = getattr(uploaded_file, "name", "unknown")
    raw = uploaded_file.read()
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    text = load_from_bytes(
        raw,
        name,
        mime_type=getattr(uploaded_file, "type", None),
    )
    return text, name


def load_from_path(path: Union[str, Path]) -> str:
    path = Path(path)
    if not path.exists():
        raise DocumentLoadError(f"文件不存在：{path}")
    return load_from_bytes(path.read_bytes(), path.name)
