"""file_utils 模块测试。"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.file_utils import (
    DEFAULT_MAX_FILE_CHARS,
    build_file_user_message,
    format_message_display,
    load_from_bytes,
    prepare_file_content,
    truncate_notice,
    truncate_text,
)


def test_truncate_text_no_truncation():
    text = "hello"
    result, truncated = truncate_text(text, max_chars=100)
    assert result == "hello"
    assert truncated is False


def test_truncate_text_with_truncation():
    text = "a" * 15000
    result, truncated = truncate_text(text, max_chars=12000)
    assert len(result) == 12000
    assert truncated is True


def test_prepare_file_content_empty():
    content, was_truncated, original_len = prepare_file_content("")
    assert content == ""
    assert was_truncated is False
    assert original_len == 0


def test_load_png_image():
    # 最小 PNG 头
    png_header = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    )
    loaded = load_from_bytes(png_header, "tiny.png")
    assert loaded.is_image
    assert loaded.image_base64


def test_build_file_user_message_text():
    loaded = load_from_bytes(b"content", "a.txt")
    msg = build_file_user_message(loaded, "请总结")
    assert msg["role"] == "user"
    assert isinstance(msg["content"], str)
    assert "content" in msg["content"]


def test_format_message_display_multimodal():
    msg = {
        "content": [
            {"type": "text", "text": "hello"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,xx"}},
        ]
    }
    display = format_message_display(msg["content"])
    assert "hello" in display
    assert "图片" in display


class FakeUpload:
    def __init__(self, file_type: str, data: bytes, name: str):
        self.type = file_type
        self._data = data
        self.name = name

    def read(self):
        return self._data


def test_read_uploaded_txt_compat():
    from utils.file_utils import read_uploaded_file

    upload = FakeUpload("text/plain", "你好".encode("utf-8"), "f.txt")
    assert "你好" in read_uploaded_file(upload)
