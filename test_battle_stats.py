#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""出战属性测试：养成是否真正作用到 PVE 战斗

逐项验证星级、觉醒、突破、装备（含强化）都会提高出战属性，且战斗单位、
/api/v1/growth/card-stats 的 battle_stats 与 player_battle_stats 一致。
用临时 SQLite 库运行，不碰 data/game.db：
    python test_battle_stats.py
"""
import os
import sys
import tempfile

os.environ['DB_PATH'] = os.path.join(tempfile.mkdtemp(), 'test_battle_stats.db')

from app import create_app, db  # noqa: E402
from app.models import Equipment, EquipmentTemplate, Stage, User, UserCard  # noqa: E402
from app.utils.pve_battle import PVEBattle, level_stat, player_battle_stats  # noqa: E402
from test_fixtures import ensure_equipment_templates, ensure_test_user  # noqa: E402

failures = []


def check(cond, label):
    print(f"  [{'OK' if cond else 'FAIL'}] {label}")
    if not cond:
        failures.append(label)


def main():
    app = create_app()
    client = app.test_client()
    res = client.post('/api/v1/auth/register', json={
        'username': 'stats_tester', 'email': 'stats@test.local', 'password': 'Passw0rd!'})
    auth = {'Authorization': f"Bearer {res.get_json()['data']['token']}"}

    with app.app_context():
        ensure_equipment_templates()
        user = ensure_test_user('stats_tester', card_count=1)
        uc = UserCard.query.filter_by(user_id=user.id).first()
        uc.level = 10
        db.session.commit()
        card = uc.card

        print('\n[基线：只有等级]')
        base = player_battle_stats(uc)
        check(base['attack'] == level_stat(card.attack, 10), f"攻击 = 等级公式 {base['attack']}")
        check(base['hp'] == level_stat(card.hp, 10) and base['speed'] == card.speed, '生命、速度与原战斗公式一致')

        print('\n[逐项养成]')
        uc.star_level = 3
        s3 = player_battle_stats(uc)
        check(s3['attack'] == int(base['attack'] * 1.35), f"★3 攻击 ×1.35 → {s3['attack']}")

        uc.awaken_level = 1
        aw = player_battle_stats(uc)
        check(aw['attack'] == int(s3['attack'] * 1.3), f"觉醒 ×1.3 → {aw['attack']}")

        uc.breakthrough_level = 1
        bt = player_battle_stats(uc)
        check(bt['defense'] == int(aw['defense'] * 1.2), f"突破一次 防御 ×1.2 → {bt['defense']}")
        db.session.commit()

        weapon = EquipmentTemplate.query.filter_by(type='weapon', quality='common').first()
        eq = Equipment(user_id=user.id, template_id=weapon.id, name=weapon.name, type='weapon',
                       quality=weapon.quality, owner_card_id=uc.id, enhance_level=0)
        db.session.add(eq)
        db.session.commit()
        worn = player_battle_stats(uc)
        expect = int(bt['attack'] * (1 + weapon.base_attack_pct))
        check(worn['attack'] == expect, f"穿 {weapon.name}（攻击 +{weapon.base_attack_pct:.0%}）→ {worn['attack']}")

        eq.enhance_level = 10
        db.session.commit()
        enhanced = player_battle_stats(uc)
        check(enhanced['attack'] > worn['attack'], f"强化 +10 → {enhanced['attack']}")

        print('\n[战斗与接口一致]')
        stage = Stage.query.filter_by(stage_type='main', stage_number=1).first()
        battle = PVEBattle(user, stage, [uc])
        unit = battle.user_team_units[0]
        check({k: unit[k] for k in ('hp', 'attack', 'defense', 'speed')} == enhanced, '战斗单位属性 = player_battle_stats')
        check(unit['max_hp'] == enhanced['hp'], '满血 = 出战生命')
        uc_id = uc.id

    data = client.get(f'/api/v1/growth/card-stats/{uc_id}', headers=auth).get_json()['data']
    check(data['battle_stats'] == enhanced, f"card-stats.battle_stats 一致 {data['battle_stats']}")

    print()
    if failures:
        print(f'[失败] {len(failures)} 项未通过')
        sys.exit(1)
    print('[成功] 养成已全部作用到出战属性')


if __name__ == '__main__':
    main()
