"""export_chat 模块测试。"""
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.export_chat import (  # noqa: E402
    build_export_filename,
    export_chat_to_markdown,
)

FIXED_TIME = datetime(2026, 6, 6, 15, 30, 45)


def test_export_empty_session():
    md = export_chat_to_markdown([], exported_at=FIXED_TIME)
    assert "# MJZ AI Pro 对话导出" in md
    assert "2026-06-06 15:30:45" in md
    assert "暂无对话内容" in md


def test_export_only_welcome_is_empty():
    messages = [
        {"role": "system", "content": "你是助手"},
        {"role": "assistant", "content": "你好"},
    ]
    md = export_chat_to_markdown(messages, exported_at=FIXED_TIME)
    assert "暂无对话内容" in md
    assert "## 用户" not in md


def test_export_user_assistant_conversation():
    messages = [
        {"role": "system", "content": "系统提示"},
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，有什么可以帮你？"},
    ]
    md = export_chat_to_markdown(
        messages,
        title="测试会话",
        exported_at=FIXED_TIME,
    )
    assert "# 测试会话" in md
    assert "## 系统" in md
    assert "系统提示" in md
    assert "## 用户" in md
    assert "## 助手" in md
    assert "有什么可以帮你" in md


def test_export_tool_role():
    messages = [
        {"role": "user", "content": "计算 1+1"},
        {"role": "tool", "content": "2"},
        {"role": "assistant", "content": "结果是 2"},
    ]
    md = export_chat_to_markdown(messages, exported_at=FIXED_TIME)
    assert "## 工具" in md
    assert "## 助手" in md


def test_export_multimodal_user_message():
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请分析图片"},
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/png;base64,xx"},
                },
            ],
        },
    ]
    md = export_chat_to_markdown(messages, exported_at=FIXED_TIME)
    assert "请分析图片" in md
    assert "图片" in md


def test_build_export_filename():
    assert (
        build_export_filename(exported_at=FIXED_TIME)
        == "mjz_ai_pro_chat_20260606_153045.md"
    )
