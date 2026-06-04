"""兼容层：统一经 LLMClient 调用。"""
from typing import List, Optional

from core.config import load_settings
from core.llm_client import LLMClient


def get_llm_response(
    client,
    *,
    system_prompt="",
    few_shot_prompt=None,
    user_prompt="",
    messages=None,
    model="qwen-plus",
    temperature=None,
    stream=False,
):
    """保留旧接口，内部使用 OpenAI client（来自 LLMClient 或裸客户端）。"""
    if messages is not None:
        msg_list = list(messages)
    else:
        msg_list = []
        if system_prompt:
            msg_list.append({"role": "system", "content": system_prompt})
        if few_shot_prompt and isinstance(few_shot_prompt, list):
            msg_list.extend(few_shot_prompt)
        if user_prompt:
            msg_list.append({"role": "user", "content": user_prompt})

    kwargs = {"model": model, "messages": msg_list, "stream": stream}
    if temperature is not None:
        kwargs["temperature"] = temperature

    response = client.chat.completions.create(**kwargs)
    if not stream:
        return response.choices[0].message.content
    return response


def build_llm_client(
    *,
    api_key_override: str = "",
    base_url_override: str = "",
    model_override: str = "",
    vendor: str = "ChatTongYi",
) -> LLMClient:
    settings = load_settings(
        api_key_override=api_key_override,
        base_url_override=base_url_override,
        model_override=model_override,
        vendor=vendor,
    )
    return LLMClient(settings)
