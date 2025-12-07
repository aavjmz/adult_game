"""
成长系统路由
包含升级、升星、技能升级、觉醒、装备等功能
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import db, UserCard, User, Card, UserItem, Equipment, EquipmentStat
from app.growth_utils import (
    calc_exp_required, calc_final_stats, get_star_up_requirements,
    get_skill_upgrade_cost, get_item_exp_value, get_card_sacrifice_exp,
    get_breakthrough_requirements, get_max_level
)

bp = Blueprint('growth', __name__, url_prefix='/growth')


@bp.route('/level-up', methods=['POST'])
@login_required
def level_up_card():
    """升级卡牌"""
    data = request.json
    user_card_id = data.get('user_card_id')
    exp_items = data.get('exp_items', [])  # [{item_type, item_subtype, quantity}]

    # 验证卡牌
    user_card = UserCard.query.get(user_card_id)
    if not user_card or user_card.user_id != current_user.id:
        return jsonify({'error': '卡牌不存在'}), 404

    # 获取等级上限
    max_level = get_max_level(user_card.breakthrough_level)
    if user_card.level >= max_level:
        return jsonify({'error': f'已达当前等级上限Lv.{max_level}'}), 400

    # 计算总经验
    total_exp = 0
    for item_info in exp_items:
        item_type = item_info.get('item_type')
        item_subtype = item_info.get('item_subtype')
        quantity = item_info.get('quantity', 1)

        # 检查用户是否拥有该道具
        user_item = UserItem.query.filter_by(
            user_id=current_user.id,
            item_type=item_type,
            item_subtype=item_subtype
        ).first()

        if not user_item or user_item.quantity < quantity:
            return jsonify({'error': f'道具 {item_type}:{item_subtype} 数量不足'}), 400

        # 消耗道具
        user_item.quantity -= quantity

        # 计算经验值
        exp_value = get_item_exp_value(item_type, item_subtype)
        total_exp += exp_value * quantity

    # 添加经验并升级
    user_card.exp += total_exp
    levels_gained = 0

    while user_card.exp >= calc_exp_required(user_card.level):
        if user_card.level >= max_level:
            # 达到等级上限，保留多余经验
            break

        user_card.exp -= calc_exp_required(user_card.level)
        user_card.level += 1
        levels_gained += 1

    db.session.commit()

    return jsonify({
        'success': True,
        'new_level': user_card.level,
        'levels_gained': levels_gained,
        'current_exp': user_card.exp,
        'exp_required': calc_exp_required(user_card.level),
        'message': f'升级成功！获得 {levels_gained} 级'
    })


@bp.route('/star-up', methods=['POST'])
@login_required
def star_up_card():
    """升星卡牌"""
    data = request.json
    user_card_id = data.get('user_card_id')
    material_type = data.get('material_type')  # 'duplicate' or 'star_stone'

    # 验证卡牌
    user_card = UserCard.query.get(user_card_id)
    if not user_card or user_card.user_id != current_user.id:
        return jsonify({'error': '卡牌不存在'}), 404

    if user_card.star_level >= 5:
        return jsonify({'error': '已达最高星级★5'}), 400

    # 获取升星需求
    required = get_star_up_requirements(user_card.star_level)
    if not required:
        return jsonify({'error': '无法升星'}), 400

    # 检查金币
    if current_user.coins < required['coins']:
        return jsonify({'error': f"金币不足，需要 {required['coins']}"}), 400

    if material_type == 'star_stone':
        # 使用万能星石
        user_item = UserItem.query.filter_by(
            user_id=current_user.id,
            item_type='star_stone'
        ).first()

        if not user_item or user_item.quantity < required['star_stones']:
            return jsonify({'error': f"万能星石不足，需要 {required['star_stones']}"}), 400

        user_item.quantity -= required['star_stones']

    elif material_type == 'duplicate':
        # 使用同名卡
        duplicates = UserCard.query.filter(
            UserCard.user_id == current_user.id,
            UserCard.card_id == user_card.card_id,
            UserCard.id != user_card_id
        ).limit(required['duplicates']).all()

        if len(duplicates) < required['duplicates']:
            return jsonify({'error': f"同名卡不足，需要 {required['duplicates']} 张"}), 400

        # 消耗同名卡
        for dup in duplicates:
            db.session.delete(dup)
    else:
        return jsonify({'error': '材料类型错误'}), 400

    # 消耗金币并升星
    current_user.coins -= required['coins']
    user_card.star_level += 1

    db.session.commit()

    return jsonify({
        'success': True,
        'new_star_level': user_card.star_level,
        'message': f'升星成功！当前星级 ★{user_card.star_level}'
    })


@bp.route('/skill-upgrade', methods=['POST'])
@login_required
def upgrade_skill():
    """升级技能"""
    data = request.json
    user_card_id = data.get('user_card_id')
    skill_type = data.get('skill_type')  # 'main' or 'passive'

    # 验证卡牌
    user_card = UserCard.query.get(user_card_id)
    if not user_card or user_card.user_id != current_user.id:
        return jsonify({'error': '卡牌不存在'}), 404

    # 获取当前技能等级
    current_level = user_card.main_skill_level if skill_type == 'main' else user_card.passive_skill_level

    if current_level >= 10:
        return jsonify({'error': '技能已达最高等级Lv.10'}), 400

    # 获取升级消耗
    cost = get_skill_upgrade_cost(current_level)
    if not cost:
        return jsonify({'error': '无法升级'}), 400

    # 检查金币
    if current_user.coins < cost['coins']:
        return jsonify({'error': f"金币不足，需要 {cost['coins']}"}), 400

    # 检查技能书
    user_item = UserItem.query.filter_by(
        user_id=current_user.id,
        item_type='skill_book',
        item_subtype=cost['book_type']
    ).first()

    if not user_item or user_item.quantity < cost['book_count']:
        return jsonify({'error': f"技能书不足，需要 {cost['book_type']} x{cost['book_count']}"}), 400

    # 消耗材料
    user_item.quantity -= cost['book_count']
    current_user.coins -= cost['coins']

    # 升级技能
    if skill_type == 'main':
        user_card.main_skill_level += 1
        new_level = user_card.main_skill_level
    else:
        user_card.passive_skill_level += 1
        new_level = user_card.passive_skill_level

    db.session.commit()

    return jsonify({
        'success': True,
        'skill_type': skill_type,
        'new_level': new_level,
        'message': f'技能升级成功！当前等级 Lv.{new_level}'
    })


@bp.route('/awaken', methods=['POST'])
@login_required
def awaken_card():
    """觉醒卡牌"""
    data = request.json
    user_card_id = data.get('user_card_id')

    # 验证卡牌
    user_card = UserCard.query.get(user_card_id)
    if not user_card or user_card.user_id != current_user.id:
        return jsonify({'error': '卡牌不存在'}), 404

    # 检查觉醒条件
    if user_card.level < 50:
        return jsonify({'error': '等级不足Lv.50'}), 400

    if user_card.star_level < 3:
        return jsonify({'error': '星级不足★3'}), 400

    if user_card.awaken_level >= 1:
        return jsonify({'error': '已完成觉醒'}), 400

    # 检查觉醒材料
    awaken_stones = UserItem.query.filter_by(
        user_id=current_user.id,
        item_type='awaken_stone'
    ).first()

    if not awaken_stones or awaken_stones.quantity < 50:
        return jsonify({'error': '觉醒石不足，需要 50 个'}), 400

    # 检查同名卡
    duplicate = UserCard.query.filter(
        UserCard.user_id == current_user.id,
        UserCard.card_id == user_card.card_id,
        UserCard.id != user_card_id
    ).first()

    if not duplicate:
        return jsonify({'error': '需要 1 张同名卡'}), 400

    # 检查金币
    if current_user.coins < 1000000:
        return jsonify({'error': '金币不足，需要 1,000,000'}), 400

    # 执行觉醒
    awaken_stones.quantity -= 50
    current_user.coins -= 1000000
    db.session.delete(duplicate)
    user_card.awaken_level = 1

    db.session.commit()

    return jsonify({
        'success': True,
        'message': '觉醒成功！解锁第二主动技能，全属性+30%'
    })


@bp.route('/breakthrough', methods=['POST'])
@login_required
def breakthrough_card():
    """突破卡牌"""
    data = request.json
    user_card_id = data.get('user_card_id')

    # 验证卡牌
    user_card = UserCard.query.get(user_card_id)
    if not user_card or user_card.user_id != current_user.id:
        return jsonify({'error': '卡牌不存在'}), 404

    # 检查基础条件
    current_max_level = get_max_level(user_card.breakthrough_level)
    if user_card.level < current_max_level:
        return jsonify({'error': f'等级不足Lv.{current_max_level}'}), 400

    if user_card.star_level < 5:
        return jsonify({'error': '星级不足★5'}), 400

    if user_card.awaken_level < 1:
        return jsonify({'error': '需要先完成觉醒'}), 400

    if user_card.breakthrough_level >= 3:
        return jsonify({'error': '已达最高突破等级'}), 400

    # 获取突破需求
    next_breakthrough = user_card.breakthrough_level + 1
    required = get_breakthrough_requirements(next_breakthrough)
    if not required:
        return jsonify({'error': '无法突破'}), 400

    # 检查突破石
    breakthrough_stones = UserItem.query.filter_by(
        user_id=current_user.id,
        item_type='breakthrough_stone'
    ).first()

    if not breakthrough_stones or breakthrough_stones.quantity < required['breakthrough_stones']:
        return jsonify({'error': f"突破石不足，需要 {required['breakthrough_stones']}"}), 400

    # 检查同名卡
    duplicates = UserCard.query.filter(
        UserCard.user_id == current_user.id,
        UserCard.card_id == user_card.card_id,
        UserCard.id != user_card_id
    ).limit(required['duplicates']).all()

    if len(duplicates) < required['duplicates']:
        return jsonify({'error': f"同名卡不足，需要 {required['duplicates']} 张"}), 400

    # 检查金币
    if current_user.coins < required['coins']:
        return jsonify({'error': f"金币不足，需要 {required['coins']}"}), 400

    # 执行突破
    breakthrough_stones.quantity -= required['breakthrough_stones']
    current_user.coins -= required['coins']

    for dup in duplicates:
        db.session.delete(dup)

    user_card.breakthrough_level += 1

    new_max_level = get_max_level(user_card.breakthrough_level)

    db.session.commit()

    return jsonify({
        'success': True,
        'breakthrough_level': user_card.breakthrough_level,
        'new_max_level': new_max_level,
        'message': f'突破成功！等级上限提升至 Lv.{new_max_level}，全属性+20%'
    })


@bp.route('/equip', methods=['POST'])
@login_required
def equip_equipment():
    """装备道具"""
    data = request.json
    user_card_id = data.get('user_card_id')
    equipment_id = data.get('equipment_id')

    # 验证卡牌
    user_card = UserCard.query.get(user_card_id)
    if not user_card or user_card.user_id != current_user.id:
        return jsonify({'error': '卡牌不存在'}), 404

    # 验证装备
    equipment = Equipment.query.get(equipment_id)
    if not equipment or equipment.user_id != current_user.id:
        return jsonify({'error': '装备不存在'}), 404

    # 获取装备类型
    slot = equipment.type

    # 卸下该槽位当前装备
    old_equipment = Equipment.query.filter_by(
        owner_card_id=user_card_id,
        type=slot
    ).first()

    if old_equipment:
        old_equipment.owner_card_id = None

    # 装备新装备
    equipment.owner_card_id = user_card_id

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'装备 {equipment.name} 成功'
    })


@bp.route('/unequip', methods=['POST'])
@login_required
def unequip_equipment():
    """卸下装备"""
    data = request.json
    equipment_id = data.get('equipment_id')

    # 验证装备
    equipment = Equipment.query.get(equipment_id)
    if not equipment or equipment.user_id != current_user.id:
        return jsonify({'error': '装备不存在'}), 404

    # 卸下装备
    equipment.owner_card_id = None

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'卸下 {equipment.name} 成功'
    })


@bp.route('/card-stats/<int:user_card_id>', methods=['GET'])
@login_required
def get_card_stats(user_card_id):
    """获取卡牌完整属性（包含所有成长加成）"""
    # 验证卡牌
    user_card = UserCard.query.get(user_card_id)
    if not user_card or user_card.user_id != current_user.id:
        return jsonify({'error': '卡牌不存在'}), 404

    # 获取基础卡牌数据
    card = Card.query.get(user_card.card_id)

    # 计算最终属性
    final_stats = calc_final_stats(user_card, card)

    # 获取装备加成
    equipments = Equipment.query.filter_by(owner_card_id=user_card_id).all()
    equipment_info = []
    for equip in equipments:
        stats = EquipmentStat.query.filter_by(equipment_id=equip.id).all()
        equipment_info.append({
            'name': equip.name,
            'type': equip.type,
            'quality': equip.quality,
            'enhance_level': equip.enhance_level,
            'stats': [{
                'type': stat.stat_type,
                'value': stat.stat_value
            } for stat in stats]
        })

    return jsonify({
        'success': True,
        'card_name': card.name,
        'rarity': card.rarity,
        'level': user_card.level,
        'exp': user_card.exp,
        'exp_required': calc_exp_required(user_card.level),
        'star_level': user_card.star_level,
        'awaken_level': user_card.awaken_level,
        'breakthrough_level': user_card.breakthrough_level,
        'main_skill_level': user_card.main_skill_level,
        'passive_skill_level': user_card.passive_skill_level,
        'max_level': get_max_level(user_card.breakthrough_level),
        'final_stats': final_stats,
        'equipments': equipment_info
    })


@bp.route('/materials', methods=['GET'])
@login_required
def get_materials():
    """获取用户所有材料"""
    items = UserItem.query.filter_by(user_id=current_user.id).all()

    materials = {}
    for item in items:
        key = f"{item.item_type}:{item.item_subtype}" if item.item_subtype else item.item_type
        materials[key] = item.quantity

    return jsonify({
        'success': True,
        'materials': materials
    })
