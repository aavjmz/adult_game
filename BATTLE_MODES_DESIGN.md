# 三国卡牌游戏 - 完整对战玩法设计方案 ⚔️

> 包含 PVE、PVP、多人对战的完整设计与技术实现方案

## 📚 目录

1. [PVE 玩法系统](#pve-玩法系统)
2. [PVP 玩法系统](#pvp-玩法系统)
3. [多人对战系统](#多人对战系统)
4. [技术实现方案](#技术实现方案)

---

## 🎯 PVE 玩法系统

### 1. 主线关卡系统 - 【逐鹿中原】

#### 关卡结构
```
第一章：黄巾起义（10关）
第二章：十八路诸侯（15关）
第三章：三国鼎立（20关）
第四章：赤壁之战（15关）
第五章：夷陵之战（15关）
...
共计：150+ 关卡
```

#### 关卡难度设计

| 章节 | 关卡数 | 敌方等级 | 推荐战力 | 奖励 |
|------|--------|----------|----------|------|
| 第1章 | 1-10 | Lv.1-10 | 500-1000 | N/R卡，少量金币 |
| 第2章 | 11-25 | Lv.11-25 | 1000-2000 | R/SR卡，抽卡券 |
| 第3章 | 26-45 | Lv.26-50 | 2000-4000 | SR/SSR卡，大量金币 |
| 第4章 | 46-60 | Lv.51-70 | 4000-6000 | SSR卡，高级材料 |
| 第5章 | 61-75 | Lv.71-90 | 6000-8000 | SSR/UR卡，稀有材料 |

#### 三星评价系统
```yaml
每个关卡可获得1-3颗星：

⭐ 1星条件: 胜利
⭐⭐ 2星条件: 3回合内胜利
⭐⭐⭐ 3星条件: 无人阵亡 + 3回合内胜利

三星奖励:
  - 首次三星: 抽卡券 x2
  - 累计星数奖励: 每10星获得一次抽卡券 x5
```

#### 扫荡系统
```python
# 扫荡条件
条件1: 关卡已通关且达到3星
条件2: 消耗体力（每次10点）

# 扫荡奖励
自动获得: 金币、经验、材料
不获得: 卡牌掉落（需要手动战斗）
```

---

### 2. 副本系统 - 【每日试炼】

#### 2.1 金币副本 - 【商贾之路】
```yaml
开放时间: 每天 12:00-14:00, 18:00-20:00
次数限制: 每天3次
难度分级:
  - 简单: Lv.20, 奖励 5000 金币
  - 普通: Lv.40, 奖励 15000 金币
  - 困难: Lv.60, 奖励 50000 金币
  - 地狱: Lv.80, 奖励 150000 金币
```

#### 2.2 经验副本 - 【演武场】
```yaml
开放时间: 每天 10:00-12:00, 20:00-22:00
次数限制: 每天3次
掉落物品: 经验药水
  - 小型经验药水: +1000 经验
  - 中型经验药水: +5000 经验
  - 大型经验药水: +20000 经验
```

#### 2.3 材料副本 - 【宝物阁】
```yaml
开放时间: 全天开放
次数限制: 每天5次
掉落物品:
  周一: 武将强化石（红色）
  周二: 谋士强化石（蓝色）
  周三: 弓将强化石（绿色）
  周四: 骑将强化石（紫色）
  周五: 步将强化石（黄色）
  周六/日: 全部材料随机掉落
```

#### 2.4 觉醒副本 - 【神兵天降】
```yaml
开放时间: 周末全天
次数限制: 无限制（消耗体力）
掉落物品:
  - 觉醒石（稀有）
  - 觉醒结晶（史诗）
  - 神器碎片（传说）

难度阶梯:
  Lv.1-5: N/R卡觉醒材料
  Lv.6-10: SR/SSR卡觉醒材料
  Lv.11+: UR卡觉醒材料
```

---

### 3. Boss 战系统 - 【英豪试炼】

#### 3.1 周常 Boss
```yaml
黄巾首领 - 张角:
  时间: 每周一
  难度: Lv.50
  机制: 召唤小怪，群体AOE
  奖励: SR卡包 x1, 金币 100000

董卓军团:
  时间: 每周三
  难度: Lv.70
  机制: 高防御，反击
  奖励: SSR卡包 x1, 觉醒石 x10

吕布无双:
  时间: 每周五
  难度: Lv.90
  机制: 超高攻击，狂暴
  奖励: SSR卡包 x2, 神器碎片 x5

诸葛亮八卦阵:
  时间: 每周日
  难度: Lv.100
  机制: 连续Debuff，智力碾压
  奖励: UR卡包 x1, 觉醒结晶 x20
```

#### 3.2 世界 Boss - 【群雄讨伐】
```yaml
机制:
  - 全服玩家共同挑战
  - Boss 生命值 1亿
  - 每位玩家每天可攻击3次
  - 根据伤害排名获得奖励

排名奖励:
  第1名: UR卡 x1, 抽卡券 x50
  第2-10名: SSR卡 x1, 抽卡券 x30
  第11-100名: SR卡 x1, 抽卡券 x10
  参与奖: R卡 x1, 抽卡券 x3

Boss 轮换:
  周1-3: 吕布（群势力）
  周4-5: 关羽（蜀势力）
  周6-7: 曹操（魏势力）
```

---

### 4. 爬塔系统 - 【虎牢关】

#### 塔层设计
```yaml
总层数: 100层
难度: 每层递增

特殊层奖励:
  第10层: 抽卡券 x5
  第20层: SR卡包 x1
  第30层: SSR卡包 x1
  第50层: UR卡包 x1（随机UR武将）
  第100层: 限定UR卡 - 吕布【方天画戟】特殊皮肤

机制:
  - 每天可挑战5次
  - 失败不消耗次数
  - 每月重置一次
  - 重置后可再次获得奖励
```

---

## ⚔️ PVP 玩法系统

### 1. 竞技场 - 【天下无双】

#### 1.1 基础规则
```yaml
匹配机制: 根据段位匹配 ±2 段位玩家
战斗方式: 异步对战（攻击对方防守队伍）
次数限制: 每天 10 次免费挑战
额外挑战: 消耗竞技券（1券 = 1次）

战斗规则:
  - 3v3 对战
  - 30回合限时
  - AI 自动战斗（基于玩家防守队伍策略）
```

#### 1.2 段位系统
```yaml
段位分级:
  青铜 I-V:   0-999 分
  白银 I-V:   1000-1999 分
  黄金 I-V:   2000-2999 分
  铂金 I-V:   3000-3999 分
  钻石 I-V:   4000-4999 分
  大师:       5000-5999 分
  宗师:       6000+ 分

升降级规则:
  - 胜利: +30 分
  - 失败: -15 分
  - 连胜加成: 连胜3场后，每场额外 +5 分

段位保护:
  - 白银及以下: 无保护
  - 黄金及以上: 掉到下一大段位时保护 3 场
```

#### 1.3 赛季奖励
```yaml
赛季周期: 每月一个赛季（每月1日重置）

赛季结算奖励:
  宗师段位:
    - UR卡包 x3
    - 抽卡券 x100
    - 专属称号【无双上将】

  大师段位:
    - SSR卡包 x5
    - 抽卡券 x50
    - 专属称号【百战不殆】

  钻石段位:
    - SSR卡包 x3
    - 抽卡券 x30

  铂金段位:
    - SR卡包 x5
    - 抽卡券 x20

  黄金及以下:
    - SR卡包 x2
    - 抽卡券 x10
```

---

### 2. 排位赛 - 【巅峰对决】

#### 2.1 赛制规则
```yaml
开放时间: 每天 19:00-22:00
参与条件: 等级 ≥30，战力 ≥5000

赛制:
  - BO3（三局两胜）
  - 实时对战（双方同时在线）
  - 禁用卡牌机制

流程:
  1. 匹配对手（段位相近）
  2. 禁卡阶段（各禁2张UR/SSR卡）
  3. 选卡阶段（3v3组队）
  4. 开始战斗
```

#### 2.2 积分与奖励
```yaml
积分规则:
  - 胜利: +50 积分
  - 失败: -20 积分
  - 连胜3场: 下一场 +80 积分
  - 本赛季最高积分记录

周奖励（每周日结算）:
  Top 1:    UR卡 x2, 限定称号【天下第一】
  Top 2-10: UR卡 x1, 抽卡券 x50
  Top 11-50: SSR卡 x3, 抽卡券 x30
  Top 51-100: SSR卡 x2, 抽卡券 x20
```

---

### 3. 实时对战 - 【华容道】

#### 3.1 快速匹配
```yaml
模式: 3v3 实时对战
匹配时间: 最长30秒
段位限制: 无

特色机制:
  - 随机地图效果（火攻地形、水域地形等）
  - 实时操作（选择攻击目标、释放技能）
  - 30秒回合限时

胜利奖励:
  - 竞技币 x10
  - 经验值 +500
  - 每日首胜: 抽卡券 x1
```

#### 3.2 好友对战
```yaml
玩法: 邀请好友 1v1 或 3v3 对战
限制: 无次数限制
奖励: 无奖励（纯娱乐）

自定义规则:
  - 可自定义回合数
  - 可禁用特定卡牌
  - 可调整地图效果
```

---

## 👥 多人对战系统

### 1. 公会系统 - 【结义堂】

#### 1.1 公会基础
```yaml
创建条件:
  - 等级 ≥20
  - 消耗 50000 金币

公会等级:
  Lv.1: 成员上限 20 人
  Lv.2: 成员上限 30 人
  Lv.3: 成员上限 40 人
  Lv.4: 成员上限 50 人
  Lv.5: 成员上限 70 人
  Lv.10: 成员上限 100 人

公会职位:
  - 会长（1人）: 所有权限
  - 副会长（2人）: 审批、踢人、编辑公告
  - 精英（5人）: 审批新人
  - 成员（其他）: 基础权限
```

#### 1.2 公会副本 - 【共讨逆贼】
```yaml
开放时间: 每周三、六、日 20:00-21:00
参与条件: 公会成员均可参与

副本机制:
  - 共同挑战超级Boss
  - Boss总血量: 5000万
  - 每人每天3次挑战机会
  - 根据个人伤害和公会总伤害发放奖励

Boss难度:
  初级: 推荐战力 3000
  中级: 推荐战力 5000
  高级: 推荐战力 8000
  史诗: 推荐战力 12000

公会排名奖励（前10公会）:
  第1名: 全员 UR卡包 x1, 抽卡券 x30
  第2-3名: 全员 SSR卡包 x2, 抽卡券 x20
  第4-10名: 全员 SSR卡包 x1, 抽卡券 x10
```

---

### 2. 公会战 - 【攻城略地】

#### 2.1 赛制规则
```yaml
开放时间: 每月第2、4周周末
参与条件: 公会等级 ≥3

赛制:
  - 公会 vs 公会
  - 每个公会派出 15 名精英成员
  - BO5（五局三胜）制

匹配规则:
  - 根据公会战力匹配
  - 同等级公会优先匹配
  - 跨服匹配
```

#### 2.2 战斗机制
```yaml
阵地战:
  - 每个公会有3个阵地（前锋、中军、后卫）
  - 每个阵地5人防守
  - 攻击方选择攻击哪个阵地
  - 攻破所有阵地即获胜

攻防切换:
  - 第1局: A公会攻，B公会守
  - 第2局: B公会攻，A公会守
  - 如此循环

特殊机制:
  - 阵亡武将本轮不可再上场
  - 守方有城墙加成（全属性 +10%）
  - 攻方有攻城器械（破防 +15%）
```

#### 2.3 公会战奖励
```yaml
胜利公会（全员）:
  - 公会币 x1000
  - SSR卡包 x2
  - 抽卡券 x20
  - 公会荣誉 +500

失败公会（全员）:
  - 公会币 x500
  - SR卡包 x2
  - 抽卡券 x10
  - 公会荣誉 +200

MVP奖励（伤害最高者）:
  - 额外 UR卡包 x1
  - 专属称号【攻城先锋】
```

---

### 3. 跨服联赛 - 【逐鹿天下】

#### 3.1 赛制
```yaml
举办周期: 每3个月一次
参与条件:
  - 赛季排名前100的玩家
  - 或公会战积分前50的公会成员

赛制:
  小组赛: 16组，每组6人，单循环
  淘汰赛: 前2名晋级，32进16
  决赛: 决出冠亚季军

奖励:
  冠军:
    - 限定UR卡【天命之子 - 刘备】
    - 抽卡券 x500
    - 专属称号【天下霸主】
    - 服务器公告

  亚军:
    - UR卡包 x5
    - 抽卡券 x300
    - 专属称号【争霸天下】

  季军:
    - UR卡包 x3
    - 抽卡券 x200
    - 专属称号【三国名将】
```

---

### 4. 联盟战 - 【三国鼎立】

#### 4.1 联盟系统
```yaml
势力选择:
  - 魏阵营
  - 蜀阵营
  - 吴阵营
  - 群雄阵营

玩家归属:
  - 根据持有武将最多的势力自动归属
  - 或手动选择（每月可更换1次）
```

#### 4.2 联盟战机制
```yaml
开放时间: 每月最后一周周末
赛制: 4个阵营混战

战场:
  - 虚拟大地图（洛阳、长安、成都、建业等15个城池）
  - 每个城池有防守方和攻击方
  - 占领城池获得积分

积分规则:
  - 占领城池: +1000 分
  - 击败敌方: +10 分
  - 守城成功: +500 分

联盟奖励（按总积分排名）:
  第1名阵营（全员）:
    - UR卡包 x2
    - 抽卡券 x50
    - 专属称号【霸业之主】
    - 势力专属皮肤

  第2名阵营（全员）:
    - SSR卡包 x3
    - 抽卡券 x30

  第3-4名阵营（全员）:
    - SSR卡包 x1
    - 抽卡券 x10
```

---

## 🛠️ 技术实现方案

### 1. 数据库设计

#### 1.1 PVE 关卡表
```sql
CREATE TABLE stages (
    id INTEGER PRIMARY KEY,
    chapter INTEGER,              -- 章节
    stage_number INTEGER,         -- 关卡号
    name VARCHAR(100),            -- 关卡名称
    enemy_formation JSON,         -- 敌方阵容（卡牌ID数组）
    enemy_level INTEGER,          -- 敌方等级
    recommended_power INTEGER,    -- 推荐战力
    rewards JSON,                 -- 奖励配置
    star_conditions JSON,         -- 三星条件
    unlock_condition VARCHAR(50), -- 解锁条件（上一关卡ID）
    created_at DATETIME
);

CREATE TABLE user_stage_progress (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    stage_id INTEGER,
    stars INTEGER,                -- 获得星数（0-3）
    best_turns INTEGER,           -- 最佳回合数
    completed_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (stage_id) REFERENCES stages(id)
);
```

#### 1.2 PVP 竞技场表
```sql
CREATE TABLE arena_rankings (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    rank INTEGER,                 -- 排名
    rating INTEGER,               -- 积分
    tier VARCHAR(20),             -- 段位
    defense_formation JSON,       -- 防守阵容
    win_count INTEGER DEFAULT 0,
    lose_count INTEGER DEFAULT 0,
    season_id INTEGER,            -- 赛季ID
    updated_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE arena_battles (
    id INTEGER PRIMARY KEY,
    attacker_id INTEGER,
    defender_id INTEGER,
    winner_id INTEGER,
    battle_log JSON,              -- 战斗日志
    rating_change INTEGER,        -- 积分变化
    created_at DATETIME,
    FOREIGN KEY (attacker_id) REFERENCES users(id),
    FOREIGN KEY (defender_id) REFERENCES users(id)
);
```

#### 1.3 公会表
```sql
CREATE TABLE guilds (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    level INTEGER DEFAULT 1,
    exp INTEGER DEFAULT 0,
    leader_id INTEGER,
    member_count INTEGER DEFAULT 1,
    max_members INTEGER DEFAULT 20,
    announcement TEXT,
    created_at DATETIME,
    FOREIGN KEY (leader_id) REFERENCES users(id)
);

CREATE TABLE guild_members (
    id INTEGER PRIMARY KEY,
    guild_id INTEGER,
    user_id INTEGER,
    role VARCHAR(20),             -- leader/vice_leader/elite/member
    contribution INTEGER DEFAULT 0,
    joined_at DATETIME,
    FOREIGN KEY (guild_id) REFERENCES guilds(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE guild_battles (
    id INTEGER PRIMARY KEY,
    guild1_id INTEGER,
    guild2_id INTEGER,
    winner_guild_id INTEGER,
    battle_log JSON,
    season_id INTEGER,
    created_at DATETIME,
    FOREIGN KEY (guild1_id) REFERENCES guilds(id),
    FOREIGN KEY (guild2_id) REFERENCES guilds(id)
);
```

---

### 2. API 路由设计

#### 2.1 PVE 路由
```python
# app/routes/pve.py

@bp.route('/stages', methods=['GET'])
@login_required
def get_stages():
    """获取关卡列表"""
    pass

@bp.route('/stages/<int:stage_id>/battle', methods=['POST'])
@login_required
def start_stage_battle(stage_id):
    """开始关卡战斗"""
    pass

@bp.route('/stages/<int:stage_id>/sweep', methods=['POST'])
@login_required
def sweep_stage(stage_id):
    """扫荡关卡（需三星）"""
    pass

@bp.route('/daily-dungeons', methods=['GET'])
@login_required
def get_daily_dungeons():
    """获取每日副本列表"""
    pass

@bp.route('/boss/challenge', methods=['POST'])
@login_required
def challenge_boss():
    """挑战Boss"""
    pass
```

#### 2.2 PVP 路由
```python
# app/routes/pvp.py

@bp.route('/arena/rank', methods=['GET'])
@login_required
def get_arena_rank():
    """获取竞技场排名"""
    pass

@bp.route('/arena/opponents', methods=['GET'])
@login_required
def get_opponents():
    """获取可挑战对手列表"""
    pass

@bp.route('/arena/battle', methods=['POST'])
@login_required
def arena_battle():
    """竞技场战斗"""
    data = request.json
    defender_id = data.get('defender_id')

    # 获取双方防守阵容
    # 执行AI自动战斗
    # 更新积分和排名
    # 返回战斗结果
    pass

@bp.route('/arena/defense', methods=['POST'])
@login_required
def set_defense_formation():
    """设置防守阵容"""
    pass

@bp.route('/ranked/match', methods=['POST'])
@login_required
def ranked_match():
    """排位赛匹配"""
    pass
```

#### 2.3 公会路由
```python
# app/routes/guild.py

@bp.route('/guilds', methods=['GET'])
def get_guilds():
    """获取公会列表"""
    pass

@bp.route('/guilds/create', methods=['POST'])
@login_required
def create_guild():
    """创建公会"""
    pass

@bp.route('/guilds/<int:guild_id>/join', methods=['POST'])
@login_required
def join_guild(guild_id):
    """申请加入公会"""
    pass

@bp.route('/guilds/my', methods=['GET'])
@login_required
def get_my_guild():
    """获取我的公会信息"""
    pass

@bp.route('/guilds/raid', methods=['POST'])
@login_required
def guild_raid():
    """公会副本战斗"""
    pass

@bp.route('/guilds/war', methods=['POST'])
@login_required
def guild_war():
    """公会战"""
    pass
```

---

### 3. AI 战斗逻辑

#### 3.1 防守AI（竞技场）
```python
class DefenseAI:
    """防守AI - 用于竞技场异步对战"""

    def __init__(self, defense_cards):
        self.cards = defense_cards
        self.strategy = self._analyze_team()

    def _analyze_team(self):
        """分析队伍构成，确定策略"""
        # 计算队伍属性
        avg_hp = sum(c['hp'] for c in self.cards) / len(self.cards)
        avg_attack = sum(c['attack'] for c in self.cards) / len(self.cards)

        # 根据属性确定策略
        if avg_attack > 200:
            return 'aggressive'  # 进攻策略
        elif avg_hp > 2000:
            return 'defensive'   # 防守策略
        else:
            return 'balanced'    # 平衡策略

    def choose_action(self, card, enemies):
        """选择行动"""
        if self.strategy == 'aggressive':
            # 优先攻击血量最少的敌人
            target = min(enemies, key=lambda e: e['current_hp'])
        elif self.strategy == 'defensive':
            # 优先攻击攻击力最高的敌人
            target = max(enemies, key=lambda e: e['attack'])
        else:
            # 随机选择目标
            target = random.choice(enemies)

        # 决定是否使用技能
        if card['skill_current_cd'] == 0:
            return {'action': 'skill', 'target': target}
        else:
            return {'action': 'attack', 'target': target}
```

#### 3.2 Boss AI
```python
class BossAI:
    """Boss AI - 特殊机制"""

    def __init__(self, boss_card, phase=1):
        self.boss = boss_card
        self.phase = phase
        self.rage = 0  # 狂暴值

    def on_phase_change(self):
        """阶段转换（血量阈值触发）"""
        hp_percent = self.boss['current_hp'] / self.boss['max_hp']

        if hp_percent < 0.3 and self.phase == 1:
            self.phase = 2
            # 进入狂暴阶段
            self.boss['attack'] *= 1.5
            self.boss['speed'] += 20
            return "Boss进入狂暴状态！攻击力和速度大幅提升！"

    def special_skill(self, enemies):
        """特殊技能"""
        if self.phase == 2:
            # 狂暴阶段使用AOE技能
            return {
                'type': 'aoe',
                'targets': enemies,
                'damage_multiplier': 3.0,
                'effect': 'stun'  # 附加眩晕
            }
```

---

### 4. 匹配系统

#### 4.1 竞技场匹配
```python
class ArenaMatchmaker:
    """竞技场匹配系统"""

    @staticmethod
    def find_opponents(user_rank, count=5):
        """查找可挑战对手"""
        # 查找排名在自己前后的玩家
        min_rank = max(1, user_rank - 20)
        max_rank = user_rank + 10

        opponents = ArenaRanking.query.filter(
            ArenaRanking.rank.between(min_rank, max_rank)
        ).order_by(func.random()).limit(count).all()

        return opponents
```

#### 4.2 排位赛实时匹配
```python
class RankedMatchmaker:
    """排位赛实时匹配"""

    waiting_players = {}  # {user_id: {rating: int, wait_time: int}}

    @classmethod
    def join_queue(cls, user_id, rating):
        """加入匹配队列"""
        cls.waiting_players[user_id] = {
            'rating': rating,
            'wait_time': 0
        }

        # 尝试匹配
        match = cls._try_match(user_id)
        return match

    @classmethod
    def _try_match(cls, user_id):
        """尝试匹配对手"""
        user_data = cls.waiting_players[user_id]
        user_rating = user_data['rating']
        wait_time = user_data['wait_time']

        # 等待时间越长，匹配范围越大
        rating_range = 100 + (wait_time * 10)

        # 查找匹配对手
        for opponent_id, opponent_data in cls.waiting_players.items():
            if opponent_id == user_id:
                continue

            rating_diff = abs(user_rating - opponent_data['rating'])
            if rating_diff <= rating_range:
                # 匹配成功
                cls.waiting_players.pop(user_id)
                cls.waiting_players.pop(opponent_id)
                return {
                    'player1_id': user_id,
                    'player2_id': opponent_id
                }

        # 未找到对手，增加等待时间
        user_data['wait_time'] += 1
        return None
```

---

### 5. 奖励发放系统

```python
class RewardSystem:
    """奖励系统"""

    @staticmethod
    def grant_stage_rewards(user_id, stage_id, stars):
        """发放关卡奖励"""
        stage = Stage.query.get(stage_id)
        rewards = stage.get_rewards_by_stars(stars)

        user = User.query.get(user_id)

        # 发放金币
        if 'coins' in rewards:
            user.coins += rewards['coins']

        # 发放抽卡券
        if 'tickets' in rewards:
            user.tickets += rewards['tickets']

        # 发放卡牌
        if 'cards' in rewards:
            for card_id in rewards['cards']:
                user_card = UserCard(
                    user_id=user_id,
                    card_id=card_id
                )
                db.session.add(user_card)

        db.session.commit()
        return rewards

    @staticmethod
    def grant_arena_rewards(user_id, rank, tier):
        """发放竞技场赛季奖励"""
        rewards = {
            'master': {'ur_packs': 3, 'tickets': 100},
            'diamond': {'ssr_packs': 5, 'tickets': 50},
            'platinum': {'ssr_packs': 3, 'tickets': 30},
            # ...
        }

        tier_rewards = rewards.get(tier, {})
        # 发放奖励...
```

---

## 📊 数据分析与平衡

### 玩家留存指标
```yaml
PVE系统:
  - 日活跃: 完成至少1个每日副本
  - 周活跃: 挑战Boss战
  - 月活跃: 爬塔进度 > 50层

PVP系统:
  - 日活跃: 竞技场挑战 ≥ 5次
  - 周活跃: 参与排位赛
  - 月活跃: 赛季排名进入前1000

公会系统:
  - 公会活跃度: 成员参与公会副本比例
  - 公会战参与率
```

### 难度曲线
```yaml
关卡推荐战力:
  第1-10关:  500-1000   (新手引导)
  第11-25关: 1000-2000  (成长期)
  第26-50关: 2000-5000  (中期)
  第51-75关: 5000-8000  (后期)
  第76+关:   8000+      (终极挑战)

经验曲线:
  Lv.1-20: 快速升级
  Lv.21-40: 正常升级
  Lv.41-60: 较慢升级
  Lv.61+: 缓慢升级
```

---

## 🎯 实施优先级

### Phase 1: 基础 PVE（2-3周）
- ✅ 主线关卡系统（30关）
- ✅ 每日副本（金币、经验）
- ✅ 扫荡功能

### Phase 2: 竞技场 PVP（1-2周）
- ✅ 竞技场匹配系统
- ✅ 段位系统
- ✅ 防守阵容设置

### Phase 3: 公会系统（2-3周）
- ✅ 公会创建/加入
- ✅ 公会副本
- ✅ 公会聊天

### Phase 4: 高级玩法（3-4周）
- ✅ 爬塔系统
- ✅ 世界Boss
- ✅ 排位赛
- ✅ 公会战

### Phase 5: 跨服玩法（4-6周）
- ✅ 跨服联赛
- ✅ 联盟战

---

## 💡 总结

本设计方案提供了：

✅ **完整的 PVE 体验** - 主线、副本、Boss、爬塔
✅ **丰富的 PVP 玩法** - 竞技场、排位赛、实时对战
✅ **深度的社交系统** - 公会、公会战、联盟战
✅ **可扩展的技术架构** - 数据库设计、API设计、AI系统
✅ **平衡的游戏经济** - 奖励体系、难度曲线

**预计开发时间**: 12-18周（3-4.5个月）
**推荐团队配置**: 2后端 + 1前端 + 1策划 + 1美术

---

是否需要我开始实现某个具体模块的代码？🚀
