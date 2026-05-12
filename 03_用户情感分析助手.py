from openai import OpenAI
from dotenv import load_dotenv
from common import get_llm_response
import json
import streamlit as st
load_dotenv()

#初始化客户端
client = OpenAI(
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    api_key='sk-a5e92709867b4578b941d6b8b77e2cca'
)



st.write("## 用户情感分析助手")
st.divider()


result = ''

#小样本提示词
demo = [
   {'role': 'user', 'content': '换电池报价8万2！二手车商都不敢收，所谓终身质保条款藏着无数套路，新能源韭菜真不是白叫的。'},
   {'role': 'assistant', 'content': '负面'},
   {'role': 'user', 'content': '驾乘体验非常舒服，增程式没有续航焦虑，月均油电费才300块，国产新能源神车当之无愧。'},
   {'role': 'assistant', 'content': '正面'},
   {'role': 'user', 'content': '驾驶质感不错，但车机逻辑混乱需要适应，价格是否合理建议先试驾后再评判，仁者见仁智者见智。'},
   {'role': 'assistant', 'content': '中性'},
]

col1, col2 = st.columns([3, 1])

with col1:
    comment = st.text_area(label='请输入用户评价：', height=120)
    button = st.button('确定', type= 'primary')
    #当点击了按钮后，调用大模型的接口
    if button:
        result = get_llm_response(
            client,
            system_prompt='你是一个文本分类器。请根据我提供的示例，严格判断用户输入的情感倾向。请只输出一个词：正面、负面 或 中性。不要输出任何其他解释。',
            few_shot_prompt=json.dump(demo),
            user_prompt=comment.strip()
        )

with col2:
    if result:
        st.write("### 分析结果")
        st.write(result)