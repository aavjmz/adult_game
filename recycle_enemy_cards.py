#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回收玩家已抽到的敌军卡

敌军卡排除出卡池（Card.is_enemy）之前，玩家可能已经从招贤里抽到了
黄巾贼兵、张角之类的敌军。本脚本把这些 UserCard 从玩家名下删除。

- 默认只预览：列出每个玩家会被回收哪些卡，不改数据库
- 加 --apply 才真正执行
- 敌军身上穿的装备先卸回背包再删卡：UserCard.equipments 配置了
  delete-orphan 级联，直接删卡会把装备一并删掉
- 抽卡记录（gacha_records）保留，作为历史不动

用法:
    python recycle_enemy_cards.py           # 预览
    python recycle_enemy_cards.py --apply   # 执行
"""
import sys
from collections import defaultdict

from app import create_app, db
from app.models import Card, Equipment, User, UserCard


def recycle(apply: bool) -> None:
    app = create_app()

    with app.app_context():
        # create_app 启动时已补好 is_enemy 列并标出敌军卡
        targets = (UserCard.query.join(Card, UserCard.card_id == Card.id)
                   .filter(Card.is_enemy.is_(True))
                   .order_by(UserCard.user_id, UserCard.id)
                   .all())

        if not targets:
            print('[完成] 没有玩家持有敌军卡，无需回收')
            return

        by_user = defaultdict(list)
        for uc in targets:
            by_user[uc.user_id].append(uc)

        target_ids = [uc.id for uc in targets]
        equipped = Equipment.query.filter(Equipment.owner_card_id.in_(target_ids)).all()

        print(f'[统计] {len(by_user)} 名玩家共持有 {len(targets)} 张敌军卡，'
              f'其中 {len(equipped)} 件装备穿在这些卡上')
        for user_id, cards in by_user.items():
            user = db.session.get(User, user_id)
            name = user.username if user else f'(已删除用户 {user_id})'
            detail = '、'.join(f'{uc.card.name} Lv.{uc.level}' for uc in cards)
            print(f'  - {name}: {detail}')

        if not apply:
            print('\n[预览] 未修改数据库。确认无误后加 --apply 执行')
            return

        for eq in equipped:
            eq.owner_card_id = None
        db.session.flush()

        for uc in targets:
            db.session.delete(uc)
        db.session.commit()

        print(f'\n[完成] 已回收 {len(targets)} 张敌军卡，卸下 {len(equipped)} 件装备回背包')


if __name__ == '__main__':
    recycle(apply='--apply' in sys.argv[1:])
