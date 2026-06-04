"""多轮对话 Agent。"""
from typing import Callable, Dict, List, Optional

from core.llm_client import LLMClient
from utils.session_utils import build_initial_messages, reset_system


class ChatAgent:
    def __init__(
        self,
        llm_client: LLMClient,
        system_prompt: str,
        agent_type: str = "通用聊天助手",
    ):
        self.llm = llm_client
        self.system_prompt = system_prompt
        self.agent_type = agent_type

    def initial_messages(self, with_welcome: bool = True) -> List[dict]:
        prompts = {self.agent_type: self.system_prompt}
        return build_initial_messages(
            self.agent_type,
            prompts,
            with_welcome=with_welcome,
        )

    def ensure_system(self, messages: List[dict]) -> List[dict]:
        prompts = {self.agent_type: self.system_prompt}
        return reset_system(messages, self.agent_type, prompts)

    def stream_reply(
        self,
        messages: List[dict],
        *,
        temperature: float = 0.7,
        model: Optional[str] = None,
        on_delta: Optional[Callable[[str], None]] = None,
    ) -> str:
        normalized = self.ensure_system(list(messages))
        return self.llm.stream_chat_collect(
            normalized,
            model=model,
            temperature=temperature,
            on_delta=on_delta,
        )
