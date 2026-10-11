# 脚本说明

仓库根目录的 Python 脚本按用途分为六类。本文说明每个脚本做什么、什么时候跑、能不能重复跑。

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

## 四、运维与数据修复

| 脚本 | 用途 | 用法 | 可重复 |
|---|---|---|---|
| `grant_materials.py` | 给指定账号发一套养成材料，测试用：银两 1000 万、各档经验丹、星石、觉醒石、突破石、技能书、强化石、保护符、各品级碎片，另有四个部位各一件装备 | `python grant_materials.py aavjmz [--dup 关羽 5]`。`--dup` 额外发同名武将卡，觉醒需 1 张、突破需 3 张 | 是，每次叠加 |
| `recycle_enemy_cards.py` | 回收玩家在敌军移出卡池之前抽到的敌军卡。删卡前先把装备卸回背包；抽卡记录保留 | 默认只预览；加 `--apply` 才执行 | 是 |
| `convert_universal_fragments.py` | 把已作废的通用碎片按 1:1 换成普通碎片 | 默认只预览；加 `--apply` 才执行 | 是 |

---

## 五、数据库迁移（`migrate_*`）

项目没有用 Alembic。**新建的数据库用不上这些脚本**：`db.create_all()` 会按当前模型建出带全部字段的表。它们只用于在这些功能上线之前就已经存在的旧库，给已有的表补字段。

| 脚本 | 补什么 | 数据库路径 | 现状 |
|---|---|---|---|
| `migrate_complete.py` | `cards` 表的三国主题字段（属性、五行、势力、职业等），并种卡牌 | `data/game.db` | `entrypoint.sh` 在新库上自动跑；旧库可以手动跑 |
| `migrate_api_token.py` | `api_tokens` 表 | 走 `create_app()` | 已被 `db.create_all()` 覆盖，跑了也无害 |
| `migrate_pve_system.py` / `migrate_pve_system_v2.py` | 用户体力、PVE 统计字段，关卡与进度表 | 走 `create_app()` | 只用于 PVE 上线前的旧库。加参数 `rollback` 为回滚，会交互询问确认 |
| `migrate_growth_system.py` | 成长字段（星级、觉醒、突破、技能等级）与材料表 | ⚠️ 写死 `game.db` | 历史脚本 |
| `migrate_equipment_system.py` | 装备模板、套装表，扩展装备表 | ⚠️ 写死 `game.db` | 历史脚本。会给所有用户发强化石和普通碎片 |
| `migrate_battle_v2.py` | 战斗 v2 字段 | ⚠️ 写死 `game.db` | 历史脚本 |
| `migrate_three_kingdoms.py` | 三国主题字段 | ⚠️ 写死 `game.db` | 历史脚本，已被 `migrate_complete.py` 覆盖 |

⚠️ 标注的四个脚本读写的是**工作目录下的 `game.db`**，而当前数据库在 `data/game.db`。直接运行只会提示「数据库文件不存在」。确实要用的话，先确认数据库位置。

---

## 六、测试数据

| 脚本 | 内容 |
|---|---|
| `init_database.py` | 建测试账号 `testuser` / `password123`，1000 万银两、100 张抽卡券 |
| `setup_test_data.py` | 建 PVE 测试账号 `test_pve_user` / `test123`，满体力，并发卡牌。账号已有卡时会交互询问是否重置 |
| `add_test_cards.py` | 给 `testuser` 发测试卡牌 |

这三个脚本都写**当前数据库**，正式服上慎用。

---

## 七、测试脚本

测试都是独立脚本，没有接 pytest，直接 `python test_xxx.py` 运行。

| 脚本 | 覆盖内容 | 数据库 |
|---|---|---|
| `test_api_client_growth.py` | `/api/v1` 成长、装备、碎片合成接口 | ✅ 临时库 |
| `test_api_client_shop.py` | `/api/v1` 市集：购买、限购、隔天重置 | ✅ 临时库 |
| `test_api_client.py` | `/api/v1` 注册 → 登录 → 抽卡 → 收藏 → 登出 | ⚠️ 当前库，会注册随机账号 |
| `test_pve_system.py` | PVE 表结构、关卡、战斗流程 | ⚠️ 当前库，会建测试用户 |
| `test_equipment_system.py` | 装备强化、套装、属性计算 | ⚠️ 当前库，结束时交互询问是否清理 |
| `test_growth_system.py` | 升级、升星、技能、觉醒、突破公式 | ⚠️ 当前库，依赖事先存在的测试用户；空库下有 6 项失败 |
| `test_battle_system.py` / `test_battle_v2.py` / `test_three_kingdoms_battle.py` / `test_battle_debug.py` | 战斗引擎计算与调试 | ⚠️ 当前库 |

本地想让标「当前库」的测试也不碰开发库，可以临时指定库路径：

```bash
DB_PATH=/tmp/test.db python test_pve_system.py
```

---

## 八、其他

| 文件 | 用途 |
|---|---|
| `run.py` | 本地启动开发服务器（默认端口 8080） |
| `entrypoint.sh` | Docker 启动：新库先跑 `migrate_complete.py`，再启动 gunicorn（默认 1 个 worker、8 个线程） |
| `config.py` | 游戏配置：稀有度概率、抽卡价格、初始资源等 |
| `generate_icons.py` | 生成 PWA 各尺寸图标，需要 Pillow |

## 九、已过时

| 脚本 | 原因 |
|---|---|
| `fix_stage_enemy_config.py` | 原本把关卡敌军配置从卡名改成卡牌 id。现在战斗引擎直接按卡名查找；而且重跑 `init_stages.py` 会把敌军配置恢复成按卡名的写法，所以不需要再跑 |
