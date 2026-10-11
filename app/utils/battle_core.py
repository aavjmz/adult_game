# -*- coding: utf-8 -*-
"""
战斗核心：可暂停、可序列化的回合制战斗

战斗状态是纯 dict（可 json.dumps 存库），因此同一套规则既能一次跑完（自动模式），
也能「推进到轮到我方武将出手就停下」，等玩家下令后再继续（手动模式）。

规则
- 每回合：所有存活单位按速度从高到低依次出手（同速时我方在前）
- 出手：普攻，或技能冷却完毕时放技能；被眩晕则跳过这次出手
- 技能冷却 N：开局需等到自己第 2 次出手；用后隔 N 次自己的出手才能再用
- 降防 / 降攻：持续目标自己的 2 次出手；眩晕：目标下次出手跳过
- 伤害 = max(1, 攻击×倍率 − 有效防御×0.5)，10% 暴击 ×1.5，±10% 浮动
- 一方全灭或超过回合上限（判负）即结束

事件（state['events']）沿用旧战报字段 turn / actor / action / target / damage / message，
另带 actor_id、side、skill、hits、heals、effects 供客户端精确回放。
"""
import random

from app.skills import ATK_DOWN_PCT, DEBUFF_TURNS, DEF_DOWN_PCT

MAX_ROUNDS = 50


# ============ 构建 ============

def make_unit(uid, side, name, stats, skill, **extra):
    """一个战斗单位。stats 需含 hp / attack / defense / speed；skill 为 skills.skill_profile()"""
    unit = {
        'id': uid,
        'side': side,                 # 'ally' / 'enemy'
        'name': name,
        'hp': int(stats['hp']),
        'max_hp': int(stats['hp']),
        'attack': int(stats['attack']),
        'defense': int(stats['defense']),
        'speed': int(stats['speed']),
        'alive': True,
        'skill': skill,
        'cd': 1,                      # 开局技能需等一次出手
        'stun': 0,
        'buffs': [],                  # [{'type': 'def_down'|'atk_down', 'value': 0.3, 'turns': 2}]
    }
    unit.update(extra)
    return unit


def new_state(allies, enemies, ai_strategy='balanced', max_rounds=MAX_ROUNDS):
    return {
        'round': 0,
        'max_rounds': max_rounds,
        'order': [],
        'cursor': 0,
        'units': {u['id']: u for u in allies + enemies},
        'ai_strategy': ai_strategy,
        'events': [],
        'stats': {'damage_dealt': 0, 'damage_taken': 0, 'deaths': 0},
        'awaiting': None,            # 手动模式下等待下令的我方单位 id
        'finished': False,
        'result': None,              # 'win' / 'lose'
    }


# ============ 查询 ============

def side_units(state, side, alive=True):
    return [u for u in state['units'].values() if u['side'] == side and (u['alive'] or not alive)]


def skill_ready(unit):
    return unit['alive'] and unit['cd'] <= 0


def awaiting_info(state):
    """手动模式下当前待命单位的可选行动，供客户端渲染"""
    uid = state.get('awaiting')
    if not uid:
        return None
    unit = state['units'][uid]
    return {
        'unit_id': uid,
        'name': unit['name'],
        'skill': {
            'name': unit['skill']['name'],
            'ready': skill_ready(unit),
            'cooldown_left': max(0, unit['cd']),
            'target': unit['skill']['target'],
            'description': unit['skill']['description'],
        },
        'targets': [u['id'] for u in side_units(state, 'enemy')],
    }


def _buff_value(unit, kind):
    return min(0.9, sum(b['value'] for b in unit['buffs'] if b['type'] == kind))


# ============ 推进 ============

def _check_end(state):
    if not side_units(state, 'enemy'):
        state['finished'], state['result'] = True, 'win'
    elif not side_units(state, 'ally'):
        state['finished'], state['result'] = True, 'lose'
    return state['finished']


def _next_actor(state):
    """取下一个出手单位 id；需要时开启新回合。战斗结束返回 None"""
    while True:
        if _check_end(state):
            return None
        if state['cursor'] >= len(state['order']):
            if state['round'] >= state['max_rounds']:
                state['finished'], state['result'] = True, 'lose'
                return None
            state['round'] += 1
            alive = [u for u in state['units'].values() if u['alive']]
            alive.sort(key=lambda u: (-u['speed'], 0 if u['side'] == 'ally' else 1, u['id']))
            state['order'] = [u['id'] for u in alive]
            state['cursor'] = 0
        uid = state['order'][state['cursor']]
        state['cursor'] += 1
        if state['units'][uid]['alive']:
            return uid


def _end_turn(unit):
    """单位出手（或被眩晕跳过）后：技能冷却 -1，自身减益持续 -1"""
    if unit['cd'] > 0:
        unit['cd'] -= 1
    for b in unit['buffs']:
        b['turns'] -= 1
    unit['buffs'] = [b for b in unit['buffs'] if b['turns'] > 0]


def run(state, manual=False):
    """推进战斗：自动模式跑到结束；手动模式停在下一个我方单位出手前

    Returns:
        list: 本次推进新产生的事件
    """
    start = len(state['events'])
    state['awaiting'] = None
    while not state['finished']:
        uid = _next_actor(state)
        if uid is None:
            break
        unit = state['units'][uid]

        if unit['stun'] > 0:
            unit['stun'] -= 1
            _emit(state, unit, 'stunned', message=f"{unit['name']} 被眩晕，无法行动")
            _end_turn(unit)
            continue

        if manual and unit['side'] == 'ally':
            # 停在这里等玩家下令；退回游标，act() 时由这个单位出手
            state['cursor'] -= 1
            state['awaiting'] = uid
            break

        action, target_id = auto_choice(state, unit)
        _perform(state, unit, action, target_id)
        _end_turn(unit)
    return state['events'][start:]


def act(state, action, target_id=None):
    """手动模式：待命单位执行玩家的指令，然后继续推进到下一个我方单位

    Returns:
        list: 本次产生的事件
    Raises:
        ValueError: 指令无效
    """
    uid = state.get('awaiting')
    if not uid or state['finished']:
        raise ValueError('当前没有等待下令的武将')
    unit = state['units'][uid]
    if action not in ('attack', 'skill'):
        raise ValueError('无效的指令')
    if action == 'skill' and not skill_ready(unit):
        raise ValueError(f"{unit['skill']['name']} 冷却中，还需 {unit['cd']} 次出手")
    if target_id is not None:
        target = state['units'].get(target_id)
        if not target or target['side'] != 'enemy' or not target['alive']:
            raise ValueError('目标无效')

    start = len(state['events'])
    state['cursor'] += 1          # 消费掉 run() 退回的那一格
    state['awaiting'] = None
    _perform(state, unit, action, target_id)
    _end_turn(unit)
    run(state, manual=True)
    return state['events'][start:]


# ============ 决策 ============

def auto_choice(state, unit):
    """自动出手：技能可用就放技能；我方集火血量比例最低的敌人，敌方按关卡 AI 策略选目标"""
    action = 'skill' if skill_ready(unit) else 'attack'
    foes = side_units(state, 'enemy' if unit['side'] == 'ally' else 'ally')
    if not foes:
        return action, None
    if unit['side'] == 'ally':
        target = min(foes, key=lambda u: (u['hp'] / u['max_hp'], u['id']))
    else:
        strategy = state.get('ai_strategy', 'balanced')
        if strategy == 'aggressive':
            target = min(foes, key=lambda u: (u['hp'], u['id']))
        elif strategy == 'defensive':
            target = max(foes, key=lambda u: (u['attack'], u['id']))
        else:
            target = random.choice(foes)
    return action, target['id']


# ============ 结算 ============

def _damage(attacker, target, multiplier=1.0, ignore_def=0.0):
    atk = attacker['attack'] * (1 - _buff_value(attacker, 'atk_down')) * multiplier
    defense = target['defense'] * (1 - _buff_value(target, 'def_down')) * (1 - ignore_def)
    base = max(1.0, atk - defense * 0.5)
    crit = random.random() < 0.1
    if crit:
        base *= 1.5
    return max(1, int(base * random.uniform(0.9, 1.1))), crit


def _apply_damage(state, attacker, target, amount):
    dealt = min(amount, target['hp'])
    target['hp'] -= dealt
    key = 'damage_dealt' if attacker['side'] == 'ally' else 'damage_taken'
    state['stats'][key] += amount
    if target['hp'] <= 0:
        target['hp'] = 0
        target['alive'] = False
        if target['side'] == 'ally':
            state['stats']['deaths'] += 1
        return True
    return False


def _heal(unit, amount):
    gained = min(int(amount), unit['max_hp'] - unit['hp'])
    unit['hp'] += max(0, gained)
    return max(0, gained)


def _perform(state, unit, action, target_id):
    foes = side_units(state, 'enemy' if unit['side'] == 'ally' else 'ally')
    if not foes:
        return
    skill = unit['skill'] if action == 'skill' else None
    fx = skill['effects'] if skill else {}

    if skill and skill['target'] == 'all':
        targets = foes
    else:
        chosen = state['units'].get(target_id) if target_id else None
        if not chosen or not chosen['alive'] or chosen['side'] == unit['side']:
            chosen = state['units'][auto_choice(state, unit)[1]]
        targets = [chosen]

    hits, heals, effects = [], [], []
    total = 0
    for t in targets:
        dmg, crit = _damage(unit, t, skill['multiplier'] if skill else 1.0, fx.get('ignore_def', 0.0))
        killed = _apply_damage(state, unit, t, dmg)
        executed = False
        if not killed and fx.get('execute') and t['hp'] / t['max_hp'] < fx['execute']:
            _apply_damage(state, unit, t, t['hp'])
            killed = executed = True
        total += dmg
        hits.append({'target_id': t['id'], 'target': t['name'], 'damage': dmg, 'crit': crit,
                     'killed': killed, 'executed': executed, 'hp': t['hp']})
        if killed:
            continue
        if fx.get('def_down'):
            t['buffs'].append({'type': 'def_down', 'value': DEF_DOWN_PCT, 'turns': DEBUFF_TURNS})
            effects.append({'target_id': t['id'], 'target': t['name'], 'type': 'def_down', 'value': DEF_DOWN_PCT})
        if fx.get('stun') and random.random() < fx['stun']:
            t['stun'] = 1
            effects.append({'target_id': t['id'], 'target': t['name'], 'type': 'stun'})

    if fx.get('atk_down_all'):
        for t in side_units(state, 'enemy' if unit['side'] == 'ally' else 'ally'):
            t['buffs'].append({'type': 'atk_down', 'value': ATK_DOWN_PCT, 'turns': DEBUFF_TURNS})
            effects.append({'target_id': t['id'], 'target': t['name'], 'type': 'atk_down', 'value': ATK_DOWN_PCT})
    if fx.get('lifesteal'):
        heals.append({'target_id': unit['id'], 'target': unit['name'], 'amount': _heal(unit, total * fx['lifesteal'])})
    if fx.get('self_heal'):
        heals.append({'target_id': unit['id'], 'target': unit['name'], 'amount': _heal(unit, unit['max_hp'] * fx['self_heal'])})
    if fx.get('team_heal'):
        for ally in side_units(state, unit['side']):
            heals.append({'target_id': ally['id'], 'target': ally['name'], 'amount': _heal(ally, ally['max_hp'] * fx['team_heal'])})
    heals = [h for h in heals if h['amount'] > 0]

    if skill:
        unit['cd'] = skill['cooldown'] + 1   # 出手结束时会 -1，正好隔 cooldown 次出手
    verb = f"施放【{skill['name']}】" if skill else '攻击'
    parts = [f"{h['target']} {'暴击 ' if h['crit'] else ''}-{h['damage']}" for h in hits]
    _emit(state, unit, 'skill' if skill else 'attack', hits=hits, heals=heals, effects=effects,
          skill=skill['name'] if skill else None, message=f"{unit['name']} {verb}：{'，'.join(parts)}")
    for h in hits:
        if h['killed']:
            fallen = state['units'][h['target_id']]
            word = '被斩杀' if h['executed'] else ('阵亡' if fallen['side'] == 'ally' else '被击败')
            _emit(state, fallen, 'death', message=f"{fallen['name']} {word}")


def _emit(state, unit, action, hits=None, heals=None, effects=None, skill=None, message=''):
    hits = hits or []
    first = hits[0] if hits else None
    state['events'].append({
        'turn': state['round'],
        'actor_id': unit['id'],
        'actor': unit['name'],
        'side': unit['side'],
        'action': action,                       # attack / skill / stunned / death
        'skill': skill,
        # 旧字段：单体时即该次命中，群攻时为第一个目标（Web 端旧战报沿用）
        'target': first['target'] if first else None,
        'damage': sum(h['damage'] for h in hits) if hits else None,
        'hits': hits,
        'heals': heals or [],
        'effects': effects or [],
        'message': message,
    })
