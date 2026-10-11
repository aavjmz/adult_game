#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化 / 同步 PVE 敌方卡牌

敌军数据统一写在 app/enemy_cards.py。改完后重跑本脚本：
- 新名字：新增为敌军卡（is_enemy=True，不进卡池）
- 已有的敌军卡：以配置为准逐列同步，配置里删掉的字段恢复为默认值
- 与玩家武将同名的：跳过，关卡直接复用玩家卡
可重复执行。
"""

import sys
import io
from app import create_app, db
from app.models import Card
from app.enemy_cards import ENEMY_CARDS
from app.utils.seed_sync import sync_columns

# 同步时不覆盖的列：主键、匹配键、创建时间，以及敌军标记本身
_SYNC_SKIP = {'id', 'name', 'created_at', 'is_enemy'}

# 修复Windows命令行编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def init_enemy_cards():
    """初始化敌方卡牌数据"""
    app = create_app()

    with app.app_context():
        print("[初始化] 开始初始化敌方卡牌...")

        added_count = 0
        updated_count = 0
        same_count = 0
        skipped_count = 0

        for card_data in ENEMY_CARDS:
            existing = Card.query.filter_by(name=card_data['name']).first()

            if not existing:
                # 敌军卡不进招贤卡池与图鉴
                db.session.add(Card(**card_data, is_enemy=True))
                added_count += 1
                print(f"  [+] {card_data['rarity']:3s} - {card_data['name']}")
                continue

            if not existing.is_enemy:
                # 与玩家武将同名（张辽、吕布等），关卡复用玩家卡，绝不改玩家卡数值
                skipped_count += 1
                print(f"  [跳过] {card_data['name']} 是玩家武将，关卡直接复用")
                continue

            # 已有的敌军卡：以 app/enemy_cards.py 为准逐列同步，
            # 配置里删掉的字段恢复为列默认值
            changed = sync_columns(existing, card_data, _SYNC_SKIP)
            if changed:
                updated_count += 1
                print(f"  [~] {card_data['name']}: {', '.join(changed)}")
            else:
                same_count += 1

        db.session.commit()

        print(f"\n[完成] 新增 {added_count} 张，更新 {updated_count} 张，{same_count} 张无变化，"
              f"跳过 {skipped_count} 张与玩家同名的武将")

        # 显示统计
        total_cards = Card.query.count()
        print(f"\n[统计] 数据库中共有 {total_cards} 张卡牌")


if __name__ == '__main__':
    init_enemy_cards()
