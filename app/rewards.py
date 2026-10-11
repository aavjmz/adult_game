# -*- coding: utf-8 -*-
"""
奖励：军令、军书附物等共用的奖励格式与发放

一条奖励为 {kind, quantity, item_type, item_subtype}：
kind 为 coins 银两 / gems 元宝 / tickets 招贤令 / item 背包道具（item_type、item_subtype 同 UserItem）。
"""
from app.models import db, UserItem

REWARD_KINDS = ('coins', 'gems', 'tickets', 'item')


def _r(kind, quantity, item_type=None, subtype=None):
    return {'kind': kind, 'quantity': quantity, 'item_type': item_type, 'item_subtype': subtype}


def coins(n):
    return _r('coins', n)


def gems(n):
    return _r('gems', n)


def tickets(n):
    return _r('tickets', n)


def item(item_type, n, subtype=None):
    return _r('item', n, item_type, subtype)


def grant(user, rewards):
    """把奖励加到玩家身上；只改 session，由调用方提交"""
    for r in rewards or []:
        kind, qty = r['kind'], r['quantity']
        if kind == 'coins':
            user.coins = (user.coins or 0) + qty
        elif kind == 'gems':
            user.gems = (user.gems or 0) + qty
        elif kind == 'tickets':
            user.tickets = (user.tickets or 0) + qty
        elif kind == 'item':
            row = UserItem.query.filter_by(
                user_id=user.id, item_type=r['item_type'], item_subtype=r['item_subtype']).first()
            if row is None:
                row = UserItem(user_id=user.id, item_type=r['item_type'], item_subtype=r['item_subtype'], quantity=0)
                db.session.add(row)
            row.quantity = (row.quantity or 0) + qty
        else:
            raise ValueError(f'未知奖励类型 {kind}')
