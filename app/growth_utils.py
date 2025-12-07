"""
成长系统工具函数
包含等级、升星、技能等计算函数
"""


def calc_exp_required(level):
    """
    计算升级所需经验

    Args:
        level: 当前等级
    Returns:
        升到下一级所需经验值
    """
    if level >= 100:
        return 0  # 已满级

    if level < 20:
        # 前期快速升级
        return level * 100
    elif level < 40:
        # 中期正常升级
        return level * 200 + 2000
    elif level < 60:
        # 后期较慢
        return level * 500 + 10000
    elif level < 80:
        # 高级较慢
        return level * 1000 + 30000
    else:
        # 终极缓慢
        return level * 2000 + 80000


def calc_total_exp_to_level(target_level):
    """
    计算从Lv.1升到目标等级所需的总经验

    Args:
        target_level: 目标等级
    Returns:
        总经验值
    """
    total_exp = 0
    for lvl in range(1, target_level):
        total_exp += calc_exp_required(lvl)
    return total_exp


def calc_stat_at_level(base_stat, growth_rate, level):
    """
    计算指定等级的属性值

    Args:
        base_stat: 基础属性值（Lv.1时的值）
        growth_rate: 成长率
        level: 等级
    Returns:
        当前等级的属性值
    """
    return int(base_stat * (1 + growth_rate * (level - 1)))


def get_growth_rate(rarity):
    """
    根据稀有度获取成长率

    Args:
        rarity: 稀有度 (N/R/SR/SSR/UR)
    Returns:
        成长率
    """
    growth_rates = {
        'N': 0.02,   # 每级+2%
        'R': 0.025,  # 每级+2.5%
        'SR': 0.03,  # 每级+3%
        'SSR': 0.035,# 每级+3.5%
        'UR': 0.04   # 每级+4%
    }
    return growth_rates.get(rarity, 0.02)


def calc_star_bonus(base_stat, star_level):
    """
    计算升星加成

    Args:
        base_stat: 基础属性值
        star_level: 星级 (1-5)
    Returns:
        应用星级加成后的属性值
    """
    bonuses = {
        1: 1.0,   # 基础
        2: 1.15,  # +15%
        3: 1.35,  # +35%
        4: 1.60,  # +60%
        5: 2.10   # +110%
    }
    return int(base_stat * bonuses.get(star_level, 1.0))


def get_star_up_requirements(current_star):
    """
    获取升星所需材料

    Args:
        current_star: 当前星级
    Returns:
        dict: {'duplicates': 同名卡数量, 'star_stones': 万能星石数量, 'coins': 金币}
    """
    requirements = {
        1: {'duplicates': 1, 'star_stones': 10, 'coins': 50000},
        2: {'duplicates': 2, 'star_stones': 30, 'coins': 150000},
        3: {'duplicates': 3, 'star_stones': 60, 'coins': 500000},
        4: {'duplicates': 5, 'star_stones': 100, 'coins': 1500000},
    }
    return requirements.get(current_star, None)


def calc_skill_level_bonus(base_value, skill_level):
    """
    计算技能等级加成

    Args:
        base_value: 基础技能效果值（如伤害倍率）
        skill_level: 技能等级 (1-10)
    Returns:
        应用技能等级加成后的值
    """
    # 每级提升10%
    return base_value * (1 + (skill_level - 1) * 0.1)


def get_skill_upgrade_cost(current_level):
    """
    获取技能升级所需的技能书和金币

    Args:
        current_level: 当前技能等级
    Returns:
        dict: {'book_type': 技能书类型, 'book_count': 数量, 'coins': 金币}
    """
    costs = {
        1: {'book_type': 'small', 'book_count': 1, 'coins': 10000},
        2: {'book_type': 'small', 'book_count': 2, 'coins': 20000},
        3: {'book_type': 'small', 'book_count': 3, 'coins': 30000},
        4: {'book_type': 'medium', 'book_count': 1, 'coins': 50000},
        5: {'book_type': 'medium', 'book_count': 2, 'coins': 100000},
        6: {'book_type': 'medium', 'book_count': 3, 'coins': 200000},
        7: {'book_type': 'large', 'book_count': 1, 'coins': 400000},
        8: {'book_type': 'large', 'book_count': 2, 'coins': 800000},
        9: {'book_type': 'large', 'book_count': 3, 'coins': 1500000},
    }
    return costs.get(current_level, None)


def calc_skill_cooldown_reduction(base_cooldown, skill_level):
    """
    计算技能冷却时间减少

    Args:
        base_cooldown: 基础冷却时间
        skill_level: 技能等级
    Returns:
        实际冷却时间
    """
    # 每3级减1回合，最低1回合
    reduction = (skill_level - 1) // 3
    return max(1, base_cooldown - reduction)


def calc_awaken_bonus(base_stat):
    """
    计算觉醒属性加成

    Args:
        base_stat: 基础属性值
    Returns:
        应用觉醒加成后的属性值（+30%）
    """
    return int(base_stat * 1.3)


def calc_breakthrough_bonus(base_stat, breakthrough_level):
    """
    计算突破加成

    Args:
        base_stat: 基础属性值
        breakthrough_level: 突破等级 (0-3)
    Returns:
        应用突破加成后的属性值
    """
    # 每次突破+20%
    return int(base_stat * (1.2 ** breakthrough_level))


def get_breakthrough_requirements(breakthrough_level):
    """
    获取突破所需材料

    Args:
        breakthrough_level: 即将进行的突破次数 (1-3)
    Returns:
        dict: {'breakthrough_stones': 突破石, 'duplicates': 同名卡, 'coins': 金币}
    """
    requirements = {
        1: {'breakthrough_stones': 100, 'duplicates': 3, 'coins': 5000000},
        2: {'breakthrough_stones': 200, 'duplicates': 5, 'coins': 10000000},
        3: {'breakthrough_stones': 500, 'duplicates': 10, 'coins': 30000000},
    }
    return requirements.get(breakthrough_level, None)


def get_max_level(breakthrough_level):
    """
    获取当前突破等级下的最大等级

    Args:
        breakthrough_level: 突破等级 (0-3)
    Returns:
        最大等级
    """
    return 100 + (breakthrough_level * 20)


def calc_enhance_bonus(base_value, enhance_level):
    """
    计算装备强化加成

    Args:
        base_value: 基础属性值
        enhance_level: 强化等级 (0-30)
    Returns:
        应用强化加成后的值
    """
    # 每级+5%
    return base_value * (1 + enhance_level * 0.05)


def get_enhance_success_rate(enhance_level):
    """
    获取装备强化成功率

    Args:
        enhance_level: 当前强化等级
    Returns:
        成功率（0-100）
    """
    if enhance_level < 5:
        return 100
    elif enhance_level < 10:
        return 90
    elif enhance_level < 15:
        return 70
    elif enhance_level < 20:
        return 50
    elif enhance_level < 25:
        return 30
    else:
        return 10


def get_item_exp_value(item_type, item_subtype):
    """
    获取经验道具提供的经验值

    Args:
        item_type: 道具类型 (exp_potion)
        item_subtype: 道具子类型 (small/medium/large/xlarge)
    Returns:
        经验值
    """
    if item_type == 'exp_potion':
        exp_values = {
            'small': 1000,
            'medium': 5000,
            'large': 20000,
            'xlarge': 100000,
        }
        return exp_values.get(item_subtype, 0)
    return 0


def get_card_sacrifice_exp(rarity, is_same_card=False):
    """
    获取吞噬卡牌获得的经验值

    Args:
        rarity: 卡牌稀有度
        is_same_card: 是否为同名卡
    Returns:
        经验值
    """
    base_exp = {
        'N': 500,
        'R': 2000,
        'SR': 10000,
        'SSR': 50000,
        'UR': 0,  # UR不可作为经验素材
    }

    exp = base_exp.get(rarity, 0)

    # 获得基础经验的80%
    exp = int(exp * 0.8)

    # 同名卡额外+50%
    if is_same_card:
        exp = int(exp * 1.5)

    return exp


def calc_final_stats(user_card, card):
    """
    计算卡牌的最终属性（包含所有成长加成）

    Args:
        user_card: UserCard 实例
        card: Card 实例
    Returns:
        dict: {'attack': 攻击力, 'defense': 防御力, 'hp': 生命值}
    """
    # 获取成长率
    growth_rate = get_growth_rate(card.rarity)

    # 计算等级加成
    attack = calc_stat_at_level(card.attack, growth_rate, user_card.level)
    defense = calc_stat_at_level(card.defense, growth_rate, user_card.level)
    hp = calc_stat_at_level(card.hp, growth_rate, user_card.level)

    # 应用星级加成
    attack = calc_star_bonus(attack, user_card.star_level)
    defense = calc_star_bonus(defense, user_card.star_level)
    hp = calc_star_bonus(hp, user_card.star_level)

    # 应用觉醒加成
    if user_card.awaken_level > 0:
        attack = calc_awaken_bonus(attack)
        defense = calc_awaken_bonus(defense)
        hp = calc_awaken_bonus(hp)

    # 应用突破加成
    if user_card.breakthrough_level > 0:
        attack = calc_breakthrough_bonus(attack, user_card.breakthrough_level)
        defense = calc_breakthrough_bonus(defense, user_card.breakthrough_level)
        hp = calc_breakthrough_bonus(hp, user_card.breakthrough_level)

    return {
        'attack': attack,
        'defense': defense,
        'hp': hp
    }
