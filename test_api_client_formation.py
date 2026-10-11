#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""客户端 API 编伍接口测试

验证 /api/v1/formation 读写、归属与重复校验、失效卡剔除，以及出征不传 team
时使用服务端阵容。用临时 SQLite 库运行，不碰 data/game.db：
    python test_api_client_formation.py
"""
import os
import sys
import tempfile

os.environ['DB_PATH'] = os.path.join(tempfile.mkdtemp(), 'test_api_formation.db')

from app import create_app, db  # noqa: E402
from app.models import Stage, User, UserCard  # noqa: E402
from test_fixtures import ensure_test_user  # noqa: E402

failures = []


def check(cond, label):
    print(f"  [{'OK' if cond else 'FAIL'}] {label}")
    if not cond:
        failures.append(label)


def register(client, name):
    res = client.post('/api/v1/auth/register', json={
        'username': name, 'email': f'{name}@test.local', 'password': 'Passw0rd!'})
    return {'Authorization': f"Bearer {res.get_json()['data']['token']}"}


def main():
    app = create_app()
    client = app.test_client()
    auth = register(client, 'form_tester')
    other_auth = register(client, 'form_other')

    with app.app_context():
        ensure_test_user('form_tester', card_count=4)
        ensure_test_user('form_other', card_count=1)
        mine = [uc.id for uc in UserCard.query.filter_by(
            user_id=User.query.filter_by(username='form_tester').first().id).order_by(UserCard.id)]
        theirs = UserCard.query.filter_by(user_id=User.query.filter_by(username='form_other').first().id).first().id
        stage1 = Stage.query.filter_by(stage_type='main', stage_number=1).first().id

    get = lambda: client.get('/api/v1/formation', headers=auth).get_json()
    save = lambda slots: client.post('/api/v1/formation', headers=auth, json={'slots': slots}).get_json()

    print('\n[读写]')
    check(client.get('/api/v1/formation').status_code == 401, '无令牌 401')
    check(get()['data']['slots'] == [None] * 6, '新账号为空阵')
    body = save([mine[0], None, mine[1], None, mine[2], None])
    check(body['success'], '保存阵容')
    check(get()['data']['slots'] == [mine[0], None, mine[1], None, mine[2], None], '读回一致')
    check(client.get('/api/v1/formation', headers=other_auth).get_json()['data']['slots'] == [None] * 6, '阵容按账号隔离')

    print('\n[校验]')
    check('6 个阵位' in save([mine[0]])['error'], '阵位数不对被拒')
    check('两个阵位' in save([mine[0], mine[0], None, None, None, None])['error'], '重复武将被拒')
    check('不属于你' in save([theirs, None, None, None, None, None])['error'], '他人卡牌被拒')
    check('卡牌 id' in save(['x', None, None, None, None, None])['error'], '非法值被拒')

    print('\n[失效卡剔除]')
    with app.app_context():
        db.session.delete(db.session.get(UserCard, mine[1]))
        db.session.commit()
    check(get()['data']['slots'] == [mine[0], None, None, None, mine[2], None], '已删除的卡从阵容中剔除')

    print('\n[出征用服务端阵容]')
    body = client.post('/api/v1/pve/battle/start', headers=auth, json={'stage_id': stage1}).get_json()
    # 没跑 init_enemy_cards 时敌军为空会报此错——能走到这一步说明阵容已被采用
    check(body['success'] or '敌军尚未配置' in (body['error'] or ''), f"不传 team 采用编伍阵容：{body['error'] or body['data']['result']}")
    save([None] * 6)
    body = client.post('/api/v1/pve/battle/start', headers=auth, json={'stage_id': stage1}).get_json()
    check(body['success'] is False and '编伍' in body['error'], f"空阵出征被拒：{body['error']}")

    print()
    if failures:
        print(f'[失败] {len(failures)} 项未通过')
        sys.exit(1)
    print('[成功] 编伍客户端接口全部通过')


if __name__ == '__main__':
    main()
