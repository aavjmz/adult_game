"""
装备系统工具函数
包含装备效果计算、套装检测、强化系统等
"""

import json
import random
from app.models import Equipment, EquipmentTemplate, EquipmentSet, Card, UserCard


def calc_equipment_bonus(equipment):
    """
    计算单件装备的属性加成

    Args:
        equipment: Equipment实例
    Returns:
        dict: 属性加成字典
    """
    if not equipment or not equipment.template:
        return {}

    template = equipment.template

    # 强化加成倍率（每级+5%）
    enhance_multiplier = 1 + (equipment.enhance_level * 0.05)

    bonus = {
        'attack_pct': template.base_attack_pct * enhance_multiplier,
        'defense_pct': template.base_defense_pct * enhance_multiplier,
        'hp_pct': template.base_hp_pct * enhance_multiplier,
        'crit_rate': template.crit_rate * enhance_multiplier,
        'crit_dmg': template.crit_dmg * enhance_multiplier,
        'speed': int(template.speed * enhance_multiplier),
        'penetration': template.penetration * enhance_multiplier,
        'block_rate': template.block_rate * enhance_multiplier,
        'dodge_rate': template.dodge_rate * enhance_multiplier,
        'lifesteal': template.lifesteal * enhance_multiplier,
    }

    # 随机附加属性
    if equipment.random_stats:
        try:
            random_stats = json.loads(equipment.random_stats)
            for stat_type, stat_value in random_stats.items():
                bonus[stat_type] = bonus.get(stat_type, 0) + stat_value
        except:
            pass

    return bonus


def calc_total_equipment_bonus(user_card):
    """
    计算武将所有装备的总加成

    Args:
        user_card: UserCard实例
    Returns:
        dict: 总属性加成
    """
    equipments = Equipment.query.filter_by(owner_card_id=user_card.id).all()

    total_bonus = {
        'attack_pct': 0,
        'defense_pct': 0,
        'hp_pct': 0,
        'crit_rate': 0,
        'crit_dmg': 0,
        'speed': 0,
        'penetration': 0,
        'block_rate': 0,
        'dodge_rate': 0,
        'lifesteal': 0,
    }

    for equip in equipments:
        bonus = calc_equipment_bonus(equip)
        for key, value in bonus.items():
            total_bonus[key] = total_bonus.get(key, 0) + value

    # 应用套装加成
    set_bonus, _ = calc_set_bonus(user_card)
    for key, value in set_bonus.items():
        total_bonus[key] = total_bonus.get(key, 0) + value

    return total_bonus


def calc_set_bonus(user_card):
    """
    计算套装加成

    Args:
        user_card: UserCard实例
    Returns:
        tuple: (套装加成字典, 激活套装列表)
    """
    equipments = Equipment.query.filter_by(owner_card_id=user_card.id).all()

    # 统计每个套装的装备数量
    set_counts = {}
    for equip in equipments:
        if equip.template and equip.template.set_id:
            set_id = equip.template.set_id
            set_counts[set_id] = set_counts.get(set_id, 0) + 1

    total_set_bonus = {
        'attack_pct': 0,
        'defense_pct': 0,
        'hp_pct': 0,
        'crit_rate': 0,
        'crit_dmg': 0,
        'speed': 0,
    }

    active_sets = []

    for set_id, count in set_counts.items():
        equipment_set = EquipmentSet.query.get(set_id)
        if not equipment_set:
            continue

        # 2件套加成
        if count >= 2:
            total_set_bonus['attack_pct'] += equipment_set.bonus_2_attack_pct
            total_set_bonus['defense_pct'] += equipment_set.bonus_2_defense_pct
            total_set_bonus['hp_pct'] += equipment_set.bonus_2_hp_pct
            total_set_bonus['crit_rate'] += equipment_set.bonus_2_crit_rate
            total_set_bonus['crit_dmg'] += equipment_set.bonus_2_crit_dmg
            total_set_bonus['speed'] += equipment_set.bonus_2_speed

            active_sets.append({
                'name': equipment_set.name,
                'pieces': 2,
                'desc': equipment_set.bonus_2_desc
            })

        # 4件套加成
        if count >= 4:
            total_set_bonus['attack_pct'] += equipment_set.bonus_4_attack_pct
            total_set_bonus['defense_pct'] += equipment_set.bonus_4_defense_pct
            total_set_bonus['hp_pct'] += equipment_set.bonus_4_hp_pct
            total_set_bonus['crit_rate'] += equipment_set.bonus_4_crit_rate
            total_set_bonus['crit_dmg'] += equipment_set.bonus_4_crit_dmg
            total_set_bonus['speed'] += equipment_set.bonus_4_speed

            active_sets.append({
                'name': equipment_set.name,
                'pieces': 4,
                'desc': equipment_set.bonus_4_desc,
                'special': equipment_set.bonus_4_special_effect
            })

    return total_set_bonus, active_sets


def check_exclusive_combo(user_card):
    """
    检查专属装备组合

    Args:
        user_card: UserCard实例
    Returns:
        dict: 专属组合信息
    """
    card = Card.query.get(user_card.card_id)
    equipments = Equipment.query.filter_by(owner_card_id=user_card.id).all()

    # 获取已装备的专属装备
    exclusive_equipments = []
    for equip in equipments:
        if equip.template and equip.template.exclusive_hero_id == card.id:
            exclusive_equipments.append(equip.template.name)

    # 检查预定义的专属组合
    exclusive_combos = get_exclusive_combos()

    for combo in exclusive_combos:
        if combo['hero_id'] == card.id:
            required = set(combo['required_equipments'])
            equipped = set(exclusive_equipments)

            if required.issubset(equipped):
                return {
                    'active': True,
                    'name': combo['name'],
                    'desc': combo['desc'],
                    'bonus': combo['bonus']
                }

    return {'active': False}


def get_exclusive_combos():
    """获取所有预定义的专属装备组合"""
    return [
        {
            'hero_id': 1,  # 关羽
            'name': '关云长之威',
            'required_equipments': ['青龙偃月刀', '赤兔马鞍'],
            'desc': '攻击力额外+50%，速度+30，击杀目标后立即行动',
            'bonus': {
                'attack_pct': 0.50,
                'speed': 30,
                'special': 'kill_reset_action'
            }
        },
        {
            'hero_id': 2,  # 张飞
            'name': '猛张飞之怒',
            'required_equipments': ['丈八蛇矛', '虎胆甲'],
            'desc': '攻击力+45%，防御力+30%，受击必定反击',
            'bonus': {
                'attack_pct': 0.45,
                'defense_pct': 0.30,
                'special': 'counter_on_hit'
            }
        },
        {
            'hero_id': 4,  # 赵云
            'name': '常山赵子龙',
            'required_equipments': ['古锭刀', '绝影马鞍'],
            'desc': '攻击力+40%，速度+40，每回合可行动2次',
            'bonus': {
                'attack_pct': 0.40,
                'speed': 40,
                'special': 'double_action'
            }
        },
        {
            'hero_id': 3,  # 诸葛亮
            'name': '卧龙天降',
            'required_equipments': ['羽扇', '八卦衣', '七星灯'],
            'desc': '全属性+35%，技能伤害+60%，死亡时80%概率复活',
            'bonus': {
                'attack_pct': 0.35,
                'defense_pct': 0.35,
                'hp_pct': 0.35,
                'special': 'revive_80'
            }
        }
    ]


def apply_equipment_to_stats(user_card, base_stats):
    """
    将装备加成应用到基础属性

    Args:
        user_card: UserCard实例
        base_stats: 基础属性字典 {'attack': xxx, 'defense': xxx, 'hp': xxx}
    Returns:
        dict: 应用装备后的最终属性
    """
    equipment_bonus = calc_total_equipment_bonus(user_card)

    final_stats = {
        'attack': int(base_stats['attack'] * (1 + equipment_bonus['attack_pct'])),
        'defense': int(base_stats['defense'] * (1 + equipment_bonus['defense_pct'])),
        'hp': int(base_stats['hp'] * (1 + equipment_bonus['hp_pct'])),
        'crit_rate': base_stats.get('crit_rate', 5.0) + equipment_bonus['crit_rate'],
        'crit_dmg': base_stats.get('crit_dmg', 150.0) + equipment_bonus['crit_dmg'],
        'speed': base_stats.get('speed', 50) + equipment_bonus['speed'],
        'penetration': equipment_bonus['penetration'],
        'block_rate': equipment_bonus['block_rate'],
        'dodge_rate': equipment_bonus['dodge_rate'],
        'lifesteal': equipment_bonus['lifesteal'],
    }

    return final_stats


def calc_enhance_success_rate(current_level):
    """
    计算强化成功率

    Args:
        current_level: 当前强化等级
    Returns:
        float: 成功率（0-1）
    """
    if current_level < 5:
        return 1.0
    elif current_level < 10:
        return 0.9
    elif current_level < 15:
        return 0.7
    elif current_level < 20:
        return 0.5
    elif current_level < 25:
        return 0.3
    else:
        return 0.1


def calc_enhance_cost(current_level, quality):
    """
    计算强化消耗

    Args:
        current_level: 当前强化等级
        quality: 装备品质
    Returns:
        dict: {'stones': 强化石数量, 'coins': 金币}
    """
    quality_multiplier = {
        'common': 1,
        'rare': 2,
        'epic': 5,
        'legendary': 10,
        'mythic': 20
    }

    base_stones = (current_level // 5 + 1) * 5
    base_coins = (current_level + 1) * 10000

    multiplier = quality_multiplier.get(quality, 1)

    return {
        'stones': base_stones * multiplier,
        'coins': base_coins * multiplier
    }


def generate_random_stats(quality):
    """
    生成随机附加属性

    Args:
        quality: 装备品质
    Returns:
        dict: 随机属性
    """
    stat_pool = [
        'crit_rate',
        'crit_dmg',
        'speed',
        'penetration',
        'lifesteal',
        'block_rate',
        'dodge_rate'
    ]

    # 附加属性数量
    stat_counts = {
        'common': 0,
        'rare': 1,
        'epic': 2,
        'legendary': 4,
        'mythic': 5
    }

    count = stat_counts.get(quality, 0)
    if count == 0:
        return {}

    selected_stats = random.sample(stat_pool, min(count, len(stat_pool)))

    random_stats = {}
    for stat in selected_stats:
        if stat == 'speed':
            random_stats[stat] = random.randint(5, 20)
        elif stat in ['crit_rate', 'penetration', 'lifesteal']:
            random_stats[stat] = round(random.uniform(5.0, 15.0), 1)
        elif stat == 'crit_dmg':
            random_stats[stat] = round(random.uniform(10.0, 30.0), 1)
        else:
            random_stats[stat] = round(random.uniform(3.0, 10.0), 1)

    return random_stats


def calc_equipment_power(equipment):
    """
    计算装备战力评分

    Args:
        equipment: Equipment实例
    Returns:
        int: 战力评分
    """
    if not equipment or not equipment.template:
        return 0

    template = equipment.template
    bonus = calc_equipment_bonus(equipment)

    # 基础属性评分
    power = 0
    power += bonus['attack_pct'] * 1000
    power += bonus['defense_pct'] * 800
    power += bonus['hp_pct'] * 500
    power += bonus['crit_rate'] * 50
    power += bonus['crit_dmg'] * 20
    power += bonus['speed'] * 10

    # 品质加成
    quality_multiplier = {
        'common': 1.0,
        'rare': 1.5,
        'epic': 2.0,
        'legendary': 3.0,
        'mythic': 5.0
    }
    power *= quality_multiplier.get(template.quality, 1.0)

    # 强化等级加成
    power *= (1 + equipment.enhance_level * 0.05)

    return int(power)
