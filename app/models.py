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
    gems = db.Column(db.Integer, default=0)  # 宝石（高级货币）

    # 抽卡保底计数
    sr_pity_count = db.Column(db.Integer, default=0)   # SR保底计数
    ssr_pity_count = db.Column(db.Integer, default=0)  # SSR保底计数

    # PVE体力系统
    stamina = db.Column(db.Integer, default=120)  # 当前体力
    max_stamina = db.Column(db.Integer, default=120)  # 最大体力
    stamina_updated_at = db.Column(db.DateTime, default=datetime.utcnow)  # 体力更新时间

    # PVE进度
    main_stage_progress = db.Column(db.Integer, default=0)  # 主线关卡进度

    # PVE统计数据
    total_pve_battles = db.Column(db.Integer, default=0)  # 总PVE战斗次数
    total_pve_wins = db.Column(db.Integer, default=0)  # 总PVE胜利次数

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    user_cards = db.relationship('UserCard', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    gacha_records = db.relationship('GachaRecord', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    stage_progress = db.relationship('UserStageProgress', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    battle_records = db.relationship('BattleRecord', backref='user', lazy='dynamic', cascade='all, delete-orphan')

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
    element = db.Column(db.String(10), default='无')  # 金、木、水、火、土、无（五行）
    job_class = db.Column(db.String(20), default='武将')  # 武将、谋士、弓将、骑将、步将
    faction = db.Column(db.String(10), default='群')  # 魏、蜀、吴、群（势力）

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

    # 成长系统
    star_level = db.Column(db.Integer, default=1)
    awaken_level = db.Column(db.Integer, default=0)
    breakthrough_level = db.Column(db.Integer, default=0)
    main_skill_level = db.Column(db.Integer, default=1)
    passive_skill_level = db.Column(db.Integer, default=1)

    obtained_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    equipments = db.relationship('Equipment', backref='owner_card', lazy='dynamic', cascade='all, delete-orphan')

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


class Equipment(db.Model):
    """装备模型"""
    __tablename__ = 'equipments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner_card_id = db.Column(db.Integer, db.ForeignKey('user_cards.id'))

    # 关联装备模板（新系统）
    template_id = db.Column(db.Integer, db.ForeignKey('equipment_templates.id'))

    # 旧字段（向后兼容）
    name = db.Column(db.String(100))
    type = db.Column(db.String(20))  # weapon/armor/accessory/treasure
    quality = db.Column(db.String(20))  # common/rare/epic/legendary/mythic
    base_stat_type = db.Column(db.String(20))  # attack/defense/hp
    base_stat_value = db.Column(db.Float)

    # 强化等级
    enhance_level = db.Column(db.Integer, default=0)

    # 随机附加属性（JSON格式）
    random_stats = db.Column(db.Text)

    # 是否锁定
    is_locked = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    user = db.relationship('User', backref='equipments')
    template = db.relationship('EquipmentTemplate', backref='instances')
    stats = db.relationship('EquipmentStat', backref='equipment', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        if self.template:
            return f'<Equipment {self.template.name} +{self.enhance_level}>'
        return f'<Equipment {self.name} ({self.quality})>'


class EquipmentStat(db.Model):
    """装备附加属性"""
    __tablename__ = 'equipment_stats'

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipments.id'), nullable=False)

    stat_type = db.Column(db.String(20), nullable=False)  # crit_rate/crit_dmg/speed/etc
    stat_value = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<EquipmentStat {self.stat_type}={self.stat_value}>'


class UserItem(db.Model):
    """用户材料物品"""
    __tablename__ = 'user_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    item_type = db.Column(db.String(50), nullable=False)  # exp_potion/skill_book/star_stone/etc
    item_subtype = db.Column(db.String(50))  # small/medium/large, warrior/mage/etc
    quantity = db.Column(db.Integer, default=0)

    # 关系
    user = db.relationship('User', backref='items')

    def __repr__(self):
        return f'<UserItem user={self.user_id} {self.item_type}:{self.item_subtype} x{self.quantity}>'


class EquipmentSet(db.Model):
    """套装配置表"""
    __tablename__ = 'equipment_sets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    name_en = db.Column(db.String(100))  # 英文名

    # 2件套加成
    bonus_2_desc = db.Column(db.String(200))
    bonus_2_attack_pct = db.Column(db.Float, default=0)
    bonus_2_defense_pct = db.Column(db.Float, default=0)
    bonus_2_hp_pct = db.Column(db.Float, default=0)
    bonus_2_crit_rate = db.Column(db.Float, default=0)
    bonus_2_crit_dmg = db.Column(db.Float, default=0)
    bonus_2_speed = db.Column(db.Integer, default=0)

    # 4件套加成
    bonus_4_desc = db.Column(db.String(200))
    bonus_4_attack_pct = db.Column(db.Float, default=0)
    bonus_4_defense_pct = db.Column(db.Float, default=0)
    bonus_4_hp_pct = db.Column(db.Float, default=0)
    bonus_4_crit_rate = db.Column(db.Float, default=0)
    bonus_4_crit_dmg = db.Column(db.Float, default=0)
    bonus_4_speed = db.Column(db.Integer, default=0)

    # 4件套特殊效果
    bonus_4_special_effect = db.Column(db.String(100))
    bonus_4_special_desc = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联的装备模板
    templates = db.relationship('EquipmentTemplate', backref='equipment_set', lazy='dynamic')

    def __repr__(self):
        return f'<EquipmentSet {self.name}>'


class EquipmentTemplate(db.Model):
    """装备模板表"""
    __tablename__ = 'equipment_templates'

    id = db.Column(db.Integer, primary_key=True)

    # 基础信息
    name = db.Column(db.String(100), nullable=False, unique=True)
    name_en = db.Column(db.String(100))  # 英文名，用于资源路径
    type = db.Column(db.String(20), nullable=False)  # weapon/armor/accessory/treasure
    quality = db.Column(db.String(20), nullable=False)  # common/rare/epic/legendary/mythic
    element = db.Column(db.String(10), default='无')  # 金/木/水/火/土/无

    # 基础属性加成（百分比）
    base_attack_pct = db.Column(db.Float, default=0)
    base_defense_pct = db.Column(db.Float, default=0)
    base_hp_pct = db.Column(db.Float, default=0)

    # 固定数值属性
    crit_rate = db.Column(db.Float, default=0)  # 暴击率%
    crit_dmg = db.Column(db.Float, default=0)  # 暴击伤害%
    speed = db.Column(db.Integer, default=0)  # 速度
    penetration = db.Column(db.Float, default=0)  # 穿透%
    block_rate = db.Column(db.Float, default=0)  # 格挡率%
    dodge_rate = db.Column(db.Float, default=0)  # 闪避率%
    lifesteal = db.Column(db.Float, default=0)  # 吸血%

    # 专属信息
    exclusive_hero_id = db.Column(db.Integer)  # 专属武将ID
    exclusive_faction = db.Column(db.String(10))  # 专属势力

    # 专属效果
    exclusive_effect_name = db.Column(db.String(100))
    exclusive_effect_desc = db.Column(db.Text)
    exclusive_effect_type = db.Column(db.String(50))  # passive/on_attack/on_hit等
    exclusive_effect_value = db.Column(db.Float)

    # 套装信息
    set_id = db.Column(db.Integer, db.ForeignKey('equipment_sets.id'))

    # 强化配置
    max_enhance_level = db.Column(db.Integer, default=30)

    # 获取方式
    obtain_method = db.Column(db.String(200))

    # 描述和故事
    description = db.Column(db.Text)
    lore = db.Column(db.Text)  # 历史典故

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<EquipmentTemplate {self.name} ({self.quality})>'


class Stage(db.Model):
    """关卡模型"""
    __tablename__ = 'stages'

    id = db.Column(db.Integer, primary_key=True)

    # 基础信息
    stage_type = db.Column(db.String(20), nullable=False)  # main/daily/special/boss
    chapter = db.Column(db.Integer)  # 章节（主线关卡）
    stage_number = db.Column(db.Integer, nullable=False)  # 关卡编号
    name = db.Column(db.String(100), nullable=False)  # 关卡名称
    description = db.Column(db.Text)  # 关卡描述

    # 难度信息
    difficulty = db.Column(db.String(20))  # easy/normal/hard/elite/boss
    recommended_power = db.Column(db.Integer)  # 推荐战力

    # 消耗
    stamina_cost = db.Column(db.Integer, default=10)  # 体力消耗

    # 敌人配置
    enemy_config = db.Column(db.Text)  # JSON格式，敌方阵容配置

    # 奖励配置
    first_clear_rewards = db.Column(db.Text)  # JSON，首通奖励
    rewards = db.Column(db.Text)  # JSON，通关奖励
    drop_config = db.Column(db.Text)  # JSON，掉落配置

    # 星级条件
    star_1_condition = db.Column(db.String(100))  # 1星条件
    star_2_condition = db.Column(db.String(100))  # 2星条件
    star_3_condition = db.Column(db.String(100))  # 3星条件

    # 开放条件
    unlock_condition = db.Column(db.Text)  # JSON，解锁条件

    # 副本特殊配置
    daily_limit = db.Column(db.Integer)  # 每日挑战次数限制
    open_days = db.Column(db.String(50))  # 开放日期（1-7表示周一到周日）

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    user_progress = db.relationship('UserStageProgress', backref='stage', lazy='dynamic', cascade='all, delete-orphan')
    battle_records = db.relationship('BattleRecord', backref='stage', lazy='dynamic')

    def __repr__(self):
        return f'<Stage {self.stage_number}: {self.name}>'


class UserStageProgress(db.Model):
    """用户关卡进度"""
    __tablename__ = 'user_stage_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stage_id = db.Column(db.Integer, db.ForeignKey('stages.id'), nullable=False)

    # 进度信息
    is_cleared = db.Column(db.Boolean, default=False)  # 是否通关
    stars = db.Column(db.Integer, default=0)  # 获得星数
    best_time = db.Column(db.Integer)  # 最快通关时间（秒）

    # 挑战次数
    total_attempts = db.Column(db.Integer, default=0)  # 总挑战次数
    today_attempts = db.Column(db.Integer, default=0)  # 今日挑战次数
    last_attempt_date = db.Column(db.Date)  # 最后挑战日期

    first_clear_at = db.Column(db.DateTime)  # 首通时间
    last_clear_at = db.Column(db.DateTime)  # 最后通关时间

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<UserStageProgress user={self.user_id} stage={self.stage_id} stars={self.stars}>'


class BattleRecord(db.Model):
    """战斗记录"""
    __tablename__ = 'battle_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stage_id = db.Column(db.Integer, db.ForeignKey('stages.id'))

    # 战斗信息
    battle_type = db.Column(db.String(20))  # pve/pvp
    team_config = db.Column(db.Text)  # JSON，我方阵容
    enemy_config = db.Column(db.Text)  # JSON，敌方阵容

    # 战斗结果
    result = db.Column(db.String(10))  # win/lose
    stars = db.Column(db.Integer, default=0)  # 获得星数
    battle_duration = db.Column(db.Integer)  # 战斗时长（秒）

    # 战斗数据
    damage_dealt = db.Column(db.Integer)  # 造成伤害
    damage_taken = db.Column(db.Integer)  # 承受伤害
    battle_log = db.Column(db.Text)  # JSON，战斗日志

    # 奖励
    rewards = db.Column(db.Text)  # JSON，获得奖励

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<BattleRecord {self.id} user={self.user_id} result={self.result}>'
