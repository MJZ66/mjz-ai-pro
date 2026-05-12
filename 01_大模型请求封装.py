
"""函数名称：get_llm_response
params模型参数：
client OpenAI标准(SDK)，用于发送模型请求
+*表示后面的函数参数都必须使用关键字参数
+system_prompt系统提示词
+few_shot_prompt 小样本提示词
+ user_prompt用户提示词
+ model 模型名称
+ stream是否开启流模型
"""
import json


def get_llm_response(client, *, system_prompt='',few_shot_prompt='',
                     user_prompt='',model='qwen3-max',stream=False):
    # 定义聊天列表
    messages = []
    # 判断是否传递那些提示词，如果传递了那么就加入到聊天列表中去
    if system_prompt:
        messages.append({'role': 'system','content': system_prompt})
    if few_shot_prompt:
            messages += json.load(few_shot_prompt)
    if user_prompt:
            messages.append({'role': 'user','content': user_prompt})
            # 发送请求（补齐信息）
    resp = client.chat.completions.create(
        model = model,
        messages = messages,
        stream = stream
    )
    # 给外界返回结果
    if not stream:
        return resp.choices[0].message.content

    return resp

