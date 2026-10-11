# 脚本说明

仓库根目录的 Python 脚本按用途分类说明。本文说明每个脚本做什么、什么时候跑、能不能重复跑。

服务器上统一在容器内执行（数据库在挂载卷 `/app/data/game.db`）：

```bash
docker-compose exec game python <脚本名>.py
```

**改动正式数据前先备份：**

```bash
docker-compose exec game cp /app/data/game.db /app/data/game.db.bak
```

---

## 一、常见场景速查

| 场景 | 要做的事 |
|---|---|
| 新服务器首次部署 | `docker-compose up -d --build`，然后跑 `init_enemy_cards.py`、`init_equipment_data.py`（见第二节） |
| 已有服务器更新代码 | `git pull && docker-compose up -d --build`；如果这次改了关卡、敌军或装备数据，再跑对应的 `init_*` 脚本 |
| 调关卡数值、掉落 | 改 `app/stage_data.py` → 部署 → `init_stages.py` |
| 调敌军数值、加新敌军 | 改 `app/enemy_cards.py` → 部署 → `init_enemy_cards.py` |
| 调装备属性、加新装备 | 改 `init_equipment_data.py` → 部署 → 重跑它 |
| 调市集价格、限购 | 改 `app/shop_data.py` → 部署即可，不用跑脚本 |
| 给测试账号发材料 | `grant_materials.py <用户名> [--dup <武将名> <张数>]` |

---

## 二、启动时自动完成的事（不用手动跑）

`create_app()`（`app/__init__.py`）每次启动都会执行以下几步，而且都可以安全地重复执行：

| 步骤 | 内容 |
|---|---|
| `db.create_all()` | 建出所有缺少的表，包括新加的 `shop_purchases`。已有表不会被修改 |
| `migrate_card_enemy_flag()` | 给 `cards` 表补 `is_enemy` 列，并把已入库的敌军卡标出来、移出卡池 |
| `init_cards()` | 卡牌表为空时，种入 14 张玩家武将 |
| `migrate_cards_to_three_kingdoms()` | 检测到旧版卡名时，改成三国武将（一次性迁移） |
| `init_stages()` | 关卡表为空时，按 `app/stage_data.py` 建出 30 关。已有关卡不动 |

`entrypoint.sh`（Docker 启动脚本）：库文件不存在时先跑一次 `migrate_complete.py`，然后启动 gunicorn。

**新服务器仍需手动跑的两个脚本：**

- `init_enemy_cards.py`：不跑的话，关卡里没有敌人，出征会提示「此关敌军尚未配置」。
- `init_equipment_data.py`：不跑的话，没有装备模板，合成装备的列表是空的。

---

## 三、数据同步脚本（改数据 → 重跑即生效）

三个脚本的规则一致：

- 以数据文件为准，按名字或编号逐条比对。
- 新增的新建；已有的只改有变化的字段，并打印改了哪些字段。
- 只新增和修改，不删除：从数据里删掉的条目，库里保留不动。
- 可以重复执行；没有改动时输出「无变化」。

| 脚本 | 数据在哪 | 匹配方式 | 说明 |
|---|---|---|---|
| `init_stages.py` | `app/stage_data.py` | 按关卡编号 | 原地更新，关卡 id 不变，玩家通关记录和星级保留。经验丹、星石掉落按章节写在同一文件的 `MATERIAL_DROPS` 里 |
| `init_enemy_cards.py` | `app/enemy_cards.py` | 按卡名 | 新卡带 `is_enemy=True`，不进卡池。与玩家武将同名的 7 位（张辽、吕布、关羽、赵云、孙策、周瑜、貂蝉）跳过，关卡直接用玩家卡 |
| `init_equipment_data.py` | 脚本自身 | 按套装名、装备名 | 4 套套装、27 个装备模板（普通 / 稀有 / 史诗 / 传说 / 神话）。玩家已有的装备会立即按新数值生效 |

注意事项：

- **改名等于新增。** 改名后旧名字那条仍留在库里，已有的数据仍关联旧条目。
- **套装名不要改。** 装备是按套装名关联套装的。
- **新敌军不要和玩家武将重名**，否则会被当成玩家卡跳过。确实要让玩家武将兼任敌将的，把名字加进 `app/enemy_cards.py` 的 `SHARED_WITH_PLAYERS`。
- 字段级的比对逻辑在 `app/utils/seed_sync.py`，敌军和装备脚本共用。

---


## 四、测试账号发材料

| 脚本 | 用途 | 用法 | 可重复 |
|---|---|---|---|
| `grant_materials.py` | 给指定账号发一套养成材料，测试用：银两 1000 万、各档经验丹、星石、觉醒石、突破石、技能书、强化石、保护符、各品级碎片，另有四个部位各一件装备 | `python grant_materials.py aavjmz [--dup 关羽 5]`。`--dup` 额外发同名武将卡，觉醒需 1 张、突破需 3 张 | 是，每次叠加 |

---

## 五、数据库迁移（`migrate_*`）

项目没有用 Alembic。**新建的数据库不需要任何迁移**：`db.create_all()` 会按当前模型建出带全部字段的表。下面两个脚本只用于在对应功能上线之前就已经存在的旧库，给已有的表补字段。

| 脚本 | 补什么 | 说明 |
|---|---|---|
| `migrate_complete.py` | `cards` 表的三国主题字段（属性、五行、势力、职业等），并种卡牌 | `entrypoint.sh` 在新库上会自动跑一次，旧库可以手动跑。读写 `data/game.db` |
| `migrate_pve_system.py` | 用户体力、PVE 统计字段，关卡与进度表 | 加参数 `check` 只检查状态；加参数 `rollback` 为回滚，会交互询问确认 |

以后给**已有的表**加字段，不要再写独立的迁移脚本：在 `create_app()` 里加一段「检查列是否存在 → 不存在就 ALTER」的逻辑（参考 `app/__init__.py` 的 `migrate_card_enemy_flag()`）。这样部署时重启即可生效，也能安全地重复执行。

---

## 六、测试脚本

测试都是独立脚本，没有接 pytest，直接 `python test_xxx.py` 运行。

需要测试账号的测试，会在开头调用 `test_fixtures.py` 的 `ensure_test_user()`：账号不存在就创建，并发卡牌和一套材料。所以**空库也能直接跑**，不用事先准备数据。`test_fixtures.py` 本身不是测试。

| 脚本 | 覆盖内容 | 数据库 |
|---|---|---|
| `test_api_client_growth.py` | `/api/v1` 成长、装备、碎片合成接口 | ✅ 临时库 |
| `test_api_client_shop.py` | `/api/v1` 市集：购买、限购、隔天重置 | ✅ 临时库 |
| `test_battle_skills.py` | 技能解析与等级换算、出手顺序与冷却、附加效果、自动 / 手动战斗与转托管 | ✅ 临时库 |
| `test_battle_stats.py` | 出战属性：星级、觉醒、突破、装备、强化逐项生效，战斗单位与接口一致 | ✅ 临时库 |
| `test_api_client_formation.py` | `/api/v1` 编伍：阵容读写、归属与重复校验、失效卡剔除、出征默认用服务端阵容 | ✅ 临时库 |
| `test_api_client.py` | `/api/v1` 注册 → 登录 → 抽卡 → 收藏 → 登出 | ⚠️ 当前库，会注册随机账号 |
| `test_pve_system.py` | PVE 表结构、关卡、战斗流程 | ⚠️ 当前库，会建测试用户 |
| `test_equipment_system.py` | 装备强化、套装、属性计算；空库时会自动补装备模板 | ⚠️ 当前库，测试账号 `testuser`，结束时交互询问是否清理 |
| `test_growth_system.py` | 升级、升星、技能、觉醒、突破公式 | ⚠️ 当前库，空库时建 `testuser` |
| `test_battle_system.py` | PVE 战斗引擎 | ⚠️ 当前库，测试账号 `test_pve_user` |
| `test_battle_v2.py` / `test_three_kingdoms_battle.py` | 战斗 v2、五行克制计算 | ⚠️ 当前库 |

本地想让标「当前库」的测试也不碰开发库，可以临时指定库路径：

```bash
DB_PATH=/tmp/test.db python test_growth_system.py
```

---

## 七、其他

| 文件 | 用途 |
|---|---|
| `run.py` | 本地启动开发服务器（默认端口 8080） |
| `entrypoint.sh` | Docker 启动：新库先跑 `migrate_complete.py`，再启动 gunicorn（默认 1 个 worker、8 个线程） |
| `config.py` | 游戏配置：稀有度概率、抽卡价格、初始资源等 |
| `generate_icons.py` | 生成 PWA 各尺寸图标，需要 Pillow |

---

## 八、已删除的脚本

下面这些脚本已经删除，需要时可以从 git 历史里找回（删除前的最后一个版本是提交 `307e415`）。

| 脚本 | 删除原因 / 替代方式 |
|---|---|
| `fix_stage_enemy_config.py` | 战斗引擎已直接按卡名查找敌军；而且重跑 `init_stages.py` 会把它的修改改回去 |
| `migrate_three_kingdoms.py`、`migrate_battle_v2.py` | 补的字段已被 `migrate_complete.py` 覆盖；脚本里写死了旧路径 `game.db`，在当前目录找不到库时还会新建一个空库 |
| `migrate_growth_system.py`、`migrate_equipment_system.py` | 只用于成长、装备上线前的旧库；同样写死旧路径 |
| `migrate_api_token.py` | `api_tokens` 表由 `db.create_all()` 自动建。它附带的「批量清理过期令牌」没有保留：过期令牌目前只在被使用时删除 |
| `migrate_pve_system_v2.py` | 已改名为 `migrate_pve_system.py`，旧的 v1 删除 |
| `test_battle_debug.py` | 早期调试用的打印脚本，已被 `test_battle_v2.py` 覆盖 |
| `recycle_enemy_cards.py`、`convert_universal_fragments.py` | 一次性数据修复（回收敌军卡、通用碎片 1:1 换普通碎片），已完成 |
| `init_database.py`、`setup_test_data.py`、`add_test_cards.py` | 造测试账号的脚本。测试改用 `test_fixtures.py` 自动准备数据；手动给账号发东西用 `grant_materials.py` |

根目录下一些早期的设计和实施文档（如 `PHASE1_IMPLEMENTATION_GUIDE.md`、`PVE_BATTLE_SYSTEM_SUMMARY.md`、`EQUIPMENT_IMPLEMENTATION.md`、`README_SETUP.md`）记录的是当时的做法，里面仍提到上述脚本，以本文为准。
