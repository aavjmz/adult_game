import random
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models import db, Card, UserCard, GachaRecord
from config import Config

bp = Blueprint('gacha', __name__, url_prefix='/gacha')

@bp.route('/')
@login_required
def index():
    """抽卡页面"""
    return render_template('gacha.html',
                         tickets=current_user.tickets,
                         gacha_config=Config.GACHA_CONFIG,
                         rarities=Config.CARD_RARITIES)

@bp.route('/pull', methods=['POST'])
@login_required
def pull():
    """执行抽卡"""
    data = request.get_json()
    pull_type = data.get('type', 'single')  # single 或 multi

    if pull_type == 'single':
        cost = Config.GACHA_CONFIG['single_cost']
        count = 1
    elif pull_type == 'multi':
        cost = Config.GACHA_CONFIG['multi_cost']
        count = 10
    else:
        return jsonify({'error': '无效的抽卡类型'}), 400

    # 检查票券是否足够
    if current_user.tickets < cost:
        return jsonify({'error': f'票券不足！需要 {cost} 张，当前只有 {current_user.tickets} 张'}), 400

    # 扣除票券
    current_user.tickets -= cost

    # 执行抽卡
    pulled_cards = []
    for i in range(count):
        card = perform_single_gacha(current_user, is_multi=(pull_type == 'multi'), position=i+1, total=count)
        pulled_cards.append({
            'id': card.id,
            'name': card.name,
            'rarity': card.rarity,
            'attack': card.attack,
            'defense': card.defense,
            'hp': card.hp,
            'is_golden': card.is_golden,
            'skill_name': card.skill_name,
            'skill_description': card.skill_description,
            'is_new': True  # 可以进一步检查是否为新卡
        })

        # 记录抽卡历史
        gacha_record = GachaRecord(
            user_id=current_user.id,
            card_id=card.id,
            is_multi_pull=(pull_type == 'multi')
        )
        db.session.add(gacha_record)

        # 添加到用户收藏
        user_card = UserCard(
            user_id=current_user.id,
            card_id=card.id
        )
        db.session.add(user_card)

    db.session.commit()

    return jsonify({
        'success': True,
        'cards': pulled_cards,
        'remaining_tickets': current_user.tickets,
        'sr_pity': current_user.sr_pity_count,
        'ssr_pity': current_user.ssr_pity_count
    })

def perform_single_gacha(user, is_multi=False, position=1, total=1):
    """执行单次抽卡逻辑"""
    # 获取所有卡牌
    all_cards = Card.query.all()
    if not all_cards:
        raise ValueError("卡池为空")

    # 检查保底
    guaranteed_rarity = None

    # SSR保底（90抽）
    if user.ssr_pity_count >= Config.GACHA_CONFIG['ssr_guarantee'] - 1:
        guaranteed_rarity = 'SSR'
        user.ssr_pity_count = 0
        user.sr_pity_count = 0
    # SR保底（10抽）
    elif user.sr_pity_count >= Config.GACHA_CONFIG['sr_guarantee'] - 1:
        guaranteed_rarity = 'SR'
        user.sr_pity_count = 0
    # 十连保底：第10抽必出SR+
    elif is_multi and position == total:
        if user.sr_pity_count >= Config.GACHA_CONFIG['sr_guarantee'] - 1:
            guaranteed_rarity = 'SR'
            user.sr_pity_count = 0

    # 根据概率或保底选择卡牌
    if guaranteed_rarity:
        # 保底：从指定稀有度或更高中随机
        if guaranteed_rarity == 'SSR':
            eligible_rarities = ['SSR', 'UR']
        elif guaranteed_rarity == 'SR':
            eligible_rarities = ['SR', 'SSR', 'UR']
        else:
            eligible_rarities = [guaranteed_rarity]

        eligible_cards = [c for c in all_cards if c.rarity in eligible_rarities]
        if not eligible_cards:
            # 如果没有符合条件的卡，使用所有卡
            eligible_cards = all_cards

        card = random.choice(eligible_cards)
    else:
        # 正常概率抽取
        card = weighted_random_card(all_cards)

        # 更新保底计数
        user.ssr_pity_count += 1
        if card.rarity in ['SR', 'SSR', 'UR']:
            user.sr_pity_count = 0
        else:
            user.sr_pity_count += 1

        if card.rarity in ['SSR', 'UR']:
            user.ssr_pity_count = 0

    return card

def weighted_random_card(cards):
    """根据稀有度概率权重随机选择卡牌"""
    rarities = Config.CARD_RARITIES

    # 创建稀有度池
    rarity_pool = []
    for rarity, config in rarities.items():
        rarity_pool.extend([rarity] * int(config['probability'] * 100))

    # 随机选择稀有度
    selected_rarity = random.choice(rarity_pool)

    # 从该稀有度中随机选择卡牌
    eligible_cards = [c for c in cards if c.rarity == selected_rarity]

    if not eligible_cards:
        # 如果该稀有度没有卡，随机选择一张
        return random.choice(cards)

    return random.choice(eligible_cards)

@bp.route('/history')
@login_required
def history():
    """抽卡历史"""
    records = GachaRecord.query.filter_by(user_id=current_user.id)\
        .order_by(GachaRecord.created_at.desc())\
        .limit(100)\
        .all()

    return render_template('gacha_history.html', records=records)

@bp.route('/api/stats')
@login_required
def api_stats():
    """API: 获取抽卡统计"""
    total_pulls = GachaRecord.query.filter_by(user_id=current_user.id).count()

    rarity_counts = {}
    for rarity in Config.CARD_RARITIES.keys():
        count = db.session.query(GachaRecord).join(Card).filter(
            GachaRecord.user_id == current_user.id,
            Card.rarity == rarity
        ).count()
        rarity_counts[rarity] = count

    return jsonify({
        'total_pulls': total_pulls,
        'rarity_counts': rarity_counts,
        'sr_pity': current_user.sr_pity_count,
        'ssr_pity': current_user.ssr_pity_count,
        'current_tickets': current_user.tickets
    })
