# 三国卡牌游戏 - 快速部署指南 🎴

## ⚠️ 重要：首次运行必须执行数据库迁移！

如果您看到类似以下错误：
```
OperationalError: no such column: cards.skill_cooldown
```

这说明您的数据库需要更新。请按照下面的步骤操作。

---

## 🚀 快速开始（新用户/重新部署）

### 步骤 1: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 2: 运行数据库迁移（必须！）

```bash
python migrate_complete.py
```

这个脚本会：
- ✅ 自动备份现有数据库
- ✅ 添加所有缺失的字段
- ✅ 更新14张卡牌为三国武将
- ✅ 验证数据库结构

**输出示例：**
```
============================================================
🔧 完整数据库迁移脚本
============================================================
✅ 已备份数据库到: game.db.backup_1764833198

检查并添加缺失的字段...
  ✅ 添加字段: skill_cooldown (INTEGER)
  ✅ 添加字段: skill_target (TEXT)
  ...

✅ 已更新 14 张卡牌为三国武将
✅ 完整迁移完成！
```

### 步骤 3: 启动游戏

```bash
python run.py
```

然后访问：http://localhost:5000

---

## 📊 数据库结构

迁移后，Card表将包含 **23个字段**：

### 基础属性
- id, name, rarity, attack, defense, hp

### 视觉效果
- is_golden, image_url, description

### 主动技能
- skill_name, skill_description, skill_damage_multiplier
- **skill_cooldown** (技能冷却回合数)
- **skill_target** (技能目标类型: single/all)

### 被动技能 ⭐ 新增
- **passive_skill_name** (被动技能名称)
- **passive_skill_description** (被动技能描述)

### 战斗增强属性 ⭐ Phase 1
- **speed** (速度值，决定行动顺序)
- **critical** (暴击率 %)
- **critical_dmg** (暴击伤害倍率 %)
- **element** (五行属性: 金/木/水/火/土)
- **job_class** (职业: 武将/谋士/弓将/骑将/步将)

### 三国主题 ⭐ 新增
- **faction** (势力: 魏/蜀/吴/群)

### 时间戳
- created_at

---

## 🎮 三国武将一览

### UR卡 (2张)
- 🌟 **诸葛亮** (蜀-水-谋士) - 卧龙
- 🌟 **曹操** (魏-土-武将) - 治世能臣乱世奸雄

### SSR卡 (3张)
- ⭐ **关羽** (蜀-金-武将) - 武圣
- ⭐ **吕布** (群-金-武将) - 人中吕布马中赤兔
- ⭐ **司马懿** (魏-水-谋士) - 鹰视狼顾

### SR卡 (3张)
- **赵云** (蜀-火-武将) - 常胜将军
- **周瑜** (吴-水-谋士) - 江东都督
- **夏侯惇** (魏-火-武将) - 独眼之怒

### R卡 (3张)
- **黄忠** (蜀-金-弓将) - 老当益壮
- **陆逊** (吴-火-谋士) - 火攻
- **甘宁** (吴-火-武将) - 江东锦帆贼

### N卡 (3张)
- **魏延** (蜀-火-武将) - 骁勇
- **黄月英** (蜀-木-谋士) - 才女
- **张郃** (魏-金-骑将) - 奇袭

---

## ⚔️ 游戏系统

### 五行克制系统
```
金 → 木 → 土 → 水 → 火 → 金
```
- 克制时：伤害 +30%
- 被克制：伤害 -20%

### 四大势力
- **魏** (4张) - 速度+10%
- **蜀** (6张) - 生命+15%
- **吴** (3张) - 防御+10%
- **群** (1张) - 攻击+12%

### 战斗系统
- 速度决定行动顺序
- 暴击系统（可配置暴击率和伤害）
- 技能冷却系统
- 五行克制加成

---

## 🔄 已有数据库升级

如果您之前已经有游戏数据：

1. **备份会自动创建** - 迁移脚本会自动备份为 `game.db.backup_时间戳`
2. **运行迁移** - `python migrate_complete.py`
3. **保留用户数据** - 用户账号、抽卡记录、拥有的卡牌都会保留
4. **卡牌更新** - 所有14张卡牌会更新为三国武将

---

## 🐛 常见问题

### Q: 运行游戏时提示 "no such column" 错误
**A:** 您需要先运行 `python migrate_complete.py` 进行数据库迁移。

### Q: 迁移后可以回退吗？
**A:** 可以！迁移脚本会自动备份数据库。如需回退：
```bash
cp game.db.backup_1764833198 game.db
```

### Q: 我可以重复运行迁移脚本吗？
**A:** 可以！脚本具有幂等性，会自动检查字段是否存在，不会重复添加。

### Q: 数据库在哪里？
**A:**
- 开发环境: `game.db` (项目根目录)
- 生产环境: 可配置为 PostgreSQL

### Q: 如何查看我的数据库有哪些字段？
**A:** 运行迁移脚本会自动显示所有字段，或者：
```bash
python -c "import sqlite3; conn = sqlite3.connect('game.db'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(cards)'); print([col[1] for col in cursor.fetchall()])"
```

---

## 📝 开发说明

### 代码结构
```
adult_game/
├── app/
│   ├── __init__.py          # 应用工厂
│   ├── models.py            # 数据库模型（Card, User, Battle等）
│   ├── battle_engine.py     # 战斗引擎（五行克制、暴击等）
│   └── routes/              # 路由蓝图
│       ├── auth.py          # 认证
│       ├── cards.py         # 卡牌展示
│       ├── gacha.py         # 抽卡系统
│       ├── battle.py        # 基础战斗
│       └── battle_v2.py     # 增强战斗
├── migrate_complete.py      # 完整迁移脚本 ⭐
├── migrate_three_kingdoms.py # 三国主题迁移
├── config.py                # 配置文件
├── run.py                   # 启动入口
└── game.db                  # SQLite数据库

```

### 添加新武将

1. 编辑 `migrate_complete.py` 中的 `three_kingdoms_cards` 列表
2. 运行迁移脚本更新数据库
3. 新武将会自动加入卡池

---

## 🎯 项目进度

- ✅ 用户系统 (100%)
- ✅ 抽卡系统 (100%)
- ✅ PWA支持 (100%)
- ✅ 卡牌系统 (70%) - 基础+三国主题
- ⏳ 战斗系统 (50%) - 核心完成，羁绊待实现
- ⏳ 成长系统 (0%) - 待开发
- ⏳ 副本系统 (0%) - 待开发

**整体完成度: 55%**

---

## 📚 相关文档

- `THREE_KINGDOMS_THEME.md` - 完整三国主题设计文档（30,000+字）
- `GAME_DESIGN.md` - 原始游戏设计文档
- `PROJECT_STATUS.md` - 项目状态和待办事项
- `PWA_GUIDE.md` - PWA安装指南

---

## 🎉 开始游戏！

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 数据库迁移（必须！）
python migrate_complete.py

# 3. 启动游戏
python run.py

# 4. 访问游戏
# http://localhost:5000
```

祝您在三国世界中征战愉快！🎴⚔️
