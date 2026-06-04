# Security Policy

## 敏感信息

本项目**不应**在仓库、Issue、PR 或截图中包含：

- API Key（`sk-` 开头等）
- `.env` 文件内容
- 私有文档全文（简历、合同等）

已忽略路径见 `.gitignore`：`.env`、`data/`、`.venv/`、`.streamlit/secrets.toml`。

## 报告安全问题

如发现仓库内存在泄露的密钥，请通过 GitHub Security Advisory 或私信仓库维护者，**勿在公开 Issue 粘贴 Key**。

## 建议

- 使用 `.env.example` 作为模板，真实 Key 仅保存在本地。
- 定期轮换 API Key。
- 生产部署请使用密钥管理服务，而非明文环境变量文件。
