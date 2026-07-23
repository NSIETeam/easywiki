"""
EasyWiki REST API Routes — v1.0
Implements sections 3.1-3.5 of EASYWIKI_EXECUTION_SPEC.md
"""
import uuid
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Body, Query
from orgmind.db import get_db
from orgmind.governance.cleaners import clean_text
from orgmind.governance.pii import detect_pii, upgrade_sensitivity
from orgmind.governance.quality import compute_quality_score, QualityInput
from orgmind.governance.dedup import compute_content_hash
from orgmind.services.write_queue import execute_write
from orgmind.services.audit import log_audit
from orgmind.auth import decode_auth_header
from orgmind.easywiki.version_diff import three_way_merge, progress_field_merge
from orgmind.easywiki.graph_lite import build_graph

router = APIRouter()

FIXED_SECTIONS = [
    "overview", "decisions_experience", "knowledge_graph",
    "agents_skills", "files", "progress_table", "agent_inbox"
]


def _project_access(db, project_id: str, org_id: str):
    project = db.execute(
        "SELECT id, department_id FROM easywiki_projects WHERE id=? AND org_id=?",
        (project_id, org_id)
    ).fetchone()
    if not project:
        raise HTTPException(404, "Project not found")
    return project


def _entry_access(db, entry_id: str, org_id: str):
    entry = db.execute(
        "SELECT * FROM easywiki_pending_entries WHERE id=? AND org_id=?",
        (entry_id, org_id)
    ).fetchone()
    if not entry:
        raise HTTPException(404, "Entry not found")
    return entry


# ============================================================
@router.get("/projects")
def list_projects(authorization: str = Header(None)):
    payload = decode_auth_header(authorization)
    db = get_db()
    rows = db.execute(
        "SELECT id, name, health, created_at FROM easywiki_projects WHERE org_id=? ORDER BY created_at DESC",
        (payload["org_id"],)
    ).fetchall()
    return {"projects": [{"id": r["id"], "name": r["name"], "health": r["health"], "created_at": r["created_at"]} for r in rows]}


@router.post("/projects")
def create_project(body: dict = Body(...), authorization: str = Header(None)):
    payload = decode_auth_header(authorization)
    pid = str(uuid.uuid4())
    name = body["name"]

    def _write(db, pid, org_id, name, uid):
        db.execute(
            "INSERT INTO easywiki_projects (id,org_id,name,created_by) VALUES (?,?,?,?)",
            (pid, org_id, name, uid)
        )
        # Create default progress fields
        for field_name, field_type in [
            ("任务状态", "select"), ("负责人", "text"), ("优先级", "select"),
            ("预估完成度", "number"), ("最近更新", "text")
        ]:
            fid = str(uuid.uuid4())
            db.execute(
                "INSERT INTO easywiki_progress_fields (id,project_id,field_name,field_type) VALUES (?,?,?,?)",
                (fid, pid, field_name, field_type)
            )

    execute_write(_write, pid, payload["org_id"], name, payload["user_id"])
    log_audit(payload["user_id"], "create_easywiki_project", "easywiki_project", pid, {"name": name})
    return {"id": pid, "name": name}


@router.get("/projects/{project_id}/manifest")
def get_project_manifest(project_id: str, authorization: str = Header(None)):
    payload = decode_auth_header(authorization)
    db = get_db()
    proj = db.execute(
        "SELECT id FROM easywiki_projects WHERE id=? AND org_id=?",
        (project_id, payload["org_id"])
    ).fetchone()
    if not proj:
        raise HTTPException(404, "Project not found")
    fields = db.execute(
        "SELECT field_name, field_type FROM easywiki_progress_fields WHERE project_id=? ORDER BY field_name",
        (project_id,)
    ).fetchall()
    return {
        "project_id": project_id,
        "sections": FIXED_SECTIONS,
        "progress_fields": [{"field_name": r["field_name"], "field_type": r["field_type"]} for r in fields]
    }


# ============================================================
# Section 3.2 — Pages (block-based, free tree inside fixed sections)
# ============================================================
@router.get("/projects/{project_id}/sections/{section}/pages")
def list_section_pages(project_id: str, section: str, authorization: str = Header(None)):
    payload = decode_auth_header(authorization)
    db = get_db()
    proj = db.execute("SELECT id FROM easywiki_projects WHERE id=? AND org_id=?", (project_id, payload["org_id"])).fetchone()
    if not proj:
        raise HTTPException(404, "Project not found")
    if section not in FIXED_SECTIONS:
        raise HTTPException(400, f"Invalid section: {section}")
    rows = db.execute(
        "SELECT p.id, p.title, p.parent_page_id, p.sort_order, p.content_ref, "
        "CASE WHEN (SELECT COUNT(*) FROM easywiki_pages p2 WHERE p2.content_ref = p.content_ref AND p2.id != p.id) > 0 "
        "THEN (SELECT p2.id FROM easywiki_pages p2 WHERE p2.content_ref = p.content_ref AND p2.id != p.id LIMIT 1) "
        "ELSE NULL END as clone_of "
        "FROM easywiki_pages p WHERE p.project_id=? AND p.section=? ORDER BY p.sort_order, p.created_at",
        (project_id, section)
    ).fetchall()

    # Phase 2: include cloned pages from clone_mounts
    cloned_pages = db.get_cloned_pages_for_project(project_id, section)

    pages = []
    seen_ids = set()
    for r in rows:
        if r["id"] not in seen_ids:
            pages.append({"id": r["id"], "title": r["title"], "parent_page_id": r["parent_page_id"],
                          "order": r["sort_order"], "is_clone_of": r["clone_of"], "is_cloned": False})
            seen_ids.add(r["id"])
    for cp in cloned_pages:
        if cp["id"] not in seen_ids:
            pages.append({"id": cp["id"], "title": cp["title"], "parent_page_id": cp.get("parent_page_id"),
                          "order": cp.get("sort_order", 0), "is_clone_of": None,
                          "is_cloned": True, "mount_id": cp["mount_id"],
                          "source_project_id": cp["source_project_id"]})
            seen_ids.add(cp["id"])

    return {"pages": pages}


@router.post("/projects/{project_id}/sections/{section}/pages")
def create_page(project_id: str, section: str, body: dict = Body(...), authorization: str = Header(None)):
    payload = decode_auth_header(authorization)
    db = get_db()
    proj = db.execute("SELECT id FROM easywiki_projects WHERE id=? AND org_id=?", (project_id, payload["org_id"])).fetchone()
    if not proj:
        raise HTTPException(404, "Project not found")
    if section not in FIXED_SECTIONS:
        raise HTTPException(400, f"Invalid section: {section}")
    page_id = str(uuid.uuid4())
    content_id = str(uuid.uuid4())
    title = body.get("title", "Untitled")
    parent_page_id = body.get("parent_page_id")

    def _write(db, page_id, content_id, project_id, section, title, parent_page_id, uid):
        version_id = str(uuid.uuid4())
        db.execute(
            "INSERT INTO easywiki_page_contents (id, blocksuite_doc, current_version_id) VALUES (?,?,?)",
            (content_id, "", version_id)
        )
        db.execute(
            "INSERT INTO easywiki_pages (id,project_id,section,title,parent_page_id,content_ref,created_by) VALUES (?,?,?,?,?,?,?)",
            (page_id, project_id, section, title, parent_page_id, content_id, uid)
        )
        db.execute(
            "INSERT INTO easywiki_versions (id,target_type,target_id,author_type,author_ref,content_snapshot) VALUES (?,?,?,?,?,?)",
            (version_id, "page", page_id, "human", uid, "")
        )
    execute_write(_write, page_id, content_id, project_id, section, title, parent_page_id, payload["user_id"])
    log_audit(payload["user_id"], "create_easywiki_page", "easywiki_page", page_id)
    return {"id": page_id}
@router.get("/pages/{page_id}")
def get_page(page_id: str, authorization: str = Header(None)):
    payload = decode_auth_header(authorization)
    db = get_db()
    page = db.execute(
        "SELECT p.id, p.title, p.project_id, p.section, p.content_ref, pc.blocksuite_doc, pc.current_version_id "
        "FROM easywiki_pages p JOIN easywiki_page_contents pc ON p.content_ref = pc.id WHERE p.id=?",
        (page_id,)
    ).fetchone()
    if not page:
        raise HTTPException(404, "Page not found")
    # Verify access through project membership
    proj = db.execute("SELECT id FROM easywiki_projects WHERE id=? AND org_id=?", (page["project_id"], payload["org_id"])).fetchone()
    if not proj:
        raise HTTPException(403, "Access denied")
    return {
        "id": page["id"], "title": page["title"],
        "blocksuite_doc": page["blocksuite_doc"], "current_version_id": page["current_version_id"]
    }


@router.put("/pages/{page_id}")
def update_page(page_id: str, body: dict = Body(...), authorization: str = Header(None)):
    """
    Save page content with version tracking.
    Runs a real 3-way merge (Section 3.5/6.6) when the submitted based_on_version
    differs from the current version — NOT a naive "reject on any mismatch" lock.
    """
    payload = decode_auth_header(authorization)
    db = get_db()
    page = db.execute(
        "SELECT p.id, p.project_id, p.content_ref, pc.blocksuite_doc, pc.current_version_id, p.title "
        "FROM easywiki_pages p JOIN easywiki_page_contents pc ON p.content_ref = pc.id WHERE p.id=?",
        (page_id,)
    ).fetchone()
    if not page:
        raise HTTPException(404, "Page not found")
    _project_access(db, page["project_id"], payload["org_id"])
    proposed_doc = body["blocksuite_doc"]
    based_on_version = body.get("based_on_version")
    current_doc = page["blocksuite_doc"] or ""
    current_version_id = page["current_version_id"]

    final_doc = proposed_doc
    conflict_id = None

    if based_on_version and current_version_id and based_on_version != current_version_id:
        base_row = db.execute(
            "SELECT content_snapshot FROM easywiki_versions WHERE id=?", (based_on_version,)
        ).fetchone()
        base_doc = base_row["content_snapshot"] if base_row else ""
        final_doc, conflict_id = three_way_merge(
            base_doc, current_doc, proposed_doc, "page", page_id, page["project_id"]
        )
        if conflict_id:
            raise HTTPException(409, {
                "detail": "Conflict detected",
                "conflict_id": conflict_id,
                "current_version": current_version_id,
                "message": "编辑冲突：与他人改动的区域重叠，已生成待裁决记录。",
            })

    version_id = str(uuid.uuid4())

    def _write(db, page_id, content_ref, doc, version_id, based_on, uid):
        db.execute("UPDATE easywiki_page_contents SET blocksuite_doc=?, current_version_id=?, updated_at=datetime('now') WHERE id=?", (doc, version_id, content_ref))
        db.execute(
            "INSERT INTO easywiki_versions (id,target_type,target_id,author_type,author_ref,content_snapshot,based_on_version) VALUES (?,?,?,?,?,?,?)",
            (version_id, "page", page_id, "human", uid, doc, based_on)
        )
    execute_write(_write, page_id, page["content_ref"], final_doc, version_id, current_version_id, payload["user_id"])
    log_audit(payload["user_id"], "update_easywiki_page", "easywiki_page", page_id, {"merged": bool(based_on_version and current_version_id and based_on_version != current_version_id)})
    return {"id": page_id, "version_id": version_id, "merged_content": final_doc if final_doc != proposed_doc else None}


@router.post("/pages/{page_id}/clone-mount")
def clone_mount_page(page_id: str, body: dict = Body(...), authorization: str = Header(None)):
    """Clone-mount a page into another project section (shared content_ref)."""
    payload = decode_auth_header(authorization)
    db = get_db()
    src = db.execute(
        "SELECT p.id, p.title, p.content_ref FROM easywiki_pages p JOIN easywiki_projects pr ON p.project_id=pr.id "
        "WHERE p.id=? AND pr.org_id=?", (page_id, payload["org_id"])
    ).fetchone()
    if not src:
        raise HTTPException(404, "Source page not found")
    target_project_id = body["target_project_id"]
    target_section = body["target_section"]
    # Verify target project exists
    tgt = db.execute("SELECT id FROM easywiki_projects WHERE id=? AND org_id=?", (target_project_id, payload["org_id"])).fetchone()
    if not tgt:
        raise HTTPException(404, "Target project not found")
    if target_section not in FIXED_SECTIONS:
        raise HTTPException(400, f"Invalid section: {target_section}")
    cloned_id = str(uuid.uuid4())

    def _write(db, cloned_id, project_id, section, title, content_ref, uid):
        db.execute(
            "INSERT INTO easywiki_pages (id,project_id,section,title,content_ref,created_by) VALUES (?,?,?,?,?,?)",
            (cloned_id, project_id, section, title, content_ref, uid)
        )
    execute_write(_write, cloned_id, target_project_id, target_section, src["title"], src["content_ref"], payload["user_id"])
    log_audit(payload["user_id"], "clone_mount_page", "easywiki_page", cloned_id, {"source": page_id})
    return {"cloned_page_id": cloned_id}


# ============================================================
# Section 3.3 — Agent Pending Entries & Inbox
# ============================================================
@router.post("/pending-entries")
def create_pending_entry(body: dict = Body(...), authorization: str = Header(None)):
    """
    MCP Server calls this internally after receiving a propose_* tool call.
    Processing pipeline: clean_text → detect_pii → hash dedup → quality_score.
    CRITICAL: Status is ALWAYS "pending", NEVER auto-published.
    """
    payload = decode_auth_header(authorization)
    db = get_db()
    project_id = body.get("project_id")
    if not project_id:
        raise HTTPException(400, "project_id is required")
    _project_access(db, project_id, payload["org_id"])
    raw_content = body.get("content", "")
    cleaned, _ = clean_text(raw_content)
    ch = compute_content_hash(cleaned)
    pii_hits = detect_pii(cleaned)
    sensitivity = upgrade_sensitivity("normal", pii_hits)

    # Hash dedup (same pattern as main_sqlite.py)
    existing = db.execute(
        "SELECT id FROM easywiki_memories WHERE org_id=? AND content_hash=?",
        (payload["org_id"], ch)
    ).fetchone()
    dedup_hint = "exact" if existing else "none"

    # Quality score
    qscore = compute_quality_score(QualityInput(
        completeness=0.8, schema_valid=1.0, near_duplicate_count=1 if dedup_hint != "none" else 0, source_trust=body.get("confidence", 0.5)
    ))

    eid = str(uuid.uuid4())
    file_refs_json = json.dumps(body.get("file_refs", []))

    def _write(db, eid, org_id, project_id, session_id, tool_name, entry_type, target_section, cleaned, file_refs_json, confidence, based_on_version, qscore, dedup_hint, pii_flag):
        db.execute(
            "INSERT INTO easywiki_pending_entries (id,org_id,project_id,session_id,tool_name,entry_type,target_section,raw_content,file_refs,confidence,based_on_version,quality_score,dedup_hint,pii_flag) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (eid, org_id, project_id, session_id, tool_name, entry_type, target_section, cleaned, file_refs_json,
             confidence, based_on_version, qscore, dedup_hint, 1 if pii_hits else 0)
        )
    execute_write(_write, eid, payload["org_id"], body.get("project_id"), body.get("session_id"),
                  body.get("tool_name"), body.get("entry_type"), body.get("target_section"),
                  cleaned, file_refs_json, body.get("confidence", 0.5),
                  body.get("based_on_version"), qscore, dedup_hint, 1 if pii_hits else 0)
    return {"id": eid, "status": "pending", "quality_score": qscore, "dedup_hint": dedup_hint, "pii_flag": bool(pii_hits)}


@router.get("/projects/{project_id}/pending-entries")
def list_pending_entries(project_id: str, status: str = Query("pending"), authorization: str = Header(None)):
    payload = decode_auth_header(authorization)
    db = get_db()
    proj = db.execute("SELECT id FROM easywiki_projects WHERE id=? AND org_id=?", (project_id, payload["org_id"])).fetchone()
    if not proj:
        raise HTTPException(404, "Project not found")
    rows = db.execute(
        "SELECT id, session_id, tool_name, entry_type, target_section, raw_content, file_refs, "
        "confidence, based_on_version, quality_score, dedup_hint, pii_flag, status, created_at, reject_reason "
        "FROM easywiki_pending_entries WHERE project_id=? AND status=? ORDER BY created_at DESC",
        (project_id, status)
    ).fetchall()
    return {"entries": [dict(r) for r in rows]}


@router.get("/pending-entries/{entry_id}")
def get_pending_entry(entry_id: str, authorization: str = Header(None)):
    payload = decode_auth_header(authorization)
    db = get_db()
    row = db.execute(
        "SELECT id, session_id, tool_name, entry_type, target_section, raw_content, file_refs, "
        "confidence, based_on_version, quality_score, dedup_hint, pii_flag, status, created_at "
        "FROM easywiki_pending_entries WHERE id=? AND org_id=?",
        (entry_id, payload["org_id"])
    ).fetchone()
    if not row:
        raise HTTPException(404, "Entry not found")
    return dict(row)


@router.post("/pending-entries/{entry_id}/approve")
def approve_pending_entry(entry_id: str, body: Optional[dict] = Body(None), authorization: str = Header(None)):
    """
    Approve a pending entry → write to easywiki_memories or easywiki_progress_fields.
    Supports "edited_approved" when edited_content is provided.
    Progress-field approvals run a real 3-way merge (progress_field_merge) against
    the field's current value using the entry's based_on_version as the merge base,
    instead of unconditionally overwriting.
    """
    payload = decode_auth_header(authorization)
    db = get_db()
    entry = _entry_access(db, entry_id, payload["org_id"])
    if entry["status"] != "pending":
        raise HTTPException(404, "Entry not found or already resolved")

    edited_content = body.get("edited_content") if body else None
    final_content = edited_content if edited_content else entry["raw_content"]

    if entry["entry_type"] == "progress_update":
        try:
            prog_data = json.loads(final_content)
            field_name = prog_data.get("field_name")
            suggested_value = prog_data.get("suggested_value", final_content)
        except json.JSONDecodeError:
            field_name = "最近更新"
            suggested_value = final_content

        existing = db.execute(
            "SELECT id, current_value FROM easywiki_progress_fields WHERE project_id=? AND field_name=?",
            (entry["project_id"], field_name)
        ).fetchone()

        conflict_id = None
        if existing and existing["current_value"] is not None:
            base_value = existing["current_value"]
            if entry["based_on_version"]:
                base_row = db.execute(
                    "SELECT content_snapshot FROM easywiki_versions WHERE id=? AND target_type='progress_field' AND target_id=?",
                    (entry["based_on_version"], existing["id"])
                ).fetchone()
                if not base_row:
                    raise HTTPException(409, "Invalid based_on_version for progress field")
                base_value = base_row["content_snapshot"]
            suggested_value, conflict_id = progress_field_merge(
                base_value, existing["current_value"], suggested_value,
                entry["project_id"], existing["id"]
            )
        if conflict_id:
            log_audit(payload["user_id"], "approve_pending_progress_conflict", "easywiki_pending_entry", entry_id, {"conflict_id": conflict_id})
            raise HTTPException(409, {
                "detail": "Conflict detected on progress field",
                "conflict_id": conflict_id,
                "field_name": field_name,
                "message": "该字段与人工修改冲突，已生成裁决记录，暂不批准。",
            })

        def _write_progress(db, entry_id, project_id, field_name, suggested_value, uid):
            existing = db.execute("SELECT id FROM easywiki_progress_fields WHERE project_id=? AND field_name=?", (project_id, field_name)).fetchone()
            if existing:
                version_id = str(uuid.uuid4())
                db.execute("UPDATE easywiki_progress_fields SET current_value=?, current_version_id=? WHERE id=?", (suggested_value, version_id, existing["id"]))
                db.execute("INSERT INTO easywiki_versions (id,target_type,target_id,author_type,author_ref,content_snapshot) VALUES (?,?,?,?,?,?)",
                           (version_id, "progress_field", existing["id"], "agent", f"{entry['tool_name']}:{entry['session_id']}", suggested_value))
            else:
                fid = str(uuid.uuid4())
                version_id = str(uuid.uuid4())
                db.execute("INSERT INTO easywiki_progress_fields (id,project_id,field_name,current_value,current_version_id) VALUES (?,?,?,?,?)",
                           (fid, project_id, field_name, suggested_value, version_id))
                db.execute("INSERT INTO easywiki_versions (id,target_type,target_id,author_type,author_ref,content_snapshot) VALUES (?,?,?,?,?,?)",
                           (version_id, "progress_field", fid, "agent", f"{entry['tool_name']}:{entry['session_id']}", suggested_value))
            db.execute("UPDATE easywiki_pending_entries SET status='approved', resolved_at=datetime('now'), resolved_by=? WHERE id=?", (uid, entry_id))
        execute_write(_write_progress, entry_id, entry["project_id"], field_name, suggested_value, payload["user_id"])
        log_audit(payload["user_id"], "approve_pending_progress", "easywiki_pending_entry", entry_id)
        try:
            build_graph(payload["org_id"], entry["project_id"], suggested_value, entry_id)
        except Exception:
            pass
        return {"id": entry_id, "status": "approved", "written_to": {"type": "progress_field", "field_name": field_name}}
    else:
        # Standard memory entry
        ch = compute_content_hash(final_content)
        mid = str(uuid.uuid4())
        emb_json = None
        try:
            from orgmind.services.embedding import get_embedding_sync
            emb_vec = get_embedding_sync(final_content)
            if emb_vec:
                emb_json = json.dumps(emb_vec)
        except Exception:
            pass

        def _write_memory(db, entry_id, mid, org_id, project_id, mem_type, content, ch, emb, uid, tool_name, session_id):
            db.execute(
                "INSERT INTO easywiki_memories (id,org_id,project_id,type,content,content_hash,embedding,sensitivity,quality_score,author_type,author_ref) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (mid, org_id, project_id, mem_type, content, ch, emb, "normal", entry["quality_score"] or 0.5, "agent", f"{tool_name}:{session_id}")
            )
            db.execute("UPDATE easywiki_pending_entries SET status='approved', resolved_at=datetime('now'), resolved_by=? WHERE id=?", (uid, entry_id))
        execute_write(_write_memory, entry_id, mid, payload["org_id"], entry["project_id"], entry["entry_type"],
                      final_content, ch, emb_json, payload["user_id"], entry["tool_name"], entry["session_id"])
        log_audit(payload["user_id"], "approve_pending_memory", "easywiki_pending_entry", entry_id, {"memory_id": mid})
        try:
            build_graph(payload["org_id"], entry["project_id"], final_content, mid)
        except Exception:
            import traceback; traceback.print_exc()
            pass
        return {"id": entry_id, "status": "approved", "written_to": {"type": "memory", "id": mid}}


@router.post("/pending-entries/{entry_id}/reject")
def reject_pending_entry(entry_id: str, body: dict = Body(...), authorization: str = Header(None)):
    payload = decode_auth_header(authorization)
    db = get_db()
    entry = _entry_access(db, entry_id, payload["org_id"])
    if entry["status"] != "pending":
        raise HTTPException(404, "Entry not found or already resolved")
    reason = body.get("reason", "")

    def _write(db, entry_id, reason, uid):
        db.execute("UPDATE easywiki_pending_entries SET status='rejected', reject_reason=?, resolved_at=datetime('now'), resolved_by=? WHERE id=?", (reason, uid, entry_id))
    execute_write(_write, entry_id, reason, payload["user_id"])
    log_audit(payload["user_id"], "reject_pending_entry", "easywiki_pending_entry", entry_id, {"reason": reason})
    return {"id": entry_id, "status": "rejected"}


@router.post("/pending-entries/batch-approve")
def batch_approve_pending_entries(body: dict = Body(...), authorization: str = Header(None)):
    payload = decode_auth_header(authorization)
    db = get_db()
    ids = body.get("ids", [])
    approved, failed = [], []
    for eid in ids:
        entry = db.execute("SELECT * FROM easywiki_pending_entries WHERE id=? AND status='pending' AND org_id=?", (eid, payload["org_id"])).fetchone()
        if not entry:
            failed.append({"id": eid, "reason": "Not found or already resolved"})
            continue
        try:
            ch = compute_content_hash(entry["raw_content"])
            mid = str(uuid.uuid4())
            emb_json = None
            try:
                from orgmind.services.embedding import get_embedding_sync
                emb_vec = get_embedding_sync(entry["raw_content"])
                if emb_vec:
                    emb_json = json.dumps(emb_vec)
            except Exception:
                pass

            def _write_batch(db, eid, mid, org_id, project_id, mem_type, content, ch, emb, uid, tool_name, session_id):
                db.execute(
                    "INSERT INTO easywiki_memories (id,org_id,project_id,type,content,content_hash,embedding,sensitivity,quality_score,author_type,author_ref) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (mid, org_id, project_id, mem_type, content, ch, emb, "normal", entry["quality_score"] or 0.5, "agent", f"{tool_name}:{session_id}")
                )
                db.execute("UPDATE easywiki_pending_entries SET status='approved', resolved_at=datetime('now'), resolved_by=? WHERE id=?", (uid, eid))
            execute_write(_write_batch, eid, mid, payload["org_id"], entry["project_id"], entry["entry_type"],
                          entry["raw_content"], ch, emb_json, payload["user_id"], entry["tool_name"], entry["session_id"])
            log_audit(payload["user_id"], "batch_approve_pending_memory", "easywiki_pending_entry", eid, {"memory_id": mid})
            try:
                build_graph(payload["org_id"], entry["project_id"], entry["raw_content"], mid)
            except Exception:
                pass
            approved.append(eid)
        except Exception as e:
            failed.append({"id": eid, "reason": str(e)})
    return {"approved": approved, "failed": failed}


# ============================================================
# Section 3.4 — Conflict Resolution
# ============================================================
@router.get("/conflicts")
def list_conflicts(status: str = Query("open"), authorization: str = Header(None)):
    payload = decode_auth_header(authorization)
    db = get_db()
    rows = db.execute(
        "SELECT id, target_type, target_id, base_version_id, human_version_id, agent_version_id, "
        "escalated_to_user_id, status, created_at FROM easywiki_conflicts WHERE status=? ORDER BY created_at DESC",
        (status,)
    ).fetchall()
    return {"conflicts": [dict(r) for r in rows]}


@router.post("/conflicts/{conflict_id}/resolve")
def resolve_conflict(conflict_id: str, body: dict = Body(...), authorization: str = Header(None)):
    payload = decode_auth_header(authorization)
    db = get_db()
    conflict = db.execute("SELECT * FROM easywiki_conflicts WHERE id=?", (conflict_id,)).fetchone()
    if not conflict:
        raise HTTPException(404, "Conflict not found")
    resolution = body.get("resolution")  # keep_human|keep_agent|manual_merge
    merged_content = body.get("merged_content")
    note = body.get("note", "")

    def _write(db, conflict_id, resolution, merged_content, note, uid):
        db.execute(
            "UPDATE easywiki_conflicts SET status='resolved', resolution=?, resolved_note=?, resolved_by=?, resolved_at=datetime('now') WHERE id=?",
            (f"{resolution}" + (f":{merged_content}" if merged_content else ""), note, uid, conflict_id)
        )
    execute_write(_write, conflict_id, resolution, merged_content, note, payload["user_id"])
    log_audit(payload["user_id"], "resolve_conflict", "easywiki_conflict", conflict_id, {"resolution": resolution})
    return {"id": conflict_id, "status": "resolved"}


# ============================================================
# Section 3.5 — Version History
# ============================================================
@router.get("/versions")
def list_versions(target_type: str = Query(...), target_id: str = Query(...), authorization: str = Header(None)):
    decode_auth_header(authorization)
    db = get_db()
    rows = db.execute(
        "SELECT id, author_type, author_ref, created_at, "
        "CASE WHEN length(content_snapshot) > 100 THEN substr(content_snapshot,1,100)||'...' ELSE content_snapshot END as diff_summary "
        "FROM easywiki_versions WHERE target_type=? AND target_id=? ORDER BY created_at DESC",
        (target_type, target_id)
    ).fetchall()
    return {"versions": [dict(r) for r in rows]}


# ============================================================
# Section 5.4 — Knowledge Graph API
# ============================================================
@router.get("/projects/{project_id}/graph")
def get_project_graph(project_id: str, authorization: str = Header(None)):
    """Return graph data (nodes + edges) for D3.js visualization."""
    payload = decode_auth_header(authorization)
    db = get_db()
    proj = db.execute("SELECT id FROM easywiki_projects WHERE id=? AND org_id=?", (project_id, payload["org_id"])).fetchone()
    if not proj:
        raise HTTPException(404, "Project not found")

    entities = db.execute(
        "SELECT id, name, entity_type FROM easywiki_graph_entities WHERE project_id=? LIMIT 200",
        (project_id,)
    ).fetchall()

    entity_ids = [r["id"] for r in entities]
    if not entity_ids:
        return {"nodes": [], "edges": []}

    placeholders = ",".join("?" * len(entity_ids))
    relations = db.execute(
        f"SELECT id, from_entity_id, to_entity_id, relation FROM easywiki_graph_relations "
        f"WHERE from_entity_id IN ({placeholders}) OR to_entity_id IN ({placeholders}) LIMIT 500",
        entity_ids + entity_ids
    ).fetchall()

    return {
        "nodes": [{"id": r["id"], "label": r["name"], "type": r["entity_type"]} for r in entities],
        "edges": [{"id": r["id"], "source": r["from_entity_id"], "target": r["to_entity_id"], "label": r["relation"]} for r in relations]
    }


# ══════════════════════════════════════════════════
# Phase 2: Clone Mount —跨项目知识分发 API
# ══════════════════════════════════════════════════

@router.post("/projects/{pid}/clone-mounts")
def create_clone_mount(
    pid: str,
    source_page_id: str = Body(...),
    target_section: str = Body(...),
    mount_parent_page_id: Optional[str] = Body(None),
    authorization: str = Header(None)
):
    """将页面从其他项目克隆挂载到当前项目"""
    user = decode_auth_header(authorization)
    if not user:
        raise HTTPException(401, "Invalid auth")

    def _create(db):
        _project_access(db, pid, user.get('org_id', ''))
        return db.create_clone_mount(
            source_page_id, pid, target_section, user['id'], mount_parent_page_id
        )

    try:
        result = execute_write(_create)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/projects/{pid}/clone-mounts")
def list_clone_mounts(pid: str, as_source: bool = False, authorization: str = Header(None)):
    """列出项目的克隆挂载"""
    user = decode_auth_header(authorization)
    if not user:
        raise HTTPException(401, "Invalid auth")

    def _list(db):
        _project_access(db, pid, user.get('org_id', ''))
        return db.list_clone_mounts(pid, as_source)

    return execute_write(_list)


@router.delete("/clone-mounts/{mid}")
def remove_clone_mount(mid: str, authorization: str = Header(None)):
    """移除克隆挂载"""
    user = decode_auth_header(authorization)
    if not user:
        raise HTTPException(401, "Invalid auth")

    def _delete(db):
        if not db.remove_clone_mount(mid):
            raise HTTPException(404, "Mount not found")
        return {"ok": True}

    return execute_write(_delete)


# ══════════════════════════════════════════════════
# Phase 3: 跨实例同步 API
# ══════════════════════════════════════════════════

@router.get("/remotes")
def list_remotes(authorization: str = Header(None)):
    """列出所有远程实例"""
    user = decode_auth_header(authorization)
    if not user:
        raise HTTPException(401, "Invalid auth")

    def _list(db):
        return db.list_remote_instances()

    return execute_write(_list)


@router.post("/remotes")
def add_remote(
    name: str = Body(...),
    url: str = Body(...),
    auth_token: str = Body(""),
    sync_direction: str = Body("pull"),
    authorization: str = Header(None)
):
    """添加远程实例"""
    user = decode_auth_header(authorization)
    if not user:
        raise HTTPException(401, "Invalid auth")

    def _add(db):
        return db.add_remote_instance(name, url, auth_token, sync_direction)

    return execute_write(_add)


@router.delete("/remotes/{rid}")
def remove_remote(rid: str, authorization: str = Header(None)):
    """删除远程实例"""
    user = decode_auth_header(authorization)
    if not user:
        raise HTTPException(401, "Invalid auth")

    def _remove(db):
        if not db.remove_remote_instance(rid):
            raise HTTPException(404, "Remote instance not found")
        return {"ok": True}

    return execute_write(_remove)


@router.get("/change-log")
def get_change_log(since: str = None, limit: int = 200, authorization: str = Header(None)):
    """获取变更日志"""
    user = decode_auth_header(authorization)
    if not user:
        raise HTTPException(401, "Invalid auth")

    def _get(db):
        return db.get_change_log(user.get('org_id', ''), since, limit)

    return execute_write(_get)


@router.post("/sync/pull")
def sync_pull(authorization: str = Header(None)):
    """从所有启用的远程实例拉取数据"""
    user = decode_auth_header(authorization)
    if not user:
        raise HTTPException(401, "Invalid auth")

    def _pull(db):
        remotes = db.list_remote_instances()
        results = []
        for remote in remotes:
            if remote.get('sync_enabled', 1) and remote.get('sync_direction') in ('pull', 'both'):
                result = db.sync_from_remote(remote)
                results.append({"remote": remote['name'], **result})
        return {"results": results}

    return execute_write(_pull)


@router.post("/sync/push")
def sync_push(authorization: str = Header(None)):
    """向所有启用的远程实例推送本地数据"""
    user = decode_auth_header(authorization)
    if not user:
        raise HTTPException(401, "Invalid auth")

    def _push(db):
        remotes = db.list_remote_instances()
        org_id = user.get('org_id', '')
        results = []
        for remote in remotes:
            if remote.get('sync_enabled', 1) and remote.get('sync_direction') in ('push', 'both'):
                result = db.push_to_remote(remote, org_id)
                results.append({"remote": remote['name'], **result})
        return {"results": results}

    return execute_write(_push)


# ============================================================
# OrionStar — Product Knowledge Base + AI Content Generation
# ============================================================

@router.get("/products")
def list_products(region: str = None, category: str = None, keyword: str = None, authorization: str = Header(None)):
    """List all products with optional region/category/keyword filters"""
    payload = decode_auth_header(authorization)
    from orgmind.easywiki.products import get_products
    products = get_products(payload['org_id'], category, region, keyword)
    return {"products": products, "total": len(products)}


@router.get("/products/{product_key}")
def get_product_detail(product_key: str, authorization: str = Header(None)):
    """Get a single product by its key"""
    payload = decode_auth_header(authorization)
    from orgmind.easywiki.products import get_product
    p = get_product(payload['org_id'], product_key)
    if not p:
        raise HTTPException(404, "Product not found")
    return p


@router.get("/products/search")
def search_products(q: str, authorization: str = Header(None)):
    """Full-text search across product names, descriptions, and keywords"""
    payload = decode_auth_header(authorization)
    from orgmind.easywiki.products import search_products
    return {"products": search_products(payload['org_id'], q), "query": q}


@router.post("/products/seed")
def seed_orionstar(authorization: str = Header(None)):
    """One-time seed: import 21 OrionStar products + 10 content templates"""
    payload = decode_auth_header(authorization)
    if payload['role'] != 'admin':
        raise HTTPException(403, "Only admin can seed products")
    from orgmind.easywiki.products import seed_orionstar_products
    result = seed_orionstar_products(payload['org_id'])
    log_audit(payload['user_id'], 'seed_orionstar_products', 'product', None, result)
    return result


# === Content Generation ===
@router.get("/models")
def get_ai_models(authorization: str = Header(None)):
    """Get available AI models grouped by family (article/image/video)"""
    decode_auth_header(authorization)
    from orgmind.easywiki.generator import get_models
    return get_models()


@router.get("/languages")
def get_languages(authorization: str = Header(None)):
    """Get 60 supported output languages"""
    decode_auth_header(authorization)
    from orgmind.easywiki.generator import get_languages
    return get_languages()


@router.get("/templates")
def list_templates(authorization: str = Header(None)):
    """Get 10 content generation templates"""
    payload = decode_auth_header(authorization)
    from orgmind.easywiki.products import get_templates
    return {"templates": get_templates(payload['org_id'])}


@router.post("/generate")
def generate_article(body: dict = Body(...), authorization: str = Header(None)):
    """Generate content: select template, product, model, language and optional reference selections"""
    payload = decode_auth_header(authorization)
    from orgmind.easywiki.generator import generate_content
    result = generate_content(
        template_id=body['template_id'],
        product_key=body['product_key'],
        model_id=body['model_id'],
        language=body.get('language', 'zh'),
        org_id=payload['org_id'],
        user_id=payload['user_id'],
        highlights=body.get('highlights'),
        specs=body.get('specs'),
    )
    if result['ok']:
        log_audit(payload['user_id'], 'generate_content', 'generated_output', result.get('output_id'), {"model": body['model_id'], "language": body.get('language','zh')})
    return result


@router.get("/outputs")
def list_outputs(limit: int = 20, authorization: str = Header(None)):
    """List recent generated outputs"""
    payload = decode_auth_header(authorization)
    from orgmind.easywiki.products import get_outputs
    return {"outputs": get_outputs(payload['org_id'], payload['user_id'], limit)}
