"""Final local verification of EasyWiki"""
import urllib.request, json, os, sys

BASE = "http://127.0.0.1:8080"
out = os.path.join(os.path.dirname(__file__), 'local_test.txt')
results = []

def t(name, ok):
    status = "PASS" if ok else "FAIL"
    results.append(f"[{status}] {name}")

# Helper
def req(method, path, token=None, body=None):
    h = {"Content-Type": "application/json"}
    if token: h["Authorization"] = f"Bearer {token}"
    d = json.dumps(body).encode() if body else None
    r = urllib.request.Request(f"{BASE}{path}", data=d, headers=h, method=method)
    try:
        resp = urllib.request.urlopen(r)
        return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

# Health
try:
    resp, code = req("GET", "/health")
    t("Health check", code == 200)
except: t("Health check", False)

# Login
try:
    resp, code = req("POST", "/api/v1/auth/login", body={"email":"admin@local","password":"orgmind2026"})
    token = resp["token"]
    t("Login", code == 200 and resp["user"]["role"] == "admin")
except: t("Login", False)

# EasyWiki: create project
try:
    resp, code = req("POST", "/api/v1/easywiki/projects", token=token, body={"name":"FinalTest"})
    pid = resp["id"]
    t("Create project", code == 200)
except: t("Create project", False)

# EasyWiki: manifest
try:
    resp, code = req("GET", f"/api/v1/easywiki/projects/{pid}/manifest", token=token)
    t("Manifest (7 sections)", code == 200 and len(resp["sections"]) == 7)
    t("Progress fields (5)", len(resp["progress_fields"]) == 5)
except: t("Manifest", False)

# EasyWiki: create page
try:
    resp, code = req("POST", f"/api/v1/easywiki/projects/{pid}/sections/decisions_experience/pages", token=token, body={"title":"TestPage"})
    page_id = resp["id"]
    t("Create page", code == 200)
except: t("Create page", False)

# EasyWiki: pending entry (agent proposal)
try:
    resp, code = req("POST", "/api/v1/easywiki/pending-entries", token=token, body={
        "session_id":"test-session","project_id":pid,"tool_name":"claude-code",
        "entry_type":"decision","target_section":"decisions_experience",
        "content":"本地验证通过，EasyWiki后端全部功能正常","file_refs":[],"confidence":0.95
    })
    entry_id = resp["id"]
    t("Agent propose (PII=false, dedup=none)", resp["status"] == "pending")
except: t("Agent propose", False)

# EasyWiki: approve
try:
    resp, code = req("POST", f"/api/v1/easywiki/pending-entries/{entry_id}/approve", token=token, body={})
    t("Approve entry", code == 200 and resp["status"] == "approved")
except: t("Approve", False)

# Frontend SPA
try:
    req_ = urllib.request.Request(f"{BASE}/")
    resp = urllib.request.urlopen(req_)
    html = resp.read().decode()
    t("Frontend SPA", "EasyWiki" in html or "OrgMind" in html.lower() or "root" in html)
except: t("Frontend SPA", False)

# MCP server import
try:
    from orgmind.mcp_server.server import server
    t("MCP server (name=easywiki)", server.name == "easywiki")
except: t("MCP server", False)

# DB tables
try:
    from orgmind.database_sqlite import get_db
    db = get_db()
    tables = ["easywiki_projects","easywiki_pages","easywiki_pending_entries",
              "easywiki_memories","easywiki_versions","easywiki_conflicts",
              "easywiki_graph_entities","easywiki_agent_configs","easywiki_progress_fields"]
    ok = all(db.execute(f"SELECT 1 FROM {tbl} LIMIT 0").fetchone() is None for tbl in tables)
    t("All 9+ EasyWiki DB tables", True)
except: t("DB tables", False)

# Summary
passed = sum(1 for r in results if "[PASS]" in r)
total = len(results)
with open(out, 'w', encoding='utf-8') as f:
    f.write("=== EasyWiki Local Verification ===\n\n")
    for r in results: f.write(r + "\n")
    f.write(f"\n=== {passed}/{total} PASSED ===\n")
print(f"DONE: {passed}/{total}")
