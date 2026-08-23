# 服务器部署清单（客户端API上线）

本次更新内容：新增 `/api/v1` 客户端Token接口 + 修复Web端登录故障。

目标服务器：`45.32.85.66:8080`
代码分支：`claude/mvp-requirements-checklist-NnoLJ`

---

## 一、更新代码

```bash
cd /path/to/adult_game        # 换成服务器上的实际路径

# 先备份数据库（重要）
cp data/game.db data/game.db.backup.$(date +%Y%m%d)

git fetch origin claude/mvp-requirements-checklist-NnoLJ
git checkout claude/mvp-requirements-checklist-NnoLJ
git pull origin claude/mvp-requirements-checklist-NnoLJ
```

如果 `git checkout` 报本地有改动冲突，先 `git stash` 暂存，或 `git checkout -- <文件>` 丢弃。

---

## 二、部署（按你的部署方式二选一）

### 方式A：Docker 部署

```bash
docker-compose down
docker-compose up -d --build
```

必须带 `--build`：镜像里的代码是构建时 `COPY` 进去的，不重新构建不会生效。

数据库挂在 `game_data` 卷上，重建镜像不会丢数据。

### 方式B：直接跑 Python

```bash
pip install -r requirements.txt

# 重启服务（按你的方式，以下三选一）
systemctl restart adult_game       # systemd
supervisorctl restart adult_game   # supervisor
# 或手动 kill 掉旧进程后重新 python run.py
```

---

## 三、建表

`app/__init__.py` 启动时会调 `db.create_all()`，`api_tokens` 表会自动创建，
所以这一步**通常不用手动执行**。但跑一下可以明确确认建表结果、顺带清理过期令牌：

```bash
# Docker
docker-compose exec game python migrate_api_token.py

# 直接部署
python migrate_api_token.py
```

预期输出：
```
[完成] 已创建 api_tokens 表        （或 [跳过] api_tokens 表已存在）
[状态] 当前有效令牌数: 0
```

---

## 四、验证

### 1. 配置接口（免登录，最快的连通性检查）

```bash
curl http://45.32.85.66:8080/api/v1/config
```

预期返回JSON，包含 `rarities` 和 `gacha` 两个字段：
```json
{"success":true,"data":{"gacha":{...},"rarities":{...}},"error":null}
```

### 2. 完整链路（注册 → 抽卡）

```bash
# 注册，拿令牌
curl -X POST http://45.32.85.66:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"apitest01","email":"apitest01@test.com","password":"test123456"}'

# 把返回的 token 填到下面
TOKEN="粘贴上一步返回的token"

# 查用户信息
curl http://45.32.85.66:8080/api/v1/user/info \
  -H "Authorization: Bearer $TOKEN"

# 单抽
curl -X POST http://45.32.85.66:8080/api/v1/gacha/pull \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"type":"single"}'
```

抽卡应返回一张卡牌，且 `user.tickets` 从 10 变成 9。

### 3. Web端登录（本次修复的故障）

浏览器打开 `http://45.32.85.66:8080/auth/login`，用已有账号登录。

修复前的症状：登录后跳回登录页，反复循环。
修复后：应正常进入 dashboard。

原因是 `SESSION_COOKIE_SECURE=True` 让浏览器只肯在HTTPS下回传Cookie，
而服务器是纯HTTP，Cookie 一直没被送回来。

---

## 五、可选：跑测试套件

```bash
# 注意：会往数据库写测试用户，跑完自动清理
python test_api_client.py
```

预期 `通过: 37   失败: 0`。

---

## 六、上线后待办（非本次必须）

**配置HTTPS**。当前令牌在网络上明文传输，内测可接受，正式发布前应处理。
Caddy 最省事，两行配置自动签发证书：

```
your-domain.com {
    reverse_proxy localhost:8080
}
```

HTTPS 生效后，给服务加环境变量开启安全Cookie：
```bash
SESSION_COOKIE_SECURE=true
```

---

## 出问题时的排查

| 现象 | 检查 |
|------|------|
| `/api/v1/config` 404 | 代码没更新成功，确认分支和重启 |
| `/api/v1/config` 500 | 看日志：`docker-compose logs -f game` |
| 注册报 `no such table: api_tokens` | 手动跑第三步的建表脚本 |
| 客户端连不上但curl正常 | 防火墙/安全组是否放行8080 |
| Web登录仍循环跳转 | 确认环境变量里没有残留 `SESSION_COOKIE_SECURE=true` |
