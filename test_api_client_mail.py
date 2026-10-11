#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""客户端 API 军书接口测试

验证 /api/v1/mail：注册收到欢迎信、未读数、阅读、领取附物（单封 / 一键）、
不可重复领、附物未领不可弃、清已阅、过期信不显示、平定整章发赏赐信（每章一次）、
send_mail.py 群发。用临时 SQLite 库运行，不碰 data/game.db：
    python test_api_client_mail.py
"""
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

os.environ['DB_PATH'] = os.path.join(tempfile.mkdtemp(), 'test_api_mail.db')

from app import create_app, db  # noqa: E402
from app.models import Mail, Stage, User, UserStageProgress  # noqa: E402
from app.utils.mail import check_chapter_cleared, send_mail  # noqa: E402

failures = []


def check(cond, label):
    print(f"  [{'OK' if cond else 'FAIL'}] {label}")
    if not cond:
        failures.append(label)


def main():
    app = create_app()
    client = app.test_client()

    res = client.post('/api/v1/auth/register', json={
        'username': 'mail_tester', 'email': 'mail@test.local', 'password': 'Passw0rd!'})
    auth = {'Authorization': f"Bearer {res.get_json()['data']['token']}"}
    user = res.get_json()['data']['user']
    tickets0, gems0 = user['tickets'], user['gems']

    with app.app_context():
        user_id = User.query.filter_by(username='mail_tester').first().id

    def state():
        return client.get('/api/v1/mail', headers=auth).get_json()['data']

    def post(path, **body):
        return client.post(f'/api/v1/mail/{path}', headers=auth, json=body).get_json()

    print('\n[欢迎信与未读]')
    check(client.get('/api/v1/mail').status_code == 401, '无令牌 401')
    st = state()
    check(len(st['mails']) == 1 and st['mails'][0]['title'] == '入营之礼', '注册即收到欢迎信')
    welcome = st['mails'][0]
    check(st['unread'] == 1 and not welcome['is_read'] and welcome['attachments'], '欢迎信未读、带附物')
    info = client.get('/api/v1/user/info', headers=auth).get_json()['data']
    check(info['unread_mail'] == 1, '/user/info 带未读数')

    print('\n[阅读与领取]')
    body = post('read', id=welcome['id'])
    check(body['success'] and body['data']['unread'] == 0, '阅读后未读 0')
    check(post('read', id=99999)['error'] == '军书不存在', '读不存在的信')

    body = post('delete', id=welcome['id'])
    check(body['success'] is False and '附物未领' in body['error'], f"附物未领不可弃：{body['error']}")

    body = post('claim', id=welcome['id'])
    check(body['success'] and body['data']['count'] == 1, '领取欢迎信附物')
    check(body['data']['user']['tickets'] == tickets0 + 10 and body['data']['user']['gems'] == gems0 + 200,
          '招贤令 +10、元宝 +200 到账')
    check(body['data']['state']['mails'][0]['claimed'], '信件标记已领')
    body = post('claim', id=welcome['id'])
    check(body['success'] is False and body['error'] == '无附物可领', '不可重复领')
    check(post('claim')['error'] == '请指定 id 或 all', '缺参数')

    print('\n[一键领取与清已阅]')
    with app.app_context():
        send_mail(user_id, '补偿一', rewards=[{'kind': 'coins', 'quantity': 500, 'item_type': None, 'item_subtype': None}])
        send_mail(user_id, '补偿二', rewards=[{'kind': 'item', 'quantity': 2, 'item_type': 'star_stone', 'item_subtype': None}])
        send_mail(user_id, '公告', body='无附物')
        send_mail(user_id, '过期补偿', rewards=[{'kind': 'gems', 'quantity': 999, 'item_type': None, 'item_subtype': None}],
                  expire_days=1)
        expired = Mail.query.filter_by(user_id=user_id, title='过期补偿').first()
        expired.expires_at = datetime.utcnow() - timedelta(minutes=1)
        db.session.commit()
        expired_id = expired.id
    st = state()
    titles = [m['title'] for m in st['mails']]
    check('过期补偿' not in titles, '过期信不显示')
    check(titles[:3] == ['公告', '补偿二', '补偿一'], f'新信在前 {titles}')
    check(st['unread'] == 3, f"未读 {st['unread']}")

    coins_before = client.get('/api/v1/user/info', headers=auth).get_json()['data']['coins']
    body = post('claim', all=True)
    check(body['success'] and body['data']['count'] == 2, '一键领取两封有附物的信')
    check(body['data']['user']['coins'] == coins_before + 500, '银两 +500')
    mats = client.get('/api/v1/growth/materials', headers=auth).get_json()['data']['materials']
    check(mats.get('star_stone') == 2, '星石入背包')
    check(post('claim', all=True)['error'] == '无附物可领', '再一键领取：无附物')
    check(post('claim', id=expired_id)['error'] == '军书不存在', '过期信不可领')

    body = post('delete', all=True)
    # 欢迎信、补偿一、补偿二已读（领取即已读）且已领，公告未读不清
    check(body['success'] and body['data']['count'] == 3, f"清已阅 {body['data'] and body['data']['count']} 封")
    check([m['title'] for m in body['data']['state']['mails']] == ['公告'], '只剩未读的公告')
    post('read', id=body['data']['state']['mails'][0]['id'])
    check(post('delete', all=True)['data']['count'] == 1, '阅后可清')
    check(post('delete', all=True)['error'] == '无已阅之书可清', '空了')

    print('\n[平定整章]')
    with app.app_context():
        stages = Stage.query.filter_by(stage_type='main', chapter=1).order_by(Stage.stage_number).all()
        for s in stages[:-1]:
            db.session.add(UserStageProgress(user_id=user_id, stage_id=s.id, is_cleared=True, stars=3))
        db.session.commit()
        check(check_chapter_cleared(user_id, stages[-2]) is None, '第一章未全通，不发')
        db.session.add(UserStageProgress(user_id=user_id, stage_id=stages[-1].id, is_cleared=True, stars=3))
        sent = check_chapter_cleared(user_id, stages[-1])
        db.session.commit()
        check(sent is not None and sent.title == '第1章平定之赏', '第一章全通，发平定之赏')
        check(check_chapter_cleared(user_id, stages[0]) is None, '同一章不重复发')
        db.session.commit()
    check(state()['mails'][0]['title'] == '第1章平定之赏', '玩家收到赏赐信')

    print('\n[send_mail.py]')
    client.post('/api/v1/auth/register', json={
        'username': 'mail_tester2', 'email': 'mail2@test.local', 'password': 'Passw0rd!'})
    cmd = [sys.executable, 'send_mail.py', '--all', '--title', '维护补偿', '--body', '谨奉补偿',
           '--gems', '50', '--item', 'exp_potion:large=3', '--days', '7']
    out = subprocess.run(cmd, capture_output=True, text=True, env=os.environ)
    check(out.returncode == 0 and '收件 2 人' in out.stdout, '群发给全部玩家')
    with app.app_context():
        mails = Mail.query.filter_by(title='维护补偿').all()
        check(len(mails) == 2 and all(m.expires_at for m in mails), '每人一封，带过期时间')
        check('exp_potion' in mails[0].attachments and '"large"' in mails[0].attachments, '道具附物带子类型')
    bad = subprocess.run([sys.executable, 'send_mail.py', '--user', 'nobody', '--title', 'x'],
                         capture_output=True, text=True, env=os.environ)
    check(bad.returncode == 1 and '找不到用户' in bad.stdout, '用户不存在时报错')

    print()
    if failures:
        print(f'[失败] {len(failures)} 项未通过')
        sys.exit(1)
    print('[成功] 军书客户端接口全部通过')


if __name__ == '__main__':
    main()
