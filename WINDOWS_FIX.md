# ⚠️ Windows环境PVE系统快速修复指南

## 问题说明

您遇到的错误：
```
sqlite3.OperationalError: no such column: users.stamina
```

**原因**：Windows环境的数据库还没有运行PVE系统迁移脚本。

## 🚀 快速解决方案

### 方案1: 运行迁移脚本（推荐）

在Windows命令行或PowerShell中执行：

```bash
# 1. 进入项目目录
cd F:\github\adult_game

# 2. 检查迁移状态
python migrate_pve_system.py check

# 3. 如果需要迁移，运行迁移脚本
python migrate_pve_system.py

# 4. 初始化关卡数据
python init_stages.py

# 5. 验证系统
python test_pve_system.py
```

### 方案2: 复制Linux数据库（临时方案）

如果迁移脚本有问题，可以直接复制已迁移的数据库：

1. 从Linux环境复制 `instance/game.db` 到Windows环境
2. 替换Windows环境的数据库文件
3. 重启Flask应用

## 📋 详细步骤

### Step 1: 检查迁移状态

```bash
python migrate_pve_system.py check
```

输出示例：
```
🔍 检查PVE系统迁移状态...

📊 User表字段检查:
  ❌ stamina (缺失)
  ❌ max_stamina (缺失)
  ❌ stamina_updated_at (缺失)
  ❌ main_stage_progress (缺失)
  ❌ total_pve_battles (缺失)
  ❌ total_pve_wins (缺失)

📊 PVE表检查:
  ❌ stages (缺失)
  ❌ user_stage_progress (缺失)
  ❌ battle_records (缺失)

⚠️  需要运行迁移脚本
```

### Step 2: 运行迁移

```bash
python migrate_pve_system.py
```

预期输出：
```
🔧 开始PVE系统数据库迁移...

📊 步骤1: 扩展User表...
  ➕ 添加字段: stamina
  ➕ 添加字段: max_stamina
  ➕ 添加字段: stamina_updated_at
  ➕ 添加字段: main_stage_progress
  ➕ 添加字段: total_pve_battles
  ➕ 添加字段: total_pve_wins
  🔄 设置stamina_updated_at默认值...
  ✅ User表更新完成

📊 步骤2: 创建PVE相关表...
  ➕ 创建 stages 表...
    ✓ stages表创建成功
  ➕ 创建 user_stage_progress 表...
    ✓ user_stage_progress表创建成功
  ➕ 创建 battle_records 表...
    ✓ battle_records表创建成功
  ✅ 所有PVE表检查完成

✅ PVE系统数据库迁移成功完成!
```

### Step 3: 初始化关卡

```bash
python init_stages.py
```

这将创建30个主线关卡。

### Step 4: 验证系统

```bash
python test_pve_system.py
```

如果看到所有测试通过，说明迁移成功：
```
✅ 所有测试通过！PVE系统运行正常！
```

### Step 5: 重启Flask应用

```bash
# 停止当前运行的Flask应用（Ctrl+C）
# 然后重新启动
python run.py
```

## 🐛 常见问题

### 问题1: "字段已存在"错误

**错误信息**：
```
sqlite3.OperationalError: duplicate column name: stamina
```

**解决**：字段已经添加过了，可以忽略。运行检查命令确认：
```bash
python migrate_pve_system.py check
```

### 问题2: 数据库文件被锁定

**错误信息**：
```
sqlite3.OperationalError: database is locked
```

**解决**：
1. 关闭所有Flask应用实例
2. 关闭所有数据库连接工具（DB Browser等）
3. 重新运行迁移脚本

### 问题3: 找不到数据库文件

**解决**：
确认数据库文件位置：
```python
python -c "from app import create_app; app = create_app(); print(app.config['SQLALCHEMY_DATABASE_URI'])"
```

### 问题4: Python路径问题

**错误信息**：
```
ModuleNotFoundError: No module named 'app'
```

**解决**：确保在项目根目录运行命令：
```bash
cd F:\github\adult_game
python migrate_pve_system.py
```

## 🔄 如果迁移失败

### 方案A: 重置数据库（开发环境）

```bash
# 备份当前数据库
copy instance\game.db instance\game.db.backup

# 删除数据库
del instance\game.db

# 重新创建数据库
python
>>> from app import create_app, db
>>> app = create_app()
>>> app.app_context().push()
>>> db.create_all()
>>> exit()

# 运行迁移
python migrate_pve_system.py

# 初始化关卡
python init_stages.py
```

### 方案B: 使用SQLite工具手动添加

使用DB Browser for SQLite等工具：

1. 打开 `instance/game.db`
2. 在User表添加字段：
   ```sql
   ALTER TABLE users ADD COLUMN stamina INTEGER DEFAULT 120;
   ALTER TABLE users ADD COLUMN max_stamina INTEGER DEFAULT 120;
   ALTER TABLE users ADD COLUMN stamina_updated_at TIMESTAMP;
   ALTER TABLE users ADD COLUMN main_stage_progress INTEGER DEFAULT 0;
   ALTER TABLE users ADD COLUMN total_pve_battles INTEGER DEFAULT 0;
   ALTER TABLE users ADD COLUMN total_pve_wins INTEGER DEFAULT 0;
   ```
3. 运行 `migrate_pve_system.py` 创建其他表

## 📞 验证清单

运行迁移后，确认以下项目：

- [ ] 运行 `python migrate_pve_system.py check` 显示全部✅
- [ ] 运行 `python test_pve_system.py` 全部通过
- [ ] Flask应用可以正常启动
- [ ] 登录功能正常工作
- [ ] 没有 "no such column" 错误

## 🎯 完成后

迁移完成后，您将获得：
- ✅ 完整的体力系统
- ✅ 30个三国主线关卡
- ✅ 用户进度追踪
- ✅ 战斗记录系统

## 📝 命令速查表

```bash
# 检查迁移状态
python migrate_pve_system.py check

# 执行迁移
python migrate_pve_system.py

# 初始化关卡
python init_stages.py

# 测试系统
python test_pve_system.py

# 启动应用
python run.py
```

## 💡 提示

1. **迁移前备份**: 复制 `instance/game.db` 到安全位置
2. **关闭应用**: 运行迁移前关闭Flask应用
3. **检查状态**: 迁移后运行check命令确认
4. **运行测试**: 使用test脚本验证所有功能

---

**需要帮助？**检查：
- 数据库文件路径是否正确
- Python环境是否激活
- 是否在项目根目录运行命令
- 数据库文件是否被其他程序锁定
