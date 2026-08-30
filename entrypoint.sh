#!/bin/bash
set -e

echo "Starting Adult Card Game..."

# 检查数据库是否存在
if [ ! -f "/app/data/game.db" ]; then
    echo "Database not found. Initializing database..."
    python migrate_complete.py
    echo "Database initialized successfully!"
else
    echo "Database found. Skipping initialization."
fi

# 启动应用（gunicorn，替代 Werkzeug 开发服务器）
#
# worker 数默认为 1，是被 SQLite 约束的刻意选择：SQLite 同一时刻只允许一个
# 写事务，多进程并发写只会制造 "database is locked"，对写入吞吐毫无帮助。
# 并发改用线程承担（同进程内由 SQLAlchemy 连接池串行化）。
# 迁移到 PostgreSQL 后可将 GUNICORN_WORKERS 提到 (2*CPU+1)。
#
# 未使用 --preload：create_app() 里的 db.create_all() 会在 fork 前打开
# 数据库连接，被子进程继承会导致 SQLite 文件句柄共享。
WORKERS="${GUNICORN_WORKERS:-1}"
THREADS="${GUNICORN_THREADS:-8}"

echo "Starting gunicorn (workers=${WORKERS}, threads=${THREADS})..."
exec gunicorn \
    --bind "${FLASK_HOST:-0.0.0.0}:${FLASK_PORT:-8080}" \
    --workers "${WORKERS}" \
    --threads "${THREADS}" \
    --worker-class gthread \
    --timeout 60 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --max-requests 2000 \
    --max-requests-jitter 200 \
    --access-logfile - \
    --error-logfile - \
    --access-logformat '%({X-Forwarded-For}i)s "%(r)s" %(s)s %(b)s %(M)sms "%(a)s"' \
    run:app
