# -*- coding: utf-8 -*-
"""
PVE 敌方卡牌数据

敌军与玩家武将共用 cards 表，靠 Card.is_enemy 区分：标记为敌军的卡
只出现在关卡里，不进招贤卡池、不进图鉴。

其中张辽、吕布、关羽、赵云、孙策、周瑜、貂蝉与玩家武将同名——种子数据
已建过这些卡，init_enemy_cards.py 按名查重会跳过它们，关卡直接复用玩家卡，
所以它们不能被标成敌军。
"""

ENEMY_CARDS = [
    # 黄巾军 (N卡)
    {'name': '黄巾贼兵', 'rarity': 'N', 'attack': 60, 'defense': 40, 'hp': 600,
     'is_golden': False, 'skill_name': '乱砍', 'skill_description': '造成120%攻击力伤害'},
    {'name': '黄巾弓手', 'rarity': 'N', 'attack': 65, 'defense': 35, 'hp': 550,
     'is_golden': False, 'skill_name': '乱箭', 'skill_description': '造成125%攻击力伤害'},
    {'name': '黄巾法师', 'rarity': 'N', 'attack': 70, 'defense': 30, 'hp': 500,
     'is_golden': False, 'skill_name': '妖术', 'skill_description': '造成135%攻击力魔法伤害'},

    # 黄巾将领 (R卡)
    {'name': '黄巾将领', 'rarity': 'R', 'attack': 100, 'defense': 80, 'hp': 1000,
     'is_golden': False, 'skill_name': '冲阵', 'skill_description': '造成170%攻击力伤害'},

    # 黄巾首领 (SR卡)
    {'name': '张梁', 'rarity': 'SR', 'attack': 160, 'defense': 130, 'hp': 1600,
     'is_golden': False, 'skill_name': '雷击术', 'skill_description': '造成240%攻击力雷电伤害'},
    {'name': '张角', 'rarity': 'SSR', 'attack': 250, 'defense': 180, 'hp': 2200,
     'is_golden': True, 'skill_name': '太平妖术', 'skill_description': '造成320%攻击力群体伤害', 'skill_damage_multiplier': 3.2},

    # 董卓军 (R卡)
    {'name': '董卓军士', 'rarity': 'R', 'attack': 110, 'defense': 90, 'hp': 1100,
     'is_golden': False, 'skill_name': '凶猛斩击', 'skill_description': '造成175%攻击力伤害'},
    {'name': '董卓弓手', 'rarity': 'R', 'attack': 105, 'defense': 85, 'hp': 1000,
     'is_golden': False, 'skill_name': '精准射击', 'skill_description': '造成180%攻击力伤害'},
    {'name': '董卓法师', 'rarity': 'R', 'attack': 115, 'defense': 75, 'hp': 950,
     'is_golden': False, 'skill_name': '火焰弹', 'skill_description': '造成185%攻击力魔法伤害'},
    {'name': '董卓将领', 'rarity': 'SR', 'attack': 170, 'defense': 140, 'hp': 1700,
     'is_golden': False, 'skill_name': '破军斩', 'skill_description': '造成245%攻击力伤害'},

    # 董卓军将领 (SR/SSR卡)
    {'name': '华雄', 'rarity': 'SR', 'attack': 200, 'defense': 160, 'hp': 2000,
     'is_golden': False, 'skill_name': '狂战之力', 'skill_description': '造成280%攻击力狂暴伤害'},
    {'name': '李傕', 'rarity': 'SR', 'attack': 195, 'defense': 155, 'hp': 1950,
     'is_golden': False, 'skill_name': '凶刃乱舞', 'skill_description': '造成270%攻击力连击伤害'},
    {'name': '郭汜', 'rarity': 'SR', 'attack': 190, 'defense': 150, 'hp': 1900,
     'is_golden': False, 'skill_name': '残暴突袭', 'skill_description': '造成265%攻击力伤害'},
    {'name': '董卓', 'rarity': 'SSR', 'attack': 270, 'defense': 200, 'hp': 2800,
     'is_golden': True, 'skill_name': '暴君之怒', 'skill_description': '造成360%攻击力毁灭伤害', 'skill_damage_multiplier': 3.6},

    # 诸侯军 (R卡)
    {'name': '诸侯军士', 'rarity': 'R', 'attack': 120, 'defense': 95, 'hp': 1150,
     'is_golden': False, 'skill_name': '战阵冲锋', 'skill_description': '造成180%攻击力伤害'},
    {'name': '诸侯弓手', 'rarity': 'R', 'attack': 115, 'defense': 90, 'hp': 1100,
     'is_golden': False, 'skill_name': '齐射', 'skill_description': '造成185%攻击力伤害'},

    # 袁绍军 (SR卡)
    {'name': '袁绍军士', 'rarity': 'SR', 'attack': 175, 'defense': 145, 'hp': 1750,
     'is_golden': False, 'skill_name': '精锐突击', 'skill_description': '造成250%攻击力伤害'},
    {'name': '袁绍弓手', 'rarity': 'SR', 'attack': 170, 'defense': 140, 'hp': 1700,
     'is_golden': False, 'skill_name': '穿云箭', 'skill_description': '造成255%攻击力伤害'},
    {'name': '袁绍将领', 'rarity': 'SR', 'attack': 185, 'defense': 155, 'hp': 1850,
     'is_golden': False, 'skill_name': '威压', 'skill_description': '造成265%攻击力伤害'},
    {'name': '袁绍法师', 'rarity': 'SR', 'attack': 180, 'defense': 135, 'hp': 1650,
     'is_golden': False, 'skill_name': '冰锥术', 'skill_description': '造成270%攻击力魔法伤害'},
    {'name': '颜良', 'rarity': 'SSR', 'attack': 290, 'defense': 210, 'hp': 2900,
     'is_golden': True, 'skill_name': '神威无双', 'skill_description': '造成380%攻击力伤害', 'skill_damage_multiplier': 3.8},
    {'name': '文丑', 'rarity': 'SSR', 'attack': 285, 'defense': 205, 'hp': 2850,
     'is_golden': True, 'skill_name': '虎啸龙吟', 'skill_description': '造成375%攻击力伤害', 'skill_damage_multiplier': 3.75},

    # 吕布军 (SR/SSR卡)
    {'name': '吕布军弓手', 'rarity': 'SR', 'attack': 175, 'defense': 140, 'hp': 1700,
     'is_golden': False, 'skill_name': '快速射击', 'skill_description': '造成255%攻击力伤害'},
    {'name': '吕布军法师', 'rarity': 'SR', 'attack': 180, 'defense': 135, 'hp': 1650,
     'is_golden': False, 'skill_name': '烈焰风暴', 'skill_description': '造成270%攻击力魔法伤害'},
    {'name': '高顺', 'rarity': 'SSR', 'attack': 275, 'defense': 200, 'hp': 2700,
     'is_golden': True, 'skill_name': '陷阵之志', 'skill_description': '造成365%攻击力伤害', 'skill_damage_multiplier': 3.65},
    {'name': '张辽', 'rarity': 'SSR', 'attack': 280, 'defense': 195, 'hp': 2650,
     'is_golden': True, 'skill_name': '突袭千里', 'skill_description': '造成370%攻击力伤害', 'skill_damage_multiplier': 3.7},
    {'name': '陈宫', 'rarity': 'SR', 'attack': 185, 'defense': 140, 'hp': 1700,
     'is_golden': False, 'skill_name': '妙计', 'skill_description': '造成260%攻击力智谋伤害'},
    {'name': '吕布', 'rarity': 'UR', 'attack': 550, 'defense': 420, 'hp': 5500,
     'is_golden': True, 'skill_name': '方天画戟', 'skill_description': '造成700%攻击力绝杀伤害', 'skill_damage_multiplier': 7.0},

    # 曹操军 (SR卡)
    {'name': '曹操军士', 'rarity': 'SR', 'attack': 180, 'defense': 150, 'hp': 1800,
     'is_golden': False, 'skill_name': '精兵突击', 'skill_description': '造成260%攻击力伤害'},
    {'name': '曹操弓手', 'rarity': 'SR', 'attack': 175, 'defense': 145, 'hp': 1750,
     'is_golden': False, 'skill_name': '连珠箭', 'skill_description': '造成265%攻击力伤害'},
    {'name': '曹操法师', 'rarity': 'SR', 'attack': 185, 'defense': 140, 'hp': 1700,
     'is_golden': False, 'skill_name': '雷霆万钧', 'skill_description': '造成275%攻击力魔法伤害'},
    {'name': '曹操将领', 'rarity': 'SR', 'attack': 190, 'defense': 160, 'hp': 1900,
     'is_golden': False, 'skill_name': '破敌', 'skill_description': '造成280%攻击力伤害'},

    # 刘备军 (SSR卡)
    {'name': '刘备军弓手', 'rarity': 'SR', 'attack': 175, 'defense': 145, 'hp': 1750,
     'is_golden': False, 'skill_name': '仁义之箭', 'skill_description': '造成265%攻击力伤害'},
    {'name': '关羽', 'rarity': 'UR', 'attack': 530, 'defense': 400, 'hp': 5200,
     'is_golden': True, 'skill_name': '青龙偃月', 'skill_description': '造成680%攻击力神圣伤害', 'skill_damage_multiplier': 6.8},
    {'name': '张飞', 'rarity': 'UR', 'attack': 540, 'defense': 410, 'hp': 5300,
     'is_golden': True, 'skill_name': '丈八蛇矛', 'skill_description': '造成690%攻击力霸道伤害', 'skill_damage_multiplier': 6.9},
    {'name': '赵云', 'rarity': 'UR', 'attack': 525, 'defense': 395, 'hp': 5100,
     'is_golden': True, 'skill_name': '七进七出', 'skill_description': '造成675%攻击力连击伤害', 'skill_damage_multiplier': 6.75},

    # 东吴军 (SSR卡)
    {'name': '东吴弓手', 'rarity': 'SR', 'attack': 180, 'defense': 145, 'hp': 1750,
     'is_golden': False, 'skill_name': '水师齐射', 'skill_description': '造成270%攻击力伤害'},
    {'name': '东吴法师', 'rarity': 'SR', 'attack': 185, 'defense': 140, 'hp': 1700,
     'is_golden': False, 'skill_name': '江东风暴', 'skill_description': '造成275%攻击力魔法伤害'},
    {'name': '孙策', 'rarity': 'SSR', 'attack': 310, 'defense': 230, 'hp': 3100,
     'is_golden': True, 'skill_name': '霸王之气', 'skill_description': '造成400%攻击力伤害', 'skill_damage_multiplier': 4.0},
    {'name': '周瑜', 'rarity': 'SSR', 'attack': 305, 'defense': 220, 'hp': 3000,
     'is_golden': True, 'skill_name': '赤壁之火', 'skill_description': '造成395%攻击力火焰伤害', 'skill_damage_multiplier': 3.95},
    {'name': '太史慈', 'rarity': 'SSR', 'attack': 295, 'defense': 215, 'hp': 2950,
     'is_golden': True, 'skill_name': '神射', 'skill_description': '造成390%攻击力精准伤害', 'skill_damage_multiplier': 3.9},

    # 其他名将
    {'name': '貂蝉', 'rarity': 'SSR', 'attack': 260, 'defense': 180, 'hp': 2400,
     'is_golden': True, 'skill_name': '魅惑之舞', 'skill_description': '造成340%攻击力魅惑伤害', 'skill_damage_multiplier': 3.4},
]


# 与玩家武将同名、由玩家卡兼任的敌将（见模块说明）
SHARED_WITH_PLAYERS = {'张辽', '吕布', '关羽', '赵云', '孙策', '周瑜', '貂蝉'}

# 只作为敌军存在的卡名
ENEMY_ONLY_NAMES = {c['name'] for c in ENEMY_CARDS} - SHARED_WITH_PLAYERS
