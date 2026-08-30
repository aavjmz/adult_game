# 生产部署参考（api.dengw.xyz）

记录 `https://api.dengw.xyz` 的线上拓扑与重建步骤。2026-08-29 建立并验证。

## 拓扑

```
客户端 ──HTTPS──> :443 xray-nginx 容器 ──HTTP──> adult_game 容器 :8080
                  (xray-deploy 栈)              (本仓库, gunicorn)
```

关键点：**反代 nginx 不在本仓库**，而在 `/root/xray-deploy/`（一个独立的
xray/VPN 部署栈）。它同时服务 `dengw.xyz`（静态站）和 xray 的 WebSocket
路径，改动时不要碰同目录下的 `trojan.conf`。

两个栈通过 Docker 网络 `adult_game_default` 打通：xray-nginx 以 external
方式额外接入该网络，从而能用容器名 `adult_game` 直接访问后端。

## 重建步骤

前提：域名 `api.dengw.xyz` 的 A 记录已指向本机，且 80/443 已放行。

### 1. 起应用

```bash
cd /root/github/adult_game
cp .env.example .env
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'   # 填入 SECRET_KEY
docker compose up -d --build
```

`.env` 缺 `SECRET_KEY` 会直接拒绝启动，这是刻意设计。

### 2. 打通网络

在 `/root/xray-deploy/docker-compose.yml` 的 nginx 服务下加入该网络：

```yaml
    networks:
      - xray-net
      - adult_game_default
```

并在顶层 `networks:` 声明 `adult_game_default: {external: true}`。
对运行中的容器可免重启即时生效：

```bash
docker network connect adult_game_default xray-nginx
```

### 3. 装 vhost 并签证书

证书尚未签发时 nginx 加载 `ssl_certificate` 会失败，因此必须分两步：

```bash
# 先只放 HTTP 段（含 ACME 验证路径），注释掉 HTTPS server 块
cp deploy/nginx/api.dengw.xyz.conf /root/xray-deploy/nginx/conf.d/
docker exec xray-nginx nginx -t && docker exec xray-nginx nginx -s reload

# 签发（先 --dry-run 验证，避免撞 Let's Encrypt 频率限制）
docker exec xray-certbot certbot certonly --webroot -w /var/www/certbot \
    -d api.dengw.xyz --key-type ecdsa --non-interactive --agree-tos \
    --register-unsafely-without-email --dry-run

# 去掉 --dry-run 正式签发，然后放开 HTTPS server 块
docker exec xray-nginx nginx -t && docker exec xray-nginx nginx -s reload
```

### 4. 验证

```bash
curl -i https://api.dengw.xyz/api/v1/config          # 期望 200
curl -s -o /dev/null -w '%{http_code}\n' https://dengw.xyz/   # 原站未受影响
timeout 5 curl -s http://<公网IP>:8080/ || echo '8080 已关闭（预期）'
```

## 证书续期

`xray-certbot` 容器每 12h 跑一次 `certbot renew`；`xray-nginx` 的 compose
`command` 每 6h 自动 `nginx -s reload`。两者叠加，续期无需人工介入。

`api.dengw.xyz` 与 `dengw.xyz` 各持一张独立证书，互不影响。

## 排查过的坑

**Docker 发布端口会绕过 ufw。** DNAT 在 PREROUTING 阶段生效，早于 ufw 的
INPUT 链，而 `DOCKER-USER` 链默认为空。所以 `ports: "8080:8080"` 会让端口
对公网开放，且 `ufw status` 里**完全看不到**。本仓库已改为绑定
`127.0.0.1:8080:8080`，外部一律走反代。

**`docker compose up -d` 不会重建镜像。** 代码是构建时 `COPY` 进镜像的，
不带 `--build` 就是在跑旧代码。曾因此让 `BEHIND_PROXY` 空转了很久——环境
变量设了，但镜像里的代码根本没有读取它的那段逻辑。

**网络名曾是隐式的。** `adult_game_default` 由项目名（即目录名）推导。
现已在 `docker-compose.yml` 中显式固定，改目录名不会再静默切断反代。

**nginx 会缓存 upstream 的 DNS 解析。** 直接写 `proxy_pass http://adult_game:8080`
会在启动时解析一次并缓存，容器重建换 IP 后就 502。配置里改用
`resolver 127.0.0.11` + 变量式 `proxy_pass` 强制运行时解析。

**`docker compose down` 会报错。** xray-nginx 挂在 `adult_game_default` 上，
compose 删不掉这个网络。容器仍会正常停止，报错可忽略。

## 不在版本库中的东西

本仓库是**公开仓库**，以下内容只存在于服务器，重建机器时需另行准备：

| 内容 | 位置 | 说明 |
|------|------|------|
| `.env` | 仓库根目录 | 含线上 `SECRET_KEY`，按 `.env.example` 重新生成即可 |
| Let's Encrypt 证书与私钥 | `/root/xray-deploy/certbot/conf/` | 重新签发即可，无需备份 |
| 数据库 | Docker 卷 `game_data` | **需要备份**，重建后无法再生 |
| xray 相关配置 | `/root/xray-deploy/xray/` | 与本项目无关 |
