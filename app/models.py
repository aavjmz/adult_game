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


class ApiToken(db.Model):
    """客户端API访问令牌

    游戏客户端（Cocos iOS/Android）无法可靠使用Session Cookie：
    原生平台的XMLHttpRequest不管理Cookie，浏览器预览时又禁止JS设置Cookie头。
    因此客户端走Bearer Token认证，Web端继续使用Flask-Login的Session。
    """
    __tablename__ = 'api_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    device = db.Column(db.String(64))  # 设备标识，便于多端登录管理

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    last_used_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    user = db.relationship('User', backref=db.backref('api_tokens', lazy='dynamic',
                                                      cascade='all, delete-orphan'))

    # 令牌有效期（天）
    TTL_DAYS = 30

    @staticmethod
    def generate(user, device=None):
        """为用户签发新令牌"""
        import secrets
        from datetime import timedelta

        token = ApiToken(
            user_id=user.id,
            token=secrets.token_urlsafe(32),
            device=device,
            expires_at=datetime.utcnow() + timedelta(days=ApiToken.TTL_DAYS)
        )
        db.session.add(token)
        return token

    def is_valid(self):
        """令牌是否仍在有效期内"""
        return datetime.utcnow() < self.expires_at

    def touch(self):
        """更新最后使用时间，并在临近过期时自动续期"""
        from datetime import timedelta

        self.last_used_at = datetime.utcnow()
        # 剩余有效期不足一半时滑动续期，避免活跃玩家被强制登出
        if self.expires_at - datetime.utcnow() < timedelta(days=self.TTL_DAYS / 2):
            self.expires_at = datetime.utcnow() + timedelta(days=self.TTL_DAYS)

    def __repr__(self):
        return f'<ApiToken user={self.user_id} device={self.device}>'


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

    # 敌军卡：只用于 PVE 关卡，不进招贤卡池与图鉴（见 app/enemy_cards.py）
    is_enemy = db.Column(db.Boolean, default=False, nullable=False)

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


class BattleSession(db.Model):
    """进行中的手动战斗：battle_core 状态存 JSON，玩家每下一次令推进一步

    status: active（进行中）/ finished（已结算）/ abandoned（被新开的战斗顶替，不结算）
    """
    __tablename__ = 'battle_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    stage_id = db.Column(db.Integer, db.ForeignKey('stages.id'), nullable=False)
    team = db.Column(db.Text, nullable=False)     # JSON：出战 UserCard id 列表
    state = db.Column(db.Text, nullable=False)    # JSON：battle_core 状态
    status = db.Column(db.String(20), default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<BattleSession {self.id} user={self.user_id} {self.status}>'


class UserFormation(db.Model):
    """编伍阵容：六个阵位（前排 0-1、中军 2-3、后阵 4-5）各放一张 UserCard 或空

    slots 存 JSON 数组，长度固定 6，元素为 UserCard.id 或 null。
    读取时会剔除已不属于该玩家的卡（如升星消耗掉的同名卡）。
    """
    __tablename__ = 'user_formations'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    slots = db.Column(db.Text, nullable=False, default='[null, null, null, null, null, null]')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<UserFormation user={self.user_id} {self.slots}>'


class ShopPurchase(db.Model):
    """市集购买记录：按自然日统计每件商品的已购次数，用于每日限购

    商品定义在 app/shop_data.py（good_key 对应其 key）；day 为北京时间日期。
    """
    __tablename__ = 'shop_purchases'
    __table_args__ = (db.UniqueConstraint('user_id', 'good_key', 'day', name='uq_shop_purchase_day'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    good_key = db.Column(db.String(50), nullable=False)
    day = db.Column(db.Date, nullable=False)
    count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ShopPurchase user={self.user_id} {self.good_key} {self.day} x{self.count}>'


class UserActivity(db.Model):
    """玩家每日行为计数（出征、招贤、消耗兵力……），军令日常 / 周常的进度据此统计

    key 见 app/orders_data.py 的 ACT_* 常量；day 为北京时间日期，周常按周一到周日求和。
    """
    __tablename__ = 'user_activities'
    __table_args__ = (db.UniqueConstraint('user_id', 'key', 'day', name='uq_user_activity_day'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    key = db.Column(db.String(30), nullable=False)
    day = db.Column(db.Date, nullable=False)
    count = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f'<UserActivity user={self.user_id} {self.key} {self.day} x{self.count}>'


class OrderClaim(db.Model):
    """军令领取记录：一道军令在一个周期内只能领一次

    period 为周期标识：日常 d2026-10-11、周常 w2026-10-05（周一）、
    通行证 s2026-10（按月）、成就 a（永久）；军功宝箱的 order_key 为 chest-30 等。
    merit 记下当时得的军功，通行证按本季领取记录求和。
    """
    __tablename__ = 'order_claims'
    __table_args__ = (db.UniqueConstraint('user_id', 'order_key', 'period', name='uq_order_claim_period'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    order_key = db.Column(db.String(50), nullable=False)
    period = db.Column(db.String(20), nullable=False)
    merit = db.Column(db.Integer, default=0, nullable=False)
    day = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<OrderClaim user={self.user_id} {self.order_key} {self.period}>'


class Mail(db.Model):
    """军书（站内信）：系统发给玩家的信件，可带附物

    attachments 为 JSON 奖励列表，格式见 app/rewards.py；领取后 claimed_at 记时间。
    玩家「弃书」只做软删除（deleted_at），便于追查补偿是否已领。
    """
    __tablename__ = 'mails'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)
    sender = db.Column(db.String(50), nullable=False, default='军 府')
    body = db.Column(db.Text, nullable=False, default='')
    attachments = db.Column(db.Text, nullable=False, default='[]')
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    claimed_at = db.Column(db.DateTime)
    deleted_at = db.Column(db.DateTime)
    # 过期后不再显示、不可领取；为空表示永不过期
    expires_at = db.Column(db.DateTime)
    # 系统信的去重标记（如 welcome、chapter-1），同一玩家同一 tag 只发一次；手发的信为空
    tag = db.Column(db.String(50), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<Mail {self.id} user={self.user_id} {self.title}>'


class ArenaPlayer(db.Model):
    """军演：玩家的积分、战绩、当日演券与当前对手批次

    首次进入军演页时建档。名次按积分现排（积分高者在前）。
    foes 为当前这批对手的 JSON 快照（真人只记 user_id，出战时读其最新编伍；电脑记阵容）。
    """
    __tablename__ = 'arena_players'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    score = db.Column(db.Integer, nullable=False, default=1000, index=True)
    wins = db.Column(db.Integer, nullable=False, default=0)
    losses = db.Column(db.Integer, nullable=False, default=0)
    best_rank = db.Column(db.Integer)
    # 演券：tickets_day 不是今天时视为已重置
    tickets_used = db.Column(db.Integer, nullable=False, default=0)
    tickets_day = db.Column(db.Date)
    foes = db.Column(db.Text, nullable=False, default='[]')
    # 最近一次领取段位之赏的日期
    reward_day = db.Column(db.Date)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ArenaPlayer user={self.user_id} score={self.score}>'


class ArenaRecord(db.Model):
    """军演战报：攻方视角记一条；守方为真人时其战报里也能看到（防守）"""
    __tablename__ = 'arena_records'

    id = db.Column(db.Integer, primary_key=True)
    attacker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    defender_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)  # 电脑对手为空
    attacker_name = db.Column(db.String(64), nullable=False)
    defender_name = db.Column(db.String(64), nullable=False)
    win = db.Column(db.Boolean, nullable=False)          # 攻方是否获胜
    attacker_delta = db.Column(db.Integer, nullable=False, default=0)
    defender_delta = db.Column(db.Integer, nullable=False, default=0)
    day = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<ArenaRecord {self.attacker_name} vs {self.defender_name} win={self.win}>'


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
