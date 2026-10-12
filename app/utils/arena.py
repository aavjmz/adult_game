# -*- coding: utf-8 -*-
"""
军演：异步 PVP

- 对手：积分相近、已布阵的真人（读其最新编伍，对方不必在线），不足时以电脑阵容补齐
- 战斗：双方阵容交给 battle_core 在服务端一次打完（与征伐同一套规则）
- 积分：Elo，越级挑战赢得多；真人守方按一半得失；名次按积分现排
- 演券：每日 DAILY_TICKETS 张，北京时间零点重置

数值见 app/arena_data.py。
"""
import json
import random

from app.arena_data import (
    DAILY_TICKETS, DEFENDER_FACTOR, ELO_K, FOES_PER_BATCH, LOG_LIMIT, MAX_PLAYER_FOES,
    NPC_BASE_POWER, NPC_MAX_LEVEL, NPC_NAMES, NPC_POWER_FACTORS, START_SCORE, TIER_REWARDS, TIERS, WIN_REWARDS, tier_of,
)
from app.models import db, ArenaPlayer, ArenaRecord, Card, User, UserFormation
from app.orders_data import ACT_ARENA, game_today
from app.rewards import grant
from app.skills import skill_profile
from app.utils import battle_core, orders
from app.utils.formation import formation_cards
from app.utils.pve_battle import level_stat, player_battle_stats


# ============ 战力与单位 ============

def unit_power(stats):
    """单员战力：攻×2 + 防 + 血/5（第一关敌军约 1,000，与关卡推荐战力同一量级）"""
    return int(stats['attack'] * 2 + stats['defense'] + stats['hp'] / 5)


def _player_units(user_id, side):
    """真人阵容 → battle_core 单位（含全部养成）"""
    units = []
    for i, uc in enumerate(formation_cards(user_id)):
        stats = player_battle_stats(uc)
        units.append(battle_core.make_unit(
            f'{side[0]}{i}', side, uc.card.name, stats, skill_profile(uc.card, uc.main_skill_level or 1),
            level=uc.level, card_id=uc.card_id, rarity=uc.card.rarity, image_url=uc.card.image_url))
    return units


def _npc_stats(card, level):
    return {'hp': level_stat(card.hp, level), 'attack': level_stat(card.attack, level),
            'defense': level_stat(card.defense, level), 'speed': card.speed or 50}


def _npc_units(spec, side):
    cards = {c.id: c for c in Card.query.filter(Card.id.in_([u['card_id'] for u in spec['units']])).all()}
    units = []
    for i, u in enumerate(spec['units']):
        card = cards.get(u['card_id'])
        if card is None:
            continue
        units.append(battle_core.make_unit(
            f'{side[0]}{i}', side, card.name, _npc_stats(card, u['level']), skill_profile(card, 1),
            level=u['level'], card_id=card.id, rarity=card.rarity, image_url=card.image_url))
    return units


def _unit_payload(unit):
    """战斗单位快照，字段同征伐出征返回的 allies / enemies"""
    skill = unit['skill']
    return {
        'id': unit['id'], 'name': unit['name'], 'level': unit.get('level', 1),
        'max_hp': unit['max_hp'], 'attack': unit['attack'], 'defense': unit['defense'], 'speed': unit['speed'],
        'rarity': unit.get('rarity'), 'image_url': unit.get('image_url'),
        'skill': {k: skill[k] for k in ('name', 'description', 'multiplier', 'cooldown', 'target', 'level')},
    }


def _team_power(units):
    return sum(unit_power(u) for u in units)


# ============ 档案 ============

def get_player(user_id):
    """取军演档案，没有就建；演券跨天重置（只改 session）"""
    player = db.session.get(ArenaPlayer, user_id)
    if player is None:
        player = ArenaPlayer(user_id=user_id, score=START_SCORE, wins=0, losses=0, tickets_used=0, foes='[]')
        db.session.add(player)
        db.session.flush()
    today = game_today()
    if player.tickets_day != today:
        player.tickets_day = today
        player.tickets_used = 0
    return player


def rank_of(player):
    return ArenaPlayer.query.filter(ArenaPlayer.score > player.score).count() + 1


def _touch_best_rank(player):
    rank = rank_of(player)
    if player.best_rank is None or rank < player.best_rank:
        player.best_rank = rank
    return rank


# ============ 对手 ============

def _slots(row):
    try:
        return json.loads(row.slots or '[]')
    except (TypeError, ValueError):
        return []


def _player_candidates(user_id, my_score):
    """已布阵的其他真人，按积分接近程度排序"""
    rows = UserFormation.query.filter(UserFormation.user_id != user_id).all()
    ids = [r.user_id for r in rows if any(s is not None for s in _slots(r))]
    if not ids:
        return []
    scores = {p.user_id: p.score for p in ArenaPlayer.query.filter(ArenaPlayer.user_id.in_(ids)).all()}
    return sorted(ids, key=lambda uid: abs(scores.get(uid, START_SCORE) - my_score))


def _npc_spec(name, target_power, size, my_score, rng):
    """电脑阵容：随机抽 size 员武将，按目标战力反推统一等级

    战力随等级线性增长（level_stat：每级 +10%），由 1 级战力 P1 可直接解出等级。
    """
    pool = Card.query.filter(db.or_(Card.is_enemy.is_(False), Card.is_enemy.is_(None))).all()
    picks = rng.sample(pool, min(len(pool), size))
    base = sum(unit_power(_npc_stats(c, 1)) for c in picks) or 1
    level = round(1 + (target_power / base - 1) / 0.1)
    level = max(1, min(NPC_MAX_LEVEL, level))
    return {
        'kind': 'npc', 'name': name,
        'score': max(0, my_score + rng.randint(-120, 160)),
        'units': [{'card_id': c.id, 'level': level} for c in picks],
    }


def refresh_foes(user, player, rng=None):
    """换一批对手：积分最接近的真人里随机挑至多 MAX_PLAYER_FOES 名，余下用电脑补齐"""
    rng = rng or random.Random()
    near = _player_candidates(user.id, player.score)[:MAX_PLAYER_FOES * 3]
    real = rng.sample(near, min(MAX_PLAYER_FOES, len(near)))
    foes = [{'kind': 'player', 'user_id': uid} for uid in real]

    # 电脑对手人数同我军，战力按我军战力的梯度抽（由弱到强排）；未布阵时按 3 员、新手战力
    mine = _player_units(user.id, 'ally')
    my_power = _team_power(mine) or NPC_BASE_POWER
    size = len(mine) or 3
    names = rng.sample(NPC_NAMES, FOES_PER_BATCH)
    factors = sorted(rng.sample(NPC_POWER_FACTORS, FOES_PER_BATCH - len(foes)))
    for name, factor in zip(names, factors):
        foes.append(_npc_spec(name, my_power * factor, size, player.score, rng))

    for f in foes:
        f['fought'] = False
    player.foes = json.dumps(foes, ensure_ascii=False)
    return foes


def _foe_view(foe, my_power):
    """对手卡片：军号、主将、积分、战力、胜算（按战力估算）"""
    if foe['kind'] == 'player':
        user = db.session.get(User, foe['user_id'])
        units = _player_units(foe['user_id'], 'enemy') if user else []
        arena = db.session.get(ArenaPlayer, foe['user_id'])
        name = user.username if user else '已离营'
        score = arena.score if arena else START_SCORE
    else:
        units = _npc_units(foe, 'enemy')
        name, score = foe['name'], foe['score']
    power = _team_power(units)
    odds = round(my_power / (my_power + power) * 100) if my_power + power else 0
    return {
        'kind': foe['kind'], 'name': name, 'lead': units[0]['name'] if units else '—',
        'score': score, 'tier': tier_of(score), 'power': power,
        'odds': max(5, min(95, odds)), 'fought': foe.get('fought', False), 'available': bool(units),
    }


# ============ 页面数据 ============

def _logs(user_id):
    rows = ArenaRecord.query.filter(db.or_(ArenaRecord.attacker_id == user_id, ArenaRecord.defender_id == user_id))\
        .order_by(ArenaRecord.created_at.desc(), ArenaRecord.id.desc()).limit(LOG_LIMIT).all()
    logs = []
    for r in rows:
        attack = r.attacker_id == user_id
        logs.append({
            'defense': not attack,
            'foe': r.defender_name if attack else r.attacker_name,
            'win': r.win if attack else not r.win,
            'delta': r.attacker_delta if attack else r.defender_delta,
            'created_at': r.created_at.isoformat() + 'Z' if r.created_at else None,
        })
    return logs


def arena_state(user):
    """军演页全部数据；首次进入建档并发第一批对手"""
    player = get_player(user.id)
    foes = json.loads(player.foes or '[]')
    if not foes:
        foes = refresh_foes(user, player)
    rank = _touch_best_rank(player)
    db.session.commit()

    my_power = _team_power(_player_units(user.id, 'ally'))
    today = game_today()
    attacks = ArenaRecord.query.filter_by(attacker_id=user.id).order_by(
        ArenaRecord.created_at.desc(), ArenaRecord.id.desc()).limit(50).all()
    streak = 0
    for r in attacks:
        if not r.win:
            break
        streak += 1
    today_rows = [r for r in attacks if r.day == today]
    tier = tier_of(player.score)

    return {
        'score': player.score, 'rank': rank, 'best_rank': player.best_rank, 'tier': tier,
        'wins': player.wins, 'losses': player.losses,
        'today': {'wins': sum(1 for r in today_rows if r.win), 'losses': sum(1 for r in today_rows if not r.win)},
        'streak': streak,
        'tickets': {'left': max(0, DAILY_TICKETS - player.tickets_used), 'max': DAILY_TICKETS},
        'power': my_power,
        'foes': [_foe_view(f, my_power) for f in foes],
        'logs': _logs(user.id),
        'tier_reward': {'tier': tier, 'rewards': TIER_REWARDS[tier], 'claimed': player.reward_day == today},
        'tiers': [{'name': name, 'min_score': floor} for floor, name in TIERS],
        'win_rewards': WIN_REWARDS,
    }


# ============ 挑战 ============

def _elo_delta(my_score, foe_score, win):
    expected = 1 / (1 + 10 ** ((foe_score - my_score) / 400))
    if win:
        return max(1, round(ELO_K * (1 - expected)))
    return -max(1, round(ELO_K * expected))


def fight(user, index):
    """挑战本批第 index 名对手。Returns: (结果 dict, 错误信息或 None)"""
    player = get_player(user.id)
    foes = json.loads(player.foes or '[]')
    if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(foes):
        return None, '对手不存在'
    foe = foes[index]
    if foe.get('fought'):
        return None, '此人本批已演，换一批再战'
    if player.tickets_used >= DAILY_TICKETS:
        return None, '演券已尽，明日零点再来'

    allies = _player_units(user.id, 'ally')
    if not allies:
        return None, '请先在编伍中安排出战武将'

    defender = None
    if foe['kind'] == 'player':
        defender = db.session.get(User, foe['user_id'])
        enemies = _player_units(foe['user_id'], 'enemy') if defender else []
        foe_name = defender.username if defender else '已离营'
        foe_arena = get_player(defender.id) if defender else None
        foe_score = foe_arena.score if foe_arena else START_SCORE
    else:
        enemies = _npc_units(foe, 'enemy')
        foe_name, foe_arena, foe_score = foe['name'], None, foe['score']
    if not enemies:
        return None, '对手已撤阵，请换一批'

    # 开战前的阵容快照，客户端回放用（战斗过程会就地扣 hp）
    lineup = {'allies': [_unit_payload(u) for u in allies], 'enemies': [_unit_payload(u) for u in enemies]}
    state = battle_core.new_state(allies, enemies)
    battle_core.run(state, manual=False)
    win = state['result'] == 'win'

    delta = _elo_delta(player.score, foe_score, win)
    player.score = max(0, player.score + delta)
    player.tickets_used += 1
    if win:
        player.wins += 1
        grant(user, WIN_REWARDS)
    else:
        player.losses += 1

    defender_delta = 0
    if foe_arena is not None:
        defender_delta = -round(delta * DEFENDER_FACTOR)
        foe_arena.score = max(0, foe_arena.score + defender_delta)
    elif foe['kind'] == 'npc':
        # 电脑对手的积分随战果变化，下次进页面看到的是新数
        foe['score'] = max(0, foe_score - delta)

    foe['fought'] = True
    player.foes = json.dumps(foes, ensure_ascii=False)
    db.session.add(ArenaRecord(
        attacker_id=user.id, defender_id=defender.id if defender else None,
        attacker_name=user.username, defender_name=foe_name, win=win,
        attacker_delta=delta, defender_delta=defender_delta, day=game_today()))
    orders.record(user.id, ACT_ARENA)
    rank = _touch_best_rank(player)
    db.session.commit()

    return {
        'win': win, 'delta': delta, 'score': player.score, 'rank': rank, 'foe': foe_name,
        'rewards': WIN_REWARDS if win else [], 'rounds': state['round'],
        'damage_dealt': state['stats']['damage_dealt'], 'damage_taken': state['stats']['damage_taken'],
        'deaths': state['stats']['deaths'],
        'battle_log': state['events'], **lineup,
    }, None


def claim_tier_reward(user):
    """领取今日段位之赏。Returns: (奖励列表, 错误信息或 None)"""
    player = get_player(user.id)
    today = game_today()
    if player.reward_day == today:
        return None, '今日已领段位之赏'
    rewards = TIER_REWARDS[tier_of(player.score)]
    # 条件更新占住今天，并发重复领取只有一次生效
    won = ArenaPlayer.query.filter(
        ArenaPlayer.user_id == user.id,
        db.or_(ArenaPlayer.reward_day.is_(None), ArenaPlayer.reward_day != today),
    ).update({'reward_day': today}, synchronize_session=False)
    if not won:
        db.session.rollback()
        return None, '今日已领段位之赏'
    player.reward_day = today  # 与库里一致，后续读 state 不会看到旧值
    grant(user, rewards)
    db.session.commit()
    return rewards, None
