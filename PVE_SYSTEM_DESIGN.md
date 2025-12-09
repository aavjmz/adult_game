# PVE关卡系统设计方案 🗺️

> 三国卡牌游戏 - 完整PVE玩法设计

## 📋 目录

1. [系统概述](#系统概述)
2. [数据库设计](#数据库设计)
3. [关卡类型](#关卡类型)
4. [战斗机制](#战斗机制)
5. [奖励系统](#奖励系统)
6. [体力系统](#体力系统)
7. [星级评价](#星级评价)
8. [API设计](#api设计)
9. [前端界面](#前端界面)
10. [实现计划](#实现计划)

---

## 系统概述

### 核心目标
- 提供丰富的PVE内容，让玩家有"刷"的目标
- 通过关卡掉落装备、材料，形成养成循环
- 设计合理的难度曲线，保持挑战性
- 多样化的关卡类型，避免单调

### PVE内容模块
```
PVE系统
├── 主线关卡 (150关)
│   ├── 普通关卡 (1-100)
│   ├── 精英关卡 (101-140)
│   └── Boss关卡 (141-150)
│
├── 每日副本
│   ├── 演武场 (经验副本)
│   ├── 宝物阁 (装备副本)
│   └── 演义殿 (金币副本)
│
├── 专属副本 (每周开放)
│   ├── 五虎上将副本 (周一/四)
│   ├── 卧龙凤雏副本 (周二/五)
│   └── 三国枭雄副本 (周三/六)
│
└── 世界Boss
    ├── 每日Boss (黄巾贼首/董卓/吕布)
    └── 周常Boss (蚩尤/神龙)
```

---

## 数据库设计

### 1. Stage 模型（关卡表）

```python
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
```

### 2. User 模型扩展

```python
# 在现有 User 模型中添加
class User(UserMixin, db.Model):
    # ... 现有字段 ...

    # 体力系统
    stamina = db.Column(db.Integer, default=120)  # 当前体力
    max_stamina = db.Column(db.Integer, default=120)  # 最大体力
    stamina_updated_at = db.Column(db.DateTime, default=datetime.utcnow)  # 体力更新时间

    # 主线进度
    main_stage_progress = db.Column(db.Integer, default=0)  # 主线关卡进度

    # 统计数据
    total_pve_battles = db.Column(db.Integer, default=0)  # 总PVE战斗次数
    total_pve_wins = db.Column(db.Integer, default=0)  # 总PVE胜利次数
```

---

## 关卡类型

### 1. 主线关卡（150关）

#### 章节划分
- **第1章 黄巾起义**（1-10关）
  - 推荐战力: 1000-3000
  - 掉落: N/R装备碎片、经验药水
  - Boss: 张角

- **第2章 董卓之乱**（11-20关）
  - 推荐战力: 3000-6000
  - 掉落: R/SR装备碎片、技能书
  - Boss: 董卓

- **第3章 群雄割据**（21-30关）
  - 推荐战力: 6000-10000
  - 掉落: SR装备碎片、升星材料
  - Boss: 吕布

- **第4章 官渡之战**（31-50关）
  - 推荐战力: 10000-20000
  - 掉落: SR/SSR装备碎片、觉醒材料
  - Boss: 袁绍

- **第5章 赤壁之战**（51-70关）
  - 推荐战力: 20000-35000
  - 掉落: SSR装备碎片、突破材料
  - Boss: 周瑜

- **第6章 三分天下**（71-90关）
  - 推荐战力: 35000-50000
  - 掉落: SSR/传说装备碎片
  - Boss: 诸葛亮

- **第7章 夷陵之战**（91-110关）
  - 推荐战力: 50000-70000
  - 掉落: 传说装备碎片、专属材料
  - Boss: 陆逊

- **第8章 六出祁山**（111-130关）
  - 推荐战力: 70000-90000
  - 掉落: 传说/神话装备碎片
  - Boss: 司马懿

- **第9章 三国归晋**（131-145关）
  - 推荐战力: 90000-120000
  - 掉落: 神话装备碎片、稀有材料
  - Boss: 邓艾

- **第10章 终章：乱世终结**（146-150关）
  - 推荐战力: 120000+
  - 掉落: 神话装备、绝版材料
  - Boss: 司马炎（终极Boss）

#### 难度分类
```python
# 普通关卡 (1-100关)
{
    "difficulty": "normal",
    "enemy_count": 3-4,
    "enemy_level_offset": 0,  # 与推荐等级一致
    "stamina_cost": 10
}

# 精英关卡 (101-140关)
{
    "difficulty": "elite",
    "enemy_count": 4-5,
    "enemy_level_offset": +5,  # 比推荐等级高5级
    "stamina_cost": 15
}

# Boss关卡 (141-150关)
{
    "difficulty": "boss",
    "enemy_count": 1,  # 单个强力Boss
    "enemy_level_offset": +10,
    "stamina_cost": 20
}
```

### 2. 每日副本

#### 演武场（经验副本）
```python
{
    "name": "演武场",
    "stages": [
        {
            "id": 1001,
            "difficulty": "easy",
            "stamina_cost": 10,
            "rewards": {
                "exp_potion_small": {"min": 3, "max": 5},
                "coins": 5000
            },
            "daily_limit": 3
        },
        {
            "id": 1002,
            "difficulty": "normal",
            "stamina_cost": 15,
            "rewards": {
                "exp_potion_medium": {"min": 2, "max": 4},
                "coins": 10000
            },
            "daily_limit": 3
        },
        {
            "id": 1003,
            "difficulty": "hard",
            "stamina_cost": 20,
            "rewards": {
                "exp_potion_large": {"min": 1, "max": 3},
                "coins": 20000
            },
            "daily_limit": 3
        }
    ]
}
```

#### 宝物阁（装备副本）
```python
{
    "name": "宝物阁",
    "stages": [
        {
            "id": 2001,
            "difficulty": "easy",
            "stamina_cost": 10,
            "drop_config": {
                "equipment_fragment_rare": {"rate": 0.8, "quantity": [1, 3]},
                "equipment_fragment_epic": {"rate": 0.2, "quantity": [1, 2]}
            },
            "daily_limit": 5
        },
        {
            "id": 2002,
            "difficulty": "normal",
            "stamina_cost": 15,
            "drop_config": {
                "equipment_fragment_epic": {"rate": 0.7, "quantity": [1, 3]},
                "equipment_fragment_legendary": {"rate": 0.3, "quantity": [1, 2]}
            },
            "daily_limit": 5
        },
        {
            "id": 2003,
            "difficulty": "hard",
            "stamina_cost": 20,
            "drop_config": {
                "equipment_fragment_legendary": {"rate": 0.8, "quantity": [1, 3]},
                "equipment_fragment_mythic": {"rate": 0.2, "quantity": [1, 1]}
            },
            "daily_limit": 5
        }
    ]
}
```

#### 演义殿（金币副本）
```python
{
    "name": "演义殿",
    "stages": [
        {
            "id": 3001,
            "difficulty": "easy",
            "stamina_cost": 10,
            "rewards": {
                "coins": {"min": 20000, "max": 30000}
            },
            "daily_limit": 5
        },
        {
            "id": 3002,
            "difficulty": "normal",
            "stamina_cost": 15,
            "rewards": {
                "coins": {"min": 50000, "max": 70000}
            },
            "daily_limit": 5
        },
        {
            "id": 3003,
            "difficulty": "hard",
            "stamina_cost": 20,
            "rewards": {
                "coins": {"min": 100000, "max": 150000}
            },
            "daily_limit": 5
        }
    ]
}
```

### 3. 专属副本（每周开放）

#### 五虎上将副本
```python
{
    "name": "五虎上将副本",
    "open_days": "1,4",  # 周一、周四开放
    "stages": [
        {
            "id": 4001,
            "name": "关羽试炼",
            "boss": "关羽幻影",
            "stamina_cost": 30,
            "exclusive_drops": [
                {"item": "青龙偃月刀碎片", "rate": 0.3},
                {"item": "赤兔马鞍碎片", "rate": 0.2},
                {"item": "关羽专属材料", "rate": 0.5}
            ],
            "daily_limit": 3
        },
        {
            "id": 4002,
            "name": "张飞试炼",
            "boss": "张飞幻影",
            "exclusive_drops": [
                {"item": "丈八蛇矛碎片", "rate": 0.3},
                {"item": "虎胆甲碎片", "rate": 0.2}
            ]
        },
        # ... 赵云、马超、黄忠
    ]
}
```

#### 卧龙凤雏副本
```python
{
    "name": "卧龙凤雏副本",
    "open_days": "2,5",  # 周二、周五开放
    "stages": [
        {
            "id": 5001,
            "name": "诸葛试炼",
            "boss": "诸葛亮幻影",
            "exclusive_drops": [
                {"item": "羽扇碎片", "rate": 0.3},
                {"item": "八卦衣碎片", "rate": 0.2},
                {"item": "七星灯碎片", "rate": 0.1}
            ]
        },
        {
            "id": 5002,
            "name": "庞统试炼",
            "boss": "庞统幻影"
        }
    ]
}
```

#### 三国枭雄副本
```python
{
    "name": "三国枭雄副本",
    "open_days": "3,6",  # 周三、周六开放
    "stages": [
        {
            "id": 6001,
            "name": "曹操试炼",
            "boss": "曹操幻影",
            "exclusive_drops": [
                {"item": "七星宝刀碎片", "rate": 0.3},
                {"item": "玄武甲碎片", "rate": 0.2}
            ]
        },
        {
            "id": 6002,
            "name": "刘备试炼"
        },
        {
            "id": 6003,
            "name": "孙权试炼"
        }
    ]
}
```

### 4. 世界Boss

#### 每日Boss
```python
{
    "name": "每日世界Boss",
    "bosses": [
        {
            "id": 7001,
            "name": "黄巾贼首",
            "hp": 10000000,
            "open_time": "12:00-13:00, 19:00-20:00",
            "rewards": {
                "damage_based": True,
                "tiers": [
                    {"min_damage": 1000000, "rewards": ["SSR碎片x5", "金币x100000"]},
                    {"min_damage": 500000, "rewards": ["SR碎片x10", "金币x50000"]},
                    {"min_damage": 100000, "rewards": ["R碎片x20", "金币x20000"]}
                ]
            }
        },
        {
            "id": 7002,
            "name": "董卓",
            "open_days": "2,4,6"
        },
        {
            "id": 7003,
            "name": "吕布",
            "open_days": "1,3,5,7"
        }
    ]
}
```

#### 周常Boss
```python
{
    "name": "周常世界Boss",
    "bosses": [
        {
            "id": 8001,
            "name": "蚩尤",
            "hp": 50000000,
            "open_days": "7",  # 仅周日开放
            "special_mechanics": [
                "五行克制加强",
                "暴击伤害提升50%"
            ],
            "ranking_rewards": [
                {"rank": [1, 1], "rewards": ["神话装备x1", "金币x1000000"]},
                {"rank": [2, 10], "rewards": ["传说装备x2", "金币x500000"]},
                {"rank": [11, 50], "rewards": ["SSR碎片x20", "金币x200000"]}
            ]
        },
        {
            "id": 8002,
            "name": "神龙"
        }
    ]
}
```

---

## 战斗机制

### 1. 敌方阵容配置

```python
# 关卡敌人配置示例
enemy_config = {
    "enemies": [
        {
            "card_id": 1,  # 关羽
            "level": 50,
            "star": 3,
            "equipment": [
                {"template_id": 1, "enhance_level": 10}
            ],
            "position": 1  # 前排位置
        },
        {
            "card_id": 2,  # 张飞
            "level": 50,
            "star": 3,
            "position": 2
        },
        {
            "card_id": 3,  # 诸葛亮
            "level": 48,
            "star": 2,
            "position": 5  # 后排位置
        }
    ],
    "ai_strategy": "aggressive"  # 积极/防守/平衡
}
```

### 2. 战斗流程

```python
def battle_pve(user_team, stage_config):
    """PVE战斗流程"""

    # 1. 初始化战斗
    battle = Battle()
    battle.team_a = user_team
    battle.team_b = generate_enemies(stage_config.enemy_config)

    # 2. 计算装备加成
    apply_equipment_bonus(battle.team_a)
    apply_equipment_bonus(battle.team_b)

    # 3. 战斗循环
    battle_log = []
    turn = 1

    while not is_battle_end(battle):
        # 按速度排序行动
        action_order = get_action_order(battle)

        for unit in action_order:
            if unit.is_alive():
                action = execute_turn(unit, battle)
                battle_log.append(action)

        turn += 1

        # 超过50回合判定失败
        if turn > 50:
            return {"result": "lose", "reason": "timeout"}

    # 4. 战斗结算
    result = {
        "result": "win" if all_enemies_dead(battle) else "lose",
        "duration": turn,
        "damage_dealt": sum([u.damage_dealt for u in battle.team_a]),
        "damage_taken": sum([u.damage_taken for u in battle.team_a]),
        "battle_log": battle_log
    }

    return result
```

### 3. AI策略

```python
class EnemyAI:
    """敌人AI"""

    def choose_action(self, unit, battle, strategy="balanced"):
        """选择行动"""

        if strategy == "aggressive":
            # 优先攻击血量最低的敌人
            target = self.find_lowest_hp_enemy(battle)
            if unit.can_use_skill():
                return {"action": "skill", "target": target}
            return {"action": "attack", "target": target}

        elif strategy == "defensive":
            # 优先保护己方低血量单位
            if self.has_low_hp_ally(battle):
                if unit.role == "healer":
                    return {"action": "heal", "target": self.find_lowest_hp_ally()}
            return {"action": "attack", "target": self.find_random_enemy()}

        else:  # balanced
            # 根据情况选择
            if unit.hp_percent < 0.3:
                return {"action": "defend"}
            if unit.can_use_skill() and random.random() < 0.5:
                return {"action": "skill"}
            return {"action": "attack"}
```

---

## 奖励系统

### 1. 首通奖励

```python
first_clear_rewards = {
    "coins": 10000,
    "tickets": 1,
    "items": [
        {"type": "equipment_fragment", "subtype": "legendary", "quantity": 5},
        {"type": "exp_potion", "subtype": "large", "quantity": 3}
    ],
    "cards": [
        {"card_id": 5, "probability": 0.1}  # 10%概率获得特定卡牌
    ]
}
```

### 2. 通关奖励

```python
clear_rewards = {
    "base": {
        "coins": {"min": 5000, "max": 8000},
        "exp": 1000
    },
    "drops": [
        {
            "item_type": "equipment_fragment",
            "item_subtype": "rare",
            "probability": 0.6,
            "quantity": [1, 3]
        },
        {
            "item_type": "equipment_fragment",
            "item_subtype": "epic",
            "probability": 0.3,
            "quantity": [1, 2]
        },
        {
            "item_type": "equipment_fragment",
            "item_subtype": "legendary",
            "probability": 0.1,
            "quantity": 1
        }
    ]
}
```

### 3. 星级额外奖励

```python
star_bonus = {
    1: {"coins": 1000},
    2: {"coins": 2000, "tickets": 1},
    3: {"coins": 5000, "tickets": 2, "gems": 10}
}
```

### 4. 掉落计算

```python
def calculate_drops(drop_config):
    """计算掉落"""
    drops = []

    for drop_item in drop_config:
        if random.random() < drop_item['probability']:
            quantity = random.randint(
                drop_item['quantity'][0],
                drop_item['quantity'][1]
            )
            drops.append({
                'type': drop_item['item_type'],
                'subtype': drop_item['item_subtype'],
                'quantity': quantity
            })

    return drops
```

---

## 体力系统

### 1. 体力机制

```python
class StaminaSystem:
    """体力系统"""

    STAMINA_RECOVERY_RATE = 6  # 每6分钟恢复1点
    MAX_STAMINA = 120

    @staticmethod
    def recover_stamina(user):
        """自动恢复体力"""
        now = datetime.utcnow()
        last_update = user.stamina_updated_at

        minutes_passed = (now - last_update).total_seconds() / 60
        stamina_recovered = int(minutes_passed / 6)

        if stamina_recovered > 0:
            user.stamina = min(
                user.stamina + stamina_recovered,
                user.max_stamina
            )
            user.stamina_updated_at = now
            db.session.commit()

    @staticmethod
    def consume_stamina(user, amount):
        """消耗体力"""
        if user.stamina < amount:
            return False

        user.stamina -= amount
        db.session.commit()
        return True

    @staticmethod
    def use_stamina_potion(user, potion_type):
        """使用体力药水"""
        potion_values = {
            'small': 30,
            'medium': 60,
            'large': 120
        }

        recovery = potion_values.get(potion_type, 0)
        user.stamina = min(user.stamina + recovery, user.max_stamina)
        db.session.commit()
```

### 2. 体力购买

```python
stamina_shop = {
    "daily_purchases": [
        {"count": 1, "cost_gems": 50, "stamina": 60},
        {"count": 2, "cost_gems": 100, "stamina": 60},
        {"count": 3, "cost_gems": 200, "stamina": 60}
    ],
    "max_daily_purchases": 3
}
```

---

## 星级评价

### 1. 星级条件配置

```python
star_conditions = {
    "1_star": {
        "type": "clear",  # 仅通关
        "description": "通关关卡"
    },
    "2_star": {
        "type": "no_death",  # 无人阵亡
        "description": "无人阵亡"
    },
    "3_star": {
        "type": "turns_limit",  # 回合数限制
        "max_turns": 10,
        "description": "10回合内通关"
    }
}

# 其他星级条件类型
star_condition_types = {
    "clear": "通关",
    "no_death": "无人阵亡",
    "turns_limit": "回合数限制",
    "hp_percent": "剩余生命百分比",
    "use_skill": "使用技能次数",
    "no_items": "不使用道具"
}
```

### 2. 星级评价计算

```python
def calculate_stars(battle_result, star_conditions):
    """计算星级"""
    stars = 0

    # 1星：通关
    if battle_result['result'] == 'win':
        stars = 1
    else:
        return 0

    # 2星：无人阵亡
    if star_conditions['2_star']['type'] == 'no_death':
        if battle_result['deaths'] == 0:
            stars = 2

    # 3星：特殊条件
    condition_3 = star_conditions['3_star']

    if condition_3['type'] == 'turns_limit':
        if battle_result['turns'] <= condition_3['max_turns']:
            stars = 3

    elif condition_3['type'] == 'hp_percent':
        if battle_result['hp_percent'] >= condition_3['min_hp']:
            stars = 3

    return stars
```

---

## API设计

### 1. 关卡列表

```
GET /stages/list?type=main&chapter=1
```

**响应**:
```json
{
    "success": true,
    "stages": [
        {
            "id": 1,
            "chapter": 1,
            "stage_number": 1,
            "name": "黄巾起义·序章",
            "difficulty": "normal",
            "recommended_power": 1000,
            "stamina_cost": 10,
            "is_unlocked": true,
            "user_progress": {
                "is_cleared": true,
                "stars": 3,
                "best_time": 45
            }
        }
    ]
}
```

### 2. 开始战斗

```
POST /stages/battle/start
```

**请求**:
```json
{
    "stage_id": 1,
    "team": [1, 2, 3, 4, 5]  // UserCard IDs
}
```

**响应**:
```json
{
    "success": true,
    "battle_id": "abc123",
    "enemy_team": [...],
    "battle_config": {...}
}
```

### 3. 战斗结算

```
POST /stages/battle/finish
```

**请求**:
```json
{
    "battle_id": "abc123",
    "result": "win",
    "turns": 8,
    "damage_dealt": 50000,
    "deaths": 0
}
```

**响应**:
```json
{
    "success": true,
    "stars": 3,
    "rewards": {
        "coins": 8000,
        "exp": 1000,
        "items": [
            {"type": "equipment_fragment", "subtype": "rare", "quantity": 3}
        ]
    },
    "first_clear": false,
    "new_record": true
}
```

### 4. 扫荡关卡

```
POST /stages/sweep
```

**请求**:
```json
{
    "stage_id": 1,
    "times": 10
}
```

**响应**:
```json
{
    "success": true,
    "total_rewards": {
        "coins": 80000,
        "items": [...]
    },
    "stamina_consumed": 100
}
```

### 5. 每日副本列表

```
GET /stages/daily
```

**响应**:
```json
{
    "success": true,
    "daily_dungeons": [
        {
            "type": "exp",
            "name": "演武场",
            "stages": [
                {
                    "id": 1001,
                    "difficulty": "easy",
                    "attempts_today": 2,
                    "daily_limit": 3
                }
            ]
        }
    ]
}
```

---

## 前端界面

### 1. 关卡地图界面

```
关卡地图
├── 章节选择（横向滑动）
│   ├── 第1章: 黄巾起义
│   ├── 第2章: 董卓之乱
│   └── ...
│
├── 关卡节点（纵向滚动）
│   ├── 关卡1 ⭐⭐⭐
│   ├── 关卡2 ⭐⭐☆
│   ├── 关卡3 🔒
│   └── Boss关卡 💀
│
└── 底部信息栏
    ├── 当前体力: 80/120
    ├── 推荐战力: 5000
    └── [挑战] [扫荡]
```

### 2. 战斗准备界面

```
战斗准备
├── 敌方阵容预览
│   └── 敌人1, 敌人2, 敌人3
│
├── 我方阵容编辑
│   └── [前排] [后排] 拖拽卡牌
│
├── 星级条件
│   ├── ⭐ 通关关卡
│   ├── ⭐ 无人阵亡
│   └── ⭐ 10回合内通关
│
├── 消耗显示
│   └── 体力: -10
│
└── [开始战斗]
```

### 3. 战斗结算界面

```
战斗结算
├── 结果展示
│   ├── 胜利/失败
│   └── ⭐⭐⭐ (星级)
│
├── 战斗数据
│   ├── 回合数: 8
│   ├── 伤害: 50000
│   └── 时间: 1:23
│
├── 奖励展示
│   ├── 金币 +8000
│   ├── 经验 +1000
│   └── 装备碎片 x3
│
└── [再次挑战] [返回]
```

### 4. 每日副本界面

```
每日副本
├── 副本分类（Tab切换）
│   ├── [演武场] - 经验
│   ├── [宝物阁] - 装备
│   └── [演义殿] - 金币
│
├── 难度选择
│   ├── 简单 (剩余: 3/3)
│   ├── 普通 (剩余: 3/3)
│   └── 困难 (剩余: 3/3)
│
└── 奖励预览
    └── 经验药水(大) x1-3
```

---

## 实现计划

### Week 1: 数据库和基础系统

**Day 1-2: 数据库模型**
- [ ] 创建 Stage 模型
- [ ] 创建 UserStageProgress 模型
- [ ] 创建 BattleRecord 模型
- [ ] 扩展 User 模型（体力系统）
- [ ] 数据库迁移脚本

**Day 3-4: 体力系统**
- [ ] 体力恢复逻辑
- [ ] 体力消耗逻辑
- [ ] 体力购买功能
- [ ] 体力API

**Day 5-7: 关卡配置系统**
- [ ] 关卡配置数据结构
- [ ] 初始化前30个关卡
- [ ] 敌人配置生成器
- [ ] 奖励配置系统

### Week 2: 战斗系统集成

**Day 8-10: PVE战斗逻辑**
- [ ] PVE战斗流程
- [ ] 敌方AI系统
- [ ] 战斗日志记录
- [ ] 星级评价系统

**Day 11-12: 奖励系统**
- [ ] 掉落计算逻辑
- [ ] 首通奖励发放
- [ ] 星级奖励发放
- [ ] 奖励领取API

**Day 13-14: 扫荡系统**
- [ ] 扫荡条件检查
- [ ] 批量战斗结算
- [ ] 扫荡奖励累计

### Week 3: 副本系统

**Day 15-17: 每日副本**
- [ ] 每日副本配置
- [ ] 挑战次数限制
- [ ] 每日重置逻辑
- [ ] 副本API

**Day 18-19: 专属副本**
- [ ] 专属副本配置
- [ ] 开放日期控制
- [ ] 专属掉落系统

**Day 20-21: 世界Boss**
- [ ] Boss血量共享机制
- [ ] 伤害排行榜
- [ ] 奖励分配逻辑

### Week 4: 前端界面

**Day 22-24: 关卡地图**
- [ ] 关卡列表界面
- [ ] 章节切换
- [ ] 关卡解锁状态
- [ ] 星级显示

**Day 25-26: 战斗界面**
- [ ] 战斗准备界面
- [ ] 阵容编辑
- [ ] 战斗结算界面

**Day 27-28: 副本界面**
- [ ] 每日副本界面
- [ ] 专属副本界面
- [ ] Boss界面

---

## 测试计划

### 单元测试
- [ ] 体力恢复计算
- [ ] 星级评价逻辑
- [ ] 掉落计算
- [ ] AI决策系统

### 集成测试
- [ ] 完整战斗流程
- [ ] 奖励发放
- [ ] 扫荡功能
- [ ] 每日重置

### 性能测试
- [ ] 大量战斗记录查询
- [ ] 排行榜计算
- [ ] 并发战斗处理

---

## 数据平衡

### 体力消耗表
| 关卡类型 | 体力消耗 |
|---------|---------|
| 主线普通 | 10 |
| 主线精英 | 15 |
| 主线Boss | 20 |
| 每日副本简单 | 10 |
| 每日副本普通 | 15 |
| 每日副本困难 | 20 |
| 专属副本 | 30 |
| 世界Boss | 0 |

### 经验获取表
| 关卡等级 | 经验值 |
|---------|--------|
| 1-10 | 100-500 |
| 11-30 | 500-1000 |
| 31-50 | 1000-2000 |
| 51-70 | 2000-3000 |
| 71-100 | 3000-5000 |

### 掉落概率表
| 品质 | 普通关卡 | 精英关卡 | Boss关卡 |
|------|---------|---------|---------|
| 稀有 | 60% | 40% | 20% |
| 史诗 | 30% | 40% | 40% |
| 传说 | 10% | 20% | 35% |
| 神话 | 0% | 0% | 5% |

---

## 后续扩展

### Phase 2.1: 爬塔系统
- 100层无尽之塔
- 层层递增难度
- 每10层一个Boss
- 重置机制

### Phase 2.2: 活动副本
- 限时活动关卡
- 特殊玩法规则
- 限定奖励

### Phase 2.3: 挑战模式
- 无限模式
- 速通模式
- 限制模式（如只能用特定势力）

---

## 总结

PVE关卡系统是游戏的核心玩法之一，提供了：

✅ **丰富的内容**：150个主线关卡 + 每日副本 + 专属副本 + 世界Boss
✅ **合理的进度**：从简单到困难的梯度设计
✅ **多样的奖励**：装备、材料、金币、经验
✅ **可持续性**：每日副本提供重复可玩内容
✅ **挑战性**：星级系统和Boss战提供挑战目标

实现完成后，玩家将有明确的游戏目标和持续的游戏动力！
