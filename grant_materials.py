#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给指定账号发放一批养成材料（测试用）

目前关卡只掉装备碎片，经验丹、星石、强化石、突破石都没有获取途径，
武将详情的升级 / 升星 / 突破 / 装备功能没法实测。本脚本直接往账号里
发一套材料，数量足够把每项功能至少走一遍。

- 可重复执行，每次在原有数量上叠加
- 装备：已跑过 init_equipment_data.py 时按装备模板四个部位各发一件，
  否则发四件旧式装备，穿戴 / 强化同样可用
- --dup：额外发同名武将卡。觉醒要 1 张、突破要 3 张同名卡，只发材料
  走不到突破；指定武将名和张数即可（没有这名武将时同时得到本体）

用法:
    python grant_materials.py <用户名> [--dup <武将名> <张数>]
    docker-compose exec game python grant_materials.py aavjmz --dup 关羽 5
"""
import json
import sys

from app import create_app, db
from app.models import Card, Equipment, EquipmentTemplate, User, UserCard, UserItem

COINS = 10_000_000

# (item_type, item_subtype, 数量)
ITEMS = [
    ('exp_potion', 'small', 50),
    ('exp_potion', 'medium', 30),
    ('exp_potion', 'large', 20),
    ('exp_potion', 'xlarge', 100),       # Lv.1→100 约需 804 万经验
    ('star_stone', None, 300),           # ★1→★5 合计需 200
    ('awaken_stone', None, 100),         # 觉醒需 50
    ('breakthrough_stone', None, 200),   # 第一次突破需 100
    ('skill_book', 'small', 10),
    ('skill_book', 'medium', 10),
    ('skill_book', 'large', 10),
    ('enhance_stone', None, 500),
    ('protection_charm', None, 20),
    # 合成装备消耗同品级碎片，够每档各合一件（普通 10 / 稀有 20 / 史诗 50 / 传说 100 / 神话 200）
    ('equipment_fragment', 'common', 30),
    ('equipment_fragment', 'rare', 60),
    ('equipment_fragment', 'epic', 100),
    ('equipment_fragment', 'legendary', 100),
    ('equipment_fragment', 'mythic', 200),
]

ITEM_NAME = {
    'exp_potion': '经验丹', 'star_stone': '万能星石', 'awaken_stone': '觉醒石',
    'breakthrough_stone': '突破石', 'skill_book': '技能书', 'enhance_stone': '强化石',
    'protection_charm': '保护符', 'equipment_fragment': '装备碎片',
}

SLOTS = ['weapon', 'armor', 'accessory', 'treasure']
LEGACY_GEAR = {
    'weapon': ('试锋剑', 'attack', 60),
    'armor': ('试炼甲', 'defense', 50),
    'accessory': ('试炼佩', 'hp', 400),
    'treasure': ('试炼印', 'attack', 40),
}
QUALITY_ORDER = ['epic', 'rare', 'legendary', 'common', 'mythic']


def grant_items(user):
    for item_type, subtype, qty in ITEMS:
        item = UserItem.query.filter_by(user_id=user.id, item_type=item_type, item_subtype=subtype).first()
        if item is None:
            item = UserItem(user_id=user.id, item_type=item_type, item_subtype=subtype, quantity=0)
            db.session.add(item)
        item.quantity = (item.quantity or 0) + qty
        label = ITEM_NAME.get(item_type, item_type) + (f'({subtype})' if subtype else '')
        print(f'  [+] {label} x{qty}  → 现有 {item.quantity}')


def grant_gear(user):
    from app.equipment_utils import generate_random_stats

    for slot in SLOTS:
        templates = EquipmentTemplate.query.filter_by(type=slot).all()
        if templates:
            # 优先发精品，避免一上来就是神品破坏测试手感
            templates.sort(key=lambda t: QUALITY_ORDER.index(t.quality) if t.quality in QUALITY_ORDER else 99)
            t = templates[0]
            stats = generate_random_stats(t.quality)
            eq = Equipment(user_id=user.id, template_id=t.id, name=t.name, type=t.type, quality=t.quality,
                           enhance_level=0, random_stats=json.dumps(stats) if stats else None, is_locked=False)
        else:
            name, stat_type, value = LEGACY_GEAR[slot]
            eq = Equipment(user_id=user.id, name=name, type=slot, quality='rare',
                           base_stat_type=stat_type, base_stat_value=value, enhance_level=0)
        db.session.add(eq)
        print(f'  [+] 装备 {eq.name}（{slot} · {eq.quality}）')


def grant_duplicates(user, card_name, count):
    card = Card.query.filter_by(name=card_name, is_enemy=False).first()
    if not card:
        print(f'  [跳过] 没有名为 {card_name} 的可招募武将')
        return
    for _ in range(count):
        db.session.add(UserCard(user_id=user.id, card_id=card.id))
    print(f'  [+] 武将卡 {card_name} x{count}')


def main():
    args = sys.argv[1:]
    dup = None
    if '--dup' in args:
        i = args.index('--dup')
        try:
            dup = (args[i + 1], int(args[i + 2]))
        except (IndexError, ValueError):
            print(__doc__)
            sys.exit(1)
        args = args[:i] + args[i + 3:]
    if len(args) != 1:
        print(__doc__)
        sys.exit(1)
    username = args[0]

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f'[错误] 找不到用户 {username}')
            sys.exit(1)

        print(f'[发放] 给 {username}（id={user.id}）发放养成材料')
        user.coins = (user.coins or 0) + COINS
        print(f'  [+] 银两 +{COINS:,}  → 现有 {user.coins:,}')
        grant_items(user)
        grant_gear(user)
        if dup:
            grant_duplicates(user, *dup)
        db.session.commit()
        print('[完成] 客户端重新打开武将详情即可看到')


if __name__ == '__main__':
    main()
