"""将 Streamlit 会话消息导出为 Markdown。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from utils.file_utils import format_message_display

DEFAULT_TITLE = "MJZ AI Pro 对话导出"

ROLE_HEADINGS = {
    "system": "系统",
    "user": "用户",
    "assistant": "助手",
    "tool": "工具",
}


def _format_content(content: Any) -> str:
    return format_message_display(content)


def _is_empty_session(messages: List[dict]) -> bool:
    """无 user / tool 消息时视为空会话（仅 system 或欢迎语）。"""
    if not messages:
        return True
    return not any(m.get("role") in ("user", "tool") for m in messages)


def export_chat_to_markdown(
    messages: List[dict],
    title: Optional[str] = None,
    *,
    exported_at: Optional[datetime] = None,
) -> str:
    """导出会话为 Markdown 字符串。"""
    when = exported_at or datetime.now()
    title_text = (title or DEFAULT_TITLE).strip() or DEFAULT_TITLE
    time_str = when.strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        f"# {title_text}",
        "",
        f"- **导出时间**：{time_str}",
        f"- **消息条数**：{len(messages)}",
        "",
    ]

    if _is_empty_session(messages):
        lines.extend(
            [
                "> 当前暂无对话内容。发送消息后再次导出即可保存完整会话。",
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(["---", ""])

    for msg in messages:
        role = str(msg.get("role", "unknown"))
        heading = ROLE_HEADINGS.get(role, role)
        body = _format_content(msg.get("content", "")).strip()
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(body if body else "_(空)_")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_export_filename(*, exported_at: Optional[datetime] = None) -> str:
    when = exported_at or datetime.now()
    return f"mjz_ai_pro_chat_{when.strftime('%Y%m%d_%H%M%S')}.md"
