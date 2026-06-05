# MJZ AI Pro 部署文档

本文档记录 MJZ AI Pro 在阿里云 ECS 上的 Docker 化部署过程，适用于 Ubuntu 22.04 + Docker + Docker Compose 环境。

## 1. 项目说明

MJZ AI Pro 是一个 AI Agent / RAG 应用原型系统，支持多轮对话、文档问答、向量检索、工具调用和流式响应。

* GitHub：https://github.com/MJZ66/mjz-ai-pro
* Demo：http://118.31.70.255:8501
* 技术栈：Python、Streamlit、ChromaDB、OpenAI Compatible API、Docker、Docker Compose、Linux

## 2. 服务器环境

* 云服务器：阿里云 ECS
* 操作系统：Ubuntu 22.04 LTS
* CPU：2 vCPU
* 内存：8 GB
* 公网 IP：118.31.70.255

## 3. 安装基础工具

```bash
apt update && apt upgrade -y
apt install -y git curl wget vim unzip htop net-tools
```

## 4. 安装 Docker 和 Docker Compose

```bash
apt install -y docker.io
systemctl start docker
systemctl enable docker
docker --version
```

如果 `docker-compose-plugin` 无法安装，可使用：

```bash
apt install -y docker-compose
docker-compose --version
```

后续统一使用：

```bash
docker-compose up -d
```

## 5. 配置 Docker 镜像源

如果拉取 Docker Hub 镜像超时，可配置镜像源：

```bash
mkdir -p /etc/docker

cat > /etc/docker/daemon.json <<'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me"
  ]
}
EOF

systemctl daemon-reload
systemctl restart docker
```

## 6. 获取项目代码

```bash
mkdir -p /opt/projects
cd /opt/projects
git clone https://github.com/MJZ66/mjz-ai-pro.git
cd mjz-ai-pro
```

## 7. Dockerfile

项目根目录创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
```

## 8. docker-compose.yml

```yaml
version: "3.8"

services:
  mjz-ai-pro:
    build: .
    container_name: mjz-ai-pro
    ports:
      - "8501:8501"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./vector_store:/app/vector_store
    restart: always
```

## 9. 配置环境变量

```bash
cp .env.example .env
nano .env
```

示例：

```env
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen-plus
EMBEDDING_MODEL=text-embedding-v3

EMBEDDING_API_KEY=your_api_key
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
VECTOR_STORE_DIR=data/vector_store

DASHSCOPE_API_KEY=your_api_key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen-plus

DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

## 10. 构建并启动

```bash
docker-compose up -d --build
```

查看状态：

```bash
docker-compose ps
```

查看日志：

```bash
docker-compose logs --tail=80
```

正常情况下可看到：

```text
You can now view your Streamlit app in your browser.
External URL: http://118.31.70.255:8501
```

## 11. 阿里云安全组配置

如果浏览器无法访问，需要在 ECS 安全组中放行端口：

```text
协议类型：自定义 TCP
端口范围：8501/8501
授权对象：0.0.0.0/0
```

访问地址：

```text
http://118.31.70.255:8501
```

## 12. 常见问题

### 12.1 Docker Hub 拉取镜像超时

报错：

```text
i/o timeout
```

解决：配置 Docker 镜像源后重新构建。

### 12.2 Streamlit 前端兼容问题

如页面出现：

```text
NotFoundError: Failed to execute removeChild on Node
```

可尝试降低 Streamlit 版本，例如：

```text
streamlit==1.36.0
```

然后重新构建：

```bash
docker-compose down
docker-compose up -d --build
```

### 12.3 容器启动但浏览器打不开

检查容器：

```bash
docker-compose ps
```

检查本地访问：

```bash
curl http://localhost:8501
```

如果本地正常但公网打不开，通常是安全组未放行 8501。

## 13. 常用运维命令

```bash
docker-compose ps
docker-compose logs --tail=80
docker-compose restart
docker-compose down
docker-compose up -d --build
```

## 14. 部署结果

MJZ AI Pro 已成功部署至阿里云 ECS，并通过公网访问：

```text
http://118.31.70.255:8501
```
