import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader

# =========================================
# 页面配置
# =========================================

st.set_page_config(
    page_title="MJZ 超级AI助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================
# 企业级 B 端 UI 风格
# =========================================

st.markdown("""
<style>

/* =========================
整体页面
========================= */

.stApp {
    background-color: #F5F7FA;
}

/* =========================
Sidebar
========================= */

section[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #E5E7EB;
    padding-top: 20px;
}

section[data-testid="stSidebar"] > div {
    padding-left: 14px;
    padding-right: 14px;
}

/* =========================
标题区域
========================= */

.main-title {
    text-align: center;
    margin-top: 10px;
    margin-bottom: 24px;
}

.main-title h1 {
    color: #111827;
    font-size: 40px;
    font-weight: 700;
    margin-bottom: 6px;
}

.main-title p {
    color: #6B7280;
    font-size: 16px;
}

/* =========================
页面容器
========================= */

.block-container {
    padding-top: 2rem;
}

/* =========================
聊天消息
========================= */

.stChatMessage {
    background-color: #FFFFFF;
    border-radius: 16px;
    padding: 16px;
    border: 1px solid #E5E7EB;
    margin-bottom: 14px;

    box-shadow:
    0 1px 2px rgba(0,0,0,0.04);

    transition: all 0.2s ease;
}

.stChatMessage:hover {

    transform: translateY(-1px);

    box-shadow:
    0 6px 18px rgba(0,0,0,0.06);
}

/* =========================
文字系统
========================= */

html, body, [class*="css"] {
    font-family:
    Inter,
    "PingFang SC",
    "Microsoft YaHei",
    sans-serif;
}

[data-testid="stChatMessageContent"] {
    color: #111827;
    line-height: 1.8;
    font-size: 15px;
}

/* =========================
输入框
========================= */

.stTextInput input {
    border-radius: 12px;
    border: 1px solid #D1D5DB;
    background-color: #FFFFFF;
}

[data-testid="stChatInput"] {
    background-color: #FFFFFF;
}

/* =========================
按钮
========================= */

.stButton button {

    width: 100%;
    height: 44px;

    border-radius: 12px;

    border: 1px solid #D1D5DB;

    background-color: #FFFFFF;

    color: #111827;

    font-weight: 600;

    transition: all 0.2s ease;
}

.stButton button:hover {

    background-color: #F3F4F6;

    border-color: #9CA3AF;
}

/* =========================
Selectbox
========================= */

.stSelectbox div[data-baseweb="select"] > div {

    border-radius: 12px;

    border: 1px solid #D1D5DB;

    background-color: #FFFFFF;
}

/* =========================
Uploader
========================= */

[data-testid="stFileUploader"] {

    background-color: #FFFFFF;

    border: 1px dashed #CBD5E1;

    border-radius: 14px;

    padding: 14px;
}

/* =========================
Footer
========================= */

.footer {

    text-align: center;

    color: #9CA3AF;

    font-size: 13px;

    margin-top: 30px;

    padding-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================================
# 超级 Prompt 系统
# =========================================

SYSTEM_PROMPTS = {

    "通用聊天助手": """
你是一个专业AI助手。

要求：
1. 回答准确
2. 逻辑清晰
3. 使用结构化表达
4. 优先使用markdown格式
5. 回答简洁但信息完整
6. 不编造信息
7. 对技术问题给出详细步骤
8. 对复杂问题进行分点分析
""",

    "法律助手": """
你是一名专业法律顾问。

要求：
1. 从法律角度分析问题
2. 使用专业法律术语
3. 提供风险提示
4. 不提供违法建议
5. 回答结构化
6. 涉及法律责任时需特别说明
7. 不确定的问题明确说明
8. 优先分析：
   - 法律依据
   - 风险点
   - 解决方案
   - 注意事项
""",

    "代码助手": """
你是一名资深Python全栈工程师。

要求：
1. 优先输出高质量代码
2. 分析Bug根源
3. 解释代码逻辑
4. 给出优化建议
5. 代码符合工程规范
6. 使用最新最佳实践
7. 避免低质量写法
8. 输出结构：
   - 问题分析
   - 解决方案
   - 完整代码
   - 优化建议
9. 代码必须可运行
""",

    "简历分析助手": """
你是一名专业HR和技术面试官。

要求：
1. 分析简历优缺点
2. 判断岗位匹配度
3. 给出修改建议
4. 分析项目含金量
5. 给出面试建议
6. 分析技术竞争力
7. 输出结构：
   - 总体评价
   - 优势分析
   - 问题分析
   - 优化建议
   - 面试风险
""",

    "PDF总结助手": """
你是一名专业文档分析专家。

要求：
1. 提炼核心信息
2. 总结关键结论
3. 输出结构化内容
4. 提取重点数据
5. 识别关键风险
6. 长文档自动分层总结
7. 输出格式：
   - 文档概述
   - 核心内容
   - 重点结论
   - 风险与建议
""",

    "小红书文案助手": """
你是小红书爆款写作专家，请遵循以下步骤进行创作：

首先产出5个标题（包含适当emoji表情），
然后输出正文内容，
最后输出tag标签。

标题字数在20字以内，
正文控制在500字以内。

==================================================
一、标题创作技巧
==================================================

1. 采用二极管标题法

1.1 基本原理

本能喜欢：
- 最省力法则
- 及时享受

动物驱动力：
- 追求快乐
- 逃避痛苦

形成：
- 正刺激
- 负刺激

1.2 标题公式

正面刺激：
产品/方法 + 极短时间 + 逆天效果

例如：
- 学会这个方法，3天逆袭
- 这个神器让我效率翻倍

负面刺激：
你不XXX + 一定后悔 + 紧迫感

例如：
- 再不学AI真的晚了
- 不会这个技巧直接吃亏

==================================================
二、爆款标题技巧
==================================================

1. 使用强情绪表达
2. 制造反差感
3. 制造悬念
4. 使用数字
5. 加入口语化表达
6. 加入emoji
7. 使用生活化场景
8. 强化结果
9. 强调小白可操作
10. 制造代入感

==================================================
三、爆款关键词
==================================================

每次随机选1-3个自然融入：

好用到哭
YYDS
宝藏
绝绝子
神器
建议收藏
停止摆烂
挑战全网
手把手
揭秘
沉浸式
搞钱必看
吐血整理
家人们
高级感
被夸爆
正确姿势
小白必看
压箱底
永远可以相信
有手就能做

==================================================
四、小红书标题规则
==================================================

1. 标题必须口语化
2. 标题必须短
3. 每次输出5个标题
4. 每个标题带emoji
5. 不解释标题
6. 直接输出标题

==================================================
五、正文写作技巧
==================================================

写作风格随机：

- 幽默
- 轻松
- 热情
- 真诚
- 沉浸式
- 鼓励型
- 情绪感染型

开篇方式随机：

- 提出疑问
- 使用对比
- 制造冲突
- 场景描述
- 数据开场
- 直接共鸣

==================================================
六、正文要求
==================================================

1. 强口语化
2. 多使用emoji
3. 分段清晰
4. 有互动感
5. 有情绪感染力
6. 避免AI味
7. 更像真实博主
8. 结尾加入互动引导

==================================================
七、Tag规则
==================================================

结尾生成5-8个tag：

例如：
#AI
#副业
#小红书运营

==================================================
八、输出格式
==================================================

输出markdown格式：

## 爆款标题

1. xxx
2. xxx

## 正文

xxx

## Tags

#xxx #xxx
"""
}

# =========================================
# Sidebar
# =========================================

with st.sidebar:

    st.markdown("### ⚙️ 模型配置")

    api_vendor = st.radio(
        "选择模型提供商",
        ['ChatTongYi', 'DeepSeek']
    )

    if api_vendor == 'ChatTongYi':

        base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'

        model_options = [
            'qwen-plus',
            'qwen-max',
            'qwen-turbo'
        ]

    else:

        base_url = 'https://api.deepseek.com'

        model_options = [
            'deepseek-chat',
            'deepseek-reasoner'
        ]

    model_name = st.selectbox(
        "选择模型",
        model_options
    )

    temperature = st.slider(
        "Temperature",
        0.0,
        2.0,
        0.7,
        0.1
    )

    st.divider()

    agent_type = st.selectbox(
        "🤖 选择智能体",
        [
            '通用聊天助手',
            '法律助手',
            '代码助手',
            '简历分析助手',
            'PDF总结助手',
            '小红书文案助手'
        ]
    )

    st.divider()

    api_key = st.text_input(
        "🔑 API Key",
        type="password"
    )

    st.divider()

    uploaded_file = st.file_uploader(
        "📂 上传 TXT/PDF 文件",
        type=['txt', 'pdf']
    )

    st.divider()

    if st.button("🗑️ 清空聊天记录"):

        st.session_state['messages'] = [

            {
                "role": "system",
                "content": SYSTEM_PROMPTS[agent_type]
            }
        ]

        st.rerun()

# =========================================
# 初始化消息
# =========================================

if 'messages' not in st.session_state:

    st.session_state['messages'] = [

        {
            "role": "system",
            "content": SYSTEM_PROMPTS[agent_type]
        },

        {
            "role": "assistant",
            "content": "你好，我是 MJZ 超级AI助手 🤖"
        }
    ]

# =========================================
# 更新 Prompt
# =========================================

st.session_state['messages'][0] = {
    "role": "system",
    "content": SYSTEM_PROMPTS[agent_type]
}

# =========================================
# 页面标题
# =========================================

st.markdown("""
<div class="main-title">
    <h1>🤖 MJZ 超级AI助手</h1>
    <p>Multi-Agent AI Workspace</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# =========================================
# API Key 检查
# =========================================

if not api_key:

    st.warning("请输入 API Key")

    st.stop()

# =========================================
# OpenAI Client
# =========================================

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

# =========================================
# 文件读取
# =========================================

def read_file(file):

    file_text = ""

    if file.type == "text/plain":

        file_text = str(file.read(), "utf-8")

    elif file.type == "application/pdf":

        pdf_reader = PdfReader(file)

        for page in pdf_reader.pages:

            text = page.extract_text()

            if text:
                file_text += text

    return file_text

# =========================================
# 文件分析
# =========================================

if uploaded_file:

    file_content = read_file(uploaded_file)

    st.success(f"文件上传成功：{uploaded_file.name}")

    with st.expander("查看文件内容"):

        st.write(file_content[:3000])

    if st.button("🧠 开始AI分析"):

        file_prompt = f"""
请分析以下文件：

文件名：
{uploaded_file.name}

文件内容：
{file_content}
"""

        st.session_state['messages'].append(
            {
                "role": "user",
                "content": file_prompt
            }
        )

        with st.spinner("AI分析中..."):

            stream = client.chat.completions.create(
                model=model_name,
                messages=st.session_state['messages'],
                temperature=temperature,
                stream=True
            )

            with st.chat_message("assistant"):

                result = st.write_stream(
                    chunk.choices[0].delta.content or ''
                    for chunk in stream
                )

            st.session_state['messages'].append(
                {
                    "role": "assistant",
                    "content": result
                }
            )

# =========================================
# 历史消息
# =========================================

for msg in st.session_state['messages']:

    if msg['role'] != 'system':

        with st.chat_message(msg['role']):

            st.write(msg['content'])

# =========================================
# 用户输入
# =========================================

user_input = st.chat_input("请输入你的问题...")

# =========================================
# 聊天逻辑
# =========================================

if user_input:

    with st.chat_message("user"):

        st.write(user_input)

    st.session_state['messages'].append(
        {
            "role": "user",
            "content": user_input
        }
    )

    stream = client.chat.completions.create(
        model=model_name,
        messages=st.session_state['messages'],
        temperature=temperature,
        stream=True
    )

    with st.chat_message("assistant"):

        with st.spinner("AI 思考中..."):

            result = st.write_stream(
                chunk.choices[0].delta.content or ''
                for chunk in stream
            )

    st.session_state['messages'].append(
        {
            "role": "assistant",
            "content": result
        }
    )

# =========================================
# Footer
# =========================================

st.markdown("""
<div class="footer">
MJZ Super AI Assistant · Streamlit + OpenAI SDK
</div>
""", unsafe_allow_html=True)