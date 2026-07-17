"""EasyWiki Phase 1 integration tests"""
import urllib.request, json, sys

BASE = "http://127.0.0.1:8080"

def req(method, path, token=None, body=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r)
        return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

# Login
resp, _ = req("POST", "/api/v1/auth/login", body={"email":"admin@local","password":"orgmind2026"})
token = resp["token"]
print(f"[OK] Login: {resp['user']['role']}")

# Test 1: Create project
resp, code = req("POST", "/api/v1/easywiki/projects", token=token, body={"name":"EasyWiki测试项目"})
assert code == 200, f"Create project failed: {resp}"
pid = resp["id"]
print(f"[OK] Create project: {pid}")

# Test 2: List projects
resp, code = req("GET", "/api/v1/easywiki/projects", token=token)
assert code == 200 and len(resp["projects"]) >= 1
print(f"[OK] List projects: {len(resp['projects'])} found")

# Test 3: Manifest
resp, code = req("GET", f"/api/v1/easywiki/projects/{pid}/manifest", token=token)
assert code == 200 and len(resp["sections"]) == 7
print(f"[OK] Manifest: {len(resp['sections'])} sections, {len(resp['progress_fields'])} progress fields")

# Test 4: Create page
resp, code = req("POST", f"/api/v1/easywiki/projects/{pid}/sections/decisions_experience/pages", token=token, body={"title":"测试决策记录"})
assert code == 200
page_id = resp["id"]
print(f"[OK] Create page: {page_id}")

# Test 5: List pages
resp, code = req("GET", f"/api/v1/easywiki/projects/{pid}/sections/decisions_experience/pages", token=token)
assert code == 200
print(f"[OK] List pages: {len(resp['pages'])} found")

# Test 6: Get page
resp, code = req("GET", f"/api/v1/easywiki/pages/{page_id}", token=token)
assert code == 200
print(f"[OK] Get page: title={resp['title']}")

# Test 7: Update page
resp, code = req("PUT", f"/api/v1/easywiki/pages/{page_id}", token=token, body={"blocksuite_doc":"dGVzdA=="})
assert code == 200
print(f"[OK] Update page: version={resp.get('version_id','N/A')}")

# Test 8: Pending entry
resp, code = req("POST", "/api/v1/easywiki/pending-entries", token=token, body={
    "session_id":"test-session","project_id":pid,"tool_name":"claude-code",
    "entry_type":"decision","target_section":"decisions_experience",
    "content":"决定使用FastAPI+SQLite作为技术栈","file_refs":[],"confidence":0.9
})
assert code == 200 and resp["status"] == "pending"
entry_id = resp["id"]
print(f"[OK] Pending entry: {entry_id} dedup={resp['dedup_hint']} pii={resp['pii_flag']}")

# Test 9: List pending
resp, code = req("GET", f"/api/v1/easywiki/projects/{pid}/pending-entries", token=token)
assert code == 200
print(f"[OK] List pending: {len(resp['entries'])} found")

# Test 10: Approve
resp, code = req("POST", f"/api/v1/easywiki/pending-entries/{entry_id}/approve", token=token, body={})
assert code == 200 and resp["status"] == "approved"
print(f"[OK] Approve: written_to={resp['written_to']}")

# Test 11: Verify approved entry is gone from pending
resp, code = req("GET", f"/api/v1/easywiki/projects/{pid}/pending-entries?status=pending", token=token)
assert code == 200 and len(resp["entries"]) == 0
print(f"[OK] Pending queue empty after approval")

# Test 12: Reject flow
resp, code = req("POST", "/api/v1/easywiki/pending-entries", token=token, body={
    "session_id":"test-session","project_id":pid,"tool_name":"easycode",
    "entry_type":"bug_fix","target_section":"decisions_experience",
    "content":"修复了登录页面空指针问题","file_refs":[],"confidence":0.7
})
entry2_id = resp["id"]
resp, code = req("POST", f"/api/v1/easywiki/pending-entries/{entry2_id}/reject", token=token, body={"reason":"需要补充更多上下文"})
assert code == 200 and resp["status"] == "rejected"
print(f"[OK] Reject: {entry2_id}")

# Test 13: Versions
resp, code = req("GET", f"/api/v1/easywiki/versions?target_type=page&target_id={page_id}", token=token)
assert code == 200
print(f"[OK] Versions: {len(resp['versions'])} found")

# Test 14: Batch approve
ids = []
for i in range(3):
    resp, _ = req("POST", "/api/v1/easywiki/pending-entries", token=token, body={
        "session_id":"batch-test","project_id":pid,"tool_name":"claude-code",
        "entry_type":"best_practice","target_section":"decisions_experience",
        "content":f"最佳实践 #{i}: 使用参数化查询","file_refs":[],"confidence":0.8
    })
    ids.append(resp["id"])
resp, code = req("POST", "/api/v1/easywiki/pending-entries/batch-approve", token=token, body={"ids":ids})
assert code == 200 and len(resp["approved"]) == 3
print(f"[OK] Batch approve: {len(resp['approved'])} approved, {len(resp['failed'])} failed")

# Test 15: Clone mount
resp, code = req("POST", "/api/v1/easywiki/projects", token=token, body={"name":"目标项目"})
target_pid = resp["id"]
resp, code = req("POST", f"/api/v1/easywiki/pages/{page_id}/clone-mount", token=token, body={"target_project_id":target_pid,"target_section":"decisions_experience"})
assert code == 200
print(f"[OK] Clone mount: {resp['cloned_page_id']}")

# Summary
print()
print("=" * 50)
print("ALL 15 PHASE 1+2 TESTS PASSED")
print("=" * 50)
