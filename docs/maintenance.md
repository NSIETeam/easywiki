# EasyWiki 维护手册

## 1. 日常巡检

### 1.1 健康检查

```bash
# API 健康状态
curl -s http://localhost:8080/health | python -m json.tool

# 预期输出
{
  "status": "ok",
  "db": "connected",
  "uptime": 86400
}
```

### 1.2 磁盘空间

```bash
# 检查数据库大小
ls -lh ~/.easywiki/easywiki.db

# 检查备份目录
du -sh ~/.easywiki/backups/

# 检查 Docker 卷
docker exec easywiki du -sh /data/
```

### 1.3 进程状态

```bash
# Docker
docker ps | grep easywiki

# PM2
pm2 status easywiki

# systemd
systemctl status easywiki
```

## 2. 数据库维护

### 2.1 自动备份

EasyWiki 每日自动备份，保留 7 天。备份文件位于 `~/.easywiki/backups/easywiki-YYYY-MM-DD.db`。

```bash
# 查看备份列表
ls -lh ~/.easywiki/backups/

# 手动触发备份（Python）
python -c "from orgmind.database_sqlite import get_db; get_db().backup_database(); print('Backup done')"
```

### 2.2 手动备份与恢复

```bash
# 备份
cp ~/.easywiki/easywiki.db ~/.easywiki/easywiki-manual-$(date +%Y%m%d-%H%M%S).db

# 恢复
docker compose down
cp ~/.easywiki/backups/easywiki-2026-07-18.db ~/.easywiki/easywiki.db
docker compose up -d
```

### 2.3 WAL 检查点

```bash
# 手动触发 WAL checkpoint
sqlite3 ~/.easywiki/easywiki.db "PRAGMA wal_checkpoint(TRUNCATE);"

# 查看 WAL 文件大小
ls -lh ~/.easywiki/easywiki.db-wal
```

### 2.4 数据库优化

```bash
# 重建索引
sqlite3 ~/.easywiki/easywiki.db "REINDEX;"

# 分析表统计
sqlite3 ~/.easywiki/easywiki.db "ANALYZE;"

# 查看表大小
sqlite3 ~/.easywiki/easywiki.db "SELECT name, SUM(pgsize) as size FROM dbstat GROUP BY name ORDER BY size DESC LIMIT 10;"
```

### 2.5 FTS5 索引维护

```bash
# 重建全文搜索索引
sqlite3 ~/.easywiki/easywiki.db "INSERT INTO documents_fts(documents_fts) VALUES('rebuild');"

# 查看索引状态
sqlite3 ~/.easywiki/easywiki.db "SELECT count(*) FROM documents_fts;"
```

## 3. 日志管理

### 3.1 日志位置

| 部署方式 | 日志位置 |
|---------|---------|
| Docker | `docker logs easywiki` |
| PM2 | `~/.pm2/logs/easywiki-out.log` |
| systemd | `journalctl -u easywiki` |

### 3.2 关键日志关键词

```bash
# 搜索错误
docker logs easywiki 2>&1 | grep -i "error\|exception\|traceback"

# 搜索数据库问题
docker logs easywiki 2>&1 | grep -i "sqlite\|database\|locked"

# 搜索认证失败
docker logs easywiki 2>&1 | grep -i "auth\|token\|unauthorized"
```

### 3.3 日志轮转

```bash
# Docker（已内置）
# PM2（已内置）

# systemd 配置 /etc/logrotate.d/easywiki
/var/log/easywiki/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

## 4. 性能调优

### 4.1 SQLite 优化

```sql
-- 在数据库中执行
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;  -- 64MB cache
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 268435456;  -- 256MB memory-mapped I/O
```

### 4.2 向量搜索优化

当文档数量超过 5000 条时，考虑：

1. 启用 batch 模式（已内置，500条/批）
2. 定期清理过期记忆：`UPDATE memories SET status='archived' WHERE expires_at < datetime('now')`
3. 降低 `top_k` 参数（默认 20，可改为 10）

### 4.3 前端性能

- 构建产物约 4MB（含代码高亮），建议启用 Nginx gzip
- 图片资源建议走 CDN
- 静态资源缓存 7 天

## 5. 安全加固

### 5.1 密码策略

```bash
# 修改管理员密码（API）
curl -X PUT http://localhost:8080/api/v1/auth/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"old_password":"admin123","new_password":"your-strong-password"}'
```

### 5.2 API 限流

默认 60 次/分钟（Token Bucket）。调整方式：

```python
# 在代码中修改
db.check_rate_limit(key, max_tokens=120, refill_rate=120)  # 120次/分钟
```

### 5.3 审计日志查询

```bash
# 查看最近 100 条操作日志
sqlite3 ~/.easywiki/easywiki.db \
  "SELECT a.created_at, u.name, a.action, a.resource_type, a.resource_id FROM audit_logs a LEFT JOIN users u ON a.user_id = u.id ORDER BY a.created_at DESC LIMIT 100;"
```

### 5.4 XSS 防护

所有富文本输入自动经过 `sanitize_html()` 处理，移除：
- `<script>`, `<iframe>`, `<object>`, `<embed>`, `<link>`, `<style>`, `<meta>`, `<form>` 标签
- 所有 `on*` 事件属性
- `javascript:` 伪协议

## 6. 故障排查

### 6.1 数据库锁定

```
错误: database is locked
```

```bash
# 检查是否有死锁进程
fuser ~/.easywiki/easywiki.db

# 重启服务
docker compose restart easywiki
# 或
pm2 restart easywiki
```

### 6.2 FTS5 不可用

```
错误: no such module: fts5
```

```bash
# 检查 SQLite 是否支持 FTS5
sqlite3 ":memory:" "SELECT fts5_source_id();"

# 如果不支持，安装带 FTS5 的版本
# Ubuntu: apt install sqlite3 (默认支持)
# macOS: brew install sqlite3
# Python: pip install pysqlite3-binary
```

### 6.3 向量模型下载失败

```bash
# 手动下载
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# 如果网络问题，设置镜像
export HF_ENDPOINT=https://hf-mirror.com
```

### 6.4 前端白屏

```bash
# 检查构建产物
ls -la frontend-src/dist/index.html

# 检查 Nginx/Caddy 是否正确代理
curl -I http://localhost:8080/

# 检查浏览器控制台错误（F12）
```

## 7. 监控指标

| 指标 | 命令 | 告警阈值 |
|------|------|---------|
| API 可用性 | `curl -sf http://localhost:8080/health` | 连续 3 次失败 |
| 磁盘使用率 | `df -h` | > 80% |
| 数据库大小 | `du -sh ~/.easywiki/easywiki.db` | > 1GB |
| 内存使用 | `docker stats easywiki` | > 1GB |
| 响应时间 | `curl -o /dev/null -w "%{time_total}" http://localhost:8080/health` | > 2s |
| 备份文件数 | `ls ~/.easywiki/backups/ | wc -l` | < 3 |

## 8. 数据导出

```bash
# 导出全部数据（不含密码哈希）
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/api/v1/org/export | python -m json.tool > export.json

# 导出审计日志
sqlite3 ~/.easywiki/easywiki.db \
  "SELECT * FROM audit_logs ORDER BY created_at DESC;" > audit.csv
```
