"""
SQLite 异步数据库层 — Tier0 Solo 模式, 零外部依赖
替代 PostgreSQL + pgvector + Redis
"""
import sqlite3
import json
import math
import numpy as np
from typing import List, Dict, Optional, Tuple, Set
from contextlib import contextmanager
import threading
import os

DB_PATH = os.getenv("ORGMIND_DB_PATH", os.path.expanduser("~/.orgmind/orgmind.db"))


class OrgMindDB:
    """SQLite 单例, 线程安全, 内嵌向量相似度计算"""
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._local = threading.local()

    @staticmethod
    def get():
        if OrgMindDB._instance is None:
            with OrgMindDB._lock:
                if OrgMindDB._instance is None:
                    OrgMindDB._instance = OrgMindDB()
                    OrgMindDB._instance._init_schema()
        return OrgMindDB._instance

    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn

    def _init_schema(self):
        c = self._conn()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS organizations (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS departments (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, parent_id TEXT, org_id TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
            role TEXT DEFAULT 'employee', department_id TEXT, org_id TEXT NOT NULL,
            project_ids TEXT DEFAULT '[]', hashed_password TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY, org_id TEXT NOT NULL, department_id TEXT, project_id TEXT,
            type TEXT NOT NULL, scope TEXT DEFAULT 'department', content TEXT NOT NULL,
            summary TEXT, content_hash TEXT, embedding TEXT,
            sensitivity TEXT DEFAULT 'normal', importance REAL DEFAULT 0.5,
            decay_score REAL DEFAULT 1.0, status TEXT DEFAULT 'active',
            superseded_by TEXT, graph_node_id TEXT, created_by TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')), expires_at TEXT,
            access_count INTEGER DEFAULT 0, last_accessed TEXT, quality_score REAL,
            extra_metadata TEXT DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS memory_shares (
            id TEXT PRIMARY KEY,
            memory_id TEXT NOT NULL,
            shared_by_user_id TEXT NOT NULL,
            shared_with_user_id TEXT,
            shared_with_department_id TEXT,
            share_scope TEXT DEFAULT 'user',
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS artifacts (
            id TEXT PRIMARY KEY, org_id TEXT NOT NULL, object_type TEXT NOT NULL,
            name TEXT NOT NULL, description TEXT NOT NULL, description_embedding TEXT,
            content TEXT NOT NULL, resources TEXT DEFAULT '{}', version TEXT NOT NULL,
            status TEXT DEFAULT 'draft', scope TEXT DEFAULT 'department',
            department_id TEXT, auto_generated INTEGER DEFAULT 0, confidence REAL DEFAULT 1.0,
            parent_id TEXT, author_id TEXT, tags TEXT DEFAULT '[]',
            tools TEXT DEFAULT '[]', bound_skill_ids TEXT DEFAULT '[]',
            usage_count INTEGER DEFAULT 0, success_rate REAL,
            graph_node_id TEXT, created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')), extra_metadata TEXT DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS artifact_permissions (
            artifact_id TEXT, role TEXT NOT NULL, access TEXT NOT NULL, scope TEXT DEFAULT 'org',
            PRIMARY KEY (artifact_id, role, access)
        );
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY, org_id TEXT NOT NULL, department_id TEXT, project_id TEXT,
            doc_type TEXT NOT NULL, title TEXT, storage_key TEXT NOT NULL, content_hash TEXT,
            scope TEXT DEFAULT 'department', sensitivity TEXT DEFAULT 'normal',
            status TEXT DEFAULT 'active', created_by TEXT NOT NULL, quality_score REAL,
            graph_node_id TEXT, created_at TEXT DEFAULT (datetime('now')), extra_metadata TEXT DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS document_chunks (
            id TEXT PRIMARY KEY, document_id TEXT NOT NULL, chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL, embedding TEXT, start_offset REAL, end_offset REAL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS tools (
            id TEXT PRIMARY KEY, org_id TEXT, name TEXT UNIQUE NOT NULL, description TEXT NOT NULL,
            input_schema TEXT NOT NULL, output_schema TEXT, execution_type TEXT NOT NULL,
            endpoint TEXT, allowed_roles TEXT NOT NULL, requires_confirmation INTEGER DEFAULT 0,
            timeout_ms INTEGER DEFAULT 30000, rate_limit_per_minute INTEGER DEFAULT 60,
            is_disabled INTEGER DEFAULT 0, created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY, user_id TEXT, title TEXT, model TEXT,
            created_at TEXT DEFAULT (datetime('now')), extra_metadata TEXT DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY, user_id TEXT, action TEXT NOT NULL, resource_type TEXT,
            resource_id TEXT, details TEXT DEFAULT '{}', created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS invite_codes (
            id TEXT PRIMARY KEY, org_id TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            department_id TEXT NOT NULL,
            role TEXT DEFAULT 'employee',
            max_uses INTEGER DEFAULT 1,
            used_count INTEGER DEFAULT 0,
            created_by TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            expires_at TEXT
        );

        -- EasyWiki tables (v1.0)
        CREATE TABLE IF NOT EXISTS easywiki_projects (
            id TEXT PRIMARY KEY, org_id TEXT NOT NULL, name TEXT NOT NULL,
            health TEXT DEFAULT 'on_track', department_id TEXT,
            created_by TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS easywiki_pages (
            id TEXT PRIMARY KEY, project_id TEXT NOT NULL, section TEXT NOT NULL,
            title TEXT NOT NULL, parent_page_id TEXT, sort_order INTEGER DEFAULT 0,
            content_ref TEXT NOT NULL,
            created_by TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS easywiki_page_contents (
            id TEXT PRIMARY KEY,
            blocksuite_doc TEXT NOT NULL,
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
            id TEXT PRIMARY KEY, org_id TEXT NOT NULL, project_id TEXT NOT NULL,
            type TEXT NOT NULL,
            content TEXT NOT NULL, content_hash TEXT NOT NULL, embedding TEXT,
            sensitivity TEXT DEFAULT 'normal', quality_score REAL,
            author_type TEXT NOT NULL,
            author_ref TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS easywiki_progress_fields (
            id TEXT PRIMARY KEY, project_id TEXT NOT NULL,
            field_name TEXT NOT NULL, field_type TEXT DEFAULT 'text',
            current_value TEXT, current_version_id TEXT,
            UNIQUE(project_id, field_name)
        );
        CREATE TABLE IF NOT EXISTS easywiki_versions (
            id TEXT PRIMARY KEY, target_type TEXT NOT NULL,
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
            manifest_json TEXT NOT NULL,
            enabled_tools TEXT DEFAULT '[]',
            updated_at TEXT DEFAULT (datetime('now'))
        );
        """)
        # FTS5 全文索引 (中文分词由 jieba 在应用层处理)
        try:
            self._conn().executescript("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    memory_id, content, tokenize='unicode61'
                );
            """)
        except Exception:
            pass  # FTS5 may not be available in all SQLite builds
        self._conn().commit()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self._conn().execute(sql, params)

    def commit(self):
        self._conn().commit()

    # === 部门层级: 获取用户可见的所有部门 ID ===
    def get_visible_departments(self, user_id: str, role: str, dept_id: str, org_id: str) -> Set[str]:
        """
        admin: 返回组织内所有部门
        manager: 返回本部门 + 所有子部门 (递归)
        employee: 返回本部门
        """
        if role == 'admin':
            rows = self.execute("SELECT id FROM departments WHERE org_id=?", (org_id,)).fetchall()
            return {r['id'] for r in rows}

        if not dept_id:
            return set()

        if role == 'manager':
            return self._get_subtree(dept_id)

        # employee
        return {dept_id}

    def _get_subtree(self, dept_id: str) -> Set[str]:
        """递归获取部门及所有子部门"""
        result = {dept_id}
        children = self.execute("SELECT id FROM departments WHERE parent_id=?", (dept_id,)).fetchall()
        for child in children:
            result.update(self._get_subtree(child['id']))
        return result

    # === 共享记忆: 获取共享给某用户或某部门的记忆 ID ===
    def get_shared_memory_ids(self, user_id: str, dept_id: str) -> Set[str]:
        rows = self.execute(
            "SELECT memory_id FROM memory_shares WHERE shared_with_user_id=? OR shared_with_department_id=?",
            (user_id, dept_id)
        ).fetchall()
        return {r['memory_id'] for r in rows}

    # === 向量相似搜索 (SQLite内联 numpy) — 带权限过滤 ===
    def vector_search(self, query_embedding: List[float], org_id: str, visible_depts: Set[str],
                      shared_mem_ids: Set[str], user_id: str, top_k: int = 20) -> List[Dict]:
        """用 numpy 计算余弦相似度, 在内存中排序取 top_k, 已过滤权限"""
        rows = self.execute(
            "SELECT id, content, type, embedding, created_at, access_count, scope, department_id, created_by FROM memories WHERE org_id=? AND embedding IS NOT NULL AND status='active'",
            (org_id,)
        ).fetchall()

        results = []
        q_emb = np.array(query_embedding)
        q_norm = np.linalg.norm(q_emb) or 1.0

        for row in rows:
            # 权限过滤
            scope = row['scope']
            if scope == 'personal' and row['created_by'] != user_id:
                continue
            if scope == 'department' and row['department_id'] not in visible_depts:
                # 检查是否被共享
                if row['id'] not in shared_mem_ids:
                    continue
            if scope == 'project':
                pass  # project scope 通过 project_ids 在调用层处理

            emb = json.loads(row['embedding'])
            vec = np.array(emb)
            sim = float(np.dot(q_emb, vec) / (q_norm * (np.linalg.norm(vec) or 1.0)))
            results.append({
                'id': row['id'], 'content_snippet': row['content'][:300],
                'source_type': 'memory', 'vector_score': sim,
                'type': row['type'], 'created_at': row['created_at'],
                'access_count': row['access_count'] or 0,
                'scope': scope, 'department_id': row['department_id'],
            })

        results.sort(key=lambda x: x['vector_score'], reverse=True)
        return results[:top_k]

    # === 关键词检索 — 带权限过滤 ===
    def keyword_search(self, query: str, org_id: str, visible_depts: Set[str],
                       shared_mem_ids: Set[str], user_id: str, top_k: int = 20) -> List[Dict]:
        """简单 LIKE 关键词检索, 已过滤权限"""
        if not query or not query.strip():
            return []
        terms = [t for t in query.split() if t.strip()]
        if not terms:
            return []
        conditions = " OR ".join(["content LIKE ?" for _ in terms])
        params = tuple(f"%{t}%" for t in terms) + (org_id,)
        rows = self.execute(
            f"SELECT id, content, created_at, access_count, scope, department_id, created_by FROM memories WHERE ({conditions}) AND org_id=? AND status='active' LIMIT ?",
            params + (top_k * 3,)
        ).fetchall()

        results = []
        for r in rows:
            scope = r['scope']
            if scope == 'personal' and r['created_by'] != user_id:
                continue
            if scope == 'department' and r['department_id'] not in visible_depts:
                if r['id'] not in shared_mem_ids:
                    continue
            results.append({
                'id': r['id'], 'content_snippet': r['content'][:300], 'source_type': 'memory',
                'keyword_score': 0.5, 'created_at': r['created_at'],
                'access_count': r['access_count'] or 0,
                'scope': scope, 'department_id': r['department_id'],
            })
        return results[:top_k]

    # === 获取最近记忆 — 带权限过滤 ===
    def recent_memories(self, org_id: str, visible_depts: Set[str], shared_mem_ids: Set[str],
                        user_id: str, limit: int = 20) -> List[Dict]:
        """返回最近记忆, 已过滤权限"""
        rows = self.execute(
            "SELECT id, content, type, created_at, access_count, quality_score, scope, department_id, created_by FROM memories WHERE org_id=? AND status='active' ORDER BY created_at DESC LIMIT ?",
            (org_id, limit * 3)
        ).fetchall()

        results = []
        for r in rows:
            scope = r['scope']
            if scope == 'personal' and r['created_by'] != user_id:
                continue
            if scope == 'department' and r['department_id'] not in visible_depts:
                if r['id'] not in shared_mem_ids:
                    continue
            results.append({
                'id': r['id'], 'content_snippet': r['content'][:300],
                'type': r['type'], 'created_at': r['created_at'],
                'access_count': r['access_count'], 'quality_score': r['quality_score'],
                'score': 1.0, 'source_type': 'memory',
                'scope': scope, 'department_id': r['department_id'],
                'score_breakdown': {'vector': 0, 'keyword': 0, 'graph': 0, 'recency': 1.0}
            })
            if len(results) >= limit:
                break
        return results

    # === FTS5 全文搜索 (中文 jieba 分词) ===
    def fts_search(self, query: str, org_id: str, visible_depts: Set[str],
                   shared_mem_ids: Set[str], user_id: str, top_k: int = 20) -> List[Dict]:
        """FTS5 全文搜索 + jieba 分词"""
        if not query or not query.strip():
            return []
        try:
            import jieba
            tokens = " ".join(jieba.cut(query))
        except ImportError:
            tokens = query
        if not tokens.strip():
            return []

        # FTS5 MATCH
        try:
            rows = self.execute(
                "SELECT m.id, m.content, m.created_at, m.access_count, m.scope, m.department_id, m.created_by, m.type "
                "FROM memories_fts f JOIN memories m ON f.memory_id = m.id "
                "WHERE f.content MATCH ? AND m.org_id=? AND m.status='active' LIMIT ?",
                (tokens, org_id, top_k * 3)
            ).fetchall()
        except Exception:
            # FTS5 not available, fall back to LIKE
            return self.keyword_search(query, org_id, visible_depts, shared_mem_ids, user_id, top_k)

        results = []
        for r in rows:
            scope = r['scope']
            if scope == 'personal' and r['created_by'] != user_id:
                continue
            if scope == 'department' and r['department_id'] not in visible_depts:
                if r['id'] not in shared_mem_ids:
                    continue
            results.append({
                'id': r['id'], 'content_snippet': r['content'][:300], 'source_type': 'memory',
                'keyword_score': 0.8, 'created_at': r['created_at'],
                'access_count': r['access_count'] or 0,
                'scope': scope, 'department_id': r['department_id'],
            })
        return results[:top_k]

    # === 记忆冲突检测 (supersede) ===
    def supersede_memory(self, old_id: str, new_id: str):
        """标记旧记忆为被取代"""
        self.execute(
            "UPDATE memories SET status='superseded', superseded_by=? WHERE id=?",
            (new_id, old_id)
        )
        self.commit()

    # === 记忆编辑 ===
    def update_memory(self, memory_id: str, content: str = None, scope: str = None, sensitivity: str = None):
        """更新记忆内容"""
        parts = []
        params = []
        if content is not None:
            parts.append("content=?")
            params.append(content)
            parts.append("summary=?")
            params.append(content[:200])
        if scope is not None:
            parts.append("scope=?")
            params.append(scope)
        if sensitivity is not None:
            parts.append("sensitivity=?")
            params.append(sensitivity)
        if not parts:
            return
        params.append(memory_id)
        self.execute(f"UPDATE memories SET {', '.join(parts)} WHERE id=?", tuple(params))
        self.commit()

    # === 记忆删除 (软删除) ===
    def delete_memory(self, memory_id: str):
        """软删除记忆"""
        self.execute("UPDATE memories SET status='deleted' WHERE id=?", (memory_id,))
        self.commit()

    # === FTS 索引同步 ===
    def index_memory_fts(self, memory_id: str, content: str):
        """将记忆写入 FTS 索引"""
        try:
            self.execute("INSERT INTO memories_fts (memory_id, content) VALUES (?, ?)", (memory_id, content))
            self.commit()
        except Exception:
            pass  # FTS5 may not exist

    # === 审计日志查询 ===
    def get_audit_logs(self, org_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        rows = self.execute(
            "SELECT a.id, a.user_id, u.name as user_name, a.action, a.resource_type, a.resource_id, a.details, a.created_at "
            "FROM audit_logs a LEFT JOIN users u ON a.user_id = u.id "
            "WHERE u.org_id=? ORDER BY a.created_at DESC LIMIT ? OFFSET ?",
            (org_id, limit, offset)
        ).fetchall()
        return [{"id": r['id'], "user_id": r['user_id'], "user_name": r['user_name'],
                 "action": r['action'], "resource_type": r['resource_type'],
                 "resource_id": r['resource_id'], "details": r['details'], "created_at": r['created_at']}
                for r in rows]

    # === 数据导出 ===
    def export_all(self, org_id: str) -> Dict:
        """导出组织所有数据为 JSON (安全: 只导出有 org_id 的表)"""
        tables = {}
        for table in ['organizations', 'departments', 'users', 'memories', 'artifacts']:
            rows = self.execute(f"SELECT * FROM {table} WHERE {'id' if table == 'organizations' else 'org_id'}=?", (org_id,)).fetchall()
            tables[table] = [dict(r) for r in rows]
        # memory_shares: 通过 JOIN memories 过滤
        try:
            share_rows = self.execute(
                "SELECT ms.* FROM memory_shares ms JOIN memories m ON ms.memory_id=m.id WHERE m.org_id=?",
                (org_id,)
            ).fetchall()
            tables['memory_shares'] = [dict(r) for r in share_rows]
        except Exception:
            tables['memory_shares'] = []
        # audit_logs: 通过 JOIN users 过滤
        try:
            log_rows = self.execute(
                "SELECT a.* FROM audit_logs a LEFT JOIN users u ON a.user_id=u.id WHERE u.org_id=?",
                (org_id,)
            ).fetchall()
            tables['audit_logs'] = [dict(r) for r in log_rows]
        except Exception:
            tables['audit_logs'] = []
        return tables

    # === 邀请码 ===
    def create_invite_code(self, org_id: str, department_id: str, role: str, max_uses: int,
                           created_by: str, expires_at: str = None) -> Dict:
        import secrets as _secrets
        code = _secrets.token_urlsafe(8).upper()[:8]
        invite_id = str(__import__('uuid').uuid4())
        self.execute(
            "INSERT INTO invite_codes (id, org_id, code, department_id, role, max_uses, used_count, created_by, expires_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (invite_id, org_id, code, department_id, role, max_uses, 0, created_by, expires_at)
        )
        self.commit()
        return {"id": invite_id, "code": code, "department_id": department_id, "role": role, "max_uses": max_uses}

    def validate_invite_code(self, code: str) -> Dict:
        """验证邀请码, 返回 {valid, org_id, department_id, role} 或 {valid: False}"""
        row = self.execute(
            "SELECT * FROM invite_codes WHERE code=? AND used_count < max_uses",
            (code,)
        ).fetchone()
        if not row:
            return {"valid": False}
        # check expiry
        if row['expires_at']:
            from datetime import datetime
            if datetime.now().isoformat() > row['expires_at']:
                return {"valid": False, "reason": "expired"}
        return {
            "valid": True, "org_id": row['org_id'],
            "department_id": row['department_id'], "role": row['role'],
            "invite_id": row['id']
        }

    def consume_invite_code(self, invite_id: str):
        """邀请码使用次数 +1"""
        self.execute("UPDATE invite_codes SET used_count = used_count + 1 WHERE id=?", (invite_id,))
        self.commit()

    def list_invite_codes(self, org_id: str) -> List[Dict]:
        rows = self.execute(
            "SELECT ic.*, d.name as dept_name FROM invite_codes ic "
            "LEFT JOIN departments d ON ic.department_id = d.id "
            "WHERE ic.org_id=? ORDER BY ic.created_at DESC",
            (org_id,)
        ).fetchall()
        return [{"id": r['id'], "code": r['code'], "department_id": r['department_id'],
                 "dept_name": r['dept_name'], "role": r['role'], "max_uses": r['max_uses'],
                 "used_count": r['used_count'], "created_at": r['created_at']} for r in rows]


def get_db() -> OrgMindDB:
    return OrgMindDB.get()
