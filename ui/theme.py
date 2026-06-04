"""MJZ AI Pro — Streamlit 视觉主题（编辑风 AI 工作站）。"""

MODE_META = {
    "多轮对话": {
        "icon": "◈",
        "tagline": "连续上下文 · 多角色智能体",
        "hint": "在下方输入框提问，支持多轮记忆。",
    },
    "RAG 知识库": {
        "icon": "◎",
        "tagline": "上传文档 · 检索增强 · 引用溯源",
        "hint": "先构建知识库，再基于文档提问。",
    },
    "Agent 工具": {
        "icon": "⚙",
        "tagline": "计算器 · 文本摘要 · 可扩展",
        "hint": "选择工具并输入参数后执行。",
    },
}

AGENT_ICONS = {
    "通用聊天助手": "💬",
    "法律助手": "⚖",
    "代码助手": "⌘",
    "简历分析助手": "📋",
    "文件助手": "📁",
    "小红书爆款文案助手": "✦",
}


def inject_theme() -> None:
    import streamlit as st

    st.markdown(
        """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;600;700&family=Sora:wght@400;500;600&display=swap" rel="stylesheet">

<style>
:root {
  --bg-paper: #F6F2EB;
  --bg-paper-2: #EFE8DC;
  --ink: #141917;
  --ink-muted: #5C6562;
  --sidebar-bg: #0F1F1C;
  --sidebar-ink: #E8EDE9;
  --sidebar-muted: #8FA39C;
  --accent: #C45C3E;
  --accent-soft: rgba(196, 92, 62, 0.12);
  --copper: #D4A574;
  --teal-glow: #2A6B5E;
  --card-bg: rgba(255, 255, 255, 0.72);
  --card-border: rgba(20, 25, 23, 0.08);
  --radius-lg: 18px;
  --radius-md: 12px;
  --shadow-soft: 0 12px 40px rgba(15, 31, 28, 0.08);
  --font-display: "Fraunces", "Noto Serif SC", serif;
  --font-body: "Sora", "PingFang SC", "Microsoft YaHei", sans-serif;
}

/* ---- 全局 ---- */
.stApp {
  background-color: var(--bg-paper);
  background-image:
    radial-gradient(ellipse 80% 50% at 100% 0%, rgba(42, 107, 94, 0.07), transparent 50%),
    radial-gradient(ellipse 60% 40% at 0% 100%, rgba(196, 92, 62, 0.06), transparent 45%),
    url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
  font-family: var(--font-body);
  color: var(--ink);
}

.block-container {
  padding-top: 1.5rem;
  max-width: 920px;
}

html, body, [class*="css"] {
  font-family: var(--font-body);
}

footer, header[data-testid="stHeader"] {
  opacity: 0.35;
}

/* ---- 侧边栏 ---- */
section[data-testid="stSidebar"] {
  background: linear-gradient(175deg, #0F1F1C 0%, #152A26 55%, #0D1816 100%);
  border-right: 1px solid rgba(212, 165, 116, 0.15);
}

section[data-testid="stSidebar"] > div {
  padding: 1.25rem 1rem 2rem;
}

section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
  color: var(--sidebar-ink);
}

section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] small {
  color: var(--sidebar-muted) !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
  font-family: var(--font-display);
  color: var(--sidebar-ink) !important;
  letter-spacing: -0.02em;
}

section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] .stRadio label {
  font-size: 0.8rem;
  font-weight: 500;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--sidebar-muted) !important;
}

section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea {
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(212, 165, 116, 0.25) !important;
  color: var(--sidebar-ink) !important;
  border-radius: 10px !important;
}

section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
  background: rgba(255,255,255,0.06) !important;
  border-color: rgba(212, 165, 116, 0.25) !important;
  border-radius: 10px !important;
}

section[data-testid="stSidebar"] .stButton > button {
  background: linear-gradient(135deg, var(--accent) 0%, #A84830 100%) !important;
  color: #FFF8F4 !important;
  border: none !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

section[data-testid="stSidebar"] .stButton > button:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(196, 92, 62, 0.35);
}

/* ---- 主区标题 ---- */
.mjz-hero {
  text-align: center;
  padding: 2rem 1rem 1.5rem;
  animation: mjzFadeUp 0.7s ease both;
}

.mjz-hero h1 {
  font-family: var(--font-display);
  font-size: clamp(2rem, 4vw, 2.75rem);
  font-weight: 600;
  color: var(--ink);
  margin: 0 0 0.35rem;
  letter-spacing: -0.03em;
}

.mjz-hero .mjz-badge {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
  background: var(--accent-soft);
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  margin-bottom: 0.75rem;
}

.mjz-hero p {
  color: var(--ink-muted);
  font-size: 1.05rem;
  margin: 0;
}

/* ---- 模式条 ---- */
.mjz-mode-strip {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  margin: 0 0 1.5rem;
  background: var(--card-bg);
  backdrop-filter: blur(12px);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft);
  animation: mjzFadeUp 0.7s ease 0.1s both;
}

.mjz-mode-strip .mjz-mode-icon {
  font-size: 1.75rem;
  line-height: 1;
  color: var(--teal-glow);
}

.mjz-mode-strip h2 {
  font-family: var(--font-display);
  font-size: 1.25rem;
  margin: 0;
  color: var(--ink);
}

.mjz-mode-strip .mjz-mode-sub {
  font-size: 0.88rem;
  color: var(--ink-muted);
  margin: 0.15rem 0 0;
}

/* ---- 卡片面板 ---- */
.mjz-panel {
  background: var(--card-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  padding: 1.35rem 1.5rem;
  margin-bottom: 1.25rem;
  box-shadow: var(--shadow-soft);
  animation: mjzFadeUp 0.6s ease 0.15s both;
}

.mjz-panel-title {
  font-family: var(--font-display);
  font-size: 1.15rem;
  color: var(--ink);
  margin: 0 0 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.mjz-panel-title span {
  color: var(--accent);
}

.mjz-hint {
  font-size: 0.9rem;
  color: var(--ink-muted);
  margin: 0 0 1rem;
  line-height: 1.55;
}

/* ---- 工具卡片 ---- */
.mjz-tool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.85rem;
  margin: 1rem 0;
}

.mjz-tool-card {
  padding: 1rem 1.1rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--card-border);
  background: rgba(255,255,255,0.5);
  transition: border-color 0.2s, transform 0.2s;
}

.mjz-tool-card:hover {
  border-color: rgba(196, 92, 62, 0.35);
  transform: translateY(-2px);
}

.mjz-tool-card strong {
  font-family: var(--font-display);
  color: var(--teal-glow);
  display: block;
  margin-bottom: 0.35rem;
}

.mjz-tool-card p {
  font-size: 0.85rem;
  color: var(--ink-muted);
  margin: 0;
  line-height: 1.45;
}

/* ---- 指标 ---- */
div[data-testid="stMetric"] {
  background: rgba(255,255,255,0.55);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-md);
  padding: 0.85rem 1rem;
}

div[data-testid="stMetric"] label {
  color: var(--ink-muted) !important;
  font-size: 0.75rem !important;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

div[data-testid="stMetric"] [data-testid="stMetricValue"] {
  font-family: var(--font-display);
  color: var(--teal-glow) !important;
}

/* ---- 拖拽上传区 ---- */
.mjz-dropzone-wrap {
  margin: 0.5rem 0 0.25rem;
}

.mjz-dropzone-visual {
  text-align: center;
  padding: 0.5rem 0 0.75rem;
  pointer-events: none;
}

.mjz-dropzone-icon {
  font-size: 1.75rem;
  color: var(--teal-glow);
  opacity: 0.85;
  line-height: 1;
}

.mjz-dropzone-title {
  font-family: var(--font-display);
  font-size: 1.05rem;
  color: var(--ink);
  margin-top: 0.35rem;
  font-weight: 600;
}

.mjz-dropzone-sub {
  font-size: 0.82rem;
  color: var(--ink-muted);
  margin-top: 0.25rem;
}

[data-testid="stFileUploader"],
[data-testid="stFileUploaderDropzone"] {
  min-height: 120px !important;
  background: rgba(255, 255, 255, 0.75) !important;
  border: 2px dashed rgba(42, 107, 94, 0.42) !important;
  border-radius: 16px !important;
  padding: 1.25rem 1rem !important;
  transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
}

[data-testid="stFileUploader"]:hover,
[data-testid="stFileUploaderDropzone"]:hover,
[data-testid="stFileUploader"]:focus-within,
[data-testid="stFileUploaderDropzone"]:focus-within {
  border-color: var(--accent) !important;
  background: rgba(196, 92, 62, 0.05) !important;
  box-shadow: 0 8px 28px rgba(196, 92, 62, 0.12);
}

[data-testid="stFileUploader"] section,
[data-testid="stFileUploaderDropzone"] {
  min-height: 88px;
  display: flex;
  align-items: center;
  justify-content: center;
}

[data-testid="stFileUploader"] small {
  color: var(--ink-muted) !important;
  font-size: 0.85rem !important;
}

/* ---- 聊天气泡 ---- */
.stChatMessage {
  background: rgba(255, 255, 255, 0.85) !important;
  border: 1px solid var(--card-border) !important;
  border-radius: var(--radius-md) !important;
  padding: 1rem 1.15rem !important;
  margin-bottom: 0.75rem !important;
  box-shadow: 0 4px 16px rgba(15, 31, 28, 0.04) !important;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
  border-left: 3px solid var(--accent) !important;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
  border-left: 3px solid var(--teal-glow) !important;
}

[data-testid="stChatMessageContent"] {
  font-size: 0.95rem !important;
  line-height: 1.75 !important;
  color: var(--ink) !important;
}

[data-testid="stChatInput"] {
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--card-border) !important;
  background: #fff !important;
}

[data-testid="stChatInput"] textarea {
  font-family: var(--font-body) !important;
}

/* ---- 主区按钮 ---- */
.main .stButton > button[kind="primary"],
.main .stButton > button[data-testid="baseButton-primary"] {
  background: linear-gradient(135deg, var(--teal-glow), #1E5248) !important;
  color: #F0F7F4 !important;
  border: none !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  padding: 0.55rem 1.25rem !important;
}

.main .stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]) {
  border-radius: 10px !important;
  border: 1px solid var(--card-border) !important;
  background: rgba(255,255,255,0.7) !important;
  color: var(--ink) !important;
}

/* ---- 空状态 ---- */
.mjz-empty-chat {
  text-align: center;
  padding: 3rem 1.5rem;
  color: var(--ink-muted);
  border: 1px dashed rgba(20, 25, 23, 0.12);
  border-radius: var(--radius-lg);
  background: rgba(255,255,255,0.35);
  margin: 1rem 0 1.5rem;
  animation: mjzFadeUp 0.5s ease 0.2s both;
}

.mjz-empty-chat .mjz-empty-icon {
  font-size: 2.5rem;
  opacity: 0.5;
  margin-bottom: 0.75rem;
}

/* ---- 页脚 ---- */
.mjz-footer {
  text-align: center;
  color: var(--ink-muted);
  font-size: 0.8rem;
  padding: 2rem 0 1rem;
  letter-spacing: 0.04em;
}

.mjz-footer strong {
  color: var(--copper);
  font-weight: 600;
}

/* ---- 侧边栏品牌 ---- */
.mjz-sidebar-brand {
  padding: 0.5rem 0 1.25rem;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid rgba(212, 165, 116, 0.2);
}

.mjz-sidebar-brand h2 {
  font-family: var(--font-display) !important;
  font-size: 1.45rem !important;
  margin: 0 !important;
  color: var(--sidebar-ink) !important;
  background: linear-gradient(120deg, #F0EDE8 0%, var(--copper) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.mjz-sidebar-brand p {
  font-size: 0.78rem !important;
  color: var(--sidebar-muted) !important;
  margin: 0.35rem 0 0 !important;
  letter-spacing: 0.06em;
}

.mjz-sidebar-section {
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--copper) !important;
  margin: 1.25rem 0 0.5rem !important;
  opacity: 0.9;
}

/* ---- 通知 ---- */
div[data-testid="stAlert"] {
  border-radius: var(--radius-md) !important;
  border: none !important;
}

@keyframes mjzFadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    import streamlit as st

    st.markdown(
        """
<div class="mjz-hero">
  <div class="mjz-badge">MJZ AI Pro</div>
  <h1>智能工作台</h1>
  <p>多轮对话 · 知识库检索 · Agent 工具 — 一处完成</p>
</div>
""",
        unsafe_allow_html=True,
    )


def render_mode_strip(mode: str) -> None:
    import streamlit as st

    meta = MODE_META.get(mode, {"icon": "◆", "tagline": "", "hint": ""})
    st.markdown(
        f"""
<div class="mjz-mode-strip">
  <div class="mjz-mode-icon">{meta["icon"]}</div>
  <div>
    <h2>{mode}</h2>
    <p class="mjz-mode-sub">{meta["tagline"]}</p>
  </div>
</div>
<p class="mjz-hint" style="margin-top:-0.5rem">{meta["hint"]}</p>
""",
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    import streamlit as st

    st.markdown(
        """
<div class="mjz-sidebar-brand">
  <h2>MJZ AI Pro</h2>
  <p>Agent · RAG · Streamlit</p>
</div>
""",
        unsafe_allow_html=True,
    )


def sidebar_section(title: str) -> None:
    import streamlit as st

    st.markdown(f'<p class="mjz-sidebar-section">{title}</p>', unsafe_allow_html=True)


def panel_open(title: str, icon: str = "") -> None:
    import streamlit as st

    st.markdown(
        f'<div class="mjz-panel"><div class="mjz-panel-title">'
        f'<span>{icon}</span> {title}</div>',
        unsafe_allow_html=True,
    )


def panel_close() -> None:
    import streamlit as st

    st.markdown("</div>", unsafe_allow_html=True)
