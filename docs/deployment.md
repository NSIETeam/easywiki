# EasyWiki 部署手册

## 1. 环境要求

| 组件 | 最低版本 | 推荐版本 |
|------|---------|---------|
| Python | 3.10+ | 3.11+ |
| Node.js | 18+ | 20+ |
| Docker | 24+ | 26+ |
| 磁盘空间 | 1GB | 5GB+（含向量模型） |
| 内存 | 512MB | 2GB+ |

## 2. Docker 一键部署（推荐）

### 2.1 单容器部署

```bash
docker run -d \
  --name easywiki \
  -p 8080:8080 \
  -v easywiki-data:/data \
  -e ORGMIND_ADMIN_PASSWORD=admin123 \
  -e ORGMIND_JWT_SECRET=$(openssl rand -hex 32) \
  -e CORS_ORIGINS="https://wiki.example.com" \
  --restart unless-stopped \
  easywiki/easywiki:latest
```

### 2.2 Docker Compose 部署

```yaml
# docker-compose.yml
services:
  easywiki:
    build: .
    container_name: easywiki
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - easywiki-data:/data
    environment:
      - ORGMIND_DB_PATH=/data/easywiki.db
      - ORGMIND_ADMIN_PASSWORD=admin123
      - ORGMIND_JWT_SECRET=your-secret-key-at-least-16-chars
      - CORS_ORIGINS=https://wiki.example.com
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3

volumes:
  easywiki-data:
```

```bash
docker compose up -d
```

### 2.3 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name wiki.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name wiki.example.com;

    ssl_certificate /etc/letsencrypt/live/wiki.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wiki.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 文件上传大小限制
    client_max_body_size 50m;
}
```

## 3. 源码部署

### 3.1 后端

```bash
git clone https://github.com/NSIETeam/easywiki.git
cd easywiki
pip install -r requirements.txt

# 设置环境变量
export ORGMIND_ADMIN_PASSWORD=admin123
export ORGMIND_JWT_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")

# 启动
python -m uvicorn orgmind.main_sqlite:app --host 0.0.0.0 --port 8080
```

### 3.2 前端构建

```bash
cd frontend-src
npm install
npm run build
# 构建产物在 frontend-src/dist/
```

### 3.3 使用 PM2 守护进程

```bash
npm install -g pm2

pm2 start "python -m uvicorn orgmind.main_sqlite:app --host 0.0.0.0 --port 8080" --name easywiki
pm2 save
pm2 startup
```

## 4. 环境变量说明

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `ORGMIND_DB_PATH` | `~/.easywiki/easywiki.db` | SQLite 数据库文件路径 |
| `ORGMIND_ADMIN_PASSWORD` | 随机生成 | 首次启动的管理员密码 |
| `ORGMIND_JWT_SECRET` | 随机生成（存文件） | JWT 签名密钥，生产环境必须固定 |
| `CORS_ORIGINS` | `localhost:8080,5173,8090` | 允许的跨域来源，逗号分隔 |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | 语义向量模型名称 |

## 5. 首次配置

1. 访问 `http://your-server:8080`
2. 使用 `admin@local` + 设置的密码登录
3. 首次登录后**立即修改密码**
4. 创建部门和项目结构
5. 通过 `seed_templates` 初始化文档模板（3个预置模板）

## 6. HTTPS 配置

### Let's Encrypt + Caddy（推荐）

```Caddyfile
wiki.example.com {
    reverse_proxy 127.0.0.1:8080
    encode zstd gzip
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
    }
}
```

## 7. 升级流程

### Docker

```bash
docker pull easywiki/easywiki:latest
docker compose down
docker compose up -d
```

### 源码

```bash
git pull origin master
pip install -r requirements.txt --upgrade
cd frontend-src && npm run build && cd ..
pm2 restart easywiki
```

> **注意：** 升级前数据库会自动执行 ALTER TABLE 迁移。建议升级前手动备份：`cp ~/.easywiki/easywiki.db ~/.easywiki/easywiki-backup-$(date +%Y%m%d).db`

## 8. 健康检查

```bash
curl http://localhost:8080/health
# 返回: {"status":"ok","db":"connected","uptime":1234}
```

Docker Compose 已内置健康检查，每 30 秒一次。
