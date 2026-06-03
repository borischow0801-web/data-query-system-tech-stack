#!/bin/sh
set -e
cd /app

# 首次部署需成功连接 MySQL；失败时容器退出便于编排重试
if [ "${SKIP_ALEMBIC:-0}" != "1" ]; then
  echo "Running alembic upgrade head..."
  alembic upgrade head
fi

exec gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -
