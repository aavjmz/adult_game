# 游戏部署文档

## 📋 概述

本文档详细说明如何使用Docker容器部署成人卡牌游戏到服务器。

## 🔧 环境要求

### 必需软件
- Docker 20.10+
- Docker Compose 2.0+
- Git

### 系统要求
- Linux服务器（推荐Ubuntu 20.04+）
- 最低配置：1GB RAM，10GB磁盘空间
- 开放端口：8080

## 📦 部署文件说明

### 核心部署文件

| 文件 | 说明 |
|------|------|
| `Dockerfile` | Docker镜像构建配置 |
| `docker-compose.yml` | 容器编排配置 |
| `entrypoint.sh` | 容器启动脚本（自动初始化数据库） |
| `.dockerignore` | Docker构建排除文件 |

### Dockerfile 配置说明

```dockerfile
# 基础镜像: Python 3.12
FROM python:3.12-slim

# 工作目录: /app
WORKDIR /app

# 依赖安装
- requirements.txt中的所有Python包
- gcc编译器（用于某些Python包）

# 暴露端口: 8080
EXPOSE 8080

# 启动方式: entrypoint.sh脚本
ENTRYPOINT ["/app/entrypoint.sh"]
```

### docker-compose.yml 配置说明

```yaml
services:
  game:
    # 容器名称
    container_name: adult_game

    # 端口映射: 主机8080 -> 容器8080
    ports:
      - "8080:8080"

    # 环境变量
    environment:
      - FLASK_HOST=0.0.0.0        # 监听所有网络接口
      - FLASK_PORT=8080            # 端口号
      - FLASK_DEBUG=false          # 生产模式
      - SECRET_KEY=...             # 应用密钥

    # 数据持久化: Docker Volume
    volumes:
      - game_data:/app

    # 重启策略: 除非手动停止，否则自动重启
    restart: unless-stopped
```

### entrypoint.sh 启动脚本

功能：
1. 检查数据库文件是否存在
2. 如果不存在，自动运行`migrate_complete.py`初始化数据库
3. 启动Flask应用

## 🚀 快速部署指南

### 步骤1: 克隆项目

```bash
git clone https://github.com/aavjmz/adult_game.git
cd adult_game
```

### 步骤2: 切换到正确分支

```bash
git checkout develop
```

### 步骤3: 构建Docker镜像

```bash
docker compose build
```

预计时间：2-5分钟（取决于网络速度）

### 步骤4: 启动容器

```bash
docker compose up -d
```

参数说明：
- `-d`: 后台运行（detached mode）

### 步骤5: 验证部署

```bash
# 查看容器状态
docker compose ps

# 查看启动日志
docker compose logs -f

# 测试服务
curl http://localhost:8080
```

成功标志：
- 容器状态显示 `Up`
- 日志显示 `Running on http://0.0.0.0:8080`
- curl返回HTTP 200

### 步骤6: 访问游戏

浏览器访问：`http://服务器IP:8080`

## 🎮 首次使用

1. 注册账号
2. 登录游戏
3. 获得初始资源：
   - 10张抽卡券
   - 1000游戏币
4. 开始抽卡、组建队伍、进行战斗

## 🛠️ 管理命令

### 日常运维

```bash
# 启动服务
docker compose start

# 停止服务
docker compose stop

# 重启服务
docker compose restart

# 查看实时日志
docker compose logs -f

# 查看最近100行日志
docker compose logs --tail=100

# 进入容器Shell（调试用）
docker compose exec game bash
```

### 数据备份

```bash
# 备份数据卷
docker run --rm -v adult_game_game_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/game_backup_$(date +%Y%m%d).tar.gz -C /data .

# 恢复数据
docker run --rm -v adult_game_game_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/game_backup_20260206.tar.gz -C /data
```

### 更新部署

```bash
# 拉取最新代码
git pull origin develop

# 重新构建镜像
docker compose build

# 重启服务
docker compose down
docker compose up -d
```

### 清理资源

```bash
# 停止并删除容器（保留数据）
docker compose down

# 停止并删除容器和数据卷（⚠️ 会删除所有游戏数据）
docker compose down -v

# 清理未使用的Docker镜像
docker image prune -a
```

## 🔒 安全配置

### 1. 设置强密钥

生产环境必须修改默认密钥：

```bash
# 生成随机密钥
export SECRET_KEY=$(openssl rand -base64 32)

# 永久保存（添加到~/.bashrc或/etc/environment）
echo "export SECRET_KEY='your-generated-key'" >> ~/.bashrc
source ~/.bashrc

# 重启容器
docker compose restart
```

### 2. 配置防火墙

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 8080/tcp
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

### 3. 使用Nginx反向代理（推荐）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. 启用HTTPS（推荐）

使用Let's Encrypt免费证书：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 📊 监控和日志

### 容器资源使用

```bash
# 实时监控
docker stats adult_game

# 查看容器详细信息
docker inspect adult_game
```

### 应用日志

```bash
# 实时日志（包含Flask输出）
docker compose logs -f game

# 筛选错误日志
docker compose logs game | grep -i error

# 导出日志
docker compose logs game > game.log
```

### 健康检查

配置中已包含健康检查，每30秒检查一次应用状态。

查看健康状态：
```bash
docker compose ps
```

## 🐛 常见问题排查

### 问题1: 容器无法启动

```bash
# 查看详细错误信息
docker compose logs

# 常见原因：
# - 端口8080已被占用 → 修改docker-compose.yml中的端口映射
# - 数据库初始化失败 → 删除数据卷重新初始化
```

### 问题2: 数据库初始化失败

```bash
# 删除数据卷重新初始化
docker compose down -v
docker compose up -d
```

### 问题3: 端口无法访问

```bash
# 检查防火墙
sudo ufw status

# 检查端口监听
ss -tlnp | grep 8080
netstat -tlnp | grep 8080

# 检查Docker网络
docker network ls
docker network inspect adult_game_default
```

### 问题4: 容器频繁重启

```bash
# 查看最近的崩溃日志
docker compose logs --tail=200

# 可能原因：
# - 内存不足
# - 数据库文件损坏
# - Python依赖缺失
```

## 🔄 数据迁移

### 从SQLite迁移到PostgreSQL（可选）

1. 安装PostgreSQL容器：

```yaml
# 在docker-compose.yml中添加
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: game_db
      POSTGRES_USER: game_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

2. 修改环境变量：

```yaml
environment:
  - DATABASE_URL=postgresql://game_user:secure_password@postgres:5432/game_db
```

## 📈 性能优化

### 1. 使用生产级WSGI服务器

修改`entrypoint.sh`，使用Gunicorn：

```bash
# 安装Gunicorn
pip install gunicorn

# 修改启动命令
exec gunicorn -w 4 -b 0.0.0.0:8080 run:app
```

### 2. 启用Redis缓存（可选）

添加Redis服务到docker-compose.yml：

```yaml
services:
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
```

### 3. 配置资源限制

```yaml
services:
  game:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 256M
```

## 📞 支持

- GitHub Issues: https://github.com/aavjmz/adult_game/issues
- 文档: 项目根目录下的README.md

## 📝 更新日志

### 2026-02-06
- ✅ 初始Docker部署配置
- ✅ 自动数据库初始化
- ✅ 数据持久化配置
- ✅ 健康检查配置

## 🎯 下一步计划

- [ ] 集成Nginx反向代理
- [ ] PostgreSQL数据库支持
- [ ] Redis缓存层
- [ ] 容器编排（Kubernetes）
- [ ] CI/CD自动部署
- [ ] 监控告警（Prometheus + Grafana）
