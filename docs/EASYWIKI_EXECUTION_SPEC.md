# EasyWiki 执行规格文档 v1.0（面向实现，强约束版）

> **本文档目的**：防止执行模型（含 DeepSeek 等）在实现阶段自由发挥导致界面乱设计、后端接口乱定义、目标跑偏。本文档是**强制规格**，产品意图/为什么这样设计见 `EASYWIKI_PRODUCT_DESIGN.md`（只读，不可改），**本文档回答"具体怎么做"，精确到文件路径/函数签名/API协议/表结构**，执行时必须逐条对照，不允许自由替换技术方案、不允许自创未在此列出的接口或表结构。
>
> **执行前必读第0节的"现状纠偏"**——这是对 v1.0 产品文档中若干"复用假设"的更正，基于对现有代码的逐文件实读核实，比产品文档更准确，如有冲突以本文档技术判断为准。

---

## 0. 现状纠偏（务必先读，否则会接错代码）

### 0.1 唯一真实运行的后端是 `orgmind/main_sqlite.py`

Windows 桌面应用（`orgmind/desktop_shell.py` pywebview壳 → 启动 uvicorn跑 `orgmind.main_sqlite:app`）实际运行的是**这一套且只有这一套**：
- 函数式 FastAPI 路由（不是 APIRouter 拆分），全部写在 `main_sqlite.py` 一个文件里（612行）。
- 数据库是 `orgmind/database_sqlite.py` 里的 `OrgMindDB` 单例类，纯 `sqlite3` 标准库，线程本地连接，手写SQL（不是SQLAlchemy ORM）。
- 鉴权是 `_get_user_from_token(authorization)` 从 `Authorization: Bearer <jwt>` 里手动 decode JWT，不是 FastAPI Depends 注入。
- 写操作一律经过 `orgmind/services/write_queue.py` 的 `execute_write(fn, *args)` 串行化，防止 SQLite 写锁冲突。

### 0.2 以下模块是"未接线的孤立代码"，EasyWiki 开发**禁止依赖**它们

| 文件 | 为什么不能用 |
|---|---|
| `orgmind/models/*.py`（Memory/Document/Artifact等 SQLAlchemy ORM） | 需要 Postgres + pgvector，桌面SQLite环境没有这些依赖，且从未被 `main_sqlite.py` import |
| `orgmind/api/routes.py` | 同上，是给 SQLAlchemy/Postgres 体系用的 APIRouter，`main_sqlite.py` 里没有 `include_router` 引用它 |
| `orgmind/graph/engine.py` `graph/extractor.py` | 依赖 `kuzu` 包，桌面环境未安装，从未被调用 |
| `orgmind/skills/engine.py` | 依赖 Redis + SQLAlchemy async，从未被调用 |
| `orgmind/agents/registry.py` | 依赖 SQLAlchemy async，从未被调用；`main_sqlite.py` 里的 `agent_invoke` 是完全独立的简化实现（直接查 `artifacts` 表） |
| `orgmind/retrieval/*.py` | 同样是 SQLAlchemy async 体系，`main_sqlite.py` 的检索逻辑是自己内联写的（`db.vector_search` + `db.fts_search` 混合） |

**结论**：EasyWiki 的知识图谱、Skill三层加载、Agent注册这些能力，**现状是零**，需要在 SQLite 体系上从零构建简化版，不是"接线复用"。执行时按本文档第5、6节的简化规格实现，不要去 import 上述孤立模块。

### 0.3 真正可信复用的模块（EasyWiki 必须直接调用，不允许重写）

| 模块 | 提供的函数 | 用法 |
|---|---|---|
| `orgmind.governance.cleaners` | `clean_text(text) -> (cleaned, meta)` | 所有写入文本前必须调用 |
| `orgmind.governance.pii` | `detect_pii(text) -> list[str]`, `upgrade_sensitivity(current, hits) -> str` | 所有 agent 提报内容必须过 PII 检测 |
| `orgmind.governance.quality` | `compute_quality_score(QualityInput(...)) -> float` | Inbox 排序用 |
| `orgmind.governance.dedup` | `compute_content_hash(text) -> str`（NFKC+SHA256，同步纯函数，可直接用；**不要用**该模块里的 `check_memory_duplicate`，那个是async SQLAlchemy版，改用 `main_sqlite.py` 风格的手写SQL哈希查重） | 去重 |
| `orgmind.services.embedding` | `get_embedding_sync(text) -> List[float]` | 生成向量，写入时序列化为JSON字符串存入SQLite TEXT列（照抄 `main_sqlite.py` 现有模式：`json.dumps(get_embedding_sync(cleaned))`） |
| `orgmind.services.audit` | `log_audit(user_id, action, resource_type, resource_id, details=None)` | 所有新增的写操作/审批操作必须记审计日志 |
| `orgmind.services.write_queue` | `execute_write(fn, *args, **kwargs)` | 所有 SQLite 写操作必须包一层 |
| `orgmind.services.auto_memory` | `extract_memories_from_session(text) -> List[Dict]` | 会话结束压缩汇总时调用（LLM优先/正则降级） |
| `orgmind.agent_detector` | `detect_agents() -> List[Dict]` | 检测本机已安装的 agent 工具，第6.5节的"一键同步配置"要用这个的检测结果 |

### 0.4 前端现状

`frontend/dist/` 只有编译产物（`index.html`/`assets/`），仓库里**没有找到任何前端源码**（无 `src/`、无 `package.json` 描述前端构建）。种子数据里记录的历史技术决策是：**React + TypeScript + Tailwind CSS，单色蓝主题，13px基础字号，间距用4px倍数**（见 `main_sqlite.py` 的 `_auto_setup` demo memory）。EasyWiki 前端必须新建源码工程，并遵守这个既有视觉规范（第7节强制细化）。

### 0.5 桌面打包路径

只用 `orgmind/desktop_shell.py`（pywebview壳）+ PyInstaller onedir，这是 `docs/PLAN_A_WINDOWS_APP.md` 明确的方向。**`electron/` 目录禁止修改或使用**，该文档原文写明"已废弃的路线，不用管"。

---

## 1. 技术栈锁定（不允许替换）

| 层 | 技术 | 版本/说明 |
|---|---|---|
| 后端语言 | Python 3.10 | 与现有环境一致 |
| 后端框架 | FastAPI（函数式路由，追加到 `main_sqlite.py` 或新建 `orgmind/easywiki_routes.py` 并在 `main_sqlite.py` 里 `app.include_router` 引入，见2.1节） | 沿用现有风格 |
| 数据库 | SQLite（`orgmind/database_sqlite.py` 的 `OrgMindDB` 单例），追加表结构，不新建数据库文件 | 禁止引入 Postgres/SQLAlchemy |
| 鉴权 | 沿用现有 JWT（`_get_user_from_token`），不新增认证体系 | |
| 编辑器/白板 UI 引擎 | **BlockSuite**（`@blocksuite/blocks` + `@blocksuite/store` + `@blocksuite/presets`，MIT许可） | 只用其编辑器/白板 Web Components，不引入 AFFiNE 的 `@affine/*` 包，不使用 AFFiNE 的账号/同步后端 |
| 前端框架 | React 18 + TypeScript + Vite | Vite构建输出到 `frontend/dist`（与现有 `main_sqlite.py` 的 `StaticFiles` 挂载点一致，不改挂载逻辑） |
| 样式 | Tailwind CSS，单色蓝主题，13px基础字号，4px倍数间距（沿用现有决策，见0.4节） | 禁止引入 Ant Design/MUI 等整套组件库改变视觉体系 |
| MCP Server | Python `mcp` 官方SDK（`pip install mcp`），stdio transport | 详见第6节 |
| 图谱（简化版） | 不引入 kuzu，用 SQLite 表 `graph_entities` + `graph_relations` 存储，纯SQL查询（第5.4节） | |

---

## 2. 目录与文件结构（新增文件精确路径）

```
OrgMind/
├── orgmind/
│   ├── main_sqlite.py                      # 追加: app.include_router(easywiki_router)
│   ├── database_sqlite.py                  # 追加: _init_schema() 里加第4节的新表
│   ├── easywiki/                           # 新建目录，EasyWiki 后端全部新代码放这里
│   │   ├── __init__.py
│   │   ├── routes.py                       # 新增 FastAPI 路由（第3节全部端点）
│   │   ├── pending_entry.py                # PendingEntry 落库前处理管线（第3.3节）
│   │   ├── version_diff.py                 # 版本/三方合并算法（第3.5节）
│   │   ├── graph_lite.py                   # 简化版图谱抽取/查询（第5.4节，纯规则，不用kuzu）
│   │   ├── manifest_writer.py              # 生成 EASYWIKI.md + manifest.json（第6.2节）
│   │   └── mcp_config_sync.py              # 检测并写入4个agent工具的MCP配置（第6.5节）
│   └── mcp_server/                         # 新建，独立可执行的MCP Server
│       ├── __init__.py
│       └── server.py                       # 第6.3节，暴露6个MCP工具
├── frontend-src/                           # 新建，前端源码工程（现有frontend/只有dist，无源码）
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── pages/
│       │   ├── ProjectList.tsx             # 全部项目（落地页）
│       │   ├── ProjectWorkspace.tsx        # 项目内七栏位容器
│       │   ├── OrgKnowledgeBase.tsx
│       │   ├── AgentActivityCenter.tsx
│       │   └── Settings.tsx
│       ├── sections/                       # 项目内七个固定栏位组件（第7.2节）
│       │   ├── Overview.tsx
│       │   ├── DecisionsExperience.tsx
│       │   ├── KnowledgeGraphView.tsx
│       │   ├── AgentsSkills.tsx
│       │   ├── Files.tsx
│       │   ├── ProgressSyncTable.tsx
│       │   └── AgentInbox.tsx
│       ├── editor/
│       │   └── BlockSuiteEditor.tsx        # BlockSuite 封装组件，第7.3节
│       └── api/
│           └── client.ts                   # fetch封装，统一带JWT header
└── docs/
    ├── EASYWIKI_PRODUCT_DESIGN.md          # 只读，不可改
    └── EASYWIKI_EXECUTION_SPEC.md          # 本文档
```

**禁止事项**：不允许把新代码直接堆进 `main_sqlite.py`（612行已经很长），必须放到 `orgmind/easywiki/` 子模块，`main_sqlite.py` 里只做一行 `include_router` 引入。不允许新建除上述列出以外的顶层目录。

---

## 3. 后端 API 规格（精确到请求/响应 JSON，禁止自创字段名）

统一前缀 `/api/v1/easywiki`。全部端点鉴权方式与现有一致：`Authorization: Bearer <jwt>` header，内部调用 `_get_user_from_token`（从 `main_sqlite.py` import，不要重新实现一套）。

### 3.1 Project 与栏位

```
GET  /api/v1/easywiki/projects
  → { "projects": [ { "id", "name", "health": "on_track|at_risk|blocked", "created_at" } ] }

POST /api/v1/easywiki/projects
  body: { "name": string }
  → { "id": string, "name": string }

GET  /api/v1/easywiki/projects/{project_id}/manifest
  → {
      "project_id": string,
      "sections": ["overview","decisions_experience","knowledge_graph","agents_skills","files","progress_table","agent_inbox"],
      "progress_fields": [ { "field_name": string, "field_type": "text|select|number|date" } ]
    }
  # 注意: sections 固定7个，硬编码在代码里返回，不做可配置（对应产品文档5.1节"固定栏位不可增删"的决策）
```

### 3.2 Page（栏位内自由页面树，BlockSuite文档载体）

```
GET  /api/v1/easywiki/projects/{project_id}/sections/{section}/pages
  → { "pages": [ { "id", "title", "parent_page_id", "order", "is_clone_of": string|null } ] }

POST /api/v1/easywiki/projects/{project_id}/sections/{section}/pages
  body: { "title": string, "parent_page_id": string|null }
  → { "id": string }

GET  /api/v1/easywiki/pages/{page_id}
  → { "id", "title", "blocksuite_doc": object, "current_version_id": string }
  # blocksuite_doc 字段: 直接存储 BlockSuite 的 Y.Doc 序列化产物 (Uint8Array -> base64字符串)，不要设计自己的富文本schema

PUT  /api/v1/easywiki/pages/{page_id}
  body: { "blocksuite_doc": string(base64), "based_on_version": string }
  → 走第3.5节的版本/冲突逻辑，可能返回 200 (直接应用) 或 409 (冲突，body里带ConflictCase)

POST /api/v1/easywiki/pages/{page_id}/clone-mount
  body: { "target_project_id": string, "target_section": string }
  → { "cloned_page_id": string }
  # 对应产品文档5.1节"克隆挂载"：cloned_page_id 与源page共享同一个 content_ref，物理内容表见4.3节
```

### 3.3 Agent 提报与审核（Agent Inbox 核心）

```
POST /api/v1/easywiki/pending-entries
  # 供 MCP Server 内部调用（不对agent直接暴露HTTP，agent只走MCP工具，MCP Server再转调此REST端点）
  body: {
    "session_id": string, "project_id": string, "tool_name": "claude-code|codex|workbuddy|easycode",
    "entry_type": "decision|bug_fix|best_practice|architecture|progress_update|session_summary",
    "target_section": "decisions_experience|progress_table|files",
    "content": string, "file_refs": [string], "confidence": float,
    "based_on_version": string|null
  }
  → { "id": string, "status": "pending", "quality_score": float, "dedup_hint": "none|near_duplicate|exact", "pii_flag": bool }
  # 内部处理顺序严格按 clean_text → detect_pii → 哈希查重(仿main_sqlite.py现有模式) → compute_quality_score
  # 绝对不允许出现自动发布路径：无论confidence/quality_score多高，status永远是"pending"，不允许直接写入正式表

GET  /api/v1/easywiki/projects/{project_id}/pending-entries?status=pending
  → { "entries": [ { 同上字段 + "id", "created_at" } ] }

POST /api/v1/easywiki/pending-entries/{id}/approve
  body: { "edited_content": string|null }  # 非null表示"编辑后批准"
  → { "id": string, "status": "approved", "written_to": {"type": "memory|progress_field", "id": string} }
  # 批准后写入正式表(4.2节 easywiki_memories 或 4.4节 progress_fields)，并调用 log_audit

POST /api/v1/easywiki/pending-entries/{id}/reject
  body: { "reason": string }
  → { "id": string, "status": "rejected" }

POST /api/v1/easywiki/pending-entries/batch-approve
  body: { "ids": [string] }
  → { "approved": [string], "failed": [{"id": string, "reason": string}] }
```

### 3.4 冲突裁决

```
GET  /api/v1/easywiki/conflicts?status=open
  → { "conflicts": [ { "id", "target_type", "target_id", "base_version_id", "human_version_id", "agent_version_id", "escalated_to_user_id", "created_at" } ] }

POST /api/v1/easywiki/conflicts/{id}/resolve
  body: { "resolution": "keep_human|keep_agent|manual_merge", "merged_content": string|null, "note": string }
  → { "id": string, "status": "resolved" }
```

### 3.5 版本历史

```
GET  /api/v1/easywiki/versions?target_type=page&target_id={id}
  → { "versions": [ { "id", "author_type": "human|agent", "author_ref", "created_at", "diff_summary" } ] }
```

**三方合并算法规格（`easywiki/version_diff.py`，必须实现，不允许简化为"后写覆盖前写"）**：
1. 输入 `base_content`（based_on_version对应的内容）、`current_content`（当前最新版本）、`proposed_content`（agent提报内容）。
2. 对于 Page（BlockSuite文档）：以 block 为最小单元做diff（BlockSuite文档本身是block数组，逐block比较id+内容）。`current`相对`base`改动的block集合 = setA；`proposed`相对`base`改动的block集合 = setB。若 `setA ∩ setB == ∅` → 自动合并（取 setA 和 setB 各自的改动叠加到 base 上）。若有交集 → 生成 ConflictCase，交集部分的block在UI并排展示两个版本。
3. 对于 ProgressField（单值字段）：`current == base` 视为无冲突直接应用；`current != base` 且 `current == proposed` 视为无冲突（内容一致）；否则一律视为冲突（字段是原子值，没有"不重叠"的中间状态），生成 ConflictCase。
4. 冲突升级路由规则：查询 `project_id` 对应的负责人（`users`表里 role='manager' 且 department_id 匹配该项目所属部门）；若找不到明确负责人或冲突的 `target_type` 涉及组织知识库（`scope='org'`），路由给 `role='admin'` 的用户。

---

## 4. 数据库表结构（追加到 `database_sqlite.py` 的 `_init_schema()`，SQL照抄，不允许改字段名/类型）

```sql
CREATE TABLE IF NOT EXISTS easywiki_projects (
    id TEXT PRIMARY KEY, org_id TEXT NOT NULL, name TEXT NOT NULL,
    health TEXT DEFAULT 'on_track', department_id TEXT,
    created_by TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS easywiki_pages (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, section TEXT NOT NULL,
    title TEXT NOT NULL, parent_page_id TEXT, sort_order INTEGER DEFAULT 0,
    content_ref TEXT NOT NULL,   -- 指向 easywiki_page_contents.id，克隆挂载时多个page共享同一content_ref
    created_by TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS easywiki_page_contents (
    id TEXT PRIMARY KEY,
    blocksuite_doc TEXT NOT NULL,       -- base64编码的BlockSuite Y.Doc二进制
    current_version_id TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS easywiki_pending_entries (
    id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT NOT NULL,
    session_id TEXT, tool_name TEXT NOT NULL, entry_type TEXT NOT NULL,
    target_section TEXT NOT NULL, raw_content TEXT NOT NULL,
    file_refs TEXT DEFAULT '[]', confidence REAL DEFAULT 0.5,
    based_on_version TEXT, quality_score REAL, dedup_hint TEXT DEFAULT 'none',
    pii_flag INTEGER DEFAULT 0, status TEXT DEFAULT 'pending',
    reject_reason TEXT, created_at TEXT DEFAULT (datetime('now')),
    resolved_at TEXT, resolved_by TEXT
);

CREATE TABLE IF NOT EXISTS easywiki_memories (
    -- 决策/经验记录正式表，字段对齐现有 memories 表风格，不要合并进 memories 表（避免与已有demo数据/RLS逻辑混淆）
    id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT NOT NULL,
    type TEXT NOT NULL,  -- decision|bug_fix|best_practice|architecture
    content TEXT NOT NULL, content_hash TEXT NOT NULL, embedding TEXT,
    sensitivity TEXT DEFAULT 'normal', quality_score REAL,
    author_type TEXT NOT NULL,  -- human|agent
    author_ref TEXT,            -- human: user_id; agent: tool_name+session_id
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS easywiki_progress_fields (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL,
    field_name TEXT NOT NULL, field_type TEXT DEFAULT 'text',
    current_value TEXT, current_version_id TEXT,
    UNIQUE(project_id, field_name)
);

CREATE TABLE IF NOT EXISTS easywiki_versions (
    id TEXT PRIMARY KEY, target_type TEXT NOT NULL,  -- page|progress_field
    target_id TEXT NOT NULL, author_type TEXT NOT NULL, author_ref TEXT,
    content_snapshot TEXT NOT NULL, based_on_version TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS easywiki_conflicts (
    id TEXT PRIMARY KEY, target_type TEXT NOT NULL, target_id TEXT NOT NULL,
    base_version_id TEXT, human_version_id TEXT, agent_version_id TEXT,
    escalated_to_user_id TEXT, status TEXT DEFAULT 'open',
    resolution TEXT, resolved_note TEXT, resolved_by TEXT, resolved_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS easywiki_graph_entities (
    id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT,
    name TEXT NOT NULL, entity_type TEXT NOT NULL,
    UNIQUE(org_id, name, entity_type)
);

CREATE TABLE IF NOT EXISTS easywiki_graph_relations (
    id TEXT PRIMARY KEY, from_entity_id TEXT NOT NULL, to_entity_id TEXT NOT NULL,
    relation TEXT NOT NULL, source_id TEXT
);

CREATE TABLE IF NOT EXISTS easywiki_agent_configs (
    project_id TEXT PRIMARY KEY,
    manifest_json TEXT NOT NULL,       -- 对应 .easywiki/manifest.json 内容
    enabled_tools TEXT DEFAULT '[]',   -- ["claude-code","easycode",...]
    updated_at TEXT DEFAULT (datetime('now'))
);
```

---

## 5. 简化版能力实现规格（替代第0.2节孤立模块）

### 5.1 去重（不用 `governance/dedup.py` 的async版）
照抄 `main_sqlite.py` 的既有模式：`compute_content_hash(cleaned)` 算哈希 → `SELECT id FROM easywiki_memories WHERE org_id=? AND content_hash=?` 精确匹配 → 若无匹配再用 embedding 做 numpy 余弦相似度（照抄 `database_sqlite.py` 的 `vector_search` 手写numpy逻辑，不引入新库）。

### 5.2 Skill/Agent 复用
**不做三层渐进加载引擎**。直接复用现有 `artifacts` 表（已存在于 `database_sqlite.py`），MCP 的 `search_knowledge` 工具里如果查询意图匹配到 skill/agent，直接 `SELECT * FROM artifacts WHERE org_id=? AND status='published' ORDER BY usage_count DESC`，与 `main_sqlite.py` 现有的 `/api/v1/skill/match` 逻辑一致，不要重新设计。

### 5.3 检索（供 MCP `search_knowledge` 使用）
直接复用 `main_sqlite.py` 里 `/api/v1/retrieve` 端点内联的向量+FTS5混合逻辑（`db.vector_search` + `db.fts_search`），扩展查询范围到 `easywiki_memories` 表（在现有基础上加一个UNION查询），不要重新发明检索算法。

### 5.4 知识图谱（简化版，`easywiki/graph_lite.py`）
不使用kuzu，规则抽取参考 `graph/extractor.py` 的**正则思路**（但独立重写为同步函数，不import该文件）：
- 手机号/邮箱 → Person（脱敏存储）
- "决定/采用/确认"+短语 → Decision
- "XX项目/系统/平台" → Project
抽取结果直接 `INSERT OR IGNORE INTO easywiki_graph_entities` + `easywiki_graph_relations`，查询走纯SQL join，不做复杂图算法（1-2跳查询即可）。

---

## 6. Agent Bridge / MCP 规格（核心模块，精确定义，不允许自创工具名/参数名）

### 6.1 EASYWIKI.md 模板（`easywiki/manifest_writer.py` 生成，写入用户选择的项目根目录）

```markdown
# EasyWiki 已接入本项目

本项目已连接 EasyWiki 知识库（project_id: {project_id}）。

## 你可以使用的工具（通过 MCP）
- `easywiki.search_knowledge` — 开始任务前，先搜索是否有相关的历史决策/最佳实践/踩坑记录
- `easywiki.get_project_manifest` — 获取本项目的栏位结构
- `easywiki.propose_entry` — 完成一个关键动作（决策/修复bug/确定架构）后，提报一条记录
- `easywiki.propose_session_summary` — 会话/任务结束时，提报压缩后的过程摘要（不是原始对话记录，是结构化摘要）
- `easywiki.propose_progress_update` — 任务状态变化时，提报进度表建议更新
- `easywiki.get_pending_status` — 查询你之前的提报是否已被人工确认

## 重要行为准则
1. 所有 propose_* 调用**不会立即生效**，会进入人工审核队列（Agent Inbox），必须等待人工批准才正式写入知识库。
2. 提报内容要精炼、结构化，避免把原始对话/代码贴进去，只提炼"发生了什么/决定了什么/为什么"。
3. 每次开始新任务前，优先调用 search_knowledge 查是否有人已经踩过同样的坑。
```

### 6.2 manifest.json 模板（同目录 `.easywiki/manifest.json`）

```json
{
  "project_id": "{project_id}",
  "org_id": "{org_id}",
  "mcp_stdio_command": "python -m orgmind.mcp_server.server",
  "mcp_working_dir": "{easywiki桌面应用安装目录}",
  "write_scopes": ["decision", "bug_fix", "best_practice", "architecture", "progress_update", "session_summary"]
}
```

### 6.3 MCP Server 工具定义（`orgmind/mcp_server/server.py`，用官方 `mcp` Python SDK，stdio transport）

必须**恰好实现这6个工具**，工具名/参数名/返回结构不允许更改（这是与前端Agent Inbox展示、REST端点强绑定的契约）：

```python
# 伪代码级规格，实现时用 mcp.server.Server + @server.list_tools() / @server.call_tool()

TOOLS = {
    "search_knowledge": {
        "input": {"query": "string", "project_id": "string", "top_k": "integer (default 5)"},
        "calls": "POST http://127.0.0.1:8080/api/v1/retrieve (复用现有端点，见5.3节)",
    },
    "get_project_manifest": {
        "input": {"project_id": "string"},
        "calls": "GET /api/v1/easywiki/projects/{project_id}/manifest",
    },
    "propose_entry": {
        "input": {
            "project_id": "string", "session_id": "string", "tool_name": "string",
            "entry_type": "decision|bug_fix|best_practice|architecture",
            "target_section": "string", "content": "string",
            "file_refs": "array[string] (optional)", "confidence": "number 0-1",
        },
        "calls": "POST /api/v1/easywiki/pending-entries",
    },
    "propose_session_summary": {
        "input": {"project_id": "string", "session_id": "string", "tool_name": "string", "session_text": "string"},
        "behavior": "内部先调用 orgmind.services.auto_memory.extract_memories_from_session(session_text) 得到多条结构化条目，每条分别调用 POST /api/v1/easywiki/pending-entries，entry_type固定用抽取结果的type，不新增session_summary专属entry_type存储（简化：拆解成多条decision/bug_fix/best_practice/architecture条目落库，Inbox展示时按session_id分组即可满足'清单式展开'需求，不需要额外的数据结构）",
    },
    "propose_progress_update": {
        "input": {"project_id": "string", "session_id": "string", "tool_name": "string", "field_name": "string", "suggested_value": "string"},
        "calls": "POST /api/v1/easywiki/pending-entries with entry_type=progress_update, target_section=progress_table, content=JSON.stringify({field_name, suggested_value})",
    },
    "get_pending_status": {
        "input": {"entry_id": "string"},
        "calls": "GET /api/v1/easywiki/pending-entries/{entry_id} (需新增此单条查询端点，返回status字段)",
    },
}
```

**禁止**：不允许给这6个工具改名、加前缀（比如不能变成`easywiki_search_knowledge`下划线风格或反过来），产品文档6.2节写的是点号风格`easywiki.search_knowledge`，MCP SDK注册时工具名本身不带命名空间点号（MCP协议工具名通常是flat string），实现时工具名直接用 `search_knowledge`、`propose_entry` 等（不带`easywiki.`前缀），前缀只在产品文档里是示意，MCP Server本身的server name注册为`easywiki`即可提供命名空间语境，避免因为死抠文档里的点号写法导致MCP SDK注册报错。

### 6.4 MCP Server 进程管理
MCP Server 必须能被 Codex CLI 以 **本地 subprocess** 方式启动（这是0.5节强调的限制），因此 `manifest.json` 里的 `mcp_stdio_command` 必须是一条可以被各工具的MCP配置文件直接引用的命令行，不要设计成"必须先手动启动一个常驻daemon再连接"的模式——每个 agent 工具自己按需 spawn 这个 Python 进程即可（MCP stdio 协议本身就是按需spawn的设计），不要额外造一个"EasyWiki daemon"概念。

### 6.5 配置自动同步（`easywiki/mcp_config_sync.py`）

调用现有 `orgmind.agent_detector.detect_agents()` 拿到本机已装工具列表，针对检测到的每个工具写入/更新对应配置文件：

| 工具 | 配置文件路径 | 写入方式 |
|---|---|---|
| Claude Code | 项目根目录 `.claude/mcp.json`（或 `.mcp.json`，需在实现时查阅 Claude Code 当前版本实际读取的文件名，不要凭猜测硬编码） | 合并写入（读取已有JSON，合并`mcpServers.easywiki`键，不覆盖用户已有的其他MCP配置） |
| Codex CLI | `~/.codex/config.toml` | TOML格式，追加`[mcp_servers.easywiki]`段，同样要合并不覆盖 |
| WorkBuddy | 项目或全局 `mcp.json`（具体路径需查阅WorkBuddy文档确认，不要凭猜测硬编码） | 合并写入 |
| Easy Code | 其MCP设置文件（具体路径需查阅确认） | 合并写入 |

**强制要求**：所有写入都必须先读取已有文件（若存在）、解析、合并键、再写回，**禁止直接整体覆盖**用户可能已有的其他MCP服务器配置。

---

## 7. 前端规格（精确到组件树与视觉规范，禁止自由设计风格）

### 7.1 强制视觉规范（沿用项目既有决策，见0.4节，不允许更改）
- 主色：单色蓝主题（一个主蓝色 + 灰阶，不引入多彩配色方案）
- 基础字号：13px
- 间距：4px的整数倍（4/8/12/16/20...）
- Tailwind CSS，不引入 Ant Design/MUI/Chakra 等会自带一套视觉语言的组件库

### 7.2 页面与栏位（对应产品文档5.2节导航结构，7个固定栏位顺序不可变）
`ProjectWorkspace.tsx` 内部用 Tab 或左侧二级导航渲染固定顺序：概览 → 决策与经验 → 知识图谱 → Agent与Skill → 文件 → 进度表 → Agent Inbox。**不允许**做成可拖拽排序/可增删的动态栏位（产品文档5.1节已明确决策：固定骨架，不可配置）。

### 7.3 BlockSuite 集成规格
`editor/BlockSuiteEditor.tsx` 封装：
- 用 `@blocksuite/presets` 的 `AffineEditorContainer`（或对应版本的编辑器容器组件，需查阅当时BlockSuite版本的实际导出API，不要凭旧版本记忆硬编码）初始化编辑器。
- 文档持久化：编辑器内容变化时序列化 Y.Doc 为二进制，base64编码后 PUT 到 `/api/v1/easywiki/pages/{page_id}`（对应3.2节）；打开页面时反向：GET拿到base64，反序列化载入编辑器。
- **不接入 BlockSuite/Yjs 的实时协同provider（不要连WebSocket同步服务）**——本产品的"多人协同"不通过CRDT实时同步实现，而是通过"保存时提交版本+冲突检测"（第3.5节）实现，这是产品文档13节明确写的架构决策，避免引入AFFiNE式复杂同步后端。

### 7.4 Agent Inbox 页面（`sections/AgentInbox.tsx`）
必须包含：条目列表（来源工具图标+entry_type标签+内容摘要+质量/去重提示角标）、单条"批准/编辑后批准/驳回"三个操作按钮、多选批量批准checkbox、冲突条目特殊样式（红色/橙色角标区分普通pending和冲突态）。这是产品文档6.5节的具体落地，不允许简化成"只有批准/驳回两个按钮"（缺少"编辑后批准"会破坏产品设计的核心治理原则）。

---

## 8. 禁止事项清单（红线，违反即视为跑偏）

1. ❌ 不允许整体引入 AFFiNE 的 `@affine/*` npm 包或其账号/同步后端。
2. ❌ 不允许 import `orgmind.models.*`、`orgmind.api.routes`、`orgmind.graph.*`、`orgmind.skills.engine`、`orgmind.agents.registry`、`orgmind.retrieval.*`（第0.2节列出的孤立模块）。
3. ❌ 不允许引入 Postgres/pgvector/Redis/SQLAlchemy 作为新依赖（现阶段桌面版是纯SQLite）。
4. ❌ 不允许修改 `electron/` 目录下任何文件。
5. ❌ 不允许设计任何"agent提报内容达到某阈值自动发布"的逻辑，`easywiki_pending_entries.status` 只能由人工审核端点（3.3节）改变，不能有后台任务自动把 pending 改成 approved。
6. ❌ 不允许把7个固定栏位做成用户可自定义增删的结构。
7. ❌ 不允许接入 BlockSuite/Yjs 的实时协同 WebSocket provider。
8. ❌ 不允许更改现有 `main_sqlite.py` 里已存在的路由/表结构（`memories`/`users`/`departments`/`artifacts`等），EasyWiki新表用`easywiki_`前缀，与现有表完全独立，避免污染现有已跑通的功能。
9. ❌ 不允许自创视觉风格（多彩配色、非13px基础字号、非4px间距倍数、引入完整UI组件库）。
10. ❌ 不允许给MCP工具改名/加前缀（工具名严格按6.3节：`search_knowledge`、`get_project_manifest`、`propose_entry`、`propose_session_summary`、`propose_progress_update`、`get_pending_status`）。
11. ❌ 不允许把 `.claude/mcp.json` 等第三方工具配置文件做整体覆盖写入，必须合并已有键。

---

## 9. 分阶段任务清单（每阶段有明确验收标准，按顺序执行）

### 阶段1：后端骨架
- [ ] 在 `database_sqlite.py` 追加第4节全部表结构
- [ ] 新建 `orgmind/easywiki/` 模块，实现 3.1/3.2 节 Project/Page 端点
- [ ] `main_sqlite.py` 里一行 `include_router` 接入
- **验收**：`curl -X POST /api/v1/easywiki/projects` 能建project，`GET manifest` 返回固定7栏位

### 阶段2：Agent 提报与治理管线
- [ ] 实现 3.3 节 pending-entries 全部端点，接入 clean_text/detect_pii/查重/质量分（0.3节列出的可信模块）
- **验收**：手工 POST 一条 propose_entry 数据，能在 `easywiki_pending_entries` 表看到 status=pending，approve后能出现在 `easywiki_memories` 表且有 audit log

### 阶段3：MCP Server
- [ ] 实现 6.3 节6个工具，本机用 Claude Code 或 mcp inspector 工具手动连接测试
- **验收**：MCP client能列出6个工具且都能成功调用并拿到预期结构的返回

### 阶段4：配置自动同步
- [ ] 实现 6.5 节，先支持 Claude Code + Easy Code 两个工具的配置写入
- **验收**：点击"启用Claude Code"后，项目里出现 `.claude/mcp.json`（或实际正确文件名）且包含 easywiki 配置，原有其他配置不丢失

### 阶段5：版本与冲突机制
- [ ] 实现 3.5 节三方合并算法 + 3.4 节冲突裁决端点
- **验收**：模拟"人改page A部分+agent提报改page同一部分" → 产生ConflictCase；"人改标题+agent改正文" → 自动合并无冲突

### 阶段6：前端
- [ ] 按第7节搭建React+Vite工程，BlockSuite集成，7个固定栏位页面，Agent Inbox审核界面
- **验收**：能创建项目→在决策与经验栏位新建页面写内容→保存成功→模拟一条agent提报出现在Inbox→批准后能在决策与经验栏位查到

### 阶段7：知识图谱简化版 + 克隆挂载
- [ ] 5.4 节图谱抽取、3.2节 clone-mount 端点
- **验收**：写入一条含"XX项目"的内容后 `easywiki_graph_entities` 出现对应实体；克隆挂载后编辑源页面，挂载方页面内容同步变化

---

*本文档与 `EASYWIKI_PRODUCT_DESIGN.md` 配套使用：产品文档回答"为什么"，本文档回答"怎么做"。执行时如发现两者冲突，以本文档的技术判断为准（因为本文档基于对现有代码的实际核实撰写）。*
