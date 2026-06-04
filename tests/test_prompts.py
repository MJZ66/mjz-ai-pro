import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agents.prompts import AGENT_NAME_ALIASES, SYSTEM_PROMPTS, normalize_agent_name


def test_agent_rename_aliases():
    assert normalize_agent_name("PDF总结助手") == "文件助手"
    assert normalize_agent_name("小红书文案助手") == "小红书爆款文案助手"


def test_required_agents_exist():
    for name in [
        "通用聊天助手",
        "法律助手",
        "代码助手",
        "简历分析助手",
        "文件助手",
        "小红书爆款文案助手",
    ]:
        assert name in SYSTEM_PROMPTS
        assert len(SYSTEM_PROMPTS[name]) > 100
