#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化 / 同步主线关卡

关卡数据在 app/stage_data.py。改完数据后重跑本脚本：
- 缺少的关卡：新建
- 已有关卡：按 stage_number 原地同步数值，打印改了哪些字段；
  关卡 id 不变，玩家进度不受影响
- 可重复执行，不再询问确认

用法:
    python init_stages.py
    docker-compose exec game python init_stages.py
"""

import sys
import io

from app import create_app
from app.stage_data import sync_main_stages

# 修复Windows命令行编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def init_stages():
    """同步主线关卡"""
    app = create_app()

    with app.app_context():
        print("[同步] 主线关卡...")
        counts = sync_main_stages()
        print(f"\n[完成] 新建 {counts['added']} 关，更新 {counts['updated']} 关，"
              f"{counts['same']} 关无变化")


if __name__ == '__main__':
    init_stages()
