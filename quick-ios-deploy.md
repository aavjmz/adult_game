# 快速iOS部署指南

## 方案1: PWA直接安装 (5分钟)

### 部署到公网

**选项A: Railway (推荐)**
```bash
# 1. 访问 https://railway.app 并登录
# 2. 点击 "New Project" → "Deploy from GitHub repo"
# 3. 选择你的仓库
# 4. Railway会自动检测Dockerfile并部署
# 5. 获得URL: https://xxx.railway.app
```

**选项B: Render**
```bash
# 1. 访问 https://render.com 并登录
# 2. 点击 "New +" → "Web Service"
# 3. 连接GitHub仓库
# 4. 设置:
#    - Environment: Docker
#    - Port: 8080
# 5. 点击 "Create Web Service"
# 6. 获得URL: https://xxx.onrender.com
```

**选项C: Fly.io**
```bash
# 安装Fly CLI
curl -L https://fly.io/install.sh | sh

# 登录
flyctl auth login

# 部署
flyctl launch
flyctl deploy

# 获得URL: https://xxx.fly.dev
```

### 在iPhone上安装

1. 在iPhone Safari中打开你的URL
2. 点击底部「分享」按钮 (⬆️图标)
3. 向下滚动找到「添加到主屏幕」
4. 点击「添加」
5. 完成！桌面会出现App图标

**注意事项：**
- ✅ PWA在iOS上全屏运行，像原生App
- ✅ 支持离线缓存（Service Worker）
- ✅ 有独立图标和启动画面
- ⚠️ 不在App Store，无法公开分发
- ⚠️ iOS Safari对PWA有些限制（推送通知等）

---

## 方案2: Capacitor打包为原生iOS App (1-2天)

### 前置要求

- Mac电脑（必须）
- Xcode 14+
- Node.js 18+
- Apple开发者账号 ($99/年，可选用于App Store)

### 步骤1: 安装Capacitor

```bash
cd /home/user/adult_game

# 安装Capacitor CLI
npm install -g @capacitor/cli @capacitor/core

# 初始化Capacitor项目
npm init -y  # 如果没有package.json
npx cap init

# 提示时输入：
# App name: 三国卡牌游戏
# App ID: com.yourdomain.cardgame
# Web directory: app/static (或app/templates，根据你的静态文件位置)
```

### 步骤2: 添加iOS平台

```bash
# 安装iOS平台
npm install @capacitor/ios
npx cap add ios

# 打开Xcode项目
npx cap open ios
```

### 步骤3: 配置Web资源

**问题：** 你的项目是Flask模板渲染，不是纯静态文件。

**解决方案A - 使用API模式（推荐）：**

```bash
# 1. 创建一个纯前端版本
mkdir -p mobile-client/www

# 2. 将app/templates中的HTML转换为静态页面
# 3. 修改所有API调用指向后端URL

# mobile-client/www/config.js
const API_BASE_URL = 'https://your-backend.railway.app';
```

**解决方案B - 使用WebView直接加载（更快）：**

在Capacitor中配置webDir为远程URL：

```json
// capacitor.config.json
{
  "appId": "com.yourdomain.cardgame",
  "appName": "三国卡牌",
  "webDir": "www",
  "server": {
    "url": "https://your-app.railway.app",  // 指向你的Flask后端
    "cleartext": true
  }
}
```

### 步骤4: 在Xcode中配置

1. 打开项目：`npx cap open ios`
2. 选择模拟器或真机设备
3. 点击▶️运行按钮
4. 在iPhone/模拟器上查看效果

### 步骤5: 真机测试

**无需Apple开发者账号的方法：**

1. 连接iPhone到Mac
2. Xcode → Preferences → Accounts → 添加你的Apple ID（免费）
3. 选择你的iPhone设备
4. Xcode会自动配置免费证书
5. 点击运行
6. iPhone上：设置 → 通用 → VPN与设备管理 → 信任证书
7. 打开App测试

**限制：**
- ⚠️ 免费证书每7天需要重新签名
- ⚠️ 无法分发给其他设备
- ⚠️ 部分功能受限（推送通知等）

### 步骤6: TestFlight分发（需要开发者账号）

```bash
# 1. 在App Store Connect创建App
# 2. 在Xcode中配置Bundle ID
# 3. Archive构建
# 4. 上传到App Store Connect
# 5. 添加测试用户
# 6. 通过TestFlight邀请链接分发
```

**优势：**
- ✅ 可以分发给最多10,000个测试用户
- ✅ 90天有效期（可续期）
- ✅ 通过邀请链接轻松分发
- ✅ 收集崩溃报告和反馈

---

## 方案3: 最简单的快速验证方案（推荐！）

### 使用ngrok + PWA (10分钟)

```bash
# 1. 安装ngrok
# 访问 https://ngrok.com 注册并下载

# 2. 启动你的Flask应用
python run.py  # 默认运行在 localhost:8080

# 3. 启动ngrok隧道
ngrok http 8080

# 4. 你会得到一个公网URL，例如:
# https://abc123.ngrok-free.app

# 5. 在iPhone Safari中打开这个URL
# 6. 添加到主屏幕

# 完成！无需部署，即可在iPhone上测试PWA
```

**优势：**
- ✅ 完全免费
- ✅ 10分钟完成
- ✅ 实时调试（修改代码立即生效）
- ✅ 支持HTTPS（PWA要求）
- ⚠️ 临时URL（重启ngrok会变）
- ⚠️ 仅用于测试，不适合生产

---

## 对比总结

| 方案 | 时间 | 成本 | 适用场景 | 推荐度 |
|------|------|------|----------|--------|
| **ngrok + PWA** | 10分钟 | 免费 | 快速验证效果 | ⭐⭐⭐⭐⭐ |
| **部署 + PWA** | 30分钟 | 免费 | 持续测试 | ⭐⭐⭐⭐ |
| **Capacitor + 免费证书** | 1天 | 免费 | 个人测试真机 | ⭐⭐⭐⭐ |
| **Capacitor + TestFlight** | 2天 | $99/年 | 团队测试/小范围分发 | ⭐⭐⭐⭐⭐ |
| **App Store上架** | 1周+ | $99/年 | 正式发布 | ⭐⭐⭐ |

---

## 推荐路径

### 第1天：快速验证
```bash
使用 ngrok + PWA
→ 10分钟在iPhone上看到效果
→ 确认基本功能可用
→ 收集初步反馈
```

### 第2-3天：持久化部署
```bash
部署到 Railway/Render
→ 获得永久URL
→ 分享给朋友测试
→ 持续迭代
```

### 第4-7天：原生App体验
```bash
使用 Capacitor + TestFlight
→ 打包为真正的iOS App
→ 通过TestFlight分发给测试用户
→ 收集更专业的反馈
```

### 第8天+：考虑是否需要App Store
```bash
根据反馈决定
→ 如果用户量大：上架App Store
→ 如果用户少：继续PWA即可
```
