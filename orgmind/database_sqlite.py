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

DB_PATH = os.getenv("ORGMIND_DB_PATH", os.path.expanduser("~/.easywiki/easywiki.db"))


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
            self._local.conn.execute("PRAGMA busy_timeout=5000")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn.execute("PRAGMA cache_size=-8000")
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
        -- Phase 2: Clone mount (Trilium-style cross-project knowledge distribution)
        CREATE TABLE IF NOT EXISTS easywiki_clone_mounts (
            id TEXT PRIMARY KEY,
            source_page_id TEXT NOT NULL,
            source_project_id TEXT NOT NULL,
            target_project_id TEXT NOT NULL,
            target_section TEXT NOT NULL,
            mount_parent_page_id TEXT,
            sort_order INTEGER DEFAULT 0,
            created_by TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(source_page_id, target_project_id)
        );
        -- Phase 3: Cross-instance sync
        CREATE TABLE IF NOT EXISTS easywiki_remote_instances (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            auth_token TEXT DEFAULT '',
            sync_enabled INTEGER DEFAULT 1,
            sync_direction TEXT DEFAULT 'pull',
            last_sync_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS easywiki_change_log (
            id TEXT PRIMARY KEY,
            resource_type TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            action TEXT NOT NULL,
            org_id TEXT NOT NULL,
            project_id TEXT,
            content_snapshot TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY, org_id TEXT NOT NULL,
            product_key TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL, name_zh TEXT, description TEXT,
            region TEXT DEFAULT 'overseas', category TEXT, keywords TEXT,
            status TEXT DEFAULT 'active', sort_order INTEGER DEFAULT 0,
            assets TEXT DEFAULT '{}', highlights TEXT DEFAULT '[]',
            specifications TEXT DEFAULT '{}', scenes TEXT DEFAULT '[]',
            cases TEXT DEFAULT '[]', solutions TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS content_templates (
            id TEXT PRIMARY KEY, org_id TEXT NOT NULL,
            name TEXT NOT NULL, article_type TEXT NOT NULL,
            category TEXT, model_family TEXT DEFAULT 'article',
            prompt_template TEXT NOT NULL, description TEXT,
            icon TEXT DEFAULT 'document', created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS generated_outputs (
            id TEXT PRIMARY KEY, org_id TEXT NOT NULL, user_id TEXT NOT NULL,
            article_type TEXT, model_used TEXT, language TEXT DEFAULT 'zh',
            prompt TEXT, content TEXT NOT NULL,
            product_id TEXT, template_id TEXT,
            created_at TEXT DEFAULT (datetime('now'))
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

        # Phase2 additions: version history + document FTS + sort order
        for alter_sql in [
            "CREATE TABLE IF NOT EXISTS version_history (id TEXT PRIMARY KEY, resource_type TEXT NOT NULL, resource_id TEXT NOT NULL, content TEXT NOT NULL, summary TEXT, created_by TEXT, created_at TEXT DEFAULT (datetime('now')))",
            "ALTER TABLE documents ADD COLUMN version INTEGER DEFAULT 1",
            "ALTER TABLE documents ADD COLUMN sort_order INTEGER DEFAULT 0",
            "ALTER TABLE artifacts ADD COLUMN version INTEGER DEFAULT 1",
        ]:
            try:
                self._conn().execute(alter_sql)
            except Exception:
                pass  # Column may already exist
        try:
            c.executescript("""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    doc_id, title, content, tokenize='unicode61'
                );
            """)
        except Exception:
            pass
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
        """用 numpy 计算余弦相似度, 分批处理+内存优化, 已过滤权限"""
        results = []
        q_emb = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_emb) or 1.0

        # H2 fix: batch processing to reduce memory usage
        BATCH_SIZE = 500
        offset = 0
        while True:
            batch = self.execute(
                "SELECT id, content, type, embedding, created_at, access_count, scope, department_id, created_by FROM memories WHERE org_id=? AND embedding IS NOT NULL AND status='active' LIMIT ? OFFSET ?",
                (org_id, BATCH_SIZE, offset)
            ).fetchall()
            if not batch:
                break
            offset += BATCH_SIZE

            for row in batch:
                scope = row['scope']
                if scope == 'personal' and row['created_by'] != user_id:
                    continue
                if scope == 'department' and row['department_id'] not in visible_depts:
                    if row['id'] not in shared_mem_ids:
                        continue
                if scope == 'project':
                    pass

                try:
                    emb = json.loads(row['embedding'])
                    vec = np.array(emb, dtype=np.float32)
                except (json.JSONDecodeError, ValueError):
                    continue
                vec_norm = np.linalg.norm(vec) or 1.0
                sim = float(np.dot(q_emb, vec) / (q_norm * vec_norm))
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
            items = [dict(r) for r in rows]
            # Security: strip hashed_password from users export
            if table == 'users':
                for item in items:
                    item.pop('hashed_password', None)
            tables[table] = items
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

    # ══════════════════════════════════════════════════
    # Phase 1: 备份 + 审计 + 版本历史
    # ══════════════════════════════════════════════════

    def backup_database(self) -> str:
        """WAL checkpoint + 副本写入 backups/ 目录, 保留最近 7 天, 每天最多 1 份"""
        import shutil, time
        backup_dir = os.path.join(os.path.dirname(DB_PATH), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        self._conn().execute("PRAGMA wal_checkpoint(TRUNCATE)")
        today = time.strftime("%Y-%m-%d")
        backup_path = os.path.join(backup_dir, f"easywiki-{today}.db")
        shutil.copy2(DB_PATH, backup_path)
        # 清理 7 天前的备份
        cutoff = time.time() - 7 * 86400
        for f in os.listdir(backup_dir):
            fp = os.path.join(backup_dir, f)
            if f.startswith("easywiki-") and os.path.getmtime(fp) < cutoff:
                os.remove(fp)
        return backup_path

    def write_audit_log(self, user_id: str, action: str, resource_type: str = "", resource_id: str = "", details: dict = None):
        """写入审计日志"""
        import uuid, json
        log_id = str(uuid.uuid4())
        self.execute(
            "INSERT INTO audit_logs (id, user_id, action, resource_type, resource_id, details) VALUES (?,?,?,?,?,?)",
            (log_id, user_id or "", action, resource_type, resource_id or "", json.dumps(details or {}, ensure_ascii=False))
        )
        self.commit()

    # NOTE: get_audit_logs is defined above with org_id filtering + pagination.
    # The duplicate definition that was here (without org_id filter) has been removed
    # to prevent it from silently overriding the correct version.

    def create_version_snapshot(self, resource_type: str, resource_id: str, content: str, user_id: str, summary: str = ""):
        """保存文档/artifact历史版本"""
        import uuid
        vid = str(uuid.uuid4())
        self.execute(
            "INSERT INTO version_history (id, resource_type, resource_id, content, created_by, summary) VALUES (?,?,?,?,?,?)",
            (vid, resource_type, resource_id, content, user_id, summary)
        )
        self.commit()
        # 每个资源最多保留 20 个版本
        self.execute("""
            DELETE FROM version_history WHERE id IN (
                SELECT id FROM version_history WHERE resource_type=? AND resource_id=?
                ORDER BY created_at DESC LIMIT -1 OFFSET 20
            )
        """, (resource_type, resource_id))
        self.commit()

    def list_versions(self, resource_type: str, resource_id: str) -> List[Dict]:
        rows = self.execute(
            "SELECT v.*, u.name as user_name FROM version_history v LEFT JOIN users u ON v.created_by = u.id "
            "WHERE v.resource_type=? AND v.resource_id=? ORDER BY v.created_at DESC LIMIT 20",
            (resource_type, resource_id)
        ).fetchall()
        return [dict(r) for r in rows]

    def restore_version(self, version_id: str) -> Optional[Dict]:
        row = self.execute("SELECT * FROM version_history WHERE id=?", (version_id,)).fetchone()
        return dict(row) if row else None

    # ══════════════════════════════════════════════════
    # Phase 2: 全文搜索 (FTS5)
    # ══════════════════════════════════════════════════

    def add_document_fts(self, doc_id: str, title: str, content: str):
        """将文档内容加入 FTS5 索引"""
        # 中文分词由 jieba 预处理, 这里先存原始内容
        try:
            self.execute("INSERT INTO documents_fts (doc_id, title, content) VALUES (?,?,?)",
                         (doc_id, title, content))
            self.commit()
        except Exception:
            pass

    def search_documents(self, org_id: str, query: str, limit: int = 20) -> List[Dict]:
        """FTS5 全文搜索文档"""
        try:
            rows = self.execute("""
                SELECT f.rank, d.id, d.title, d.doc_type, d.scope, d.created_by,
                       snippet(documents_fts, 1, '<b>', '</b>', '...', 60) as snippet,
                       u.name as author_name
                FROM documents_fts f
                JOIN documents d ON f.doc_id = d.id
                LEFT JOIN users u ON d.created_by = u.id
                WHERE d.org_id = ? AND documents_fts MATCH ?
                ORDER BY rank LIMIT ?
            """, (org_id, query, limit)).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            # FTS5 不可用时回退到 LIKE 搜索
            like_q = f"%{query}%"
            rows = self.execute(
                "SELECT d.*, u.name as author_name FROM documents d LEFT JOIN users u ON d.created_by=u.id "
                "WHERE d.org_id=? AND (d.title LIKE ? OR d.storage_key LIKE ?) ORDER BY d.created_at DESC LIMIT ?",
                (org_id, like_q, like_q, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    # ══════════════════════════════════════════════════
    # Phase 3: 输入安全 sanitize
    # ══════════════════════════════════════════════════

    @staticmethod
    def sanitize_html(raw_html: str) -> str:
        """移除危险 HTML 标签和属性, 保留安全内容"""
        import re
        if not raw_html:
            return ""
        # 移除 <script>, <iframe>, <object>, <embed>, <link>, <style>
        raw_html = re.sub(r'</?(script|iframe|object|embed|link|style|meta|form|input|button)\b[^>]*>', '', raw_html, flags=re.IGNORECASE)
        # 移除 on* 事件属性
        raw_html = re.sub(r'\s+on\w+\s*=\s*"[^"]*"', '', raw_html)
        raw_html = re.sub(r"\s+on\w+\s*=\s*'[^']*'", '', raw_html)
        # 移除 javascript: 伪协议
        raw_html = re.sub(r'href\s*=\s*["\']\s*javascript:', 'href="', raw_html, flags=re.IGNORECASE)
        return raw_html

    # ══════════════════════════════════════════════════
    # Phase 4: 并发乐观锁
    # ══════════════════════════════════════════════════

    def update_with_lock(self, table: str, resource_id: str, updates: Dict[str, any], expected_version: int, id_field: str = "id") -> Tuple[bool, int]:
        """乐观锁更新：只有版本号匹配时才更新, 返回 (成功, 新版本号)"""
        current = self.execute(f"SELECT version FROM {table} WHERE {id_field}=?", (resource_id,)).fetchone()
        if not current:
            return False, 0
        if current['version'] != expected_version:
            return False, current['version']  # 冲突, 返回当前版本

        new_version = expected_version + 1
        set_clause = ", ".join([f"{k}=?" for k in updates.keys()])
        values = list(updates.values()) + [new_version, resource_id]
        self.execute(f"UPDATE {table} SET {set_clause}, version=?, updated_at=datetime('now') WHERE {id_field}=? AND version=?", values + [expected_version])
        self.commit()
        return True, new_version

    # ══════════════════════════════════════════════════
    # Phase 5: 限流 (Token Bucket)
    # ══════════════════════════════════════════════════
    _rate_limits: Dict[str, Tuple[float, int]] = {}  # key → (last_refill_ts, tokens)

    def check_rate_limit(self, key: str, max_tokens: int = 60, refill_rate: int = 60) -> bool:
        """Token bucket限流: 默认60次/分钟"""
        import time as _time
        now = _time.time()
        if key not in self._rate_limits:
            self._rate_limits[key] = (now, max_tokens - 1)
            return True
        last_refill, tokens = self._rate_limits[key]
        refill = (now - last_refill) * (refill_rate / 60)
        tokens = min(max_tokens, tokens + refill)
        if tokens < 1:
            return False
        self._rate_limits[key] = (now, tokens - 1)
        return True

    # ══════════════════════════════════════════════════
    # Phase 6: 文档模板
    # ══════════════════════════════════════════════════
    def seed_templates(self, org_id: str, admin_id: str):
        """为新组织注入预置文档模板"""
        import uuid
        templates = [
            {"type": "knowledge", "title": "团队知识库", "content": "# 团队知识库\n\n## 新人入职\n- 账号开通清单\n- 开发环境配置\n- 常用工具和链接\n\n## 技术文档\n- 架构设计\n- API 文档\n- 部署流程\n\n## 会议记录\n- 周会纪要模板"},
            {"type": "project", "title": "项目管理制度", "content": "# 项目管理制度\n\n## 项目启动\n- 需求评审流程\n- 技术方案模板\n- 排期与里程碑\n\n## 日常管理\n- 每日站会\n- 周报模板\n- 风险跟踪"},
            {"type": "hr", "title": "人事行政", "content": "# 人事行政\n\n## 考勤与休假\n- 请假流程\n- 加班政策\n\n## 报销流程\n- 差旅报销\n- 采购报销\n\n## 培训发展\n- 内部培训计划\n- 外部学习资源"},
        ]
        for t in templates:
            doc_id = str(uuid.uuid4())
            self.execute(
                "INSERT INTO documents (id, org_id, title, doc_type, storage_key, content_hash, scope, status, created_by) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (doc_id, org_id, t['title'], t['type'], t['content'], org_id, 'department', 'active', admin_id)
            )
            self.add_document_fts(doc_id, t['title'], t['content'])
            self.write_audit_log(admin_id, 'seed_template', 'document', doc_id, {'title': t['title']})
        self.commit()

    # ══════════════════════════════════════════════════
    # Phase 7: 拖拽排序
    # ══════════════════════════════════════════════════
    def reorder_documents(self, org_id: str, doc_orders: List[Tuple[str, int]]):
        """批量更新文档排序位置"""
        for doc_id, order in doc_orders:
            self.execute("UPDATE documents SET sort_order=? WHERE id=? AND org_id=?", (order, doc_id, org_id))
        self.commit()

    # ══════════════════════════════════════════════════
    # Phase 8: 通知 Webhook
    # ══════════════════════════════════════════════════
    _webhook_urls: Dict[str, str] = {}

    def set_webhook(self, org_id: str, url: str):
        self._webhook_urls[org_id] = url

    def send_notification(self, org_id: str, event: str, payload: dict):
        """向组织的 webhook URL 发送事件通知"""
        import json, urllib.request
        url = self._webhook_urls.get(org_id)
        if not url:
            return
        try:
            data = json.dumps({"event": event, "payload": payload, "org_id": org_id, "timestamp": __import__('datetime').datetime.now().isoformat()}).encode()
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass

    # ══════════════════════════════════════════════════
    # Phase 2: Clone Mount —跨项目知识分发
    # ══════════════════════════════════════════════════

    def create_clone_mount(self, source_page_id: str, target_project_id: str,
                           target_section: str, user_id: str,
                           mount_parent_page_id: str = None) -> Dict:
        """将页面克隆挂载到另一个项目 — Trilium-style"""
        import uuid as _uuid
        src = self.execute(
            "SELECT id, project_id FROM easywiki_pages WHERE id=?",
            (source_page_id,)
        ).fetchone()
        if not src:
            raise ValueError("Source page not found")

        mount_id = str(_uuid.uuid4())
        self.execute(
            "INSERT OR IGNORE INTO easywiki_clone_mounts "
            "(id, source_page_id, source_project_id, target_project_id, "
            "target_section, mount_parent_page_id, created_by) "
            "VALUES (?,?,?,?,?,?,?)",
            (mount_id, source_page_id, src['project_id'], target_project_id,
             target_section, mount_parent_page_id, user_id)
        )
        self.commit()
        self._write_change_log('clone_mount', mount_id, 'create', '', target_project_id)
        return {"id": mount_id, "source_page_id": source_page_id,
                "target_project_id": target_project_id, "target_section": target_section}

    def remove_clone_mount(self, mount_id: str) -> bool:
        row = self.execute("SELECT id FROM easywiki_clone_mounts WHERE id=?", (mount_id,)).fetchone()
        if not row:
            return False
        self.execute("DELETE FROM easywiki_clone_mounts WHERE id=?", (mount_id,))
        self.commit()
        self._write_change_log('clone_mount', mount_id, 'delete', '', '')
        return True

    def list_clone_mounts(self, project_id: str, as_source: bool = False) -> List[Dict]:
        """列出项目的克隆挂载: as_source=True返回此项目作为来源的挂载, 否则返回接收的挂载"""
        if as_source:
            rows = self.execute(
                "SELECT cm.*, p.title as page_title "
                "FROM easywiki_clone_mounts cm "
                "JOIN easywiki_pages p ON cm.source_page_id = p.id "
                "WHERE cm.source_project_id=?",
                (project_id,)
            ).fetchall()
        else:
            rows = self.execute(
                "SELECT cm.*, p.title as page_title, p.project_id as source_project_ref "
                "FROM easywiki_clone_mounts cm "
                "JOIN easywiki_pages p ON cm.source_page_id = p.id "
                "WHERE cm.target_project_id=?",
                (project_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_cloned_pages_for_project(self, project_id: str, section: str = None) -> List[Dict]:
        """获取通过克隆挂载注入到项目的页面列表（用于页面列表查询）"""
        sql = (
            "SELECT p.*, cm.id as mount_id, cm.source_project_id "
            "FROM easywiki_clone_mounts cm "
            "JOIN easywiki_pages p ON cm.source_page_id = p.id "
            "WHERE cm.target_project_id=?"
        )
        params = [project_id]
        if section:
            sql += " AND cm.target_section=?"
            params.append(section)
        rows = self.execute(sql, tuple(params)).fetchall()
        return [dict(r) for r in rows]

    # ══════════════════════════════════════════════════
    # Phase 3: 跨实例同步 — remote_instances + change_log + import/export
    # ══════════════════════════════════════════════════

    def _write_change_log(self, resource_type: str, resource_id: str, action: str,
                          org_id: str, project_id: str = "", content_snapshot: dict = None):
        import uuid as _uuid, json as _json
        log_id = str(_uuid.uuid4())
        snap = _json.dumps(content_snapshot, ensure_ascii=False) if content_snapshot else None
        self.execute(
            "INSERT INTO easywiki_change_log (id, resource_type, resource_id, action, org_id, project_id, content_snapshot) "
            "VALUES (?,?,?,?,?,?,?)",
            (log_id, resource_type, resource_id, action, org_id, project_id or "", snap)
        )
        self.commit()

    def get_change_log(self, org_id: str, since: str = None, limit: int = 200) -> List[Dict]:
        """获取变更日志，支持增量导出(since参数)"""
        if since:
            rows = self.execute(
                "SELECT * FROM easywiki_change_log WHERE org_id=? AND created_at > ? "
                "ORDER BY created_at ASC LIMIT ?",
                (org_id, since, limit)
            ).fetchall()
        else:
            rows = self.execute(
                "SELECT * FROM easywiki_change_log WHERE org_id=? "
                "ORDER BY created_at DESC LIMIT ?",
                (org_id, limit)
            ).fetchall()
        return [dict(r) for r in rows]

    def add_remote_instance(self, name: str, url: str, auth_token: str = "",
                            sync_direction: str = "pull") -> Dict:
        import uuid as _uuid
        rid = str(_uuid.uuid4())
        self.execute(
            "INSERT INTO easywiki_remote_instances (id, name, url, auth_token, sync_direction) "
            "VALUES (?,?,?,?,?)",
            (rid, name, url.rstrip('/'), auth_token, sync_direction)
        )
        self.commit()
        return {"id": rid, "name": name, "url": url.rstrip('/'), "sync_direction": sync_direction}

    def list_remote_instances(self) -> List[Dict]:
        rows = self.execute(
            "SELECT * FROM easywiki_remote_instances ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def remove_remote_instance(self, rid: str) -> bool:
        row = self.execute("SELECT id FROM easywiki_remote_instances WHERE id=?", (rid,)).fetchone()
        if not row:
            return False
        self.execute("DELETE FROM easywiki_remote_instances WHERE id=?", (rid,))
        self.commit()
        return True

    def update_remote_sync_time(self, rid: str):
        self.execute(
            "UPDATE easywiki_remote_instances SET last_sync_at=datetime('now') WHERE id=?",
            (rid,)
        )
        self.commit()

    def import_org_data(self, data: dict, target_org_id: str, user_mapping: dict = None) -> Dict:
        """导入另一个实例导出的组织数据，处理ID重映射和冲突检测"""
        import uuid as _uuid, json as _json
        stats = {"imported": 0, "skipped": 0, "errors": 0}
        user_map = user_mapping or {}

        id_map = {}  # old_id → new_id

        for table_name in ['memories', 'artifacts', 'documents']:
            items = data.get(table_name, [])
            for item in items:
                old_id = item.get('id', '')
                new_id = str(_uuid.uuid4())
                id_map[old_id] = new_id

                # Skip if content hash already exists
                if item.get('content_hash'):
                    existing = self.execute(
                        "SELECT id FROM memories WHERE content_hash=? AND org_id=?",
                        (item['content_hash'], target_org_id)
                    ).fetchone()
                    if existing:
                        stats['skipped'] += 1
                        continue

                # Map creator to local user if possible
                creator = item.get('created_by', '')
                if creator and creator in user_map:
                    creator = user_map[creator]

                try:
                    if table_name == 'memories':
                        self.execute(
                            "INSERT OR IGNORE INTO memories "
                            "(id, org_id, department_id, type, scope, content, summary, "
                            "content_hash, sensitivity, importance, status, created_by) "
                            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                            (new_id, target_org_id, item.get('department_id', ''),
                             item.get('type', 'general'), item.get('scope', 'department'),
                             item.get('content', ''), item.get('summary', ''),
                             item.get('content_hash', ''), item.get('sensitivity', 'normal'),
                             item.get('importance', 0.5), 'active', creator)
                        )
                        stats['imported'] += 1
                    elif table_name == 'artifacts':
                        self.execute(
                            "INSERT OR IGNORE INTO artifacts "
                            "(id, org_id, object_type, name, description, content, "
                            "version, status, scope, author_id) "
                            "VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (new_id, target_org_id, item.get('object_type', 'skill'),
                             item.get('name', ''), item.get('description', ''),
                             item.get('content', ''), item.get('version', '1'),
                             'draft', item.get('scope', 'department'), creator)
                        )
                        stats['imported'] += 1
                except Exception as e:
                    stats['errors'] += 1

        self.commit()
        self._write_change_log('org_import', target_org_id, 'import',
                               target_org_id, '', {'stats': stats})
        return stats

    def export_org_incremental(self, org_id: str, since: str = None) -> Dict:
        """增量导出：since参数指定起始时间戳，返回该时间之后的新增/修改数据"""
        data = {"org_id": org_id, "exported_at": __import__('datetime').datetime.now().isoformat()}
        if since:
            data['since'] = since
            data['is_incremental'] = True
        else:
            data['is_incremental'] = False

        for table in ['memories', 'artifacts']:
            if since:
                rows = self.execute(
                    f"SELECT * FROM {table} WHERE org_id=? AND created_at > ?",
                    (org_id, since)
                ).fetchall()
            else:
                rows = self.execute(
                    f"SELECT * FROM {table} WHERE org_id=?",
                    (org_id,)
                ).fetchall()
            data[table] = [dict(r) for r in rows]

        # Include change log entries for incremental
        data['change_log'] = self.get_change_log(org_id, since)
        return data

    def sync_from_remote(self, remote_instance: dict) -> Dict:
        """从远程实例拉取数据"""
        import urllib.request, json as _json

        url = remote_instance['url'].rstrip('/')
        token = remote_instance.get('auth_token', '')
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        last_sync = remote_instance.get('last_sync_at', '')
        export_url = f"{url}/api/v1/org/export"
        if last_sync:
            export_url += f"?since={last_sync}"

        try:
            req = urllib.request.Request(export_url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=30)
            data = _json.loads(resp.read().decode())
        except Exception as e:
            return {"success": False, "error": str(e)}

        # We need the target org_id — use the first org
        org_row = self.execute("SELECT id FROM organizations LIMIT 1").fetchone()
        if not org_row:
            return {"success": False, "error": "No local organization found"}
        target_org_id = org_row['id']

        stats = self.import_org_data(data, target_org_id)
        self.update_remote_sync_time(remote_instance['id'])
        self._write_change_log('sync_pull', remote_instance['id'], 'sync_pull',
                               target_org_id, '', {'remote': remote_instance['name'], 'stats': stats})
        return {"success": True, "stats": stats}

    def push_to_remote(self, remote_instance: dict, org_id: str) -> Dict:
        """向远程实例推送本地数据"""
        import urllib.request, json as _json

        url = remote_instance['url'].rstrip('/')
        token = remote_instance.get('auth_token', '')
        last_sync = remote_instance.get('last_sync_at', '')
        export_data = self.export_org_incremental(org_id, last_sync)

        try:
            data_bytes = _json.dumps(export_data, ensure_ascii=False).encode('utf-8')
            headers = {'Content-Type': 'application/json'}
            if token:
                headers['Authorization'] = f'Bearer {token}'
            req = urllib.request.Request(f"{url}/api/v1/org/import", data=data_bytes,
                                         headers=headers, method='POST')
            resp = urllib.request.urlopen(req, timeout=30)
            result = _json.loads(resp.read().decode())
        except Exception as e:
            return {"success": False, "error": str(e)}

        self.update_remote_sync_time(remote_instance['id'])
        self._write_change_log('sync_push', remote_instance['id'], 'sync_push',
                               org_id, '', {'remote': remote_instance['name']})
        return {"success": True, "result": result}


def get_db() -> OrgMindDB:
    return OrgMindDB.get()
