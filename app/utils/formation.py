# -*- coding: utf-8 -*-
"""编伍阵容读取（出征、军演共用）"""
import json

from app.models import db, UserCard, UserFormation

FORMATION_SIZE = 6


def load_formation(user_id):
    """读取阵容，剔除已不属于该玩家的卡；返回长度 6 的 [UserCard.id | None]"""
    row = db.session.get(UserFormation, user_id)
    try:
        slots = json.loads(row.slots) if row else []
    except (TypeError, ValueError):
        slots = []
    slots = (list(slots) + [None] * FORMATION_SIZE)[:FORMATION_SIZE]

    ids = [s for s in slots if s is not None]
    owned = {uc.id for uc in UserCard.query.filter(UserCard.user_id == user_id, UserCard.id.in_(ids)).all()} if ids else set()
    return [s if s in owned else None for s in slots]


def formation_cards(user_id):
    """阵中武将（按阵位顺序，跳过空位）"""
    ids = [s for s in load_formation(user_id) if s is not None]
    by_id = {uc.id: uc for uc in UserCard.query.filter(UserCard.id.in_(ids)).all()} if ids else {}
    return [by_id[i] for i in ids if i in by_id]
