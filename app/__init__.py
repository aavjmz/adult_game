import os

from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix

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

    # 置于 nginx/Caddy 之后时，读取 X-Forwarded-* 还原真实协议与客户端IP，
    # 否则 HTTPS 下 url_for(_external=True) 和重定向会生成 http:// 地址。
    #
    # 必须由环境变量显式开启：直连暴露时信任这些头等于让客户端随意伪造
    # 来源IP和协议。仅在确实有反向代理时设置 BEHIND_PROXY=true。
    if os.environ.get('BEHIND_PROXY', '').lower() in ('1', 'true', 'yes'):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # 配置CORS（Cocos客户端跨域访问 /api/*）
    # 客户端走Bearer Token而非Cookie，因此不开启credentials：
    # 浏览器规范禁止 Access-Control-Allow-Origin: * 与凭证同时使用。
    CORS(app,
         resources={r"/api/*": {"origins": "*"}},
         supports_credentials=False,
         allow_headers=["Content-Type", "Authorization"])

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)

    # 注册蓝图
    from app.routes import (auth, cards, gacha, battle, battle_v2, growth,
                            equipment, main, pve, pve_frontend, api_client)
    app.register_blueprint(auth.bp)
    app.register_blueprint(api_client.bp)
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
        migrate_card_enemy_flag()
        init_cards()
        migrate_cards_to_three_kingdoms()
        init_stages()

    return app

def migrate_card_enemy_flag():
    """给 cards 表补 is_enemy 列，并把已入库的敌军卡标出来（幂等）

    db.create_all() 不会给已有表加列；这一列又被每次查询 Card 用到，
    缺了整个应用都起不来，所以放在启动时自动补，而不是另写手动迁移脚本。
    """
    from sqlalchemy import inspect, text
    from app.models import Card
    from app.enemy_cards import ENEMY_ONLY_NAMES

    columns = {c['name'] for c in inspect(db.engine).get_columns('cards')}
    if 'is_enemy' not in columns:
        db.session.execute(text('ALTER TABLE cards ADD COLUMN is_enemy BOOLEAN NOT NULL DEFAULT FALSE'))
        db.session.commit()
        print('[迁移] cards 表已添加 is_enemy 列')

    # 早先跑过 init_enemy_cards.py 的库里，敌军卡还混在卡池中
    marked = Card.query.filter(Card.name.in_(ENEMY_ONLY_NAMES), Card.is_enemy.is_(False)) \
        .update({Card.is_enemy: True}, synchronize_session=False)
    if marked:
        db.session.commit()
        print(f'[迁移] 已将 {marked} 张敌军卡移出招贤卡池')


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
    """关卡表为空时自动建出主线关卡；数据定义在 app/stage_data.py

    已有关卡时不动——改了关卡数值要手动跑 init_stages.py 同步，
    避免每次启动都悄悄改线上数据。
    """
    from app.models import Stage
    from app.stage_data import sync_main_stages

    if Stage.query.count() > 0:
        return  # 已有数据，跳过初始化

    print("[初始化] 开始自动创建主线关卡...")
    counts = sync_main_stages(verbose=False)
    print(f"[初始化] 已自动创建 {counts['added']} 个主线关卡")
