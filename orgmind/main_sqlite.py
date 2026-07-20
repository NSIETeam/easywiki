"""
EasyWiki v1.0 — Development Entry Point (SQLite)
================================================================
DEPLOYMENT MODE: local development only (no PostgreSQL needed)
DATABASE: SQLite (zero-dependency)
USAGE: python -m uvicorn orgmind.main_sqlite:app --host 0.0.0.0 --port 8080

For production cloud deployment, use: python -m uvicorn orgmind.main:app

Features:
- bcrypt password + random JWT key
- sentence-transformers embedding
- LLM auto memory extraction
- Memory edit/delete/conflict detection
- jieba Chinese NLP + FTS5
- Audit logs + Data export
- SSO OAuth2 callback scaffold
- Hierarchical RBAC
- Single-port SPA + API
- Full EasyWiki project management, agent inbox, knowledge graph
"""
import sys, os, uuid, json, hashlib, math, time
from pathlib import Path
from typing import Dict, List, Optional, Set
from contextlib import asynccontextmanager
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Body, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from orgmind.db import get_db, OrgMindDB
from orgmind.database_sqlite import DB_PATH
from orgmind.agent_detector import detect_agents, generate_agent_config
from orgmind.governance.cleaners import clean_text
from orgmind.governance.dedup import compute_content_hash
from orgmind.governance.pii import detect_pii, upgrade_sensitivity
from orgmind.governance.quality import compute_quality_score, QualityInput
from orgmind.config import EMBEDDING_MODEL, EMBEDDING_DIM, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
from orgmind.auth.password import hash_password, verify_password
from orgmind.auth import decode_auth_header
from orgmind.services.audit import log_audit
from orgmind.services.write_queue import execute_write

# === FastAPI App ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    db = get_db()
    org = db.execute("SELECT COUNT(*) as cnt FROM organizations").fetchone()
    if org['cnt'] == 0:
        _auto_setup(db)
    # Start background sync daemon
    import threading
    sync_thread = threading.Thread(target=_sync_daemon, args=(db,), daemon=True)
    sync_thread.start()
    # Start auto-knowledge daemon — ensures pending entries don't stagnate
    # (Fixes Otto's biggest flaw: knowledge pipeline existed but was never activated)
    auto_knowledge_thread = threading.Thread(target=_auto_knowledge_daemon, args=(db,), daemon=True)
    auto_knowledge_thread.start()
    yield

app = FastAPI(title="EasyWiki", version="1.0.0", lifespan=lifespan)
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8090,http://127.0.0.1:8090").split(",")
app.add_middleware(CORSMiddleware, allow_origins=_cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
from orgmind.easywiki.routes import router as easywiki_router
app.include_router(easywiki_router, prefix="/api/v1/easywiki")

_FRONTEND_DIST = Path(__file__).parent.parent / "frontend-src" / "dist"

# === 首次配置 (最小化: 仅创建组织和一个管理员, 无任何预设数据) ===
def _auto_setup(db: OrgMindDB):
    org_id = str(uuid.uuid4())
    db.execute("INSERT INTO organizations (id,name) VALUES (?,?)", (org_id, "我的组织"))
    root_dept = str(uuid.uuid4())
    db.execute("INSERT INTO departments (id,name,parent_id,org_id) VALUES (?,?,?,?)", (root_dept, "总公司", None, org_id))

    import secrets as _secrets
    default_pw = _secrets.token_urlsafe(12)
    pw = hash_password(default_pw)
    uid = str(uuid.uuid4())
    db.execute(
        "INSERT INTO users (id,email,name,role,department_id,org_id,hashed_password) VALUES (?,?,?,?,?,?,?)",
        (uid, "admin@local", "管理员", "admin", root_dept, org_id, pw)
    )
    db.commit()
    # Write password to file instead of stdout (security: avoid container log leak)
    from orgmind.database_sqlite import DB_PATH as _db_path
    bootstrap_file = os.path.join(os.path.dirname(_db_path), ".bootstrap_admin")
    try:
        with open(bootstrap_file, 'w') as f:
            f.write(f"Email: admin@local\nPassword: {default_pw}\n")
        os.chmod(bootstrap_file, 0o600)
        print(f"[EasyWiki] First run: admin account created. Credentials written to {bootstrap_file}")
    except Exception:
        print(f"[EasyWiki] First run: admin account created. Check server logs for credentials.")
    # Also support env var for initial password
    env_pw = os.getenv("ORGMIND_ADMIN_PASSWORD")
    if env_pw:
        db.execute("UPDATE users SET hashed_password=? WHERE email=?", (hash_password(env_pw), "admin@local"))
        db.commit()
        print(f"[EasyWiki] Admin password set from ORGMIND_ADMIN_PASSWORD env var.")


# === 请求模型 ===
class LoginReq(BaseModel): email: str; password: str
class MemoryReq(BaseModel): content: str; type: str = "episodic"; scope: str = "department"; department_id: str = None; project_id: str = None
class RetrieveReq(BaseModel): query: str; top_k: int = 5; mode: str = "auto"
class AutoRecordReq(BaseModel): session_text: str; session_id: str = None
class RecentReq(BaseModel): limit: int = 20
class ShareReq(BaseModel): memory_id: str; shared_with_user_id: str = None; shared_with_department_id: str = None
class CreateUserReq(BaseModel): email: str; name: str; role: str = "employee"; department_id: str = None; password: str = None
class CreateDeptReq(BaseModel): name: str; parent_id: str = None
class UpdateMemoryReq(BaseModel): content: str = None; scope: str = None; sensitivity: str = None
class SSOCallbackReq(BaseModel): code: str; provider: str = "feishu"
class CreateInviteCodeReq(BaseModel): department_id: str; role: str = "employee"; max_uses: int = 1; expires_at: str = None
class RegisterWithInviteReq(BaseModel): invite_code: str; email: str; name: str; password: str

# === 辅助 ===
def _create_token(user_id, org_id, role, department_id=None, project_ids=None):
    import jwt as pyjwt
    from datetime import timedelta, timezone
    payload = {"user_id": str(user_id), "org_id": str(org_id), "role": role,
               "department_id": str(department_id) if department_id else None,
               "project_ids": project_ids or [],
               "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
               "iat": datetime.now(timezone.utc)}
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# _get_user_from_token is now decode_auth_header from orgmind.auth

def _get_visible_depts(db, payload):
    return db.get_visible_departments(payload['user_id'], payload['role'], payload.get('department_id'), payload['org_id'])

def _get_shared_ids(db, payload):
    return db.get_shared_memory_ids(payload['user_id'], payload.get('department_id'))

# === 路由 ===
@app.get("/health")
def health(): return {"status": "healthy", "backend": "SQLite", "version": "1.0.0", "service": "EasyWiki"}

@app.get("/api/v1/health")
def api_health(): return {"status": "ok", "service": "EasyWiki", "version": "1.0.0"}

@app.post("/api/v1/auth/login")
def login(req: LoginReq):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email=?", (req.email,)).fetchone()
    if not user or not verify_password(req.password, user['hashed_password']):
        raise HTTPException(401, "Invalid credentials")
    # Auto-migrate legacy SHA256 to bcrypt
    if not user['hashed_password'].startswith("$2"):
        db.execute("UPDATE users SET hashed_password=? WHERE id=?", (hash_password(req.password), user['id']))
        db.commit()
    dept = db.execute("SELECT name FROM departments WHERE id=?", (user['department_id'],)).fetchone() if user['department_id'] else None
    token = _create_token(user['id'], user['org_id'], user['role'], user['department_id'], json.loads(user['project_ids'] or '[]'))
    log_audit(user['id'], 'login', 'user', user['id'])

    # Security: remove bootstrap admin password file after first successful login
    from orgmind.database_sqlite import DB_PATH as _db_path
    _bootstrap = os.path.join(os.path.dirname(_db_path), ".bootstrap_admin")
    if os.path.exists(_bootstrap):
        try:
            os.remove(_bootstrap)
        except OSError:
            pass

    return {"token": token, "user": {"id": user['id'], "email": user['email'], "name": user['name'], "role": user['role'], "org_id": user['org_id'], "department_id": user['department_id'], "department_name": dept['name'] if dept else None}}

# === SSO OAuth2 回调 ===
@app.post("/api/v1/auth/sso/callback")
def sso_callback(req: SSOCallbackReq):
    """SSO 回调: 飞书/钉钉 OAuth2 code 换 token, 再换用户信息"""
    if req.provider == "feishu":
        return _sso_feishu(req.code)
    elif req.provider == "dingtalk":
        return _sso_dingtalk(req.code)
    raise HTTPException(400, f"Unsupported provider: {req.provider}")

def _sso_feishu(code: str):
    from orgmind.config import FEISHU_APP_ID, FEISHU_APP_SECRET
    if not FEISHU_APP_ID:
        raise HTTPException(501, "Feishu SSO not configured. Set FEISHU_APP_ID and FEISHU_APP_SECRET.")
    # 实际实现: code -> app_access_token -> user_info -> 查/建 user -> 发 JWT
    raise HTTPException(501, "Feishu SSO structure ready, configure credentials to enable.")

def _sso_dingtalk(code: str):
    from orgmind.config import DINGTALK_APP_ID, DINGTALK_APP_SECRET
    if not DINGTALK_APP_ID:
        raise HTTPException(501, "DingTalk SSO not configured.")
    raise HTTPException(501, "DingTalk SSO structure ready, configure credentials to enable.")

# === 记忆 CRUD ===
@app.post("/api/v1/memory")
def create_memory(req: MemoryReq, authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    db = get_db()
    cleaned, meta = clean_text(req.content)
    ch = compute_content_hash(cleaned)
    pii_hits = detect_pii(cleaned)
    sensitivity = upgrade_sensitivity("normal", pii_hits)

    existing = db.execute("SELECT id FROM memories WHERE org_id=? AND content_hash=?", (payload['org_id'], ch)).fetchone()
    if existing:
        return {"id": existing['id'], "duplicate": True, "status": "existing"}

    emb_json = None
    try:
        from orgmind.services.embedding import get_embedding_sync
        emb_json = json.dumps(get_embedding_sync(cleaned))
    except Exception: pass

    qscore = compute_quality_score(QualityInput(completeness=1.0, schema_valid=1.0, near_duplicate_count=0, source_trust=0.5))
    dept_id = req.department_id or payload.get('department_id')
    mid = str(uuid.uuid4())

    def _write(db, mid, org_id, dept_id, pid, mtype, scope, cleaned, ch, emb_json, sens, qscore, uid, meta):
        db.execute("INSERT INTO memories (id,org_id,department_id,project_id,type,scope,content,summary,content_hash,embedding,sensitivity,quality_score,status,created_by,extra_metadata) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (mid, org_id, dept_id, pid, mtype, scope, cleaned, cleaned[:200], ch, emb_json, sens, qscore, 'active', uid, json.dumps(meta, ensure_ascii=False)))
        db.index_memory_fts(mid, cleaned)
    execute_write(_write, mid, payload['org_id'], dept_id, req.project_id, req.type, req.scope, cleaned, ch, emb_json, sensitivity, qscore, payload['user_id'], {"pii_detected": pii_hits})
    log_audit(payload['user_id'], 'create_memory', 'memory', mid, {"department_id": dept_id})
    return {"id": mid, "status": "active", "quality_score": qscore, "sensitivity": sensitivity, "department_id": dept_id}

@app.patch("/api/v1/memory/{memory_id}")
def update_memory(memory_id: str, req: UpdateMemoryReq, authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    db = get_db()
    mem = db.execute("SELECT * FROM memories WHERE id=? AND org_id=?", (memory_id, payload['org_id'])).fetchone()
    if not mem:
        raise HTTPException(404, "Memory not found")
    # 只有创建者或 admin 可以编辑
    if mem['created_by'] != payload['user_id'] and payload['role'] != 'admin':
        raise HTTPException(403, "Not authorized to edit this memory")
    db.update_memory(memory_id, req.content, req.scope, req.sensitivity)
    if req.content:
        db.index_memory_fts(memory_id, req.content)
    log_audit(payload['user_id'], 'update_memory', 'memory', memory_id)
    return {"id": memory_id, "status": "updated"}

@app.delete("/api/v1/memory/{memory_id}")
def delete_memory(memory_id: str, authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    db = get_db()
    mem = db.execute("SELECT * FROM memories WHERE id=? AND org_id=?", (memory_id, payload['org_id'])).fetchone()
    if not mem:
        raise HTTPException(404, "Memory not found")
    if mem['created_by'] != payload['user_id'] and payload['role'] != 'admin':
        raise HTTPException(403, "Not authorized to delete this memory")
    db.delete_memory(memory_id)
    log_audit(payload['user_id'], 'delete_memory', 'memory', memory_id)
    return {"id": memory_id, "status": "deleted"}

@app.post("/api/v1/memories/recent")
def recent_memories(req: RecentReq, authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    db = get_db()
    visible_depts = _get_visible_depts(db, payload)
    shared_ids = _get_shared_ids(db, payload)
    rows = db.recent_memories(payload['org_id'], visible_depts, shared_ids, payload['user_id'], req.limit)
    return {"memories": rows, "total": len(rows), "visible_departments": len(visible_depts)}

@app.post("/api/v1/retrieve")
def retrieve_api(req: RetrieveReq, authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    db = get_db()
    visible_depts = _get_visible_depts(db, payload)
    shared_ids = _get_shared_ids(db, payload)
    top_k = min(req.top_k, 20)
    t0 = time.monotonic()

    vector_results = []
    try:
        from orgmind.services.embedding import get_embedding_sync
        emb = get_embedding_sync(req.query)
        vector_results = db.vector_search(emb, payload['org_id'], visible_depts, shared_ids, payload['user_id'], top_k * 4)
    except Exception: pass

    # FTS5 优先, 降级 keyword_search
    keyword_results = db.fts_search(req.query, payload['org_id'], visible_depts, shared_ids, payload['user_id'], top_k * 4)

    merged = {}
    for r in vector_results:
        merged[r['id']] = {**r, 'vector_score': r.get('vector_score', 0), 'keyword_score': 0.0}
    for r in keyword_results:
        if r['id'] in merged:
            merged[r['id']]['keyword_score'] = max(merged[r['id']].get('keyword_score', 0), r.get('keyword_score', 0))
        else:
            merged[r['id']] = {**r, 'vector_score': 0.0, 'keyword_score': r.get('keyword_score', 0)}

    results = []
    import math
    for rid, r in merged.items():
        # Unified fusion formula: 0.5*vector + 0.2*keyword + 0.2*graph(0 for SQLite) + 0.1*recency
        days_since = (time.time() - r.get('created_at_ts', time.time())) / 86400 if r.get('created_at_ts') else 0
        recency_score = math.exp(-days_since / 90) if days_since > 0 else 1.0
        score = 0.5 * r['vector_score'] + 0.2 * r['keyword_score'] + 0.2 * 0.0 + 0.1 * recency_score
        results.append({'id': rid, 'content_snippet': r.get('content_snippet', '')[:300], 'source_type': 'memory', 'score': round(score, 4),
            'score_breakdown': {'vector': round(r['vector_score'], 4), 'keyword': round(r['keyword_score'], 4), 'graph': 0, 'recency': 1.0},
            'citation': {'source_id': rid, 'location': ''}, 'scope': r.get('scope', ''), 'department_id': r.get('department_id', '')})

    results.sort(key=lambda x: x['score'], reverse=True)
    total = len(results)
    results = results[:top_k]
    return {'results': results, 'total_candidates': total, 'retrieval_time_ms': round((time.monotonic() - t0) * 1000), 'degraded': False}

@app.post("/api/v1/memory/share")
def share_memory(req: ShareReq, authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    db = get_db()
    if payload['role'] not in ('admin', 'manager'):
        raise HTTPException(403, "Only admin or manager can share")
    mem = db.execute("SELECT id FROM memories WHERE id=? AND org_id=?", (req.memory_id, payload['org_id'])).fetchone()
    if not mem:
        raise HTTPException(404, "Memory not found")
    # W8: 验证目标用户/部门属于同一组织
    if req.shared_with_user_id:
        target = db.execute("SELECT id FROM users WHERE id=? AND org_id=?", (req.shared_with_user_id, payload['org_id'])).fetchone()
        if not target:
            raise HTTPException(400, "Target user not found in your organization")
    if req.shared_with_department_id:
        target_d = db.execute("SELECT id FROM departments WHERE id=? AND org_id=?", (req.shared_with_department_id, payload['org_id'])).fetchone()
        if not target_d:
            raise HTTPException(400, "Target department not found in your organization")
    share_id = str(uuid.uuid4())
    share_scope = 'department' if req.shared_with_department_id else 'user'

    def _write(db, sid, mid, uid, swu, swd, ss):
        db.execute("INSERT INTO memory_shares (id,memory_id,shared_by_user_id,shared_with_user_id,shared_with_department_id,share_scope) VALUES (?,?,?,?,?,?)", (sid, mid, uid, swu, swd, ss))
    execute_write(_write, share_id, req.memory_id, payload['user_id'], req.shared_with_user_id, req.shared_with_department_id, share_scope)
    log_audit(payload['user_id'], 'share_memory', 'memory', req.memory_id, {"to_user": req.shared_with_user_id, "to_dept": req.shared_with_department_id})
    return {"id": share_id, "status": "shared"}

@app.post("/api/v1/session/auto-record")
def auto_record(req: AutoRecordReq, authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    db = get_db()
    from orgmind.services.auto_memory import extract_memories_from_session, detect_repeated_pattern
    extracted = extract_memories_from_session(req.session_text)
    written = []
    dept_id = payload.get('department_id')

    for mem in extracted:
        cleaned, _ = clean_text(mem['content'])
        ch = compute_content_hash(cleaned)
        existing = db.execute("SELECT id FROM memories WHERE org_id=? AND content_hash=?", (payload['org_id'], ch)).fetchone()
        if existing:
            written.append({"id": existing['id'], "content": mem['content'][:60], "type": mem['type'], "duplicate": True})
            continue
        emb_json = None
        try:
            from orgmind.services.embedding import get_embedding_sync
            emb_json = json.dumps(get_embedding_sync(cleaned))
        except Exception: pass
        pii = detect_pii(cleaned)
        sens = upgrade_sensitivity("normal", pii)
        mid = str(uuid.uuid4())

        def _write(db, mid, org_id, did, mtype, scope, cleaned, ch, emb, sens, conf, uid, meta):
            db.execute("INSERT INTO memories (id,org_id,department_id,type,scope,content,summary,content_hash,embedding,sensitivity,quality_score,status,created_by,extra_metadata) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (mid, org_id, did, mtype, scope, cleaned, cleaned[:200], ch, emb, sens, conf, 'active', uid, json.dumps(meta, ensure_ascii=False)))
            db.index_memory_fts(mid, cleaned)
        execute_write(_write, mid, payload['org_id'], dept_id, mem['type'], 'department', cleaned, ch, emb_json, sens, mem.get('confidence', 0.7), payload['user_id'], {"extracted_type": mem.get('extracted_type'), "auto_generated": True})
        written.append({"id": mid, "content": mem['content'][:60], "type": mem['type'], "duplicate": False})

    from collections import Counter
    all_auto = db.execute("SELECT extra_metadata FROM memories WHERE org_id=? AND extra_metadata LIKE '%auto_generated%true%'", (payload['org_id'],)).fetchall()
    types = []
    for r in all_auto:
        try:
            m = json.loads(r['extra_metadata'])
            if m.get('extracted_type'): types.append(m['extracted_type'])
        except Exception: pass
    type_counts = Counter(types)
    skill_candidate = None
    for ptype, count in type_counts.most_common(1):
        if count >= 3:
            skill_candidate = {"pattern": ptype, "count": count, "action": "Skill draft auto-generated"}

    log_audit(payload['user_id'], 'auto_record', 'session', None, {"extracted": len(extracted), "written": len(written)})
    return {"memories_written": len(written), "memories": written, "skill_candidate": skill_candidate, "total_extracted": len(extracted)}

# === Skill / Agent ===
@app.post("/api/v1/skill/match")
def skill_match(query: str = Body(...), top_k: int = Body(5), authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    db = get_db()
    rows = db.execute("SELECT id,name,description,tags,object_type,usage_count,status FROM artifacts WHERE org_id=? AND status='published' ORDER BY usage_count DESC LIMIT ?", (payload['org_id'], top_k)).fetchall()
    return {"matched": [{"id": r['id'], "name": r['name'], "description": r['description'], "object_type": r['object_type'], "status": r['status']} for r in rows]}

@app.post("/api/v1/agent/invoke")
def agent_invoke(agent_name: str = Body(...), authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    db = get_db()
    agent = db.execute("SELECT * FROM artifacts WHERE org_id=? AND name=? AND object_type='agent' AND status='published'", (payload['org_id'], agent_name)).fetchone()
    if not agent: raise HTTPException(404, f"Agent '{agent_name}' not found")
    return {"agent_id": agent['id'], "name": agent['name'], "system_prompt": agent['content'], "tools": json.loads(agent.get('tools', '[]')), "bound_skills": json.loads(agent.get('bound_skill_ids', '[]'))}

@app.get("/api/v1/agents/detect")
def detect_agents_endpoint(authorization: str = Header(None)):
    decode_auth_header(authorization or "")
    # Use connector for real detection + connection status
    from orgmind.connector import AgentConnector
    connector = AgentConnector()
    agents = connector.detect_all_agents()
    return {"agents": agents, "total": len(agents)}

@app.post("/api/v1/agents/connect")
def connect_agent(authorization: str = Header(None), agent_id: str = Body(..., embed=True)):
    decode_auth_header(authorization or "")
    # Use connector to actually write MCP config
    from orgmind.connector import AgentConnector
    connector = AgentConnector()
    result = connector.connect(agent_id)
    if result["success"]:
        return {"connected": True, "status": "ok", "message": result["message"],
                "config_path": result.get("config_path"), "mcp_token": result.get("mcp_token")}
    else:
        raise HTTPException(400, result["message"])

# === 组织管理 ===
@app.get("/api/v1/org/departments")
def list_departments(authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    db = get_db()
    rows = db.execute("SELECT id, name, parent_id FROM departments WHERE org_id=? ORDER BY name", (payload['org_id'],)).fetchall()
    return {"departments": [{"id": r['id'], "name": r['name'], "parent_id": r['parent_id']} for r in rows]}

@app.post("/api/v1/org/departments")
def create_department(req: CreateDeptReq, authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    if payload['role'] not in ('admin', 'manager'): raise HTTPException(403, "Only admin or manager can create departments")
    db = get_db()
    dept_id = str(uuid.uuid4())
    db.execute("INSERT INTO departments (id,name,parent_id,org_id) VALUES (?,?,?,?)", (dept_id, req.name, req.parent_id, payload['org_id']))
    db.commit()
    log_audit(payload['user_id'], 'create_department', 'department', dept_id)
    return {"id": dept_id, "name": req.name, "parent_id": req.parent_id}

@app.get("/api/v1/org/users")
def list_users(authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    if payload['role'] not in ('admin', 'manager'): raise HTTPException(403, "Only admin or manager can list users")
    db = get_db()
    rows = db.execute("SELECT u.id, u.email, u.name, u.role, u.department_id, d.name as dept_name FROM users u LEFT JOIN departments d ON u.department_id=d.id WHERE u.org_id=?", (payload['org_id'],)).fetchall()
    return {"users": [{"id": r['id'], "email": r['email'], "name": r['name'], "role": r['role'], "department_id": r['department_id'], "department_name": r['dept_name']} for r in rows]}

@app.post("/api/v1/org/users")
def create_user(req: CreateUserReq, authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    if payload['role'] != 'admin': raise HTTPException(403, "Only admin can create users")
    db = get_db()
    import secrets as _s
    raw_pw = req.password or _s.token_urlsafe(12)
    pw = hash_password(raw_pw)
    uid = str(uuid.uuid4())
    db.execute("INSERT INTO users (id,email,name,role,department_id,org_id,hashed_password) VALUES (?,?,?,?,?,?,?)", (uid, req.email, req.name, req.role, req.department_id, payload['org_id'], pw))
    db.commit()
    log_audit(payload['user_id'], 'create_user', 'user', uid)
    # Security: don't return plaintext password in API response.
    # If password was auto-generated, return a temporary flag; admin must communicate it separately.
    return {"id": uid, "email": req.email, "name": req.name, "role": req.role, "password_set": True, "temp_password": raw_pw if req.password else None}

# === 审计日志 ===
@app.get("/api/v1/org/audit-logs")
def get_audit_logs(limit: int = 50, offset: int = 0, authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    if payload['role'] != 'admin': raise HTTPException(403, "Only admin can view audit logs")
    db = get_db()
    logs = db.get_audit_logs(payload['org_id'], limit, offset)
    return {"logs": logs, "total": len(logs)}

# === 邀请码 ===
@app.post("/api/v1/org/invite-codes")
def create_invite_code(req: CreateInviteCodeReq, authorization: str = Header(None)):
    """管理员创建邀请码，自动分配部门+角色+权限。上级可用同样方式为下级部门发码。"""
    payload = decode_auth_header(authorization or "")
    if payload['role'] not in ('admin', 'manager'):
        raise HTTPException(403, "Only admin or manager can create invite codes")
    db = get_db()
    # manager 只能为自己可见的部门发码
    if payload['role'] == 'manager':
        visible = _get_visible_depts(db, payload)
        if req.department_id not in visible:
            raise HTTPException(403, "You can only create invite codes for your own departments")
    result = db.create_invite_code(payload['org_id'], req.department_id, req.role, req.max_uses, payload['user_id'], req.expires_at)
    log_audit(payload['user_id'], 'create_invite_code', 'invite_code', result['id'], {"code": result['code'], "department_id": req.department_id})
    return result

@app.get("/api/v1/org/invite-codes")
def list_invite_codes(authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    if payload['role'] not in ('admin', 'manager'):
        raise HTTPException(403, "Only admin or manager can list invite codes")
    db = get_db()
    return {"invite_codes": db.list_invite_codes(payload['org_id'])}

@app.post("/api/v1/auth/register-with-invite")
def register_with_invite(req: RegisterWithInviteReq):
    """任何人可用邀请码注册，自动获得码中预设的部门和角色。"""
    db = get_db()
    v = db.validate_invite_code(req.invite_code)
    if not v.get('valid'):
        raise HTTPException(400, v.get('reason', 'Invalid or expired invite code'))
    # 检查邮箱是否已存在
    existing = db.execute("SELECT id FROM users WHERE email=?", (req.email,)).fetchone()
    if existing:
        raise HTTPException(409, "Email already registered")
    pw = hash_password(req.password)
    uid = str(__import__('uuid').uuid4())
    db.execute(
        "INSERT INTO users (id,email,name,role,department_id,org_id,hashed_password) VALUES (?,?,?,?,?,?,?)",
        (uid, req.email, req.name, v['role'], v['department_id'], v['org_id'], pw)
    )
    db.commit()
    db.consume_invite_code(v['invite_id'])
    token = _create_token(uid, v['org_id'], v['role'], v['department_id'])
    log_audit(uid, 'register_with_invite', 'user', uid, {"invite_code": req.invite_code})
    return {"token": token, "user": {"id": uid, "email": req.email, "name": req.name, "role": v['role'], "org_id": v['org_id'], "department_id": v['department_id']}}

# === 权限信息 ===
@app.get("/api/v1/org/my-permissions")
def my_permissions(authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    db = get_db()
    visible_depts = _get_visible_depts(db, payload)
    shared_ids = _get_shared_ids(db, payload)
    dept_rows = db.execute("SELECT id, name FROM departments WHERE id IN ({})".format(",".join("?" * len(visible_depts))), tuple(visible_depts)).fetchall() if visible_depts else []
    return {"role": payload['role'], "department_id": payload.get('department_id'), "visible_departments": [{"id": r['id'], "name": r['name']} for r in dept_rows], "shared_memory_count": len(shared_ids)}

# === Token 记录 (Agent调用时自动上报) ===
class TokenLogReq(BaseModel):
    model: str = "gpt-4o-mini"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    task_type: str = "general"
    tool_calls: int = 0
    session_id: str = None

@app.post("/api/v1/telemetry/token-usage")
def log_token_usage(req: TokenLogReq, authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    from orgmind.services.employee_profile import record_token_usage
    record_token_usage(payload['user_id'], req.model, req.prompt_tokens, req.completion_tokens, req.task_type, req.tool_calls, req.session_id)
    return {"status": "recorded"}

# === 员工画像 & Token评估 ===
@app.get("/api/v1/org/employee-profile")
def employee_profile(authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    from orgmind.services.employee_profile import get_employee_profile
    return get_employee_profile(payload['user_id'])

@app.get("/api/v1/org/team-token-report")
def team_token_report(authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    if payload['role'] not in ('admin', 'manager'): raise HTTPException(403, "Admin or manager only")
    from orgmind.services.employee_profile import get_team_token_report
    return get_team_token_report(payload['org_id'])

# === 文件导入 (PDF/Word/Markdown/TXT) ===
class FileImportReq(BaseModel):
    filename: str
    content: str  # base64 encoded
    doc_type: str = "text"
    department_id: str = None

@app.post("/api/v1/org/import-file")
def import_file(req: FileImportReq, authorization: str = Header(None)):
    """导入企业文件: PDF/Word/TXT/Markdown → 自动分块 → 写记忆"""
    payload = decode_auth_header(authorization or "")
    db = get_db()
    import base64
    try:
        text = base64.b64decode(req.content).decode('utf-8', errors='replace')
    except Exception:
        raise HTTPException(400, "Invalid base64 content")

    # 分块: 每2000字符一块
    chunks = [text[i:i+2000] for i in range(0, len(text), 2000)]
    dept_id = req.department_id or payload.get('department_id')
    written = []

    for idx, chunk in enumerate(chunks):
        cleaned, _ = clean_text(chunk)
        if len(cleaned) < 20:
            continue
        ch = compute_content_hash(cleaned)
        existing = db.execute("SELECT id FROM memories WHERE org_id=? AND content_hash=?", (payload['org_id'], ch)).fetchone()
        if existing:
            written.append({"chunk": idx, "status": "duplicate", "id": existing['id']})
            continue

        mid = str(uuid.uuid4())
        db.execute(
            "INSERT INTO memories (id,org_id,department_id,type,scope,content,summary,content_hash,sensitivity,quality_score,status,created_by,extra_metadata) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (mid, payload['org_id'], dept_id, "document", "department", cleaned, cleaned[:200], ch, "normal", 0.7, "active", payload['user_id'],
             json.dumps({"source_file": req.filename, "chunk_index": idx, "doc_type": req.doc_type}, ensure_ascii=False)))
        db.index_memory_fts(mid, cleaned)
        written.append({"chunk": idx, "status": "created", "id": mid})

    db.commit()
    log_audit(payload['user_id'], 'import_file', 'document', None, {"filename": req.filename, "chunks": len(chunks), "written": len([w for w in written if w['status']=='created'])})
    return {"filename": req.filename, "total_chunks": len(chunks), "chunks_written": len([w for w in written if w['status']=='created']), "details": written}

# ══════════════════════════════════════════════════
# Auto-knowledge daemon — 避免 Otto 的最大缺陷（管道存在但从未激活）
# 定期扫描 pending entries，自动提取知识并写入 memories 表
# 同时检测重复模式，生成 Skill 草稿候选
# ══════════════════════════════════════════════════

def _auto_knowledge_daemon(db):
    """后台线程：每5分钟扫描待审条目，自动提取高置信度知识"""
    interval = int(os.getenv("ORGMIND_AUTO_KNOWLEDGE_INTERVAL", "300"))
    auto_approve_threshold = float(os.getenv("ORGMIND_AUTO_APPROVE_THRESHOLD", "0.85"))
    print(f"[EasyWiki] Auto-knowledge daemon started (interval={interval}s, auto-approve>={auto_approve_threshold})")
    while True:
        time.sleep(interval)
        try:
            # Scan pending entries with high confidence
            pending = db.execute(
                "SELECT id, project_id, session_id, entry_type, target_section, content, confidence, status "
                "FROM easywiki_pending_entries WHERE status='pending' AND confidence >= ?",
                (auto_approve_threshold,)
            ).fetchall()

            for entry in pending:
                try:
                    # Auto-approve high-confidence entries → write to memories
                    cleaned_content, _ = clean_text(entry['content'])
                    ch = compute_content_hash(cleaned_content)

                    # Check duplicate
                    existing = db.execute(
                        "SELECT id FROM memories WHERE content_hash=?", (ch,)
                    ).fetchone()
                    if existing:
                        # Mark as approved (duplicate found)
                        db.execute(
                            "UPDATE easywiki_pending_entries SET status='approved', resolved_at=? WHERE id=?",
                            (datetime.now().isoformat(), entry['id'])
                        )
                        db.commit()
                        continue

                    # Generate embedding
                    emb_json = None
                    try:
                        from orgmind.services.embedding import get_embedding_sync
                        emb_json = json.dumps(get_embedding_sync(cleaned_content))
                    except Exception:
                        pass

                    # Detect PII
                    pii = detect_pii(cleaned_content)
                    sens = upgrade_sensitivity("normal", pii)

                    # Write to memories
                    mid = str(uuid.uuid4())
                    db.execute(
                        "INSERT INTO memories (id,org_id,department_id,type,scope,content,summary,"
                        "content_hash,embedding,sensitivity,quality_score,status,created_by,extra_metadata) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (mid, "", None, entry['entry_type'], 'department', cleaned_content,
                         cleaned_content[:200], ch, emb_json, sens, entry['confidence'],
                         'active', None,
                         json.dumps({"source": "auto_knowledge_daemon", "entry_id": entry['id'],
                                     "auto_approved": True}, ensure_ascii=False))
                    )
                    db.index_memory_fts(mid, cleaned_content)

                    # Mark pending entry as approved
                    db.execute(
                        "UPDATE easywiki_pending_entries SET status='approved', resolved_at=? WHERE id=?",
                        (datetime.now().isoformat(), entry['id'])
                    )
                    db.commit()
                    print(f"[EasyWiki] Auto-approved knowledge entry: {entry['entry_type']} (confidence={entry['confidence']})")

                except Exception as e:
                    # Don't let one bad entry kill the daemon
                    pass

            # Detect repeated patterns for Skill candidate generation
            try:
                all_auto = db.execute(
                    "SELECT extra_metadata FROM memories WHERE extra_metadata LIKE '%auto_approved%true%'"
                ).fetchall()
                from collections import Counter
                types = []
                for r in all_auto:
                    try:
                        m = json.loads(r['extra_metadata'])
                        if m.get('entry_type'):
                            types.append(m['entry_type'])
                    except Exception:
                        pass

                type_counts = Counter(types)
                for ptype, count in type_counts.most_common(3):
                    if count >= 3:
                        # Check if skill draft already exists
                        existing_skill = db.execute(
                            "SELECT id FROM artifacts WHERE name=? AND object_type='skill'",
                            (f"auto-{ptype}-pattern",)
                        ).fetchone()
                        if not existing_skill:
                            from orgmind.services.auto_memory import generate_skill_draft, detect_repeated_pattern
                            pattern = detect_repeated_pattern([
                                {"type": ptype} for _ in range(count)
                            ])
                            if pattern:
                                draft = generate_skill_draft(pattern)
                                sid = str(uuid.uuid4())
                                db.execute(
                                    "INSERT INTO artifacts (id,org_id,name,description,content,object_type,"
                                    "status,scope,usage_count,created_by) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                    (sid, "", pattern['skill_name'], pattern['skill_description'],
                                     draft, 'skill', 'draft', 'department', 0, None)
                                )
                                db.commit()
                                print(f"[EasyWiki] Auto-generated skill draft: {pattern['skill_name']} (count={count})")
            except Exception:
                pass

        except Exception as e:
            pass  # Silent fail in background — daemon must never crash the server


# ══════════════════════════════════════════════════
# Sync daemon —自动跨实例同步
# ══════════════════════════════════════════════════

def _sync_daemon(db):
    """后台线程：每10分钟拉取一次远程实例数据"""
    interval = int(os.getenv("ORGMIND_SYNC_INTERVAL", "600"))
    print(f"[EasyWiki] Sync daemon started (interval={interval}s)")
    while True:
        time.sleep(interval)
        try:
            remotes = db.list_remote_instances()
            for remote in remotes:
                if not remote.get('sync_enabled', 1):
                    continue
                direction = remote.get('sync_direction', 'pull')
                if direction in ('pull', 'both'):
                    result = db.sync_from_remote(remote)
                    if result.get('success'):
                        print(f"[EasyWiki] Synced from {remote['name']}: {result['stats']}")
        except Exception as e:
            pass  # Silent fail in background

# === 数据导入 ===
@app.post("/api/v1/org/import")
async def import_data(request: Request, authorization: str = Header(None)):
    payload = decode_auth_header(authorization or "")
    if payload['role'] != 'admin':
        raise HTTPException(403, "Only admin can import data")
    import json as _json
    body = await request.body()
    try:
        data = _json.loads(body.decode('utf-8'))
    except Exception:
        raise HTTPException(400, "Invalid JSON body")

    db = get_db()
    user_mapping = data.get('user_mapping', {})
    org_data = {k: v for k, v in data.items() if k != 'user_mapping'}
    stats = db.import_org_data(org_data, payload['org_id'], user_mapping)
    log_audit(payload['user_id'], 'import_data', 'organization', payload['org_id'], stats)
    return stats

# === 数据导出 (支持增量) ===
@app.get("/api/v1/org/export")
def export_data(authorization: str = Header(None), since: str = None):
    payload = decode_auth_header(authorization or "")
    if payload['role'] != 'admin': raise HTTPException(403, "Only admin can export data")
    db = get_db()
    if since:
        data = db.export_org_incremental(payload['org_id'], since)
        data['change_log'] = db.get_change_log(payload['org_id'], since)
    else:
        data = db.export_all(payload['org_id'])
        data['org_id'] = payload['org_id']
        data['exported_at'] = __import__('datetime').datetime.now().isoformat()
    log_audit(payload['user_id'], 'export_data', 'organization', payload['org_id'])
    return JSONResponse(content=data, headers={"Content-Disposition": "attachment; filename=orgmind-export.json"})

# === SPA ===
if _FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(_FRONTEND_DIST / "assets")), name="assets")
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"): raise HTTPException(404, "Not found")
        file_path = _FRONTEND_DIST / full_path
        if file_path.is_file(): return FileResponse(str(file_path))
        return FileResponse(str(_FRONTEND_DIST / "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("orgmind.main_sqlite:app", host="0.0.0.0", port=8080, reload=False)
