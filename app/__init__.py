from flask import Flask
from flask_login import LoginManager
from config import Config
from app.models import db, User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)

    # 注册蓝图
    from app.routes import auth, cards, gacha, battle, battle_v2, growth, equipment, main, pve, pve_frontend
    app.register_blueprint(auth.bp)
    app.register_blueprint(cards.bp)
    app.register_blueprint(gacha.bp)
    app.register_blueprint(battle.bp)
    app.register_blueprint(battle_v2.bp)
    app.register_blueprint(growth.bp)
    app.register_blueprint(equipment.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(pve.pve_bp)
    app.register_blueprint(pve_frontend.pve_frontend_bp)

    # 创建数据库表
    with app.app_context():
        db.create_all()
        init_cards()
        migrate_cards_to_three_kingdoms()
        init_stages()

    return app

def init_cards():
    """初始化三国武将卡牌数据"""
    from app.models import Card

    if Card.query.count() > 0:
        return  # 已有数据，跳过初始化

    # 三国武将卡牌数据（匹配 static/images/cards/ 中的原画）
    sample_cards = [
        # N卡 — 普通兵种（无原画，使用占位）
        {'name': '黄巾力士', 'rarity': 'N', 'attack': 80, 'defense': 60, 'hp': 800,
         'element': '土', 'faction': '群', 'job_class': '步将',
         'is_golden': False, 'skill_name': '奋力一击', 'skill_description': '造成150%攻击力的伤害'},
        {'name': '义勇民兵', 'rarity': 'N', 'attack': 70, 'defense': 50, 'hp': 700,
         'element': '木', 'faction': '群', 'job_class': '弓将',
         'is_golden': False, 'skill_name': '齐射', 'skill_description': '造成160%攻击力的远程伤害'},
        {'name': '游侠剑客', 'rarity': 'N', 'attack': 75, 'defense': 55, 'hp': 750,
         'element': '金', 'faction': '群', 'job_class': '武将',
         'is_golden': False, 'skill_name': '剑气斩', 'skill_description': '造成155%攻击力的伤害'},

        # R卡 — 三国名将（有原画）
        {'name': '张辽', 'rarity': 'R', 'attack': 130, 'defense': 100, 'hp': 1200,
         'element': '金', 'faction': '魏', 'job_class': '骑将',
         'image_url': '/static/images/cards/zhangliao.png',
         'is_golden': False, 'skill_name': '突袭', 'skill_description': '造成180%攻击力的伤害，并降低目标防御'},
        {'name': '孙策', 'rarity': 'R', 'attack': 125, 'defense': 90, 'hp': 1100,
         'element': '火', 'faction': '吴', 'job_class': '武将',
         'image_url': '/static/images/cards/sunce.png',
         'is_golden': False, 'skill_name': '霸王之击', 'skill_description': '造成190%攻击力的伤害'},
        {'name': '孙权', 'rarity': 'R', 'attack': 110, 'defense': 110, 'hp': 1150,
         'element': '水', 'faction': '吴', 'job_class': '谋士',
         'image_url': '/static/images/cards/sunquan.png',
         'is_golden': False, 'skill_name': '制衡', 'skill_description': '造成170%攻击力的伤害，恢复少量生命'},

        # SR卡 — 三国名将（有原画）
        {'name': '赵云', 'rarity': 'SR', 'attack': 190, 'defense': 150, 'hp': 1800,
         'element': '金', 'faction': '蜀', 'job_class': '骑将',
         'image_url': '/static/images/cards/zhaoyun.png',
         'is_golden': False, 'skill_name': '龙胆', 'skill_description': '造成250%攻击力的伤害，无视部分防御'},
        {'name': '周瑜', 'rarity': 'SR', 'attack': 200, 'defense': 120, 'hp': 1600,
         'element': '火', 'faction': '吴', 'job_class': '谋士',
         'image_url': '/static/images/cards/zhouyu.png',
         'is_golden': False, 'skill_name': '火攻', 'skill_description': '造成280%攻击力的火焰范围伤害'},
        {'name': '诸葛亮', 'rarity': 'SR', 'attack': 210, 'defense': 130, 'hp': 1700,
         'element': '火', 'faction': '蜀', 'job_class': '谋士',
         'image_url': '/static/images/cards/zhugeliang.png',
         'is_golden': False, 'skill_name': '八阵图', 'skill_description': '造成270%攻击力的伤害，有几率眩晕'},

        # SSR卡 — 三国名将（有原画，金色）
        {'name': '关羽', 'rarity': 'SSR', 'attack': 300, 'defense': 200, 'hp': 2500,
         'element': '金', 'faction': '蜀', 'job_class': '武将',
         'image_url': '/static/images/cards/guanyu.png',
         'is_golden': True, 'skill_name': '青龙偃月', 'skill_description': '造成350%攻击力的伤害，斩杀低血量目标',
         'skill_damage_multiplier': 3.5},
        {'name': '曹操', 'rarity': 'SSR', 'attack': 280, 'defense': 220, 'hp': 2600,
         'element': '水', 'faction': '魏', 'job_class': '谋士',
         'image_url': '/static/images/cards/caocao.png',
         'is_golden': True, 'skill_name': '奸雄', 'skill_description': '造成320%攻击力的伤害，恢复造成伤害的30%生命',
         'skill_damage_multiplier': 3.2},
        {'name': '刘备', 'rarity': 'SSR', 'attack': 260, 'defense': 240, 'hp': 2800,
         'element': '木', 'faction': '蜀', 'job_class': '武将',
         'image_url': '/static/images/cards/liubei.png',
         'is_golden': True, 'skill_name': '仁德', 'skill_description': '造成300%攻击力的伤害，同时恢复全体己方20%生命',
         'skill_damage_multiplier': 3.0},

        # UR卡 — 最强武将（有原画，金色）
        {'name': '吕布', 'rarity': 'UR', 'attack': 520, 'defense': 350, 'hp': 4800,
         'element': '火', 'faction': '群', 'job_class': '武将',
         'image_url': '/static/images/cards/lvbu.png',
         'is_golden': True, 'skill_name': '天下无双', 'skill_description': '造成600%攻击力的毁灭性伤害，无视防御',
         'skill_damage_multiplier': 6.0},
        {'name': '貂蝉', 'rarity': 'UR', 'attack': 480, 'defense': 380, 'hp': 5000,
         'element': '水', 'faction': '群', 'job_class': '谋士',
         'is_golden': True, 'skill_name': '闭月羞花', 'skill_description': '造成550%攻击力的伤害，魅惑敌方全体降低攻击',
         'skill_damage_multiplier': 5.5},
    ]

    for card_data in sample_cards:
        card = Card(**card_data)
        db.session.add(card)

    db.session.commit()
    print(f"已初始化 {len(sample_cards)} 张三国武将卡牌")


def migrate_cards_to_three_kingdoms():
    """将旧版泛用卡牌迁移为三国武将（一次性迁移，检测旧名称触发）"""
    from app.models import Card

    # 旧名称→新数据的映射（按ID顺序对应）
    old_to_new = {
        '新手剑士': {'name': '黄巾力士', 'element': '土', 'faction': '群', 'job_class': '步将',
                   'skill_name': '奋力一击', 'skill_description': '造成150%攻击力的伤害'},
        '见习法师': {'name': '义勇民兵', 'element': '木', 'faction': '群', 'job_class': '弓将',
                   'skill_name': '齐射', 'skill_description': '造成160%攻击力的远程伤害'},
        '乡村猎人': {'name': '游侠剑客', 'element': '金', 'faction': '群', 'job_class': '武将',
                   'skill_name': '剑气斩', 'skill_description': '造成155%攻击力的伤害'},
        '精英骑士': {'name': '张辽', 'element': '金', 'faction': '魏', 'job_class': '骑将',
                   'image_url': '/static/images/cards/zhangliao.png',
                   'skill_name': '突袭', 'skill_description': '造成180%攻击力的伤害，并降低目标防御'},
        '魔法学徒': {'name': '孙策', 'element': '火', 'faction': '吴', 'job_class': '武将',
                   'image_url': '/static/images/cards/sunce.png',
                   'skill_name': '霸王之击', 'skill_description': '造成190%攻击力的伤害'},
        '暗影刺客': {'name': '孙权', 'element': '水', 'faction': '吴', 'job_class': '谋士',
                   'image_url': '/static/images/cards/sunquan.png',
                   'skill_name': '制衡', 'skill_description': '造成170%攻击力的伤害，恢复少量生命'},
        '圣骑士':  {'name': '赵云', 'element': '金', 'faction': '蜀', 'job_class': '骑将',
                   'image_url': '/static/images/cards/zhaoyun.png',
                   'skill_name': '龙胆', 'skill_description': '造成250%攻击力的伤害，无视部分防御'},
        '大魔导师': {'name': '周瑜', 'element': '火', 'faction': '吴', 'job_class': '谋士',
                   'image_url': '/static/images/cards/zhouyu.png',
                   'skill_name': '火攻', 'skill_description': '造成280%攻击力的火焰范围伤害'},
        '龙骑士':  {'name': '诸葛亮', 'element': '火', 'faction': '蜀', 'job_class': '谋士',
                   'image_url': '/static/images/cards/zhugeliang.png',
                   'skill_name': '八阵图', 'skill_description': '造成270%攻击力的伤害，有几率眩晕'},
        '堕落天使': {'name': '关羽', 'element': '金', 'faction': '蜀', 'job_class': '武将',
                   'image_url': '/static/images/cards/guanyu.png',
                   'skill_name': '青龙偃月', 'skill_description': '造成350%攻击力的伤害，斩杀低血量目标'},
        '炎之女皇': {'name': '曹操', 'element': '水', 'faction': '魏', 'job_class': '谋士',
                   'image_url': '/static/images/cards/caocao.png',
                   'skill_name': '奸雄', 'skill_description': '造成320%攻击力的伤害，恢复造成伤害的30%生命'},
        '冰霜女神': {'name': '刘备', 'element': '木', 'faction': '蜀', 'job_class': '武将',
                   'image_url': '/static/images/cards/liubei.png',
                   'skill_name': '仁德', 'skill_description': '造成300%攻击力的伤害，同时恢复全体己方20%生命'},
        '创世神':  {'name': '吕布', 'element': '火', 'faction': '群', 'job_class': '武将',
                   'image_url': '/static/images/cards/lvbu.png',
                   'skill_name': '天下无双', 'skill_description': '造成600%攻击力的毁灭性伤害，无视防御'},
        '混沌之主': {'name': '貂蝉', 'element': '水', 'faction': '群', 'job_class': '谋士',
                   'skill_name': '闭月羞花', 'skill_description': '造成550%攻击力的伤害，魅惑敌方全体降低攻击'},
    }

    # 检测是否需要迁移（看第一张卡是否是旧名称）
    first_card = Card.query.first()
    if not first_card or first_card.name not in old_to_new:
        return  # 已经是新数据或为空

    print("[迁移] 检测到旧版卡牌数据，正在迁移为三国武将...")
    migrated = 0
    for card in Card.query.all():
        new_data = old_to_new.get(card.name)
        if new_data:
            for key, value in new_data.items():
                setattr(card, key, value)
            migrated += 1

    db.session.commit()
    print(f"[迁移] 已将 {migrated} 张卡牌迁移为三国武将")


def init_stages():
    """初始化PVE关卡数据（当Stage表为空时自动创建30个主线关卡）"""
    import json
    from app.models import Stage

    if Stage.query.count() > 0:
        return  # 已有数据，跳过初始化

    print("[初始化] 开始自动创建主线关卡...")

    def _create_stages(chapter, stages_data):
        count = 0
        for sd in stages_data:
            stage = Stage(
                stage_type='main',
                chapter=chapter,
                stage_number=sd['stage_number'],
                name=sd['name'],
                description=sd['description'],
                difficulty=sd.get('difficulty', 'normal'),
                recommended_power=sd['recommended_power'],
                stamina_cost=sd.get('stamina_cost', 10),
                enemy_config=sd['enemy_config'],
                rewards=sd['rewards'],
                drop_config=sd['drop_config'],
                first_clear_rewards=sd['first_clear_rewards'],
                star_1_condition='通关关卡',
                star_2_condition='无人阵亡',
                star_3_condition='10回合内通关',
                unlock_condition=json.dumps({
                    "type": "previous_stage",
                    "stage_number": sd['stage_number'] - 1
                }) if sd['stage_number'] > 1 else None
            )
            db.session.add(stage)
            count += 1
        db.session.commit()
        return count

    total = 0

    # ========== 第1章: 黄巾起义 (1-10关) ==========
    chapter_1 = [
        {
            "stage_number": 1, "name": "黄巾起义·序章",
            "description": "公元184年，黄巾起义爆发，天下大乱。击败黄巾贼兵，开启你的三国征程！",
            "recommended_power": 1000,
            "enemy_config": json.dumps({"enemies": [
                {"level": 5, "card_name": "黄巾贼兵", "position": 1},
                {"level": 5, "card_name": "黄巾贼兵", "position": 2}
            ], "ai_strategy": "aggressive"}),
            "rewards": json.dumps({"coins": {"min": 500, "max": 800}, "exp": 100}),
            "drop_config": json.dumps([{"item_type": "equipment_fragment", "item_subtype": "common", "probability": 0.6, "quantity": [1, 2]}]),
            "first_clear_rewards": json.dumps({"coins": 1000, "tickets": 1, "items": [{"type": "exp_potion", "subtype": "small", "quantity": 2}]})
        },
        {
            "stage_number": 2, "name": "平定乡村",
            "description": "黄巾军攻占了附近的村庄，需要立即出兵平定！",
            "recommended_power": 1200,
            "enemy_config": json.dumps({"enemies": [
                {"level": 6, "card_name": "黄巾贼兵", "position": 1},
                {"level": 6, "card_name": "黄巾贼兵", "position": 2},
                {"level": 5, "card_name": "黄巾弓手", "position": 5}
            ], "ai_strategy": "balanced"}),
            "rewards": json.dumps({"coins": {"min": 600, "max": 900}, "exp": 120}),
            "drop_config": json.dumps([{"item_type": "equipment_fragment", "item_subtype": "common", "probability": 0.6, "quantity": [1, 2]}]),
            "first_clear_rewards": json.dumps({"coins": 1200, "items": [{"type": "exp_potion", "subtype": "small", "quantity": 3}]})
        },
        {
            "stage_number": 3, "name": "黄巾小队",
            "description": "遭遇黄巾军的巡逻小队，必须将其击溃！",
            "recommended_power": 1500,
            "enemy_config": json.dumps({"enemies": [
                {"level": 7, "card_name": "黄巾贼兵", "position": 1},
                {"level": 7, "card_name": "黄巾贼兵", "position": 2},
                {"level": 6, "card_name": "黄巾法师", "position": 4}
            ], "ai_strategy": "defensive"}),
            "rewards": json.dumps({"coins": {"min": 700, "max": 1000}, "exp": 150}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "common", "probability": 0.5, "quantity": [1, 2]},
                {"item_type": "equipment_fragment", "item_subtype": "rare", "probability": 0.3, "quantity": [1, 1]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 1500, "tickets": 1})
        },
        {
            "stage_number": 4, "name": "守卫粮仓",
            "description": "黄巾军意图焚毁粮仓，守住粮仓保障军粮供应！",
            "recommended_power": 1800,
            "enemy_config": json.dumps({"enemies": [
                {"level": 8, "card_name": "黄巾贼兵", "position": 1},
                {"level": 8, "card_name": "黄巾贼兵", "position": 2},
                {"level": 7, "card_name": "黄巾弓手", "position": 5},
                {"level": 7, "card_name": "黄巾法师", "position": 4}
            ], "ai_strategy": "aggressive"}),
            "rewards": json.dumps({"coins": {"min": 800, "max": 1200}, "exp": 180}),
            "drop_config": json.dumps([{"item_type": "equipment_fragment", "item_subtype": "rare", "probability": 0.5, "quantity": [1, 2]}]),
            "first_clear_rewards": json.dumps({"coins": 2000, "items": [{"type": "exp_potion", "subtype": "medium", "quantity": 1}]})
        },
        {
            "stage_number": 5, "name": "反攻据点",
            "description": "主动出击，攻占黄巾军的据点！",
            "recommended_power": 2100,
            "enemy_config": json.dumps({"enemies": [
                {"level": 9, "card_name": "黄巾贼兵", "position": 1},
                {"level": 9, "card_name": "黄巾贼兵", "position": 2},
                {"level": 8, "card_name": "黄巾弓手", "position": 5},
                {"level": 8, "card_name": "黄巾将领", "position": 3}
            ], "ai_strategy": "balanced"}),
            "rewards": json.dumps({"coins": {"min": 1000, "max": 1500}, "exp": 200}),
            "drop_config": json.dumps([{"item_type": "equipment_fragment", "item_subtype": "rare", "probability": 0.6, "quantity": [1, 3]}]),
            "first_clear_rewards": json.dumps({"coins": 2500, "tickets": 2})
        },
        {
            "stage_number": 6, "name": "解救人质",
            "description": "黄巾军劫持了大量村民，迅速营救人质！",
            "recommended_power": 2400,
            "enemy_config": json.dumps({"enemies": [
                {"level": 10, "card_name": "黄巾贼兵", "position": 1},
                {"level": 10, "card_name": "黄巾贼兵", "position": 2},
                {"level": 9, "card_name": "黄巾法师", "position": 4},
                {"level": 9, "card_name": "黄巾将领", "position": 3}
            ], "ai_strategy": "defensive"}),
            "rewards": json.dumps({"coins": {"min": 1200, "max": 1800}, "exp": 250}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "rare", "probability": 0.6, "quantity": [1, 3]},
                {"item_type": "equipment_fragment", "item_subtype": "epic", "probability": 0.2, "quantity": [1, 1]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 3000, "items": [{"type": "exp_potion", "subtype": "medium", "quantity": 2}]})
        },
        {
            "stage_number": 7, "name": "追击残兵",
            "description": "黄巾军溃败，追击残兵以绝后患！",
            "recommended_power": 2700,
            "enemy_config": json.dumps({"enemies": [
                {"level": 11, "card_name": "黄巾贼兵", "position": 1},
                {"level": 11, "card_name": "黄巾弓手", "position": 5},
                {"level": 10, "card_name": "黄巾法师", "position": 4},
                {"level": 10, "card_name": "黄巾将领", "position": 2}
            ], "ai_strategy": "aggressive"}),
            "rewards": json.dumps({"coins": {"min": 1500, "max": 2000}, "exp": 300}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "rare", "probability": 0.5, "quantity": [2, 3]},
                {"item_type": "equipment_fragment", "item_subtype": "epic", "probability": 0.3, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 3500, "tickets": 2})
        },
        {
            "stage_number": 8, "name": "夺回城池",
            "description": "黄巾军占领的城池必须夺回！",
            "recommended_power": 3000,
            "enemy_config": json.dumps({"enemies": [
                {"level": 12, "card_name": "黄巾贼兵", "position": 1},
                {"level": 12, "card_name": "黄巾贼兵", "position": 2},
                {"level": 11, "card_name": "黄巾弓手", "position": 5},
                {"level": 11, "card_name": "黄巾法师", "position": 4},
                {"level": 11, "card_name": "黄巾将领", "position": 3}
            ], "ai_strategy": "balanced"}),
            "rewards": json.dumps({"coins": {"min": 2000, "max": 2500}, "exp": 350}),
            "drop_config": json.dumps([{"item_type": "equipment_fragment", "item_subtype": "epic", "probability": 0.5, "quantity": [1, 2]}]),
            "first_clear_rewards": json.dumps({"coins": 4000, "items": [{"type": "exp_potion", "subtype": "medium", "quantity": 3}]})
        },
        {
            "stage_number": 9, "name": "张梁的挑战",
            "description": "黄巾军地公将军张梁率军迎战，这将是一场恶战！",
            "recommended_power": 3500,
            "enemy_config": json.dumps({"enemies": [
                {"level": 15, "card_name": "张梁", "position": 3},
                {"level": 13, "card_name": "黄巾贼兵", "position": 1},
                {"level": 13, "card_name": "黄巾贼兵", "position": 2},
                {"level": 12, "card_name": "黄巾法师", "position": 4},
                {"level": 12, "card_name": "黄巾弓手", "position": 5}
            ], "ai_strategy": "aggressive"}),
            "rewards": json.dumps({"coins": {"min": 2500, "max": 3000}, "exp": 400}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "epic", "probability": 0.6, "quantity": [1, 3]},
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.1, "quantity": [1, 1]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 5000, "tickets": 3, "items": [{"type": "exp_potion", "subtype": "large", "quantity": 1}]})
        },
        {
            "stage_number": 10, "name": "击败张角",
            "description": "黄巾军首领张角现身！击败他即可平定黄巾之乱！",
            "recommended_power": 4000, "difficulty": "boss", "stamina_cost": 15,
            "enemy_config": json.dumps({"enemies": [
                {"level": 18, "card_name": "张角", "position": 3, "is_boss": True},
                {"level": 14, "card_name": "张梁", "position": 2},
                {"level": 13, "card_name": "黄巾将领", "position": 1},
                {"level": 13, "card_name": "黄巾法师", "position": 4},
                {"level": 13, "card_name": "黄巾法师", "position": 5}
            ], "ai_strategy": "balanced"}),
            "rewards": json.dumps({"coins": {"min": 3000, "max": 4000}, "exp": 500}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "epic", "probability": 0.7, "quantity": [2, 4]},
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.2, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 10000, "tickets": 5, "items": [
                {"type": "exp_potion", "subtype": "large", "quantity": 3},
                {"type": "skill_book", "subtype": "common", "quantity": 1}
            ]})
        }
    ]
    total += _create_stages(1, chapter_1)

    # ========== 第2章: 董卓之乱 (11-20关) ==========
    chapter_2 = [
        {
            "stage_number": 11, "name": "董卓之乱·开端",
            "description": "董卓废少帝，立献帝，把持朝政，天下诸侯不服！",
            "recommended_power": 4500,
            "enemy_config": json.dumps({"enemies": [
                {"level": 15, "card_name": "董卓军士", "position": 1},
                {"level": 15, "card_name": "董卓军士", "position": 2},
                {"level": 14, "card_name": "董卓弓手", "position": 5}
            ], "ai_strategy": "aggressive"}),
            "rewards": json.dumps({"coins": {"min": 3500, "max": 4500}, "exp": 600}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "epic", "probability": 0.6, "quantity": [1, 3]},
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.2, "quantity": [1, 1]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 5000, "tickets": 2, "items": [{"type": "exp_potion", "subtype": "large", "quantity": 2}]})
        },
        {
            "stage_number": 12, "name": "洛阳之战",
            "description": "董卓驻军洛阳，需要攻破其防线！",
            "recommended_power": 5000,
            "enemy_config": json.dumps({"enemies": [
                {"level": 16, "card_name": "董卓军士", "position": 1},
                {"level": 16, "card_name": "董卓军士", "position": 2},
                {"level": 15, "card_name": "董卓弓手", "position": 5},
                {"level": 15, "card_name": "董卓将领", "position": 3}
            ], "ai_strategy": "defensive"}),
            "rewards": json.dumps({"coins": {"min": 4000, "max": 5000}, "exp": 700}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "epic", "probability": 0.6, "quantity": [2, 3]},
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.3, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 6000, "items": [{"type": "skill_book", "subtype": "common", "quantity": 1}]})
        },
        {
            "stage_number": 13, "name": "虎牢关前",
            "description": "虎牢关乃天下雄关，必须攻克此关！",
            "recommended_power": 5500,
            "enemy_config": json.dumps({"enemies": [
                {"level": 17, "card_name": "董卓军士", "position": 1},
                {"level": 17, "card_name": "董卓军士", "position": 2},
                {"level": 16, "card_name": "董卓将领", "position": 3},
                {"level": 16, "card_name": "董卓弓手", "position": 5},
                {"level": 16, "card_name": "董卓法师", "position": 4}
            ], "ai_strategy": "balanced"}),
            "rewards": json.dumps({"coins": {"min": 4500, "max": 5500}, "exp": 800}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "epic", "probability": 0.5, "quantity": [2, 4]},
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.4, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 7000, "tickets": 3})
        },
        {
            "stage_number": 14, "name": "华雄的威胁",
            "description": "董卓麾下猛将华雄守关，连斩数将！",
            "recommended_power": 6000,
            "enemy_config": json.dumps({"enemies": [
                {"level": 20, "card_name": "华雄", "position": 3},
                {"level": 18, "card_name": "董卓军士", "position": 1},
                {"level": 18, "card_name": "董卓军士", "position": 2},
                {"level": 17, "card_name": "董卓弓手", "position": 5}
            ], "ai_strategy": "aggressive"}),
            "rewards": json.dumps({"coins": {"min": 5000, "max": 6000}, "exp": 900}),
            "drop_config": json.dumps([{"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.5, "quantity": [1, 3]}]),
            "first_clear_rewards": json.dumps({"coins": 8000, "tickets": 3, "items": [{"type": "exp_potion", "subtype": "large", "quantity": 3}]})
        },
        {
            "stage_number": 15, "name": "温酒斩华雄",
            "description": "关羽请缨出战，温酒未冷，已斩华雄而归！",
            "recommended_power": 6500,
            "enemy_config": json.dumps({"enemies": [
                {"level": 22, "card_name": "华雄", "position": 3, "is_boss": True},
                {"level": 19, "card_name": "董卓将领", "position": 1},
                {"level": 19, "card_name": "董卓将领", "position": 2},
                {"level": 18, "card_name": "董卓法师", "position": 4},
                {"level": 18, "card_name": "董卓弓手", "position": 5}
            ], "ai_strategy": "balanced"}),
            "rewards": json.dumps({"coins": {"min": 5500, "max": 6500}, "exp": 1000}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.6, "quantity": [1, 3]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.05, "quantity": [1, 1]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 10000, "tickets": 4, "items": [{"type": "skill_book", "subtype": "rare", "quantity": 1}]})
        },
        {
            "stage_number": 16, "name": "进军长安",
            "description": "华雄已败，继续进军长安！",
            "recommended_power": 7000,
            "enemy_config": json.dumps({"enemies": [
                {"level": 20, "card_name": "董卓军士", "position": 1},
                {"level": 20, "card_name": "董卓军士", "position": 2},
                {"level": 19, "card_name": "董卓将领", "position": 3},
                {"level": 19, "card_name": "董卓法师", "position": 4}
            ], "ai_strategy": "defensive"}),
            "rewards": json.dumps({"coins": {"min": 6000, "max": 7000}, "exp": 1100}),
            "drop_config": json.dumps([{"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.6, "quantity": [2, 3]}]),
            "first_clear_rewards": json.dumps({"coins": 8000, "items": [{"type": "exp_potion", "subtype": "large", "quantity": 4}]})
        },
        {
            "stage_number": 17, "name": "李傕郭汜",
            "description": "董卓手下猛将李傕、郭汜率军阻拦！",
            "recommended_power": 7500,
            "enemy_config": json.dumps({"enemies": [
                {"level": 23, "card_name": "李傕", "position": 2},
                {"level": 23, "card_name": "郭汜", "position": 3},
                {"level": 21, "card_name": "董卓军士", "position": 1},
                {"level": 20, "card_name": "董卓弓手", "position": 5},
                {"level": 20, "card_name": "董卓法师", "position": 4}
            ], "ai_strategy": "aggressive"}),
            "rewards": json.dumps({"coins": {"min": 6500, "max": 7500}, "exp": 1200}),
            "drop_config": json.dumps([{"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.7, "quantity": [2, 4]}]),
            "first_clear_rewards": json.dumps({"coins": 9000, "tickets": 4})
        },
        {
            "stage_number": 18, "name": "貂蝉连环计",
            "description": "王允使连环计，吕布与董卓生隙！",
            "recommended_power": 8000,
            "enemy_config": json.dumps({"enemies": [
                {"level": 22, "card_name": "董卓军士", "position": 1},
                {"level": 22, "card_name": "董卓军士", "position": 2},
                {"level": 21, "card_name": "董卓将领", "position": 3},
                {"level": 21, "card_name": "董卓法师", "position": 4},
                {"level": 21, "card_name": "董卓弓手", "position": 5}
            ], "ai_strategy": "balanced"}),
            "rewards": json.dumps({"coins": {"min": 7000, "max": 8000}, "exp": 1300}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.7, "quantity": [2, 4]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.1, "quantity": [1, 1]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 10000, "items": [{"type": "skill_book", "subtype": "rare", "quantity": 2}]})
        },
        {
            "stage_number": 19, "name": "凤仪亭对决",
            "description": "吕布与董卓决裂，在凤仪亭展开激战！",
            "recommended_power": 8500,
            "enemy_config": json.dumps({"enemies": [
                {"level": 25, "card_name": "董卓", "position": 3},
                {"level": 23, "card_name": "李傕", "position": 1},
                {"level": 23, "card_name": "郭汜", "position": 2},
                {"level": 22, "card_name": "董卓法师", "position": 4},
                {"level": 22, "card_name": "董卓法师", "position": 5}
            ], "ai_strategy": "defensive"}),
            "rewards": json.dumps({"coins": {"min": 7500, "max": 8500}, "exp": 1400}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.8, "quantity": [2, 5]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.15, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 12000, "tickets": 5, "items": [{"type": "exp_potion", "subtype": "large", "quantity": 5}]})
        },
        {
            "stage_number": 20, "name": "董卓之死",
            "description": "吕布刺杀董卓，董卓之乱终于平定！",
            "recommended_power": 9000, "difficulty": "boss", "stamina_cost": 15,
            "enemy_config": json.dumps({"enemies": [
                {"level": 28, "card_name": "董卓", "position": 3, "is_boss": True},
                {"level": 24, "card_name": "李傕", "position": 1},
                {"level": 24, "card_name": "郭汜", "position": 2},
                {"level": 23, "card_name": "董卓将领", "position": 4},
                {"level": 23, "card_name": "董卓法师", "position": 5}
            ], "ai_strategy": "aggressive"}),
            "rewards": json.dumps({"coins": {"min": 8000, "max": 10000}, "exp": 1500}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.8, "quantity": [3, 5]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.2, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 15000, "tickets": 8, "items": [
                {"type": "exp_potion", "subtype": "large", "quantity": 5},
                {"type": "skill_book", "subtype": "epic", "quantity": 1}
            ]})
        }
    ]
    total += _create_stages(2, chapter_2)

    # ========== 第3章: 群雄割据 (21-30关) ==========
    chapter_3 = [
        {
            "stage_number": 21, "name": "群雄割据·序幕",
            "description": "董卓已死，各路诸侯开始争夺天下！",
            "recommended_power": 9500,
            "enemy_config": json.dumps({"enemies": [
                {"level": 25, "card_name": "诸侯军士", "position": 1},
                {"level": 25, "card_name": "诸侯军士", "position": 2},
                {"level": 24, "card_name": "诸侯弓手", "position": 5}
            ], "ai_strategy": "balanced"}),
            "rewards": json.dumps({"coins": {"min": 8500, "max": 9500}, "exp": 1600}),
            "drop_config": json.dumps([{"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.7, "quantity": [2, 4]}]),
            "first_clear_rewards": json.dumps({"coins": 10000, "tickets": 3})
        },
        {
            "stage_number": 22, "name": "袁绍起兵",
            "description": "袁绍自命盟主，起兵讨伐不臣！",
            "recommended_power": 10000,
            "enemy_config": json.dumps({"enemies": [
                {"level": 26, "card_name": "袁绍军士", "position": 1},
                {"level": 26, "card_name": "袁绍军士", "position": 2},
                {"level": 25, "card_name": "袁绍弓手", "position": 5},
                {"level": 25, "card_name": "袁绍将领", "position": 3}
            ], "ai_strategy": "aggressive"}),
            "rewards": json.dumps({"coins": {"min": 9000, "max": 10000}, "exp": 1700}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.7, "quantity": [2, 4]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.15, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 11000, "items": [{"type": "exp_potion", "subtype": "large", "quantity": 5}]})
        },
        {
            "stage_number": 23, "name": "吕布之威",
            "description": "飞将吕布横扫千军，无人能敌！",
            "recommended_power": 10500,
            "enemy_config": json.dumps({"enemies": [
                {"level": 30, "card_name": "吕布", "position": 3},
                {"level": 27, "card_name": "高顺", "position": 1},
                {"level": 26, "card_name": "张辽", "position": 2},
                {"level": 26, "card_name": "吕布军弓手", "position": 5}
            ], "ai_strategy": "aggressive"}),
            "rewards": json.dumps({"coins": {"min": 9500, "max": 10500}, "exp": 1800}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.8, "quantity": [3, 5]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.2, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 12000, "tickets": 4})
        },
        {
            "stage_number": 24, "name": "曹操东征",
            "description": "曹操起兵，挟天子以令诸侯！",
            "recommended_power": 11000,
            "enemy_config": json.dumps({"enemies": [
                {"level": 28, "card_name": "曹操军士", "position": 1},
                {"level": 28, "card_name": "曹操军士", "position": 2},
                {"level": 27, "card_name": "曹操将领", "position": 3},
                {"level": 27, "card_name": "曹操法师", "position": 4},
                {"level": 27, "card_name": "曹操弓手", "position": 5}
            ], "ai_strategy": "balanced"}),
            "rewards": json.dumps({"coins": {"min": 10000, "max": 11000}, "exp": 1900}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.8, "quantity": [3, 5]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.2, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 13000, "items": [{"type": "skill_book", "subtype": "epic", "quantity": 1}]})
        },
        {
            "stage_number": 25, "name": "刘备起势",
            "description": "刘皇叔招贤纳士，麾下猛将云集！",
            "recommended_power": 11500,
            "enemy_config": json.dumps({"enemies": [
                {"level": 29, "card_name": "关羽", "position": 1},
                {"level": 29, "card_name": "张飞", "position": 2},
                {"level": 28, "card_name": "赵云", "position": 3},
                {"level": 28, "card_name": "刘备军弓手", "position": 5}
            ], "ai_strategy": "defensive"}),
            "rewards": json.dumps({"coins": {"min": 10500, "max": 11500}, "exp": 2000}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.8, "quantity": [3, 5]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.25, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 14000, "tickets": 5})
        },
        {
            "stage_number": 26, "name": "孙策平江东",
            "description": "小霸王孙策横扫江东，建立基业！",
            "recommended_power": 12000,
            "enemy_config": json.dumps({"enemies": [
                {"level": 30, "card_name": "孙策", "position": 3},
                {"level": 29, "card_name": "周瑜", "position": 2},
                {"level": 29, "card_name": "太史慈", "position": 1},
                {"level": 28, "card_name": "东吴弓手", "position": 5},
                {"level": 28, "card_name": "东吴法师", "position": 4}
            ], "ai_strategy": "aggressive"}),
            "rewards": json.dumps({"coins": {"min": 11000, "max": 12000}, "exp": 2100}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.8, "quantity": [3, 6]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.3, "quantity": [1, 3]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 15000, "items": [{"type": "exp_potion", "subtype": "large", "quantity": 6}]})
        },
        {
            "stage_number": 27, "name": "白马之战",
            "description": "关羽斩颜良诛文丑，威震华夏！",
            "recommended_power": 12500,
            "enemy_config": json.dumps({"enemies": [
                {"level": 32, "card_name": "颜良", "position": 2},
                {"level": 32, "card_name": "文丑", "position": 3},
                {"level": 30, "card_name": "袁绍军士", "position": 1},
                {"level": 29, "card_name": "袁绍弓手", "position": 5},
                {"level": 29, "card_name": "袁绍法师", "position": 4}
            ], "ai_strategy": "aggressive"}),
            "rewards": json.dumps({"coins": {"min": 11500, "max": 12500}, "exp": 2200}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.9, "quantity": [4, 6]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.3, "quantity": [1, 3]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 16000, "tickets": 5})
        },
        {
            "stage_number": 28, "name": "徐州之战",
            "description": "曹操攻打徐州，吕布趁机夺取兖州！",
            "recommended_power": 13000,
            "enemy_config": json.dumps({"enemies": [
                {"level": 33, "card_name": "吕布", "position": 3},
                {"level": 31, "card_name": "高顺", "position": 1},
                {"level": 31, "card_name": "张辽", "position": 2},
                {"level": 30, "card_name": "陈宫", "position": 4},
                {"level": 30, "card_name": "吕布军弓手", "position": 5}
            ], "ai_strategy": "balanced"}),
            "rewards": json.dumps({"coins": {"min": 12000, "max": 13000}, "exp": 2300}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.9, "quantity": [4, 6]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.35, "quantity": [1, 3]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 17000, "items": [{"type": "skill_book", "subtype": "epic", "quantity": 2}]})
        },
        {
            "stage_number": 29, "name": "下邳围城",
            "description": "曹操围困下邳，吕布陷入绝境！",
            "recommended_power": 13500,
            "enemy_config": json.dumps({"enemies": [
                {"level": 35, "card_name": "吕布", "position": 3},
                {"level": 32, "card_name": "高顺", "position": 1},
                {"level": 32, "card_name": "张辽", "position": 2},
                {"level": 31, "card_name": "陈宫", "position": 4},
                {"level": 31, "card_name": "吕布军法师", "position": 5}
            ], "ai_strategy": "defensive"}),
            "rewards": json.dumps({"coins": {"min": 12500, "max": 13500}, "exp": 2400}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.9, "quantity": [4, 7]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.4, "quantity": [1, 3]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 18000, "tickets": 6})
        },
        {
            "stage_number": 30, "name": "白门楼之殇",
            "description": "吕布兵败被俘，在白门楼被处死，群雄割据时代落幕！",
            "recommended_power": 14000, "difficulty": "boss", "stamina_cost": 15,
            "enemy_config": json.dumps({"enemies": [
                {"level": 38, "card_name": "吕布", "position": 3, "is_boss": True},
                {"level": 33, "card_name": "高顺", "position": 1},
                {"level": 33, "card_name": "张辽", "position": 2},
                {"level": 32, "card_name": "陈宫", "position": 4},
                {"level": 32, "card_name": "貂蝉", "position": 5}
            ], "ai_strategy": "aggressive"}),
            "rewards": json.dumps({"coins": {"min": 13000, "max": 15000}, "exp": 2500}),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 1.0, "quantity": [5, 8]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.5, "quantity": [2, 4]}
            ]),
            "first_clear_rewards": json.dumps({"coins": 20000, "tickets": 10, "items": [
                {"type": "exp_potion", "subtype": "large", "quantity": 10},
                {"type": "skill_book", "subtype": "legendary", "quantity": 1}
            ]})
        }
    ]
    total += _create_stages(3, chapter_3)

    print(f"[初始化] 已自动创建 {total} 个主线关卡")
