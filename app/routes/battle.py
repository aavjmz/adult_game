import random
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models import db, Card, UserCard, Battle

bp = Blueprint('battle', __name__, url_prefix='/battle')

@bp.route('/')
@login_required
def index():
    """战斗页面"""
    # 获取用户的卡牌
    user_cards = UserCard.query.filter_by(user_id=current_user.id).all()
    return render_template('battle.html', user_cards=user_cards)

@bp.route('/start', methods=['POST'])
@login_required
def start():
    """开始战斗"""
    data = request.get_json()
    player_card_ids = data.get('card_ids', [])

    if not player_card_ids or len(player_card_ids) == 0:
        return jsonify({'error': '请至少选择一张卡牌'}), 400

    if len(player_card_ids) > 3:
        return jsonify({'error': '最多选择3张卡牌'}), 400

    # 验证卡牌是否属于用户
    player_cards = []
    for card_id in player_card_ids:
        user_card = UserCard.query.filter_by(
            user_id=current_user.id,
            card_id=card_id
        ).first()

        if not user_card:
            return jsonify({'error': f'卡牌 {card_id} 不属于您'}), 400

        player_cards.append(user_card.card)

    # 生成敌方卡牌（随机选择）
    all_cards = Card.query.all()
    enemy_count = random.randint(1, 3)
    enemy_cards = random.sample(all_cards, min(enemy_count, len(all_cards)))

    # 执行战斗
    battle_result = execute_battle(player_cards, enemy_cards)

    # 计算奖励
    rewards_coins = 0
    rewards_tickets = 0

    if battle_result['is_victory']:
        # 根据敌人强度给予奖励
        total_enemy_power = sum(c.attack + c.defense + c.hp for c in enemy_cards)
        rewards_coins = int(total_enemy_power / 10)
        rewards_tickets = random.randint(0, 2)  # 随机获得0-2张票

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

def execute_battle(player_cards, enemy_cards):
    """执行战斗逻辑（简化版回合制）"""
    battle_log = []

    # 初始化战斗状态
    player_hp = {i: card.hp for i, card in enumerate(player_cards)}
    enemy_hp = {i: card.hp for i, card in enumerate(enemy_cards)}

    round_num = 1
    max_rounds = 20  # 最多20回合

    battle_log.append({
        'type': 'start',
        'message': f'战斗开始！你的队伍 vs 敌方队伍'
    })

    while round_num <= max_rounds:
        battle_log.append({
            'type': 'round',
            'round': round_num,
            'message': f'--- 第 {round_num} 回合 ---'
        })

        # 玩家回合
        for i, player_card in enumerate(player_cards):
            if player_hp[i] <= 0:
                continue

            # 随机选择一个存活的敌人攻击
            alive_enemies = [j for j, hp in enemy_hp.items() if hp > 0]
            if not alive_enemies:
                break

            target = random.choice(alive_enemies)
            enemy_card = enemy_cards[target]

            # 计算伤害（考虑防御）
            damage = max(player_card.attack - enemy_card.defense // 2, player_card.attack // 2)

            # 有20%概率触发技能
            if random.random() < 0.2:
                damage = int(damage * player_card.skill_damage_multiplier)
                battle_log.append({
                    'type': 'skill',
                    'attacker': player_card.name,
                    'skill': player_card.skill_name,
                    'target': enemy_card.name,
                    'damage': damage,
                    'message': f'{player_card.name} 使用了 {player_card.skill_name}！对 {enemy_card.name} 造成 {damage} 点伤害！'
                })
            else:
                battle_log.append({
                    'type': 'attack',
                    'attacker': player_card.name,
                    'target': enemy_card.name,
                    'damage': damage,
                    'message': f'{player_card.name} 攻击 {enemy_card.name}，造成 {damage} 点伤害'
                })

            enemy_hp[target] -= damage

            if enemy_hp[target] <= 0:
                battle_log.append({
                    'type': 'defeat',
                    'target': enemy_card.name,
                    'message': f'{enemy_card.name} 被击败了！'
                })

        # 检查敌方是否全灭
        if all(hp <= 0 for hp in enemy_hp.values()):
            battle_log.append({
                'type': 'victory',
                'message': '胜利！你击败了所有敌人！'
            })
            return {'is_victory': True, 'log': battle_log}

        # 敌方回合
        for i, enemy_card in enumerate(enemy_cards):
            if enemy_hp[i] <= 0:
                continue

            # 随机选择一个存活的玩家卡牌攻击
            alive_players = [j for j, hp in player_hp.items() if hp > 0]
            if not alive_players:
                break

            target = random.choice(alive_players)
            player_card = player_cards[target]

            damage = max(enemy_card.attack - player_card.defense // 2, enemy_card.attack // 2)

            if random.random() < 0.2:
                damage = int(damage * enemy_card.skill_damage_multiplier)
                battle_log.append({
                    'type': 'skill',
                    'attacker': enemy_card.name,
                    'skill': enemy_card.skill_name,
                    'target': player_card.name,
                    'damage': damage,
                    'message': f'{enemy_card.name} 使用了 {enemy_card.skill_name}！对 {player_card.name} 造成 {damage} 点伤害！'
                })
            else:
                battle_log.append({
                    'type': 'attack',
                    'attacker': enemy_card.name,
                    'target': player_card.name,
                    'damage': damage,
                    'message': f'{enemy_card.name} 攻击 {player_card.name}，造成 {damage} 点伤害'
                })

            player_hp[target] -= damage

            if player_hp[target] <= 0:
                battle_log.append({
                    'type': 'defeat',
                    'target': player_card.name,
                    'message': f'{player_card.name} 被击败了！'
                })

        # 检查玩家是否全灭
        if all(hp <= 0 for hp in player_hp.values()):
            battle_log.append({
                'type': 'defeat',
                'message': '战败！你的队伍被击败了...'
            })
            return {'is_victory': False, 'log': battle_log}

        round_num += 1

    # 超过最大回合数，判定为平局（算作失败）
    battle_log.append({
        'type': 'timeout',
        'message': '战斗超时，判定为平局'
    })
    return {'is_victory': False, 'log': battle_log}

@bp.route('/history')
@login_required
def history():
    """战斗历史"""
    battles = Battle.query.filter_by(user_id=current_user.id)\
        .order_by(Battle.created_at.desc())\
        .limit(50)\
        .all()

    return render_template('battle_history.html', battles=battles)
