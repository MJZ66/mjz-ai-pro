# MJZ AI Pro

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**MJZ AI Pro**（`mjz-ai-pro`）是一个基于 **Python + Streamlit** 的 AI 应用原型：多轮对话、RAG 知识库、Agent 工具、多格式附件解析。适用于 LLM 应用工程、RAG 与全栈方向的简历项目展示。

> 仓库地址：[https://github.com/MJZ66/mjz-ai-pro](https://github.com/MJZ66/mjz-ai-pro)

---

## 功能概览

| 模块 | 说明 |
|------|------|
| **多轮对话** | 6 类智能体角色；支持 txt/md/pdf/docx/xlsx/图片附件；拖入即解析，可直接追问 |
| **RAG 知识库** | 文档分块 → ChromaDB 向量库 → Top-K 检索 → 带【引用】的回答 |
| **Agent 工具** | 安全计算器（AST）、文本摘要（LLM） |
| **模型** | 通义千问 / DeepSeek（OpenAI Compatible API） |
| **工程化** | 分层目录、`pytest`、统一日志、友好错误提示 |

---

## 技术栈

- Python 3.8+
- Streamlit ≥ 1.30
- OpenAI Python SDK（兼容通义 / DeepSeek）
- ChromaDB（持久化向量库）
- PyPDF2、python-docx、openpyxl、Pillow

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/MJZ66/mjz-ai-pro.git
cd mjz-ai-pro
```

### 2. 创建虚拟环境并安装依赖

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. 配置环境变量（必做）

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

编辑 `.env`，填入你自己的 Key（**不要提交 `.env` 到 Git**）：

| 变量 | 说明 |
|------|------|
| `DASHSCOPE_API_KEY` | 通义千问（对话 + RAG 向量化） |
| `DEEPSEEK_API_KEY` | DeepSeek 对话（侧边栏选 DeepSeek 时使用） |
| `EMBEDDING_API_KEY` | 可选；默认同 `DASHSCOPE_API_KEY` |
| `EMBEDDING_BASE_URL` | 默认通义 compatible-mode |
| `MODEL_NAME` | 如 `qwen-plus` |
| `EMBEDDING_MODEL` | 如 `text-embedding-v3` |

### 4. 启动应用

```bash
streamlit run app.py
```

浏览器打开：**http://localhost:8501**

---

## 使用说明

### 多轮对话

1. 侧边栏选择 **通义千问** 或 **DeepSeek**；API Key 可留空（自动读 `.env`）。
2. 选择智能体（通用 / 法律 / 代码 / 简历 / 文件 / 小红书文案等）。
3. **附件**：拖入 PDF/Word 等 → 自动解析 → 底部直接提问（无需先点「分析」）。
4. 简单算式（如 `计算 (125+76)*9`）会走本地计算器，避免模型乱格式。

### RAG 知识库

1. 上传 txt / md / pdf / docx / xlsx → **构建索引**。
2. 在「检索问答」输入问题，查看回答与引用片段。

> **注意**：向量 Embedding 固定走**通义**接口。侧边栏选 DeepSeek 时，对话用 DeepSeek，向量化仍需 `DASHSCOPE_API_KEY`。

### Agent 工具

- `calculator`：如 `(125 + 76) * 9`
- `text_summary`：粘贴长文本生成摘要

---

## 项目结构

```
mjz-ai-pro/
├── app.py                 # Streamlit 主入口
├── requirements.txt
├── .env.example           # 配置模板（无真实 Key）
├── core/                  # 配置与 LLM 客户端
├── agents/                # 对话与工具调度
├── rag/                   # 文档加载、分块、向量库、检索
├── tools/                 # calculator、text_summary
├── ui/                    # 主题、上传区、面板
├── utils/                 # 文件、会话、附件上下文、日志
├── tests/                 # pytest
├── docs/                  # 实施报告与配置说明
└── assets/                # 运行截图（可选）
```

---

## 测试

```bash
pytest tests/ -v
```

---

## 文档

| 文档 | 内容 |
|------|------|
| [docs/配置与安全说明.md](docs/配置与安全说明.md) | 环境变量、厂商 Key 分工、防泄露 |
| [docs/MJZ_AI_Pro_实施报告.md](docs/MJZ_AI_Pro_实施报告.md) | 模块划分与实施记录 |
| [docs/项目功能检查报告.md](docs/项目功能检查报告.md) | 功能验收清单 |
| [SECURITY.md](SECURITY.md) | 安全与密钥政策 |

---

## 常见问题

**Q：侧边栏留空仍提示 API Key 无效？**  
A：选 DeepSeek 时需配置 `DEEPSEEK_API_KEY`；选通义时需 `DASHSCOPE_API_KEY`。不要用通义 Key 调 DeepSeek 接口。

**Q：RAG 向量化 404？**  
A：确认 `EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1` 且 `EMBEDDING_MODEL=text-embedding-v3`。

**Q：页面报 `removeChild` 前端错误？**  
A：硬刷新（Ctrl+F5）或重启 Streamlit；请使用本仓库最新版。

---

## 安全声明

- **禁止**在代码或文档中硬编码 API Key。
- `.env`、`data/`、`.venv/` 已加入 `.gitignore`。
- 若 Key 曾泄露，请在云平台**立即轮换**。

---

## License

MIT License — 见 [LICENSE](LICENSE)。

---

## 作者

赵洋 · [GitHub @MJZ66](https://github.com/MJZ66)
