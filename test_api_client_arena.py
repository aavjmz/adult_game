#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""客户端 API 军演接口测试

验证 /api/v1/arena：建档、对手批次（真人 + 电脑补齐）、挑战扣演券与积分得失、
真人守方积分与防守战报、同一对手不可重复挑战、演券用尽与隔天重置、
换一批、段位之赏每日一次、未布阵不能出战、计入军令周常。
用临时 SQLite 库运行，不碰 data/game.db：
    python test_api_client_arena.py
"""
import os
import sys
import tempfile
from datetime import timedelta
from unittest import mock

os.environ['DB_PATH'] = os.path.join(tempfile.mkdtemp(), 'test_api_arena.db')

from app import create_app, db  # noqa: E402
from app.models import Card, UserCard  # noqa: E402
from app.orders_data import game_today  # noqa: E402

failures = []


def check(cond, label):
    print(f"  [{'OK' if cond else 'FAIL'}] {label}")
    if not cond:
        failures.append(label)


def main():
    app = create_app()
    client = app.test_client()

    def register(name, level):
        res = client.post('/api/v1/auth/register', json={
            'username': name, 'email': f'{name}@test.local', 'password': 'Passw0rd!'}).get_json()
        auth = {'Authorization': f"Bearer {res['data']['token']}"}
        uid = res['data']['user']['id']
        with app.app_context():
            heroes = Card.query.filter(db.or_(Card.is_enemy.is_(False), Card.is_enemy.is_(None))).order_by(Card.id).limit(3).all()
            ucs = [UserCard(user_id=uid, card_id=c.id, level=level) for c in heroes]
            db.session.add_all(ucs)
            db.session.commit()
            ids = [uc.id for uc in ucs]
        return auth, ids

    strong, strong_ids = register('arena_strong', 60)
    weak, weak_ids = register('arena_weak', 1)

    def state(auth):
        return client.get('/api/v1/arena', headers=auth).get_json()['data']

    def post(auth, path, **body):
        return client.post(f'/api/v1/arena/{path}', headers=auth, json=body).get_json()

    print('\n[未布阵]')
    st = state(strong)
    check(st['score'] == 1000 and st['tickets'] == {'left': 5, 'max': 5}, '建档：积分 1000、演券 5/5')
    check(len(st['foes']) == 5 and all(f['kind'] == 'npc' for f in st['foes']), '没有布阵的真人时，五名全是电脑')
    body = post(strong, 'fight', index=0)
    check(body['success'] is False and '编伍' in body['error'], f"未布阵不能出战：{body['error']}")

    print('\n[真人对手]')
    client.post('/api/v1/formation', headers=weak, json={'slots': weak_ids + [None] * 3})
    client.post('/api/v1/formation', headers=strong, json={'slots': strong_ids + [None] * 3})
    st = post(strong, 'refresh')['data']
    kinds = [f['kind'] for f in st['foes']]
    check(kinds.count('player') == 1 and len(kinds) == 5, f'换一批：真人 1 名 + 电脑补齐 {kinds}')
    idx = kinds.index('player')
    foe = st['foes'][idx]
    check(foe['name'] == 'arena_weak' and foe['power'] > 0 and foe['odds'] >= 50, f"真人对手战力 {foe['power']}，胜算 {foe['odds']}%")
    check(st['power'] > foe['power'], f"我军战力 {st['power']} 高于对手")
    npc_powers = [f['power'] for f in st['foes'] if f['kind'] == 'npc']
    check(npc_powers == sorted(npc_powers) or len(set(npc_powers)) > 1, f'电脑对手强弱有别 {npc_powers}')

    coins0 = client.get('/api/v1/user/info', headers=strong).get_json()['data']['coins']
    body = post(strong, 'fight', index=idx)
    res = body['data']['result']
    check(body['success'] and res['win'], '60 级打 1 级：胜')
    check(res['delta'] > 0 and body['data']['state']['score'] == 1000 + res['delta'], f"积分 +{res['delta']}")
    check(body['data']['user']['coins'] == coins0 + 1500, '胜一场 +1,500 银两')
    check(body['data']['state']['tickets']['left'] == 4, '演券 4/5')
    check(body['data']['state']['foes'][idx]['fought'], '该对手标记已演')
    check(res['battle_log'], '返回战报事件')
    check(post(strong, 'fight', index=idx)['error'].startswith('此人本批已演'), '同一对手不能再打')
    check(post(strong, 'fight', index=9)['error'] == '对手不存在', '序号越界')

    wst = state(weak)
    check(wst['score'] == 1000 - round(res['delta'] * 0.5), f"守方积分 -{round(res['delta'] * 0.5)}")
    check(wst['logs'] and wst['logs'][0]['defense'] and not wst['logs'][0]['win'], '守方战报：防守失利')
    check(state(strong)['rank'] == 1 and wst['rank'] == 2, '名次按积分')

    print('\n[演券与隔天]')
    st = state(strong)
    left = [i for i, f in enumerate(st['foes']) if not f['fought']]
    for i in left:
        post(strong, 'fight', index=i)
    st = state(strong)
    check(st['tickets']['left'] == 0, '五张演券用完')
    check(st['today']['wins'] + st['today']['losses'] == 5, f"今日 胜 {st['today']['wins']} 负 {st['today']['losses']}")
    st = post(strong, 'refresh')['data']
    check(post(strong, 'fight', index=0)['error'].startswith('演券已尽'), '演券用尽不能出战')
    tomorrow = game_today() + timedelta(days=1)
    with mock.patch('app.utils.arena.game_today', return_value=tomorrow):
        check(state(strong)['tickets']['left'] == 5, '次日演券恢复 5 张')
        check(post(strong, 'fight', index=0)['success'], '次日可再战')

    print('\n[段位之赏]')
    st = state(weak)
    check(st['tier'] == '蛰伏' and not st['tier_reward']['claimed'], '积分不足 1300 为蛰伏')
    gems0 = client.get('/api/v1/user/info', headers=weak).get_json()['data']['gems']
    body = post(weak, 'reward')
    check(body['success'] and body['data']['user']['gems'] == gems0 + 40, '蛰伏领 40 元宝')
    check(body['data']['state']['tier_reward']['claimed'], '标记已领')
    check(post(weak, 'reward')['error'] == '今日已领段位之赏', '一天只能领一次')

    print('\n[军令]')
    orders = client.get('/api/v1/orders', headers=strong).get_json()['data']['orders']
    weekly = next(o for o in orders if o['key'] == 'weekly_arena')
    check(weekly['progress'] >= 5, f"周常「军演十场」进度 {weekly['progress']}")

    print()
    if failures:
        print(f'[失败] {len(failures)} 项未通过')
        sys.exit(1)
    print('[成功] 军演客户端接口全部通过')


if __name__ == '__main__':
    main()
