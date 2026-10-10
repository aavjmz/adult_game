#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""客户端 API 成长 / 装备接口测试

验证 /api/v1/growth/* 与 /api/v1/equipment/* 走 Bearer Token 认证、
复用 Web 端业务逻辑，并统一返回 {success, data, error} 信封。

用临时 SQLite 库运行，不碰 data/game.db：
    python test_api_client_growth.py
"""
import os
import sys
import tempfile

os.environ['DB_PATH'] = os.path.join(tempfile.mkdtemp(), 'test_api_growth.db')

from app import create_app, db  # noqa: E402
from app.models import Card, Equipment, User, UserCard, UserItem  # noqa: E402

failures = []


def check(cond, label):
    print(f"  [{'OK' if cond else 'FAIL'}] {label}")
    if not cond:
        failures.append(label)


def main():
    app = create_app()
    client = app.test_client()

    res = client.post('/api/v1/auth/register', json={
        'username': 'growth_tester', 'email': 'growth@test.local', 'password': 'Passw0rd!'})
    token = res.get_json()['data']['token']
    auth = {'Authorization': f'Bearer {token}'}

    with app.app_context():
        user = User.query.filter_by(username='growth_tester').first()
        user.coins = 10_000_000
        card = Card.query.filter_by(is_enemy=False).first()
        uc = UserCard(user_id=user.id, card_id=card.id)
        db.session.add(uc)
        db.session.add(UserItem(user_id=user.id, item_type='exp_potion', item_subtype='medium', quantity=3))
        db.session.add(UserItem(user_id=user.id, item_type='enhance_stone', quantity=50))
        eq = Equipment(user_id=user.id, name='青釭剑', type='weapon', quality='rare')
        db.session.add(eq)
        db.session.commit()
        uc_id, eq_id = uc.id, eq.id

    print('\n[认证]')
    res = client.get('/api/v1/growth/materials')
    check(res.status_code == 401 and res.get_json()['success'] is False, '无令牌返回 401 信封')

    print('\n[成长]')
    body = client.post('/api/v1/growth/level-up', headers=auth, json={
        'user_card_id': uc_id,
        'exp_items': [{'item_type': 'exp_potion', 'item_subtype': 'medium', 'quantity': 2}],
    }).get_json()
    check(body['success'] and body['data']['new_level'] > 1, f"升级成功 → Lv.{body['data'] and body['data'].get('new_level')}")
    check('user' in body['data'] and body['data']['user']['coins'] == 10_000_000, '写操作附带最新 user')

    body = client.post('/api/v1/growth/level-up', headers=auth, json={
        'user_card_id': uc_id,
        'exp_items': [{'item_type': 'exp_potion', 'item_subtype': 'medium', 'quantity': 5}],
    }).get_json()
    check(body['success'] is False and '数量不足' in body['error'], f"道具不足返回错误信封：{body['error']}")

    body = client.get(f'/api/v1/growth/card-stats/{uc_id}', headers=auth).get_json()
    check(body['success'] and body['data'], '查询卡牌属性')

    body = client.get('/api/v1/growth/card-stats/999999', headers=auth).get_json()
    check(body['success'] is False and body['error'] == '卡牌不存在', '他人或不存在的卡被拒')

    body = client.get('/api/v1/growth/materials', headers=auth).get_json()
    check(body['success'], '查询材料')

    res = client.post('/api/v1/growth/star-up', headers=auth, data='not json')
    check(res.status_code == 400 and res.get_json()['error'] == '请求体须为 JSON 对象', '非 JSON 请求体被拒')

    print('\n[装备]')
    body = client.get('/api/v1/equipment/list', headers=auth).get_json()
    check(body['success'], '装备列表')

    body = client.post('/api/v1/equipment/equip', headers=auth,
                       json={'user_card_id': uc_id, 'equipment_id': eq_id}).get_json()
    check(body['success'], f"穿戴装备 {body.get('error') or ''}")

    body = client.get(f'/api/v1/equipment/card/{uc_id}', headers=auth).get_json()
    check(body['success'], '查询武将身上装备')

    body = client.post('/api/v1/equipment/enhance', headers=auth, json={'equipment_id': eq_id}).get_json()
    check(body['success'] and body['data']['result'] in ('success', 'fail', 'fail_protected'),
          f"强化（结果 {body['data'] and body['data'].get('result')}）")
    check(body['data']['user']['coins'] < 10_000_000, '强化扣除银两并回传')

    body = client.post('/api/v1/equipment/unequip', headers=auth, json={'equipment_id': eq_id}).get_json()
    check(body['success'], f"卸下装备 {body.get('error') or ''}")

    body = client.post('/api/v1/equipment/lock', headers=auth, json={'equipment_id': eq_id}).get_json()
    check(body['success'], '锁定装备')

    body = client.post('/api/v1/equipment/dismantle', headers=auth, json={'equipment_id': eq_id}).get_json()
    check(body['success'] is False and '锁定' in body['error'], f"锁定后不可分解：{body['error']}")

    for path in ('/api/v1/equipment/templates', '/api/v1/equipment/sets'):
        check(client.get(path, headers=auth).get_json()['success'], f'GET {path}')

    print()
    if failures:
        print(f'[失败] {len(failures)} 项未通过')
        sys.exit(1)
    print('[成功] 成长 / 装备客户端接口全部通过')


if __name__ == '__main__':
    main()
