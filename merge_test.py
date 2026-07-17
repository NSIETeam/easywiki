import urllib.request, json

B = "http://127.0.0.1:8080"
def req(m, path, token=None, body=None):
    h = {"Content-Type": "application/json"}
    if token: h["Authorization"] = f"Bearer {token}"
    d = json.dumps(body).encode() if body else None
    r = urllib.request.Request(f"{B}{path}", data=d, headers=h, method=m)
    resp = urllib.request.urlopen(r)
    return json.loads(resp.read()), resp.status

resp, _ = req("POST", "/api/v1/auth/login", body={"email":"admin@local","password":"orgmind2026"})
token = resp["token"]

resp, _ = req("POST", "/api/v1/easywiki/projects", token=token, body={"name":"VTest"})
pid = resp["id"]

resp, _ = req("POST", f"/api/v1/easywiki/projects/{pid}/sections/decisions_experience/pages",
             token=token, body={"title":"VP"})
page_id = resp["id"]

resp, _ = req("GET", f"/api/v1/easywiki/pages/{page_id}", token=token)
print(f"GET1 full: {json.dumps(resp, indent=2)[:500]}")
v1 = resp.get("current_version_id")
print(f"v1={v1[:8] if v1 else 'NONE'} doc={repr(resp.get('blocksuite_doc',''))}")

# Edit 1: from v1 → "doc_A_content"
resp, code = req("PUT", f"/api/v1/easywiki/pages/{page_id}", token=token,
                 body={"blocksuite_doc": "doc_A_content", "based_on_version": v1})
print(f"PUT2: code={code} resp={resp}")

resp, _ = req("GET", f"/api/v1/easywiki/pages/{page_id}", token=token)
v2 = resp["current_version_id"]
print(f"v2={v2[:8]} doc={repr(resp.get('blocksuite_doc',''))}")

# Edit 2: from v1 (stale base) → should auto-merge or conflict
resp, code = req("PUT", f"/api/v1/easywiki/pages/{page_id}", token=token,
                 body={"blocksuite_doc": "doc_B_disjoint", "based_on_version": v1})
print(f"PUT3: code={code} resp={resp}")

resp, _ = req("GET", f"/api/v1/easywiki/pages/{page_id}", token=token)
print(f"FINAL: v={resp['current_version_id'][:8]} doc={repr(resp.get('blocksuite_doc',''))}")

import sqlite3, os
db = sqlite3.connect(os.path.expanduser("~/.orgmind/orgmind.db"))
db.row_factory = sqlite3.Row
rows = db.execute("SELECT id, substr(content_snapshot,1,40) as cs FROM easywiki_versions WHERE target_id=? ORDER BY created_at", (page_id,)).fetchall()
print(f"\nVersions ({len(rows)}):")
for r in rows: print(f"  {r['id'][:8]}: {r['cs']}")
