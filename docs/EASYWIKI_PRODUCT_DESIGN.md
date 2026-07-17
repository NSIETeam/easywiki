# EasyWiki 产品设计文档 v1.0

> 状态：已定稿（本文档写入后按用户要求转为只读，后续变更需另开新版本文档）
> 关联项目：OrgMind（后端能力全面复用）
> 编写依据：对 OrgMind 现有代码（models/memory.py, artifact.py, document.py, graph/engine.py, skills/engine.py, governance/*, retrieval/*, agents/registry.py 等）的实读分析 + 开源生态调研（AFFiNE/BlockSuite、Trilium、AppFlowy）+ 用户对定位、协议、冲突机制的明确决策。

---

## 0. 一句话定位

EasyWiki 是组织的"活知识库"：人在里面写流程、经验、图谱；Claude Code / Codex / WorkBuddy / Easy Code 等 AI 编码工具在检测到项目接入 EasyWiki 后，通过 **MCP** 把工作过程中的决策、修复、最佳实践、进度**提交为待审核记录**，由项目负责人确认后正式沉淀。人写的和 agent 干活留下的知识汇聚在同一处，且全程有类似 git 的版本、冲突、责任追溯机制。

---

## 1. 背景与问题

- 多个 AI 编码工具协作开发时，每个工具的会话历史互相隔离，做过的决策、踩过的坑、修复方案随会话结束即丢失，无法被同事或下一次会话复用。
- 组织流程文档、项目经验依赖人工整理，滞后且易过时。
- 项目进度靠人工在表格里手动填报，而 agent 本身已经知道任务进展，却没有可信、可控的渠道自动同步。
- 现有 OrgMind 已经具备记忆抽取、去重、PII 检测、知识图谱、Skill/Agent 复用、检索路由、Token画像等完整后端能力，但前端是自研 SPA，编辑体验（块编辑、白板、页面组织）薄弱，且缺少标准化的 Agent 写入协议。

## 2. 核心决策（已与用户确认，作为本文档的设计前提，不再讨论）

| 决策项 | 结论 |
|---|---|
| 与 OrgMind 关系 | **复用现有后端全部代码**（models/governance/retrieval/graph/skills/agents），EasyWiki = OrgMind 的新前端引擎 + Agent Bridge 新模块，不重建业务逻辑 |
| UI 引擎 | 不整体 fork AFFiNE App（其 `packages/backend` 是 EE 商业许可，且自带一整套账号/同步后端会与 OrgMind 后端冲突）。**只取 BlockSuite**（MIT 许可，块编辑器 + Edgeless 白板，Web Components，框架无关）作为编辑与白板渲染层，持久化层自己写适配器对接 OrgMind FastAPI |
| Agent 协议 | **只做 MCP，不支持 MCP 的工具不考虑**。已核实 Claude Code / Codex CLI（本地 subprocess MCP）/ WorkBuddy（mcp.json）/ Easy Code 均支持 MCP |
| 写入时机 | 关键节点实时上报 + 会话结束后**压缩汇总**（不是原始transcript，是过程摘要），**两种情况都需人工确认才正式入库**，没有任何自动发布路径 |
| 项目定位 | Project 是**最小的完整协作过程记录单位**（不是任务、不是文档，是"一段协作历史"的容器） |
| 信息架构 | **固定栏位骨架 + 栏位内自由页面树**的混合模式（见第5.1节，含选择理由） |
| 进度表所有权 | 人可写、agent 可写（需确认），**没有单向锁定字段**；冲突不是"禁止覆盖"而是走版本对比，由组织中更高级别的人或超级管理员裁决 |
| 冲突解决 | 全面采用 **git 式三方合并（3-way merge）** 思路：base/人工版本/agent版本对比，无重叠自动合并，有重叠生成冲突块，升级给上级或超管裁决，所有历史版本保留可追溯 |
| 范围 | 本文档为**完整愿景版**，不做 MVP 裁剪；文末附建议的建设顺序（非裁剪范围，只是先后顺序） |

## 3. 技术选型调研结论（供架构组存档）

| 候选 | 许可/架构 | 结论 |
|---|---|---|
| AFFiNE（整体） | 编辑器/桌面壳 MIT；`packages/backend`（协同同步、workspace账号体系）为 **AFFiNE EE 商业许可** | 不采用整体方案。自带后端会和 OrgMind FastAPI 形成"两个大脑"，且 EE 部分二次修改需要商业授权 |
| **BlockSuite**（单独） | MIT，块树结构，Web Components，CRDT(Yjs)可选启用 | **采用**。只借渲染引擎，不借它的同步后端；持久化、权限、版本全部走 OrgMind 后端，CRDT 能力仅用于同一文档内的本地多光标编辑体验，不用于跨端同步（跨端同步走我们自己的 git 式版本机制，见第6节） |
| Trilium Notes | AGPL3，TS+Node+SQLite，树形笔记 + "克隆(Cloning)"机制 + ETAPI REST | 不整体采用（Node后端会与Python后端重复）。**借鉴其"克隆"信息架构**：一篇内容可同时挂载在多个位置，编辑一处处处同步 —— 这正好解决"组织级SOP被多个项目继承"的需求，已吸收进第5.1节设计 |
| AppFlowy | AGPL3，Flutter+Rust，Grid/Board/Calendar 数据库视图 | 不采用（技术栈与现有 Python 后端无法共享代码，集成成本高于收益）。其数据库视图思路作为"进度同步表"UI 设计的参考 |

## 4. 核心概念模型

```
Organization
 ├─ Project（最小的完整协作过程记录单位，一级导航主体）
 │   ├─ Overview（项目概览：目标/团队/关键人/健康度）
 │   ├─ Decisions & Experience（决策记录 + 经验库，人写 + agent提报）
 │   ├─ Knowledge Graph View（本项目相关实体关系图）
 │   ├─ Agents & Skills（可复用 agent 设定 / skill，可来自组织库）
 │   ├─ Files（各类文件资料）
 │   ├─ Progress Sync Table（进度同步表，人写 + agent提报）
 │   └─ Agent Inbox（本项目的 agent 提报待审核队列）
 └─ Org Knowledge Base（跨项目共享内容：组织级流程/SOP/通用Skill/通用Agent）
     └─ 内容通过"克隆挂载"方式出现在各 Project 的对应栏位里（非复制，编辑同步）
```

- **Memory**（复用 OrgMind `models/memory.py`）：细粒度知识条目（decision/bug_fix/best_practice/architecture/episodic），Decisions & Experience 栏位的原子内容单元。
- **Document/DocumentChunk**（复用 `models/document.py`）：非结构化文件，chunk+embedding 支持语义检索定位段落。
- **Artifact/ArtifactPermission**（复用 `models/artifact.py`）：Agent/Skill 定义，object_type 区分，三层渐进加载（复用 `skills/engine.py`）。
- **Graph Entity/RELATED**（复用 `graph/engine.py` + `graph/extractor.py`）：实体关系抽取与查询。
- **ProgressField**（新增）：进度表字段，见第7节。
- **AgentEvent / PendingEntry**（新增）：agent 提报的原始事件与待审核记录，见第6节。
- **VersionRecord / ConflictCase**（新增）：git式版本与冲突裁决记录，见第6节。

## 5. 信息架构

### 5.1 固定栏位 + 自由页面树（选型理由）

用户明确表示对"固定栏位 vs 自由页面树"没有定论，这里给出推荐方案并说明理由：

**推荐：栏位骨架固定，栏位内部内容自由组织成页面树。**

理由：
1. **Agent 写入需要可预测的落点**。如果整个项目是纯自由页面树，agent 提报"一条决策记录"时不知道该挂在哪个页面下，容易造成同类内容散落各处，检索效率下降。固定栏位（Decisions & Experience / Progress 等）给 agent 提供了确定的写入目标，MCP 工具的参数设计（第6.3节）也依赖这个确定性。
2. **人整理知识需要自由度**。纯固定表单（类似飞书多维表格单一结构）无法承载"某个复杂项目需要拆出5篇子文档说明架构演进"这种非结构化需求，所以栏位内部必须是自由页面树（无限层级子页面）。
3. **借鉴 Trilium 的"克隆"机制解决跨项目复用**：组织级 SOP 页面可以同时"挂载"在 Org Knowledge Base 和多个 Project 的 Decisions & Experience 栏位下，物理上是同一份内容、同一套版本历史，编辑任意一处、所有挂载点同步更新，避免"复制后各自漂移"。

结论：Project 固定 7 个一级栏位（不可增删，保证跨项目一致性和 agent 可预测性）；每个栏位下允许用户自由创建/嵌套页面（用 BlockSuite 块编辑器，支持子页面无限层级）。

### 5.2 顶层导航

```
Workspace（对应组织，多组织时可切换）
 ├─ 🏠 我的项目 / 全部项目（默认落地页，列表+卡片视图，含健康度/最近Agent活动摘要）
 ├─ 📚 组织知识库（跨项目 SOP / 通用 Agent / 通用 Skill，来源于此的内容会被克隆挂载进项目）
 ├─ 🕸 全局知识图谱（跨所有项目的实体关系，可下钻到具体 Memory/Page）
 ├─ 🤖 Agent 活动中心（全组织范围的 agent 提报流水 + 待审核汇总 + 冲突裁决队列）
 └─ ⚙️ 设置（成员与角色/部门结构/接入的 Agent 工具管理/MCP连接状态/Token用量看板）

进入某个 Project 后：
 概览 | 决策与经验 | 知识图谱 | Agent与Skill | 文件 | 进度表 | Agent Inbox
```

## 6. Agent 集成协议（EasyWiki Agent Bridge）

这是本产品相对 OrgMind 的最核心新增模块。

### 6.1 发现层（检测机制）

EasyWiki 桌面客户端在用户"接入项目"时，在项目根目录写入两个文件：

- `EASYWIKI.md`：自然语言说明，供 agent 的模型本身读取理解（心智类似 `CLAUDE.md`/`AGENTS.md`），内容包括：本项目已接入 EasyWiki、有哪些 MCP 工具可用、什么时候应该调用（关键节点 + 会话结束）、写入后需要人工确认不会立即生效等行为准则。
- `.easywiki/manifest.json`：机器可读配置，包含 project_id、栏位schema、MCP endpoint信息。

**关键设计**：MCP 的"连接"和"检测"是两件事分开处理——

- **检测**：agent 打开项目目录时读到 `EASYWIKI.md`，模型自己知道"这里有 EasyWiki"。
- **连接**：不能指望每个开发者手动给4个工具分别配置MCP。所以 EasyWiki 桌面客户端提供"**同步Agent配置**"功能：一键检测机器上已安装的支持工具（Claude Code 的项目级`.claude`配置、Codex 的`~/.codex/config.toml`、WorkBuddy 的`mcp.json`、Easy Code 的MCP设置），自动写入/更新对应配置项，指向本机 EasyWiki 的 MCP Server 地址。用户只需在 EasyWiki 里点一次"启用xx工具"，无需分别去4个工具里手搓配置。

### 6.2 EasyWiki MCP Server（本机常驻）

EasyWiki 桌面应用内置一个 MCP Server（与现有 FastAPI 后端同进程或旁路进程，走 stdio 或本机 SSE，供 Codex 等仅支持本地 subprocess 的工具使用）。

暴露的 MCP 工具：

| 工具名 | 用途 | 何时调用 |
|---|---|---|
| `easywiki.search_knowledge` | 语义检索组织知识库/项目历史（复用 `retrieval/router.py` 三路混合检索） | 干活前，避免重复踩坑 |
| `easywiki.get_project_manifest` | 获取项目栏位schema、进度表字段定义 | 首次进入项目/需要知道结构时 |
| `easywiki.propose_entry` | 提报一条决策/修复/最佳实践/架构记录（关键节点触发） | 完成一个关键动作时 |
| `easywiki.propose_session_summary` | 提报会话结束后的**压缩汇总**（不是原始transcript，是结构化摘要条目数组） | 会话/任务结束时 |
| `easywiki.propose_progress_update` | 提报进度表某字段的建议新值 | 任务状态变化时 |
| `easywiki.get_pending_status` | 查询自己之前提报的记录是否已被人工确认 | 可选，用于自我核对 |

所有 `propose_*` 均不直接写入正式知识库，而是创建 `PendingEntry`，等待人工确认（见6.4节）——这是用户明确要求的"需要人工确认"，无任何置信度阈值下的自动发布路径。

### 6.3 事件/提报 Schema

```json
{
  "session_id": "...",
  "project_id": "...",
  "tool_name": "claude-code | codex | workbuddy | easycode",
  "entry_type": "decision | bug_fix | best_practice | architecture | progress_update | session_summary",
  "target_section": "decisions_experience | progress_table | files",
  "content": "...",
  "file_refs": ["src/auth.py"],
  "confidence": 0.0-1.0,
  "based_on_version": "vX",
  "timestamp": "..."
}
```

`based_on_version` 是关键字段：agent 生成提报时记录它当时读到的知识库版本号，用于6.6节的三方合并判断。

### 6.4 落库前处理管线（复用 OrgMind governance）

```
propose_* 提报 → PendingEntry(status=pending)
  → clean_text（清洗）
  → check_memory_duplicate（去重，提示"可能与已有内容重复"）
  → detect_pii（PII检测，敏感内容强制标记，审核时高亮提示）
  → compute_quality_score（质量分，仅用于审核队列排序/建议，不用于自动发布判断）
  → 进入对应项目的 Agent Inbox，等待人工"批准/编辑后批准/驳回"
  → 批准后 → 写入正式 Memory/ProgressField → build_graph_from_text 增量写图谱
```

**治理原则**：质量分/置信度只影响 Inbox 里的**排序和建议标签**（比如"建议优先审核"或"建议直接批准"角标），绝不触发自动发布——这是与 v0.1 草稿的关键区别，已按用户要求修正。

### 6.5 人工确认体验

Agent Inbox 是一个类似 PR review 的界面：

- 列表：来源工具图标、entry_type、内容摘要、目标栏位、质量/去重提示、时间。
- 单条操作：**批准**（直写入库）/ **编辑后批准**（可修改文字再入库，编辑记录留痕）/ **驳回**（说明理由，可选择"通知发起会话的工具下次改进"，仅记录不强制生效）。
- 批量操作：可勾选多条低风险（无PII、无重复冲突提示）内容一键批准，降低审核疲劳。
- **会话汇总类提报**默认展开为清单形式（一次会话可能压缩出3-5条待确认条目），可逐条批准而非整体二选一。

### 6.6 版本与冲突机制（git式三方合并）

这是响应用户"git的解决思路已经非常不错了"的核心设计，贯穿全产品（不止进度表，Page内容、Progress字段都适用）：

- 每个可编辑单元（一篇 Page、一个 ProgressField）维护线性版本历史（VersionRecord），每次人工编辑或 agent 提报被批准都产生一个新版本，记录 `author`（人或具体agent+工具+session_id）、`based_on_version`、`diff`。
- **agent 提报审核时的三方对比**：
  - `base` = agent 生成提报时读到的版本（`based_on_version`）
  - `current` = 审核当下的最新已批准版本（可能因为期间有人手动编辑而领先于base）
  - `proposed` = agent 提报内容
  - 若 `current == base`（期间无人编辑）→ 无冲突，批准即直接应用。
  - 若 `current != base` 且改动范围不重叠（比如人改了标题，agent提报改的是正文）→ 系统自动三方合并，审核者看到的是合并后预览，一键确认。
  - 若改动重叠（人和agent都改了同一段/同一字段的值）→ 生成 **ConflictCase**，UI 用类似 git 冲突标记的方式并排展示 `current`（人工版本）与 `proposed`（agent版本），审核者可以：采纳人工版 / 采纳agent版 / 手动合并两者 / **升级（Escalate）**。
- **升级裁决**：若审核者（通常是项目负责人）无法/不愿独自决定，或冲突涉及组织级共享内容（Org Knowledge Base，影响多个项目），系统按组织架构（复用 `models/user.py` 的 department/role 层级）自动路由给**上级管理者**；若无明确上级或冲突跨部门，则路由给**超级管理员**。裁决记录（谁、何时、选了哪个版本、理由）永久留痕，任何历史版本都不会被物理删除，可随时回溯（"git blame"式的溯源视图：一段内容是谁在哪次会话里写的）。

## 7. 项目进度同步表单（Progress Sync Table）

- 不做成通用多维表格，而是**结构化字段 + 每字段独立版本历史**的表：任务、负责人、状态、优先级、预估完成度、最近更新说明等字段均可人写、也可被 agent 提报建议值。
- 无预设的"只读锁定字段"（按用户要求去掉了 v0.1 中的所有权锁定设计），**人和 agent 对同一字段的并发修改统一走第6.6节的三方合并/冲突裁决机制**，不是简单的"后写覆盖前写"或"人工优先"。
- 视图层：基于 BlockSuite 的 database block（或自定义 block 扩展）渲染成类似 Notion/飞书多维表格的表格视图，同时保留"这个格子背后是谁在哪次会话改的"的溯源角标。
- Agent 提报的进度更新同样先进 Agent Inbox 待确认（不做字段级例外），保证"人工确认"原则在整个产品里统一，不因内容类型产生特例。

## 8. 功能模块详述

### 8.1 项目工作台
Project 首页：概览卡片（阶段/健康度/团队）、最近 Agent 提报流（可直接跳转到对应 Inbox 条目处理）、待处理冲突提醒、进度表快照视图。

### 8.2 组织知识库
组织级流程/SOP/通用 Agent/通用 Skill 的中心；内容通过"克隆挂载"出现在各项目对应栏位（同一份内容、同一版本历史，非复制）。变更该内容会影响所有挂载它的项目，因此编辑组织知识库内容需要更高权限（默认：manager及以上）。

### 8.3 知识图谱
复用 KuzuDB/FalkorDB 图引擎（`graph/engine.py`），在 Edgeless 白板（BlockSuite）里渲染实体关系图，支持从节点反查关联的 Memory/Page/Document，支持项目内视图与全局视图切换。

### 8.4 Agent 与 Skill 库
复用 `models/artifact.py` + 三层渐进加载引擎（`skills/engine.py`：Redis目录常驻 → 按需加载正文 → 延迟加载附属资源）+ `agents/registry.py` 的注册/调用/衍生(fork)逻辑。团队可发布好用的 agent 人设/skill 为组织级共享资产，MCP 的 `search_knowledge` 检索时可命中并被其他项目的 agent 复用。

### 8.5 文件中心
文件上传走 chunk+embedding（复用 `models/document.py`），支持语义检索定位到具体段落/表格行。版本管理复用第6.6节的通用版本机制（文件视为特殊的可编辑单元，新版本上传即产生 VersionRecord）。

### 8.6 检索
三路混合检索（复用 `retrieval/router.py`：vector + keyword(jieba分词) + graph扩展 + token预算 + 降级容错），按 role/department/project scope 权限过滤（复用现有RLS/scope机制）。MCP 的 `search_knowledge` 直接调用此路由。

## 9. 数据模型（复用 + 新增）

**直接复用（不改动 schema）**：`Memory`、`Document`/`DocumentChunk`/`DataLineage`、`Artifact`/`ArtifactPermission`、图引擎的 Entity/RELATED、`User`/`Department`/`Organization`。

**新增**：
- `PendingEntry`：agent 提报的待审核记录（session_id, tool_name, entry_type, target_section, raw_content, based_on_version, quality_score, dedup_hint, pii_flag, status[pending/approved/edited_approved/rejected]）
- `ProgressField`：进度表字段（project_id, field_name, current_value, current_version_id）
- `VersionRecord`：通用版本历史（target_type[page/progress_field/document], target_id, author_type[human/agent], author_ref, content_diff, based_on_version, created_at）
- `ConflictCase`：冲突裁决记录（target_type, target_id, base_version, human_version, agent_version, escalated_to, resolution, resolved_by, resolved_at）
- `AgentBridgeConfig`：项目的 manifest 配置（对应 `.easywiki/manifest.json`）+ 已启用的工具连接状态

## 10. 技术架构

```
┌───────────────────────────────────────────┐
│  EasyWiki Desktop（复用 desktop_shell.py 的 pywebview 桌面壳模式）│
│  BlockSuite 编辑器 + Edgeless白板 + Database block（自定义持久化适配器） │
└───────────────────┬─────────────────────────┘
                     │ REST（复用现有 FastAPI /api/v1 路由）
┌───────────────────▼─────────────────────────┐
│  EasyWiki Backend = OrgMind FastAPI（原有全部模块）│
│  memory/document/artifact API + governance管线    │
│  retrieval router + graph engine + skills engine   │
│  + 新增：PendingEntry/VersionRecord/ConflictCase API│
└───────────────────┬─────────────────────────┘
                     │
┌───────────────────▼─────────────────────────┐
│  Agent Bridge（新增，本机常驻 MCP Server）│
│  stdio/SSE MCP + 配置自动同步（写各工具的MCP配置文件）│
└──────┬──────────┬───────────┬───────────┬─────┘
   Claude Code   Codex CLI   WorkBuddy   Easy Code
   (原生MCP)   (本地subprocess) (mcp.json)  (MCP)
```

沿用 OrgMind 现有分层部署策略：Solo 模式（SQLite 本地，单机桌面应用，个人/小团队）→ 企业模式（Postgres + Redis + FalkorDB 图数据库集群，多端协同）。

## 11. 权限与治理

- 延用 OrgMind 现有 org/department/project scope + role(admin/manager/employee) 权限模型。
- Agent 提报内容强制过 `governance/pii.py` 检测，敏感信息在 Inbox 审核界面高亮提示，不自动脱敏隐藏（人工判断是否需要脱敏/驳回）。
- 组织知识库（跨项目共享内容）的编辑权限默认高于项目内容（manager及以上），因为改动影响面更大。
- 冲突裁决权限路由：项目负责人 → 部门/上级管理者 → 超级管理员，按 `models/user.py` 现有的 department 层级自动计算路由链路。

## 12. 关键用户故事

1. 开发者用 Claude Code 解决一个棘手 bug → 会话结束，Claude Code 调用 `propose_session_summary` 提报压缩摘要（含这条 bug_fix）→ 出现在项目 Agent Inbox → 项目负责人审核批准 → 写入 Decisions & Experience，之后其他项目的开发者通过 `search_knowledge` 能检索到。
2. 新人加入项目，agent 在开始干活前调用 `search_knowledge("部署流程")` → 命中组织知识库里克隆挂载进本项目的 SOP 页面，减少重复提问人力。
3. Agent 提报"任务X已完成"更新进度表，但审核时发现负责人在此期间已手动改成"遇到阻塞"→ 系统检测到字段改动重叠 → 生成 ConflictCase，因涉及跨部门联调任务，自动升级给项目所在部门经理裁决 → 经理选择保留人工版本并备注原因，两版本均保留在历史中可查。
4. 组织知识库里的"代码审查规范"页面被产品负责人修改，因其被5个项目克隆挂载，系统提示"该修改将影响5个项目"，需 manager 及以上权限确认。

## 13. 非目标 / 已知限制

- 不做多 agent 间的"强编排协作"（互相调用、接续任务），本产品是"共享知识层"的松耦合协作模式。
- BlockSuite 的 CRDT 能力仅用于单文档内的本地多光标编辑体验，不承担跨端实时同步职责（同步走本产品自建的版本/冲突机制），避免引入 AFFiNE 式的复杂同步后端。
- Codex CLI 目前仅支持本地 subprocess MCP（不支持远程 MCP），因此 Agent Bridge 必须以本机常驻进程形态提供服务，纯云端部署场景下 Codex 用户需要本机运行一个轻量连接器（后续技术方案需专门设计，此处仅标注限制）。
- 知识库审核疲劳是长期运营风险：会话汇总压缩得越好、批量批准做得越顺畅，人工确认成本才可控，这部分的压缩算法质量（复用 `services/auto_memory.py` 的 LLM优先/规则降级思路）直接决定产品体验，需要持续迭代。

## 14. 建议建设顺序（非范围裁剪，仅为落地顺序）

1. Agent Bridge 骨架：本机 MCP Server + 配置自动同步 + `propose_entry`/`search_knowledge` 两个最核心工具，先打通 Claude Code + Easy Code。
2. Agent Inbox 审核体验 + PendingEntry/governance管线接入（复用现有清洗/去重/PII/质量分模块）。
3. BlockSuite 编辑器集成 + 项目固定栏位骨架 + 自由页面树。
4. 版本历史 VersionRecord + 三方合并 + ConflictCase 裁决路由。
5. 进度同步表 + Database block 视图。
6. 知识图谱可视化（Edgeless白板嵌图）+ 组织知识库克隆挂载机制。
7. Codex/WorkBuddy 的 MCP 接入验证与体验打磨。

---

*本文档为 v1.0 定稿版，写入后转为只读状态。*
