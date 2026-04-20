FROM python:3.12-slim

LABEL maintainer="AI Content Hub Contributors"
LABEL description="个人知识采集中枢 — 多平台内容统一采集、整理、同步"

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 安装Python包
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/
RUN pip install --no-cache-dir ".[all]"

# 配置和数据目录
VOLUME /app/config
VOLUME /app/data

# 环境变量
ENV PYTHONIOENCODING=utf-8
ENV AI_CONTENT_HUB_CONFIG=/app/config/config.yaml
ENV AI_CONTENT_HUB_DATA=/app/data

# 健康检查
HEALTHCHECK --interval=60s --timeout=10s --retries=3 \
    CMD python -c "import ai_content_hub; print('ok')" || exit 1

# 默认运行MCP Server
CMD ["python", "-m", "ai_content_hub.mcp.server"]
