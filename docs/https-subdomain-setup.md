# 用子域名给游戏后端配 HTTPS

> **已完成（2026-08-29）**：线上已是 `https://api.dengw.xyz`。
> 实际落地方案与本文档不同（反代 nginx 在 `/root/xray-deploy/` 容器栈里，
> 不是系统 nginx）。**当前拓扑见 [`deploy/README.md`](../deploy/README.md)**，
> 本文档作为通用方案参考保留。

现状：VPS 上已有 nginx 托管一个网站，游戏后端跑在 Docker 里监听 8080。

做法：加一个子域名（如 `api.你的域名.com`）指向同一台 VPS，
在 nginx 里新增一个 server 块反代到 `127.0.0.1:8080`。
**现有网站的配置完全不动**，两者互不影响。

配好之后能解决三个问题：
- 国内直连 8080 被拦（走 443 稳定得多）
- iOS 的 ATS 限制（不用再加 `NSAllowsArbitraryLoads`，上架不会被问）
- 令牌明文传输

---

## 一、加 DNS 记录

在域名服务商的控制台加一条 A 记录：

| 类型 | 主机记录 | 记录值 |
|------|---------|--------|
| A | `api` | `45.32.85.66` |

等生效后验证（可能要几分钟到几十分钟）：

```bash
dig +short api.你的域名.com
# 应输出 45.32.85.66
```

DNS 没生效就往下走，certbot 签发证书会失败。

---

## 二、加 nginx 配置

新建独立文件，不要改现有站点的配置：

```bash
nano /etc/nginx/sites-available/game-api
```

内容（把域名换成你的）：

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name api.你的域名.com;

    # 客户端上传/响应都不大，但抽卡十连的JSON稍长，给足缓冲
    client_max_body_size 4m;

    location / {
        proxy_pass http://127.0.0.1:8080;

        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        # 这一条让Flask知道外面是HTTPS，缺了会导致重定向跳回http
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 60s;
    }
}
```

启用并检查语法：

```bash
ln -s /etc/nginx/sites-available/game-api /etc/nginx/sites-enabled/
nginx -t          # 必须显示 syntax is ok / test is successful
systemctl reload nginx
```

`nginx -t` 不通过就不要 reload，否则可能连现有网站一起挂掉。

先用 HTTP 验证反代通了：

```bash
curl -i http://api.你的域名.com/api/v1/config
```

---

## 三、签发证书

```bash
# 没装过 certbot 的话
apt install -y certbot python3-certbot-nginx

certbot --nginx -d api.你的域名.com
```

certbot 只会修改 `server_name` 匹配的那个 server 块，不会动现有网站。
过程中问是否重定向 HTTP 到 HTTPS，选 **重定向**。

验证：

```bash
curl -i https://api.你的域名.com/api/v1/config
```

应返回 200 和完整的配置 JSON。

---

## 四、告诉 Flask 它在代理后面

拉取最新代码后，用环境变量开启：

```bash
cd /path/to/adult_game
git pull

BEHIND_PROXY=true SESSION_COOKIE_SECURE=true docker-compose up -d --build
```

或者写进 `.env` 文件（和 `docker-compose.yml` 同目录），之后正常 `docker-compose up -d` 即可：

```
BEHIND_PROXY=true
SESSION_COOKIE_SECURE=true
```

两个变量的作用：

- `BEHIND_PROXY=true` — Flask 读取 `X-Forwarded-Proto` 还原真实协议。
  不开的话 HTTPS 下的重定向会生成 `http://` 地址，Web端登录会跳错。
  **只在确实有反向代理时开启**：直连暴露时信任这些头等于允许客户端伪造来源IP。

- `SESSION_COOKIE_SECURE=true` — Web端 Cookie 只在 HTTPS 下传输。
  ⚠️ 开启后，通过 `http://45.32.85.66:8080` 访问的Web端登录会失效。
  确认 HTTPS 域名正常工作、且不再用 IP 直连之后再开。

---

## 五、收回对外暴露的 8080（可选但建议）

HTTPS 验证通过后，让 8080 只对本机开放，公网只能走 nginx：

编辑 `docker-compose.yml`：

```yaml
    ports:
      - "127.0.0.1:8080:8080"    # 原来是 "8080:8080"
```

```bash
docker-compose up -d
```

改完 `http://45.32.85.66:8080` 就不通了，这是预期行为——所有流量走
`https://api.你的域名.com`。

顺带把 Vultr 控制台防火墙里 8080 的放行规则删掉。

---

## 六、改客户端地址

`cocos/SanguoCardGame/assets/scripts/core/AppConfig.ts`：

```ts
static readonly USE_LOCAL_TUNNEL = false;       // 隧道用不着了

static readonly BACKEND_URL = AppConfig.USE_LOCAL_TUNNEL
    ? 'http://localhost:8080'
    : 'https://api.你的域名.com';                // ← 改这里
```

改完在 Cocos 里预览跑一次 NetworkTest，确认全部通过。

---

## 七、证书续期

certbot 会自动装好续期定时任务，验证一下：

```bash
systemctl list-timers | grep certbot
certbot renew --dry-run
```

Let's Encrypt 证书 90 天有效期，自动续期正常的话不用管。

---

## 出问题时

| 现象 | 原因 |
|------|------|
| certbot 报 DNS 验证失败 | A 记录没生效，`dig +short` 确认 |
| certbot 报 80 端口占用 | 现有 nginx 在跑，用 `--nginx` 插件而非 `--standalone` |
| 502 Bad Gateway | 后端容器没起来，`docker-compose logs --tail=50 game` |
| 现有网站受影响 | `nginx -t` 检查，必要时删掉 `sites-enabled/game-api` 软链再 reload |
| Web端登录跳回登录页 | `SESSION_COOKIE_SECURE=true` 但在用 HTTP 访问 |
| 客户端 CORS 报错 | 后端没重启，或 nginx 没转发 OPTIONS |
