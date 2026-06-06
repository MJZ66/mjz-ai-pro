"""UI 层默认常量（facade 兜底，不依赖 theme/layout 是否加载成功）。"""

AGENT_ICONS: dict[str, str] = {
    "通用聊天助手": "💬",
    "法律助手": "⚖",
    "代码助手": "💻",
    "简历分析助手": "📋",
    "文件助手": "📁",
    "小红书爆款文案助手": "✦",
    "知识库助手": "📚",
    "数据分析助手": "📊",
}

WORK_MODE_ICONS: dict[str, str] = {
    "多轮对话": "💬",
    "RAG 知识库": "📚",
    "Agent 工具": "⚡",
}

MODEL_ICONS: dict[str, str] = {
    "通义千问": "🌐",
    "DeepSeek": "🔷",
}

MODE_META: dict[str, dict[str, str]] = {
    "多轮对话": {
        "title": "MJZ AI Pro",
        "subtitle": "多轮对话 · 附件解析 · 智能体切换",
        "tag": "对话",
    },
    "RAG 知识库": {
        "title": "知识库问答",
        "subtitle": "上传文档，基于检索增强生成回答",
        "tag": "RAG",
    },
    "Agent 工具": {
        "title": "Agent 工具箱",
        "subtitle": "计算器、文本摘要与可扩展工具",
        "tag": "Tools",
    },
}

RAG_UPLOAD_TYPES: list[str] = ["txt", "md", "pdf", "docx", "xlsx", "xls"]

CHAT_UPLOAD_TYPES: list[str] = ["txt", "pdf", "docx", "xlsx", "png", "jpg", "jpeg"]
