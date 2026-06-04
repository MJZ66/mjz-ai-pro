"""工具调度 Agent。"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from core.llm_client import LLMClient
from tools import calculator, text_summary


@dataclass
class ToolSpec:
    name: str
    description: str
    handler: Callable[..., str]


class BaseAgent:
    """简单工具注册与调度。"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client
        self._registry: Dict[str, ToolSpec] = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self) -> None:
        self.register(
            calculator.TOOL_NAME,
            calculator.TOOL_DESCRIPTION,
            lambda expression: calculator.calculate(expression),
        )
        self.register(
            text_summary.TOOL_NAME,
            text_summary.TOOL_DESCRIPTION,
            lambda text: text_summary.summarize(text, self.llm),
        )

    def register(self, name: str, description: str, handler: Callable[..., str]) -> None:
        self._registry[name] = ToolSpec(name=name, description=description, handler=handler)

    def list_tools(self) -> List[ToolSpec]:
        return list(self._registry.values())

    def run_tool(self, name: str, **kwargs: Any) -> str:
        if name not in self._registry:
            available = ", ".join(self._registry.keys())
            return f"未知工具：{name}。可用工具：{available}"
        try:
            return self._registry[name].handler(**kwargs)
        except TypeError:
            return f"工具 {name} 参数不正确，请参考工具说明。"
        except Exception as exc:
            return f"工具执行失败：{exc}"

    def dispatch_command(self, tool_name: str, user_input: str) -> str:
        """根据工具名分发执行。"""
        if tool_name == calculator.TOOL_NAME:
            return self.run_tool(calculator.TOOL_NAME, expression=user_input)
        if tool_name == text_summary.TOOL_NAME:
            return self.run_tool(text_summary.TOOL_NAME, text=user_input)
        return self.run_tool(tool_name)
