from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # 游戏资源
    tickets = db.Column(db.Integer, default=10)  # 抽卡券
    coins = db.Column(db.Integer, default=1000)  # 游戏币

    # 抽卡保底计数
    sr_pity_count = db.Column(db.Integer, default=0)   # SR保底计数
    ssr_pity_count = db.Column(db.Integer, default=0)  # SSR保底计数

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    user_cards = db.relationship('UserCard', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    gacha_records = db.relationship('GachaRecord', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Card(db.Model):
    """卡牌模型"""
    __tablename__ = 'cards'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rarity = db.Column(db.String(10), nullable=False)  # N, R, SR, SSR, UR

    # 卡牌属性
    attack = db.Column(db.Integer, default=100)
    defense = db.Column(db.Integer, default=100)
    hp = db.Column(db.Integer, default=1000)

    # 视觉效果
    is_golden = db.Column(db.Boolean, default=False)  # 是否为金色卡牌（3D动态效果）
    image_url = db.Column(db.String(200))
    description = db.Column(db.Text)

    # 技能
    skill_name = db.Column(db.String(100))
    skill_description = db.Column(db.Text)
    skill_damage_multiplier = db.Column(db.Float, default=1.5)
    skill_cooldown = db.Column(db.Integer, default=3)
    skill_target = db.Column(db.String(20), default='single')  # single, all

    # 被动技能
    passive_skill_name = db.Column(db.String(100))
    passive_skill_description = db.Column(db.Text)

    # 增强战斗属性
    speed = db.Column(db.Integer, default=50)
    critical = db.Column(db.Float, default=5.0)
    critical_dmg = db.Column(db.Float, default=150.0)
    element = db.Column(db.String(10), default='无')  # 火、水、雷、风、光、暗、无
    job_class = db.Column(db.String(20), default='战士')  # 战士、法师、刺客、坦克、辅助

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    user_cards = db.relationship('UserCard', backref='card', lazy='dynamic')

    def __repr__(self):
        return f'<Card {self.name} ({self.rarity})>'


class UserCard(db.Model):
    """用户拥有的卡牌"""
    __tablename__ = 'user_cards'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id'), nullable=False)

    # 卡牌强化
    level = db.Column(db.Integer, default=1)
    exp = db.Column(db.Integer, default=0)

    obtained_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserCard user={self.user_id} card={self.card_id}>'


class GachaRecord(db.Model):
    """抽卡记录"""
    __tablename__ = 'gacha_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id'), nullable=False)

    is_multi_pull = db.Column(db.Boolean, default=False)  # 是否为十连抽
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    card = db.relationship('Card', backref='gacha_records')

    def __repr__(self):
        return f'<GachaRecord user={self.user_id} card={self.card_id}>'


class Battle(db.Model):
    """战斗记录"""
    __tablename__ = 'battles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 战斗配置
    player_card_ids = db.Column(db.String(200))  # 逗号分隔的卡牌ID
    enemy_card_ids = db.Column(db.String(200))   # 敌方卡牌ID

    # 战斗结果
    is_victory = db.Column(db.Boolean)
    rewards_coins = db.Column(db.Integer, default=0)
    rewards_tickets = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    user = db.relationship('User', backref='battles')

    def __repr__(self):
        return f'<Battle {self.id} user={self.user_id}>'
