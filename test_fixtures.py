# -*- coding: utf-8 -*-
"""
测试用的数据准备（不是测试本身）

原先测试依赖事先跑过 init_database.py / setup_test_data.py / add_test_cards.py
建出测试账号，空库上会跳过或报错。这里在测试开头按需补齐，测试自给自足。
都可重复调用：已有的不重复创建。须在 app_context 内调用。
"""
from datetime import datetime

from app.models import db, Card, User, UserCard

# 优先给这几位，测试输出里看得懂；库里没有时按 id 顺序补
PREFERRED_HEROES = ['关羽', '赵云', '诸葛亮']


def ensure_test_user(username, password='test123', coins=10_000_000, card_count=3):
    """取得测试账号，不存在则创建；名下卡牌不足 card_count 张则补齐；
    新建的账号顺带发一套养成材料（同 grant_materials.py）"""
    user = User.query.filter_by(username=username).first()
    if user is None:
        user = User(
            username=username, email=f'{username}@test.local', coins=coins,
            stamina=120, max_stamina=120, stamina_updated_at=datetime.utcnow(),
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        print(f'  [准备] 创建测试账号 {username}')
        from grant_materials import grant_items
        grant_items(user)

    owned = UserCard.query.filter_by(user_id=user.id).count()
    if owned < card_count:
        preferred = Card.query.filter(Card.name.in_(PREFERRED_HEROES), Card.is_enemy.is_(False)).all()
        others = Card.query.filter(Card.is_enemy.is_(False), Card.name.notin_(PREFERRED_HEROES)).order_by(Card.id).all()
        for card in (preferred + others)[:card_count - owned]:
            db.session.add(UserCard(user_id=user.id, card_id=card.id))
        print(f'  [准备] 为 {username} 补 {card_count - owned} 张武将卡')

    db.session.commit()
    return user


def ensure_equipment_templates():
    """装备套装与模板（init_equipment_data 的同步函数，已有的不变）"""
    from app.models import EquipmentTemplate
    if EquipmentTemplate.query.count():
        return
    from init_equipment_data import (
        init_basic_equipments, init_equipment_sets, init_legendary_equipments, init_mythic_equipments,
    )
    init_equipment_sets()
    init_mythic_equipments()
    init_legendary_equipments()
    init_basic_equipments()
