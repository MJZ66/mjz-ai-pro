"""session_utils 模块测试。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.session_utils import (  # noqa: E402
    build_initial_messages,
    reset_system,
    should_reset_messages_on_agent_change,
)

PROMPTS = {
    "通用聊天助手": "你是通用助手",
    "法律助手": "你是法律助手",
}


def test_should_reset_when_agent_changes_and_not_keep_history():
    assert should_reset_messages_on_agent_change("A", "B", keep_history=False) is True


def test_should_not_reset_when_keep_history():
    assert should_reset_messages_on_agent_change("A", "B", keep_history=True) is False


def test_reset_system_updates_first_message():
    messages = [
        {"role": "system", "content": "old"},
        {"role": "user", "content": "hi"},
    ]
    updated = reset_system(messages, "法律助手", PROMPTS)
    assert updated[0]["content"] == "你是法律助手"
    assert updated[1]["content"] == "hi"


def test_build_initial_messages_with_welcome():
    messages = build_initial_messages("通用聊天助手", PROMPTS)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
