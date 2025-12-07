# 三国卡牌游戏 - 成长系统完整设计 📈

> 包含升级、升星、技能、装备、觉醒的完整武将养成体系

## 📚 目录

1. [卡牌升级系统](#1-卡牌升级系统)
2. [升星系统](#2-升星系统)
3. [技能升级系统](#3-技能升级系统)
4. [装备系统](#4-装备系统)
5. [觉醒系统](#5-觉醒系统)
6. [突破系统](#6-突破系统)
7. [数值成长曲线](#7-数值成长曲线)
8. [技术实现方案](#8-技术实现方案)

---

## 1. 卡牌升级系统 ⬆️

### 1.1 等级范围

```yaml
等级上限: Lv.100
初始等级: Lv.1
升级方式:
  - 战斗获得经验
  - 使用经验药水
  - 吞噬其他卡牌
```

### 1.2 经验值需求曲线

#### 基础公式
```python
def calc_exp_required(level):
    """计算升级所需经验"""
    if level < 20:
        # 前期快速升级
        return level * 100
    elif level < 40:
        # 中期正常升级
        return level * 200 + 2000
    elif level < 60:
        # 后期较慢
        return level * 500 + 10000
    elif level < 80:
        # 高级较慢
        return level * 1000 + 30000
    else:
        # 终极缓慢
        return level * 2000 + 80000
```

#### 经验需求表

| 等级范围 | 单级经验 | 累计经验 | 备注 |
|---------|---------|---------|------|
| Lv.1-10 | 100-1000 | 5,500 | 新手期 |
| Lv.11-20 | 1100-2000 | 21,000 | 快速成长 |
| Lv.21-30 | 6200-8000 | 92,000 | 过渡期 |
| Lv.31-40 | 8200-10000 | 183,000 | 中期 |
| Lv.41-50 | 30500-35000 | 510,000 | 后期 |
| Lv.51-60 | 61000-70000 | 1,165,000 | 高级 |
| Lv.61-70 | 91000-100000 | 2,120,000 | 精英 |
| Lv.71-80 | 101000-110000 | 3,175,000 | 大师 |
| Lv.81-90 | 242000-260000 | 5,685,000 | 宗师 |
| Lv.91-100 | 262000-280000 | 8,395,000 | 传说 |

### 1.3 属性成长

#### 成长公式
```python
def calc_stat_at_level(base_stat, growth_rate, level):
    """计算指定等级的属性值"""
    return int(base_stat * (1 + growth_rate * (level - 1)))

# 成长率（按稀有度）
growth_rates = {
    'N': 0.02,   # 每级+2%
    'R': 0.025,  # 每级+2.5%
    'SR': 0.03,  # 每级+3%
    'SSR': 0.035,# 每级+3.5%
    'UR': 0.04   # 每级+4%
}
```

#### 示例：诸葛亮（UR）成长

| 等级 | 攻击力 | 防御力 | 生命值 |
|------|--------|--------|--------|
| Lv.1 | 520 | 400 | 5200 |
| Lv.20 | 915 | 704 | 9152 |
| Lv.40 | 1331 | 1024 | 13312 |
| Lv.60 | 1747 | 1344 | 17472 |
| Lv.80 | 2163 | 1664 | 21632 |
| Lv.100 | 2580 | 1984 | 25792 |

### 1.4 经验获取方式

#### 战斗获取
```yaml
主线关卡:
  - Lv.1-10关卡: 50 经验/次
  - Lv.11-30关卡: 100 经验/次
  - Lv.31-50关卡: 200 经验/次
  - Lv.51+关卡: 500 经验/次

每日副本:
  - 演武场（简单）: 1000 经验
  - 演武场（普通）: 3000 经验
  - 演武场（困难）: 10000 经验

竞技场:
  - 每场胜利: 500 经验
```

#### 经验药水
```yaml
小型经验药水:
  - 提供经验: 1000
  - 获取方式: 每日签到、主线关卡

中型经验药水:
  - 提供经验: 5000
  - 获取方式: 每日副本、商店购买

大型经验药水:
  - 提供经验: 20000
  - 获取方式: 活动奖励、商店购买

超大型经验药水:
  - 提供经验: 100000
  - 获取方式: 限时活动、充值奖励
```

#### 卡牌吞噬
```yaml
机制:
  - 将不需要的卡牌作为经验素材
  - 获得该卡牌基础经验值的80%
  - 同名卡牌额外+50%经验

经验值计算:
  N卡: 基础经验 500
  R卡: 基础经验 2000
  SR卡: 基础经验 10000
  SSR卡: 基础经验 50000
  UR卡: 不可作为经验素材
```

---

## 2. 升星系统 ⭐

### 2.1 星级范围

```yaml
初始星级: ★1
最高星级: ★★★★★5

升星效果:
  - 大幅提升基础属性
  - 解锁新的被动技能槽
  - 提升技能等级上限
  - 改变卡面外观
```

### 2.2 升星材料需求

| 升星路径 | 所需材料 | 金币消耗 | 备注 |
|---------|---------|---------|------|
| ★1 → ★2 | 同名卡 x1 或 万能星石 x10 | 50,000 | 解锁被动槽1 |
| ★2 → ★3 | 同名卡 x2 或 万能星石 x30 | 150,000 | 全属性+20% |
| ★3 → ★4 | 同名卡 x3 或 万能星石 x60 | 500,000 | 解锁被动槽2 |
| ★4 → ★5 | 同名卡 x5 或 万能星石 x100 | 1,500,000 | 全属性+50% |

### 2.3 升星属性加成

#### 加成公式
```python
def calc_star_bonus(base_stat, star_level):
    """计算升星加成"""
    bonuses = {
        1: 1.0,   # 基础
        2: 1.15,  # +15%
        3: 1.35,  # +35%
        4: 1.60,  # +60%
        5: 2.10   # +110%
    }
    return int(base_stat * bonuses[star_level])
```

#### 示例：关羽（SSR）升星对比

| 星级 | 攻击力 | 防御力 | 生命值 | 特殊能力 |
|------|--------|--------|--------|---------|
| ★1 | 300 | 210 | 2600 | 基础被动 |
| ★2 | 345 | 242 | 2990 | +被动槽1 |
| ★3 | 405 | 284 | 3510 | 全属性+20% |
| ★4 | 480 | 336 | 4160 | +被动槽2 |
| ★5 | 630 | 441 | 5460 | 全属性+50%，专属称号 |

### 2.4 万能星石获取

```yaml
主线关卡:
  - 三星通关: 星石 x1
  - 首次通关: 星石 x3

副本掉落:
  - 宝物阁（困难）: 星石 x2-5
  - 周常Boss: 星石 x10

竞技场:
  - 段位奖励: 星石 x10-100
  - 赛季奖励: 星石 x50-500

商店购买:
  - 金币商店: 10,000金币 = 1星石
  - 竞技币商店: 100竞技币 = 1星石
```

---

## 3. 技能升级系统 🎯

### 3.1 技能等级范围

```yaml
主动技能:
  - 初始等级: Lv.1
  - 最高等级: Lv.10
  - 升级方式: 消耗技能书

被动技能:
  - 初始等级: Lv.1
  - 最高等级: Lv.10
  - 升级方式: 消耗技能书
```

### 3.2 技能升级材料

#### 技能书类型
```yaml
通用技能书:
  - 小型技能书: 提升 1 级
  - 中型技能书: 提升 2 级
  - 大型技能书: 提升 3 级

专属技能书（按职业）:
  - 武将技能书: 仅武将可用
  - 谋士技能书: 仅谋士可用
  - 弓将技能书: 仅弓将可用
  - 骑将技能书: 仅骑将可用
  - 步将技能书: 仅步将可用
```

#### 升级消耗表

| 技能等级 | 技能书需求 | 金币消耗 |
|---------|-----------|---------|
| Lv.1 → 2 | 小型 x1 | 10,000 |
| Lv.2 → 3 | 小型 x2 | 20,000 |
| Lv.3 → 4 | 小型 x3 | 30,000 |
| Lv.4 → 5 | 中型 x1 | 50,000 |
| Lv.5 → 6 | 中型 x2 | 100,000 |
| Lv.6 → 7 | 中型 x3 | 200,000 |
| Lv.7 → 8 | 大型 x1 | 400,000 |
| Lv.8 → 9 | 大型 x2 | 800,000 |
| Lv.9 → 10 | 大型 x3 | 1,500,000 |

### 3.3 技能升级效果

#### 主动技能提升
```yaml
每级提升:
  - 伤害倍率: +10%
  - 附加效果概率: +5%
  - 冷却时间: 每3级-1回合（最低1回合）

示例 - 诸葛亮【七星续命】:
  Lv.1: 450% 伤害，5回合CD
  Lv.3: 470% 伤害，4回合CD
  Lv.6: 500% 伤害，3回合CD
  Lv.10: 540% 伤害，2回合CD，必定触发全队增益
```

#### 被动技能提升
```yaml
每级提升:
  - 效果数值: +10%
  - 触发概率: +5%

示例 - 关羽【武圣】:
  Lv.1: 忽略防御30%
  Lv.5: 忽略防御50%
  Lv.10: 忽略防御80%，攻击时额外造成20%真实伤害
```

---

## 4. 装备系统 ⚔️

### 4.1 装备槽位

```yaml
每个武将有4个装备槽:
  - 武器槽: 提升攻击力
  - 防具槽: 提升防御力
  - 饰品槽: 提升生命值
  - 宝物槽: 提供特殊效果
```

### 4.2 装备品质

| 品质 | 颜色 | 基础属性 | 附加属性数量 | 强化上限 |
|------|------|---------|-------------|---------|
| 普通 | 白色 | +5% | 0 | +5 |
| 精良 | 绿色 | +10% | 1 | +10 |
| 稀有 | 蓝色 | +15% | 2 | +15 |
| 史诗 | 紫色 | +25% | 3 | +20 |
| 传说 | 金色 | +40% | 4 | +25 |
| 神话 | 红色 | +60% | 5 | +30 |

### 4.3 装备示例

#### 武器 - 青龙偃月刀（传说）
```yaml
基础属性:
  - 攻击力: +40%
  - 暴击率: +10%

附加属性（随机4条）:
  - 暴击伤害: +25%
  - 速度: +15
  - 五行伤害（金）: +20%
  - 技能伤害: +15%

专属效果（关羽装备）:
  - 【武圣之威】攻击时额外造成30%真实伤害
  - 击败敌人回复50%最大生命
```

#### 防具 - 八卦衣（史诗）
```yaml
基础属性:
  - 防御力: +25%
  - 生命值: +20%

附加属性（随机3条）:
  - 五行抗性（全）: +10%
  - 受到伤害-15%
  - 回合开始恢复5%生命

专属效果（诸葛亮装备）:
  - 【八卦奇术】每回合有30%概率免疫一次伤害
```

### 4.4 装备强化

#### 强化等级
```yaml
强化范围: +0 → +30
强化消耗: 强化石 + 金币

每次强化:
  - +1~+5: 100%成功率
  - +6~+10: 90%成功率
  - +11~+15: 70%成功率
  - +16~+20: 50%成功率
  - +21~+25: 30%成功率
  - +26~+30: 10%成功率

失败惩罚:
  - +0~+10: 不降级
  - +11~+20: 降1级
  - +21~+30: 降2级
```

#### 强化属性加成
```python
def calc_enhance_bonus(base_value, enhance_level):
    """计算强化加成"""
    return base_value * (1 + enhance_level * 0.05)

# 示例：攻击力+40%的装备
# +0: 40%
# +10: 60%
# +20: 90%
# +30: 115%
```

### 4.5 装备获取

```yaml
主线关卡:
  - 普通/精良装备随机掉落
  - Boss关卡: 稀有装备

每日副本:
  - 宝物阁: 稀有/史诗装备

周常Boss:
  - 史诗/传说装备

世界Boss:
  - 传说/神话装备

装备副本（特殊）:
  - 三国名将专属装备副本
  - 掉落对应武将的专属装备
```

---

## 5. 觉醒系统 🌟

### 5.1 觉醒条件

```yaml
基础条件:
  - 等级达到 Lv.50
  - 星级达到 ★3
  - 完成专属觉醒任务

觉醒材料:
  - 觉醒石 x50（按稀有度）
  - 同名卡 x1
  - 金币 1,000,000
```

### 5.2 觉醒效果

#### 属性提升
```yaml
全属性: +30%
额外效果:
  - 解锁第二个主动技能
  - 强化现有被动技能
  - 改变卡面外观（觉醒形态）
  - 获得专属称号
```

#### 觉醒技能示例

**关羽觉醒 - 【武圣降临】**
```yaml
觉醒前:
  主动技能: 过五关斩六将
  被动技能: 武圣

觉醒后:
  主动技能1: 过五关斩六将（强化）
    - 伤害: 350% → 500%
    - 击败目标后继续攻击，最多5次

  主动技能2: 单刀赴会（新增）
    - 对单体敌人造成600%伤害
    - 自身获得无敌状态（1回合）
    - CD: 6回合

  被动技能: 武圣·觉醒
    - 忽略防御: 30% → 50%
    - 攻击时额外造成30%真实伤害
    - 生命低于30%时，攻击力翻倍
```

**诸葛亮觉醒 - 【卧龙出山】**
```yaml
觉醒前:
  主动技能: 七星续命
  被动技能: 卧龙

觉醒后:
  主动技能1: 七星续命（强化）
    - AOE伤害: 450% → 600%
    - 全队回复: 200% → 300%
    - 全队增益持续: 3回合 → 5回合

  主动技能2: 草船借箭（新增）
    - 为全队增加护盾（吸收500%攻击力伤害）
    - 反弹所有受到的伤害
    - CD: 7回合

  被动技能: 卧龙·天命
    - 战斗开始全队增益: 攻击+25% → +40%
    - 每回合恢复: 10% → 15%
    - 释放技能时，50%概率重置CD
    - 队友阵亡时，诸葛亮获得其50%属性
```

### 5.3 觉醒任务

```yaml
任务类型（以关羽为例）:
  1. 使用关羽击败100个敌人
  2. 使用关羽完成单挑模式（1v1击败SSR敌人）
  3. 使用关羽达成10次连胜
  4. 收集【青龙偃月刀】装备

任务奖励:
  - 觉醒资格
  - 觉醒石 x10
  - 专属装备碎片 x50
```

---

## 6. 突破系统 💎

### 6.1 突破机制

```yaml
解锁条件:
  - 等级达到 Lv.100
  - 星级达到 ★5
  - 完成觉醒

突破上限: 最多3次突破
```

### 6.2 突破材料

| 突破次数 | 材料需求 | 金币消耗 |
|---------|---------|---------|
| 第1次突破 | 突破石 x100, 同名卡 x3 | 5,000,000 |
| 第2次突破 | 突破石 x200, 同名卡 x5 | 10,000,000 |
| 第3次突破 | 突破石 x500, 同名卡 x10 | 30,000,000 |

### 6.3 突破效果

```yaml
每次突破:
  - 等级上限: +20（最高Lv.160）
  - 全属性: +20%
  - 技能等级上限: +5（最高Lv.25）
  - 装备槽位: +1（最多7个装备槽）

第3次突破额外效果:
  - 解锁终极被动
  - 获得专属光环效果
  - 战斗时全队获得增益
```

---

## 7. 数值成长曲线 📊

### 7.1 完全体武将属性对比

#### 诸葛亮（UR）完全体
```yaml
基础（Lv.1, ★1）:
  攻击: 520
  防御: 400
  生命: 5200

满级（Lv.100, ★5, 觉醒, 突破x3）:
  攻击: 520 × 1.04^99 × 2.1 × 1.3 × 1.2^3 ≈ 15,890
  防御: 400 × 1.04^99 × 2.1 × 1.3 × 1.2^3 ≈ 12,223
  生命: 5200 × 1.04^99 × 2.1 × 1.3 × 1.2^3 ≈ 158,900

战力评分: 约 50,000
```

### 7.2 培养成本预估

#### 单个UR武将培养至完全体

| 项目 | 材料/资源 | 数量 | 获取难度 |
|------|----------|------|---------|
| 升级至Lv.100 | 经验值 | 8,395,000 | 中等 |
| 升星至★5 | 同名卡或万能星石 | 11张 或 200星石 | 困难 |
| 技能升至Lv.10 | 技能书 | 大型x6 | 中等 |
| 觉醒 | 觉醒石、同名卡 | 50石、1卡 | 困难 |
| 突破x3 | 突破石、同名卡 | 800石、18卡 | 极难 |
| 装备满强化 | 强化石、金币 | 海量 | 困难 |
| **总金币消耗** | - | **约 5000万** | - |
| **总时间预估** | - | **3-6个月** | - |

---

## 8. 技术实现方案 💻

### 8.1 数据库设计

#### 用户卡牌扩展表
```sql
-- 扩展 user_cards 表
ALTER TABLE user_cards ADD COLUMN star_level INTEGER DEFAULT 1;
ALTER TABLE user_cards ADD COLUMN awaken_level INTEGER DEFAULT 0;
ALTER TABLE user_cards ADD COLUMN breakthrough_level INTEGER DEFAULT 0;
ALTER TABLE user_cards ADD COLUMN main_skill_level INTEGER DEFAULT 1;
ALTER TABLE user_cards ADD COLUMN passive_skill_level INTEGER DEFAULT 1;

-- 装备表
CREATE TABLE equipments (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    type VARCHAR(20),              -- weapon/armor/accessory/treasure
    quality VARCHAR(20),            -- common/rare/epic/legendary/mythic
    base_stat_type VARCHAR(20),    -- attack/defense/hp
    base_stat_value FLOAT,
    enhance_level INTEGER DEFAULT 0,
    owner_card_id INTEGER,
    created_at DATETIME,
    FOREIGN KEY (owner_card_id) REFERENCES user_cards(id)
);

-- 装备附加属性表
CREATE TABLE equipment_stats (
    id INTEGER PRIMARY KEY,
    equipment_id INTEGER,
    stat_type VARCHAR(20),         -- crit_rate/crit_dmg/speed/etc
    stat_value FLOAT,
    FOREIGN KEY (equipment_id) REFERENCES equipments(id)
);

-- 材料物品表
CREATE TABLE user_items (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    item_type VARCHAR(50),         -- exp_potion/skill_book/star_stone/etc
    item_subtype VARCHAR(50),      -- small/medium/large, warrior/mage/etc
    quantity INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 8.2 API 路由设计

```python
# app/routes/growth.py

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import db, UserCard, User, Card

bp = Blueprint('growth', __name__, url_prefix='/growth')

@bp.route('/level-up', methods=['POST'])
@login_required
def level_up_card():
    """升级卡牌"""
    data = request.json
    user_card_id = data.get('user_card_id')
    exp_items = data.get('exp_items', [])  # [{item_id, quantity}]

    user_card = UserCard.query.get(user_card_id)
    if not user_card or user_card.user_id != current_user.id:
        return jsonify({'error': '卡牌不存在'}), 404

    # 计算总经验
    total_exp = 0
    for item in exp_items:
        # 消耗经验药水，计算经验值
        pass

    # 添加经验并升级
    user_card.exp += total_exp
    while user_card.exp >= get_exp_required(user_card.level):
        if user_card.level >= 100:
            break
        user_card.exp -= get_exp_required(user_card.level)
        user_card.level += 1

    db.session.commit()

    return jsonify({
        'success': True,
        'new_level': user_card.level,
        'current_exp': user_card.exp,
        'exp_required': get_exp_required(user_card.level)
    })

@bp.route('/star-up', methods=['POST'])
@login_required
def star_up_card():
    """升星卡牌"""
    data = request.json
    user_card_id = data.get('user_card_id')
    material_type = data.get('material_type')  # 'duplicate' or 'star_stone'

    user_card = UserCard.query.get(user_card_id)
    if not user_card or user_card.user_id != current_user.id:
        return jsonify({'error': '卡牌不存在'}), 404

    if user_card.star_level >= 5:
        return jsonify({'error': '已达最高星级'}), 400

    # 检查材料并消耗
    required = get_star_up_requirements(user_card.star_level)

    if material_type == 'star_stone':
        # 使用万能星石
        user_item = get_user_item(current_user.id, 'star_stone')
        if user_item.quantity < required['star_stones']:
            return jsonify({'error': '星石不足'}), 400
        user_item.quantity -= required['star_stones']
    else:
        # 使用同名卡
        duplicates = get_duplicate_cards(current_user.id, user_card.card_id)
        if len(duplicates) < required['duplicates']:
            return jsonify({'error': '同名卡不足'}), 400
        # 消耗同名卡
        for dup in duplicates[:required['duplicates']]:
            db.session.delete(dup)

    # 检查金币
    if current_user.coins < required['coins']:
        return jsonify({'error': '金币不足'}), 400

    current_user.coins -= required['coins']
    user_card.star_level += 1

    db.session.commit()

    return jsonify({
        'success': True,
        'new_star_level': user_card.star_level
    })

@bp.route('/skill-upgrade', methods=['POST'])
@login_required
def upgrade_skill():
    """升级技能"""
    data = request.json
    user_card_id = data.get('user_card_id')
    skill_type = data.get('skill_type')  # 'main' or 'passive'
    skill_books = data.get('skill_books', [])  # [{book_type, quantity}]

    user_card = UserCard.query.get(user_card_id)
    if not user_card or user_card.user_id != current_user.id:
        return jsonify({'error': '卡牌不存在'}), 404

    # 计算技能等级提升
    levels_gained = 0
    for book in skill_books:
        book_levels = {'small': 1, 'medium': 2, 'large': 3}
        levels_gained += book_levels[book['book_type']] * book['quantity']
        # 消耗技能书
        consume_skill_book(current_user.id, book['book_type'], book['quantity'])

    # 升级技能
    if skill_type == 'main':
        user_card.main_skill_level = min(10, user_card.main_skill_level + levels_gained)
    else:
        user_card.passive_skill_level = min(10, user_card.passive_skill_level + levels_gained)

    db.session.commit()

    return jsonify({
        'success': True,
        'new_level': user_card.main_skill_level if skill_type == 'main' else user_card.passive_skill_level
    })

@bp.route('/awaken', methods=['POST'])
@login_required
def awaken_card():
    """觉醒卡牌"""
    data = request.json
    user_card_id = data.get('user_card_id')

    user_card = UserCard.query.get(user_card_id)
    if not user_card or user_card.user_id != current_user.id:
        return jsonify({'error': '卡牌不存在'}), 404

    # 检查觉醒条件
    if user_card.level < 50:
        return jsonify({'error': '等级不足Lv.50'}), 400
    if user_card.star_level < 3:
        return jsonify({'error': '星级不足★3'}), 400
    if user_card.awaken_level >= 1:
        return jsonify({'error': '已完成觉醒'}), 400

    # 检查觉醒材料
    awaken_stones = get_user_item(current_user.id, 'awaken_stone')
    if awaken_stones.quantity < 50:
        return jsonify({'error': '觉醒石不足'}), 400

    # 检查金币
    if current_user.coins < 1000000:
        return jsonify({'error': '金币不足'}), 400

    # 执行觉醒
    awaken_stones.quantity -= 50
    current_user.coins -= 1000000
    user_card.awaken_level = 1

    db.session.commit()

    return jsonify({
        'success': True,
        'message': '觉醒成功！'
    })

@bp.route('/equip', methods=['POST'])
@login_required
def equip_equipment():
    """装备道具"""
    data = request.json
    user_card_id = data.get('user_card_id')
    equipment_id = data.get('equipment_id')
    slot = data.get('slot')  # weapon/armor/accessory/treasure

    user_card = UserCard.query.get(user_card_id)
    equipment = Equipment.query.get(equipment_id)

    # 验证权限
    if not user_card or user_card.user_id != current_user.id:
        return jsonify({'error': '卡牌不存在'}), 404
    if not equipment or equipment.user_id != current_user.id:
        return jsonify({'error': '装备不存在'}), 404

    # 卸下当前装备
    old_equipment = Equipment.query.filter_by(
        owner_card_id=user_card_id,
        type=slot
    ).first()
    if old_equipment:
        old_equipment.owner_card_id = None

    # 装备新装备
    equipment.owner_card_id = user_card_id

    db.session.commit()

    return jsonify({'success': True})
```

### 8.3 前端界面设计

#### 成长界面布局
```html
<!-- 成长主界面 -->
<div class="growth-panel">
    <!-- 左侧：卡牌展示 -->
    <div class="card-display">
        <div class="card-model">
            <!-- 3D卡牌模型 -->
            <img src="{{ card.image_url }}" alt="{{ card.name }}">

            <!-- 等级/星级显示 -->
            <div class="level-badge">Lv.{{ user_card.level }}</div>
            <div class="star-badge">
                {% for i in range(user_card.star_level) %}
                    ⭐
                {% endfor %}
            </div>

            <!-- 觉醒标记 -->
            {% if user_card.awaken_level > 0 %}
                <div class="awaken-badge">觉醒</div>
            {% endif %}
        </div>

        <!-- 基础属性 -->
        <div class="base-stats">
            <div class="stat">
                <span>攻击力</span>
                <span>{{ calc_attack(user_card) }}</span>
            </div>
            <div class="stat">
                <span>防御力</span>
                <span>{{ calc_defense(user_card) }}</span>
            </div>
            <div class="stat">
                <span>生命值</span>
                <span>{{ calc_hp(user_card) }}</span>
            </div>
        </div>
    </div>

    <!-- 右侧：成长选项 -->
    <div class="growth-tabs">
        <ul class="nav-tabs">
            <li class="active">升级</li>
            <li>升星</li>
            <li>技能</li>
            <li>装备</li>
            <li>觉醒</li>
        </ul>

        <!-- 升级面板 -->
        <div class="tab-content active" id="level-up">
            <div class="exp-bar">
                <div class="exp-progress" style="width: {{ (user_card.exp / exp_required) * 100 }}%"></div>
                <span>{{ user_card.exp }} / {{ exp_required }}</span>
            </div>

            <div class="material-list">
                <!-- 经验药水列表 -->
                <div class="material-item" data-exp="1000">
                    <img src="/static/items/exp_small.png">
                    <span>小型经验药水 x{{ small_exp_count }}</span>
                    <button class="use-btn">使用</button>
                </div>
                <!-- ... 更多材料 -->
            </div>

            <button class="level-up-btn">升级</button>
        </div>

        <!-- 升星面板 -->
        <div class="tab-content" id="star-up">
            <!-- 升星界面 -->
        </div>

        <!-- 技能面板 -->
        <div class="tab-content" id="skills">
            <!-- 技能升级界面 -->
        </div>

        <!-- 装备面板 -->
        <div class="tab-content" id="equipment">
            <!-- 装备管理界面 -->
        </div>

        <!-- 觉醒面板 -->
        <div class="tab-content" id="awaken">
            <!-- 觉醒界面 -->
        </div>
    </div>
</div>
```

---

## 9. 实施优先级与时间预估 ⏱️

### Phase 1: 基础升级系统（1周）
```yaml
✅ 等级系统（Lv.1-100）
✅ 经验值计算
✅ 属性成长公式
✅ 经验药水功能
```

### Phase 2: 升星系统（1周）
```yaml
✅ 星级提升（★1-★5）
✅ 万能星石机制
✅ 同名卡吞噬
✅ 升星属性加成
```

### Phase 3: 技能升级（1周）
```yaml
✅ 主动技能升级
✅ 被动技能升级
✅ 技能书系统
✅ 技能效果提升
```

### Phase 4: 装备系统（2周）
```yaml
✅ 装备槽位（4个）
✅ 装备品质系统
✅ 装备强化机制
✅ 装备附加属性
```

### Phase 5: 觉醒系统（1-2周）
```yaml
✅ 觉醒条件判定
✅ 觉醒任务系统
✅ 第二主动技能
✅ 觉醒外观变化
```

### Phase 6: 突破系统（1周）
```yaml
✅ 突破材料系统
✅ 等级上限提升
✅ 额外装备槽
✅ 终极被动技能
```

**总开发周期**: 7-9周

---

## 💡 总结

本成长系统设计提供了：

✅ **完整的养成路径** - 从Lv.1到完全体的清晰成长线
✅ **多维度培养** - 等级、星级、技能、装备、觉醒、突破
✅ **合理的数值曲线** - 前期快速，后期深度
✅ **丰富的材料系统** - 多种获取途径，平衡付费与肝度
✅ **可扩展的架构** - 易于添加新的成长维度

**预计培养一个完全体UR武将需要**:
- 💰 金币: 约 5000万
- ⏱️ 时间: 3-6个月
- 🎴 同名卡: 约30张（或大量星石/突破石替代）

---

是否需要我开始实现某个具体模块？🚀
