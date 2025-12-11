#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置测试数据脚本

为测试用户添加卡牌，方便测试PVE战斗系统
"""

import sys
import io
from app import create_app, db
from app.models import User, Card, UserCard

# 修复Windows命令行编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def setup_test_data():
    """设置测试数据"""
    app = create_app()

    with app.app_context():
        print("[设置] 开始设置测试数据...")

        # 获取或创建测试用户
        test_user = User.query.filter_by(username='test_pve_user').first()

        if not test_user:
            print("\n[创建] 创建测试用户...")
            from datetime import datetime
            test_user = User(
                username='test_pve_user',
                email='test_pve@example.com',
                stamina=120,
                max_stamina=120,
                stamina_updated_at=datetime.utcnow(),
                coins=100000  # 给一些金币
            )
            test_user.set_password('test123')
            db.session.add(test_user)
            db.session.commit()
            print(f"  [OK] 测试用户创建成功 (ID: {test_user.id})")
        else:
            print(f"\n[OK] 测试用户已存在 (ID: {test_user.id})")

        # 给测试用户添加卡牌
        existing_cards = UserCard.query.filter_by(user_id=test_user.id).count()

        if existing_cards > 0:
            print(f"\n[OK] 测试用户已有 {existing_cards} 张卡牌")
            choice = input("是否清除并重新添加? (yes/no): ")
            if choice.lower() == 'yes':
                UserCard.query.filter_by(user_id=test_user.id).delete()
                db.session.commit()
                print("  [OK] 已清除现有卡牌")
            else:
                print("  [跳过] 保留现有卡牌")
                return

        # 添加测试卡牌
        print("\n[添加] 为测试用户添加卡牌...")

        # 获取各稀有度的卡牌
        n_cards = Card.query.filter_by(rarity='N').limit(2).all()
        r_cards = Card.query.filter_by(rarity='R').limit(2).all()
        sr_cards = Card.query.filter_by(rarity='SR').limit(2).all()
        ssr_cards = Card.query.filter_by(rarity='SSR').limit(1).all()

        cards_to_add = []
        cards_to_add.extend(n_cards)
        cards_to_add.extend(r_cards)
        cards_to_add.extend(sr_cards)
        cards_to_add.extend(ssr_cards)

        if not cards_to_add:
            print("  [警告] 数据库中没有卡牌，请先初始化卡牌数据")
            return

        for card in cards_to_add:
            user_card = UserCard(
                user_id=test_user.id,
                card_id=card.id,
                level=10,  # 给一些等级
                exp=0
            )
            db.session.add(user_card)
            print(f"  [+] {card.rarity} - {card.name} (等级10)")

        db.session.commit()

        total = len(cards_to_add)
        print(f"\n[成功] 共添加了 {total} 张卡牌")

        # 显示测试账号信息
        print("\n[测试账号信息]")
        print(f"  用户名: test_pve_user")
        print(f"  密码: test123")
        print(f"  金币: {test_user.coins}")
        print(f"  体力: {test_user.stamina}/{test_user.max_stamina}")
        print(f"  卡牌数: {total}张")

        print("\n[提示] 现在可以运行 python test_battle_system.py 测试战斗系统")


if __name__ == '__main__':
    setup_test_data()
