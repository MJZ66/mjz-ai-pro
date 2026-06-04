"""会话与智能体状态管理（与 Streamlit 解耦的核心逻辑）。"""
from typing import Any, Dict, List, Optional

from utils.attachment_context import apply_attachment_to_system


def build_initial_messages(
    agent_type: str,
    system_prompts: Dict[str, str],
    *,
    with_welcome: bool = True,
    attachment: Optional[Dict[str, Any]] = None,
) -> List[dict]:
    system_content = apply_attachment_to_system(
        system_prompts[agent_type],
        attachment,
    )
    messages = [
        {"role": "system", "content": system_content},
    ]
    if with_welcome:
        messages.append(
            {
                "role": "assistant",
                "content": "你好，我是 MJZ 超级AI助手 🤖",
            }
        )
    return messages


def reset_system(
    messages: List[dict],
    agent_type: str,
    system_prompts: Dict[str, str],
    *,
    attachment: Optional[Dict[str, Any]] = None,
) -> List[dict]:
    """更新或插入 system 消息，不改动其余历史。"""
    system_content = apply_attachment_to_system(
        system_prompts[agent_type],
        attachment,
    )
    system_msg = {"role": "system", "content": system_content}
    updated = list(messages)

    if not updated:
        return [system_msg]

    if updated[0].get("role") == "system":
        updated[0] = system_msg
    else:
        updated.insert(0, system_msg)

    return updated


def should_reset_messages_on_agent_change(
    current_agent: str,
    selected_agent: str,
    keep_history: bool,
) -> bool:
    """切换智能体且未勾选保留历史时，应清空对话。"""
    if current_agent == selected_agent:
        return False
    return not keep_history
