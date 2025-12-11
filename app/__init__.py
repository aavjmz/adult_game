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
    from app.routes import auth, cards, gacha, battle, battle_v2, growth, equipment, main, pve
    app.register_blueprint(auth.bp)
    app.register_blueprint(cards.bp)
    app.register_blueprint(gacha.bp)
    app.register_blueprint(battle.bp)
    app.register_blueprint(battle_v2.bp)
    app.register_blueprint(growth.bp)
    app.register_blueprint(equipment.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(pve.pve_bp)

    # 创建数据库表
    with app.app_context():
        db.create_all()
        init_cards()

    return app

def init_cards():
    """初始化卡牌数据"""
    from app.models import Card

    if Card.query.count() > 0:
        return  # 已有数据，跳过初始化

    # 示例卡牌数据
    sample_cards = [
        # N卡
        {'name': '新手剑士', 'rarity': 'N', 'attack': 80, 'defense': 60, 'hp': 800,
         'is_golden': False, 'skill_name': '普通斩击', 'skill_description': '造成150%攻击力的伤害'},
        {'name': '见习法师', 'rarity': 'N', 'attack': 70, 'defense': 50, 'hp': 700,
         'is_golden': False, 'skill_name': '火球术', 'skill_description': '造成160%攻击力的魔法伤害'},
        {'name': '乡村猎人', 'rarity': 'N', 'attack': 75, 'defense': 55, 'hp': 750,
         'is_golden': False, 'skill_name': '精准射击', 'skill_description': '造成155%攻击力的伤害'},

        # R卡
        {'name': '精英骑士', 'rarity': 'R', 'attack': 120, 'defense': 100, 'hp': 1200,
         'is_golden': False, 'skill_name': '冲锋', 'skill_description': '造成180%攻击力的伤害'},
        {'name': '魔法学徒', 'rarity': 'R', 'attack': 110, 'defense': 90, 'hp': 1100,
         'is_golden': False, 'skill_name': '冰霜箭', 'skill_description': '造成190%攻击力的冰冻伤害'},
        {'name': '暗影刺客', 'rarity': 'R', 'attack': 130, 'defense': 80, 'hp': 1000,
         'is_golden': False, 'skill_name': '背刺', 'skill_description': '造成200%攻击力的暴击伤害'},

        # SR卡
        {'name': '圣骑士', 'rarity': 'SR', 'attack': 180, 'defense': 150, 'hp': 1800,
         'is_golden': False, 'skill_name': '圣光审判', 'skill_description': '造成250%攻击力的神圣伤害'},
        {'name': '大魔导师', 'rarity': 'SR', 'attack': 200, 'defense': 120, 'hp': 1600,
         'is_golden': False, 'skill_name': '奥术轰炸', 'skill_description': '造成280%攻击力的范围伤害'},
        {'name': '龙骑士', 'rarity': 'SR', 'attack': 190, 'defense': 140, 'hp': 1700,
         'is_golden': False, 'skill_name': '龙之吐息', 'skill_description': '造成270%攻击力的火焰伤害'},

        # SSR卡（金色卡牌）
        {'name': '堕落天使', 'rarity': 'SSR', 'attack': 280, 'defense': 200, 'hp': 2500,
         'is_golden': True, 'skill_name': '暗黑审判', 'skill_description': '造成350%攻击力的暗黑伤害', 'skill_damage_multiplier': 3.5},
        {'name': '炎之女皇', 'rarity': 'SSR', 'attack': 300, 'defense': 180, 'hp': 2400,
         'is_golden': True, 'skill_name': '业火焚天', 'skill_description': '造成400%攻击力的终极火焰伤害', 'skill_damage_multiplier': 4.0},
        {'name': '冰霜女神', 'rarity': 'SSR', 'attack': 290, 'defense': 190, 'hp': 2450,
         'is_golden': True, 'skill_name': '极寒冰封', 'skill_description': '造成380%攻击力的冰冻伤害', 'skill_damage_multiplier': 3.8},

        # UR卡（金色卡牌）
        {'name': '创世神', 'rarity': 'UR', 'attack': 500, 'defense': 400, 'hp': 5000,
         'is_golden': True, 'skill_name': '创世之光', 'skill_description': '造成600%攻击力的毁灭性伤害', 'skill_damage_multiplier': 6.0},
        {'name': '混沌之主', 'rarity': 'UR', 'attack': 520, 'defense': 380, 'hp': 4800,
         'is_golden': True, 'skill_name': '混沌湮灭', 'skill_description': '造成650%攻击力的混沌伤害', 'skill_damage_multiplier': 6.5},
    ]

    for card_data in sample_cards:
        card = Card(**card_data)
        db.session.add(card)

    db.session.commit()
    print(f"已初始化 {len(sample_cards)} 张卡牌")
