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
        uc_id, eq_id, user_id, card_name = uc.id, eq.id, user.id, card.name

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
    stats = body['data']
    check(stats['next_star_up'] == {'duplicates': 1, 'star_stones': 10, 'coins': 50000},
          f"附带下一档升星需求 {stats['next_star_up']}")
    check(stats['next_breakthrough'] is not None and stats['duplicates_owned'] == 0, '附带突破需求与同名卡数')

    body = client.post('/api/v1/growth/star-up', headers=auth,
                       json={'user_card_id': uc_id, 'material_type': 'star_stone'}).get_json()
    check(body['success'] is False and '星石不足' in body['error'], f"星石不足被拒：{body['error']}")
    with app.app_context():
        db.session.add(UserItem(user_id=user_id, item_type='star_stone', quantity=10))
        db.session.commit()
    body = client.post('/api/v1/growth/star-up', headers=auth,
                       json={'user_card_id': uc_id, 'material_type': 'star_stone'}).get_json()
    check(body['success'] and body['data']['new_star_level'] == 2, '星石升星 ★1 → ★2')
    check(body['data']['user']['coins'] == 10_000_000 - 50000, '升星扣除银两并回传')

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
    worn = next(e for e in client.get('/api/v1/equipment/list', headers=auth).get_json()['data']['equipments']
                if e['id'] == eq_id)
    check(worn['owner_card_name'] == card_name, f"装备列表带穿戴者 {worn['owner_card_name']}")

    body = client.get(f'/api/v1/equipment/card/{uc_id}', headers=auth).get_json()
    check(body['success'], '查询武将身上装备')

    body = client.post('/api/v1/equipment/enhance', headers=auth, json={'equipment_id': eq_id}).get_json()
    check(body['success'] and body['data']['result'] in ('success', 'fail', 'fail_protected'),
          f"强化（结果 {body['data'] and body['data'].get('result')}）")
    check(body['data']['user']['coins'] < 10_000_000 - 50000, '强化扣除银两并回传')

    body = client.post('/api/v1/equipment/unequip', headers=auth, json={'equipment_id': eq_id}).get_json()
    check(body['success'], f"卸下装备 {body.get('error') or ''}")

    body = client.post('/api/v1/equipment/lock', headers=auth, json={'equipment_id': eq_id}).get_json()
    check(body['success'], '锁定装备')

    body = client.post('/api/v1/equipment/dismantle', headers=auth, json={'equipment_id': eq_id}).get_json()
    check(body['success'] is False and '锁定' in body['error'], f"锁定后不可分解：{body['error']}")

    for path in ('/api/v1/equipment/templates', '/api/v1/equipment/sets'):
        check(client.get(path, headers=auth).get_json()['success'], f'GET {path}')

    print('\n[碎片合成：同品级碎片合同品级装备]')
    from init_equipment_data import init_basic_equipments
    with app.app_context():
        init_basic_equipments()
        db.session.add(UserItem(user_id=user_id, item_type='equipment_fragment', item_subtype='legendary', quantity=100))
        db.session.commit()

    templates = client.get('/api/v1/equipment/templates', headers=auth).get_json()['data']['templates']
    common_tpl = next(t for t in templates if t['quality'] == 'common')
    check(common_tpl['synthesize_cost'] == {'fragments': 10, 'coins': 10000}, f"模板附带合成花费 {common_tpl['synthesize_cost']}")
    check({t['quality'] for t in templates} >= {'common', 'rare', 'epic'}, '已有普通 / 稀有 / 史诗模板')

    body = client.post('/api/v1/equipment/synthesize', headers=auth, json={'template_id': common_tpl['id']}).get_json()
    check(body['success'] is False and '普通碎片不足' in body['error'], f"传说碎片不能合普通装备：{body['error']}")

    with app.app_context():
        db.session.add(UserItem(user_id=user_id, item_type='equipment_fragment', item_subtype='common', quantity=10))
        db.session.commit()
    body = client.post('/api/v1/equipment/synthesize', headers=auth, json={'template_id': common_tpl['id']}).get_json()
    check(body['success'], f"普通碎片合成 {common_tpl['name']}")
    mats = client.get('/api/v1/growth/materials', headers=auth).get_json()['data']['materials']
    check(mats.get('equipment_fragment:common') == 0 and mats.get('equipment_fragment:legendary') == 100,
          '只扣普通碎片，传说碎片不动')

    new_id = body['data']['equipment']['id']
    body = client.post('/api/v1/equipment/dismantle', headers=auth, json={'equipment_id': new_id}).get_json()
    mats = client.get('/api/v1/growth/materials', headers=auth).get_json()['data']['materials']
    check(body['success'] and body['data']['fragment_quality'] == 'common'
          and mats.get('equipment_fragment:common') == body['data']['fragments_gained'],
          f"分解返还普通碎片：{body['data'] and body['data'].get('message')}")

    print()
    if failures:
        print(f'[失败] {len(failures)} 项未通过')
        sys.exit(1)
    print('[成功] 成长 / 装备客户端接口全部通过')


if __name__ == '__main__':
    main()
