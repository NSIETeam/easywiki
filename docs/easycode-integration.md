# EasyWiki × EasyCode 协作指南

## 概述

EasyCode 是 AI 编程助手，EasyWiki 是组织知识管理平台。两者协作形成 **"编码 → 知识沉淀 → 辅助编码"** 闭环：

```
EasyCode 编码/决策 ──→ EasyWiki 自动记录 ──→ 知识检索/复用 ──→ EasyCode 辅助编码
```

## 1. 集成架构

```
┌─────────────┐         ┌─────────────┐
│   EasyCode   │         │  EasyWiki   │
│  (CLI/IDE)   │◄───────►│  (Server)   │
│              │  HTTP   │             │
│  Agent 工作  │  API    │  知识存储    │
│  代码生成    │         │  全文搜索    │
│  代码审查    │         │  知识图谱    │
└─────────────┘         └─────────────┘
      │                        │
      │  决策/Bug/最佳实践      │
      └───────写入────────────►│
                              │
      │  知识检索/上下文        │
      ◄───────查询────────────┤
```

## 2. 配置方式

### 2.1 EasyCode 端配置

在 EasyCode 的项目配置 `.easycode/settings.json` 中添加：

```json
{
  "easywiki": {
    "enabled": true,
    "base_url": "http://your-wiki-server:8080",
    "token": "your-jwt-token",
    "auto_record": true,
    "project_id": "wiki-project-id"
  }
}
```

### 2.2 EasyWiki 端配置

1. 在 EasyWiki 中创建对应项目
2. 创建专用 API 账号（角色: agent）
3. 生成 JWT Token 供 EasyCode 使用
4. 配置 Webhook 接收 EasyCode 事件

## 3. 协作场景

### 3.1 自动决策记录

EasyCode Agent 在编码过程中做出的技术决策，自动写入 EasyWiki 待审核队列：

```
EasyCode: "我决定使用 Redis 做缓存，因为..."
  ↓ auto_record: true
EasyWiki: 收到待审核条目
  ↓ 管理员审核通过
EasyWiki: 正式入库，加入知识图谱
```

**触发条件：**
- 技术选型决策
- 架构方案变更
- Bug 修复方案
- 性能优化策略

### 3.2 知识辅助编码

EasyCode 在编码时查询 EasyWiki 获取团队历史经验：

```python
# EasyCode Hook 示例
def before_code_generation(context):
    # 查询 EasyWiki 相关知识
    results = easywiki.search(context.task_description, top_k=5)
    if results:
        context.add_system_prompt(
            f"团队历史经验参考:\n{format_results(results)}"
        )
```

### 3.3 代码审查知识化

EasyCode 审查代码时，自动关联 EasyWiki 中的规范文档：

```
EasyCode 发现代码问题
  ↓ 查询 EasyWiki: "代码规范" + 当前文件类型
  ↓ 匹配到相关规范文档
EasyCode: "根据团队规范《API 设计规范 v2》，建议..."
```

### 3.4 项目文档同步

EasyCode 的项目结构变更时，自动更新 EasyWiki 中的项目文档：

| EasyCode 事件 | EasyWiki 动作 |
|--------------|--------------|
| 新建模块 | 创建文档页面 |
| 删除文件 | 标记文档为归档 |
| 依赖变更 | 更新技术栈记录 |
| CI/CD 配置变更 | 更新部署流程文档 |

## 4. API 接口

### 4.1 写入知识条目

```bash
curl -X POST http://wiki-server:8080/api/v1/easywiki/projects/{pid}/pending-entries \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "EasyCode",
    "entry_type": "decision",
    "raw_content": "决定使用 WebSocket 替代轮询，原因：实时性要求高，服务端推送效率更好",
    "metadata": {"file": "src/realtime/handler.ts", "commit": "abc123"}
  }'
```

### 4.2 搜索知识

```bash
curl -X POST http://wiki-server:8080/api/v1/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "缓存方案 Redis",
    "top_k": 5,
    "mode": "hybrid"
  }'
```

### 4.3 获取知识图谱

```bash
curl http://wiki-server:8080/api/v1/easywiki/projects/{pid}/graph \
  -H "Authorization: Bearer $TOKEN"
```

### 4.4 审计日志查询

```bash
curl "http://wiki-server:8080/api/v1/audit-logs?limit=50" \
  -H "Authorization: Bearer $TOKEN"
```

## 5. Hooks 集成

### 5.1 EasyCode Hook 配置

在 `.easycode/hooks.json` 中配置：

```json
{
  "hooks": [
    {
      "event": "task_complete",
      "action": "easywiki_record",
      "config": {
        "entry_type": "auto",
        "project_id": "wiki-project-id"
      }
    },
    {
      "event": "before_code_gen",
      "action": "easywiki_search",
      "config": {
        "top_k": 5,
        "inject_context": true
      }
    }
  ]
}
```

### 5.2 Hook 执行流程

```
1. EasyCode 完成任务
2. Hook 触发 → 提取决策内容
3. 调用 EasyWiki API 写入 pending-entries
4. EasyWiki 管理员收到通知（Webhook）
5. 审核通过 → 正式入库
```

## 6. 数据流

```
EasyCode 工作会话
    │
    ├── 技术决策 ──────► EasyWiki pending-entries (entry_type: decision)
    ├── Bug 修复 ──────► EasyWiki pending-entries (entry_type: bug_fix)
    ├── 最佳实践 ──────► EasyWiki pending-entries (entry_type: best_practice)
    ├── 架构变更 ──────► EasyWiki pending-entries (entry_type: architecture)
    │
    ├── 编码前 ────────► EasyWiki search (获取历史经验)
    ├── 审查时 ────────► EasyWiki search (关联规范文档)
    │
    └── 项目变更 ──────► EasyWiki documents (同步更新)
```

## 7. 权限模型

| 角色 | EasyCode 权限 | EasyWiki 权限 |
|------|-------------|--------------|
| admin | 全部 | 全部 + 管理 |
| agent | 写入 pending-entries, 搜索 | 写入, 搜索 |
| member | 搜索, 读取 | 读取, 搜索 |
| viewer | 无 | 只读 |

## 8. 最佳实践

### 8.1 项目映射

- 一个 EasyCode 项目对应一个 EasyWiki 项目
- EasyCode 的 git 仓库 URL 作为 EasyWiki 项目的 `external_id`
- 分支映射到 EasyWiki 的版本快照

### 8.2 知识质量

- EasyCode 自动记录的条目必须经人工审核
- 设置 PII 检测，自动升级敏感条目的访问级别
- 定期清理过期/低质量条目（quality_score < 0.3）

### 8.3 性能建议

- 搜索 top_k 不超过 10
- 批量写入时每批不超过 50 条
- Webhook 超时设为 5 秒，失败静默
- 向量搜索在 5000+ 文档时考虑分批模式

### 8.4 安全建议

- EasyCode 和 EasyWiki 之间的通信走 HTTPS
- JWT Token 定期轮换（建议 7 天）
- Agent 账号使用最小权限（只写 pending-entries + 搜索）
- 审计日志保留至少 90 天
