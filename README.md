# EasyWiki — Agent-Driven Organizational Knowledge Base
# EasyWiki — 智能体驱动的组织知识管理平台

[English](#english) | [中文](#chinese)

---

## English

### What is EasyWiki?

EasyWiki is a **self-hosted, desktop-first knowledge management platform** designed for AI-powered software teams. It acts as a shared brain for your organization: capturing decisions, bug fixes, best practices, and architecture choices from both humans and AI agents (Claude Code, Codex, EasyCode, etc.), then making them searchable and reusable.

Unlike traditional wikis that rot in silence, EasyWiki is **agent-native**: your AI coding assistants automatically propose knowledge entries after each session. Humans review, approve, or edit them — forming a living knowledge graph that grows with every project.

### Core Features

| Feature | Description |
|---------|------------|
| **AI Session Auto-Recording** | LLM-powered extraction of decisions, bug fixes, and patterns from coding session transcripts |
| **Agent Inbox & Review** | Human-in-the-loop approval queue with edit-before-approve and batch operations |
| **BlockSuite Rich Editor** | WYSIWYG document editing with version history, clone-mount, and 3-way merge conflict resolution |
| **Semantic Search** | Hybrid retrieval: vector (sentence-transformers) + keyword (jieba FTS5) + graph traversal |
| **MCP Server** | Exposes EasyWiki as an MCP tool for Claude Code, Codex, EasyCode, and other agent frameworks |
| **Knowledge Graph** | Auto-built entity-relation graph from approved memories |
| **Progress Sync Table** | Customizable project tracking fields with agent-proposed updates |
| **RBAC + Invite Codes** | Role-based access (admin/manager/employee) with department hierarchy and invite-code onboarding |
| **Desktop App** | Electron shell bundling the Python backend — no Docker, no cloud, runs locally |

### Architecture

```
┌──────────────────────────────────┐
│  Electron Desktop Shell          │
│  ┌────────────────────────────┐  │
│  │  React Frontend (Vite)     │  │
│  │  - Tailwind CSS            │  │
│  │  - BlockSuite Editor       │  │
│  │  - React Router            │  │
│  └──────────┬─────────────────┘  │
│             │ REST + JWT          │
│  ┌──────────▼─────────────────┐  │
│  │  FastAPI Backend           │  │
│  │  - SQLite (Tier0 Solo)     │  │
│  │  - sentence-transformers   │  │
│  │  - jieba Chinese NLP       │  │
│  │  - MCP stdio server        │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

### Quick Start

**Prerequisites:** Python 3.10+, Node.js 18+

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Start backend
cd orgmind
python -m orgmind.main_sqlite

# 3. Start frontend (separate terminal)
cd frontend-src
npm install
npm run dev

# 4. Open browser
# http://localhost:5173
```

**Default login:** `admin@local` / `orgmind2026`

### Tech Stack

- **Backend:** Python 3.10+, FastAPI, SQLite, sentence-transformers, jieba
- **Frontend:** React 19, TypeScript 6, Tailwind CSS 3, BlockSuite 0.19, Vite 8
- **Desktop:** Electron 33
- **AI:** OpenAI-compatible LLM API for memory extraction

### License

**This software is NOT free for commercial use.** All rights reserved.

- **Personal/Educational use:** Allowed without restriction.
- **Commercial use:** Requires a written license agreement from the copyright holder. Contact the project maintainers for licensing inquiries.
- **Redistribution:** Not permitted without explicit permission.

See [LICENSE](LICENSE) for full terms.

---

## 中文

### EasyWiki 是什么？

EasyWiki 是一个**本机优先、桌面化的组织知识管理平台**，专为 AI 辅助的软件团队设计。它作为团队的共享大脑：自动捕获人类和 AI 智能体（Claude Code、Codex、EasyCode 等）在编码过程中产生的决策、Bug 修复、最佳实践和架构选择，并将其组织为可搜索、可复用的知识。

与传统 wiki 不同，EasyWiki 是 **Agent 原生** 的：你的 AI 编程助手会在每次会话后自动提报知识条目。人类审核、批准或编辑它们——形成一张随项目持续生长的活知识图谱。

### 核心功能

| 功能 | 说明 |
|------|------|
| **AI 会话自动记录** | LLM 驱动的决策/Bug修复/模式提取，从编码会话文本自动生成结构化记忆 |
| **Agent 待审核队列** | 人工审核工作流：批准/编辑后批准/驳回，支持批量操作 |
| **BlockSuite 富文本编辑器** | 所见即所得文档编辑，支持版本历史、克隆挂载、三路合并冲突解决 |
| **语义搜索** | 混合检索：向量（sentence-transformers）+ 关键词（jieba FTS5）+ 图谱遍历 |
| **MCP 服务** | 将 EasyWiki 暴露为 MCP 工具，供 Claude Code、Codex、EasyCode 等 Agent 框架调用 |
| **知识图谱** | 从已批准的记忆中自动构建实体-关系图谱 |
| **进度同步表** | 可自定义的项目跟踪字段，Agent 可建议更新 |
| **RBAC + 邀请码** | 角色权限（管理员/经理/员工），部门层级体系，邀请码自助入职 |
| **桌面应用** | Electron 壳封装 Python 后端——无需 Docker、无需云端、本地运行 |

### 架构

```
┌──────────────────────────────────┐
│  Electron 桌面壳                  │
│  ┌────────────────────────────┐  │
│  │  React 前端 (Vite)         │  │
│  │  - Tailwind CSS            │  │
│  │  - BlockSuite 编辑器        │  │
│  │  - React Router            │  │
│  └──────────┬─────────────────┘  │
│             │ REST + JWT          │
│  ┌──────────▼─────────────────┐  │
│  │  FastAPI 后端               │  │
│  │  - SQLite (Tier0 单机版)    │  │
│  │  - sentence-transformers   │  │
│  │  - jieba 中文分词           │  │
│  │  - MCP stdio 服务           │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

### 快速开始

**前提条件：** Python 3.10+, Node.js 18+

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 启动后端
cd orgmind
python -m orgmind.main_sqlite

# 3. 启动前端（新终端窗口）
cd frontend-src
npm install
npm run dev

# 4. 打开浏览器
# http://localhost:5173
```

**默认登录账号：** `admin@local` / `orgmind2026`

### 技术栈

- **后端：** Python 3.10+, FastAPI, SQLite, sentence-transformers, jieba
- **前端：** React 19, TypeScript 6, Tailwind CSS 3, BlockSuite 0.19, Vite 8
- **桌面端：** Electron 33
- **AI：** OpenAI 兼容的 LLM API（用于记忆提取）

### 许可协议

**本软件禁止免费商用。** 保留所有权利。

- **个人/教育用途：** 无需授权，自由使用。
- **商业用途：** 必须获得著作权人的书面许可授权。商业授权咨询请联系项目维护者。
- **再分发：** 未经明确许可，禁止再分发。

完整条款见 [LICENSE](LICENSE) 文件。

---

## Team

Maintained by **NSIETeam**. Contributions welcome under the project's contribution guidelines.

## 团队

由 **NSIETeam** 维护。欢迎按项目贡献指南参与开发。
