#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复关卡敌方配置

将enemy_config中的card_name转换为card_id
"""

import sys
import io
import json
from app import create_app, db
from app.models import Stage, Card

# 修复Windows命令行编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def fix_stage_enemy_config():
    """修复关卡敌方配置"""
    app = create_app()

    with app.app_context():
        print("[修复] 开始修复关卡敌方配置...")

        # 构建卡牌名称到ID的映射
        print("\n[1] 构建卡牌映射表...")
        card_map = {}
        all_cards = Card.query.all()
        for card in all_cards:
            card_map[card.name] = card.id
        print(f"  [OK] 找到 {len(card_map)} 张卡牌")

        # 获取所有关卡
        stages = Stage.query.filter_by(stage_type='main').all()
        print(f"\n[2] 处理 {len(stages)} 个关卡...")

        fixed_count = 0
        error_count = 0

        for stage in stages:
            try:
                # 解析enemy_config
                enemy_config = json.loads(stage.enemy_config)
                enemies = enemy_config.get('enemies', [])

                updated = False
                missing_cards = []

                for enemy in enemies:
                    # 如果有card_name但没有card_id，进行转换
                    if 'card_name' in enemy and 'card_id' not in enemy:
                        card_name = enemy['card_name']
                        if card_name in card_map:
                            enemy['card_id'] = card_map[card_name]
                            # 保留card_name作为注释
                            updated = True
                        else:
                            missing_cards.append(card_name)

                    # 如果card_id是None，尝试从card_name转换
                    elif enemy.get('card_id') is None and 'card_name' in enemy:
                        card_name = enemy['card_name']
                        if card_name in card_map:
                            enemy['card_id'] = card_map[card_name]
                            updated = True
                        else:
                            missing_cards.append(card_name)

                if missing_cards:
                    print(f"  [错误] 关卡 {stage.stage_number}: {stage.name}")
                    print(f"         缺少卡牌: {', '.join(missing_cards)}")
                    error_count += 1
                    continue

                if updated:
                    # 更新数据库
                    stage.enemy_config = json.dumps(enemy_config, ensure_ascii=False)
                    fixed_count += 1
                    print(f"  [OK] 关卡 {stage.stage_number}: {stage.name} ({len(enemies)}个敌人)")

            except Exception as e:
                print(f"  [错误] 关卡 {stage.stage_number}: {str(e)}")
                error_count += 1

        # 提交更改
        if fixed_count > 0:
            db.session.commit()
            print(f"\n[成功] 修复了 {fixed_count} 个关卡")
        else:
            print(f"\n[完成] 没有需要修复的关卡")

        if error_count > 0:
            print(f"[警告] {error_count} 个关卡处理失败")


if __name__ == '__main__':
    fix_stage_enemy_config()
