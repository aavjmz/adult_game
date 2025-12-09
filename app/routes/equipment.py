"""
装备系统路由
包含装备强化、合成、分解、装备/卸下等功能
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import json
import random
from app.models import db, Equipment, EquipmentTemplate, EquipmentSet, UserCard, User, UserItem, Card
from app.equipment_utils import (
    calc_equipment_bonus, calc_total_equipment_bonus, calc_set_bonus,
    check_exclusive_combo, apply_equipment_to_stats, calc_enhance_success_rate,
    calc_enhance_cost, generate_random_stats, calc_equipment_power
)

bp = Blueprint('equipment', __name__, url_prefix='/equipment')


@bp.route('/list', methods=['GET'])
@login_required
def list_equipments():
    """获取用户所有装备"""
    # 获取查询参数
    quality_filter = request.args.get('quality')  # common/rare/epic/legendary/mythic
    type_filter = request.args.get('type')  # weapon/armor/accessory/treasure
    equipped_only = request.args.get('equipped') == 'true'
    unequipped_only = request.args.get('unequipped') == 'true'

    # 构建查询
    query = Equipment.query.filter_by(user_id=current_user.id)

    if equipped_only:
        query = query.filter(Equipment.owner_card_id.isnot(None))
    elif unequipped_only:
        query = query.filter(Equipment.owner_card_id.is_(None))

    equipments = query.all()

    # 格式化装备数据
    equipment_list = []
    for equip in equipments:
        # 使用模板系统
        if equip.template:
            template = equip.template
            equip_data = {
                'id': equip.id,
                'template_id': template.id,
                'name': template.name,
                'type': template.type,
                'quality': template.quality,
                'element': template.element,
                'enhance_level': equip.enhance_level,
                'is_locked': equip.is_locked,
                'owner_card_id': equip.owner_card_id,
                'set_name': template.equipment_set.name if template.set_id else None,
                'exclusive_hero_id': template.exclusive_hero_id,
                'exclusive_effect': template.exclusive_effect_name,
                'power': calc_equipment_power(equip)
            }

            # 计算属性加成
            bonus = calc_equipment_bonus(equip)
            equip_data['bonus'] = bonus

            # 添加随机属性
            if equip.random_stats:
                try:
                    equip_data['random_stats'] = json.loads(equip.random_stats)
                except:
                    equip_data['random_stats'] = {}

        else:
            # 旧装备系统（向后兼容）
            equip_data = {
                'id': equip.id,
                'name': equip.name,
                'type': equip.type,
                'quality': equip.quality,
                'enhance_level': equip.enhance_level,
                'is_locked': equip.is_locked,
                'owner_card_id': equip.owner_card_id,
                'base_stat_type': equip.base_stat_type,
                'base_stat_value': equip.base_stat_value,
                'power': calc_equipment_power(equip)
            }

        # 应用过滤器
        if quality_filter and equip_data.get('quality') != quality_filter:
            continue
        if type_filter and equip_data.get('type') != type_filter:
            continue

        equipment_list.append(equip_data)

    # 按战力排序
    equipment_list.sort(key=lambda x: x.get('power', 0), reverse=True)

    return jsonify({
        'success': True,
        'count': len(equipment_list),
        'equipments': equipment_list
    })


@bp.route('/enhance', methods=['POST'])
@login_required
def enhance_equipment():
    """强化装备"""
    data = request.json
    equipment_id = data.get('equipment_id')
    use_protection = data.get('use_protection', False)  # 是否使用保护符（防止降级）

    # 验证装备
    equipment = Equipment.query.get(equipment_id)
    if not equipment or equipment.user_id != current_user.id:
        return jsonify({'error': '装备不存在'}), 404

    # 检查是否已锁定
    if equipment.is_locked:
        return jsonify({'error': '装备已锁定，无法强化'}), 400

    # 获取装备品质
    if equipment.template:
        quality = equipment.template.quality
        max_level = equipment.template.max_enhance_level
    else:
        quality = equipment.quality
        max_level = 30

    # 检查是否达到上限
    if equipment.enhance_level >= max_level:
        return jsonify({'error': f'已达最高强化等级 +{max_level}'}), 400

    # 计算强化消耗
    cost = calc_enhance_cost(equipment.enhance_level, quality)

    # 检查金币
    if current_user.coins < cost['coins']:
        return jsonify({'error': f"金币不足，需要 {cost['coins']}"}), 400

    # 检查强化石
    enhance_stone = UserItem.query.filter_by(
        user_id=current_user.id,
        item_type='enhance_stone'
    ).first()

    if not enhance_stone or enhance_stone.quantity < cost['stones']:
        return jsonify({'error': f"强化石不足，需要 {cost['stones']}"}), 400

    # 检查保护符
    if use_protection:
        protection_item = UserItem.query.filter_by(
            user_id=current_user.id,
            item_type='protection_charm'
        ).first()

        if not protection_item or protection_item.quantity < 1:
            return jsonify({'error': '保护符不足'}), 400

        protection_item.quantity -= 1

    # 计算成功率
    success_rate = calc_enhance_success_rate(equipment.enhance_level)
    roll = random.random()
    success = roll < success_rate

    # 消耗材料
    enhance_stone.quantity -= cost['stones']
    current_user.coins -= cost['coins']

    old_level = equipment.enhance_level

    if success:
        # 强化成功
        equipment.enhance_level += 1
        new_level = equipment.enhance_level

        db.session.commit()

        return jsonify({
            'success': True,
            'result': 'success',
            'old_level': old_level,
            'new_level': new_level,
            'power': calc_equipment_power(equipment),
            'message': f'强化成功！ +{old_level} → +{new_level}'
        })
    else:
        # 强化失败
        if use_protection:
            # 使用了保护符，等级不变
            db.session.commit()
            return jsonify({
                'success': True,
                'result': 'fail_protected',
                'old_level': old_level,
                'new_level': old_level,
                'message': '强化失败！保护符生效，等级未降低'
            })
        else:
            # 未使用保护符，可能降级
            if equipment.enhance_level <= 10:
                # 0-10级失败不降级
                penalty = 0
            elif equipment.enhance_level <= 20:
                # 11-20级失败降1级
                penalty = 1
            else:
                # 21-30级失败降2级
                penalty = 2

            equipment.enhance_level = max(0, equipment.enhance_level - penalty)
            new_level = equipment.enhance_level

            db.session.commit()

            return jsonify({
                'success': True,
                'result': 'fail',
                'old_level': old_level,
                'new_level': new_level,
                'penalty': penalty,
                'message': f'强化失败！ +{old_level} → +{new_level}'
            })


@bp.route('/synthesize', methods=['POST'])
@login_required
def synthesize_equipment():
    """合成装备"""
    data = request.json
    template_id = data.get('template_id')

    # 验证模板
    template = EquipmentTemplate.query.get(template_id)
    if not template:
        return jsonify({'error': '装备模板不存在'}), 404

    # 计算合成消耗（基于品质）
    fragment_costs = {
        'common': 10,
        'rare': 20,
        'epic': 50,
        'legendary': 100,
        'mythic': 200
    }

    coin_costs = {
        'common': 10000,
        'rare': 50000,
        'epic': 200000,
        'legendary': 1000000,
        'mythic': 5000000
    }

    fragments_required = fragment_costs.get(template.quality, 50)
    coins_required = coin_costs.get(template.quality, 100000)

    # 检查金币
    if current_user.coins < coins_required:
        return jsonify({'error': f'金币不足，需要 {coins_required}'}), 400

    # 检查碎片
    fragment = UserItem.query.filter_by(
        user_id=current_user.id,
        item_type='equipment_fragment',
        item_subtype='universal'  # 通用碎片
    ).first()

    if not fragment or fragment.quantity < fragments_required:
        return jsonify({'error': f'装备碎片不足，需要 {fragments_required}'}), 400

    # 消耗材料
    fragment.quantity -= fragments_required
    current_user.coins -= coins_required

    # 生成随机属性
    random_stats = generate_random_stats(template.quality)

    # 创建装备（包含向后兼容字段）
    new_equipment = Equipment(
        user_id=current_user.id,
        template_id=template_id,
        name=template.name,  # 向后兼容
        type=template.type,  # 向后兼容
        quality=template.quality,  # 向后兼容
        enhance_level=0,
        random_stats=json.dumps(random_stats) if random_stats else None,
        is_locked=False
    )

    db.session.add(new_equipment)
    db.session.commit()

    return jsonify({
        'success': True,
        'equipment': {
            'id': new_equipment.id,
            'name': template.name,
            'quality': template.quality,
            'type': template.type,
            'random_stats': random_stats,
            'power': calc_equipment_power(new_equipment)
        },
        'message': f'成功合成 {template.name}！'
    })


@bp.route('/dismantle', methods=['POST'])
@login_required
def dismantle_equipment():
    """分解装备"""
    data = request.json
    equipment_id = data.get('equipment_id')

    # 验证装备
    equipment = Equipment.query.get(equipment_id)
    if not equipment or equipment.user_id != current_user.id:
        return jsonify({'error': '装备不存在'}), 404

    # 检查是否已装备
    if equipment.owner_card_id:
        return jsonify({'error': '请先卸下装备'}), 400

    # 检查是否已锁定
    if equipment.is_locked:
        return jsonify({'error': '装备已锁定，无法分解'}), 400

    # 计算分解收益（基于品质和强化等级）
    if equipment.template:
        quality = equipment.template.quality
    else:
        quality = equipment.quality

    base_fragments = {
        'common': 2,
        'rare': 5,
        'epic': 15,
        'legendary': 40,
        'mythic': 100
    }

    fragments_gained = base_fragments.get(quality, 5)
    # 强化等级加成
    fragments_gained += equipment.enhance_level * 2

    # 获取或创建碎片记录
    fragment = UserItem.query.filter_by(
        user_id=current_user.id,
        item_type='equipment_fragment',
        item_subtype='universal'
    ).first()

    if not fragment:
        fragment = UserItem(
            user_id=current_user.id,
            item_type='equipment_fragment',
            item_subtype='universal',
            quantity=0
        )
        db.session.add(fragment)

    fragment.quantity += fragments_gained

    # 删除装备
    equipment_name = equipment.template.name if equipment.template else equipment.name
    db.session.delete(equipment)
    db.session.commit()

    return jsonify({
        'success': True,
        'fragments_gained': fragments_gained,
        'message': f'分解 {equipment_name} 获得 {fragments_gained} 个装备碎片'
    })


@bp.route('/card-equipments/<int:user_card_id>', methods=['GET'])
@login_required
def get_card_equipments(user_card_id):
    """获取卡牌装备信息"""
    # 验证卡牌
    user_card = UserCard.query.get(user_card_id)
    if not user_card or user_card.user_id != current_user.id:
        return jsonify({'error': '卡牌不存在'}), 404

    # 获取卡牌基础信息
    card = Card.query.get(user_card.card_id)

    # 获取已装备的装备
    equipments = Equipment.query.filter_by(owner_card_id=user_card_id).all()

    equipment_list = []
    for equip in equipments:
        if equip.template:
            template = equip.template
            equip_data = {
                'id': equip.id,
                'name': template.name,
                'type': template.type,
                'quality': template.quality,
                'element': template.element,
                'enhance_level': equip.enhance_level,
                'is_locked': equip.is_locked,
                'bonus': calc_equipment_bonus(equip),
                'power': calc_equipment_power(equip),
                'set_name': template.equipment_set.name if template.set_id else None,
                'exclusive_effect': template.exclusive_effect_name if template.exclusive_hero_id == card.id else None
            }

            # 添加随机属性
            if equip.random_stats:
                try:
                    equip_data['random_stats'] = json.loads(equip.random_stats)
                except:
                    equip_data['random_stats'] = {}
        else:
            # 旧装备
            equip_data = {
                'id': equip.id,
                'name': equip.name,
                'type': equip.type,
                'quality': equip.quality,
                'enhance_level': equip.enhance_level,
                'power': calc_equipment_power(equip)
            }

        equipment_list.append(equip_data)

    # 计算总装备加成
    total_bonus = calc_total_equipment_bonus(user_card)

    # 计算套装加成
    set_bonus, active_sets = calc_set_bonus(user_card)

    # 检查专属组合
    exclusive_combo = check_exclusive_combo(user_card)

    return jsonify({
        'success': True,
        'card_name': card.name,
        'card_rarity': card.rarity,
        'equipments': equipment_list,
        'total_bonus': total_bonus,
        'active_sets': active_sets,
        'exclusive_combo': exclusive_combo
    })


@bp.route('/equip', methods=['POST'])
@login_required
def equip_to_card():
    """装备到卡牌"""
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
    if equipment.template:
        equip_type = equipment.template.type
        equip_name = equipment.template.name
    else:
        equip_type = equipment.type
        equip_name = equipment.name

    # 检查该类型槽位是否已有装备
    existing = Equipment.query.filter_by(
        owner_card_id=user_card_id
    ).join(EquipmentTemplate).filter(
        EquipmentTemplate.type == equip_type
    ).first()

    # 如果没找到新模板装备，检查旧装备
    if not existing:
        existing = Equipment.query.filter_by(
            owner_card_id=user_card_id,
            type=equip_type
        ).first()

    # 卸下旧装备
    if existing:
        existing.owner_card_id = None

    # 装备新装备
    equipment.owner_card_id = user_card_id

    db.session.commit()

    # 计算新的装备加成
    total_bonus = calc_total_equipment_bonus(user_card)
    set_bonus, active_sets = calc_set_bonus(user_card)

    return jsonify({
        'success': True,
        'message': f'成功装备 {equip_name}',
        'total_bonus': total_bonus,
        'active_sets': active_sets
    })


@bp.route('/unequip', methods=['POST'])
@login_required
def unequip_from_card():
    """卸下装备"""
    data = request.json
    equipment_id = data.get('equipment_id')

    # 验证装备
    equipment = Equipment.query.get(equipment_id)
    if not equipment or equipment.user_id != current_user.id:
        return jsonify({'error': '装备不存在'}), 404

    if not equipment.owner_card_id:
        return jsonify({'error': '装备未被装备'}), 400

    # 获取装备名称
    if equipment.template:
        equip_name = equipment.template.name
    else:
        equip_name = equipment.name

    # 卸下装备
    equipment.owner_card_id = None

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'成功卸下 {equip_name}'
    })


@bp.route('/lock', methods=['POST'])
@login_required
def lock_equipment():
    """锁定/解锁装备"""
    data = request.json
    equipment_id = data.get('equipment_id')
    lock_state = data.get('lock', True)

    # 验证装备
    equipment = Equipment.query.get(equipment_id)
    if not equipment or equipment.user_id != current_user.id:
        return jsonify({'error': '装备不存在'}), 404

    # 设置锁定状态
    equipment.is_locked = lock_state

    db.session.commit()

    return jsonify({
        'success': True,
        'is_locked': equipment.is_locked,
        'message': '装备已锁定' if lock_state else '装备已解锁'
    })


@bp.route('/templates', methods=['GET'])
@login_required
def get_equipment_templates():
    """获取装备模板列表"""
    # 获取查询参数
    quality_filter = request.args.get('quality')
    type_filter = request.args.get('type')
    set_id_filter = request.args.get('set_id', type=int)

    # 构建查询
    query = EquipmentTemplate.query

    if quality_filter:
        query = query.filter_by(quality=quality_filter)
    if type_filter:
        query = query.filter_by(type=type_filter)
    if set_id_filter:
        query = query.filter_by(set_id=set_id_filter)

    templates = query.all()

    template_list = []
    for template in templates:
        template_data = {
            'id': template.id,
            'name': template.name,
            'type': template.type,
            'quality': template.quality,
            'element': template.element,
            'base_attack_pct': template.base_attack_pct,
            'base_defense_pct': template.base_defense_pct,
            'base_hp_pct': template.base_hp_pct,
            'crit_rate': template.crit_rate,
            'crit_dmg': template.crit_dmg,
            'speed': template.speed,
            'set_id': template.set_id,
            'set_name': template.equipment_set.name if template.set_id else None,
            'exclusive_hero_id': template.exclusive_hero_id,
            'exclusive_effect_name': template.exclusive_effect_name,
            'exclusive_effect_desc': template.exclusive_effect_desc,
            'obtain_method': template.obtain_method,
            'description': template.description,
            'lore': template.lore
        }
        template_list.append(template_data)

    return jsonify({
        'success': True,
        'count': len(template_list),
        'templates': template_list
    })


@bp.route('/sets', methods=['GET'])
@login_required
def get_equipment_sets():
    """获取套装列表"""
    equipment_sets = EquipmentSet.query.all()

    set_list = []
    for equip_set in equipment_sets:
        set_data = {
            'id': equip_set.id,
            'name': equip_set.name,
            'bonus_2': {
                'desc': equip_set.bonus_2_desc,
                'attack_pct': equip_set.bonus_2_attack_pct,
                'defense_pct': equip_set.bonus_2_defense_pct,
                'hp_pct': equip_set.bonus_2_hp_pct,
                'crit_rate': equip_set.bonus_2_crit_rate,
                'crit_dmg': equip_set.bonus_2_crit_dmg,
                'speed': equip_set.bonus_2_speed
            },
            'bonus_4': {
                'desc': equip_set.bonus_4_desc,
                'attack_pct': equip_set.bonus_4_attack_pct,
                'defense_pct': equip_set.bonus_4_defense_pct,
                'hp_pct': equip_set.bonus_4_hp_pct,
                'crit_rate': equip_set.bonus_4_crit_rate,
                'crit_dmg': equip_set.bonus_4_crit_dmg,
                'speed': equip_set.bonus_4_speed,
                'special_effect': equip_set.bonus_4_special_effect,
                'special_desc': equip_set.bonus_4_special_desc
            },
            'equipment_count': equip_set.templates.count()
        }
        set_list.append(set_data)

    return jsonify({
        'success': True,
        'count': len(set_list),
        'sets': set_list
    })
