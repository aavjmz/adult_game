"""
为测试用户添加测试卡牌
"""

import sys
import os

# 设置UTF-8编码输出（解决Windows GBK编码问题）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, User, Card, UserCard

def main():
    """为测试用户添加卡牌"""
    app = create_app()

    with app.app_context():
        # 获取测试用户
        user = User.query.filter_by(username='testuser').first()
        if not user:
            print("❌ 测试用户不存在")
            return

        # 获取一些卡牌（从每个稀有度各选一张）
        cards_to_add = []

        # 获取三国武将
        guan_yu = Card.query.filter_by(name='关羽').first()
        zhao_yun = Card.query.filter_by(name='赵云').first()
        zhuge_liang = Card.query.filter_by(name='诸葛亮').first()

        if guan_yu:
            cards_to_add.append(guan_yu)
        if zhao_yun:
            cards_to_add.append(zhao_yun)
        if zhuge_liang:
            cards_to_add.append(zhuge_liang)

        # 如果没有三国武将，添加任意卡牌
        if not cards_to_add:
            all_cards = Card.query.all()
            if all_cards:
                cards_to_add = all_cards[:3]

        if not cards_to_add:
            print("❌ 没有可用的卡牌")
            return

        print(f"为用户 {user.username} 添加卡牌:")

        for card in cards_to_add:
            # 检查是否已拥有
            existing = UserCard.query.filter_by(
                user_id=user.id,
                card_id=card.id
            ).first()

            if existing:
                print(f"  ⏭️ {card.name} ({card.rarity}) - 已拥有")
                continue

            # 添加卡牌
            user_card = UserCard(
                user_id=user.id,
                card_id=card.id,
                level=1,
                exp=0,
                star_level=1,
                awaken_level=0,
                breakthrough_level=0,
                main_skill_level=1,
                passive_skill_level=1
            )
            db.session.add(user_card)
            print(f"  ✅ {card.name} ({card.rarity})")

        db.session.commit()
        print("\n✅ 卡牌添加完成")

if __name__ == '__main__':
    main()
