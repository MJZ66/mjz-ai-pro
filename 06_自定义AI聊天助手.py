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
Slider
========================= */

.stSlider {
    padding-top: 8px;
    padding-bottom: 8px;
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
Expander
========================= */

.streamlit-expanderHeader {

    background-color: #FFFFFF;

    border-radius: 10px;
}

/* =========================
Divider
========================= */

hr {

    border-color: #E5E7EB;
}

/* =========================
Sidebar 标题
========================= */

.sidebar-title {

    color: #111827;

    font-size: 15px;

    font-weight: 700;

    margin-top: 8px;

    margin-bottom: 8px;
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
# Sidebar
# =========================================

with st.sidebar:

    st.markdown("### ⚙️ 模型配置")

    api_vendor = st.radio(
        "选择模型提供商",
        ['ChatTongYi', 'DeepSeek']
    )

    # 模型配置
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
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1
    )

    st.divider()

    st.markdown("### 🤖 智能体类型")

    agent_type = st.selectbox(
        "请选择智能体",
        [
            '通用聊天助手',
            '法律助手',
            '小红书文案助手',
            '代码助手',
            '简历分析助手',
            'PDF总结助手'
        ]
    )

    st.divider()

    st.markdown("### 🔑 API配置")

    api_key = st.text_input(
        "请输入 API Key",
        type='password'
    )

    st.divider()

    st.markdown("### 📂 文件上传")

    uploaded_file = st.file_uploader(
        "上传 TXT / PDF 文件",
        type=['txt', 'pdf']
    )

    st.divider()

    if st.button("🗑️ 清空聊天记录"):

        st.session_state['messages'] = [

            {
                "role": "system",
                "content": "你是一个专业AI助手。"
            },

            {
                "role": "assistant",
                "content": "聊天记录已清空。"
            }
        ]

        st.rerun()

# =========================================
# System Prompt
# =========================================

SYSTEM_PROMPTS = {

    "通用聊天助手":
        "你是一个专业AI助手，请准确回答用户问题。",

    "法律助手":
        "你是一名专业法律顾问，请从法律角度分析问题，但不要提供违法建议。",

    "小红书文案助手":
        "你是一名顶级小红书运营专家，请生成爆款标题和种草文案。",

    "代码助手":
        "你是一名资深Python工程师，请帮助用户分析代码问题并提供解决方案。",

    "简历分析助手":
        "你是一名专业HR，请分析简历优缺点，并给出优化建议。",

    "PDF总结助手":
        "你是一名文档总结专家，请提炼重点内容并进行结构化总结。"
}

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
# 更新 System Prompt
# =========================================

if st.session_state['messages'][0]['content'] != SYSTEM_PROMPTS[agent_type]:

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
    <p>
        Multi-Agent AI Workspace
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# =========================================
# API KEY 检查
# =========================================

if not api_key:

    st.warning("⚠️ 请先输入 API Key")

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

    # TXT
    if file.type == "text/plain":

        file_text = str(file.read(), "utf-8")

    # PDF
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

    st.success(f"✅ 文件上传成功：{uploaded_file.name}")

    with st.expander("📖 查看文件内容"):

        st.write(file_content[:3000])

    col1, col2 = st.columns(2)

    with col1:

        if st.button("🧠 开始AI分析"):

            file_prompt = f"""
请根据以下文件内容进行分析：

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

            with st.spinner("AI 正在分析文件中..."):

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

    with col2:

        st.info("""
支持功能：

• PDF 内容总结  
• 简历分析  
• 法律文件分析  
• TXT 文本总结  
• AI 内容提炼
""")

# =========================================
# 展示历史消息
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