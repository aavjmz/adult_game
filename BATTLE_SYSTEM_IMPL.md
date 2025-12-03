# ⚔️ 战斗系统实现指南

本文档说明如何将游戏设计转化为实际代码实现。

---

## 📋 目录

1. [数据库模型扩展](#数据库模型扩展)
2. [战斗系统核心代码](#战斗系统核心代码)
3. [前端UI实现](#前端ui实现)
4. [实现路线图](#实现路线图)

---

## 🗄️ 数据库模型扩展

### 1. 扩展Card模型

```python
# 在 app/models.py 中扩展

class Card(db.Model):
    """卡牌模型 - 增强版"""
    __tablename__ = 'cards'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rarity = db.Column(db.String(10), nullable=False)  # N, R, SR, SSR, UR

    # ===== 基础战斗属性 =====
    attack = db.Column(db.Integer, default=100)
    defense = db.Column(db.Integer, default=100)
    hp = db.Column(db.Integer, default=1000)

    # ===== 新增属性 ⭐ =====
    speed = db.Column(db.Integer, default=50)           # 速度（行动顺序）
    critical = db.Column(db.Float, default=5.0)         # 暴击率（%）
    critical_dmg = db.Column(db.Float, default=150.0)   # 暴击伤害（%）

    # ===== 元素和职业 ⭐ =====
    element = db.Column(db.String(20), default='无')    # 火/水/雷/风/光/暗/无
    job_class = db.Column(db.String(20), default='战士') # 战士/法师/坦克/刺客/辅助

    # ===== 视觉效果 =====
    is_golden = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(200))
    description = db.Column(db.Text)

    # ===== 主动技能 =====
    skill_name = db.Column(db.String(100))
    skill_type = db.Column(db.String(20))               # damage/buff/debuff/heal
    skill_description = db.Column(db.Text)
    skill_damage_multiplier = db.Column(db.Float, default=1.5)
    skill_cooldown = db.Column(db.Integer, default=3)   # 冷却回合数
    skill_target = db.Column(db.String(20), default='single')  # single/all/random

    # ===== 被动技能 ⭐新增 =====
    passive_skill_name = db.Column(db.String(100))
    passive_skill_description = db.Column(db.Text)
    passive_skill_effect = db.Column(db.String(200))    # JSON格式存储

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    user_cards = db.relationship('UserCard', backref='card', lazy='dynamic')

    def to_battle_dict(self):
        """转换为战斗用的字典"""
        return {
            'id': self.id,
            'name': self.name,
            'rarity': self.rarity,
            'attack': self.attack,
            'defense': self.defense,
            'hp': self.hp,
            'max_hp': self.hp,
            'current_hp': self.hp,
            'speed': self.speed,
            'critical': self.critical,
            'critical_dmg': self.critical_dmg,
            'element': self.element,
            'job_class': self.job_class,
            'skill_name': self.skill_name,
            'skill_type': self.skill_type,
            'skill_damage_multiplier': self.skill_damage_multiplier,
            'skill_cooldown': self.skill_cooldown,
            'skill_current_cd': 0,  # 当前冷却
            'buffs': [],  # 增益效果列表
            'debuffs': [],  # 减益效果列表
        }
```

### 2. 新增Buff/Debuff模型

```python
class BuffDebuff(db.Model):
    """Buff/Debuff效果模型"""
    __tablename__ = 'buff_debuffs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(10))  # 'buff' 或 'debuff'

    # 效果
    effect_type = db.Column(db.String(30))  # attack_up, defense_down, dot, stun等
    effect_value = db.Column(db.Float)       # 数值或百分比
    duration = db.Column(db.Integer)         # 持续回合数

    # 描述
    description = db.Column(db.Text)
    icon_url = db.Column(db.String(200))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

---

## ⚔️ 战斗系统核心代码

### 1. 战斗引擎类

```python
# 新文件: app/battle_engine.py

import random
from typing import List, Dict, Tuple

class BattleEngine:
    """战斗引擎 - 增强版"""

    def __init__(self, player_cards, enemy_cards):
        """
        初始化战斗

        Args:
            player_cards: 玩家卡牌列表
            enemy_cards: 敌方卡牌列表
        """
        self.player_team = [card.to_battle_dict() for card in player_cards]
        self.enemy_team = [card.to_battle_dict() for card in enemy_cards]

        # 战斗日志
        self.battle_log = []

        # 回合数
        self.round_num = 0
        self.max_rounds = 30

        self.log('战斗开始！', 'start')

    def log(self, message, log_type='info'):
        """记录战斗日志"""
        self.battle_log.append({
            'type': log_type,
            'round': self.round_num,
            'message': message
        })

    def execute_battle(self) -> Dict:
        """
        执行战斗主循环

        Returns:
            战斗结果字典
        """
        while self.round_num < self.max_rounds:
            self.round_num += 1
            self.log(f'=== 第 {self.round_num} 回合 ===', 'round')

            # 1. 回合开始阶段
            self.round_start_phase()

            # 2. 行动阶段
            self.action_phase()

            # 3. 检查胜负
            result = self.check_battle_end()
            if result:
                return result

            # 4. 回合结束阶段
            self.round_end_phase()

        # 超时平局
        self.log('战斗超时，判定为平局', 'timeout')
        return {
            'is_victory': False,
            'log': self.battle_log,
            'reason': 'timeout'
        }

    def round_start_phase(self):
        """回合开始阶段"""
        # 减少技能冷却
        for card in self.player_team + self.enemy_team:
            if card['skill_current_cd'] > 0:
                card['skill_current_cd'] -= 1

        # Buff/Debuff持续时间-1
        for card in self.player_team + self.enemy_team:
            card['buffs'] = [b for b in card['buffs'] if self.decrease_buff_duration(b)]
            card['debuffs'] = [d for d in card['debuffs'] if self.decrease_buff_duration(d)]

    def action_phase(self):
        """行动阶段 - 按速度排序"""
        # 合并双方所有存活角色
        all_actors = []
        for i, card in enumerate(self.player_team):
            if card['current_hp'] > 0:
                all_actors.append({'card': card, 'team': 'player', 'index': i})

        for i, card in enumerate(self.enemy_team):
            if card['current_hp'] > 0:
                all_actors.append({'card': card, 'team': 'enemy', 'index': i})

        # 按速度排序（速度高的先行动）
        all_actors.sort(key=lambda x: x['card']['speed'], reverse=True)

        # 依次行动
        for actor in all_actors:
            card = actor['card']

            # 检查是否被控制（眩晕/冰冻）
            if self.is_controlled(card):
                self.log(f"{card['name']} 被控制，无法行动", 'control')
                continue

            # 决定行动
            if actor['team'] == 'player':
                enemies = self.enemy_team
            else:
                enemies = self.player_team

            # 选择目标
            target = self.select_target(card, enemies)
            if not target:
                continue

            # 执行行动
            self.perform_action(card, target, actor['team'])

    def perform_action(self, attacker, defender, attacker_team):
        """
        执行一次行动

        Args:
            attacker: 攻击者
            defender: 防御者
            attacker_team: 攻击者队伍
        """
        # 判断是否使用技能
        use_skill = False
        if attacker['skill_current_cd'] == 0:
            # 简单AI: 技能可用时有70%概率使用
            if random.random() < 0.7:
                use_skill = True

        if use_skill:
            self.use_skill(attacker, defender, attacker_team)
        else:
            self.normal_attack(attacker, defender)

    def normal_attack(self, attacker, defender):
        """普通攻击"""
        damage, is_critical = self.calculate_damage(attacker, defender, 1.0)

        defender['current_hp'] -= damage
        defender['current_hp'] = max(0, defender['current_hp'])

        crit_text = '[暴击]' if is_critical else ''
        self.log(
            f"{attacker['name']} 攻击 {defender['name']}，造成 {damage} 点伤害 {crit_text}",
            'critical' if is_critical else 'attack'
        )

        if defender['current_hp'] <= 0:
            self.log(f"{defender['name']} 被击败！", 'defeat')

    def use_skill(self, attacker, defender, attacker_team):
        """使用技能"""
        skill_multiplier = attacker['skill_damage_multiplier']
        damage, is_critical = self.calculate_damage(attacker, defender, skill_multiplier)

        defender['current_hp'] -= damage
        defender['current_hp'] = max(0, defender['current_hp'])

        self.log(
            f"{attacker['name']} 使用 [{attacker['skill_name']}]！",
            'skill'
        )

        crit_text = '[暴击]' if is_critical else ''
        self.log(
            f"对 {defender['name']} 造成 {damage} 点伤害 {crit_text}",
            'critical' if is_critical else 'damage'
        )

        # 设置冷却
        attacker['skill_current_cd'] = attacker['skill_cooldown']

        if defender['current_hp'] <= 0:
            self.log(f"{defender['name']} 被击败！", 'defeat')

    def calculate_damage(self, attacker, defender, multiplier) -> Tuple[int, bool]:
        """
        伤害计算 - 增强版

        Args:
            attacker: 攻击者
            defender: 防御者
            multiplier: 技能倍率

        Returns:
            (伤害值, 是否暴击)
        """
        # 1. 基础伤害
        base_damage = attacker['attack'] * multiplier

        # 2. 防御减免
        defense_reduction = defender['defense'] / (defender['defense'] + 100)
        damage = base_damage * (1 - defense_reduction)

        # 3. 元素克制
        element_bonus = self.get_element_bonus(
            attacker['element'],
            defender['element']
        )
        damage *= element_bonus

        # 4. 暴击判定
        is_critical = random.random() * 100 < attacker['critical']
        if is_critical:
            damage *= (attacker['critical_dmg'] / 100)

        # 5. 随机波动 (90% - 110%)
        damage *= random.uniform(0.9, 1.1)

        # 6. Buff/Debuff加成
        damage *= self.get_buff_multiplier(attacker, defender)

        return int(damage), is_critical

    def get_element_bonus(self, attacker_element, defender_element) -> float:
        """
        获取元素克制加成

        Returns:
            伤害倍率
        """
        counters = {
            '火': '风',
            '风': '雷',
            '雷': '水',
            '水': '火',
            '光': '暗',
            '暗': '光'
        }

        if counters.get(attacker_element) == defender_element:
            return 1.3  # 克制: +30%
        elif counters.get(defender_element) == attacker_element:
            return 0.8  # 被克制: -20%
        else:
            return 1.0  # 无关系

    def get_buff_multiplier(self, attacker, defender) -> float:
        """获取Buff/Debuff加成"""
        multiplier = 1.0

        # 攻击者的攻击Buff
        for buff in attacker['buffs']:
            if buff['effect_type'] == 'attack_up':
                multiplier *= (1 + buff['value'])

        # 防御者的防御Debuff
        for debuff in defender['debuffs']:
            if debuff['effect_type'] == 'defense_down':
                multiplier *= (1 + abs(debuff['value']))

        return multiplier

    def select_target(self, attacker, enemies) -> Dict:
        """
        选择攻击目标

        Args:
            attacker: 攻击者
            enemies: 敌方队伍

        Returns:
            目标卡牌
        """
        alive_enemies = [e for e in enemies if e['current_hp'] > 0]

        if not alive_enemies:
            return None

        # 简单AI: 攻击血量最低的
        target = min(alive_enemies, key=lambda x: x['current_hp'])
        return target

    def is_controlled(self, card) -> bool:
        """检查是否被控制"""
        for debuff in card['debuffs']:
            if debuff['effect_type'] in ['stun', 'freeze']:
                return True
        return False

    def decrease_buff_duration(self, buff) -> bool:
        """
        减少Buff持续时间

        Returns:
            是否继续保留
        """
        buff['duration'] -= 1
        return buff['duration'] > 0

    def check_battle_end(self) -> Dict:
        """
        检查战斗是否结束

        Returns:
            战斗结果（如果未结束返回None）
        """
        # 检查玩家是否全灭
        player_alive = any(card['current_hp'] > 0 for card in self.player_team)

        # 检查敌人是否全灭
        enemy_alive = any(card['current_hp'] > 0 for card in self.enemy_team)

        if not enemy_alive:
            self.log('🎉 胜利！击败了所有敌人！', 'victory')
            return {
                'is_victory': True,
                'log': self.battle_log,
                'reason': 'enemy_defeated'
            }

        if not player_alive:
            self.log('😢 战败...你的队伍被击败了', 'defeat')
            return {
                'is_victory': False,
                'log': self.battle_log,
                'reason': 'player_defeated'
            }

        return None

    def round_end_phase(self):
        """回合结束阶段"""
        # DOT伤害结算（燃烧、中毒等）
        for card in self.player_team + self.enemy_team:
            if card['current_hp'] <= 0:
                continue

            for debuff in card['debuffs']:
                if debuff['effect_type'] == 'dot':
                    damage = int(card['max_hp'] * debuff['value'])
                    card['current_hp'] -= damage
                    card['current_hp'] = max(0, card['current_hp'])

                    self.log(
                        f"{card['name']} 受到持续伤害 {damage} 点",
                        'dot'
                    )

                    if card['current_hp'] <= 0:
                        self.log(f"{card['name']} 被持续伤害击败！", 'defeat')
```

### 2. 集成到Flask路由

```python
# 修改 app/routes/battle.py

from app.battle_engine import BattleEngine

@bp.route('/start', methods=['POST'])
@login_required
def start():
    """开始战斗 - 使用新战斗引擎"""
    data = request.get_json()
    player_card_ids = data.get('card_ids', [])

    # ... 验证代码（同之前）...

    # 使用新战斗引擎
    battle_engine = BattleEngine(player_cards, enemy_cards)
    battle_result = battle_engine.execute_battle()

    # ... 奖励计算和保存（同之前）...

    return jsonify({
        'success': True,
        'battle_log': battle_result['log'],
        'is_victory': battle_result['is_victory'],
        'rewards': {...},
        'current_resources': {...}
    })
```

---

## 🎨 前端UI实现

### 1. 战斗页面HTML增强

```html
<!-- app/templates/battle_v2.html -->

{% extends "base.html" %}

{% block content %}
<div class="battle-container">
    <!-- 顶部信息栏 -->
    <div class="battle-header">
        <div class="round-info">回合: <span id="currentRound">0</span> / <span id="maxRound">30</span></div>
        <div class="battle-controls">
            <button id="autoBtn" class="btn btn-secondary">自动: OFF</button>
            <button id="speedBtn" class="btn btn-secondary">速度: x1</button>
            <button id="pauseBtn" class="btn btn-secondary">暂停</button>
        </div>
    </div>

    <!-- 战场 -->
    <div class="battlefield">
        <!-- 敌方队伍 -->
        <div class="enemy-team" id="enemyTeam">
            <h3>敌方队伍</h3>
            <div class="card-slots enemy-slots"></div>
        </div>

        <!-- 战场中线 -->
        <div class="battlefield-divider"></div>

        <!-- 我方队伍 -->
        <div class="player-team" id="playerTeam">
            <div class="card-slots player-slots"></div>
            <h3>我方队伍</h3>
        </div>
    </div>

    <!-- 战斗日志 -->
    <div class="battle-log-container">
        <h3>战斗日志</h3>
        <div class="battle-log" id="battleLog"></div>
    </div>

    <!-- 操作区 -->
    <div class="battle-actions" id="battleActions" style="display:none;">
        <button class="action-btn" id="attackBtn">
            <span>普通攻击</span>
        </button>
        <button class="action-btn" id="skillBtn">
            <span>使用技能</span>
            <small>CD: <span id="skillCd">0</span></small>
        </button>
        <button class="action-btn" id="defendBtn">
            <span>防御</span>
        </button>
    </div>

    <!-- 战斗结果 -->
    <div class="battle-result" id="battleResult" style="display:none;">
        <div class="result-content">
            <h2 id="resultTitle"></h2>
            <div id="resultRewards"></div>
            <button class="btn btn-primary" onclick="location.reload()">再战一次</button>
            <button class="btn btn-secondary" onclick="location.href='/cards/'">返回</button>
        </div>
    </div>
</div>

<style>
.battlefield {
    background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
    padding: 30px;
    border-radius: 15px;
    margin: 20px 0;
}

.card-slots {
    display: flex;
    justify-content: center;
    gap: 15px;
    margin: 20px 0;
}

.battle-card {
    width: 120px;
    background: white;
    border-radius: 10px;
    padding: 10px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    transition: transform 0.3s;
}

.battle-card.enemy {
    border: 2px solid #e74c3c;
}

.battle-card.player {
    border: 2px solid #3498db;
}

.battle-card.defeated {
    opacity: 0.3;
    filter: grayscale(100%);
}

.battle-card.attacking {
    animation: attack 0.8s ease-in-out;
}

@keyframes attack {
    0%, 100% { transform: translateX(0); }
    30% { transform: translateX(20px); }
    60% { transform: translateX(10px); }
}

.hp-bar-container {
    background: #ddd;
    height: 10px;
    border-radius: 5px;
    overflow: hidden;
    margin: 5px 0;
}

.hp-bar {
    height: 100%;
    background: linear-gradient(90deg, #e74c3c, #c0392b);
    transition: width 0.5s;
}

.hp-bar.player {
    background: linear-gradient(90deg, #3498db, #2980b9);
}

.damage-number {
    position: absolute;
    font-size: 24px;
    font-weight: bold;
    color: #e74c3c;
    animation: damage-float 1s ease-out forwards;
    pointer-events: none;
}

.damage-number.critical {
    font-size: 32px;
    color: #f39c12;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
}

@keyframes damage-float {
    0% {
        transform: translateY(0) scale(0.5);
        opacity: 1;
    }
    100% {
        transform: translateY(-50px) scale(1.2);
        opacity: 0;
    }
}

.battle-log {
    max-height: 300px;
    overflow-y: auto;
    background: #f8f9fa;
    padding: 15px;
    border-radius: 10px;
    font-family: monospace;
}

.log-entry {
    padding: 5px;
    margin: 3px 0;
    border-radius: 3px;
}

.log-entry.round {
    background: #3498db;
    color: white;
    font-weight: bold;
}

.log-entry.critical {
    background: #f39c12;
    color: white;
}

.log-entry.victory {
    background: #27ae60;
    color: white;
    font-weight: bold;
}

.log-entry.defeat {
    background: #e74c3c;
    color: white;
    font-weight: bold;
}
</style>

<script>
// 战斗前端逻辑
class BattleFrontend {
    constructor() {
        this.isAuto = false;
        this.speed = 1;  // 1x, 2x, 4x
        this.currentLogIndex = 0;
    }

    async startBattle(cardIds) {
        // 发送战斗请求
        const response = await fetch('/battle/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({card_ids: cardIds})
        });

        const result = await response.json();

        if (result.success) {
            // 播放战斗动画
            await this.playBattle(result.battle_log);

            // 显示结果
            this.showResult(result);
        }
    }

    async playBattle(battleLog) {
        for (const entry of battleLog) {
            await this.playLogEntry(entry);
            await this.delay(1000 / this.speed);
        }
    }

    playLogEntry(entry) {
        // 根据日志类型播放不同动画
        switch(entry.type) {
            case 'attack':
                this.playAttackAnimation(entry);
                break;
            case 'critical':
                this.playCriticalAnimation(entry);
                break;
            case 'defeat':
                this.playDefeatAnimation(entry);
                break;
        }

        // 添加到日志
        this.addLogMessage(entry.message, entry.type);
    }

    playAttackAnimation(entry) {
        // 实现攻击动画
        // ...
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    addLogMessage(message, type) {
        const logDiv = document.getElementById('battleLog');
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.textContent = message;
        logDiv.appendChild(entry);
        logDiv.scrollTop = logDiv.scrollHeight;
    }
}

// 初始化
const battleFrontend = new BattleFrontend();
</script>
{% endblock %}
```

---

## 🛣️ 实现路线图

### Phase 1: 核心系统升级（1-2周）

**Week 1**:
```
✅ Day 1-2: 扩展数据库模型
  - 添加speed, critical等新属性
  - 数据库迁移脚本
  - 更新初始化卡牌数据

✅ Day 3-4: 实现增强战斗引擎
  - BattleEngine类
  - 新伤害计算公式
  - 元素克制系统

✅ Day 5-7: 测试和调试
  - 单元测试
  - 平衡性测试
  - Bug修复
```

**Week 2**:
```
✅ Day 1-3: 前端战斗UI
  - 新战斗界面
  - 动画效果
  - 日志展示

✅ Day 4-5: Buff/Debuff系统
  - 数据模型
  - 效果逻辑
  - UI显示

✅ Day 6-7: 集成测试
  - 完整流程测试
  - 性能优化
```

### Phase 2: 成长系统（2-3周）

```
Week 1: 升级系统
Week 2: 升星系统
Week 3: 装备系统（基础）
```

### Phase 3: 玩法扩展（3-4周）

```
Week 1-2: 关卡系统
Week 3: 每日副本
Week 4: 自动战斗
```

---

## 📝 快速开始

### 1. 更新数据库
```bash
# 备份当前数据库
cp game.db game.db.backup

# 运行迁移脚本
python migrate_database.py
```

### 2. 创建测试卡牌
```python
# 创建带新属性的测试卡牌
python create_test_cards.py
```

### 3. 测试新战斗系统
```bash
# 运行单元测试
python -m pytest tests/test_battle_engine.py

# 启动游戏
python run.py
```

---

## 🎯 总结

本实现指南提供了：

✅ **数据库模型扩展**: 新增speed、critical等属性
✅ **战斗引擎类**: 完整的BattleEngine实现
✅ **伤害计算**: 包含元素克制、暴击、Buff系统
✅ **前端UI**: 动画、日志、交互
✅ **实现路线**: 分阶段的开发计划

**下一步**: 选择Phase 1开始实现，逐步构建完整的战斗系统！

---

**文档版本**: 1.0
**最后更新**: 2025-12-03
