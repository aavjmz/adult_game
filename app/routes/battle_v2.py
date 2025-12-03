"""
战斗路由 v2.0 - 集成增强版战斗引擎

使用方法:
1. 将此文件内容复制到 app/routes/battle.py
2. 或在 app/__init__.py 中注册这个新路由
"""

import random
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models import db, Card, UserCard, Battle
from app.battle_engine import BattleEngine

bp = Blueprint('battle_v2', __name__, url_prefix='/battle_v2')

@bp.route('/')
@login_required
def index():
    """战斗页面"""
    user_cards = UserCard.query.filter_by(user_id=current_user.id).all()
    return render_template('battle.html', user_cards=user_cards)

@bp.route('/start', methods=['POST'])
@login_required
def start():
    """开始战斗 - 使用增强版战斗引擎"""
    data = request.get_json()
    player_card_ids = data.get('card_ids', [])

    # 验证
    if not player_card_ids or len(player_card_ids) == 0:
        return jsonify({'error': '请至少选择一张卡牌'}), 400

    if len(player_card_ids) > 3:
        return jsonify({'error': '最多选择3张卡牌'}), 400

    # 获取玩家卡牌
    player_cards = []
    for card_id in player_card_ids:
        user_card = UserCard.query.filter_by(
            user_id=current_user.id,
            card_id=card_id
        ).first()

        if not user_card:
            return jsonify({'error': f'卡牌 {card_id} 不属于您'}), 400

        player_cards.append(user_card.card)

    # 生成敌方卡牌
    all_cards = Card.query.all()
    enemy_count = random.randint(1, 3)
    enemy_cards = random.sample(all_cards, min(enemy_count, len(all_cards)))

    # ===== 使用新战斗引擎 ⭐ =====
    battle_engine = BattleEngine(player_cards, enemy_cards)
    battle_result = battle_engine.execute_battle()

    # 计算奖励
    rewards_coins = 0
    rewards_tickets = 0

    if battle_result['is_victory']:
        # 根据敌人强度给予奖励
        total_enemy_power = sum(
            getattr(c, 'attack', 100) +
            getattr(c, 'defense', 100) +
            getattr(c, 'hp', 1000)
            for c in enemy_cards
        )
        rewards_coins = int(total_enemy_power / 10)
        rewards_tickets = random.randint(0, 2)

        current_user.coins += rewards_coins
        current_user.tickets += rewards_tickets

    # 记录战斗
    battle = Battle(
        user_id=current_user.id,
        player_card_ids=','.join(map(str, player_card_ids)),
        enemy_card_ids=','.join(map(str, [c.id for c in enemy_cards])),
        is_victory=battle_result['is_victory'],
        rewards_coins=rewards_coins,
        rewards_tickets=rewards_tickets
    )
    db.session.add(battle)
    db.session.commit()

    return jsonify({
        'success': True,
        'battle_log': battle_result['log'],
        'is_victory': battle_result['is_victory'],
        'rewards': {
            'coins': rewards_coins,
            'tickets': rewards_tickets
        },
        'current_resources': {
            'coins': current_user.coins,
            'tickets': current_user.tickets
        }
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
