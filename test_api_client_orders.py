#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""客户端 API 军令接口测试

验证 /api/v1/orders：各玩法计入日常 / 周常进度、领取发奖、不可重复领、
一键领取、军功宝箱、隔天重置日常而周常保留、成就按当前数据统计、通行证累计军功。
用临时 SQLite 库运行，不碰 data/game.db：
    python test_api_client_orders.py
"""
import os
import sys
import tempfile
from datetime import date, timedelta
from unittest import mock

os.environ['DB_PATH'] = os.path.join(tempfile.mkdtemp(), 'test_api_orders.db')

from app import create_app, db  # noqa: E402
from app.models import Card, Stage, User, UserCard, UserItem, UserStageProgress  # noqa: E402

failures = []

# 固定在某周的周三，次日（周四）仍在同一周，下周一跨周；均在同一个月
WED = date(2026, 10, 14)
THU = WED + timedelta(days=1)
NEXT_MON = date(2026, 10, 19)


def check(cond, label):
    print(f"  [{'OK' if cond else 'FAIL'}] {label}")
    if not cond:
        failures.append(label)


def on_day(day):
    return mock.patch('app.utils.orders.game_today', return_value=day)


def main():
    app = create_app()
    client = app.test_client()

    with on_day(WED):
        res = client.post('/api/v1/auth/register', json={
            'username': 'order_tester', 'email': 'orders@test.local', 'password': 'Passw0rd!'})
    auth = {'Authorization': f"Bearer {res.get_json()['data']['token']}"}

    with app.app_context():
        user = User.query.filter_by(username='order_tester').first()
        user.tickets = 30
        user.coins = 100_000
        stage = Stage.query.filter_by(stage_type='main').order_by(Stage.chapter, Stage.stage_number).first()
        db.session.add(UserStageProgress(user_id=user.id, stage_id=stage.id, is_cleared=True, stars=3))
        db.session.commit()
        user_id, stage_id, stage_cost = user.id, stage.id, stage.stamina_cost

    def state():
        return client.get('/api/v1/orders', headers=auth).get_json()['data']

    def order(st, key):
        return next(o for o in st['orders'] if o['key'] == key)

    def claim(**body):
        return client.post('/api/v1/orders/claim', headers=auth, json=body).get_json()

    def chest(step):
        return client.post('/api/v1/orders/chest', headers=auth, json={'step': step}).get_json()

    print('\n[军令页]')
    check(client.get('/api/v1/orders').status_code == 401, '无令牌 401')
    with on_day(WED):
        st = state()
    check(st['tabs'] == ['日常', '周常', '成就', '通行证'], f"分类 {st['tabs']}")
    daily_total = sum(o['merit'] for o in st['orders'] if o['tab'] == '日常')
    check(daily_total == st['merit']['max'] == 120, f'日常军功合计 {daily_total} = 宝箱满档 120')
    check(order(st, 'daily_checkin')['ready'], '注册即点卯，可领')
    check(not order(st, 'daily_battle')['ready'] and order(st, 'daily_battle')['progress'] == 0, '出征 0/3')

    print('\n[玩法计入进度]')
    with on_day(WED):
        body = client.post('/api/v1/pve/battle/sweep', headers=auth, json={'stage_id': stage_id, 'times': 3}).get_json()
        check(body['success'], '扫荡 3 次')
        client.post('/api/v1/gacha/pull', headers=auth, json={'type': 'multi'})
        client.post('/api/v1/shop/buy', headers=auth, json={'key': 'exp_small'})
        st = state()
    check(order(st, 'daily_battle')['progress'] == 3 and order(st, 'daily_battle')['ready'], '扫荡计入出征 3/3')
    check(order(st, 'daily_stamina')['progress'] == 3 * stage_cost, f'消耗兵力计 {3 * stage_cost}')
    check(order(st, 'weekly_win')['progress'] == 3, '扫荡计入周常胜场 3')
    check(order(st, 'daily_gacha')['progress'] == 10 and order(st, 'daily_gacha')['ready'], '十连计 10 员')
    check(order(st, 'weekly_multi')['ready'], '十连完成周常')
    check(order(st, 'daily_shop')['ready'], '市集购买计入')
    check(not order(st, 'daily_skill')['ready'], '没升技能，磨刃未成')

    print('\n[领取]')
    with on_day(WED):
        body = claim(key='daily_checkin')
        check(body['success'] and body['data']['user']['gems'] == 20, '点卯领 20 元宝')
        check(body['data']['state']['merit']['today'] == 20, '今日军功 20')
        body = claim(key='daily_checkin')
        check(body['success'] is False and '已领取' in body['error'], f"不可重复领：{body['error']}")
        body = claim(key='daily_skill')
        check(body['success'] is False and '未成' in body['error'], f"未完成不可领：{body['error']}")
        check(claim(key='nope')['error'] == '军令不存在', '未知军令')

        body = claim(tab='日常')
        got = sorted(c['key'] for c in body['data']['claimed'])
        check(got == ['daily_battle', 'daily_gacha', 'daily_shop'], f'一键领取日常 {got}')
        merit = body['data']['state']['merit']
        check(merit['today'] == 70, f"今日军功 {merit['today']}")
        check(claim(tab='日常')['error'] == '暂无可领军令', '再一键领取：暂无可领')

        body = claim(key='weekly_multi')
        check(body['success'] and body['data']['user']['tickets'] == 30 - 10 + 1 + 3, '周常十连领 3 张招贤令')
        check(body['data']['state']['merit']['today'] == 70, '周常军功不计入今日军功')
        check(body['data']['state']['season']['merit'] == 110, '本季军功 = 日常 70 + 周常 40')

    print('\n[军功宝箱]')
    with on_day(WED):
        body = chest(60)
        check(body['success'] and body['data']['user']['gems'] == 20 + 30, '60 档开出 30 元宝')
        check(chest(60)['error'] == '此箱已启', '同一箱不能再开')
        check(chest(90)['error'] == '军功未足 90', '军功不足不能开')
        check(chest(45)['error'] == '宝箱不存在', '没有的档位')

    with app.app_context():
        items = {(i.item_type, i.item_subtype): i.quantity for i in UserItem.query.filter_by(user_id=user_id)}
    check(items.get(('exp_potion', 'small'), 0) >= 1, '道具奖励入背包')

    print('\n[隔天 / 跨周]')
    with on_day(THU):
        client.get('/api/v1/user/info', headers=auth)  # 次日启动客户端即点卯
        st = state()
    check(st['merit']['today'] == 0 and not st['merit']['chests'][1]['claimed'], '次日军功与宝箱重置')
    check(order(st, 'daily_battle')['progress'] == 0 and not order(st, 'daily_battle')['claimed'], '次日日常重置')
    check(order(st, 'daily_checkin')['ready'], '次日可再点卯')
    check(order(st, 'weekly_win')['progress'] == 3 and order(st, 'weekly_multi')['claimed'], '同周周常进度与领取保留')
    check(st['season']['checkin_days'] == 2, f"本季点卯 {st['season']['checkin_days']} 日")
    with on_day(NEXT_MON):
        st = state()
    check(order(st, 'weekly_win')['progress'] == 0 and not order(st, 'weekly_multi')['claimed'], '下周一周常重置')

    print('\n[成就]')
    with on_day(THU):
        st = state()
        check(not order(st, 'ach_collect')['ready'], f"收录 {order(st, 'ach_collect')['progress']}/10 未成")
        with app.app_context():
            heroes = Card.query.filter(db.or_(Card.is_enemy.is_(False), Card.is_enemy.is_(None))).limit(10).all()
            for c in heroes:
                db.session.add(UserCard(user_id=user_id, card_id=c.id))
            db.session.commit()
        st = state()
        check(order(st, 'ach_collect')['progress'] >= 10 and order(st, 'ach_collect')['ready'], '收录满十员可领')
        check(order(st, 'ach_clear')['target'] > 1, f"一统天下目标为主线关卡数 {order(st, 'ach_clear')['target']}")
        check(claim(key='ach_collect')['success'], '领取成就')
    with on_day(NEXT_MON):
        check(order(state(), 'ach_collect')['claimed'], '成就领过永久不再可领')

    print('\n[真实出征计入]')
    from init_enemy_cards import init_enemy_cards
    init_enemy_cards()
    with on_day(NEXT_MON):
        team = [c['user_card_id'] for c in client.get('/api/v1/cards/mine', headers=auth).get_json()['data']['cards']][:3]
        body = client.post('/api/v1/pve/battle/start', headers=auth,
                           json={'stage_id': stage_id, 'team': team}).get_json()
        check(body['success'], f"自动战斗 {body['error'] or body['data']['result']}")
        st = state()
        won = body['data']['result'] == 'win'
    check(order(st, 'daily_battle')['progress'] == 1, '出征一次计 1')
    check(order(st, 'weekly_win')['progress'] == (1 if won else 0), f"胜场随战果计入（本场{'胜' if won else '负'}）")

    print()
    if failures:
        print(f'[失败] {len(failures)} 项未通过')
        sys.exit(1)
    print('[成功] 军令客户端接口全部通过')


if __name__ == '__main__':
    main()
