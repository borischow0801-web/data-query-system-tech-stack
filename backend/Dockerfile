# 通用 Linux 镜像，便于在麒麟等国产服务器上构建（架构需与宿主机一致：amd64/arm64）
FROM python:3.11-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

# 部分依赖（如 pandas/numpy 已有 wheel）；若构建失败可取消注释安装 gcc
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -sf http://127.0.0.1:8000/health || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
