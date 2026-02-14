# ngrok 完全指南

## 什么是ngrok？

**ngrok**（读作"en-grok"）是一个**反向代理工具**，可以将你本地运行的应用**瞬间暴露到公网**，获得一个公开可访问的HTTPS URL。

### 简单理解

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
没有ngrok的情况：

你的电脑 (localhost:8080)
  ↓
只有你自己能访问
❌ 朋友无法访问
❌ 手机无法访问（除非在同一WiFi）
❌ 客户无法查看demo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

使用ngrok后：

你的电脑 (localhost:8080)
  ↓
ngrok隧道
  ↓
公网URL: https://abc123.ngrok-free.app
  ↓
✅ 全世界任何人都能访问
✅ iPhone可以直接打开
✅ 客户可以查看demo
✅ 支持HTTPS（安全连接）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 工作原理

### 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                     互联网（公网）                       │
│                                                         │
│   用户访问: https://abc123.ngrok-free.app              │
│                          │                              │
│                          ▼                              │
│              ┌───────────────────────┐                  │
│              │   ngrok云端服务器      │                  │
│              │  (ngrok.com运营)      │                  │
│              └───────────┬───────────┘                  │
│                          │                              │
└──────────────────────────┼──────────────────────────────┘
                           │
                  安全的WebSocket隧道
                  (加密传输)
                           │
┌──────────────────────────┼──────────────────────────────┐
│                你的本地网络（私网）                       │
│                          ▼                              │
│              ┌───────────────────────┐                  │
│              │   ngrok客户端程序      │                  │
│              │   (运行在你电脑上)     │                  │
│              └───────────┬───────────┘                  │
│                          │                              │
│                          ▼                              │
│              ┌───────────────────────┐                  │
│              │   你的Flask应用        │                  │
│              │   localhost:8080      │                  │
│              └───────────────────────┘                  │
└─────────────────────────────────────────────────────────┘

流程说明：
1. 用户访问公网URL (https://abc123.ngrok-free.app)
2. 请求到达ngrok云端服务器
3. ngrok服务器通过隧道转发给你的本地客户端
4. ngrok客户端转发给localhost:8080
5. 你的Flask应用处理请求
6. 响应原路返回给用户
```

---

## 主要用途

### 1. 移动端测试（最常用）⭐⭐⭐⭐⭐

```bash
场景：你在开发Web应用，想在真实iPhone上测试

传统方式：
  ❌ 部署到测试服务器（耗时30分钟+）
  ❌ 配置域名和SSL证书
  ❌ 每次修改都要重新部署

ngrok方式：
  ✅ ngrok http 8080（1秒启动）
  ✅ 在iPhone上打开URL立即查看
  ✅ 修改代码，刷新即可看到效果
  ✅ 自动提供HTTPS
```

### 2. 演示Demo给客户

```bash
场景：客户要看项目进度，但项目还没部署

传统方式：
  ❌ 紧急部署到服务器
  ❌ 或者发屏幕截图/录屏

ngrok方式：
  ✅ ngrok http 8080
  ✅ 发送URL给客户
  ✅ 客户直接在浏览器体验
  ✅ 实时交互，比视频更直观
```

### 3. Webhook开发和测试

```bash
场景：开发微信支付/GitHub Webhook回调

问题：第三方服务需要回调你的接口，但你在本地开发

ngrok方式：
  ✅ ngrok http 8080
  ✅ 将ngrok URL配置为回调地址
  ✅ 本地调试接收到的Webhook请求
  ✅ 可以断点调试回调逻辑
```

### 4. 物联网设备远程访问

```bash
场景：树莓派运行在家里，你在公司想访问

ngrok方式：
  ✅ 在树莓派上运行ngrok
  ✅ 从任何地方访问家里的设备
  ✅ 不需要配置路由器端口转发
```

---

## 免费版 vs 付费版

### 免费版功能（够用了！）

```yaml
✅ 随机域名: https://abc123.ngrok-free.app
✅ HTTPS自动提供
✅ HTTP/TCP隧道
✅ 40连接/分钟限制
✅ 1个在线隧道
✅ 访问前显示警告页面（可点击"Visit Site"继续）

⚠️ 限制：
  - 每次重启URL会变
  - 有访问警告页面（对开发测试影响不大）
  - 每分钟40个连接（通常足够）
  - 隧道8小时后自动断开（重新运行即可）
```

### 付费版（$8-$20/月）

```yaml
Plus ($8/月):
  ✅ 固定域名: https://yourname.ngrok.app
  ✅ 无警告页面
  ✅ 3个隧道同时在线
  ✅ 100连接/分钟

Pro ($20/月):
  ✅ 自定义域名: https://yourdomain.com
  ✅ IP白名单
  ✅ 10个隧道
  ✅ 500连接/分钟

Enterprise:
  ✅ 专用云/本地部署
  ✅ SSO认证
  ✅ 无限制
```

---

## 安装和使用

### 方法1: 快速安装（推荐）

#### macOS
```bash
# 使用Homebrew
brew install ngrok/ngrok/ngrok
```

#### Linux
```bash
# 下载二进制文件
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list && \
  sudo apt update && sudo apt install ngrok
```

#### Windows
```powershell
# 使用Chocolatey
choco install ngrok

# 或者使用Scoop
scoop install ngrok
```

### 方法2: 手动下载

1. 访问 https://ngrok.com/download
2. 下载适合你操作系统的版本
3. 解压到任意目录
4. 将目录添加到PATH（可选）

### 首次配置

```bash
# 1. 注册ngrok账号（免费）
# 访问 https://dashboard.ngrok.com/signup

# 2. 获取认证令牌（authtoken）
# 登录后访问 https://dashboard.ngrok.com/get-started/your-authtoken

# 3. 配置令牌
ngrok config add-authtoken YOUR_AUTH_TOKEN

# 这会将令牌保存到 ~/.ngrok2/ngrok.yml
```

---

## 基本使用示例

### 示例1: 暴露HTTP服务（最常用）

```bash
# 你的Flask应用运行在 localhost:8080
python run.py

# 新终端，启动ngrok
ngrok http 8080

# 输出示例：
# ngrok
#
# Session Status                online
# Account                       yourname@email.com (Plan: Free)
# Version                       3.5.0
# Region                        United States (us)
# Latency                       20ms
# Web Interface                 http://127.0.0.1:4040
# Forwarding                    https://abc123.ngrok-free.app -> http://localhost:8080
#
# Connections                   ttl     opn     rt1     rt5     p50     p90
#                               0       0       0.00    0.00    0.00    0.00

✅ 公网URL: https://abc123.ngrok-free.app
✅ 本地监控: http://127.0.0.1:4040 (可以查看所有请求)
```

### 示例2: 指定子域名（需要付费版）

```bash
ngrok http --domain=myapp.ngrok.app 8080

# 固定域名，不会变化
```

### 示例3: 使用自定义域名（需要Pro版）

```bash
ngrok http --domain=demo.yourdomain.com 8080
```

### 示例4: 添加基本认证

```bash
# 访问时需要用户名和密码
ngrok http 8080 --basic-auth="username:password"
```

### 示例5: 仅允许特定IP访问（需要付费版）

```bash
ngrok http 8080 --cidr-allow="1.2.3.4/32"
```

### 示例6: 暴露HTTPS服务

```bash
# 如果本地已经是HTTPS
ngrok http https://localhost:8443
```

### 示例7: TCP隧道（SSH、数据库等）

```bash
# 暴露SSH服务
ngrok tcp 22

# 暴露MySQL
ngrok tcp 3306

# 暴露PostgreSQL
ngrok tcp 5432
```

### 示例8: 配置文件方式（推荐）

创建 `~/.ngrok2/ngrok.yml`:

```yaml
version: "2"
authtoken: YOUR_AUTH_TOKEN

tunnels:
  flask-app:
    proto: http
    addr: 8080
    inspect: true

  mysql:
    proto: tcp
    addr: 3306

  ssh:
    proto: tcp
    addr: 22
```

使用配置启动：
```bash
# 启动指定隧道
ngrok start flask-app

# 启动多个隧道
ngrok start flask-app mysql

# 启动所有隧道
ngrok start --all
```

---

## Web界面（监控台）

启动ngrok后，访问 **http://127.0.0.1:4040** 可以看到：

```
功能：
✅ 所有HTTP请求列表
✅ 请求详情（Headers、Body、响应）
✅ 重放请求（Replay）
✅ 请求响应时间统计
✅ 连接状态

用途：
→ 调试API接口
→ 查看Webhook回调内容
→ 测试不同请求参数
→ 性能分析
```

---

## 实际应用场景

### 场景1: 开发微信小程序/公众号

```bash
问题：
  - 微信要求回调URL必须是公网HTTPS
  - 本地开发无法直接测试

解决：
# 1. 本地运行微信后端
python wechat_backend.py  # localhost:8080

# 2. 启动ngrok
ngrok http 8080

# 3. 在微信公众平台配置回调URL
服务器地址: https://abc123.ngrok-free.app/wechat/callback

# 4. 本地调试微信消息
→ 用户发消息给公众号
→ 微信服务器调用你的ngrok URL
→ ngrok转发到本地localhost:8080
→ 你可以断点调试
```

### 场景2: 测试支付回调

```bash
# 1. 本地运行支付系统
python payment_server.py  # localhost:5000

# 2. ngrok暴露
ngrok http 5000

# 3. 配置支付宝/微信支付回调URL
https://abc123.ngrok-free.app/payment/notify

# 4. 发起测试支付
→ 支付成功后，支付宝回调到ngrok URL
→ 本地收到回调数据
→ 可以调试支付逻辑
```

### 场景3: 给远程同事演示

```bash
# 团队成员在不同城市，想看你的开发进度

# 1. 启动项目
npm start  # localhost:3000

# 2. ngrok分享
ngrok http 3000

# 3. 发送URL给同事
https://abc123.ngrok-free.app

# 同事可以：
✅ 直接在浏览器体验
✅ 实时看到你的修改（刷新即可）
✅ 测试功能并反馈
```

---

## 替代方案

| 工具 | 特点 | 价格 | 推荐度 |
|------|------|------|--------|
| **ngrok** | 最流行，功能强大 | 免费+付费 | ⭐⭐⭐⭐⭐ |
| **localtunnel** | 完全免费，开源 | 免费 | ⭐⭐⭐⭐ |
| **serveo** | SSH转发，简单 | 免费 | ⭐⭐⭐ |
| **Cloudflare Tunnel** | 企业级，免费 | 免费 | ⭐⭐⭐⭐ |
| **Pagekite** | 老牌工具 | 付费 | ⭐⭐⭐ |

### localtunnel示例（完全免费）

```bash
# 安装
npm install -g localtunnel

# 使用
lt --port 8080

# 输出:
# your url is: https://random-name.loca.lt

# 特点：
✅ 完全免费
✅ 开源
⚠️ 稳定性不如ngrok
⚠️ 速度较慢
```

### Cloudflare Tunnel（企业级免费）

```bash
# 安装
brew install cloudflared  # macOS
# 或从 https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/

# 使用
cloudflared tunnel --url localhost:8080

# 特点：
✅ 完全免费
✅ Cloudflare CDN加速
✅ 无限流量
✅ 企业级稳定性
⚠️ 配置相对复杂
```

---

## 安全性考虑

### ⚠️ 注意事项

```bash
1. 不要暴露敏感服务
   ❌ 生产数据库
   ❌ 含有真实用户数据的系统
   ❌ 管理后台（除非加了认证）

2. 使用基本认证保护
   ✅ ngrok http 8080 --basic-auth="user:pass"

3. 限制访问时间
   ✅ 测试完立即关闭ngrok
   ✅ 免费版8小时自动断开

4. 检查ngrok配置
   ✅ 确认没有暴露不该暴露的端口
   ✅ 查看 ~/.ngrok2/ngrok.yml

5. 监控访问日志
   ✅ 通过 http://127.0.0.1:4040 查看所有请求
   ✅ 发现异常访问立即关闭
```

### 安全最佳实践

```bash
# ✅ 推荐：仅用于开发测试
ngrok http 8080  # 测试完就关闭

# ✅ 推荐：添加认证
ngrok http 8080 --basic-auth="test:demo123"

# ✅ 推荐：使用配置文件管理
# ~/.ngrok2/ngrok.yml
tunnels:
  safe-tunnel:
    proto: http
    addr: 8080
    auth: "user:password"
    inspect: true

# ❌ 不推荐：长期暴露无认证的服务
ngrok http 8080  # 然后让它运行几天 ← 危险！
```

---

## 常见问题

### Q1: 免费版的警告页面能去掉吗？

```
A: 免费版无法去掉。访问时会先显示：
   "You are about to visit: abc123.ngrok-free.app
    Click 'Visit Site' to continue"

   解决方案：
   1. 付费升级 ($8/月)
   2. 使用替代方案（localtunnel, Cloudflare Tunnel）
   3. 接受这个警告页面（开发测试够用）
```

### Q2: 每次启动URL都变怎么办？

```
A: 免费版每次URL都是随机的。

   解决方案：
   1. 付费版可以固定域名 ($8/月)
   2. 使用配置文件自动重连
   3. 部署到真实服务器（Railway等）
```

### Q3: ngrok隧道经常断开？

```
A: 免费版限制：
   - 8小时自动断开
   - 网络波动会断开

   解决方案：
   1. 监控脚本自动重启
   2. 使用 systemd/supervisor 守护进程
   3. 付费版更稳定
```

### Q4: 速度慢怎么办？

```
A: 可能原因：
   - ngrok服务器在国外（美国）
   - 免费版限速

   解决方案：
   1. 付费版选择区域（亚太、欧洲等）
   2. 使用国内替代方案（花生壳等）
   3. 仅用于测试，不用于生产
```

### Q5: 如何在Docker容器中使用？

```bash
# 方式1: Docker外运行ngrok
ngrok http 8080  # 转发到容器映射的端口

# 方式2: Docker内运行ngrok
docker run -it -e NGROK_AUTHTOKEN=YOUR_TOKEN \
  ngrok/ngrok http host.docker.internal:8080
```

---

## 实用技巧

### 技巧1: 保存常用配置

`~/.ngrok2/ngrok.yml`:
```yaml
version: "2"
authtoken: YOUR_TOKEN

tunnels:
  flask:
    proto: http
    addr: 8080
    inspect: true
    bind_tls: true  # 仅HTTPS

  react:
    proto: http
    addr: 3000
    host_header: rewrite  # 处理HOST头
```

使用：
```bash
ngrok start flask
```

### 技巧2: 自动重连脚本

```bash
#!/bin/bash
# auto-ngrok.sh

while true; do
  ngrok http 8080
  echo "ngrok断开，5秒后重连..."
  sleep 5
done
```

### 技巧3: 与PM2集成

```javascript
// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'flask-app',
      script: 'run.py',
      interpreter: 'python3'
    },
    {
      name: 'ngrok',
      script: 'ngrok',
      args: 'http 8080'
    }
  ]
}
```

---

## 总结

### ngrok的核心价值

```
✅ 10秒内将本地应用暴露到公网
✅ 自动提供HTTPS（免费）
✅ 无需配置路由器、域名、证书
✅ 非常适合开发、测试、演示
✅ Web界面方便调试API
```

### 最佳使用场景

```
1. 移动端开发测试 ⭐⭐⭐⭐⭐
2. Webhook开发调试 ⭐⭐⭐⭐⭐
3. 快速演示Demo ⭐⭐⭐⭐⭐
4. 第三方集成测试 ⭐⭐⭐⭐
5. 远程协作 ⭐⭐⭐⭐
```

### 不适合的场景

```
❌ 生产环境部署
❌ 长期稳定服务
❌ 高并发场景
❌ 需要低延迟
❌ 处理敏感数据
```

---

## 你的项目使用ngrok

### 立即开始

```bash
# 1. 安装ngrok
brew install ngrok  # macOS
# 或访问 https://ngrok.com/download

# 2. 注册并配置（免费）
# https://dashboard.ngrok.com/signup
ngrok config add-authtoken YOUR_TOKEN

# 3. 启动Flask应用
cd /home/user/adult_game
python run.py

# 4. 新终端启动ngrok
ngrok http 8080

# 5. 复制HTTPS URL
# 示例: https://abc123.ngrok-free.app

# 6. iPhone Safari打开
# → 分享 → 添加到主屏幕

# 完成！你的游戏已经在iPhone上了！
```

### 效果

```
✅ 10分钟内在iPhone上看到效果
✅ 修改代码，刷新iPhone即可看到
✅ 可以分享给朋友测试
✅ 完全免费
✅ HTTPS安全连接（PWA需要）
```
