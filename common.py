from openai import OpenAI


def get_llm_response(
    client,
    *,
    system_prompt="",
    few_shot_prompt=None,
    user_prompt="",
    model="qwen-plus",
    stream=False
):
    """
    通用 LLM 请求函数

    参数：
    client              OpenAI 客户端
    system_prompt       系统提示词
    few_shot_prompt     小样本提示词(list)
    user_prompt         用户输入
    model               模型名称
    stream              是否流式输出
    """

    # 初始化消息列表
    messages = []

    # system prompt
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })

    # few-shot
    if few_shot_prompt:
        if isinstance(few_shot_prompt, list):
            messages.extend(few_shot_prompt)

    # user prompt
    if user_prompt:
        messages.append({
            "role": "user",
            "content": user_prompt
        })

    # 请求模型
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=stream
    )

    # 非流式
    if not stream:
        return response.choices[0].message.content

    # 流式
    return response