# 服务器执行清单：HTTPS 子域名

> **已完成（2026-08-29）**：线上已是 `https://api.dengw.xyz`。
> 实际部署与本文档的方案不同——反代 nginx 在独立的 `/root/xray-deploy/` 栈里
> 以容器方式运行，而非系统 nginx，证书也由该栈的 certbot 容器签发。
> **当前拓扑与重建步骤以 [`deploy/README.md`](../deploy/README.md) 为准**，
> 本文档仅作为通用 nginx + certbot 方案的参考保留。

按顺序执行，每步都有验证。**验证不过不要进下一步**——顺序错了会把现有网站或登录搞挂。

把下文所有 `api.你的域名.com` 替换成实际子域名。

---

## 步骤 0：DNS（在域名商控制台做，不在服务器上）

添加一条 A 记录：主机记录 `api`，类型 `A`，记录值 `45.32.85.66`。

**验证：**
```bash
dig +short api.你的域名.com @8.8.8.8
```
输出 `45.32.85.66` 才能继续。

没生效就等，别急着往下走——DNS 未生效时 certbot 必然失败，
连续失败还会触发 Let's Encrypt 频率限制（每域名每小时 5 次）。

---

## 步骤 1：更新代码

```bash
cd ~/github/adult_game
git pull origin claude/mvp-requirements-checklist-NnoLJ
```

这次拉到的是 ProxyFix 支持和 docker-compose 的环境变量开关。

**验证：**
```bash
grep -c BEHIND_PROXY app/__init__.py docker-compose.yml
```
两个文件都应有匹配。

---

## 步骤 2：配置 nginx 反代

新建独立配置，不动现有网站：

```bash
cat > /etc/nginx/sites-available/game-api <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name api.你的域名.com;

    client_max_body_size 4m;

    location / {
        proxy_pass http://127.0.0.1:8080;

        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 60s;
    }
}
EOF
```

写完记得把文件里的 `api.你的域名.com` 改成实际域名：
```bash
nano /etc/nginx/sites-available/game-api
```

启用并**先检查语法**：
```bash
ln -s /etc/nginx/sites-available/game-api /etc/nginx/sites-enabled/
nginx -t
```

**`nginx -t` 不通过绝对不要 reload**，否则可能连现有网站一起挂掉。
通过了再：
```bash
systemctl reload nginx
```

**验证：**
```bash
curl -i http://api.你的域名.com/api/v1/config
```
应返回 200 和配置 JSON。

---

## 步骤 3：签发证书

```bash
apt install -y certbot python3-certbot-nginx      # 装过就跳过
certbot --nginx -d api.你的域名.com
```

交互中问是否把 HTTP 重定向到 HTTPS，选**重定向**。

certbot 只修改 `server_name` 匹配的 server 块，不会碰现有网站。

**验证：**
```bash
curl -i https://api.你的域名.com/api/v1/config
```
返回 200 且证书无警告。

---

## 步骤 4：开启代理模式

```bash
cd ~/github/adult_game
cat > .env <<'EOF'
BEHIND_PROXY=true
SESSION_COOKIE_SECURE=true
EOF

docker-compose up -d --build
```

`.env` 和 `docker-compose.yml` 同目录，之后正常 `docker-compose up -d` 就会自动读取。

**验证：**
```bash
# API 正常
curl -s https://api.你的域名.com/api/v1/config | head -c 100

# Web 端登录不再循环跳转（浏览器打开）
# https://api.你的域名.com/auth/login
```

⚠️ 这一步之后，通过 `http://45.32.85.66:8080` 访问 Web 端的登录会失效，
这是 `SESSION_COOKIE_SECURE=true` 的预期行为——Cookie 只在 HTTPS 下传输。

---

## 步骤 5：收回公网 8080

**确认步骤 4 全部通过后再做。**

```bash
nano docker-compose.yml
```

把端口映射改成只监听本机：
```yaml
    ports:
      - "127.0.0.1:8080:8080"      # 原来是 "8080:8080"
```

```bash
docker-compose up -d
```

**验证：**
```bash
# 本机仍通
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/api/v1/config   # 200

# 域名仍通
curl -s -o /dev/null -w "%{http_code}\n" https://api.你的域名.com/api/v1/config # 200
```

从你 Mac 上 `http://45.32.85.66:8080` 应该连不上了，这是预期的。

顺带在 Vultr 控制台防火墙里删掉 8080 的放行规则。

这一步不是可选的洁癖：`BEHIND_PROXY=true` 开着的同时留公网 8080，
等于任何人都能绕过 nginx 直接发伪造的 `X-Forwarded-For` 头冒充任意来源 IP。

---

## 步骤 6：确认证书自动续期

```bash
certbot renew --dry-run
systemctl list-timers | grep certbot
```

Let's Encrypt 证书 90 天有效，定时任务正常就不用管了。

---

## 完成后

告诉我子域名，我把客户端 `AppConfig.ts` 的 `BACKEND_URL` 改过去，
SSH 隧道就可以撤掉了，iOS 真机也不再需要 ATS 例外配置。

---

## 回滚

任何一步出问题想恢复原状：

```bash
rm /etc/nginx/sites-enabled/game-api
nginx -t && systemctl reload nginx

cd ~/github/adult_game
rm .env
# docker-compose.yml 端口改回 "8080:8080"
docker-compose up -d
```

现有网站全程不受影响——所有改动都在独立的配置文件里。
