# 三国卡牌游戏「十三州」· 项目状态

> 最后更新：2026-10-11
> 剩余任务见 [TODO.md](TODO.md)；脚本用途见 [docs/SCRIPTS.md](docs/SCRIPTS.md)。

## 概览

| 项 | 内容 |
|---|---|
| 后端 | Python 3.12 · Flask 3.0 · Flask-SQLAlchemy · SQLite（可换 PostgreSQL） |
| 主客户端 | Cocos Creator 3.8（`cocos/SanguoCardGame/`），走 `/api/v1` Bearer Token 接口 |
| Web 端 | Jinja2 + 原生 JS（早期版本，Session Cookie 鉴权，仍可用但不再是主力） |
| 部署 | Docker Compose，端口 8080，数据库在 `game_data` 卷 |

主客户端的玩法数据已全部由服务端保存与结算，客户端本机只存「设置」开关与旧版阵容的一次性迁移数据。

## 模块完成度

| 模块 | 后端 | Cocos 客户端 | 说明 |
|---|---|---|---|
| 登录 / 注册 | ✅ | ✅ | 账号密码；已登录启动直接进主城。第三方登录、短信验证码未接 |
| 主城 | — | ✅ | 征伐卡、通行证卡读真实进度；月卡为占位 |
| 招贤（抽卡） | ✅ | ✅ | 单抽 / 十连，SR 10 抽、SSR 90 抽保底 |
| 将台（武将） | ✅ | ✅ | 升级、升星、技能升级、觉醒、突破、装备穿戴与强化 |
| 编伍 | ✅ | ✅ | 六阵位，存服务端；出征与军演默认用此阵容 |
| 征伐（PVE） | ✅ | ✅ | 3 章 30 关，体力，自动 / 手动 / 托管战斗，扫荡，掉落，三星评价 |
| 市集 | ✅ | ✅ | 银两购买养成与锻造材料，每日限购 |
| 行囊 | ✅ | ✅ | 材料与装备 |
| 军令 | ✅ | ✅ | 日常 / 周常 / 成就 / 通行证（按月一季），军功宝箱 |
| 军书（邮件） | ✅ | ✅ | 欢迎信、平定整章赏赐、运维 `send_mail.py`；附物领取、弃书、过期 |
| 军演（PVP） | ✅ | ✅ | 异步：打真人最新编伍或电脑阵容，Elo 积分，演券，段位之赏，战斗回放 |
| 盟 | ✅ | ✅ | 建盟入盟、职位、捐献、盟令、盟仓、盟内 / 世界聊天。盟战攻城、私信未做 |
| 设置 | — | ⚠️ | 只有「自动战斗」「重置阵型」「退出登录」生效，其余开关无实际效果 |

## 后端结构

- **客户端接口**：`app/routes/api_client.py`，`/api/v1/*`，统一 `{success, data, error}` 信封；成长与装备接口复用 Web 端视图（17 个）。
- **玩法逻辑**：`app/utils/`：`battle_core.py`（可暂停、可序列化的回合制战斗）、`pve_battle.py`、`orders.py`、`mail.py`、`arena.py`、`guild.py`、`formation.py`、`stamina.py`。
- **数值表**（改了无需迁移）：`app/stage_data.py`、`app/enemy_cards.py`、`app/shop_data.py`、`app/orders_data.py`、`app/mail_data.py`、`app/arena_data.py`、`app/guild_data.py`、`config.py`。
- **奖励发放**：`app/rewards.py`，军令、军书、军演、盟共用。
- **数据表**：`db.create_all()` 启动时自动建新表；给旧表加列时在 `create_app()` 里加幂等的 ALTER（见 CLAUDE.md）。

## 测试

根目录 17 个 `test_*.py`，各自直接运行。`test_api_client_*.py` 与 `test_battle_*.py` 使用临时库，不碰 `data/game.db`。
客户端没有自动化测试；改动后需在 Cocos 编辑器里实测。

## 已知限制

- 战斗为服务端结算，客户端回放（征伐与军演共用 Battle 场景）。
- 聊天用轮询（8 秒），不是推送。
- 没有充值、月卡、排行榜页面、好友、私信、盟战。
- 第三方登录、短信 / 邮件验证码需要外部服务与资质，当前为演示实现（验证码固定 123456）。
