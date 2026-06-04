"""attachment_context 模块测试。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.attachment_context import (  # noqa: E402
    apply_attachment_to_system,
    attachment_status_line,
    build_user_message_from_attachment,
    format_attachment_block,
    strip_attachment_from_system,
)
from utils.attachment_context import loaded_file_to_attachment  # noqa: E402
from utils.file_utils import LoadedFile  # noqa: E402


def test_apply_attachment_appends_block():
    base = "你是助手"
    att = {
        "filename": "resume.pdf",
        "extension": ".pdf",
        "kind": "text",
        "text": "赵洋 数字媒体技术",
        "truncated": False,
        "char_count": 10,
    }
    merged = apply_attachment_to_system(base, att)
    assert "赵洋 数字媒体技术" in merged
    assert "勿声称" in merged
    assert strip_attachment_from_system(merged) == base


def test_apply_attachment_none_returns_base():
    base = "你是助手"
    assert apply_attachment_to_system(base, None) == base


def test_apply_attachment_none_preserves_existing_block():
    base = "你是助手"
    merged = apply_attachment_to_system(
        base,
        {
            "filename": "a.pdf",
            "extension": ".pdf",
            "kind": "text",
            "text": "数字媒体技术",
            "truncated": False,
            "char_count": 6,
        },
    )
    again = apply_attachment_to_system(merged, None)
    assert again == merged
    assert "数字媒体技术" in again


def test_build_user_message_from_attachment():
    att = {
        "filename": "a.txt",
        "extension": ".txt",
        "kind": "text",
        "text": "hello",
        "truncated": False,
    }
    msg = build_user_message_from_attachment(att, "总结一下")
    assert msg["role"] == "user"
    assert "总结一下" in msg["content"]
    assert "hello" in msg["content"]


def test_loaded_file_to_attachment_roundtrip():
    loaded = LoadedFile(
        filename="doc.txt",
        extension=".txt",
        kind="text",
        text="正文内容",
    )
    att = loaded_file_to_attachment(loaded)
    assert att["filename"] == "doc.txt"
    assert att["text"] == "正文内容"


def test_attachment_status_line():
    line = attachment_status_line(
        {"filename": "x.pdf", "kind": "text", "char_count": 100}
    )
    assert "x.pdf" in line
    assert "可直接" in line


def test_format_attachment_block_mentions_requirement():
    block = format_attachment_block(
        {"filename": "f.pdf", "extension": ".pdf", "kind": "text", "text": "x"}
    )
    assert "f.pdf" in block
