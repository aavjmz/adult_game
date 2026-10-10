#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化PVE敌方卡牌

为PVE关卡添加敌方角色卡牌数据
"""

import sys
import io
from app import create_app, db
from app.models import Card
from app.enemy_cards import ENEMY_CARDS

# 修复Windows命令行编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def init_enemy_cards():
    """初始化敌方卡牌数据"""
    app = create_app()

    with app.app_context():
        print("[初始化] 开始初始化敌方卡牌...")

        enemy_cards = ENEMY_CARDS

        added_count = 0
        skipped_count = 0

        for card_data in enemy_cards:
            # 检查是否已存在
            existing = Card.query.filter_by(name=card_data['name']).first()
            if existing:
                print(f"  [跳过] {card_data['name']} 已存在")
                skipped_count += 1
                continue

            # 创建新卡牌
            # 敌军卡不进招贤卡池与图鉴
            card = Card(**card_data, is_enemy=True)
            db.session.add(card)
            added_count += 1
            print(f"  [+] {card_data['rarity']:3s} - {card_data['name']}")

        db.session.commit()

        print(f"\n[完成] 添加了 {added_count} 张敌方卡牌")
        if skipped_count > 0:
            print(f"[跳过] {skipped_count} 张卡牌已存在")

        # 显示统计
        total_cards = Card.query.count()
        print(f"\n[统计] 数据库中共有 {total_cards} 张卡牌")


if __name__ == '__main__':
    init_enemy_cards()
