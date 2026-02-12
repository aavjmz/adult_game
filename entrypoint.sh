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

# 启动应用
echo "Starting Flask application..."
exec python run.py
