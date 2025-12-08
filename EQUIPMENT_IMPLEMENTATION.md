# 装备系统技术实现方案 ⚔️

> 三国卡牌游戏装备系统完整技术方案

## 📚 目录

1. [系统架构](#1-系统架构)
2. [数据库设计](#2-数据库设计)
3. [装备效果计算](#3-装备效果计算)
4. [API接口设计](#4-api接口设计)
5. [实现步骤](#5-实现步骤)

---

## 1. 系统架构 🏗️

### 1.1 核心模块

```
装备系统
├── 数据层
│   ├── EquipmentTemplate（装备模板）
│   ├── Equipment（用户装备实例）
│   ├── EquipmentStat（附加属性）
│   └── EquipmentSet（套装配置）
│
├── 逻辑层
│   ├── equipment_utils.py（装备计算工具）
│   ├── equipment_effects.py（装备效果）
│   └── equipment_sets.py（套装系统）
│
└── 接口层
    └── routes/equipment.py（装备API）
```

### 1.2 数据流

```
用户操作 → API路由 → 业务逻辑 → 数据库
                ↓
         效果计算 → 战斗系统
```

---

## 2. 数据库设计 💾

### 2.1 装备模板表

```python
# app/models.py

class EquipmentTemplate(db.Model):
    """装备模板表（预定义的装备类型）"""
    __tablename__ = 'equipment_templates'

    id = db.Column(db.Integer, primary_key=True)

    # 基础信息
    name = db.Column(db.String(100), nullable=False, unique=True)
    name_en = db.Column(db.String(100))  # 英文名，用于资源路径
    type = db.Column(db.String(20), nullable=False)  # weapon/armor/accessory/treasure
    quality = db.Column(db.String(20), nullable=False)  # common/rare/epic/legendary/mythic
    element = db.Column(db.String(10), default='无')  # 金/木/水/火/土/无

    # 基础属性加成（百分比）
    base_attack_pct = db.Column(db.Float, default=0)  # 攻击力加成%
    base_defense_pct = db.Column(db.Float, default=0)  # 防御力加成%
    base_hp_pct = db.Column(db.Float, default=0)  # 生命值加成%

    # 固定数值属性
    crit_rate = db.Column(db.Float, default=0)  # 暴击率%
    crit_dmg = db.Column(db.Float, default=0)  # 暴击伤害%
    speed = db.Column(db.Integer, default=0)  # 速度
    penetration = db.Column(db.Float, default=0)  # 穿透%
    block_rate = db.Column(db.Float, default=0)  # 格挡率%
    dodge_rate = db.Column(db.Float, default=0)  # 闪避率%
    lifesteal = db.Column(db.Float, default=0)  # 吸血%

    # 专属信息
    exclusive_hero_id = db.Column(db.Integer)  # 专属武将ID（为空表示通用）
    exclusive_faction = db.Column(db.String(10))  # 专属势力（魏/蜀/吴/群）

    # 专属效果
    exclusive_effect_name = db.Column(db.String(100))
    exclusive_effect_desc = db.Column(db.Text)
    exclusive_effect_type = db.Column(db.String(50))  # passive/on_attack/on_hit等
    exclusive_effect_value = db.Column(db.Float)  # 效果数值

    # 套装信息
    set_id = db.Column(db.Integer, db.ForeignKey('equipment_sets.id'))

    # 强化配置
    max_enhance_level = db.Column(db.Integer, default=30)

    # 获取方式
    obtain_method = db.Column(db.String(200))  # 掉落途径说明

    # 描述和故事
    description = db.Column(db.Text)  # 装备描述
    lore = db.Column(db.Text)  # 历史典故

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<EquipmentTemplate {self.name} ({self.quality})>'


class EquipmentSet(db.Model):
    """套装配置表"""
    __tablename__ = 'equipment_sets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    # 套装加成（2件套）
    bonus_2_desc = db.Column(db.String(200))
    bonus_2_attack_pct = db.Column(db.Float, default=0)
    bonus_2_defense_pct = db.Column(db.Float, default=0)
    bonus_2_hp_pct = db.Column(db.Float, default=0)
    bonus_2_crit_rate = db.Column(db.Float, default=0)
    bonus_2_crit_dmg = db.Column(db.Float, default=0)
    bonus_2_speed = db.Column(db.Integer, default=0)

    # 套装加成（4件套）
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

    # 关联的装备模板
    templates = db.relationship('EquipmentTemplate', backref='equipment_set', lazy='dynamic')

    def __repr__(self):
        return f'<EquipmentSet {self.name}>'


# 扩展现有的 Equipment 模型
class Equipment(db.Model):
    """用户装备实例（已存在，需要扩展）"""
    __tablename__ = 'equipments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner_card_id = db.Column(db.Integer, db.ForeignKey('user_cards.id'))

    # 关联装备模板
    template_id = db.Column(db.Integer, db.ForeignKey('equipment_templates.id'), nullable=False)
    template = db.relationship('EquipmentTemplate', backref='instances')

    # 强化等级
    enhance_level = db.Column(db.Integer, default=0)

    # 随机附加属性（JSON存储）
    # 示例: {"crit_rate": 8.5, "speed": 12, "lifesteal": 5.0}
    random_stats = db.Column(db.Text)  # JSON格式

    # 是否锁定（防止误分解）
    is_locked = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    user = db.relationship('User', backref='equipments')
    stats = db.relationship('EquipmentStat', backref='equipment', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Equipment {self.template.name if self.template else "Unknown"} +{self.enhance_level}>'
```

### 2.2 数据库迁移脚本

```python
# migrate_equipment_system.py

import sys
import os
import sqlite3
from datetime import datetime

# UTF-8编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

DB_PATH = 'game.db'

def create_equipment_templates_table(cursor):
    """创建装备模板表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipment_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            name_en VARCHAR(100),
            type VARCHAR(20) NOT NULL,
            quality VARCHAR(20) NOT NULL,
            element VARCHAR(10) DEFAULT '无',

            base_attack_pct FLOAT DEFAULT 0,
            base_defense_pct FLOAT DEFAULT 0,
            base_hp_pct FLOAT DEFAULT 0,

            crit_rate FLOAT DEFAULT 0,
            crit_dmg FLOAT DEFAULT 0,
            speed INTEGER DEFAULT 0,
            penetration FLOAT DEFAULT 0,
            block_rate FLOAT DEFAULT 0,
            dodge_rate FLOAT DEFAULT 0,
            lifesteal FLOAT DEFAULT 0,

            exclusive_hero_id INTEGER,
            exclusive_faction VARCHAR(10),
            exclusive_effect_name VARCHAR(100),
            exclusive_effect_desc TEXT,
            exclusive_effect_type VARCHAR(50),
            exclusive_effect_value FLOAT,

            set_id INTEGER,
            max_enhance_level INTEGER DEFAULT 30,
            obtain_method VARCHAR(200),
            description TEXT,
            lore TEXT,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (set_id) REFERENCES equipment_sets(id)
        )
    ''')

def create_equipment_sets_table(cursor):
    """创建套装配置表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipment_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,

            bonus_2_desc VARCHAR(200),
            bonus_2_attack_pct FLOAT DEFAULT 0,
            bonus_2_defense_pct FLOAT DEFAULT 0,
            bonus_2_hp_pct FLOAT DEFAULT 0,
            bonus_2_crit_rate FLOAT DEFAULT 0,
            bonus_2_crit_dmg FLOAT DEFAULT 0,
            bonus_2_speed INTEGER DEFAULT 0,

            bonus_4_desc VARCHAR(200),
            bonus_4_attack_pct FLOAT DEFAULT 0,
            bonus_4_defense_pct FLOAT DEFAULT 0,
            bonus_4_hp_pct FLOAT DEFAULT 0,
            bonus_4_crit_rate FLOAT DEFAULT 0,
            bonus_4_crit_dmg FLOAT DEFAULT 0,
            bonus_4_speed INTEGER DEFAULT 0,
            bonus_4_special_effect VARCHAR(100),
            bonus_4_special_desc TEXT
        )
    ''')

def extend_equipments_table(cursor):
    """扩展装备表"""
    # 添加缺失字段
    fields = [
        ('template_id', 'INTEGER'),
        ('random_stats', 'TEXT'),
        ('is_locked', 'BOOLEAN', 0)
    ]

    # 检查现有字段
    cursor.execute("PRAGMA table_info(equipments)")
    existing = [row[1] for row in cursor.fetchall()]

    for field_info in fields:
        field_name = field_info[0]
        field_type = field_info[1]
        default = field_info[2] if len(field_info) > 2 else 'NULL'

        if field_name not in existing:
            cursor.execute(f'ALTER TABLE equipments ADD COLUMN {field_name} {field_type} DEFAULT {default}')
            print(f"  ✅ 添加字段: equipments.{field_name}")
```

---

## 3. 装备效果计算 🧮

### 3.1 装备工具函数

```python
# app/equipment_utils.py

import json
from app.models import Equipment, EquipmentTemplate, EquipmentSet, Card, UserCard

def calc_equipment_bonus(equipment):
    """
    计算单件装备的属性加成

    Args:
        equipment: Equipment实例
    Returns:
        dict: 属性加成字典
    """
    template = equipment.template
    if not template:
        return {}

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
    set_bonus = calc_set_bonus(user_card)
    for key, value in set_bonus.items():
        total_bonus[key] = total_bonus.get(key, 0) + value

    return total_bonus


def calc_set_bonus(user_card):
    """
    计算套装加成

    Args:
        user_card: UserCard实例
    Returns:
        dict: 套装加成字典
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
    """
    获取所有预定义的专属装备组合
    """
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
        # ... 更多专属组合
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
        'crit_rate': base_stats.get('crit_rate', 0) + equipment_bonus['crit_rate'],
        'crit_dmg': base_stats.get('crit_dmg', 150) + equipment_bonus['crit_dmg'],
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
```

---

## 4. API接口设计 🔌

### 4.1 装备路由

```python
# app/routes/equipment.py

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Equipment, EquipmentTemplate, UserCard, UserItem
from app.equipment_utils import (
    calc_equipment_bonus, calc_total_equipment_bonus,
    calc_set_bonus, check_exclusive_combo,
    calc_enhance_success_rate, calc_enhance_cost
)
import random
import json

bp = Blueprint('equipment', __name__, url_prefix='/equipment')


@bp.route('/list', methods=['GET'])
@login_required
def list_equipments():
    """获取用户所有装备"""
    equipments = Equipment.query.filter_by(user_id=current_user.id).all()

    result = []
    for equip in equipments:
        template = equip.template
        result.append({
            'id': equip.id,
            'name': template.name,
            'type': template.type,
            'quality': template.quality,
            'element': template.element,
            'enhance_level': equip.enhance_level,
            'is_equipped': equip.owner_card_id is not None,
            'owner_card_id': equip.owner_card_id,
            'is_locked': equip.is_locked,
            'bonus': calc_equipment_bonus(equip)
        })

    return jsonify({
        'success': True,
        'equipments': result
    })


@bp.route('/enhance', methods=['POST'])
@login_required
def enhance_equipment():
    """强化装备"""
    data = request.json
    equipment_id = data.get('equipment_id')

    # 验证装备
    equipment = Equipment.query.get(equipment_id)
    if not equipment or equipment.user_id != current_user.id:
        return jsonify({'error': '装备不存在'}), 404

    template = equipment.template

    # 检查是否达到上限
    if equipment.enhance_level >= template.max_enhance_level:
        return jsonify({'error': f'已达最高强化等级+{template.max_enhance_level}'}), 400

    # 计算强化消耗
    cost = calc_enhance_cost(equipment.enhance_level, template.quality)

    # 检查强化石
    enhance_stones = UserItem.query.filter_by(
        user_id=current_user.id,
        item_type='enhance_stone'
    ).first()

    if not enhance_stones or enhance_stones.quantity < cost['stones']:
        return jsonify({'error': f"强化石不足，需要{cost['stones']}"}), 400

    # 检查金币
    if current_user.coins < cost['coins']:
        return jsonify({'error': f"金币不足，需要{cost['coins']}"}), 400

    # 计算成功率
    success_rate = calc_enhance_success_rate(equipment.enhance_level)

    # 执行强化
    is_success = random.random() < success_rate

    # 消耗材料
    enhance_stones.quantity -= cost['stones']
    current_user.coins -= cost['coins']

    if is_success:
        equipment.enhance_level += 1
        message = f'强化成功！当前等级+{equipment.enhance_level}'
    else:
        # 失败处理
        if equipment.enhance_level >= 21:
            equipment.enhance_level = max(0, equipment.enhance_level - 2)
            message = f'强化失败，等级降低2级，当前+{equipment.enhance_level}'
        elif equipment.enhance_level >= 11:
            equipment.enhance_level -= 1
            message = f'强化失败，等级降低1级，当前+{equipment.enhance_level}'
        else:
            message = f'强化失败，等级未改变，当前+{equipment.enhance_level}'

    db.session.commit()

    return jsonify({
        'success': is_success,
        'new_level': equipment.enhance_level,
        'message': message,
        'bonus': calc_equipment_bonus(equipment)
    })


@bp.route('/synthesize', methods=['POST'])
@login_required
def synthesize_equipment():
    """合成装备"""
    data = request.json
    template_id = data.get('template_id')

    # 验证模板
    template = EquipmentTemplate.query.get(template_id)
    if not template:
        return jsonify({'error': '装备模板不存在'}), 404

    # 检查碎片
    fragment_item = UserItem.query.filter_by(
        user_id=current_user.id,
        item_type='equipment_fragment',
        item_subtype=template.name_en
    ).first()

    required_fragments = {
        'legendary': 50,
        'mythic': 100
    }.get(template.quality, 50)

    if not fragment_item or fragment_item.quantity < required_fragments:
        return jsonify({'error': f'碎片不足，需要{required_fragments}'}), 400

    # 消耗碎片
    fragment_item.quantity -= required_fragments

    # 创建装备
    new_equipment = Equipment(
        user_id=current_user.id,
        template_id=template_id,
        enhance_level=0
    )

    # 随机生成附加属性
    random_stats = generate_random_stats(template.quality)
    new_equipment.random_stats = json.dumps(random_stats)

    db.session.add(new_equipment)
    db.session.commit()

    return jsonify({
        'success': True,
        'equipment_id': new_equipment.id,
        'message': f'成功合成{template.name}！',
        'random_stats': random_stats
    })


@bp.route('/dismantle', methods=['POST'])
@login_required
def dismantle_equipment():
    """分解装备"""
    data = request.json
    equipment_ids = data.get('equipment_ids', [])

    if not equipment_ids:
        return jsonify({'error': '请选择要分解的装备'}), 400

    total_fragments = 0
    total_coins = 0

    for equip_id in equipment_ids:
        equipment = Equipment.query.get(equip_id)

        if not equipment or equipment.user_id != current_user.id:
            continue

        if equipment.is_locked:
            continue

        if equipment.owner_card_id:
            continue  # 已装备的不能分解

        template = equipment.template

        # 计算分解收益
        fragments = {
            'common': 1,
            'rare': 5,
            'epic': 15,
            'legendary': 30,
            'mythic': 60
        }.get(template.quality, 1)

        # 强化等级额外收益
        fragments += equipment.enhance_level

        coins = fragments * 1000

        total_fragments += fragments
        total_coins += coins

        db.session.delete(equipment)

    # 添加碎片
    fragment_item = UserItem.query.filter_by(
        user_id=current_user.id,
        item_type='equipment_fragment',
        item_subtype='universal'
    ).first()

    if fragment_item:
        fragment_item.quantity += total_fragments
    else:
        fragment_item = UserItem(
            user_id=current_user.id,
            item_type='equipment_fragment',
            item_subtype='universal',
            quantity=total_fragments
        )
        db.session.add(fragment_item)

    current_user.coins += total_coins

    db.session.commit()

    return jsonify({
        'success': True,
        'fragments': total_fragments,
        'coins': total_coins,
        'message': f'分解成功！获得{total_fragments}碎片，{total_coins}金币'
    })


@bp.route('/card-equipments/<int:user_card_id>', methods=['GET'])
@login_required
def get_card_equipments(user_card_id):
    """获取武将的装备信息"""
    user_card = UserCard.query.get(user_card_id)
    if not user_card or user_card.user_id != current_user.id:
        return jsonify({'error': '卡牌不存在'}), 404

    equipments = Equipment.query.filter_by(owner_card_id=user_card_id).all()

    # 按槽位整理
    equipped = {
        'weapon': None,
        'armor': None,
        'accessory': None,
        'treasure': None
    }

    for equip in equipments:
        template = equip.template
        equipped[template.type] = {
            'id': equip.id,
            'name': template.name,
            'quality': template.quality,
            'enhance_level': equip.enhance_level,
            'bonus': calc_equipment_bonus(equip)
        }

    # 计算总加成
    total_bonus = calc_total_equipment_bonus(user_card)

    # 套装信息
    set_bonus, active_sets = calc_set_bonus(user_card)

    # 专属组合
    exclusive_combo = check_exclusive_combo(user_card)

    return jsonify({
        'success': True,
        'equipped': equipped,
        'total_bonus': total_bonus,
        'active_sets': active_sets,
        'exclusive_combo': exclusive_combo
    })


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
```

---

## 5. 实现步骤 📝

### Step 1: 数据库扩展（第1天）

```bash
# 1. 创建迁移脚本
python migrate_equipment_system.py

# 2. 验证表结构
sqlite3 game.db
.schema equipment_templates
.schema equipment_sets
```

### Step 2: 初始化装备数据（第2-3天）

```python
# init_equipment_data.py

def init_equipment_sets():
    """初始化套装配置"""
    sets = [
        {
            'name': '五虎上将',
            'bonus_2_desc': '攻击力+15%，暴击率+8%',
            'bonus_2_attack_pct': 0.15,
            'bonus_2_crit_rate': 8.0,
            'bonus_4_desc': '攻击力+30%，暴击率+15%，暴击伤害+30%',
            'bonus_4_attack_pct': 0.30,
            'bonus_4_crit_rate': 15.0,
            'bonus_4_crit_dmg': 30.0,
            'bonus_4_special_effect': '五虎降世',
            'bonus_4_special_desc': '战斗开始时全队攻击+20%，防御+20%，持续5回合'
        },
        # ... 更多套装
    ]

def init_legendary_weapons():
    """初始化传说级武器"""
    weapons = [
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
            'exclusive_effect_desc': '攻击时额外造成30%真实伤害，击败敌人回复50%最大生命',
            'exclusive_effect_type': 'on_attack',
            'exclusive_effect_value': 0.30,
            'set_id': 1,  # 五虎上将套装
            'obtain_method': '五虎上将副本、世界Boss',
            'description': '关羽的专属武器，重达82斤',
            'lore': '建安五年，关羽斩颜良文丑，威震华夏'
        },
        # ... 更多武器
    ]
```

### Step 3: 测试装备系统（第4天）

```python
# test_equipment_system.py

def test_equipment_enhance():
    """测试装备强化"""
    # 创建测试装备
    # 测试强化成功/失败
    # 验证强化加成计算

def test_set_bonus():
    """测试套装加成"""
    # 装备2件套装
    # 验证2件套加成
    # 装备4件套装
    # 验证4件套加成

def test_exclusive_combo():
    """测试专属装备组合"""
    # 装备专属装备
    # 验证组合效果触发
```

### Step 4: 前端界面（第5-7天）

- 装备列表界面
- 装备详情界面
- 强化界面（带动画）
- 套装预览界面

---

## 6. 关键技术点 🔑

### 6.1 强化系统

```python
# 强化成功率曲线
+0~+5:  100% 成功
+6~+10:  90% 成功
+11~+15: 70% 成功
+16~+20: 50% 成功
+21~+25: 30% 成功
+26~+30: 10% 成功

# 失败惩罚
+0~+10:  不降级
+11~+20: 降1级
+21~+30: 降2级
```

### 6.2 随机属性生成

```python
# 按品质生成随机附加属性
普通: 0条
精良: 1条
稀有: 2条
史诗: 3条
传说: 4条
神话: 5条

# 属性池和数值范围
暴击率: 5~15%
暴击伤害: 10~30%
速度: 5~20
穿透: 5~15%
吸血: 5~15%
```

### 6.3 套装系统优先级

```
专属组合 > 4件套 > 2件套 > 单件装备
```

---

## 7. 数据配置示例 📊

### 传说级装备完整配置

```json
{
  "name": "青龙偃月刀",
  "name_en": "green_dragon_crescent_blade",
  "type": "weapon",
  "quality": "legendary",
  "element": "金",
  "base_attack_pct": 0.40,
  "crit_rate": 10.0,
  "crit_dmg": 25.0,
  "speed": 15,
  "exclusive_hero_id": 1,
  "exclusive_effect_name": "武圣之威",
  "exclusive_effect_desc": "攻击时额外造成30%真实伤害，击败敌人回复50%最大生命",
  "exclusive_effect_type": "on_attack",
  "exclusive_effect_value": 0.30,
  "set_id": 1,
  "max_enhance_level": 25,
  "obtain_method": "五虎上将副本、世界Boss",
  "description": "关羽的专属武器，重达八十二斤，刀身镌刻青龙图案",
  "lore": "建安五年，关羽单骑赴会，斩颜良文丑，此刀威震华夏。后人传言，刀身青龙若隐若现，斩敌必见血光。"
}
```

---

## 总结 ✅

本实现方案包含：

1. ✅ **完整的数据模型设计**（3张新表）
2. ✅ **装备效果计算系统**（10+工具函数）
3. ✅ **RESTful API设计**（5个核心接口）
4. ✅ **套装系统实现**（自动检测和加成）
5. ✅ **专属装备组合**（预定义配置）
6. ✅ **随机属性生成**（按品质差异）
7. ✅ **强化系统**（成功率曲线+失败惩罚）

**预估开发工期**: 1周（7天）
**技术难点**: 装备效果的动态计算、套装检测算法
**扩展性**: 易于添加新装备、新套装、新专属组合
