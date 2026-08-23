"""
PVP战斗路由 - 使用与PVE相同的炉石风格手动出牌UI
"""

import random
import json
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models import db, Card, UserCard, Battle

bp = Blueprint('battle', __name__, url_prefix='/battle')


@bp.route('/')
@login_required
def index():
    """PVP战斗页面 - 使用统一战斗UI"""
    return render_template('pve/battle_ui_unified.html',
                           stage_id=None,
                           battle_mode='pvp')


@bp.route('/opponent-deck', methods=['GET'])
@login_required
def get_opponent_deck():
    """
    生成PVP对手牌组

    从所有卡牌中随机选取，构建一个与用户实力相当的AI对手牌组。
    返回格式与 /api/pve/user-deck 一致，便于统一战斗UI复用。
    """
    JOB_CLASS_MAP = {
        '武将': 'INFANTRY', '谋士': 'MAGE', '弓将': 'ARCHER',
        '骑将': 'CAVALRY', '步将': 'SHIELD'
    }
    FACTION_MAP = {'魏': 'WEI', '蜀': 'SHU', '吴': 'WU', '群': 'QUN'}

    # 获取所有可用卡牌
    all_cards = Card.query.all()
    if not all_cards:
        return jsonify({'success': False, 'message': '没有可用的卡牌数据'})

    # 随机选取对手势力（决定对手的卡牌风格）
    opponent_factions = ['魏', '蜀', '吴', '群']
    main_faction = random.choice(opponent_factions)

    # 优先选本势力卡牌，不够则补充其他卡牌
    faction_cards = [c for c in all_cards if getattr(c, 'faction', '群') == main_faction]
    other_cards = [c for c in all_cards if getattr(c, 'faction', '群') != main_faction]

    # 选6-10张卡牌作为对手的卡牌池
    pool_size = min(random.randint(6, 10), len(all_cards))
    if len(faction_cards) >= pool_size:
        selected = random.sample(faction_cards, pool_size)
    else:
        selected = faction_cards[:]
        remaining = pool_size - len(selected)
        if other_cards and remaining > 0:
            selected += random.sample(other_cards, min(remaining, len(other_cards)))

    # 根据用户战力调整对手等级
    user_cards = UserCard.query.filter_by(user_id=current_user.id).all()
    avg_user_level = 1
    if user_cards:
        avg_user_level = max(1, sum(uc.level for uc in user_cards) // len(user_cards))

    # 对手等级在用户平均等级附近浮动
    opponent_level = max(1, avg_user_level + random.randint(-3, 3))

    deck = []
    for card in selected:
        unit_type = JOB_CLASS_MAP.get(getattr(card, 'job_class', '武将'), 'INFANTRY')
        faction = FACTION_MAP.get(getattr(card, 'faction', '群'), 'QUN')

        # 根据稀有度估算费用
        base_cost = {'N': 1, 'R': 2, 'SR': 3, 'SSR': 4, 'UR': 6}
        cost = base_cost.get(card.rarity, 2)
        if opponent_level >= 30:
            cost = min(cost + 1, 8)

        # 缩放属性到卡牌游戏数值（1-10范围）
        level_scale = 1 + (opponent_level - 1) * 0.03
        atk = max(1, min(10, int(card.attack * level_scale / 40)))
        hp = max(1, min(12, int(card.hp * level_scale / 250)))

        keywords = []
        desc_parts = []
        if unit_type == 'SHIELD':
            keywords.append('taunt')
            desc_parts.append('护卫')
        elif unit_type == 'CAVALRY':
            keywords.append('charge')
            desc_parts.append('突击')

        deck.append({
            'card_id': card.id,
            'name': card.name,
            'faction': faction,
            'rarity': card.rarity,
            'unitType': unit_type,
            'cost': cost,
            'attack': atk,
            'hp': hp,
            'keywords': keywords,
            'desc': ' '.join(desc_parts),
            'level': opponent_level,
            'star_level': random.randint(1, 3),
        })

    return jsonify({
        'success': True,
        'deck': deck,
        'opponent_faction': FACTION_MAP.get(main_faction, 'QUN'),
        'opponent_name': _get_faction_leader(main_faction)
    })


def _get_faction_leader(faction):
    """获取势力代表人物名称"""
    leaders = {
        '魏': '曹操',
        '蜀': '刘备',
        '吴': '孙权',
        '群': '吕布'
    }
    return leaders.get(faction, '对手')


@bp.route('/settle', methods=['POST'])
@login_required
def settle_pvp_battle():
    """
    PVP战斗结算

    前端卡牌对战结束后提交结果：
    POST: { result: 'win'/'lose', turns: N }
    """
    data = request.get_json()
    result = data.get('result')
    turns = data.get('turns', 0)

    if result not in ('win', 'lose'):
        return jsonify({'success': False, 'message': '参数错误'}), 400

    rewards = {}

    if result == 'win':
        # PVP胜利奖励
        coins = 200 + turns * 10
        tickets = random.randint(0, 2)
        gems = random.randint(0, 1)

        rewards = {
            'coins': coins,
            'tickets': tickets,
            'gems': gems,
        }

        current_user.coins += coins
        current_user.tickets += tickets
        current_user.gems += gems

    # 记录战斗
    battle = Battle(
        user_id=current_user.id,
        player_card_ids='pvp',
        enemy_card_ids='pvp_ai',
        is_victory=(result == 'win'),
        rewards_coins=rewards.get('coins', 0),
        rewards_tickets=rewards.get('tickets', 0)
    )
    db.session.add(battle)
    db.session.commit()

    return jsonify({
        'success': True,
        'result': result,
        'rewards': rewards
    })


@bp.route('/history')
@login_required
def history():
    """战斗历史"""
    battles = Battle.query.filter_by(user_id=current_user.id)\
        .order_by(Battle.created_at.desc())\
        .limit(50)\
        .all()

    return render_template('battle_history.html', battles=battles)
