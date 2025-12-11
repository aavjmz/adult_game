# PVE系统使用指南

## 📦 系统概述

PVE（Player vs Environment）系统是三国卡牌游戏的核心玩法，包含30个主线关卡、体力系统和完整的进度追踪。

## 🚀 快速开始

### 1. 数据库迁移

如果是首次部署或更新，需要运行数据库迁移：

```bash
python migrate_pve_system.py
```

这将：
- 为User表添加体力系统字段
- 创建stages表（关卡配置）
- 创建user_stage_progress表（用户进度）
- 创建battle_records表（战斗记录）

### 2. 初始化关卡数据

运行关卡初始化脚本创建30个主线关卡：

```bash
python init_stages.py
```

这将创建：
- 第1章：黄巾起义（1-10关）
- 第2章：董卓之乱（11-20关）
- 第3章：群雄割据（21-30关）

### 3. 验证系统

运行测试脚本验证所有功能：

```bash
python test_pve_system.py
```

## 📊 数据库结构

### User表扩展字段
```sql
stamina             INTEGER      -- 当前体力
max_stamina         INTEGER      -- 最大体力
stamina_updated_at  TIMESTAMP    -- 体力更新时间
main_stage_progress INTEGER      -- 主线进度
total_pve_battles   INTEGER      -- 总战斗次数
total_pve_wins      INTEGER      -- 总胜利次数
```

### Stage表（关卡配置）
```sql
id                  INTEGER PRIMARY KEY
stage_type          VARCHAR(20)  -- main/daily/special/boss
chapter             INTEGER      -- 章节号
stage_number        INTEGER      -- 关卡编号
name                VARCHAR(100) -- 关卡名称
description         TEXT         -- 关卡描述
difficulty          VARCHAR(20)  -- 难度
recommended_power   INTEGER      -- 推荐战力
stamina_cost        INTEGER      -- 体力消耗
enemy_config        TEXT         -- 敌人配置(JSON)
rewards             TEXT         -- 奖励(JSON)
drop_config         TEXT         -- 掉落配置(JSON)
first_clear_rewards TEXT         -- 首通奖励(JSON)
star_*_condition    VARCHAR(100) -- 星级条件
```

### UserStageProgress表（用户进度）
```sql
id                INTEGER PRIMARY KEY
user_id           INTEGER      -- 用户ID
stage_id          INTEGER      -- 关卡ID
is_cleared        BOOLEAN      -- 是否通关
stars             INTEGER      -- 获得星数
best_time         INTEGER      -- 最快时间
total_attempts    INTEGER      -- 总尝试次数
today_attempts    INTEGER      -- 今日尝试次数
```

### BattleRecord表（战斗记录）
```sql
id              INTEGER PRIMARY KEY
user_id         INTEGER      -- 用户ID
stage_id        INTEGER      -- 关卡ID
battle_type     VARCHAR(20)  -- pve/pvp
result          VARCHAR(10)  -- win/lose
stars           INTEGER      -- 获得星数
battle_duration INTEGER      -- 战斗时长
damage_dealt    INTEGER      -- 造成伤害
damage_taken    INTEGER      -- 承受伤害
battle_log      TEXT         -- 战斗日志(JSON)
rewards         TEXT         -- 奖励(JSON)
```

## 🎮 体力系统

### 基本机制
- 默认最大体力：120点
- 恢复速率：每6分钟恢复1点
- 关卡消耗：普通10点，Boss 15点

### 使用示例

```python
from app.utils.stamina import StaminaSystem
from app.models import User

# 获取体力信息
user = User.query.get(user_id)
stamina_info = StaminaSystem.get_stamina_info(user)
# 返回: {current, max, time_to_next_recovery, minutes_to_full}

# 消耗体力
success = StaminaSystem.consume_stamina(user, 10)

# 增加体力（药水）
added = StaminaSystem.add_stamina(user, 60)

# 检查是否有足够体力
can_afford = StaminaSystem.can_afford_stage(user, 10)
```

## 🗺️ 关卡系统

### 关卡类型
- **main** - 主线关卡（当前30个）
- **daily** - 每日副本（待实现）
- **special** - 专属副本（待实现）
- **boss** - 世界Boss（待实现）

### 难度等级
- **normal** - 普通（1-100关）
- **elite** - 精英（101-140关）
- **boss** - Boss战（141-150关）

### 星级评价
- ⭐ 1星：通关关卡
- ⭐⭐ 2星：无人阵亡
- ⭐⭐⭐ 3星：10回合内通关

### 查询关卡示例

```python
from app.models import Stage

# 获取所有主线关卡
main_stages = Stage.query.filter_by(stage_type='main').order_by(Stage.stage_number).all()

# 获取第1章关卡
chapter1_stages = Stage.query.filter_by(stage_type='main', chapter=1).all()

# 获取特定关卡
stage = Stage.query.filter_by(stage_type='main', stage_number=1).first()

# 解析JSON配置
import json
enemy_config = json.loads(stage.enemy_config)
rewards = json.loads(stage.rewards)
```

## 🎯 用户进度追踪

### 记录进度示例

```python
from app.models import UserStageProgress
from datetime import datetime

# 创建或更新进度
progress = UserStageProgress.query.filter_by(
    user_id=user.id,
    stage_id=stage.id
).first()

if not progress:
    progress = UserStageProgress(
        user_id=user.id,
        stage_id=stage.id
    )
    db.session.add(progress)

# 更新进度
progress.is_cleared = True
progress.stars = 3
progress.total_attempts += 1
progress.first_clear_at = datetime.utcnow()

db.session.commit()
```

## 🔧 故障排查

### 问题1: "no such column: users.stamina"

**原因**: 数据库未运行迁移脚本

**解决**:
```bash
python migrate_pve_system.py
```

### 问题2: 没有关卡数据

**原因**: 未初始化关卡

**解决**:
```bash
python init_stages.py
```

### 问题3: 验证系统是否正常

**解决**:
```bash
python test_pve_system.py
```

应该看到所有测试通过的输出。

## 📝 开发计划

### ✅ Week 1 已完成
- [x] 数据库模型设计
- [x] 体力系统实现
- [x] 前30个关卡初始化
- [x] 数据库迁移脚本
- [x] 测试脚本

### 🔄 Week 2 进行中
- [ ] PVE战斗流程
- [ ] 敌方AI系统
- [ ] 星级评价逻辑
- [ ] 掉落计算
- [ ] 扫荡系统

### 📅 Week 3-4 计划
- [ ] 每日副本系统
- [ ] 专属副本
- [ ] 世界Boss
- [ ] 前端界面

## 🔗 相关文件

- `app/models.py` - 数据库模型定义
- `app/utils/stamina.py` - 体力系统工具
- `migrate_pve_system.py` - 数据库迁移
- `init_stages.py` - 关卡初始化
- `test_pve_system.py` - 系统测试
- `PVE_SYSTEM_DESIGN.md` - 完整设计文档

## 💡 最佳实践

1. **部署前检查**: 运行 `test_pve_system.py` 确保系统正常
2. **备份数据库**: 迁移前备份 `instance/game.db`
3. **验证迁移**: 迁移后检查所有表和字段
4. **监控体力**: 定期检查体力恢复逻辑是否正常
5. **日志记录**: 记录所有战斗和掉落，便于平衡调整

## 📞 技术支持

遇到问题？检查：
1. 数据库是否有所有必需的表和字段
2. 关卡数据是否正确初始化
3. 体力系统时间计算是否准确
4. JSON配置格式是否正确

运行完整测试：
```bash
python test_pve_system.py
```
