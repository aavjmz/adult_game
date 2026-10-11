"""
装备数据初始化 / 同步脚本
初始化套装和装备模板数据

按名字匹配，可重复执行：
- 新名字：新建
- 已存在：以本脚本里的数据为准逐列同步，只改有变化的列并打印字段名；
  脚本里没写的列恢复为该列默认值（删掉某个属性也能同步）
- 只增改，不删除：从脚本里去掉的套装 / 模板在库里保留不动
"""

import sys
import os

# 设置UTF-8编码输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, EquipmentSet, EquipmentTemplate
from app.utils.seed_sync import sync_columns


# 同步时不覆盖的列：主键、用作匹配键的名字、创建时间
_SYNC_SKIP = {'id', 'name', 'created_at'}


def sync_row(model, data, label):
    """按 name 新建或同步一条套装 / 装备模板

    Returns:
        'added' / 'updated' / 'same'
    """
    row = model.query.filter_by(name=data['name']).first()
    if row is None:
        db.session.add(model(**data))
        print(f"  ✅ 添加{label}: {data['name']}")
        return 'added'

    changed = sync_columns(row, data, _SYNC_SKIP)
    if changed:
        print(f"  🔄 更新{label}: {data['name']}（{', '.join(changed)}）")
        return 'updated'
    print(f"  ⏭️ {label} {data['name']} 无变化")
    return 'same'


def init_equipment_sets():
    """初始化4大套装配置"""
    print("\n🎨 初始化套装配置...")

    sets_data = [
        {
            'name': '五虎上将',
            'name_en': 'five_tigers',
            'bonus_2_desc': '攻击力+15%，暴击率+8%',
            'bonus_2_attack_pct': 0.15,
            'bonus_2_crit_rate': 8.0,
            'bonus_4_desc': '攻击力+30%，暴击率+15%，暴击伤害+30%',
            'bonus_4_attack_pct': 0.30,
            'bonus_4_crit_rate': 15.0,
            'bonus_4_crit_dmg': 30.0,
            'bonus_4_special_effect': '五虎降世',
            'bonus_4_special_desc': '战斗开始时己方全体获得【五虎之威】，攻击+20%，防御+20%，持续5回合'
        },
        {
            'name': '卧龙凤雏',
            'name_en': 'wise_strategists',
            'bonus_2_desc': '技能伤害+20%，技能冷却-1回合',
            'bonus_2_attack_pct': 0.10,
            'bonus_2_defense_pct': 0.10,
            'bonus_4_desc': '技能伤害+40%，技能冷却-2回合，全属性+15%',
            'bonus_4_attack_pct': 0.15,
            'bonus_4_defense_pct': 0.15,
            'bonus_4_hp_pct': 0.15,
            'bonus_4_special_effect': '天下无双',
            'bonus_4_special_desc': '释放技能时有30%概率立即重置冷却时间，为全队施加【智者祝福】，攻击+25%，每回合恢复5%生命'
        },
        {
            'name': '三国枭雄',
            'name_en': 'three_lords',
            'bonus_2_desc': '全属性+12%，暴击伤害+20%',
            'bonus_2_attack_pct': 0.12,
            'bonus_2_defense_pct': 0.12,
            'bonus_2_hp_pct': 0.12,
            'bonus_2_crit_dmg': 20.0,
            'bonus_4_desc': '全属性+25%，暴击伤害+40%，吸血20%',
            'bonus_4_attack_pct': 0.25,
            'bonus_4_defense_pct': 0.25,
            'bonus_4_hp_pct': 0.25,
            'bonus_4_crit_dmg': 40.0,
            'bonus_4_special_effect': '治世能臣',
            'bonus_4_special_desc': '攻击时有15%概率触发【奸雄之策】，窃取目标20%攻击力持续2回合，己方魏势力武将全属性额外+15%'
        },
        {
            'name': '江东霸业',
            'name_en': 'dongwu_lords',
            'bonus_2_desc': '攻击力+15%，速度+20',
            'bonus_2_attack_pct': 0.15,
            'bonus_2_speed': 20,
            'bonus_4_desc': '攻击力+30%，速度+35，暴击率+15%',
            'bonus_4_attack_pct': 0.30,
            'bonus_4_speed': 35,
            'bonus_4_crit_rate': 15.0,
            'bonus_4_special_effect': '东吴霸业',
            'bonus_4_special_desc': '战斗开始时获得【小霸王之威】，先手行动，首回合必定暴击，己方吴势力武将全属性额外+15%'
        }
    ]

    for set_data in sets_data:
        sync_row(EquipmentSet, set_data, '套装')

    db.session.commit()
    print("✅ 套装配置初始化完成")


def init_mythic_equipments():
    """初始化神话级装备"""
    print("\n⚔️ 初始化神话级装备...")

    # 获取套装ID（如果有）
    five_tigers_set = EquipmentSet.query.filter_by(name='五虎上将').first()
    wise_set = EquipmentSet.query.filter_by(name='卧龙凤雏').first()

    mythic_data = [
        {
            'name': '轩辕剑',
            'name_en': 'xuanyuan_sword',
            'type': 'weapon',
            'quality': 'mythic',
            'element': '无',
            'base_attack_pct': 0.60,
            'crit_rate': 20.0,
            'crit_dmg': 50.0,
            'speed': 25,
            'penetration': 30.0,
            'max_enhance_level': 30,
            'exclusive_effect_name': '轩辕之威',
            'exclusive_effect_desc': '攻击时有15%概率触发【剑气纵横】，对敌方全体造成200%攻击力的真实伤害，自身获得【圣剑庇护】状态（免疫控制，3回合）',
            'exclusive_effect_type': 'on_attack',
            'exclusive_effect_value': 0.15,
            'obtain_method': '轩辕剑副本（超难）',
            'description': '上古神剑，轩辕黄帝铸造，剑身铭刻日月星辰',
            'lore': '黄帝采首山之铜，铸此神剑，剑成之日，天降祥瑞，黄帝乘龙升天。后世得此剑者，必成一代霸主。'
        },
        {
            'name': '方天画戟',
            'name_en': 'sky_piercer_halberd',
            'type': 'weapon',
            'quality': 'mythic',
            'element': '火',
            'base_attack_pct': 0.65,
            'crit_rate': 18.0,
            'crit_dmg': 45.0,
            'speed': 30,
            'exclusive_hero_id': 9,  # 吕布
            'exclusive_effect_name': '无双战神',
            'exclusive_effect_desc': '每次攻击有25%概率触发连击，连续攻击2-4次，每次造成80%伤害，连击期间无法被打断',
            'exclusive_effect_type': 'on_attack',
            'exclusive_effect_value': 0.25,
            'max_enhance_level': 30,
            'obtain_method': '吕布专属副本（超难）',
            'description': '吕布的专属武器，戟长一丈八尺，重九十八斤',
            'lore': '虎牢关前，吕布独战刘关张三英，方天画戟所向披靡，人中吕布，马中赤兔，威震天下。'
        },
        {
            'name': '玄武甲',
            'name_en': 'xuanwu_armor',
            'type': 'armor',
            'quality': 'mythic',
            'element': '水',
            'base_defense_pct': 0.60,
            'base_hp_pct': 0.50,
            'block_rate': 20.0,
            'max_enhance_level': 30,
            'exclusive_effect_name': '玄武庇护',
            'exclusive_effect_desc': '受到致命伤害时，免疫此次伤害并回复50%最大生命（每场战斗1次），获得【神龟护体】状态（减伤50%，3回合）',
            'exclusive_effect_type': 'on_damaged',
            'exclusive_effect_value': 0.50,
            'obtain_method': '四神兽副本',
            'description': '玄武神兽的护甲，龟蛇合一，坚不可摧',
            'lore': '北方之神玄武，主杀伐征战。得此甲者，可保性命无虞，万军之中如入无人之境。'
        },
        {
            'name': '白虎战甲',
            'name_en': 'white_tiger_armor',
            'type': 'armor',
            'quality': 'mythic',
            'element': '金',
            'base_defense_pct': 0.55,
            'base_attack_pct': 0.30,
            'crit_dmg': 30.0,
            'block_rate': 25.0,
            'max_enhance_level': 30,
            'exclusive_effect_name': '白虎杀气',
            'exclusive_effect_desc': '受到攻击时有30%概率触发反击，反击造成80%攻击力的伤害，反击暴击率提升至100%',
            'exclusive_effect_type': 'on_damaged',
            'exclusive_effect_value': 0.30,
            'obtain_method': '四神兽副本',
            'description': '白虎神兽的战甲，杀气腾腾，攻守兼备',
            'lore': '西方之神白虎，主征战杀伐。得此甲者，攻防一体，反击之势如白虎下山。'
        },
        {
            'name': '传国玉玺',
            'name_en': 'imperial_jade_seal',
            'type': 'treasure',
            'quality': 'mythic',
            'element': '无',
            'base_attack_pct': 0.20,
            'base_defense_pct': 0.20,
            'base_hp_pct': 0.20,
            'speed': 40,
            'max_enhance_level': 30,
            'exclusive_effect_name': '帝王之威',
            'exclusive_effect_desc': '战斗开始时，己方全体获得【王者之气】，全属性+20%持续全场，每击败一个敌人全队回复10%生命',
            'exclusive_effect_type': 'battle_start',
            'exclusive_effect_value': 0.20,
            'obtain_method': '传国玉玺副本（超难）',
            'description': '秦始皇传世玉玺，得之者得天下',
            'lore': '秦始皇令李斯篆书"受命于天，既寿永昌"八字，咸阳玉工孙寿刻于和氏璧上，历代帝王视为正统象征。'
        },
        {
            'name': '七星灯',
            'name_en': 'seven_star_lamp',
            'type': 'accessory',
            'quality': 'mythic',
            'element': '火',
            'base_attack_pct': 0.25,
            'speed': 50,
            'crit_rate': 20.0,
            'max_enhance_level': 30,
            'exclusive_hero_id': 3,  # 诸葛亮
            'exclusive_effect_name': '续命之术',
            'exclusive_effect_desc': '战斗中首次死亡时必定复活，复活时回复80%生命，获得【天命所归】状态（无敌1回合）',
            'exclusive_effect_type': 'on_death',
            'exclusive_effect_value': 0.80,
            'obtain_method': '七星灯副本（限时活动）',
            'description': '诸葛亮续命所用，七星排列，玄妙无比',
            'lore': '建兴十二年，诸葛亮病重五丈原，设七星灯祈禳北斗，欲延寿十二年。然天意难违，魏延误闯帐中，灯灭而亡。'
        }
    ]

    for equip_data in mythic_data:
        sync_row(EquipmentTemplate, equip_data, '神话装备')

    db.session.commit()
    print("✅ 神话级装备初始化完成")


def init_legendary_equipments():
    """初始化传说级装备"""
    print("\n🗡️ 初始化传说级装备...")

    # 获取套装ID
    five_tigers_set = EquipmentSet.query.filter_by(name='五虎上将').first()
    wise_set = EquipmentSet.query.filter_by(name='卧龙凤雏').first()
    lords_set = EquipmentSet.query.filter_by(name='三国枭雄').first()
    dongwu_set = EquipmentSet.query.filter_by(name='江东霸业').first()

    legendary_data = [
        # 五虎上将套装 - 武器
        {
            'name': '青龙偃月刀',
            'name_en': 'green_dragon_crescent_blade',
            'type': 'weapon',
            'quality': 'legendary',
            'element': '金',
            'base_attack_pct': 0.40,
            'crit_rate': 10.0,
            'crit_dmg': 25.0,
            'speed': 15,
            'exclusive_hero_id': 1,  # 关羽
            'exclusive_effect_name': '武圣之威',
            'exclusive_effect_desc': '攻击时额外造成30%真实伤害，击败敌人回复50%最大生命，对魏势力武将额外造成15%伤害',
            'exclusive_effect_type': 'on_attack',
            'exclusive_effect_value': 0.30,
            'set_id': five_tigers_set.id if five_tigers_set else None,
            'max_enhance_level': 25,
            'obtain_method': '五虎上将副本、世界Boss',
            'description': '关羽的专属武器，重达八十二斤，刀身镌刻青龙图案',
            'lore': '建安五年，关羽斩颜良文丑，此刀威震华夏。后人传言，刀身青龙若隐若现，斩敌必见血光。'
        },
        {
            'name': '丈八蛇矛',
            'name_en': 'serpent_spear',
            'type': 'weapon',
            'quality': 'legendary',
            'element': '金',
            'base_attack_pct': 0.42,
            'crit_rate': 12.0,
            'speed': 18,
            'penetration': 20.0,
            'exclusive_hero_id': 2,  # 张飞
            'exclusive_effect_name': '猛虎啸天',
            'exclusive_effect_desc': '攻击时无视目标30%防御，对生命低于50%的敌人额外造成40%伤害，每回合开始时获得【嗜血】状态（攻击+15%，叠加3层）',
            'exclusive_effect_type': 'on_attack',
            'exclusive_effect_value': 0.30,
            'set_id': five_tigers_set.id if five_tigers_set else None,
            'max_enhance_level': 25,
            'obtain_method': '五虎上将副本',
            'description': '张飞的专属武器，长一丈八尺，矛头如蛇信',
            'lore': '长坂坡前，张翼德独挡曹军，一声怒吼，吓退曹操百万雄师，矛尖所指，无人敢挡。'
        },
        {
            'name': '古锭刀',
            'name_en': 'ancient_saber',
            'type': 'weapon',
            'quality': 'legendary',
            'element': '火',
            'base_attack_pct': 0.45,
            'crit_rate': 8.0,
            'crit_dmg': 30.0,
            'speed': 20,
            'exclusive_hero_id': 4,  # 赵云
            'exclusive_effect_name': '龙吟破军',
            'exclusive_effect_desc': '暴击时额外造成50%伤害，攻击时有10%概率触发【斩杀】，直接击杀生命低于20%的敌人',
            'exclusive_effect_type': 'on_crit',
            'exclusive_effect_value': 0.50,
            'set_id': five_tigers_set.id if five_tigers_set else None,
            'max_enhance_level': 25,
            'obtain_method': '五虎上将副本',
            'description': '赵云的专属武器，刀身古朴，锋利无比',
            'lore': '长坂坡七进七出，赵子龙单骑救主，古锭刀所向披靡，曹军闻风丧胆。'
        },
        # 卧龙凤雏套装
        {
            'name': '羽扇',
            'name_en': 'feather_fan',
            'type': 'weapon',
            'quality': 'legendary',
            'element': '木',
            'base_attack_pct': 0.35,
            'speed': 30,
            'crit_rate': 12.0,
            'exclusive_hero_id': 3,  # 诸葛亮
            'exclusive_effect_name': '羽扇纶巾',
            'exclusive_effect_desc': '释放技能时，为全队施加【智者庇护】，抵挡一次伤害，技能伤害提升30%',
            'exclusive_effect_type': 'on_skill',
            'exclusive_effect_value': 0.30,
            'set_id': wise_set.id if wise_set else None,
            'max_enhance_level': 25,
            'obtain_method': '卧龙副本',
            'description': '诸葛亮的标志性羽扇，挥扇之间，决胜千里',
            'lore': '隆中对策，羽扇轻摇，三分天下之计成。后随孔明征战，扇动处风云变色。'
        },
        {
            'name': '八卦衣',
            'name_en': 'bagua_robe',
            'type': 'armor',
            'quality': 'legendary',
            'element': '土',
            'base_defense_pct': 0.25,
            'base_hp_pct': 0.20,
            'dodge_rate': 10.0,
            'exclusive_hero_id': 3,  # 诸葛亮
            'exclusive_effect_name': '八卦奇术',
            'exclusive_effect_desc': '每回合有30%概率免疫一次伤害，免疫时触发【八门遁甲】，下次技能伤害提升100%',
            'exclusive_effect_type': 'passive',
            'exclusive_effect_value': 0.30,
            'set_id': wise_set.id if wise_set else None,
            'max_enhance_level': 25,
            'obtain_method': '卧龙副本',
            'description': '诸葛亮所穿八卦道袍，玄机暗藏',
            'lore': '孔明通晓奇门遁甲，八卦之术，此袍以八卦排列织成，可避刀兵之祸。'
        },
        # 三国枭雄套装
        {
            'name': '七星宝刀',
            'name_en': 'seven_star_sword',
            'type': 'weapon',
            'quality': 'legendary',
            'element': '木',
            'base_attack_pct': 0.38,
            'speed': 25,
            'crit_rate': 15.0,
            'lifesteal': 15.0,
            'exclusive_hero_id': 5,  # 曹操
            'exclusive_effect_name': '奸雄之刃',
            'exclusive_effect_desc': '攻击时有20%概率触发【毒刃】，造成目标最大生命10%的持续伤害（3回合），击杀带有【毒刃】的敌人时，冷却时间全部重置',
            'exclusive_effect_type': 'on_attack',
            'exclusive_effect_value': 0.20,
            'set_id': lords_set.id if lords_set else None,
            'max_enhance_level': 25,
            'obtain_method': '三国枭雄副本',
            'description': '曹操刺杀董卓时所用宝刀，刀柄镶七星',
            'lore': '初平元年，曹操献七星宝刀入相府，欲刺董卓。事泄未成，献刀托言，仓皇而逃。'
        },
        {
            'name': '倚天剑',
            'name_en': 'heaven_reliant_sword',
            'type': 'weapon',
            'quality': 'legendary',
            'element': '水',
            'base_attack_pct': 0.35,
            'base_defense_pct': 0.20,
            'crit_rate': 10.0,
            'exclusive_hero_id': 6,  # 曹操（也可以给其他人）
            'exclusive_effect_name': '倚天屠龙',
            'exclusive_effect_desc': '攻击时有15%概率触发【冰封】，冻结目标1回合无法行动，自身每回合回复5%最大生命',
            'exclusive_effect_type': 'on_attack',
            'exclusive_effect_value': 0.15,
            'set_id': lords_set.id if lords_set else None,
            'max_enhance_level': 25,
            'obtain_method': '三国枭雄副本',
            'description': '曹操的佩剑之一，与青釭剑齐名',
            'lore': '曹操得此剑后，佩之征战四方，剑锋所指，所向披靡。倚天既出，谁与争锋。'
        },
        # 江东霸业套装
        {
            'name': '霸王枪',
            'name_en': 'overlord_spear',
            'type': 'weapon',
            'quality': 'legendary',
            'element': '火',
            'base_attack_pct': 0.43,
            'crit_rate': 15.0,
            'speed': 25,
            'exclusive_hero_id': 7,  # 孙策
            'exclusive_effect_name': '小霸王之威',
            'exclusive_effect_desc': '战斗开始时，先手行动，首回合攻击必定暴击，击败目标后立即行动',
            'exclusive_effect_type': 'battle_start',
            'exclusive_effect_value': 1.0,
            'set_id': dongwu_set.id if dongwu_set else None,
            'max_enhance_level': 25,
            'obtain_method': '江东霸王副本',
            'description': '孙策的专属武器，枪长九尺，威猛无比',
            'lore': '孙伯符年少成名，号称"小霸王"，持此枪纵横江东，无人能敌。'
        },
        {
            'name': '麒麟甲',
            'name_en': 'qilin_armor',
            'type': 'armor',
            'quality': 'legendary',
            'element': '火',
            'base_defense_pct': 0.28,
            'base_hp_pct': 0.25,
            'block_rate': 15.0,
            'exclusive_hero_id': 7,  # 孙策
            'exclusive_effect_name': '麒麟降世',
            'exclusive_effect_desc': '生命低于30%时触发【涅槃】，回复40%最大生命，获得【重生之焰】（攻击+50%，3回合），每场战斗1次',
            'exclusive_effect_type': 'on_low_hp',
            'exclusive_effect_value': 0.40,
            'set_id': dongwu_set.id if dongwu_set else None,
            'max_enhance_level': 25,
            'obtain_method': '江东霸王副本',
            'description': '传说中的麒麟战甲，凤凰之力',
            'lore': '孙策得此甲后，如有神助，转战千里，所向披靡，江东子弟尽归心。'
        }
    ]

    for equip_data in legendary_data:
        sync_row(EquipmentTemplate, equip_data, '传说装备')

    db.session.commit()
    print("✅ 传说级装备初始化完成")


def init_basic_equipments():
    """初始化普通 / 稀有 / 史诗装备

    关卡掉落的碎片分五个品级，合成时消耗同品级碎片；原先只有传说、神话两档
    模板，前三档碎片没东西可合。这里四个部位各补一件，属性逐档递增，
    都低于传说级，没有专属效果与套装。
    """
    print("\n⚔️ 初始化普通 / 稀有 / 史诗装备...")

    basic_data = [
        # 普通
        {'name': '环首刀', 'name_en': 'ring_pommel_dao', 'type': 'weapon', 'quality': 'common', 'element': '金',
         'base_attack_pct': 0.08, 'description': '汉军制式佩刀，刀柄铸环，便于劈砍'},
        {'name': '皮甲', 'name_en': 'leather_armor', 'type': 'armor', 'quality': 'common', 'element': '土',
         'base_defense_pct': 0.08, 'base_hp_pct': 0.05, 'description': '鞣制牛皮缝成的轻甲'},
        {'name': '铜带钩', 'name_en': 'bronze_belt_hook', 'type': 'accessory', 'quality': 'common', 'element': '金',
         'base_attack_pct': 0.04, 'speed': 5, 'description': '青铜铸的腰带钩，士卒常佩'},
        {'name': '竹简兵书', 'name_en': 'bamboo_manual', 'type': 'treasure', 'quality': 'common', 'element': '木',
         'base_attack_pct': 0.04, 'base_defense_pct': 0.04, 'base_hp_pct': 0.04, 'description': '抄录兵法要略的竹简'},
        # 稀有
        {'name': '百炼环刀', 'name_en': 'refined_dao', 'type': 'weapon', 'quality': 'rare', 'element': '金',
         'base_attack_pct': 0.15, 'crit_rate': 3.0, 'description': '百炼精钢锻成，锋利远胜寻常刀剑'},
        {'name': '鱼鳞甲', 'name_en': 'fish_scale_armor', 'type': 'armor', 'quality': 'rare', 'element': '水',
         'base_defense_pct': 0.15, 'base_hp_pct': 0.10, 'description': '甲片层叠如鱼鳞，兼顾防护与灵活'},
        {'name': '青玉佩', 'name_en': 'jade_pendant', 'type': 'accessory', 'quality': 'rare', 'element': '木',
         'base_attack_pct': 0.08, 'speed': 10, 'crit_dmg': 10.0, 'description': '青玉雕成的佩饰，君子比德于玉'},
        {'name': '六韬', 'name_en': 'six_secret_teachings', 'type': 'treasure', 'quality': 'rare', 'element': '无',
         'base_attack_pct': 0.08, 'base_defense_pct': 0.08, 'base_hp_pct': 0.08, 'description': '托名太公所著的兵书'},
        # 史诗
        {'name': '斩马刀', 'name_en': 'zhanma_dao', 'type': 'weapon', 'quality': 'epic', 'element': '金',
         'base_attack_pct': 0.25, 'crit_rate': 6.0, 'crit_dmg': 10.0, 'description': '长柄重刀，可斩奔马'},
        {'name': '明光铠', 'name_en': 'mingguang_armor', 'type': 'armor', 'quality': 'epic', 'element': '金',
         'base_defense_pct': 0.25, 'base_hp_pct': 0.18, 'block_rate': 5.0, 'description': '胸背护镜光可鉴人，将领所服'},
        {'name': '蟠螭玉环', 'name_en': 'panchi_jade_ring', 'type': 'accessory', 'quality': 'epic', 'element': '水',
         'base_attack_pct': 0.12, 'speed': 18, 'crit_dmg': 18.0, 'description': '玉环上盘绕螭龙纹，王侯之器'},
        {'name': '太公兵法', 'name_en': 'taigong_art_of_war', 'type': 'treasure', 'quality': 'epic', 'element': '无',
         'base_attack_pct': 0.12, 'base_defense_pct': 0.12, 'base_hp_pct': 0.12, 'description': '张良圯上所受之书'},
    ]

    quality_label = {'common': '普通装备', 'rare': '稀有装备', 'epic': '史诗装备'}
    for equip_data in basic_data:
        # 这两项三档共用，并进数据里一起参与同步
        data = dict(equip_data, max_enhance_level=30, obtain_method='碎片合成')
        sync_row(EquipmentTemplate, data, quality_label[equip_data['quality']])

    db.session.commit()
    print("✅ 普通 / 稀有 / 史诗装备初始化完成")


def main():
    """主函数"""
    print("=" * 60)
    print("🎮 三国卡牌游戏 - 装备数据初始化")
    print("=" * 60)

    app = create_app()

    with app.app_context():
        # 初始化套装
        init_equipment_sets()

        # 初始化装备
        init_mythic_equipments()
        init_legendary_equipments()
        init_basic_equipments()

        # 统计
        sets_count = EquipmentSet.query.count()
        templates_count = EquipmentTemplate.query.count()

        print("\n" + "=" * 60)
        print("📊 初始化统计")
        print("=" * 60)
        print(f"套装数量: {sets_count}")
        print(f"装备模板数量: {templates_count}")
        print("\n✅ 装备数据初始化完成！")
        print("\n可以运行以下命令测试:")
        print("  python test_equipment_system.py")


if __name__ == '__main__':
    main()
