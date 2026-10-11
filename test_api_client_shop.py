#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""客户端 API 市集接口测试

验证 /api/v1/shop 货架与 /api/v1/shop/buy：扣银两、道具入背包、每日限购、
隔天重置。用临时 SQLite 库运行，不碰 data/game.db：
    python test_api_client_shop.py
"""
import os
import sys
import tempfile
from datetime import timedelta
from unittest import mock

os.environ['DB_PATH'] = os.path.join(tempfile.mkdtemp(), 'test_api_shop.db')

from app import create_app, db  # noqa: E402
from app.models import User  # noqa: E402
import app.shop_data as shop_data  # noqa: E402

failures = []


def check(cond, label):
    print(f"  [{'OK' if cond else 'FAIL'}] {label}")
    if not cond:
        failures.append(label)


def main():
    app = create_app()
    client = app.test_client()

    res = client.post('/api/v1/auth/register', json={
        'username': 'shop_tester', 'email': 'shop@test.local', 'password': 'Passw0rd!'})
    auth = {'Authorization': f"Bearer {res.get_json()['data']['token']}"}

    with app.app_context():
        User.query.filter_by(username='shop_tester').first().coins = 100_000
        db.session.commit()

    def buy(key, times=1):
        return client.post('/api/v1/shop/buy', headers=auth, json={'key': key, 'times': times}).get_json()

    def mats():
        return client.get('/api/v1/growth/materials', headers=auth).get_json()['data']['materials']

    print('\n[货架]')
    check(client.get('/api/v1/shop').status_code == 401, '无令牌 401')
    data = client.get('/api/v1/shop', headers=auth).get_json()['data']
    check(data['tabs'] == ['养成', '锻造'], f"货架分类 {data['tabs']}")
    small = next(g for g in data['goods'] if g['key'] == 'exp_small')
    check(small['price'] == 1000 and small['remaining'] == 20 and small['bought_today'] == 0, '小经验丹 1,000 银 / 限购 20')
    check(not any(g['item_subtype'] in ('legendary', 'mythic') for g in data['goods']), '不卖传说 / 神话碎片')

    print('\n[购买]')
    body = buy('exp_small', 3)
    check(body['success'] and body['data']['user']['coins'] == 97_000, '买 3 个扣 3,000 银')
    check(body['data']['good']['remaining'] == 17 and body['data']['owned'] == 3, '剩余 17 次，背包 3 个')
    check(mats().get('exp_potion:small') == 3, '背包里有小经验丹 ×3')

    body = buy('enhance_stone', 2)
    check(body['success'] and mats().get('enhance_stone') == 20, '强化石 ×10 买 2 份 → 20 个')
    body = buy('star_stone')
    check(body['success'] and mats().get('star_stone') == 1, '星石（无子类型）入背包')

    print('\n[限购与校验]')
    body = buy('exp_small', 18)
    check(body['success'] is False and '还可买 17 次' in body['error'], f"超出限购：{body['error']}")
    body = buy('exp_small', 17)
    check(body['success'] and body['data']['good']['remaining'] == 0, '买满 20 次')
    body = buy('exp_small')
    check(body['success'] is False and '已售罄' in body['error'], f"售罄：{body['error']}")
    body = buy('exp_xlarge', 2)
    check(body['success'] is False and '银两不足' in body['error'], f"银两不足：{body['error']}")
    check(buy('nope')['error'] == '商品不存在', '未知商品')
    check(buy('exp_medium', 0)['error'] == '购买数量无效', '数量 0 被拒')

    print('\n[隔天重置]')
    tomorrow = shop_data.shop_today() + timedelta(days=1)
    with mock.patch('app.shop_data.shop_today', return_value=tomorrow):
        small = next(g for g in client.get('/api/v1/shop', headers=auth).get_json()['data']['goods']
                     if g['key'] == 'exp_small')
        check(small['remaining'] == 20, '次日限购恢复 20 次')
        check(buy('exp_small')['success'], '次日可再买')

    print()
    if failures:
        print(f'[失败] {len(failures)} 项未通过')
        sys.exit(1)
    print('[成功] 市集客户端接口全部通过')


if __name__ == '__main__':
    main()
