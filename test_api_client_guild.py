#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""客户端 API 盟接口测试

验证 /api/v1/guild：建盟（扣银两、盟名校验）、入盟 / 人数上限、捐献（盟功、盟阶经验、每日次数）、
盟令（全盟捐满后人人可领一次）、盟仓兑换（扣盟功、每日限换）、任命 / 让位 / 逐出权限、
离盟传位与解散、盟内与世界聊天（发言间隔）。用临时 SQLite 库运行，不碰 data/game.db：
    python test_api_client_guild.py
"""
import os
import sys
import tempfile
from unittest import mock

os.environ['DB_PATH'] = os.path.join(tempfile.mkdtemp(), 'test_api_guild.db')

from app import create_app, db  # noqa: E402
from app.models import User  # noqa: E402

failures = []


def check(cond, label):
    print(f"  [{'OK' if cond else 'FAIL'}] {label}")
    if not cond:
        failures.append(label)


def main():
    app = create_app()
    client = app.test_client()

    def register(name, coins=1_000_000):
        res = client.post('/api/v1/auth/register', json={
            'username': name, 'email': f'{name}@test.local', 'password': 'Passw0rd!'}).get_json()
        with app.app_context():
            User.query.filter_by(username=name).first().coins = coins
            db.session.commit()
        return {'Authorization': f"Bearer {res['data']['token']}"}, res['data']['user']['id']

    lord, lord_id = register('guild_lord')
    a, a_id = register('guild_a')
    b, b_id = register('guild_b')
    poor, _ = register('guild_poor', coins=100)

    def get(auth):
        return client.get('/api/v1/guild', headers=auth).get_json()['data']

    def post(auth, path, **body):
        return client.post(f'/api/v1/guild/{path}', headers=auth, json=body).get_json()

    print('\n[建盟]')
    st = get(lord)
    check(st['guild'] is None and st['guilds'] == [], '未入盟：无盟可加入')
    check(post(lord, 'create', name='虎')['error'].startswith('盟名须'), '盟名太短')
    check(post(poor, 'create', name='穷盟')['error'].startswith('建盟需银两'), '银两不足不能建盟')
    body = post(lord, 'create', name='虎牢义盟', motto='同年同月同日死')
    check(body['success'] and body['data']['state']['me']['role'] == '盟主', '建盟成功，自任盟主')
    check(body['data']['user']['coins'] == 1_000_000 - 50_000, '扣 50,000 银两')
    check(post(a, 'create', name='虎牢义盟')['error'] == '此盟名已有人用', '盟名不能重复')
    check(post(lord, 'create', name='另一个盟')['error'].startswith('已在盟中'), '已在盟中不能再建')

    print('\n[入盟]')
    lst = get(a)['guilds']
    check(len(lst) == 1 and lst[0]['name'] == '虎牢义盟' and lst[0]['max_members'] == 20, '盟列表：1 阶上限 20 人')
    gid = lst[0]['id']
    check(post(a, 'join', guild_id=gid)['success'] and post(b, 'join', guild_id=gid)['success'], '两人入盟')
    check(post(a, 'join', guild_id=gid)['error'].startswith('已在盟中'), '不能重复入盟')
    check(post(poor, 'join', guild_id=999)['error'] == '此盟不存在', '盟不存在')
    with mock.patch('app.utils.guild.max_members', return_value=3):
        check(post(poor, 'join', guild_id=gid)['error'] == '此盟人数已满', '人数已满')
    st = get(lord)
    check([m['name'] for m in st['members']] == ['guild_lord', 'guild_a', 'guild_b'], '成员按职位排序')
    check(all(m['online'] for m in st['members']), '刚用过客户端的成员显示在线')

    print('\n[捐献与盟令]')
    body = post(a, 'donate')
    me = body['data']['state']['me']
    check(body['success'] and me['contribution'] == 100, '捐献得盟功 100')
    check(body['data']['user']['coins'] == 1_000_000 - 10_000, '扣 10,000 银两')
    check(body['data']['state']['guild']['exp'] == 100, '盟阶经验 +100')
    post(a, 'donate'), post(a, 'donate')
    check(post(a, 'donate')['error'].startswith('今日已捐 3 次'), '每日至多 3 次')
    check(post(a, 'order')['error'].startswith('盟令未成'), '全盟捐献未满 10 次不能领盟令')
    for auth in (lord, b):
        for _ in range(3):
            post(auth, 'donate')
    st = get(lord)
    check(st['order']['progress'] == 9, f"全盟今日捐献 {st['order']['progress']}")
    with mock.patch('app.utils.guild.ORDER_TARGET', 9):
        gems0 = client.get('/api/v1/user/info', headers=b).get_json()['data']['gems']
        body = post(b, 'order')
        check(body['success'] and body['data']['user']['gems'] == gems0 + 50, '盟令达成，领 50 元宝')
        check(post(b, 'order')['error'] == '今日盟令已领', '每日只领一次')
    check(st['guild']['week_contribution'] == 900, '本周盟功 900')

    print('\n[盟仓]')
    body = post(a, 'exchange', key='book_small')
    check(body['success'] and body['data']['state']['me']['contribution'] == 100, '换初级技能书，盟功 300 → 100')
    check(post(a, 'exchange', key='star_stone')['error'] == '盟功不足，需 300', '盟功不足')
    check(post(a, 'exchange', key='nope')['error'] == '盟仓没有此物', '没有的东西')
    mats = client.get('/api/v1/growth/materials', headers=a).get_json()['data']['materials']
    check(mats.get('skill_book:small') == 1, '道具入背包')

    print('\n[职位]')
    check(post(a, 'role', user_id=b_id, role='精锐')['error'] == '只有盟主可以任命', '非盟主不能任命')
    check(post(lord, 'role', user_id=a_id, role='副盟主')['success'], '任命副盟主')
    check(post(lord, 'role', user_id=a_id, role='大将军')['error'] == '没有这个职位', '无效职位')
    check(post(a, 'kick', user_id=lord_id)['error'] == '无权逐出此人', '副盟主不能逐盟主')
    check(post(a, 'kick', user_id=b_id)['success'], '副盟主逐出盟众')
    check(get(b)['guild'] is None, '被逐者回到未入盟状态')
    post(b, 'join', guild_id=gid)

    print('\n[聊天]')
    body = post(lord, 'chat', channel='guild', text='诸君戮力')
    check(body['success'] and body['data']['messages'][-1]['badge'] == '盟主', '盟内发言带职位')
    check(post(lord, 'chat', channel='guild', text='再言')['error'] == '传书太急，稍候再发', '发言间隔')
    check(post(b, 'chat', channel='world', text='')['error'] == '且书一言', '空消息')
    check(post(b, 'chat', channel='world', text='x' * 61)['error'] == '一次至多 60 字', '太长')
    body = post(poor, 'chat', channel='world', text='散人问好')
    check(body['success'] and body['data']['messages'][-1]['badge'] == '散人', '未入盟可在世界频道发言')
    msgs = client.get('/api/v1/guild/chat?channel=guild', headers=b).get_json()['data']['messages']
    check([m['text'] for m in msgs] == ['诸君戮力'], '盟友看到盟内消息')
    res = client.get('/api/v1/guild/chat?channel=guild', headers=poor).get_json()
    check(res['error'] == '尚未入盟', '未入盟看不到盟内频道')

    print('\n[离盟]')
    check(post(lord, 'leave')['success'], '盟主离盟')
    st = get(a)
    check(st['me']['role'] == '盟主' and st['me']['is_leader'], '传位给副盟主')
    post(a, 'leave')
    check(get(b)['me']['role'] == '盟主', '再传给剩下的人')
    post(b, 'leave')
    check(get(b)['guilds'] == [], '最后一人离盟，盟解散')

    print()
    if failures:
        print(f'[失败] {len(failures)} 项未通过')
        sys.exit(1)
    print('[成功] 盟客户端接口全部通过')


if __name__ == '__main__':
    main()
