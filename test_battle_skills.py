#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""战斗技能与手动模式测试

覆盖：技能解析与等级换算、出手顺序与冷却节奏、附加效果（眩晕、斩杀、吸血、群体回血、
无视防御、降防降攻）、自动战斗、手动战斗逐个下令、中途转托管、会话状态校验。
用临时 SQLite 库运行，不碰 data/game.db：
    python test_battle_skills.py
"""
import os
import random
import sys
import tempfile

os.environ['DB_PATH'] = os.path.join(tempfile.mkdtemp(), 'test_battle_skills.db')

from app import create_app, db  # noqa: E402
from app.models import Card, Stage, User, UserCard  # noqa: E402
from app.skills import skill_profile  # noqa: E402
from app.utils import battle_core as bc  # noqa: E402
from test_fixtures import ensure_test_user  # noqa: E402

failures = []


def check(cond, label):
    print(f"  [{'OK' if cond else 'FAIL'}] {label}")
    if not cond:
        failures.append(label)


def skill(mult=2.0, cd=3, target='single', **effects):
    return {'name': '测试技', 'level': 1, 'base_multiplier': mult, 'multiplier': mult, 'base_cooldown': cd,
            'cooldown': cd, 'target': target, 'effects': effects, 'description': ''}


def unit(uid, side, hp=1000, atk=100, df=0, spd=50, sk=None):
    return bc.make_unit(uid, side, uid, {'hp': hp, 'attack': atk, 'defense': df, 'speed': spd}, sk or skill())


def test_skill_parse(app):
    print('\n[技能解析]')
    with app.app_context():
        get = lambda n: Card.query.filter_by(name=n).first()
        zy = skill_profile(get('周瑜'))
        check(zy['multiplier'] == 2.8 and zy['target'] == 'all', '周瑜 280% 范围伤害 → 全体')
        gy = skill_profile(get('关羽'), 5)
        check(abs(gy['multiplier'] - 4.9) < 1e-9 and gy['cooldown'] == 2 and 'execute' in gy['effects'],
              f"关羽 Lv5：倍率 {gy['multiplier']}、冷却 {gy['cooldown']}、斩杀")
        check('490%攻击力' in gy['description'], f"描述随等级换算：{gy['description']}")
        check(skill_profile(get('吕布'))['effects'].get('ignore_def') == 1.0, '吕布 无视防御')
        check(skill_profile(get('刘备'))['effects'].get('team_heal') == 0.2, '刘备 全体回血 20%')
        dc = skill_profile(get('貂蝉'))
        check(dc['target'] == 'single' and 'atk_down_all' in dc['effects'], '貂蝉 单体伤害 + 全体降攻')


def test_order_and_cooldown():
    print('\n[出手顺序与冷却]')
    st = bc.new_state([unit('a0', 'ally', spd=80)], [unit('e0', 'enemy', hp=10 ** 9, spd=30, atk=1)])
    bc.run(st, manual=True)
    check(st['awaiting'] == 'a0' and not st['events'], '速度高的我方先出手，开局停在 a0')
    ready = []
    for _ in range(9):
        info = bc.awaiting_info(st)
        ready.append(info['skill']['ready'])
        bc.act(st, 'skill' if info['skill']['ready'] else 'attack', 'e0')
    # 开局等 1 次；冷却 3：用后隔 3 次出手
    check(ready == [False, True, False, False, False, True, False, False, False], f'技能可用节奏 {ready}')
    st2 = bc.new_state([unit('a0', 'ally', spd=80)], [unit('e0', 'enemy', hp=10 ** 9, spd=30, atk=1)])
    bc.run(st2, manual=True)
    try:
        bc.act(st2, 'skill', 'e0')
        check(False, '冷却中放技能应被拒')
    except ValueError as e:
        check('冷却中' in str(e), f'冷却中放技能被拒：{e}')
    check(all(ev['side'] in ('ally', 'enemy') for ev in st['events']), '事件带出手方')


def test_effects():
    print('\n[附加效果]')
    random.seed(1)
    # 眩晕：概率 100% 时目标下次出手被跳过
    st = bc.new_state([unit('a0', 'ally', spd=80, sk=skill(stun=1.0))], [unit('e0', 'enemy', hp=10 ** 9, spd=30)])
    st['units']['a0']['cd'] = 0
    bc.run(st, manual=True)
    bc.act(st, 'skill', 'e0')
    check(any(ev['action'] == 'stunned' and ev['actor_id'] == 'e0' for ev in st['events']), '眩晕：敌方跳过出手')

    # 斩杀：命中后低于 20% 直接击杀
    st = bc.new_state([unit('a0', 'ally', atk=900, spd=80, sk=skill(mult=1.0, execute=0.2))],
                      [unit('e0', 'enemy', hp=1000), unit('e1', 'enemy', hp=10 ** 9)])
    st['units']['a0']['cd'] = 0
    bc.run(st, manual=True)
    ev = bc.act(st, 'skill', 'e0')[0]
    check(ev['hits'][0]['killed'] and ev['hits'][0]['executed'], '斩杀：残血目标被斩杀')

    # 无视防御：防御极高时普攻只有 1，无视防御技能照常伤害
    st = bc.new_state([unit('a0', 'ally', atk=500, spd=80, sk=skill(mult=1.0, ignore_def=1.0))],
                      [unit('e0', 'enemy', hp=10 ** 9, df=5000)])
    bc.run(st, manual=True)
    normal = bc.act(st, 'attack', 'e0')[0]['damage']
    skilled = bc.act(st, 'skill', 'e0')[0]['damage']
    check(normal == 1 and skilled >= 400, f'无视防御：普攻 {normal}，技能 {skilled}')

    # 吸血 + 群体回血 + 降防 + 全体降攻
    st = bc.new_state([unit('a0', 'ally', spd=80, sk=skill(lifesteal=0.5, team_heal=0.2, def_down=0.3, atk_down_all=0.2)),
                       unit('a1', 'ally', spd=10)],
                      [unit('e0', 'enemy', hp=10 ** 9, df=100), unit('e1', 'enemy', hp=10 ** 9)])
    for u in st['units'].values():
        if u['side'] == 'ally':
            u['hp'] = 100
    st['units']['a0']['cd'] = 0
    bc.run(st, manual=True)
    ev = bc.act(st, 'skill', 'e0')[0]
    healed = {h['target_id'] for h in ev['heals']}
    types = sorted({e['type'] for e in ev['effects']})
    check({'a0', 'a1'} <= healed, f'吸血与群体回血：{ev["heals"]}')
    check(types == ['atk_down', 'def_down'], f'降防与全体降攻：{types}')
    check(bc._buff_value(st['units']['e0'], 'def_down') == 0.3, '目标带降防')


def test_group_attack():
    print('\n[群攻]')
    st = bc.new_state([unit('a0', 'ally', spd=80, sk=skill(target='all'))],
                      [unit('e0', 'enemy', hp=10 ** 9), unit('e1', 'enemy', hp=10 ** 9), unit('e2', 'enemy', hp=10 ** 9)])
    st['units']['a0']['cd'] = 0
    bc.run(st, manual=True)
    ev = bc.act(st, 'skill')[0]
    check(len(ev['hits']) == 3, '群攻命中全部 3 个敌人')


def test_api(app):
    print('\n[接口：自动 / 手动 / 转托管]')
    client = app.test_client()
    res = client.post('/api/v1/auth/register', json={
        'username': 'skill_tester', 'email': 'skill@test.local', 'password': 'Passw0rd!'})
    auth = {'Authorization': f"Bearer {res.get_json()['data']['token']}"}
    with app.app_context():
        user = ensure_test_user('skill_tester', card_count=3)
        user.stamina = 120
        for uc in UserCard.query.filter_by(user_id=user.id):
            uc.level = 20
        db.session.commit()
        # 首领关：战斗持续多个回合，技能有机会冷却完毕
        stage = Stage.query.filter_by(stage_type='main', stage_number=10).first().id
        team = [uc.id for uc in UserCard.query.filter_by(user_id=user.id)]
    post = lambda path, body: client.post(path, headers=auth, json=dict(body, team=team) if 'stage_id' in body else body).get_json()

    body = post('/api/v1/pve/battle/start', {'stage_id': stage, 'mode': 'auto'})
    check(body['success'] and body['data']['finished'], f"自动战斗完成：{body['error'] or body['data']['result']}")
    log = body['data']['battle_log']
    check(any(e['action'] == 'skill' for e in log), '自动战斗中有技能释放')
    check(all('id' in u and 'skill' in u for u in body['data']['allies']), '单位带 id 与技能信息')

    body = post('/api/v1/pve/battle/start', {'stage_id': stage, 'mode': 'manual'})
    data = body['data']
    check(body['success'] and not data['finished'] and data['awaiting'], f"手动开局等待下令：{data.get('awaiting', {}).get('name')}")
    sid = data['session_id']
    bad = post('/api/v1/pve/battle/action', {'session_id': sid, 'action': 'skill'})
    check(bad['success'] is False and '冷却中' in bad['error'], f"开局技能未就绪：{bad['error']}")

    steps = 0
    while not data['finished'] and steps < 200:
        aw = data['awaiting']
        action = 'skill' if aw['skill']['ready'] else 'attack'
        body = post('/api/v1/pve/battle/action', {'session_id': sid, 'action': action, 'target_id': aw['targets'][0]})
        assert body['success'], body['error']
        data = body['data']
        steps += 1
    check(data['finished'] and data['result'] in ('win', 'lose'), f"手动下令 {steps} 次打完：{data['result']}，{data['stars']} 星")
    check(any(e['action'] == 'skill' and e['side'] == 'ally' for e in data['battle_log']), '手动战斗战报含我方技能')
    again = post('/api/v1/pve/battle/action', {'session_id': sid, 'action': 'attack'})
    check(again['success'] is False and '已经结束' in again['error'], '已结算的战斗不能再下令')

    body = post('/api/v1/pve/battle/start', {'stage_id': stage, 'mode': 'manual'})
    sid2 = body['data']['session_id']
    body = post('/api/v1/pve/battle/auto', {'session_id': sid2})
    check(body['success'] and body['data']['finished'], f"转托管后自动打完：{body['data']['result']}")

    body = post('/api/v1/pve/battle/start', {'stage_id': stage, 'mode': 'manual'})
    sid3 = body['data']['session_id']
    post('/api/v1/pve/battle/start', {'stage_id': stage, 'mode': 'manual'})
    old = post('/api/v1/pve/battle/action', {'session_id': sid3, 'action': 'attack'})
    check(old['success'] is False and '替代' in old['error'], '新开战斗后旧的作废')
    check(post('/api/v1/pve/battle/start', {'stage_id': stage, 'mode': 'x'})['success'] is False, '非法 mode 被拒')

    print('\n[接口：技能展示]')
    with app.app_context():
        uc = UserCard.query.filter_by(user_id=User.query.filter_by(username='skill_tester').first().id).first()
        uc.main_skill_level = 4
        db.session.commit()
        uc_id, card_name = uc.id, uc.card.name
    data = client.get(f'/api/v1/growth/card-stats/{uc_id}', headers=auth).get_json()['data']
    sk, nxt = data['skill'], data['skill_next']
    check(sk['level'] == 4 and abs(sk['multiplier'] - sk['base_multiplier'] * 1.3) < 1e-6,
          f"card-stats.skill 按 Lv4 换算：{sk['name']} ×{sk['multiplier']}")
    check(nxt['level'] == 5 and nxt['multiplier'] > sk['multiplier'], f"skill_next 预览 Lv5 ×{nxt['multiplier']}")
    cat = client.get('/api/v1/cards/catalog', headers=auth).get_json()['data']['cards']
    check(any(c['name'] == card_name and c['skill']['level'] == 1 for c in cat), f'卡牌图鉴含技能（{len(cat)} 张）')
    with app.app_context():
        enemy_names = {c.name for c in Card.query.filter_by(is_enemy=True)}
    check(enemy_names and not enemy_names & {c['name'] for c in cat}, '图鉴不含敌军')


def main():
    app = create_app()
    from init_enemy_cards import init_enemy_cards
    init_enemy_cards()

    test_skill_parse(app)
    test_order_and_cooldown()
    test_effects()
    test_group_attack()
    test_api(app)

    print()
    if failures:
        print(f'[失败] {len(failures)} 项未通过')
        sys.exit(1)
    print('[成功] 战斗技能与手动模式全部通过')


if __name__ == '__main__':
    main()
