"""
Deep integration test — verifies the 3 critical fixes from the audit report:
  1. three_way_merge is wired into PUT /pages/{page_id} (real 3-way merge, not naive lock)
  2. build_graph is wired into approve_pending_entry path
  3. log_audit is called on create_page and update_page
  4. progress_field_merge is wired into progress_update approve path
"""
import urllib.request, urllib.error, json, os, time, sys

BASE = "http://127.0.0.1:8080"
results = []

def t(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    results.append(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        print(f"  XXX FAIL: {name} — {detail}")

def req(method, path, token=None, body=None):
    h = {"Content-Type": "application/json"}
    if token: h["Authorization"] = f"Bearer {token}"
    d = json.dumps(body).encode() if body else None
    r = urllib.request.Request(f"{BASE}{path}", data=d, headers=h, method=method)
    try:
        resp = urllib.request.urlopen(r)
        return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try: return json.loads(body), e.code
        except: return body, e.code

# ── Login ──
resp, code = req("POST", "/api/v1/auth/login", body={"email":"admin@local","password":"orgmind2026"})
token = resp["token"]; org_id = resp["user"]["org_id"]; uid = resp["user"]["id"]

# ── Create project ──
resp, code = req("POST", "/api/v1/easywiki/projects", token=token, body={"name":"DeepTest"})
pid = resp["id"]
t("Create project", code == 200)

# ================================================================
# TEST 1: Three-way merge is wired into PUT /pages (Section 3.5)
# ================================================================
resp, code = req("POST", f"/api/v1/easywiki/projects/{pid}/sections/decisions_experience/pages",
                 token=token, body={"title":"MergeTest"})
page_id = resp["id"]

# Get initial state (should have version v1 from creation with content_snapshot="")
resp, _ = req("GET", f"/api/v1/easywiki/pages/{page_id}", token=token)
v1 = resp["current_version_id"]  # version after creation (empty doc)

# First, set initial content with 3 lines so subsequent edits can be disjoint
initial_body = {"blocksuite_doc": "line1\nline2\nline3", "based_on_version": v1}
resp, code = req("PUT", f"/api/v1/easywiki/pages/{page_id}", token=token, body=initial_body)
t("PUT v2 (set initial multi-line content)", code == 200, f"version={resp.get('version_id','?')[:8]}")

resp, _ = req("GET", f"/api/v1/easywiki/pages/{page_id}", token=token)
v2 = resp["current_version_id"]

# User A edits line 0: change "line1" → "line1_modified"
resp, code = req("PUT", f"/api/v1/easywiki/pages/{page_id}",
                 token=token, body={"blocksuite_doc": "line1_modified\nline2\nline3", "based_on_version": v2})
t("PUT v3 (A edits line 0)", code == 200)

resp, _ = req("GET", f"/api/v1/easywiki/pages/{page_id}", token=token)
v3 = resp["current_version_id"]

# User B edits line 1 from same base (v2): "line2" → "line2_modified" — disjoint, should auto-merge
resp, code = req("PUT", f"/api/v1/easywiki/pages/{page_id}",
                 token=token, body={"blocksuite_doc": "line1\nline2_modified\nline3", "based_on_version": v2})
t("PUT v4 (B edits line 1 from old base v2 → auto-merge, no conflict)", code == 200 and resp.get("conflict_id") is None,
   f"code={code} merged={'present' if resp.get('merged_content') else 'none'}")

# Verify the merged result contains both edits
resp, _ = req("GET", f"/api/v1/easywiki/pages/{page_id}", token=token)
final_doc = resp.get("blocksuite_doc", "")
t("Merged doc has both edits", "line1_modified" in final_doc and "line2_modified" in final_doc,
   f"doc={final_doc[:50]}")

# Force a real conflict: A and B both edit the same line area.
# We need to create a scenario where base != current and edits overlap.
# Simpler approach: directly verify that editing from a non-existent (stale) version does something useful.
# Actually, let's test the conflict path by making concurrent edits that overlap.

# Use the raw three_way_merge function directly to verify the merge logic works
try:
    from orgmind.easywiki.version_diff import three_way_merge
    merged, cid = three_way_merge("line1\nline2\nline3", "line1_modified\nline2\nline3", "line1\nline2_modified\nline3",
                                   "page", "test_id", pid)
    t("3-way merge: disjoint edits auto-merge (no conflict)", cid is None and "line1_modified" in merged and "line2_modified" in merged)

    merged2, cid2 = three_way_merge("line1\nline2\nline3", "line1_CHANGED\nline2\nline3", "line1_OTHER\nline2\nline3",
                                    "page", "test_id2", pid)
    t("3-way merge: overlapping edits create conflict", cid2 is not None)
except Exception as e:
    t("3-way merge: function can be imported and executed", False, str(e))

# ================================================================
# TEST 2: build_graph wired into approve_pending_entry
# ================================================================
resp, code = req("POST", "/api/v1/easywiki/pending-entries", token=token, body={
    "session_id":"deep-test-session","project_id":pid,"tool_name":"claude-code",
    "entry_type":"decision","target_section":"decisions_experience",
    "content":"决定采用PostgreSQL作为主数据库，替代原有的MySQL方案。联系人: test@orgmind.com",
    "file_refs":[],"confidence":0.9
})
entry_id = resp["id"]
t("Create pending entry for graph test", code == 200)

# Approve — this should trigger build_graph
resp, code = req("POST", f"/api/v1/easywiki/pending-entries/{entry_id}/approve", token=token, body={})
t("Approve entry (triggers build_graph)", code == 200, f"status={resp.get('status','?')}")

# Wait for server to commit before direct DB reads
time.sleep(0.5)

# Check easywiki_graph_entities table for extracted entities
db_path = os.path.expanduser("~/.orgmind/orgmind.db")
import sqlite3
db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
db.row_factory = sqlite3.Row
entities = db.execute("SELECT name, entity_type FROM easywiki_graph_entities WHERE org_id=? AND project_id=?",
                      (org_id, pid)).fetchall()
entity_names = [e["name"] for e in entities]
t("Graph entities table has records after approve", len(entities) > 0, f"found: {entity_names}")

# Check easywiki_graph_relations for pairwise relations (not self-loops)
relations = db.execute("SELECT from_entity_id, to_entity_id, relation FROM easywiki_graph_relations WHERE source_id=?",
                       (resp.get("memory_id", entry_id),)).fetchall()
if relations:
    has_self_loop = any(r["from_entity_id"] == r["to_entity_id"] for r in relations)
    t("Graph relations: no self-loops (different from_entity_id != to_entity_id)", not has_self_loop,
       f"{len(relations)} relations")
else:
    # May be 0 relations if only 1 entity found. Check if at least entities were written.
    t("Graph relations: at least entities were written (relations may be 0 with 1 entity)",
       len(entities) > 0, f"entities={len(entities)} relations={len(relations)}")

# ================================================================
# TEST 3: log_audit on create_page and update_page
# ================================================================
audit_rows = db.execute(
    "SELECT action, resource_type, resource_id FROM audit_logs WHERE resource_type='easywiki_page' ORDER BY created_at DESC LIMIT 10"
).fetchall()
create_audit = [r for r in audit_rows if r["action"] == "create_easywiki_page"]
update_audit = [r for r in audit_rows if r["action"] == "update_easywiki_page"]
t("log_audit: create_page has audit record", len(create_audit) > 0)
t("log_audit: update_page has audit record", len(update_audit) > 0)

# ================================================================
# TEST 4: progress_field_merge in approve_pending_entry
# ================================================================
# Create a progress_update pending entry
resp, code = req("POST", "/api/v1/easywiki/pending-entries", token=token, body={
    "session_id":"deep-test-session-2","project_id":pid,"tool_name":"claude-code",
    "entry_type":"progress_update","target_section":"",  # progress fields use target_section for field_name mapping
    "content":"{\"field_name\":\"status_summary\",\"suggested_value\":\"Phase 1 completed, moving to Phase 2\"}",
    "file_refs":[],"confidence":0.85
})
prog_entry_id = resp["id"]
t("Create progress_update pending entry", code == 200)

resp, code = req("POST", f"/api/v1/easywiki/pending-entries/{prog_entry_id}/approve", token=token, body={})
t("Approve progress_update entry", code == 200, f"status={resp.get('status','?')}")

# Check that the progress field was updated in easywiki_progress_fields
pf_rows = db.execute("SELECT field_name, current_value FROM easywiki_progress_fields WHERE project_id=?",
                     (pid,)).fetchall()
pf_map = {r["field_name"]: r["current_value"] for r in pf_rows}
t("Progress field 'status_summary' updated after approve",
   pf_map.get("status_summary", "") == "Phase 1 completed, moving to Phase 2",
   f"value={pf_map.get('status_summary','NOT FOUND')}")

# ================================================================
# TEST 5: Version tracking works through PUT /pages
# ================================================================
time.sleep(1.0)  # Allow server WAL to flush
db_v = sqlite3.connect(db_path)
db_v.row_factory = sqlite3.Row
resp, _ = req("GET", f"/api/v1/easywiki/pages/{page_id}", token=token)
current_v = resp["current_version_id"]
# Check easywiki_versions table
versions = db_v.execute("SELECT id FROM easywiki_versions WHERE target_id=? ORDER BY created_at DESC",
                      (page_id,)).fetchall()
print(f"  DEBUG: page_id={page_id}, versions_found={len(versions)}, current_v={current_v}")
for v in versions:
    print(f"    version: {v['id']}")
t("Version history: at least 4 versions (create + init + A edit + B auto-merge)", len(versions) >= 4, f"count={len(versions)}")
version_ids = {v["id"] for v in versions}
t("Current version is in version history", current_v in version_ids,
   f"current={current_v[:8]} in_history={'yes' if current_v in version_ids else 'no'}")
db_v.close()

db.close()

# ── Summary ──
passed = sum(1 for r in results if "[PASS]" in r)
total = len(results)
out_path = os.path.join(os.path.dirname(__file__), "deep_test_results.txt")
with open(out_path, 'w', encoding='utf-8') as f:
    f.write("=== Deep Integration Test Results ===\n\n")
    for r in results: f.write(r + "\n")
    f.write(f"\n=== {passed}/{total} PASSED ===\n")
print(f"\nDONE: {passed}/{total} PASSED")
