from httpx import stream
from openai import OpenAI

client = OpenAI(
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    api_key='sk-a5e92709867b4578b941d6b8b77e2cca'
)

resp = client.chat.completions.create(
    model='qwen3-max',
    messages=[
        {'role':'system','content':'你是一个专业的评论家，说话均来自于客观证据和可查询的资料'},
        {'role':'user','content':'评价一下成都理工大学'}
    ]
)

for chunk in stream:
    if isinstance(chunk, tuple):
        chunk = chunk[0]
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end='')
